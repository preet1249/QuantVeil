# QuantVeil — Market Intelligence Platform

Turn any company URL into a full intelligence report in minutes. QuantVeil extracts contacts, scrapes Reddit sentiment, checks GitHub activity, pulls Crunchbase funding data, fetches Google News & HN mentions, and generates an AI-powered SWOT analysis — all through a clean web UI with PDF and PPTX export.

---

## What It Does

| Module | What you get |
|---|---|
| **Website Scan** | Detects CMS, analytics, e-commerce, marketing stack |
| **Contact Intelligence** | Emails, phone numbers, social profiles from homepage + sub-pages |
| **Reddit Pulse** | Community sentiment, top posts, AI summary across subreddits |
| **Google News + HN** | Recent coverage, Hacker News mentions with point scores |
| **GitHub Activity** | Open-source repos, hiring signals, top languages |
| **Crunchbase** | Funding rounds, investors, employee count |
| **Wayback Machine** | Page-size growth trend over 12 months |
| **AI SWOT Analysis** | GPT-quality report: Snapshot, SWOT, Competitive Landscape, Outreach Angle |
| **Export** | Download as PDF report or PowerPoint slides (7-slide deck) |

---

## Prerequisites

Install these before anything else:

| Tool | Version | Download |
|---|---|---|
| Python | 3.11+ | https://python.org/downloads |
| Node.js | 18+ | https://nodejs.org |
| Git | any | https://git-scm.com |

**Optional (for Cloudflare bypass):**
- [Tor Browser](https://www.torproject.org/download/) — run it in background, QuantVeil auto-detects SOCKS5 on port 9150

---

## Installation — Step by Step

### 1. Clone the repo

```bash
git clone https://github.com/preet1249/QuantVeil.git
cd QuantVeil
```

### 2. Set up Python environment

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `curl_cffi` — Chrome TLS fingerprint spoofing (bypasses basic bot detection)
- `DrissionPage` — real Chrome automation (bypasses Cloudflare)
- `beautifulsoup4 + lxml` — HTML parsing
- `openai` — OpenRouter API client for AI analysis
- `flask` — web server
- `python-dotenv` — reads `.env` file
- `reportlab` — PDF generation
- `python-pptx` — PowerPoint generation
- `requests` — HTTP client for news/GitHub/Crunchbase

### 4. Install Node.js frontend dependencies

```bash
cd frontend
npm install
```

### 5. Build the React frontend

```bash
# Still inside frontend/
npm run build
cd ..
```

This creates `frontend/dist/` — the static files Flask will serve.

> **Rebuilding after UI changes:** Run `npm run build` in the `frontend/` folder again any time you edit the React source.

---

## Configuration

### Create your `.env` file

Copy the example and fill in your API key:

```bash
cp .env.example .env
```

Open `.env` and edit:

```env
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=nvidia/nemotron-3-super-120b-a12b:free
```

### Get a free OpenRouter API key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up (free)
3. Create an API key under **Keys**
4. Paste it into `.env` as `OPENROUTER_API_KEY`

> The default model `nvidia/nemotron-3-super-120b-a12b:free` is completely free — no credit card needed. You can change `LLM_MODEL` to any OpenRouter model ID.

---

## Running the App

```bash
# From the project root
python backend/web_app.py
```

Then open your browser at:

```
http://localhost:5001
```

You should see the QuantVeil hero screen. Paste any company URL and click **Analyze**.

---

## Optional Enhancements

### Tor Browser (IP rotation + Cloudflare bypass)

Without Tor, some heavily protected sites (Cloudflare Business, Akamai) may block scraping. Tor routes your traffic through random exit nodes.

1. Download [Tor Browser](https://www.torproject.org/download/)
2. Open Tor Browser and connect to the Tor network
3. Leave it running in the background
4. Start QuantVeil — it auto-detects Tor on `127.0.0.1:9150`

You'll see `[TOR] Active on port 9150` in the terminal when it's detected.

### Camoufox (modified Firefox — hardest to detect)

Camoufox is the third fallback engine when curl_cffi and DrissionPage both fail.

```bash
pip install "camoufox[geoip]"
python -m camoufox fetch
```

Once installed, it's used automatically for the most protected sites.

---

## Project Structure

```
QuantVeil/
├── backend/                    # All Python backend code
│   ├── engines/                # Scraping engine tier
│   │   ├── curl_engine.py      # Tier 1: curl_cffi with Chrome TLS fingerprint
│   │   ├── drission_engine.py  # Tier 2: real Chrome headless (DrissionPage)
│   │   ├── camoufox_engine.py  # Tier 3: modified Firefox (hardest to detect)
│   │   └── session_store.py    # Cookie persistence across requests
│   ├── web_app.py              # Flask server — start this to run QuantVeil
│   ├── dispatcher.py           # Engine escalation chain + Tor fallback logic
│   ├── extractor.py            # Email/phone/social extraction from HTML
│   ├── contact_finder.py       # Smart contact page discovery
│   ├── tech_stack.py           # CMS, framework, analytics detection
│   ├── reddit_module.py        # Reddit scraper (real Chrome, off-screen)
│   ├── news_module.py          # Google News + Hacker News
│   ├── wayback_module.py       # Wayback Machine growth indicators
│   ├── github_module.py        # GitHub org/repo/language search
│   ├── crunchbase_module.py    # Crunchbase funding + investor data
│   ├── market_research.py      # AI SWOT analysis via OpenRouter
│   ├── llm_client.py           # Cold outreach brief via OpenRouter
│   ├── pdf_generator.py        # A4 report PDF + landscape slides PDF
│   ├── ppt_generator.py        # 7-slide PowerPoint deck
│   ├── proxy_rotator.py        # Tor detection + free proxy pool
│   ├── config.py               # API keys + timeout configuration
│   └── main.py                 # CLI mode (no web UI)
├── frontend/                   # React web UI
│   ├── src/
│   │   ├── components/         # UI components (Topbar, Sidebar, cards)
│   │   └── index.css           # Cohere-inspired design system
│   ├── public/                 # Static assets
│   └── package.json
├── .env.example                # API key template (copy to .env)
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Scraping Engine Tiers

QuantVeil uses a 3-tier escalation system — fastest to most stealthy:

```
curl_cffi (Chrome TLS fingerprint)
    ↓ timeout or Cloudflare detected
DrissionPage (real Chrome headless)
    ↓ still blocked
Camoufox (modified Firefox, 40+ fingerprint patches)
```

**Tor proxy behaviour:** When Tor is active and a site times out through Tor, QuantVeil automatically retries without the proxy before escalating to Chrome. Sites that are simply blocking Tor exit nodes (not Cloudflare) load instantly on direct retry — no Chrome overhead needed.

---

## CLI Mode (no web UI)

Run analysis directly in terminal:

```bash
python backend/main.py https://stripe.com
python backend/main.py basecamp.com --no-research     # skip AI (faster)
python backend/main.py stripe.com --engine drission   # force Chrome
python backend/main.py stripe.com --proxy             # use free proxy pool
```

---

## Generating Reports

1. Run a scan in the web UI
2. Wait for **Analysis Complete**
3. Click **Download Report PDF** for a full A4 intelligence report
4. Enable **PPT Export Mode** in the sidebar first, then click **Download PPTX** for a 7-slide deck

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'curl_cffi'`**
→ Run `pip install -r requirements.txt` with your venv activated.

**Frontend shows "not built yet"**
→ Run `cd frontend && npm install && npm run build`

**Scraping hangs on a site**
→ Open Tor Browser (free), connect to Tor network, then restart QuantVeil. It auto-detects Tor and falls back to direct connection if the site blocks Tor exit nodes.

**AI analysis returns "(failed)"**
→ Check `OPENROUTER_API_KEY` in your `.env` — make sure there are no extra spaces or quotes.

**Reddit shows no posts**
→ Reddit requires real Chrome. Make sure ChromeDriver is installed (DrissionPage auto-manages it on first run).

---

## Security Notes

- **`.env` is gitignored** — your API key never touches GitHub
- **`sessions/`** (cookie cache) is gitignored
- **`downloads/`** (generated reports) is gitignored
- Never commit your `.env` file

---

## License

MIT
