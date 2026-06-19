"""Lesson 3 — Parallelization (voting flavor).

Run several calls AT ONCE, then combine them. Here we ask the same question three
times in parallel (each run varies a little), then a judge call picks the best
answer. This is the "quality via redundancy" idea — and it's faster than running
the calls one after another.

    [answer A]  [answer B]  [answer C]   (in parallel)
                    |
                 judge picks best

Run:  python lesson_3_parallelization.py
"""

from concurrent.futures import ThreadPoolExecutor

from common import ask, SMART

QUESTION = "My order arrived damaged. What are my options?"


def candidate(_):
    # Each call is independent, so they can run concurrently.
    return ask(f"Answer this customer question helpfully:\n\n{QUESTION}", model=SMART)


def main():
    # Fan out: three answers at the same time.
    with ThreadPoolExecutor(max_workers=3) as pool:
        answers = list(pool.map(candidate, range(3)))

    for i, a in enumerate(answers, 1):
        print(f"--- candidate {i} ---\n{a}\n")

    # Fan in: a judge call merges/selects the best.
    options = "\n\n".join(f"Option {i}:\n{a}" for i, a in enumerate(answers, 1))
    best = ask(
        "You are an editor. Pick the single best customer reply from the options "
        f"below and return it verbatim (no commentary).\n\n{options}",
        model=SMART,
    )
    print("--- judge's pick ---\n", best)


if __name__ == "__main__":
    main()
