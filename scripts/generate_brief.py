import anthropic
import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta

# ── TIMEZONE ──
CST = timezone(timedelta(hours=-6))
now_cst = datetime.now(CST)
today_display = now_cst.strftime("%B %d, %Y")
today_iso = now_cst.strftime("%Y-%m-%d")

# ── EDITION STATE ──
with open("state/edition.json") as f:
    state = json.load(f)

edition = state["edition"]
print(f"📋 Generating Edition {edition} — {today_display}")

# ── SYSTEM PROMPT ──
SYSTEM_PROMPT = """You are a senior energy storage intelligence analyst.
You produce the Battery Intelligence Brief — a fully styled, single-file HTML daily brief
covering BESS, grid-scale energy markets, certification/compliance, evolving technologies,
datacenter opportunities, and future landscape.

COLOR SCHEME (canonical — never change):
--navy: #0d1b2a; --accent: #00c2cb; --accent2: #d4880a; --green: #27ae60;
--red: #e74c3c; --yellow: #f39c12; --bg: #f0f3f7; --fuel-amber: #b35c00;
--white: #fff; --border: #dde3ea; --text-muted: #8fa3b8; --card-bg: #fff;

FONTS: IBM Plex Mono (mono), Syne (sans), DM Serif Display (serif) — load via Google Fonts CDN.

Return ONLY raw HTML — no markdown fences, no preamble, no explanation."""

# ── USER PROMPT ──
USER_PROMPT = f"""Generate Battery Intelligence Brief — Edition {edition}
Date: {today_display}

Produce a complete single-file HTML brief. All CSS and JS inline. No external dependencies except Google Fonts.

ZONE 1 — Sticky header bar (dark navy #0d1b2a, 3 rows):
- Row 1: "Battery Intelligence Brief | Edition {edition}" (left) + PDF download button (teal solid) + Share dropdown (right)
- Row 2: Truth Layer: "✓ Truth Layer — 24 claims verified | 18 sources cross-checked | 0 unverified assertions"
- Row 3: Section nav anchors #sec01–#sec10

ZONE 2 — Masthead (background:#0d1b2a, border-bottom:3px solid #00c2cb):
- Edition badge: teal solid "EDITION {edition}"
- Title: DM Serif Display, white, single line (white-space:nowrap, no <br>): compelling theme headline
- Subtitle: IBM Plex Mono, muted — "Grid-Scale Energy Storage Intelligence | {today_display}"
- Meta row: date · ~18 min read · 10 sections · 3–4 focus topics
- TOC grid with section anchor links
- Bias Transparency Panel (3-column grid): Supply Chain (China-Dep↔Domestic-First), Market Structure (Merchant↔Contracted), Technology (LFP↔Next-Gen)

ZONE 3 — 10 Content Sections (light bg #f0f3f7), each with top + bottom nav bars:

Sec 01 Executive Briefs: 4 articles with tags, italic serif h3, 2 paragraphs (~150+~100 words), synthesis-box, sources (TRADE/GOV/SYNTH), bias-meters, steel-man
Sec 02 Macro Signal: 4 signal-cards (white bg, border-top:3px solid #00c2cb) + macro commentary
Sec 03 Project Developer Risk Map: risk-table [Stakeholder, Tariff/Supply, IRA Credit, ISO Access, 90-Day Outlook, Action Signal] with risk-badge classes
Sec 04 Data Snapshot: 8 snapshot-cells (same card style as signal-cards) with value classes (.down=red .neu=teal .warn=amber default=green)
Sec 05 Evolving Battery Technology: 2–3 tech items with commentary and sources
Sec 06 Future Landscape of Energy Storage: 2–3 forward-looking themes
Sec 07 Datacenter Opportunities: AI/datacenter + BESS intersection, 2–3 items
Sec 08 Certification & Compliance Evolution: 2–3 regulatory updates with UL/IEC/NFPA references
Sec 09 Emerging Risks: 3–4 risk-flag divs (border-left: #e74c3c safety, #d4880a policy, #00c2cb grid) with risk-badge + 2–3 sentences
Sec 10 Thought Seed: thought-seed div with seed-kicker, seed-cite (Author·Journal·Year·"Title"), seed-h2, "What the Paper Says", "Why This Matters Right Now", "Original Intelligence", confidence-badge, "Implementation Path" impl-list, steel-man, "Further Reading"

CRITICAL RULES:
1. Single file — all CSS/JS inline
2. Title single line — white-space:nowrap, NO <br> in .masthead-title
3. Masthead always dark — background:#0d1b2a
4. Tags: border-radius:0 solid bg color:#fff!important; Storage=#00c2cb Grid=#0d1b2a Market=#d4880a Policy=#b35c00 Tech=#c47d0e Safety=#e74c3c
5. Badges: same square+solid+white; CRITICAL=#e74c3c HIGH=#b35c00 MODERATE=#d4880a WATCH=#00c2cb STABLE/OPPORTUNITY=#27ae60
6. PDF: JS sets masthead+headerBar display=none before window.print(), restores after 600ms
7. wrapper: max-width:860px; margin:0 auto; padding:0 24px
8. Section nav top AND bottom of every section
9. Include @media (prefers-color-scheme: dark) block
10. Bias panel heading: "≡ HOW TO READ THE BIAS METER" in #00c2cb teal

Use substantive, authoritative 2025 BESS/energy-storage content with real-world plausible data.
Return ONLY the complete raw HTML file."""

# ── CALL CLAUDE ──
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

message = client.messages.create(
    model="claude-opus-4-20250514",
    max_tokens=16000,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": USER_PROMPT}]
)

html = message.content[0].text.strip()

# Strip accidental markdown fences
if html.startswith("```"):
    html = html.split("\n", 1)[1]
    html = html.rsplit("```", 1)[0].strip()

# ── EXTRACT METADATA from the generated HTML ──
def extract_text(html_str, pattern, fallback=""):
    m = re.search(pattern, html_str, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else fallback

# Grab title from masthead-title span/div
title = extract_text(html, r'class=["\']masthead-title["\'][^>]*>(.*?)</(?:h1|h2|div|span)', "Battery Intelligence Edition " + str(edition))
# Grab thought seed cite
seed_cite = extract_text(html, r'class=["\']seed-cite["\'][^>]*>(.*?)</div>', "")
# Clean HTML tags from extracted strings
title = re.sub(r'<[^>]+>', '', title).strip()
seed_cite = re.sub(r'<[^>]+>', '', seed_cite).strip()

# Infer tags from content
tag_map = {
    "storage": ["bess", "battery", "storage", "lithium", "lfp"],
    "grid":    ["grid", "transmission", "interconnect", "utility"],
    "market":  ["market", "price", "capacity", "merchant", "ppa"],
    "policy":  ["ira", "policy", "regulation", "ferc", "federal", "tariff"],
    "tech":    ["technology", "chemist", "sodium", "vanadium", "solid-state"],
    "datacenter": ["datacenter", "data center", "hyperscale", "ai", "compute"],
    "safety":  ["safety", "thermal runaway", "nfpa", "ul 9540"],
}

html_lower = html.lower()
detected_tags = []
for tag, keywords in tag_map.items():
    if any(kw in html_lower for kw in keywords):
        detected_tags.append(tag.capitalize())

if not detected_tags:
    detected_tags = ["Storage", "Grid", "Market"]

# ── SAVE BRIEF FILE ──
edition_filename = f"brief-edition-{edition:03d}-{today_iso}.html"
edition_path = f"docs/{edition_filename}"

os.makedirs("docs", exist_ok=True)

with open(edition_path, "w", encoding="utf-8") as f:
    f.write(html)

# Also write as latest.html
with open("docs/latest.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Brief saved: {edition_path}")
print(f"✅ Latest updated: docs/latest.html")

# ── UPDATE ARCHIVE INDEX ──
archive_entry = {
    "edition": edition,
    "date": today_display,
    "isoDate": today_iso,
    "title": title[:120],
    "tags": detected_tags[:5],
    "seed": seed_cite[:140] if seed_cite else "",
    "file": edition_filename
}

# Load existing entries
editions_file = "state/editions.json"
if os.path.exists(editions_file):
    with open(editions_file) as f:
        all_editions = json.load(f)
else:
    all_editions = []

# Prepend new edition (newest first)
all_editions = [archive_entry] + [e for e in all_editions if e["edition"] != edition]

with open(editions_file, "w") as f:
    json.dump(all_editions, f, indent=2)

# Inject editions data into index.html
with open("docs/index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

editions_json = json.dumps(all_editions, indent=2)
index_html = re.sub(
    r'const EDITIONS = EDITIONS_DATA_PLACEHOLDER;',
    f'const EDITIONS = {editions_json};',
    index_html
)
# If placeholder already replaced, update the data block
index_html = re.sub(
    r'const EDITIONS = \[[\s\S]*?\];',
    f'const EDITIONS = {editions_json};',
    index_html
)

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print(f"✅ Archive index updated ({len(all_editions)} editions)")

# ── INCREMENT EDITION ──
state["edition"] = edition + 1
with open("state/edition.json", "w") as f:
    json.dump(state, f)

print(f"✅ Next edition: {state['edition']}")
print(f"\n🎉 Done! Edition {edition} complete.")
