import json
import sys

from fetcher import fetch_dynamic_html, fetch_paginated_html
from extractor import extract_article_payload
from formatter import dataFormatter
from llm.analyzer import analyze_cleaned_dom, plan_scraping


def read_input():
    """
    Expected input format:
    {
        "url": "...",
        "output_format": "json"
    }
    """
    raw = sys.stdin.read()
    if not raw:
        raise RuntimeError("No input received from native host")
    return json.loads(raw)

def fetch_html(payload):
    url = payload["url"]
    pagination = None

    if not pagination:
        return fetch_dynamic_html(url)

    if pagination['type'] == 'scroll':
        return fetch_dynamic_html(url, scroll_pages=pagination['pages'])

    if pagination['type'] == 'url':
        pages = fetch_paginated_html(url, page_param=pagination['page'], total_pages=pagination['pages'])
        return "\n".join(pages)

    raise ValueError("Unsupported pagination type")

def main():
    # Hardcoding inputs
    request = {}
    request['url'] = input("Enter URL: ")
    request['user_prompt'] = input("Enter prompt: ")
    url = request['url']
    user_prompt = request['user_prompt']

    # 1. Ask LLM to plan scraping
    plan = plan_scraping(url, user_prompt)
    print(plan)

    # 2. fetching html
    html = fetch_html(request)

    # 3. Extract cleaned DOM
    cleaned_dom = extract_article_payload(html)

    # 4. Analyze using plan
    llm_result = analyze_cleaned_dom(cleaned_dom=cleaned_dom,
                                     plan=plan,
                                     max_retries=5)

    # Optional Formatting based on requirement
    if isinstance(llm_result, dict):
        if llm_result['records']:
            dataFormatter(llm_result)

    # 5. Sending to JS
    result = {
        "status": "success",
        "data": llm_result
    }

    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()

if __name__ == '__main__':
    main()