"""
QuantVeil — backend API server.
API routes prefixed with /api/
Serves React build from frontend/dist/
"""
import os
import sys
import json
import time
import queue
import threading
import uuid
import traceback

from flask import Flask, jsonify, request, Response, send_file, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(_ROOT, "downloads")
FRONTEND_DIST = os.path.join(_ROOT, "frontend", "dist")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="")
JOBS: dict = {}


# ── Event helper ──────────────────────────────────────────────────────────────

def _push(q: queue.Queue, event_type: str, **kwargs):
    q.put({"type": event_type, **kwargs})


# ── Pipeline ──────────────────────────────────────────────────────────────────

def _run_pipeline(job_id: str, url: str, options: dict):
    q     = JOBS[job_id]["queue"]
    start = time.time()
    cold  = ""
    mkt   = ""
    result = {}

    try:
        from urllib.parse import urlparse
        from concurrent.futures import ThreadPoolExecutor

        import config
        from dispatcher    import dispatch
        from extractor     import extract
        from contact_finder import find_contact_pages
        from reddit_module  import scrape_reddit
        import news_module
        import wayback_module
        import tech_stack as ts
        import market_research
        import llm_client
        import github_module
        import crunchbase_module

        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        domain    = urlparse(url).netloc.replace("www.", "")
        brand_raw = domain.split(".")[0]

        # Tor / proxy
        proxy = None
        try:
            from proxy_rotator import check_tor
            proxy = check_tor()
        except Exception:
            pass

        force_engine = options.get("engine") or None
        do_research  = options.get("research", True)

        # ── Step 1: Website ───────────────────────────────────────────────────
        _push(q, "progress", step="website", message=f"Fetching {url}…")
        r       = dispatch(url, proxy=proxy, force_engine=force_engine)
        html    = r.get("html", "")
        headers = r.get("headers", {})
        engine  = r.get("engine", "unknown")
        status  = r.get("status", 0)
        stack   = ts.detect(html, headers) if html else {}

        _push(q, "result", section="website", data={
            "engine": engine, "bytes": len(html),
            "status": status, "tech_stack": stack, "url": url,
        })

        # ── Step 2: Contacts ──────────────────────────────────────────────────
        _push(q, "progress", step="contacts", message="Extracting contacts…")
        homepage = extract(html) if html else {
            "emails": [], "phones": [], "socials": {},
            "title": domain, "meta_description": "", "visible_text": "",
        }
        all_emails  = set(homepage["emails"])
        all_phones  = set(homepage["phones"])
        all_socials = dict(homepage.get("socials", {}))

        if html:
            def _eng(u): return dispatch(u, proxy=proxy, force_engine=force_engine)
            site_cf = r.get("is_cloudflare", False) or engine in ("drission", "camoufox")
            for cp in find_contact_pages(url, html, _eng, max_pages=3,
                                         site_is_cloudflare=site_cf):
                cpd = extract(cp["html"])
                all_emails  |= set(cpd["emails"])
                all_phones  |= set(cpd["phones"])
                all_socials.update(cpd.get("socials", {}))
                if not homepage.get("meta_description") and cpd.get("meta_description"):
                    homepage["meta_description"] = cpd["meta_description"]

        emails  = sorted(all_emails)
        phones  = sorted(all_phones)
        homepage.update({"emails": emails, "phones": phones, "socials": all_socials})

        _push(q, "result", section="contacts", data={
            "emails": emails, "phones": phones, "socials": all_socials,
        })

        # ── Step 3: Fast intelligence (parallel) ─────────────────────────────
        title = homepage.get("title", domain)
        _push(q, "progress", step="intelligence", message="Fetching news, GitHub, Crunchbase, Wayback…")

        with ThreadPoolExecutor(max_workers=4) as ex:
            f_news    = ex.submit(news_module.fetch_all, domain, title)
            f_wayback = ex.submit(wayback_module.get_growth_indicators, domain)
            f_github  = ex.submit(github_module.search_github, brand_raw, domain)
            f_cb      = ex.submit(crunchbase_module.search_crunchbase,
                                  brand_raw, domain, proxy)
            news_data    = f_news.result()
            wayback_data = f_wayback.result()
            github_data  = f_github.result()
            crunchbase_d = f_cb.result()

        _push(q, "result", section="news",       data=news_data)
        _push(q, "result", section="wayback",    data=wayback_data)
        _push(q, "result", section="github",     data=github_data)
        _push(q, "result", section="crunchbase", data=crunchbase_d)

        # ── Step 4: Reddit (own Chrome instance) ─────────────────────────────
        _push(q, "progress", step="reddit",
              message="Searching Reddit (launching Chrome off-screen)…")
        reddit_data = scrape_reddit(domain)
        _push(q, "result", section="reddit", data=reddit_data)

        # ── Step 5: AI Analysis ───────────────────────────────────────────────
        if do_research and config.OPENROUTER_API_KEY:
            _push(q, "progress", step="ai", message="Running AI market analysis…")
            cold = llm_client.analyze(homepage, reddit_data, domain)
            mkt  = market_research.analyze(
                domain, homepage, reddit_data, news_data,
                stack, wayback_data, github_data, crunchbase_d,
            )
            _push(q, "result", section="cold_outreach",   data={"text": cold})
            _push(q, "result", section="market_research", data={"text": mkt})

        result = {
            "domain":         domain,
            "url":            url,
            "title":          title,
            "tech_stack":     stack,
            "contacts":       homepage,
            "reddit":         reddit_data,
            "news":           news_data,
            "wayback":        wayback_data,
            "github":         github_data,
            "crunchbase":     crunchbase_d,
            "cold_outreach":  cold,
            "market_research": mkt,
            "engine":         engine,
        }
        JOBS[job_id]["result"] = result

    except Exception as e:
        _push(q, "error", message=str(e))
        print(traceback.format_exc())
    finally:
        _push(q, "complete", elapsed=round(time.time() - start, 1))
        JOBS[job_id]["done"] = True


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/scrape", methods=["POST"])
def start_scrape():
    data = request.get_json() or {}
    url  = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    job_id = str(uuid.uuid4())
    q = queue.Queue()
    JOBS[job_id] = {"queue": q, "result": None, "done": False}
    threading.Thread(
        target=_run_pipeline,
        args=(job_id, url, data.get("options", {})),
        daemon=True,
    ).start()
    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def stream(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        q = job["queue"]
        while True:
            done = job["done"]
            try:
                msg = q.get(timeout=0.4)
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                if done and q.empty():
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                yield ": heartbeat\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


@app.route("/api/download/ppt/<job_id>")
def download_ppt(job_id):
    job = JOBS.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "No data available"}), 404
    from ppt_generator import generate_ppt
    path   = generate_ppt(job["result"], DOWNLOADS_DIR)
    domain = job["result"].get("domain", "report")
    return send_file(path, as_attachment=True, download_name=f"intel_{domain}.pptx",
                     mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")


@app.route("/api/download/pdf/<job_id>")
def download_pdf(job_id):
    job = JOBS.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "No data available"}), 404
    from pdf_generator import generate_report_pdf
    path   = generate_report_pdf(job["result"], DOWNLOADS_DIR)
    domain = job["result"].get("domain", "report")
    return send_file(path, as_attachment=True, download_name=f"report_{domain}.pdf",
                     mimetype="application/pdf")


@app.route("/api/download/slides-pdf/<job_id>")
def download_slides_pdf(job_id):
    job = JOBS.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "No data available"}), 404
    from pdf_generator import generate_slides_pdf
    path   = generate_slides_pdf(job["result"], DOWNLOADS_DIR)
    domain = job["result"].get("domain", "report")
    return send_file(path, as_attachment=True, download_name=f"slides_{domain}.pdf",
                     mimetype="application/pdf")


# ── Serve React build ─────────────────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    target = os.path.join(FRONTEND_DIST, path)
    if path and os.path.exists(target):
        return send_from_directory(FRONTEND_DIST, path)
    index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index):
        return send_from_directory(FRONTEND_DIST, "index.html")
    return (
        "<h2>Frontend not built yet.</h2>"
        "<p>Run: <code>cd frontend && npm install && npm run build</code></p>"
        "<p>Then restart: <code>python web_app.py</code></p>",
        200,
    )


if __name__ == "__main__":
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║        QuantVeil  —  v1.0            ║")
    print("  ║   Market Intelligence Platform       ║")
    print("  ╚══════════════════════════════════════╝")
    has_ui = os.path.exists(os.path.join(FRONTEND_DIST, "index.html"))
    print(f"\n  Backend :  http://localhost:5001")
    if has_ui:
        print(f"  Open UI :  http://localhost:5001")
    else:
        print("  UI not built — run: cd frontend && npm install && npm run build")
    print()
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
