---
name: scrape-steamcharts
description: >
  Scrapes monthly CCU (concurrent users) history for Steam games from SteamCharts.com
  using playwright-cli, then merges the results into backend/data/steamcharts_history.json
  and resets the MongoDB seed so the data is immediately live. Use this skill whenever
  the user wants to add new games, refresh existing CCU data, update the comparison chart,
  or says anything like "scrape", "爬数据", "update game data", "add game [name/id]",
  "refresh steamcharts", or "更多游戏".
---

# SteamCharts CCU Scraper

Scrapes one or more games from SteamCharts, merges into the project data file, and
re-seeds MongoDB — so the Compare page and GameDetail charts update immediately.

## Quick start

```
/scrape-steamcharts [appid1 appid2 ...]
```

If no AppIDs are given, scrape the full **default game list** below. If AppIDs are
provided as arguments, scrape only those (and still merge with existing data).

---

## Default game list

| AppID   | Name                   |
|---------|------------------------|
| 730     | Counter-Strike 2       |
| 570     | Dota 2                 |
| 578080  | PUBG                   |
| 271590  | GTA V                  |
| 252490  | Rust                   |
| 1172470 | Apex Legends           |
| 440     | Team Fortress 2        |
| 1086940 | Baldur's Gate 3        |
| 1245620 | Elden Ring             |
| 2399830 | Helldivers 2           |
| 1091500 | Cyberpunk 2077         |
| 252950  | Rocket League          |
| 1599340 | Lost Ark               |
| 381210  | Dead by Daylight       |
| 550     | Left 4 Dead 2          |
| 346110  | ARK: Survival Evolved  |
| 359550  | Rainbow Six Siege      |

---

## Step-by-step workflow

### 1  Resolve playwright-cli path

```bash
which playwright-cli 2>/dev/null || ls ~/.nvm/versions/node/*/bin/playwright-cli 2>/dev/null | tail -1
```

If missing, install globally: `npm install -g @anthropic-ai/playwright-cli`

### 2  Open browser

```bash
playwright-cli open
```

### 3  Scrape each target AppID

For every AppID run these two commands:

**Navigate:**
```bash
playwright-cli goto https://steamcharts.com/app/APP_ID
```

**Extract table** (try selector `#main-chart-data tr` first; fall back to `table.common-table tr`):
```bash
playwright-cli --raw eval "
(() => {
  const rows = Array.from(
    document.querySelectorAll('#main-chart-data tr, table.common-table tr')
  );
  return rows.slice(1).map(tr => {
    const c = tr.querySelectorAll('td');
    return {
      month:       c[0]?.textContent.trim(),
      avg_players: parseFloat(c[1]?.textContent.replace(/,/g,'')) || 0,
      gain_pct:    c[2]?.textContent.trim() || '-',
      peak_players:parseFloat(c[3]?.textContent.replace(/,/g,'')) || 0,
    };
  }).filter(r => r.month && r.month.match(/[A-Za-z]+ \d{4}/));
})()"
```

**Get game name:**
```bash
playwright-cli --raw eval "
document.querySelector('h1.title')?.textContent.trim() ||
document.querySelector('h1')?.textContent.trim() ||
document.title.split(' App ')[0].trim()
"
```

If the table returns 0 rows (blank page / rate-limit), wait 3 seconds and retry once.
If it still fails, skip this AppID and continue.

### 4  Accumulate results in memory

Build a Python dict as you go:

```python
new_data = {
  "730": {
    "appid": "730",
    "name":  "Counter-Strike 2",
    "history": [                          # newest → oldest, as returned by the table
      {"month": "April 2026", "avg_players": 974785.7,
       "peak_players": 1564830.0, "gain_pct": "-8.83%"},
      ...
    ]
  },
  ...
}
```

### 5  Merge and save

Use the bundled helper script — it loads the existing file, merges by AppID
(new data overwrites old for the same AppID), and writes back:

```bash
python3 .claude/skills/scrape-steamcharts/scripts/merge_save.py \
  --data-file backend/data/steamcharts_history.json \
  --new-data  /tmp/scraped.json
```

Or inline in Python:

```python
import json, pathlib

DATA_FILE = pathlib.Path("backend/data/steamcharts_history.json")
existing  = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
existing.update(new_data)
DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✓ Saved {len(existing)} games → {DATA_FILE}")
```

### 6  Close browser

```bash
playwright-cli close
```

### 7  Reset MongoDB and reseed

The seeder skips if data already exists. Drop steamcharts_monthly records so the
next backend start re-imports the fresh JSON:

```bash
python3 -c "
from pymongo import MongoClient
db = MongoClient('mongodb://127.0.0.1:27017')['steam_hot_games']
n = db['ccu_timeseries'].delete_many({'source': 'steamcharts_monthly'}).deleted_count
print(f'Deleted {n} old records')
"
```

Then restart the backend (it will auto-seed on startup):

```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
```

### 8  Verify

```bash
curl -s "http://127.0.0.1:8000/api/compare?ids=730,1086940" | \
  python3 -c "import json,sys; [print(g['name'], len(g['history']), 'months') for g in json.load(sys.stdin)]"
```

---

## Tips

- Add `time.sleep(2)` between games if SteamCharts returns blank pages (rate limiting).
- All AppIDs in `TARGET_APP_IDS` (see `backend/.env`) are fair game to scrape.
- After adding new AppIDs, also add them to `GAME_LIST` in
  `frontend/src/views/Compare.vue` so they appear in the UI.
- The `gain_pct` field is display-only; the charts use `avg_players` and `peak_players`.
