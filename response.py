import os
import requests
from openai import OpenAI
import random

def get_system_message(url):
    """
    Fetch the system message from a URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        print(response.text.strip())
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error fetching system message from {url}: {str(e)}")
        return ""

def get_ai_response(prompt, context):
    # Get the system message URL from environment variables
    system_message_url = os.getenv("SYSTEM_MESSAGE_URL")
    if not system_message_url:
        return "System message URL is not set in the environment variables."

    system_message = get_system_message(system_message_url)
    if not system_message:
        return "System message could not be retrieved. Please check the URL or internet connection."

    client = OpenAI()
    temperature = round(random.uniform(0.8, 1.2), 2)
    top_p = round(random.uniform(0.7, 0.95), 2)
    frequency_penalty = round(random.uniform(0.1, 0.5), 2)
    presence_penalty = round(random.uniform(0.1, 0.5), 2)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": f"Hi agent, I'm moderator bot helper. Reply here, and I'll redirect your message to Discord. (Reposting your response as it).\nPrompt: {prompt}\nLast 5 chat messages: {context}"
                }
            ],
            # Hard-coded parameters
            temperature=temperature,
            max_tokens=16384,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        print("OpenAI API response:", response)  # Debugging

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in get_ai_response: {str(e)}")
        return "I couldn't process your request. Please try again later."
