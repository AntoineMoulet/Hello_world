"""Lesson 4 — Generator–Critic (reflection / evaluator-optimizer).  ⭐

THE pattern behind your colleague's app: one agent produces, another *challenges*
it, the first revises — looping until the critic approves or we hit a max number
of rounds. Nobody hardcoded "do 3 revisions"; the loop decides when to stop.

    generator -> critic (approve? + issues) -> generator revises -> ...

The critic returns a structured verdict so the LOOP CONDITION is reliable.

Run:  python lesson_4_generator_critic.py
"""

from pydantic import BaseModel
from typing import List

from common import client, ask, text_of, SMART

QUESTION = "My order arrived damaged. What are my options?"
MAX_ROUNDS = 3


class Verdict(BaseModel):
    approved: bool
    issues: List[str]   # what's still wrong; empty when approved


def critique(answer: str) -> Verdict:
    """The challenger. Scores the draft and lists concrete problems."""
    response = client.messages.parse(
        model=SMART,
        max_tokens=512,
        messages=[{"role": "user", "content": (
            "You are a strict support-quality reviewer. Review the customer reply "
            "below. Approve only if it is accurate, empathetic, and gives clear next "
            "steps. Otherwise list specific issues to fix.\n\n"
            f"Customer question: {QUESTION}\n\nReply to review:\n{answer}"
        )}],
        output_format=Verdict,
    )
    return response.parsed_output


def main():
    # Round 0: first draft.
    answer = ask(f"Answer this customer question:\n\n{QUESTION}")

    for round_num in range(1, MAX_ROUNDS + 1):
        verdict = critique(answer)
        print(f"--- round {round_num}: approved={verdict.approved} ---")
        for issue in verdict.issues:
            print("   • ", issue)

        if verdict.approved:                       # dynamic stop condition
            print("\nCritic approved. Final answer:\n", answer)
            return

        # Generator revises using the critic's feedback.
        feedback = "\n".join(f"- {i}" for i in verdict.issues)
        answer = ask(
            f"Improve this reply to the question '{QUESTION}'.\n\n"
            f"Reply:\n{answer}\n\nFix these issues:\n{feedback}"
        )

    print("\nHit max rounds. Best effort so far:\n", answer)


if __name__ == "__main__":
    main()
