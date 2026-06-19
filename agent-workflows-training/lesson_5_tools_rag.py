"""Lesson 5 — Tools & RAG (the "based on docs" part).

The agent is given a `search_docs` tool over the ./docs folder and decides, on its
own, when to call it before answering. This is how "agents make content based on
doc and code base" actually works: retrieve on demand, then ground the answer in
what came back.

We use the SDK's tool runner, which drives the whole loop for us:
    model wants tool -> SDK runs our function -> feeds result back -> repeat -> final answer

Run:  python lesson_5_tools_rag.py
"""

from pathlib import Path

import anthropic
from anthropic import beta_tool

from common import client, text_of, SMART

DOCS = Path(__file__).parent / "docs"
QUESTION = "My order arrived damaged and I think I was double-charged. What do I do?"


@beta_tool
def search_docs(query: str) -> str:
    """Search the support knowledge base for relevant policy text.

    Args:
        query: keywords describing what you need (e.g. "damaged item refund").
    """
    # A deliberately simple keyword search — enough to show the retrieval loop.
    # A real system would use embeddings / a vector store here.
    terms = [t for t in query.lower().split() if len(t) > 3]
    hits = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text()
        score = sum(text.lower().count(t) for t in terms)
        if score:
            hits.append((score, path.name, text))
    hits.sort(reverse=True)
    if not hits:
        return "No matching documents."
    return "\n\n".join(f"### {name}\n{text}" for _, name, text in hits[:2])


def main():
    runner = client.beta.messages.tool_runner(
        model=SMART,
        max_tokens=1024,
        tools=[search_docs],
        messages=[{"role": "user", "content": (
            "You are a support agent. Use search_docs to ground your answer in "
            f"policy before replying. Cite the policy you used.\n\n{QUESTION}"
        )}],
    )

    # Each iteration is one model turn; watch it decide to search, then answer.
    for message in runner:
        for block in message.content:
            if block.type == "text" and block.text.strip():
                print("ASSISTANT:", block.text)
            elif block.type == "tool_use":
                print(f"[calling {block.name}({block.input})]")


if __name__ == "__main__":
    main()
