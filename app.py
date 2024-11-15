import os
import discord
import ollama
import tiktoken

from discord.ext import commands
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('Hello I am Llama Bot!')

@bot.command(name='ask')
async def ask(ctx,*,message):
    print(message)
    response = ollama.chat(model='llama3', messages=[
      {
          'role':'system',
          'content':'You are a helpful assistant that answers questions concisely and informatively in no more than 1000 words'
      },
      {
        'role': 'user',
        'content': message,
      },
    ])

    print(response)
    await ctx.send(response['message']['content'])


@bot.command(name='summarise')
async def summarise(ctx):

    msgs = [message.content async for message in ctx.channel.history(limit=10)]

    summarise_prompt = f"""
        Summarise the following messages delimited by 3 backticks :
        ```
        {msgs}
        ```
    """

    response = ollama.chat(model='llama3', messages=[
      {
          'role':'system',
          'content':'You are a helpful assistant who summarises provided messages concisely and informatively in no more than 1000 words'
      },
      {
        'role': 'user',
        'content': summarise_prompt,
      },
    ])
    await ctx.send(response['message']['content'])

@bot.command(name='yt_tldr')
async def yt_tldr(ctx,url):

    await ctx.send("Fetching and Summarising the youtube video.....")

    video_id = url.split('v=')[1]
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    full_transcript = " ".join([item['text'] for item in transcript_list])

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(full_transcript)
    num_tokens = len(tokens)

    print(num_tokens)
    chunk_size = 7000

    if num_tokens>chunk_size:
        num_chunks = (num_tokens + chunk_size - 1) // chunk_size
        chunks = [tokens[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]

        async def process_chunks(chunk, chunk_num):

            await ctx.send(f"Processing chunk {chunk_num} of {num_chunks}....")
            response = ollama.chat(model='llama3', messages=[
            {
                'role':'system',
                'content' : '''
                    You are a helpful assistant who provides a concise summary of provided Youtube Video transcript in bullet points
                    ''',
            },
            {
                'role': 'user',
                'content': f'''
                Please provide a summary for the following chunk of the Youtube Video Transcript:
                {chunk}            
                ''',
            },
            ])
            return response(['message']['content'])
        
        for i,chunk in  enumerate(chunks,start=1):
            summary = await process_chunks(chunk,i)
            await ctx.send(summary)

        else:
            response = ollama.chat(model='llama3', messages=[
            {
                'role':'system',
                'content' : '''
                    You are a helpful assistant who provides a concise summary of provided Youtube Video transcript in bullet points
                    ''',
            },
            {
                'role': 'user',
                'content': full_transcript,
            },
            ])
            final_summary = response(['message']['content'])
            await ctx.send(final_summary)

@bot.command(name='ideas')
async def extract_ideas(ctx,url):

    await ctx.send("Extracting ideas from the youtube video.....")

    video_id = url.split('v=')[1]
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    full_transcript = " ".join([item['text'] for item in transcript_list])

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(full_transcript)
    num_tokens = len(tokens)

    chunk_size=7000

    response = ollama.chat(model='llama3', messages=[
        {
            'role':'system',
            'content' : '''
                You are an expert youtube content creator who is an expert at analysing and extracting ideas from provided Youtube Video transcript
                ''',
        },
        {
            'role': 'user',
            'content': f'''
                Extract 3 key ideas

                Video Transcript:
                {full_transcript}
                ''',
        },
        ])
    ideas = response(['message']['content'])
    await ctx.send(ideas)


bot.run(os.getenv('DISCORD_BOT_TOKEN'))