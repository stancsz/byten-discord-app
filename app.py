import mimetypes
import os, io
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI
import requests

async def is_text_file(attachment):
    try:
        # Infer MIME type from filename
        mime_type, _ = mimetypes.guess_type(attachment.filename)
        if mime_type and (mime_type.startswith("text/") or mime_type in [
            "application/json",
            "application/javascript",
            "application/x-yaml",
        ]):
            # Read and decode the attachment content
            file_content = await attachment.read()
            try:
                decoded_content = file_content.decode("utf-8")
                return True, decoded_content
            except UnicodeDecodeError:
                print(f"File {attachment.filename} is not a UTF-8 text file.")
                return False, ""
        else:
            return False, ""
    except Exception as e:
        print(f"Error checking attachment {attachment.filename}: {str(e)}")
        return False, ""

def setup_environment():
    load_dotenv()

    def load_trigger_words(env_var):
        trigger_words = os.getenv(env_var, "").split(",")
        return [re.compile(word.strip(), re.IGNORECASE) for word in trigger_words if word.strip()]

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
    TRIGGER_WORDS = load_trigger_words("TRIGGER_WORDS")

    if SYSTEM_PROMPT.startswith("http://") or SYSTEM_PROMPT.startswith("https://"):
        try:
            response = requests.get(SYSTEM_PROMPT)
            response.raise_for_status()
            SYSTEM_PROMPT = response.text.strip()
            print("SYSTEM_PROMPT fetched from URL successfully.")
        except requests.RequestException as e:
            print(f"Error fetching SYSTEM_PROMPT from URL: {e}")
            SYSTEM_PROMPT = ""

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

config = setup_environment()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def ai_response(prompt, messages):
    client = OpenAI()
    final_messages = []
    if config["SYSTEM_PROMPT"]:
        final_messages.append({"role": "system", "content": config["SYSTEM_PROMPT"]})
    final_messages.extend(messages)
    if prompt:
        final_messages.append({"role": "user", "content": prompt})

    try:
        if "o1" in config["OPENAI_MODEL"]:
            print("Using an o1 model. System instructions and advanced configurations are not supported.")
            response = client.chat.completions.create(
                model=config["OPENAI_MODEL"],
                messages=messages
            )
        else:
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
    if config["ALLOWED_CHANNELS"] and str(message.channel.id) not in config["ALLOWED_CHANNELS"]:
        return False
    if config["ALLOWED_USERS"] and str(message.author.id) not in config["ALLOWED_USERS"]:
        return False
    if (not config["ALLOW_BOTS"] and message.author.bot) or not re.match(
        config["NAME_PATTERN"], message.author.name
    ):
        return False
    if bot.user in message.mentions:
        return True
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
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
        else:
            message_excerpt = message.content[:50]
            sanitized_excerpt = message_excerpt.replace('\n', ' ').strip()
            thread_name = f"{sanitized_excerpt}" if sanitized_excerpt else f"Response to {message.author.name}"
            thread = await message.channel.create_thread(
                name=thread_name,
                message=message,
                auto_archive_duration=4320
            )

        messages = []
        async for msg in message.channel.history(limit=config["HISTORY_LIMIT"]):
            role = "assistant" if msg.author.bot else "user"
            content = msg.content

            for attachment in msg.attachments:
                is_text, file_text = await is_text_file(attachment)
                if is_text:
                    content += f"\n\n# {attachment.filename}\n{file_text}\n"

            messages.insert(0, {"role": role, "content": content})

        response = ai_response(config["MSG_PROMPT"], messages)

        if len(response) > 2000:
            file_buffer = io.BytesIO(response.encode('utf-8'))
            file_buffer.seek(0)
            discord_file = discord.File(file_buffer, filename="response.txt")

            await thread.send(file=discord_file)

            for chunk in split_text(response):
                await thread.send(chunk)
        else:
            await thread.send(response)

    except Exception as e:
        print(f"Error in on_message: {str(e)}")
        await message.channel.send(f"I couldn't process the request. Please try again later. Debug:{str(e)}")

    await bot.process_commands(message)

bot.run(config["DISCORD_BOT_TOKEN"])
