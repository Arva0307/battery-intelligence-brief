#!/bin/bash

# ── CONFIG ──
REPO="$HOME/Downloads/battery-brief-repo"
BRIEF_SRC="$HOME/Downloads/latest-brief.html"
DOCS="$REPO/docs"
STATE="$REPO/state"

# ── CHECK brief file exists ──
if [ ! -f "$BRIEF_SRC" ]; then
  echo "❌ Error: $BRIEF_SRC not found. Save the brief as latest-brief.html in your Downloads first."
  exit 1
fi

cd "$REPO"

# ── READ current edition number ──
EDITION=$(python3 -c "import json; print(json.load(open('$STATE/edition.json'))['edition'])")
TODAY_DISPLAY=$(date +'%B %d, %Y')
TODAY_ISO=$(date +'%Y-%m-%d')
EDITION_FILE="brief-edition-$(printf '%03d' $EDITION)-$TODAY_ISO.html"

echo "📋 Processing Edition $EDITION — $TODAY_DISPLAY"

# ── COPY brief files ──
cp "$BRIEF_SRC" "$DOCS/latest.html"
cp "$BRIEF_SRC" "$DOCS/$EDITION_FILE"
echo "✅ Brief saved as latest.html and $EDITION_FILE"

# ── DO EVERYTHING ELSE IN ONE PYTHON SCRIPT ──
python3 << PYEOF
import json, re, os

DOCS = "$DOCS"
STATE = "$STATE"
EDITION = $EDITION
TODAY_DISPLAY = "$TODAY_DISPLAY"
TODAY_ISO = "$TODAY_ISO"
EDITION_FILE = "$EDITION_FILE"

html = open(os.path.join(DOCS, 'latest.html')).read()
html_lower = html.lower()

# Extract title
m = re.search(r'class=["\']masthead-title["\'][^>]*>(.*?)</', html, re.DOTALL)
title = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:120] if m else f'Battery Intelligence Brief Edition {EDITION}'
print(f"📰 Title: {title}")

# Detect tags
tag_map = {
    'Storage':    ['bess','battery','storage','lithium','lfp'],
    'Grid':       ['grid','transmission','interconnect','utility'],
    'Market':     ['market','price','capacity','merchant','ppa'],
    'Policy':     ['ira','policy','regulation','ferc','tariff'],
    'Tech':       ['technology','sodium','vanadium','solid-state'],
    'Datacenter': ['datacenter','data center','hyperscale'],
    'Safety':     ['safety','thermal runaway','nfpa','ul 9540'],
    'Macro':      ['treasury','inflation','interest rate','macro'],
}
tags = [t for t, kws in tag_map.items() if any(k in html_lower for k in kws)][:5]
if not tags:
    tags = ['Storage', 'Grid', 'Market']

# Extract thought seed
m2 = re.search(r'class=["\']seed-cite["\'][^>]*>(.*?)</div>', html, re.DOTALL)
seed = re.sub(r'<[^>]+>', '', m2.group(1)).strip()[:140] if m2 else ''

# Extract signal from signal cards
cards = re.findall(r'class=["\']value["\'][^>]*>(.*?)</div>.*?class=["\']sub["\'][^>]*>(.*?)</div>', html, re.DOTALL)
parts = []
for v, s in cards[:3]:
    v2 = re.sub(r'<[^>]+>', '', v).strip()
    s2 = re.sub(r'<[^>]+>', '', s).strip().split('·')[0].strip()
    parts.append(v2 + ' ' + s2)
signal = ' x '.join(parts)[:160]

# Load existing editions
editions_file = os.path.join(STATE, 'editions.json')
existing = json.load(open(editions_file)) if os.path.exists(editions_file) else []
existing = [e for e in existing if e.get('edition') != EDITION]

new_entry = {
    'edition': EDITION,
    'date': TODAY_DISPLAY,
    'isoDate': TODAY_ISO,
    'title': title,
    'tags': tags,
    'seed': seed,
    'signal': signal,
    'file': EDITION_FILE
}

all_editions = [new_entry] + existing

# Save editions.json
with open(editions_file, 'w') as f:
    json.dump(all_editions, f, indent=2)
print(f"✅ editions.json updated ({len(all_editions)} edition(s))")

# Inject into index.html using lambda to avoid regex escape issues
index_path = os.path.join(DOCS, 'index.html')
index_html = open(index_path).read()
editions_js = 'const EDITIONS = ' + json.dumps(all_editions, indent=2) + ';'
index_html = re.sub(r'const EDITIONS = \[[\s\S]*?\];', lambda m: editions_js, index_html)
with open(index_path, 'w') as f:
    f.write(index_html)
print(f"✅ index.html updated with {len(all_editions)} edition(s)")
PYEOF

# ── INCREMENT edition counter ──
python3 -c "
import json
with open('$STATE/edition.json') as f:
    s = json.load(f)
s['edition'] = s['edition'] + 1
with open('$STATE/edition.json', 'w') as f:
    json.dump(s, f)
print('✅ Next edition will be:', s['edition'])
"

# ── GIT COMMIT & PUSH ──
git add docs/ state/
git diff --cached --quiet && echo "⚠️ No changes to commit" || git commit -m "Brief Edition $EDITION — $TODAY_ISO"
git push origin main

echo ""
echo "🎉 Done! Edition $EDITION is live."
echo "🔗 https://Arva0307.github.io/battery-intelligence-brief/"
