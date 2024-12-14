import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI
import requests


def setup_environment():
    """
    Load and configure environment variables, ensuring defaults and simplifications.
    Returns a dictionary of all configurations.
    """
    # Load environment variables from .env file
    load_dotenv()
    def load_trigger_words(env_var):
        """
        Load trigger words from an environment variable and compile them into regex patterns.
        :param env_var: A comma-separated string of regex patterns.
        :return: A list of compiled regex patterns.
        """
        trigger_words = os.getenv(env_var, "").split(",")
        return [re.compile(word.strip(), re.IGNORECASE) for word in trigger_words if word.strip()]

    # Fetch environment variables with defaults
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "").strip()
    MSG_PROMPT = os.getenv("MSG_PROMPT", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    MAX_RESPONSE_CHARS = int(os.getenv("MAX_RESPONSE_CHARS", 2000))
    ALLOW_BOTS = os.getenv("ALLOW_BOTS", "false").lower() == "true"
    NAME_PATTERN = os.getenv("NAME_PATTERN", ".*")
    ALLOWED_CHANNELS = [
        ch.strip() for ch in os.getenv("ALLOWED_CHANNELS", "").split(",") if ch.strip()
    ]
    ALLOWED_USERS = [
        usr.strip() for usr in os.getenv("ALLOWED_USERS", "").split(",") if usr.strip()
    ]
    HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", 5))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 1))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))
    TOP_P = float(os.getenv("TOP_P", 1))
    FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", 0))
    PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", 0))

    # Load trigger words as regex patterns
    TRIGGER_WORDS = load_trigger_words("TRIGGER_WORDS")

    # Fetch SYSTEM_PROMPT content if it's a URL
    if SYSTEM_PROMPT.startswith("http://") or SYSTEM_PROMPT.startswith("https://"):
        try:
            response = requests.get(SYSTEM_PROMPT)
            response.raise_for_status()
            SYSTEM_PROMPT = response.text.strip()
            print("SYSTEM_PROMPT fetched from URL successfully.")
        except requests.RequestException as e:
            print(f"Error fetching SYSTEM_PROMPT from URL: {e}")
            SYSTEM_PROMPT = ""  # Fallback to empty if fetching fails

    # Ensure required environment variables are set
    if not DISCORD_BOT_TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN is not set in environment variables")

    return {
        "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
        "SYSTEM_PROMPT": SYSTEM_PROMPT,
        "MSG_PROMPT": MSG_PROMPT,
        "OPENAI_MODEL": OPENAI_MODEL,
        "MAX_RESPONSE_CHARS": MAX_RESPONSE_CHARS,
        "ALLOW_BOTS": ALLOW_BOTS,
        "NAME_PATTERN": NAME_PATTERN,
        "ALLOWED_CHANNELS": ALLOWED_CHANNELS,
        "ALLOWED_USERS": ALLOWED_USERS,
        "HISTORY_LIMIT": HISTORY_LIMIT,
        "TEMPERATURE": TEMPERATURE,
        "MAX_TOKENS": MAX_TOKENS,
        "TOP_P": TOP_P,
        "FREQUENCY_PENALTY": FREQUENCY_PENALTY,
        "PRESENCE_PENALTY": PRESENCE_PENALTY,
        "TRIGGER_WORDS": TRIGGER_WORDS,
    }

# Fetch environment configuration
config = setup_environment()

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable access to message content

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)


def ai_response(prompt, messages):
    """
    Fetch an AI response based on the given prompt and messages.
    """
    client = OpenAI()

    # Build the final message list, excluding empty prompts
    final_messages = []
    if config["SYSTEM_PROMPT"]:
        final_messages.append({"role": "system", "content": config["SYSTEM_PROMPT"]})
    final_messages.extend(messages)
    if prompt:
        final_messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=config["OPENAI_MODEL"],
            messages=final_messages,
            temperature=config["TEMPERATURE"],
            max_tokens=config["MAX_TOKENS"],
            top_p=config["TOP_P"],
            frequency_penalty=config["FREQUENCY_PENALTY"],
            presence_penalty=config["PRESENCE_PENALTY"],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_response: {str(e)}")
        return "I couldn't process your request. Please try again later."


def split_text(text, max_length=config["MAX_RESPONSE_CHARS"]):
    """
    Split text into chunks of up to `max_length`, breaking on the last newline within the limit.
    """
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:
            split_index = max_length
        chunks.append(text[:split_index])
        text = text[split_index:].lstrip("\n")
    chunks.append(text)
    return chunks


def should_reply_to_message(message):
    """
    Determine if the bot should reply to the given message based on allowed channels, users, bot status,
    name pattern, and regex-based trigger word or bot mention.
    """
    # Check if the channel or user is allowed
    if config["ALLOWED_CHANNELS"] and str(message.channel.id) not in config["ALLOWED_CHANNELS"]:
        return False
    if config["ALLOWED_USERS"] and str(message.author.id) not in config["ALLOWED_USERS"]:
        return False

    # Check if bots are allowed and if the name pattern matches
    if (not config["ALLOW_BOTS"] and message.author.bot) or not re.match(
        config["NAME_PATTERN"], message.author.name
    ):
        return False

    # Check if the message mentions the bot
    if bot.user in message.mentions:
        return True

    # Check if any of the TRIGGER_WORDS regex patterns match the message content
    for pattern in config["TRIGGER_WORDS"]:
        if pattern.search(message.content):
            return True

    return False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if not should_reply_to_message(message):
        return

    try:
        messages = []
        async for msg in message.channel.history(limit=config["HISTORY_LIMIT"]):
            role = "assistant" if msg.author.bot else "user"
            messages.insert(0, {"role": role, "content": msg.content})

        response = ai_response(config["MSG_PROMPT"], messages)

        for chunk in split_text(response):
            await message.channel.send(chunk)
    except Exception as e:
        print(f"Error in on_message: {str(e)}")
        await message.channel.send("I couldn't process the request. Please try again later.")

    await bot.process_commands(message)


bot.run(config["DISCORD_BOT_TOKEN"])
