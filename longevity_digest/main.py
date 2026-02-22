"""
Longevity & Prevention Weekly Digest — main orchestrator.

Run manually:  python -m longevity_digest.main
Scheduled:     GitHub Actions every Monday 07:00 UTC (see .github/workflows/weekly_digest.yml)

Flow:
  1. Fetch all articles from configured sources (past 7 days)
  2. Process each article with Claude: neutral summary + Alan-lens opinion + tags
  3. Push each article to the Notion sources database
  4. Generate the opinionated weekly digest with Claude
  5. Create the weekly digest page in Notion
"""

import logging
import sys
import time
from datetime import datetime, timezone

from . import config, fetchers, processor, notion_client as nc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _validate_config() -> None:
    missing = [
        name
        for name, val in {
            "ANTHROPIC_API_KEY":    config.ANTHROPIC_API_KEY,
            "NOTION_API_KEY":       config.NOTION_API_KEY,
            "NOTION_DATABASE_ID":   config.NOTION_DATABASE_ID,
            "NOTION_DIGEST_PARENT_ID": config.NOTION_DIGEST_PARENT_ID,
        }.items()
        if not val
    ]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)


def run() -> None:
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Longevity Digest — %s", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    logger.info("=" * 60)

    _validate_config()

    # ── Step 1: Fetch ─────────────────────────────────────────────────────────
    logger.info("Step 1/4 — Fetching articles from all sources…")
    articles = fetchers.fetch_all()
    if not articles:
        logger.warning("No articles fetched. Exiting.")
        return
    logger.info("Fetched %d articles total.", len(articles))

    # ── Step 2: Process each article ─────────────────────────────────────────
    logger.info("Step 2/4 — Processing articles with Claude (%d articles)…", len(articles))
    processed = []
    for i, article in enumerate(articles, 1):
        logger.info("  [%d/%d] %s", i, len(articles), article["title"][:70])
        enriched = processor.process_article(article)
        processed.append(enriched)
        time.sleep(0.3)  # be gentle with the Claude API

    # ── Step 3: Push to Notion sources table ──────────────────────────────────
    logger.info("Step 3/4 — Pushing %d rows to Notion sources database…", len(processed))
    success_count = 0
    for article in processed:
        page_id = nc.add_article_row(article)
        if page_id:
            success_count += 1
        time.sleep(0.2)  # Notion API rate limit: 3 req/s
    logger.info("  %d/%d rows created in Notion.", success_count, len(processed))

    # ── Step 4: Generate & publish weekly digest ──────────────────────────────
    logger.info("Step 4/4 — Generating weekly digest…")
    digest_md = processor.generate_weekly_digest(processed)

    digest_page_id = nc.create_digest_page(digest_md, article_count=len(processed))
    if digest_page_id:
        logger.info("Digest page created: https://notion.so/%s", digest_page_id.replace("-", ""))
    else:
        logger.error("Digest page creation failed.")
        # Still print to stdout so CI logs capture it
        print("\n" + "=" * 60)
        print("WEEKLY DIGEST (fallback — Notion push failed)")
        print("=" * 60)
        print(digest_md)

    elapsed = time.time() - start_time
    logger.info("Done in %.1fs — %d articles processed.", elapsed, len(processed))


if __name__ == "__main__":
    run()
