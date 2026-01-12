import trafilatura

def extract_article_payload(html):
    result = trafilatura.extract(html)

    #title = result.get('title', "UNKNOWN")
    #paragraphs = result.get("text", "").split("\n\n")

    return result

