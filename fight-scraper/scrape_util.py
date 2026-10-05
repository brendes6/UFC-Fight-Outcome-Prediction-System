"""HTTP fetch helper for stats scraper.

The ufcstats.com website occasionally returns a JS challenge instead of the 
requested page. If the scrape_challenge module is available, it is used to resolve 
the challenge; otherwise, the raw response text is returned so that callers can handle it themselves.
"""


def parse_height_cm(value):
    """Convert an UFCStats height to centimeters, tolerating missing values."""
    cleaned = str(value or "").replace("'", "").replace('"', "").strip()
    if cleaned in {"", "--", "nan", "N/A"}:
        return 0.0

    parts = cleaned.split()
    if len(parts) < 2:
        return 0.0
    try:
        total_inches = int(parts[0]) * 12 + int(parts[1])
    except (TypeError, ValueError):
        return 0.0
    return total_inches * 2.54


def normalize_fighter_tag(name):
    """Build the fighter tag used by the scraper and canonical data tables."""
    return "_".join(str(name or "").lower().replace("-", " ").split())


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
