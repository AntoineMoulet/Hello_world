# Longevity & Prevention Weekly Digest — Setup

## What it does

Every Monday at 07:00 UTC the agent:
1. Pulls articles from 12 curated sources (past 7 days)
2. For each article: writes a **neutral summary** and a separate **Alan-lens opinion**
3. Pushes every article as a row to a **Notion database**
4. Generates an **opinionated weekly digest** and creates it as a Notion page

---

## Source selection rationale

Chosen for scientific rigour and low mainstream noise:

| Source | Domain | Why |
|---|---|---|
| Nature Aging | Longevity science | Highest-impact peer-reviewed aging journal |
| The Lancet Healthy Longevity | Longevity science | Open-access clinical evidence on healthy aging |
| GeroScience | Longevity science | Bridges aging biology and medicine |
| SENS Research Foundation | Longevity science | Damage-repair framing, very technical |
| PubMed (7 targeted queries) | Longevity science | Peer-reviewed source of record |
| bioRxiv / medRxiv | Longevity science | Preprints — catches findings 6–12 months before journals |
| Behavioral Scientist | Behavioral psychology | Rigorous applied behavioral science, not pop-psych |
| Nesta Health | Behavioral psychology | Policy-grade behavioral insights in health |
| ideas42 | Behavioral psychology | Behavioral design for real-world problems |
| Lifespan.io | Market intelligence | Most rigorous dedicated longevity news outlet |
| Fight Aging! | Market intelligence | Daily digest of research + industry, very active |
| Longevity Technology | Market intelligence | Funding, M&A, product launches |
| AgingBiotech.info | Market intelligence | Curated tracker of aging biotech companies and trials |

---

## Notion setup

### 1 — Create the Sources database

Create a full-page Notion database with these properties:

| Property name | Type |
|---|---|
| Name | Title |
| Date | Date |
| Publication | Select |
| Source | URL |
| Domain | Select |
| Type | Select |
| Summary | Text |
| Alan Opinion | Text |
| Week | Date |
| Tags | Multi-select |

### 2 — Create the Digest parent page

Create an empty Notion page. Weekly digest sub-pages will be created inside it.

### 3 — Create a Notion integration

1. Go to https://www.notion.so/my-integrations
2. Create a new integration → copy the **Internal Integration Token**
3. Share both the database and the digest parent page with the integration

---

## GitHub setup

Add these four **repository secrets** (Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `NOTION_API_KEY` | Your Notion integration token |
| `NOTION_DATABASE_ID` | ID from your sources database URL |
| `NOTION_DIGEST_PARENT_ID` | ID from your digest parent page URL |

---

## Local run

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# fill in .env with your keys

export $(cat .env | xargs)

# Run
python -m longevity_digest.main
```

---

## Customisation

- **Add/remove sources** — edit `RSS_FEEDS` and `PUBMED_QUERIES` in `config.py`
- **Change lookback window** — edit `LOOKBACK_DAYS` in `config.py`
- **Change Alan context** — edit `ALAN_CONTEXT` in `config.py`
- **Change schedule** — edit the cron expression in `.github/workflows/weekly_digest.yml`
- **Change Notion column names** — edit `NOTION_PROPS` in `config.py`
