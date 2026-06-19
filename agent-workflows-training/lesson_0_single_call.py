"""Lesson 0 — Single call (the baseline).

One prompt in, one answer out. This is NOT a workflow yet — it's the control
group. Every later lesson is "what do I add to this?"

Run:  python lesson_0_single_call.py
"""

from common import ask

QUESTION = "My order arrived damaged. What are my options?"


def main():
    answer = ask(QUESTION)
    print("Q:", QUESTION)
    print("\nA:", answer)


if __name__ == "__main__":
    main()
