import os
from groq import Groq


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


async def call_groq(prompt: str) -> str:
    client = get_client()

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=os.getenv("GROQ_MODEL")
    )

    return response.choices[0].message.content.strip()