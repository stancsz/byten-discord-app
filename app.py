import os
import asyncio
import random
import discord
from discord.ext import commands
from response import get_ai_response
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable access to message content

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

async def random_pokes():
    await bot.wait_until_ready()
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
    channel = bot.get_channel(channel_id)

    if channel is None:
        print("Channel not found. Please check the channel ID.")
        return

    while not bot.is_closed():
        sleep_duration = random.randint(21600, 28800)
        print(f"Sleeping for {sleep_duration} seconds.")
        await asyncio.sleep(sleep_duration)
        try:
            messages = []
            async for msg in channel.history(limit=5):  # Fetch last 5 messages
                messages.append(msg)

            # Format the response
            context = "Here are the last 5 messages in this channel:\n\n"
            for msg in reversed(messages):  # Reverse to show oldest to newest
                context += f"{msg.author.display_name}: {msg.content}\n"

            response = get_ai_response(
                "If no one else replied since you last post asking for more work, independently come up with some lyrics ideas to work on it. Otherwise, You're ready to work, let your boss know you want a new task.",
                str(context)
            )

            # Send the response in chunks of 2000 characters or fewer
            for chunk in [response[i:i + 2000] for i in range(0, len(response), 2000)]:
                await channel.send(chunk)
        except Exception as e:
            print(f"Error fetching messages: {str(e)}")
            await channel.send("I couldn't fetch the messages. Please try again later.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    bot.loop.create_task(random_pokes())  # Start the random pokes task

@bot.event
async def on_message(message):
    # Prevent the bot from responding to its own messages
    if message.author == bot.user:
        return

    # Fetch and relay the last 5 messages
    try:
        messages = []
        async for msg in message.channel.history(limit=5):  # Fetch last 5 messages
            messages.append(msg)

        # Format the response
        context = "Here are the last 5 messages in this channel:\n\n"
        for msg in reversed(messages):  # Reverse to show oldest to newest
            context += f"{msg.author.display_name}: {msg.content}\n"

        response = get_ai_response("participate in the chat", str(context))

        # Send the response in chunks of 2000 characters or fewer
        for chunk in [response[i:i + 2000] for i in range(0, len(response), 2000)]:
            await message.channel.send(chunk)
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        await message.channel.send("I couldn't fetch the messages. Please try again later.")

    # Process commands if any are present
    await bot.process_commands(message)

# Run the bot using the token from the environment variables
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
