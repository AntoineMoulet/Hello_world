"""
Notion integration.

Two operations:
  1. add_article_row()  — creates one row in the Sources database
  2. create_digest_page() — creates a new page (child of NOTION_DIGEST_PARENT_ID)
                            with the full weekly digest as markdown blocks
"""

import logging
from datetime import datetime, timezone
from typing import Any

from notion_client import Client

from . import config

logger = logging.getLogger(__name__)
_notion: Client | None = None


def _get_client() -> Client:
    global _notion
    if _notion is None:
        _notion = Client(auth=config.NOTION_API_KEY)
    return _notion


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rich_text(text: str) -> list[dict]:
    """Wrap a plain string in a Notion rich_text block (2000-char limit per segment)."""
    chunks = [text[i : i + 2000] for i in range(0, len(text), 2000)]
    return [{"type": "text", "text": {"content": chunk}} for chunk in chunks]


def _multi_select(values: list[str]) -> list[dict]:
    return [{"name": v[:100]} for v in values]


def _current_week_start() -> str:
    """ISO date string for this week's Monday."""
    today = datetime.now(timezone.utc)
    monday = today - __import__("datetime").timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


def _paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text)},
    }


def _heading_block(text: str, level: int = 2) -> dict:
    htype = f"heading_{level}"
    return {
        "object": "block",
        "type": htype,
        htype: {"rich_text": _rich_text(text)},
    }


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def _divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _markdown_to_blocks(md: str) -> list[dict]:
    """
    Lightweight markdown → Notion blocks converter.
    Handles: ## headings, ### headings, - bullets, blank lines, plain text.
    Good enough for the digest format we generate.
    """
    blocks = []
    for line in md.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            blocks.append(_heading_block(stripped[3:], level=2))
        elif stripped.startswith("### "):
            blocks.append(_heading_block(stripped[4:], level=3))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append(_bullet_block(stripped[2:]))
        elif stripped.startswith("---"):
            blocks.append(_divider_block())
        else:
            blocks.append(_paragraph_block(stripped))
    return blocks


# ── Main operations ───────────────────────────────────────────────────────────

def add_article_row(article: dict[str, Any]) -> str | None:
    """
    Insert one article into the Notion sources database.
    Returns the created page ID, or None on failure.

    Expected article keys: title, url, date, publication, domain,
                           source_type, summary, opinion, tags
    """
    props = config.NOTION_PROPS
    notion = _get_client()

    properties: dict[str, Any] = {
        props["title"]: {
            "title": _rich_text(article.get("title", "(no title)")[:2000])
        },
        props["publication"]: {
            "select": {"name": article.get("publication", "Unknown")[:100]}
        },
        props["domain"]: {
            "select": {"name": article.get("domain", "other")[:100]}
        },
        props["type"]: {
            "select": {"name": article.get("source_type", "news")[:100]}
        },
        props["summary"]: {
            "rich_text": _rich_text(article.get("summary", "")[:2000])
        },
        props["opinion"]: {
            "rich_text": _rich_text(article.get("opinion", "")[:2000])
        },
        props["week"]: {
            "date": {"start": _current_week_start()}
        },
        props["tags"]: {
            "multi_select": _multi_select(article.get("tags", []))
        },
    }

    # Optional URL
    if article.get("url"):
        properties[props["url"]] = {"url": article["url"]}

    # Optional date
    if article.get("date"):
        properties[props["date"]] = {"date": {"start": article["date"]}}

    try:
        page = notion.pages.create(
            parent={"database_id": config.NOTION_DATABASE_ID},
            properties=properties,
        )
        return page["id"]
    except Exception as exc:
        logger.error("Failed to add Notion row for '%s': %s", article.get("title", "?")[:60], exc)
        return None


def create_digest_page(digest_md: str, article_count: int) -> str | None:
    """
    Create a weekly digest page in Notion under NOTION_DIGEST_PARENT_ID.
    Returns the created page ID, or None on failure.
    """
    notion = _get_client()
    week_label = _current_week_start()
    title = f"Longevity Digest — Week of {week_label} ({article_count} sources)"

    # Convert digest markdown to Notion blocks
    content_blocks = _markdown_to_blocks(digest_md)

    # Prepend metadata header
    header_blocks = [
        _heading_block(title, level=1),
        _paragraph_block(
            f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"{article_count} sources processed"
        ),
        _divider_block(),
    ]

    # Notion API: max 100 blocks per create call — chunk if needed
    all_blocks = header_blocks + content_blocks
    chunks = [all_blocks[i : i + 95] for i in range(0, len(all_blocks), 95)]

    try:
        page = notion.pages.create(
            parent={"page_id": config.NOTION_DIGEST_PARENT_ID},
            properties={
                "title": {
                    "title": _rich_text(title)
                }
            },
            children=chunks[0],
        )
        page_id = page["id"]

        # Append remaining chunks if any
        for chunk in chunks[1:]:
            notion.blocks.children.append(block_id=page_id, children=chunk)

        logger.info("Digest page created: %s", page_id)
        return page_id
    except Exception as exc:
        logger.error("Failed to create Notion digest page: %s", exc)
        return None
