"""
LLM processing via Claude API.

Two layers:
  1. Per-article: neutral summary + separate Alan-lens opinion
  2. Weekly: opinionated synthesis digest across all articles
"""

import logging
from typing import Any

import anthropic

from . import config

logger = logging.getLogger(__name__)
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _call(system: str, user: str, max_tokens: int = 500) -> str:
    """Single Claude API call. Returns the text content."""
    resp = _get_client().messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


# ── Per-article processing ────────────────────────────────────────────────────

_SUMMARY_SYSTEM = """You are a scientific editor. Given a research article or news item,
write a concise, neutral factual summary (3–5 sentences).
- Report only what the source says; do not editorialize.
- Use plain language; avoid jargon where possible.
- If the abstract is thin, summarise what can be inferred from the title and context."""


_OPINION_SYSTEM = f"""You are a strategic analyst working for Alan, a French digital health insurance company.
{config.ALAN_CONTEXT}

Given a research article or news item and its neutral summary, write a short opinionated take (3–5 sentences):
- Is this relevant to Alan's mission? Why or why not?
- What opportunity or risk does it signal?
- Could a behavioral mechanism or product feature be derived from this?
- Be direct and specific. No generic observations.

Keep your opinion clearly separated from factual claims. Use first-person plural ("We think…", "This suggests…")."""


_TAG_SYSTEM = """You are a tagger. Given an article title and summary, return 3–5 comma-separated tags.
Tags must come from these categories:
  topics: epigenetics, senescence, behavior change, habit formation, gamification,
          nutrition, exercise, sleep, stress, biomarkers, wearables, gut microbiome,
          mental health, cognitive aging, longevity biotech, funding, AI in health,
          clinical trial, behavioral economics, prevention, digital therapeutics

Return ONLY the tags, comma-separated. No explanation."""


def process_article(article: dict[str, Any]) -> dict[str, Any]:
    """
    Enrich an article dict with:
      - summary: neutral factual summary
      - opinion: Alan-lens opinionated take
      - tags: list of topic tags
    """
    input_text = f"Title: {article['title']}\nSource: {article['publication']}\n\nContent:\n{article['abstract']}"

    try:
        summary = _call(_SUMMARY_SYSTEM, input_text, max_tokens=300)
    except Exception as exc:
        logger.warning("Summary failed for '%s': %s", article["title"][:60], exc)
        summary = article["abstract"][:500]

    try:
        opinion_input = f"{input_text}\n\nNeutral summary:\n{summary}"
        opinion = _call(_OPINION_SYSTEM, opinion_input, max_tokens=300)
    except Exception as exc:
        logger.warning("Opinion failed for '%s': %s", article["title"][:60], exc)
        opinion = ""

    try:
        tags_raw = _call(_TAG_SYSTEM, f"Title: {article['title']}\nSummary: {summary}", max_tokens=60)
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    except Exception as exc:
        logger.warning("Tagging failed for '%s': %s", article["title"][:60], exc)
        tags = []

    return {**article, "summary": summary, "opinion": opinion, "tags": tags}


# ── Weekly digest synthesis ───────────────────────────────────────────────────

_DIGEST_SYSTEM = f"""You are the editor of a weekly intelligence briefing on longevity science,
preventive health, behavioral psychology, gamification, and health-tech market signals.
Your audience is the leadership team at Alan, a French digital health insurer.

{config.ALAN_CONTEXT}

Structure your digest as follows (use markdown):

## Week at a Glance
2–3 sentence headline summary of the most important signal this week.

## Key Trends
3–5 bullet points on patterns across this week's sources.

## Alan Perspective
A frank, opinionated synthesis (5–8 sentences) on what this week means for Alan:
what to watch, what to act on, what to discard. Be specific. Name companies, papers,
or mechanisms when relevant.

## Top Picks by Domain
For each domain (Longevity Science / Behavioral Psychology / Market Intelligence),
list 2–3 standout items with one-line explanations.

Be direct. Avoid filler sentences. Use "We" for Alan's perspective."""


def generate_weekly_digest(processed_articles: list[dict[str, Any]]) -> str:
    """
    Generate the opinionated weekly digest from all processed articles.
    Returns a markdown string.
    """
    # Build a compact input: title + summary for each article, grouped by domain
    by_domain: dict[str, list[dict]] = {}
    for art in processed_articles:
        by_domain.setdefault(art["domain"], []).append(art)

    lines = []
    for domain, arts in by_domain.items():
        lines.append(f"\n### {domain.upper()}")
        for art in arts:
            lines.append(f"- **{art['title']}** ({art['publication']}, {art['date']})")
            lines.append(f"  Summary: {art.get('summary', art['abstract'])[:300]}")

    corpus = "\n".join(lines)
    prompt = f"Here are this week's sources:\n{corpus}\n\nGenerate the weekly digest."

    try:
        return _call(_DIGEST_SYSTEM, prompt, max_tokens=1200)
    except Exception as exc:
        logger.error("Digest generation failed: %s", exc)
        return f"Digest generation failed: {exc}\n\nSources processed: {len(processed_articles)}"
