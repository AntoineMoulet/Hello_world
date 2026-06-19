"""Lesson 6 — Orchestrator–workers.

The most "dynamic" of the structured patterns: a lead agent breaks a goal into
subtasks AT RUNTIME (the number and shape aren't known in advance), dispatches a
worker per subtask, then synthesizes the results.

    orchestrator -> [subtask 1, subtask 2, ...]  (decided at runtime)
                       worker  worker  ...        (run in parallel)
                            synthesize

Goal: write release notes from a list of merged changes. Different input would
produce a different number of workers.

Run:  python lesson_6_orchestrator_workers.py
"""

from concurrent.futures import ThreadPoolExecutor
from typing import List

from pydantic import BaseModel

from common import client, ask, FAST, SMART

CHANGES = [
    "Added dark mode to the settings page",
    "Fixed a crash when uploading photos over 10MB",
    "Sped up search by caching recent queries",
]


class Plan(BaseModel):
    subtasks: List[str]   # one writing task per feature, decided by the model


def orchestrate(changes: List[str]) -> List[str]:
    """The lead agent decides how to split the work."""
    response = client.messages.parse(
        model=SMART,
        max_tokens=512,
        messages=[{"role": "user", "content": (
            "You are writing release notes. Break the work into one short writing "
            "subtask per change below. Return the subtasks.\n\n- "
            + "\n- ".join(changes)
        )}],
        output_format=Plan,
    )
    return response.parsed_output.subtasks


def worker(subtask: str) -> str:
    """A specialist that completes one subtask."""
    return ask(f"Write one polished release-note bullet for: {subtask}", model=FAST)


def main():
    subtasks = orchestrate(CHANGES)                 # dynamic: how many workers?
    print(f"Orchestrator created {len(subtasks)} subtasks.\n")

    with ThreadPoolExecutor(max_workers=len(subtasks)) as pool:
        bullets = list(pool.map(worker, subtasks))

    # Synthesize the workers' output into one deliverable.
    notes = ask(
        "Combine these bullets into clean release notes with a one-line intro:\n\n"
        + "\n".join(bullets),
        model=SMART,
    )
    print("--- release notes ---\n", notes)


if __name__ == "__main__":
    main()
