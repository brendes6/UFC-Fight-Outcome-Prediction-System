"""HTTP fetch helper for stats scraper.

The ufcstats.com website occasionally returns a JS challenge instead of the 
requested page. If the scrape_challenge module is available, it is used to resolve 
the challenge; otherwise, the raw response text is returned so that callers can handle it themselves.
"""


def get_text_helper(url, session):
    response = session.get(url)

    if "Checking your browser" not in response.text:
        return response.text

    # Optional local handler for resolving the JS challenge.
    try:
        from scrape_challenge import resolve

        return resolve(url, session, response)
    except ImportError:
        print(f"JS challenge encountered for {url}; returning raw response.")
        return response.text
