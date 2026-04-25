# ⚡ Battery Intelligence Brief

Daily automated intelligence brief covering battery energy storage (BESS), grid-scale energy markets, certification/compliance, evolving technologies, datacenter opportunities, and future landscape.

**Live site:** `https://YOUR-USERNAME.github.io/battery-intelligence-brief/`

---

## How It Works

A GitHub Actions workflow runs every day at **7:00 AM CST**:

1. Calls the Claude API (`claude-opus-4-20250514`) with the full brief spec
2. Generates a complete single-file HTML brief
3. Saves it as `docs/brief-edition-NNN-YYYY-MM-DD.html`
4. Updates `docs/latest.html` with the newest edition
5. Injects the new edition card into `docs/index.html` (the archive page)
6. Commits and pushes — GitHub Pages auto-deploys within ~1 minute

---

## Repo Structure

```
├── .github/workflows/generate-brief.yml   ← Scheduled workflow (7AM CST daily)
├── scripts/generate_brief.py              ← Brief generator + archive updater
├── docs/
│   ├── index.html                         ← Archive page (GitHub Pages root)
│   ├── latest.html                        ← Always the most recent edition
│   └── brief-edition-NNN-YYYY-MM-DD.html ← Individual dated editions
└── state/
    ├── edition.json                       ← Current edition counter
    └── editions.json                      ← All edition metadata (auto-updated)
```

---

## Setup

### 1. Add your Anthropic API key

Go to **Settings → Secrets and variables → Actions → New repository secret**:
- Name: `ANTHROPIC_API_KEY`
- Value: your key from [console.anthropic.com](https://console.anthropic.com)

### 2. Enable GitHub Pages

Go to **Settings → Pages**:
- Source: `Deploy from a branch`
- Branch: `main`, Folder: `/docs`

### 3. Manual test run

Go to **Actions → Generate Battery Intelligence Brief → Run workflow**

---

## Cost

~$0.24/day using `claude-opus-4-20250514` (~16K output tokens per brief).  
Swap to `claude-sonnet-4-20250514` in `scripts/generate_brief.py` to reduce to ~$0.03/day.
# Battery-Intelligence-Briefing
