"""Lesson 2 — Routing.

The first DYNAMIC pattern. A cheap model classifies the incoming question, and
the code routes it to a differently-prompted handler. The path is chosen at
runtime instead of being hardcoded.

    classify  ->  {billing | technical | other} handler

We use a structured output (a pydantic model) so the classifier returns a clean,
validated label instead of free text we'd have to parse.

Run:  python lesson_2_routing.py
"""

from pydantic import BaseModel
from typing import Literal

from common import client, ask, FAST, SMART

QUESTIONS = [
    "Why was I charged twice this month?",          # -> billing
    "The app crashes when I upload a photo.",        # -> technical
    "Do you ship to Canada?",                        # -> other
]

# Different system prompts make each branch behave like a specialist.
HANDLERS = {
    "billing":   "You are a billing specialist. Be precise about charges and refunds.",
    "technical": "You are a technical support engineer. Give clear troubleshooting steps.",
    "other":     "You are a friendly general support agent.",
}


class Route(BaseModel):
    category: Literal["billing", "technical", "other"]


def classify(question: str) -> str:
    """Use the FAST model + structured output to pick a branch."""
    response = client.messages.parse(
        model=FAST,
        max_tokens=128,
        messages=[{"role": "user",
                   "content": f"Classify this support question.\n\n{question}"}],
        output_format=Route,
    )
    return response.parsed_output.category


def main():
    for question in QUESTIONS:
        category = classify(question)                       # dynamic: which path?
        answer = ask(question, model=SMART, system=HANDLERS[category])
        print(f"[{category}] {question}")
        print("  ->", answer.replace("\n", " ")[:200], "...\n")


if __name__ == "__main__":
    main()
