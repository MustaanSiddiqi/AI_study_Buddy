import os
import importlib
from typing import Optional
from prompts import (
    SUMMARY_PROMPT,
    FLASHCARDS_PROMPT, QUIZ_PROMPT,
    FLASHCARDS_FROM_SUMMARY_PROMPT, QUIZ_FROM_SUMMARY_PROMPT
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is missing.")
    try:
        openai_mod = importlib.import_module("openai")
        OpenAI = getattr(openai_mod, "OpenAI")
        return OpenAI(api_key=key)
    except Exception as e:
        raise RuntimeError(f"OpenAI client init failed: {e}")

def call_openai(prompt: str, model: str = MODEL_NAME, temperature: float = 0.7) -> str:
    client = _get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

def generate_summary(topic: str) -> str:
    return call_openai(SUMMARY_PROMPT.format(topic=topic), temperature=0.4)

def generate_flashcards(topic: str, n: int = 10, summary: Optional[str] = None):
    if summary:
        prompt = FLASHCARDS_FROM_SUMMARY_PROMPT.format(summary=summary, n=n)
        temperature = 0.2
    else:
        prompt = FLASHCARDS_PROMPT.format(topic=topic, n=n)
        temperature = 0.5

    text = call_openai(prompt, temperature=temperature)
    cards, question, answer = [], None, None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif line.startswith("A:") and question:
            answer = line[2:].strip()
            cards.append({"question": question, "answer": answer})
            question, answer = None, None
        if len(cards) >= n:
            break
    return cards[:n]

def generate_quiz(topic: str, n: int = 10, summary: Optional[str] = None):
    if summary:
        prompt = QUIZ_FROM_SUMMARY_PROMPT.format(summary=summary, n=n)
        temperature = 0.2
    else:
        prompt = QUIZ_PROMPT.format(topic=topic, n=n)
        temperature = 0.5

    text = call_openai(prompt, temperature=temperature)
    quizzes, question, options, answer = [], None, [], None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif line.startswith("Options:"):
            opts_text = line[len("Options:"):].strip()
            tokens = opts_text.replace("A)", "|A)").replace("B)", "|B)").replace("C)", "|C)").replace("D)", "|D)").split("|")
            tokens = [t for t in tokens if t]
            options = []
            for t in tokens:
                t = t.strip()
                if len(t) >= 2 and t[1] == ")":
                    options.append(t[2:].strip())
                else:
                    options.append(t)
        elif line.startswith("Answer:") and question:
            answer = line[len("Answer:"):].strip()
            quizzes.append({"question": question, "options": options[:4], "answer": answer})
            question, options, answer = None, [], None
        if len(quizzes) >= n:
            break
    return quizzes[:n]
