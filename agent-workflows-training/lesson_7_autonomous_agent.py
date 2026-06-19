"""Lesson 7 — Autonomous agent (capstone).

Everything combined into a small replica of your colleague's flow:
    research (tools, lesson 5) -> draft -> self-critique (lesson 4) -> loop

The agent uses a retrieval tool to ground itself, drafts an answer, a critic
challenges it, and the agent re-researches/revises until the critic approves or
we hit a round cap. No fixed step count anywhere — the loop drives itself.

Run:  python lesson_7_autonomous_agent.py
"""

from pathlib import Path
from typing import List

from anthropic import beta_tool
from pydantic import BaseModel

from common import client, text_of, SMART

DOCS = Path(__file__).parent / "docs"
QUESTION = "My order arrived damaged and I think I was double-charged. What do I do?"
MAX_ROUNDS = 3


@beta_tool
def search_docs(query: str) -> str:
    """Search the support knowledge base for relevant policy text.

    Args:
        query: keywords describing what you need.
    """
    terms = [t for t in query.lower().split() if len(t) > 3]
    hits = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text()
        score = sum(text.lower().count(t) for t in terms)
        if score:
            hits.append((score, path.name, text))
    hits.sort(reverse=True)
    return "\n\n".join(f"### {n}\n{t}" for _, n, t in hits[:2]) or "No matching documents."


class Verdict(BaseModel):
    approved: bool
    issues: List[str]


def research_and_draft(instructions: str) -> str:
    """Run a tool-using agent (lesson 5) and return its final text answer."""
    runner = client.beta.messages.tool_runner(
        model=SMART,
        max_tokens=1024,
        tools=[search_docs],
        messages=[{"role": "user", "content": (
            "You are a support agent. Use search_docs to ground your answer in "
            f"policy, then reply.\n\n{instructions}"
        )}],
    )
    final = ""
    for message in runner:
        for block in message.content:
            if block.type == "text" and block.text.strip():
                final = block.text
    return final


def critique(answer: str) -> Verdict:
    """The challenger (lesson 4)."""
    response = client.messages.parse(
        model=SMART,
        max_tokens=512,
        messages=[{"role": "user", "content": (
            "Strictly review this support reply for accuracy, empathy, and clear "
            "next steps. Approve only if it fully addresses BOTH the damage and the "
            f"double-charge.\n\nQuestion: {QUESTION}\n\nReply:\n{answer}"
        )}],
        output_format=Verdict,
    )
    return response.parsed_output


def main():
    instructions = QUESTION
    answer = research_and_draft(instructions)

    for round_num in range(1, MAX_ROUNDS + 1):
        verdict = critique(answer)
        print(f"--- round {round_num}: approved={verdict.approved} ---")
        for issue in verdict.issues:
            print("   • ", issue)

        if verdict.approved:
            print("\nApproved. Final answer:\n", answer)
            return

        # Feed the critique back in and let the agent re-research + revise.
        instructions = (
            f"{QUESTION}\n\nYour previous reply had these problems — fix them, "
            "searching the docs again if needed:\n"
            + "\n".join(f"- {i}" for i in verdict.issues)
            + f"\n\nPrevious reply:\n{answer}"
        )
        answer = research_and_draft(instructions)

    print("\nHit max rounds. Best effort:\n", answer)


if __name__ == "__main__":
    main()
