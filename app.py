#!/usr/bin/env python3
"""
Nieruchomości Monitor — Flask web app.
Deployment: Render.com (free tier) or any Python host.
"""
import json
import os
import sys
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, render_template, request, abort

BASE_DIR = Path(__file__).resolve().parent
DEALS_JSON = BASE_DIR / "deals.json"
CONFIG_PATH = BASE_DIR / "config.json"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = Flask(__name__, template_folder="templates")

# Secret for refresh endpoint
REFRESH_SECRET = os.environ.get("REFRESH_SECRET", "nieruchomosci2026")

_scraper_running = False
_last_run = None
_last_error = None


def run_scraper_bg():
    """Import and call monitor.main() directly — no subprocess, errors visible in logs."""
    global _scraper_running, _last_run, _last_error
    if _scraper_running:
        log.info("Scraper already running, skipping.")
        return
    _scraper_running = True
    _last_error = None
    try:
        log.info("Scraper: importing monitor...")
        sys.path.insert(0, str(BASE_DIR))
        import importlib
        import monitor as mon_module
        importlib.reload(mon_module)   # reload so config changes take effect
        log.info("Scraper: calling main()...")
        mon_module.main()
        _last_run = datetime.now().isoformat()
        log.info(f"Scraper: done at {_last_run}")
    except Exception as e:
        _last_error = str(e)
        log.error(f"Scraper FAILED: {e}", exc_info=True)
    finally:
        _scraper_running = False


def schedule_loop():
    """Background scheduler — runs scraper every 6 hours.
    Waits 30 seconds on first start to avoid hammering on cold-start (Render free tier).
    """
    log.info("Scheduler: waiting 30s before first run (cold-start guard)...")
    time.sleep(30)
    while True:
        log.info("Scheduler: running scraper...")
        run_scraper_bg()
        time.sleep(6 * 3600)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/deals")
def api_deals():
    if not DEALS_JSON.exists():
        resp = jsonify({"deals": [], "total": 0, "timestamp": None, "markets": {}})
        resp.headers["Cache-Control"] = "max-age=60"
        return resp

    with open(DEALS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    # Query params
    market = request.args.get("market", "")
    min_discount = float(request.args.get("min_discount", 0))
    prop_type = request.args.get("type", "")
    interesting_only = request.args.get("interesting_only", "false").lower() == "true"
    limit = int(request.args.get("limit", 200))

    deals = data.get("deals", [])

    # Load config to get market metadata
    config = load_config()
    markets_cfg = config.get("markets", {})

    # Enrich each deal with type + label + flag from config
    for d in deals:
        mk = d.get("market", "")
        mk_cfg = markets_cfg.get(mk, {})
        d["market_label"] = mk_cfg.get("label", mk)
        d["market_flag"] = mk_cfg.get("flag", "")
        d["type"] = mk_cfg.get("type", "")

    # Server-side filters
    if market and market != "all":
        deals = [d for d in deals if d.get("market") == market]

    if min_discount > 0:
        deals = [d for d in deals if d.get("discount_pct", 0) >= min_discount]

    if prop_type and prop_type != "all":
        deals = [d for d in deals if d.get("type") == prop_type]

    if interesting_only:
        deals = [d for d in deals if d.get("discount_pct", 0) >= 8 or d.get("okazja_score", 0) > 0]

    # Server-side sort by score desc before slicing
    deals.sort(key=lambda d: d.get("okazja_score", 0), reverse=True)

    # Slice
    deals = deals[:limit]

    resp = jsonify({
        "deals": deals,
        "total": data.get("total", len(data.get("deals", []))),
        "interesting": data.get("interesting", 0),
        "timestamp": data.get("timestamp"),
        "scraper_running": _scraper_running,
        "last_run": _last_run,
        "markets": markets_cfg,
    })
    resp.headers["Cache-Control"] = "max-age=60"
    return resp


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    if not request.is_json:
        abort(400)
    secret = request.json.get("secret", "")
    if secret != REFRESH_SECRET:
        abort(403)
    if _scraper_running:
        return jsonify({"status": "already_running"})
    thread = threading.Thread(target=run_scraper_bg, daemon=True)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/api/status")
def api_status():
    """Debug endpoint — shows scraper state and deals.json info."""
    info = {
        "scraper_running": _scraper_running,
        "last_run": _last_run,
        "last_error": _last_error,
        "deals_json_exists": DEALS_JSON.exists(),
        "deals_json_size": DEALS_JSON.stat().st_size if DEALS_JSON.exists() else 0,
        "python": sys.version,
        "base_dir": str(BASE_DIR),
    }
    if DEALS_JSON.exists():
        with open(DEALS_JSON, encoding="utf-8") as f:
            d = json.load(f)
        info["total_deals"] = d.get("total", 0)
        info["timestamp"] = d.get("timestamp")
    return jsonify(info)


@app.route("/api/stats")
def api_stats():
    if not DEALS_JSON.exists():
        return jsonify({})
    with open(DEALS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    deals = data.get("deals", [])

    by_market = {}
    for d in deals:
        mk = d.get("market", "other")
        if mk not in by_market:
            by_market[mk] = {"count": 0, "mega_deals": 0, "good_deals": 0}
        by_market[mk]["count"] += 1
        disc = d.get("discount_pct", 0)
        if disc >= 25:
            by_market[mk]["mega_deals"] += 1
        elif disc >= 15:
            by_market[mk]["good_deals"] += 1

    return jsonify({
        "total": len(deals),
        "by_market": by_market,
        "timestamp": data.get("timestamp"),
    })


# Start scheduler regardless of how the app is launched.
# Must be at module level — gunicorn imports app without running __main__.
_sched = threading.Thread(target=schedule_loop, daemon=True)
_sched.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
