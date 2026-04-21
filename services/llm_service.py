from groq import Groq
from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a helpful study assistant.
Answer the student's question using ONLY the notes provided below.
If the answer is not found in the notes, say exactly:
"I couldn't find that in your notes."
Be concise, clear, and helpful."""


def build_prompt(question: str, context_chunks: list[str]) -> str:
    """Combine retrieved chunks and question into a single prompt."""
    context = "\n\n---\n\n".join(context_chunks)
    return f"NOTES:\n{context}\n\nQUESTION: {question}"


def generate_answer(question: str, context_chunks: list[str]) -> str:
    """Send prompt to Groq LLM and return the answer."""
    user_prompt = build_prompt(question, context_chunks)

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content