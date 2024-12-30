import os
import discord
import ollama
import tiktoken

from discord.ext import commands
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(
    # This is the default and can be omitted
    api_key=GROQ_API_KEY,
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


def split_message(content, limit=2000):
    """
    Splits a long message into chunks, ensuring each chunk is within the character limit.
    """
    return [content[i:i+limit] for i in range(0, len(content), limit)]


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Hello, I am Llama Bot!')


@bot.command(name='ask')
async def ask(ctx, *, message):
    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant that answers questions concisely and informatively in not more than 1000 words.'
            },
            {
                'role': 'user',
                'content': message,
            },
        ])
        content = response.choices[0].message.content
        
        for chunk in split_message(content):
            await ctx.send(chunk)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


@bot.command(name='summarise')
async def summarise(ctx):
    try:
        msgs = [message.content async for message in ctx.channel.history(limit=10)]
        summarise_prompt = f"""
        Summarise the following messages delimited by 3 backticks:
        ```
        {msgs}
        ```
        """

        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant who summarises provided messages concisely and informatively in no more than 1000 words.'
            },
            {
                'role': 'user',
                'content': summarise_prompt,
            },
        ])
        content = response.choices[0].message.content

        for chunk in split_message(content):
            await ctx.send(chunk)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


@bot.command(name='yt_tldr')
async def yt_tldr(ctx, url):
    try:
        await ctx.send("Fetching and summarizing the YouTube video...")

        query = parse_qs(urlparse(url).query)
        video_id = query.get("v", [None])[0]

        if not video_id:
            await ctx.send("Invalid YouTube URL!")
            return

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item['text'] for item in transcript])

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens = encoding.encode(full_transcript)
        num_tokens = len(tokens)

        chunk_size = 7000
        if num_tokens > chunk_size:
            chunks = [
                encoding.decode(tokens[i:i+chunk_size])
                for i in range(0, len(tokens), chunk_size)
            ]

            for i, chunk in enumerate(chunks, start=1):
                await ctx.send(f"Processing chunk {i}/{len(chunks)}...")
                response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant summarizing the transcript in bullet points.'
                    },
                    {
                        'role': 'user',
                        'content': f"Please summarize this transcript chunk:\n{chunk}",
                    },
                ])
                for chunk in split_message(response.choices[0].message.content):
                    await ctx.send(chunk)
        else:
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant summarizing the transcript in bullet points.'
                },
                {
                    'role': 'user',
                    'content': full_transcript,
                },
            ])
            for chunk in split_message(response.choices[0].message.content):
                await ctx.send(chunk)
    except (TranscriptsDisabled, NoTranscriptFound):
        await ctx.send("Transcript not available for this video.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


@bot.command(name='ideas')
async def extract_ideas(ctx, url):
    try:
        await ctx.send("Extracting ideas from the YouTube video...")

        query = parse_qs(urlparse(url).query)
        video_id = query.get("v", [None])[0]

        if not video_id:
            await ctx.send("Invalid YouTube URL!")
            return

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item['text'] for item in transcript])

        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[
            {
                'role': 'system',
                'content': 'You are an expert YouTube content creator who is skilled at analyzing and extracting ideas from provided YouTube video transcripts.'
            },
            {
                'role': 'user',
                'content': f"Extract 3 key ideas from the following transcript:\n{full_transcript}"
            },
        ])
        content = response.choices[0].message.content

        for chunk in split_message(content):
            await ctx.send(chunk)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")


bot.run(os.getenv('DISCORD_BOT_TOKEN'))

