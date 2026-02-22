"""
Configuration for the Longevity & Prevention Weekly Digest agent.
All secrets are read from environment variables.
"""

import os

# ── API keys ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")    # Sources table
NOTION_DIGEST_PARENT_ID = os.getenv("NOTION_DIGEST_PARENT_ID")  # Parent page for weekly digests

# ── Claude model ──────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"

# ── Fetch window ──────────────────────────────────────────────────────────────
LOOKBACK_DAYS = 7

# ── Alan context (injected into every opinion prompt) ────────────────────────
ALAN_CONTEXT = """
Alan is a French digital health insurance company. Its core thesis:
- Prevention is more valuable than treatment — use data and AI to keep people healthy
- Behavior change is the primary lever: habits, motivation, and environment design
- Scientific rigor matters; evidence beats anecdote
- Gamification and behavioral economics are underutilised in health insurance
- Long-term, Alan wants to know what makes people live longer and feel better,
  and embed that into its product (coaching, alerts, incentives, challenges)

When evaluating a source through the Alan lens, consider:
1. Does this create a product or research opportunity for Alan?
2. Does it validate or challenge Alan's current direction?
3. Is there a behavioral mechanism Alan could operationalise?
4. What is the competitive signal (other players, funding trends)?
"""

# ── PubMed queries ───────────────────────────────────────────────────────────
# Focused, non-generic — catches the intersection we care about
PUBMED_QUERIES = [
    "behavior change intervention longevity aging",
    "gamification physical activity adherence",
    "digital health habit formation prevention",
    "epigenetic clock lifestyle intervention",
    "senescence prevention physical activity",
    "behavioral economics preventive health",
    "wearable sensor health outcome aging",
]
PUBMED_MAX_RESULTS_PER_QUERY = 5

# ── bioRxiv / medRxiv ────────────────────────────────────────────────────────
BIORXIV_CATEGORIES = ["gerontology"]
MEDRXIV_CATEGORIES = ["health informatics", "primary care"]

# ── RSS feeds ─────────────────────────────────────────────────────────────────
# Chosen criteria: peer-reviewed or editorially rigorous, not mainstream press,
# directly relevant to longevity science / behavioral prevention / industry signals
RSS_FEEDS = [
    # ── Longevity science ─────────────────────────────────────────────────────
    {
        "url": "https://www.nature.com/nataging.rss",
        "publication": "Nature Aging",
        "domain": "longevity science",
    },
    {
        # Lancet's dedicated healthy-ageing sub-journal, fully open-access
        "url": "https://www.thelancet.com/rssfeed/lanhea_current.xml",
        "publication": "The Lancet Healthy Longevity",
        "domain": "longevity science",
    },
    {
        # Springer journal bridging geroscience and clinical practice
        "url": "https://link.springer.com/search.rss?query=aging+intervention&search-within=Journal&facet-journal-id=11357",
        "publication": "GeroScience",
        "domain": "longevity science",
    },
    {
        # SENS Foundation — highly technical, aging damage-repair framing
        "url": "https://www.sens.org/feed/",
        "publication": "SENS Research Foundation",
        "domain": "longevity science",
    },
    # ── Behavioral psychology & motivation ───────────────────────────────────
    {
        # Rigorous applied behavioral science, not pop-psych
        "url": "https://behavioralscientist.org/feed/",
        "publication": "Behavioral Scientist",
        "domain": "behavioral psychology",
    },
    {
        # Nesta's health evidence and innovation blog
        "url": "https://www.nesta.org.uk/feed/?category=health-and-care",
        "publication": "Nesta Health",
        "domain": "behavioral psychology",
    },
    {
        # ideas42 — behavioral design applied to real-world problems incl. health
        "url": "https://www.ideas42.org/feed/",
        "publication": "ideas42",
        "domain": "behavioral psychology",
    },
    # ── Longevity industry / market signals ──────────────────────────────────
    {
        # Lifespan.io — most rigorous dedicated longevity news outlet
        "url": "https://www.lifespan.io/feed/",
        "publication": "Lifespan.io",
        "domain": "market intelligence",
    },
    {
        # Fight Aging! — daily digest of longevity research and industry
        "url": "https://www.fightaging.org/feed/",
        "publication": "Fight Aging!",
        "domain": "market intelligence",
    },
    {
        # Dedicated longevity industry newsletter — funding, M&A, product launches
        "url": "https://longevity.technology/feed/",
        "publication": "Longevity Technology",
        "domain": "market intelligence",
    },
    {
        # AgingBiotech.info — curated tracker of aging biotech companies & trials
        "url": "https://agingbiotech.info/feed/",
        "publication": "AgingBiotech.info",
        "domain": "market intelligence",
    },
]

# ── Notion table property names ───────────────────────────────────────────────
# Adjust if your database uses different column names
NOTION_PROPS = {
    "title":      "Name",
    "date":       "Date",
    "publication":"Publication",
    "url":        "Source",
    "domain":     "Domain",
    "type":       "Type",
    "summary":    "Summary",
    "opinion":    "Alan Opinion",
    "week":       "Week",
    "tags":       "Tags",
}
