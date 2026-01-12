from playwright.sync_api import sync_playwright
import time

def fetch_dynamic_html(url, scroll_pages=1):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                "Gecko/20100101 Firefox/121.0"
            ),
            locale="en-US",
            java_script_enabled=True
        )

        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        for _ in range(scroll_pages):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

        html = page.content()
        browser.close()
        return html

def fetch_paginated_html(base_url, page_param, total_pages):
    pages=[]
    for i in range(1, total_pages+1):
        url = f"{base_url}?{page_param}={i}"
        pages.append(fetch_dynamic_html(url, scroll_pages=0))
    return pages