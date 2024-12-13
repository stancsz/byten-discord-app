import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Environment variables (all centralized here for easy tracking)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "").strip()
MSG_PROMPT = os.getenv("MSG_PROMPT", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RESPONSE_CHARS = int(os.getenv("MAX_RESPONSE_CHARS", 2000))
ALLOW_BOTS = os.getenv("ALLOW_BOTS", "false").lower() == "true"
NAME_PATTERN = os.getenv("NAME_PATTERN", ".*")

# OpenAI parameters with defaults
TEMPERATURE = float(os.getenv("TEMPERATURE", 1))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))
TOP_P = float(os.getenv("TOP_P", 1))
FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", 0))
PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", 0))

# Ensure required environment variables are set
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN is not set in environment variables")

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable access to message content

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

def ai_response(prompt, messages):
    """
    Fetch an AI response based on the given prompt and messages.
    """
    client = OpenAI()

    # Build the final message list, excluding empty prompts
    final_messages = []
    if SYSTEM_PROMPT:
        final_messages.append({"role": "system", "content": SYSTEM_PROMPT})
    final_messages.extend(messages)
    if prompt:
        final_messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=final_messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_response: {str(e)}")
        return "I couldn't process your request. Please try again later."

def split_text(text, max_length=MAX_RESPONSE_CHARS):
    """
    Split text into chunks of up to `max_length`, breaking on the last newline within the limit.
    """
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index])
        text = text[split_index:].lstrip('\n')
    chunks.append(text)
    return chunks

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Check if the sender is allowed based on bot status and name pattern
    if (not ALLOW_BOTS and message.author.bot) or not re.match(NAME_PATTERN, message.author.name):
        return

    try:
        messages = []
        async for msg in message.channel.history(limit=5):
            role = "assistant" if msg.author.bot else "user"
            messages.insert(0, {  # Insert older messages earlier in the list
                "role": role,
                "content": [{"type": "text", "text": msg.content}]
            })

        response = ai_response(MSG_PROMPT, messages)

        for chunk in split_text(response):
            await message.channel.send(chunk)
    except Exception as e:
        print(f"Error in on_message: {str(e)}")
        await message.channel.send("I couldn't process the request. Please try again later.")

    await bot.process_commands(message)

bot.run(DISCORD_BOT_TOKEN)
