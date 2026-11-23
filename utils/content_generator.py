
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found. Check your .env file.")

# Configure Gemini with retry support
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=2,
            initial_delay=1.0,
            max_delay=5.0,
            http_status_codes=[408, 429, 500, 502, 503, 504]
        )
    )
)


def generate_content(topic, content_type, tone, length):

    prompt = f"""
    Act as a professional content writer.

    Generate a {content_type} about: {topic}

    Writing tone: {tone}
    Content length: {length}

    Requirements:
    1. Use clear and meaningful language.
    2. Organize the content with suitable headings.
    3. Include relevant information.
    4. Avoid unnecessary repetition.
    5. Make the content engaging and useful.
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text
