# app/services/grok_client.py

import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def generate_grok_reply(message: str, language: str = "English") -> str:
    """
    Generates AI reply using Groq in the user's preferred language
    """

    try:
        prompt = f"""
        You are a helpful showroom assistant.

        Always reply in this language: {language}

        Customer message: {message}
        """

        response = client.chat.completions.create(
            model="llama3-8b-8192",  # fast + good enough
            messages=[
                {"role": "system", "content": "You are a smart retail showroom assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq Error: {e}")
        return "Sorry, something went wrong. Please try again."