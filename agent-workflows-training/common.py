"""Shared setup for every lesson.

Import the client and the model constants from here so each lesson stays focused
on the *pattern* it teaches rather than on boilerplate.
"""

import anthropic

# One client for everything. It reads ANTHROPIC_API_KEY from the environment.
client = anthropic.Anthropic()

# Cost-tiered models. See README for the rationale.
FAST = "claude-haiku-4-5"     # cheap, fast: classification and simple sub-steps
SMART = "claude-sonnet-4-6"   # the reasoning workhorse: drafting, critiquing
BEST = "claude-opus-4-8"      # swap SMART -> BEST for the hardest reasoning


def ask(prompt, model=SMART, system=None, max_tokens=1024):
    """Send one user message and return Claude's text reply.

    A thin convenience wrapper so the lessons read clearly. Real apps usually
    build the `messages` list themselves; we hide that here for readability.
    """
    kwargs = {"model": model, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if system is not None:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return text_of(response)


def text_of(response):
    """Pull the plain text out of a response (it's a list of content blocks)."""
    return "".join(block.text for block in response.content if block.type == "text")
