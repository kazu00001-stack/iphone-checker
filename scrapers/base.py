from __future__ import annotations

import os
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@asynccontextmanager
async def open_browser():
    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=headless)
        context: BrowserContext = await browser.new_context(
            user_agent=DEFAULT_UA,
            locale="ja-JP",
            viewport={"width": 1280, "height": 900},
        )
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


async def fetch_html(context: BrowserContext, url: str, timeout_ms: int | None = None) -> str:
    timeout = timeout_ms or int(os.environ.get("SCRAPE_TIMEOUT_MS", "30000"))
    page: Page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass
        return await page.content()
    finally:
        await page.close()
