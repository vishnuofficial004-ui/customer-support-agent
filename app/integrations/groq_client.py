import os
from groq import Groq


def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Make sure app/.env is loaded or the environment variable is configured."
        )
    return Groq(api_key=api_key)


async def call_groq(prompt: str, temperature: float = 0.3) -> str:
    client = get_client()

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You must strictly follow instructions and output format. No creativity outside rules."
            },
            {"role": "user", "content": prompt}
        ],
        model=os.getenv("GROQ_MODEL"),
        temperature=temperature
    )

    return response.choices[0].message.content.strip()