"""Lesson 1 — Prompt chaining.

A FIXED sequence of calls where each step's output feeds the next. This is still
*static* (the steps never change), but it introduces the core idea of "steps" and
of a gate that can stop the chain early.

    draft  ->  warmer tone  ->  shorten to 3 sentences

Run:  python lesson_1_prompt_chaining.py
"""

from common import ask

QUESTION = "My order arrived damaged. What are my options?"


def main():
    # Step 1: a plain first draft.
    draft = ask(f"Answer this customer question:\n\n{QUESTION}")
    print("--- Step 1: draft ---\n", draft)

    # A GATE: a tiny bit of dynamic control. If step 1 produced nothing, stop.
    if not draft.strip():
        print("\nDraft was empty — stopping the chain.")
        return

    # Step 2: rewrite the draft in a friendlier tone.
    friendly = ask(f"Rewrite this in a warm, friendly tone:\n\n{draft}")
    print("\n--- Step 2: friendlier ---\n", friendly)

    # Step 3: compress to exactly three sentences.
    short = ask(f"Shorten this to exactly 3 sentences, keeping the key info:\n\n{friendly}")
    print("\n--- Step 3: shortened ---\n", short)


if __name__ == "__main__":
    main()
