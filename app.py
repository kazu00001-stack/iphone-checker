from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path


def _find_bundled_browsers(bundle_dir: Path) -> Path | None:
    candidates = [bundle_dir / "pw-browsers"]
    exe_dir = Path(sys.executable).parent
    candidates.append(exe_dir / "pw-browsers")
    if sys.platform == "darwin":
        candidates.append(exe_dir.parent / "Resources" / "pw-browsers")
    for c in candidates:
        if c.exists() and any(c.iterdir()):
            return c
    return None


def _resolve_paths() -> tuple[Path, Path, Path]:
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        if sys.platform == "darwin":
            user_dir = Path.home() / "Library" / "Application Support" / "iPhone転売価格チェッカー"
        elif sys.platform == "win32":
            base = os.environ.get("APPDATA") or str(Path.home())
            user_dir = Path(base) / "iPhone転売価格チェッカー"
        else:
            user_dir = Path.home() / ".iphone-checker"
        user_dir.mkdir(parents=True, exist_ok=True)

        browsers_path = _find_bundled_browsers(bundle_dir)
        if browsers_path:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

        return bundle_dir, bundle_dir / "config.yaml", user_dir / "latest.json"

    here = Path(__file__).resolve().parent
    return here, here / "config.yaml", here / "output" / "latest.json"


BASE_DIR, CONFIG_PATH, OUTPUT_PATH = _resolve_paths()

import yaml  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from flask import Flask, jsonify, redirect, render_template, request, url_for  # noqa: E402

from core.compare import build_rows  # noqa: E402
from core.models import AppleModel, BuybackQuote, ModelKey  # noqa: E402
from scrapers.apple import scrape_apple  # noqa: E402
from scrapers.base import open_browser  # noqa: E402
from scrapers.ichome import scrape_ichome  # noqa: E402
from scrapers.iosys import scrape_iosys  # noqa: E402
from scrapers.mobile_mix import scrape_mobile_mix  # noqa: E402


load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("app")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_latest() -> dict | None:
    if not OUTPUT_PATH.exists():
        return None
    try:
        with OUTPUT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning("failed to load latest.json: %s", e)
        return None


def save_latest(payload: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


async def run_all_scrapers(cfg: dict) -> dict:
    apple_cfg = cfg["scrapers"]["apple"]
    iosys_cfg = cfg["scrapers"]["iosys"]
    mobile_mix_cfg = cfg["scrapers"]["mobile_mix"]
    ichome_cfg = cfg["scrapers"]["ichome"]

    async with open_browser() as context:
        tasks = []
        tasks.append(scrape_apple(context, cfg["apple_models"], apple_cfg["base_url"]))
        if iosys_cfg.get("enabled"):
            tasks.append(scrape_iosys(context, iosys_cfg["url"]))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
        if mobile_mix_cfg.get("enabled"):
            tasks.append(scrape_mobile_mix(context, mobile_mix_cfg["candidate_urls"]))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
        if ichome_cfg.get("enabled"):
            tasks.append(scrape_ichome(context, ichome_cfg["candidate_urls"]))
        else:
            tasks.append(asyncio.sleep(0, result=[]))

        apple_models, iosys_quotes, mm_quotes, ichome_quotes = await asyncio.gather(
            *tasks, return_exceptions=True
        )

    apple_models = _unwrap(apple_models, [])
    iosys_quotes = _unwrap(iosys_quotes, [])
    mm_quotes = _unwrap(mm_quotes, [])
    ichome_quotes = _unwrap(ichome_quotes, [])

    payload = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "apple_models": [
            {
                "name": m.key.name,
                "capacity": m.key.capacity,
                "price_jpy": m.price_jpy,
                "url": m.url,
                "is_fallback": m.is_fallback,
            }
            for m in apple_models
        ],
        "quotes": [
            {
                "site": q.site,
                "name": q.key.name,
                "capacity": q.key.capacity,
                "price_jpy": q.price_jpy,
                "source_url": q.source_url,
            }
            for q in iosys_quotes + mm_quotes + ichome_quotes
        ],
    }
    save_latest(payload)
    return payload


def _unwrap(value, default):
    if isinstance(value, Exception):
        log.warning("scraper raised: %s", value)
        return default
    return value


def _payload_to_rows(payload: dict, mile_rate: float):
    apple_models = [
        AppleModel(
            key=ModelKey(name=m["name"], capacity=m["capacity"]),
            price_jpy=int(m["price_jpy"]),
            url=m["url"],
            is_fallback=bool(m.get("is_fallback", False)),
        )
        for m in payload.get("apple_models", [])
    ]
    quotes = [
        BuybackQuote(
            key=ModelKey(name=q["name"], capacity=q["capacity"]),
            site=q["site"],
            price_jpy=int(q["price_jpy"]),
            source_url=q["source_url"],
        )
        for q in payload.get("quotes", [])
    ]
    return build_rows(apple_models, quotes, mile_rate)


@app.get("/")
def index():
    cfg = load_config()
    try:
        mile_rate = float(request.args.get("rate", cfg.get("default_mile_rate", 1.0)))
    except ValueError:
        mile_rate = float(cfg.get("default_mile_rate", 1.0))

    payload = load_latest()
    rows = _payload_to_rows(payload, mile_rate) if payload else []
    return render_template(
        "index.html",
        rows=rows,
        mile_rate=mile_rate,
        fetched_at=(payload or {}).get("fetched_at"),
        sites=["iosys", "mobile_mix", "ichome"],
        site_labels={
            "iosys": "iosys",
            "mobile_mix": "mobile-mix",
            "ichome": "1丁目",
        },
    )


@app.post("/refresh")
def refresh():
    cfg = load_config()
    try:
        asyncio.run(run_all_scrapers(cfg))
    except Exception as e:
        log.exception("refresh failed")
        return jsonify({"ok": False, "error": str(e)}), 500
    rate = request.form.get("rate") or request.args.get("rate")
    if rate:
        return redirect(url_for("index", rate=rate))
    return redirect(url_for("index"))


@app.get("/health")
def health():
    return jsonify({"ok": True})


def _open_browser_later(url: str, delay: float = 1.5) -> None:
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception as e:
            log.warning("failed to open browser: %s", e)

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    url = f"http://{host}:{port}"
    log.info("Starting server at %s", url)
    log.info("Config: %s", CONFIG_PATH)
    log.info("Output: %s", OUTPUT_PATH)
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        log.info("Bundled Chromium: %s", os.environ["PLAYWRIGHT_BROWSERS_PATH"])

    is_frozen = getattr(sys, "frozen", False)
    if is_frozen or os.environ.get("AUTO_OPEN_BROWSER", "true").lower() != "false":
        _open_browser_later(url)

    app.run(host=host, port=port, debug=not is_frozen, use_reloader=False)


if __name__ == "__main__":
    main()
