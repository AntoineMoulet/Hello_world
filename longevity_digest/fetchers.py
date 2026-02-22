"""
Fetchers for all data sources.
Each fetcher returns a list of Article dicts:
  {
    "title":       str,
    "url":         str,
    "abstract":    str,   # best available text (abstract, snippet, or full intro)
    "date":        str,   # ISO 8601 date (YYYY-MM-DD)
    "publication": str,
    "domain":      str,   # longevity science | behavioral psychology | market intelligence
    "source_type": str,   # research paper | preprint | news | funding
  }
"""

import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
import requests

from . import config

logger = logging.getLogger(__name__)

# ── Shared helpers ────────────────────────────────────────────────────────────

def _cutoff_date() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)


def _parse_date(raw: str | None) -> str | None:
    """Try to parse a messy date string into YYYY-MM-DD. Returns None on failure."""
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%d",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw[:10]  # best-effort: take first 10 chars


def _within_window(date_str: str | None) -> bool:
    if not date_str:
        return True  # include if we can't determine
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt >= _cutoff_date()
    except ValueError:
        return True


# ── RSS feeds ─────────────────────────────────────────────────────────────────

def fetch_rss_feeds() -> list[dict[str, Any]]:
    """Fetch articles from all configured RSS feeds published in the last N days."""
    articles = []
    for feed_cfg in config.RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            logger.info("RSS %s — %d entries found", feed_cfg["publication"], len(feed.entries))
            for entry in feed.entries:
                # Date
                raw_date = (
                    entry.get("published")
                    or entry.get("updated")
                    or entry.get("dc_date")
                )
                date_str = _parse_date(raw_date)
                if not _within_window(date_str):
                    continue

                # Content — prefer summary > description > content
                abstract = (
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                )
                # Strip rudimentary HTML tags
                import re
                abstract = re.sub(r"<[^>]+>", " ", abstract).strip()
                abstract = abstract[:1500]  # cap for token budget

                articles.append({
                    "title":       entry.get("title", "(no title)").strip(),
                    "url":         entry.get("link", ""),
                    "abstract":    abstract,
                    "date":        date_str or "",
                    "publication": feed_cfg["publication"],
                    "domain":      feed_cfg["domain"],
                    "source_type": "news",
                })
        except Exception as exc:
            logger.warning("Failed to fetch RSS %s: %s", feed_cfg.get("url"), exc)

    logger.info("RSS total: %d articles within window", len(articles))
    return articles


# ── PubMed ────────────────────────────────────────────────────────────────────

_PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _pubmed_search(query: str, days: int, max_results: int) -> list[str]:
    """Return a list of PubMed IDs matching query within the last N days."""
    min_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    params = {
        "db":       "pubmed",
        "term":     query,
        "mindate":  min_date,
        "datetype": "pdat",
        "retmax":   max_results,
        "retmode":  "json",
        "usehistory": "n",
    }
    resp = requests.get(f"{_PUBMED_BASE}/esearch.fcgi", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])


def _pubmed_fetch(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch article metadata for a list of PubMed IDs."""
    if not pmids:
        return []
    params = {
        "db":      "pubmed",
        "id":      ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    resp = requests.get(f"{_PUBMED_BASE}/efetch.fcgi", params=params, timeout=20)
    resp.raise_for_status()

    articles = []
    root = ET.fromstring(resp.text)
    for article_el in root.findall(".//PubmedArticle"):
        try:
            # Title
            title_el = article_el.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else "(no title)"

            # Abstract
            abstract_texts = [
                "".join(el.itertext())
                for el in article_el.findall(".//AbstractText")
            ]
            abstract = " ".join(abstract_texts).strip()[:1500]

            # Date — prefer PubDate, fall back to ArticleDate
            year  = article_el.findtext(".//PubDate/Year") or article_el.findtext(".//ArticleDate/Year") or ""
            month = article_el.findtext(".//PubDate/Month") or article_el.findtext(".//ArticleDate/Month") or "01"
            day   = article_el.findtext(".//PubDate/Day") or article_el.findtext(".//ArticleDate/Day") or "01"
            # Month may be a 3-letter abbreviation
            try:
                month_num = datetime.strptime(month, "%b").month
                month = f"{month_num:02d}"
            except ValueError:
                month = month.zfill(2) if month.isdigit() else "01"
            date_str = f"{year}-{month}-{day.zfill(2)}" if year else ""

            # PMID → URL
            pmid = article_el.findtext(".//PMID") or ""
            url  = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            # Journal
            journal = article_el.findtext(".//Journal/Title") or "PubMed"

            articles.append({
                "title":       title,
                "url":         url,
                "abstract":    abstract,
                "date":        date_str,
                "publication": journal,
                "domain":      "longevity science",
                "source_type": "research paper",
            })
        except Exception as exc:
            logger.warning("PubMed parse error for article: %s", exc)

    return articles


def fetch_pubmed() -> list[dict[str, Any]]:
    """Run all configured queries against PubMed and deduplicate by URL."""
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []

    for query in config.PUBMED_QUERIES:
        try:
            pmids = _pubmed_search(query, config.LOOKBACK_DAYS, config.PUBMED_MAX_RESULTS_PER_QUERY)
            batch = _pubmed_fetch(pmids)
            for art in batch:
                if art["url"] not in seen_urls:
                    seen_urls.add(art["url"])
                    articles.append(art)
            time.sleep(0.4)  # NCBI rate limit: 3 req/s without API key
        except Exception as exc:
            logger.warning("PubMed query '%s' failed: %s", query, exc)

    logger.info("PubMed total: %d unique articles", len(articles))
    return articles


# ── bioRxiv / medRxiv ────────────────────────────────────────────────────────

def fetch_biorxiv(server: str = "biorxiv") -> list[dict[str, Any]]:
    """
    Fetch recent preprints from bioRxiv or medRxiv via their public API.
    server: 'biorxiv' | 'medrxiv'
    """
    end   = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=config.LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    url   = f"https://api.biorxiv.org/details/{server}/{start}/{end}/json"

    # Keywords to filter (the API returns everything; we filter client-side)
    keywords = [
        "aging", "longevity", "lifespan", "senescence",
        "behavior", "habit", "gamif", "prevention", "epigenetic",
    ]

    articles = []
    cursor = 0
    while True:
        try:
            resp = requests.get(f"{url}/{cursor}", timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("bioRxiv/medRxiv fetch error (cursor=%d): %s", cursor, exc)
            break

        collection = data.get("collection", [])
        if not collection:
            break

        for item in collection:
            combined = (item.get("title", "") + " " + item.get("abstract", "")).lower()
            if not any(kw in combined for kw in keywords):
                continue
            articles.append({
                "title":       item.get("title", "").strip(),
                "url":         f"https://doi.org/{item['doi']}" if item.get("doi") else "",
                "abstract":    item.get("abstract", "")[:1500],
                "date":        item.get("date", ""),
                "publication": server.capitalize(),
                "domain":      "longevity science",
                "source_type": "preprint",
            })

        messages = data.get("messages", [{}])
        total = int(messages[0].get("total", 0)) if messages else 0
        cursor += len(collection)
        if cursor >= total:
            break
        time.sleep(0.5)

    logger.info("%s total: %d filtered preprints", server, len(articles))
    return articles


# ── Public entry point ─────────────────────────────────────────────────────────

def fetch_all() -> list[dict[str, Any]]:
    """Fetch from all sources and return a deduplicated, time-windowed list."""
    articles: list[dict[str, Any]] = []
    articles += fetch_rss_feeds()
    articles += fetch_pubmed()
    articles += fetch_biorxiv("biorxiv")
    articles += fetch_biorxiv("medrxiv")

    # Deduplicate by URL (keep first occurrence)
    seen: set[str] = set()
    deduped = []
    for art in articles:
        key = art["url"] or art["title"]
        if key not in seen:
            seen.add(key)
            deduped.append(art)

    logger.info("Total after dedup: %d articles", len(deduped))
    return deduped
