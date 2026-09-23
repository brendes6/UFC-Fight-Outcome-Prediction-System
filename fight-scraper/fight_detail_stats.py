"""Helper to parse per-bout totals from UFCStats fight-detail pages."""

import re

from bs4 import BeautifulSoup


def _normalise(value):
    return re.sub(r"[^a-z]", "", str(value).lower())


def _pair(cell):
    values = [p.get_text(" ", strip=True) for p in cell.find_all("p")]
    return values if len(values) == 2 else None


def _landed(value):
    match = re.match(r"^\s*(\d+)\s+of\s+(\d+)\s*$", str(value))
    return (int(match.group(1)), int(match.group(2))) if match else None


def _integer(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _clock(value):
    try:
        minutes, seconds = (int(part) for part in str(value).strip().split(":", 1))
        return minutes * 60 + seconds
    except (TypeError, ValueError):
        return None


def _sum_column(rows, index, parser):
    totals = [0, 0]
    found = [False, False]
    for row in rows:
        cells = row.find_all("td", recursive=False)
        if len(cells) <= index:
            return None
        values = _pair(cells[index])
        if not values:
            return None
        for side, value in enumerate(values):
            parsed = parser(value)
            if parsed is None:
                continue
            if isinstance(parsed, tuple):
                parsed = parsed[0]
            totals[side] += parsed
            found[side] = True
    return totals if all(found) else None


def _labelled_value(soup, label):
    wanted = _normalise(label)
    for item in soup.select(".b-fight-details__text-item"):
        marker = item.find("i")
        if marker and _normalise(marker.get_text(" ", strip=True)) == wanted:
            for sibling in marker.next_siblings:
                value = str(sibling).strip()
                if value:
                    return value
        text = item.get_text(" ", strip=True)
        if _normalise(text).startswith(wanted):
            match = re.search(r"(\d+(?::\d{2})?)\s*$", text)
            if match:
                return match.group(1)
    return None


def _fight_time(soup):
    try:
        round_number = int(_labelled_value(soup, "Round"))
        clock = _clock(_labelled_value(soup, "Time"))
        return (round_number - 1) * 300 + clock if round_number > 0 and clock is not None else None
    except (TypeError, ValueError):
        return None


def parse_fight_detail_stats(html):
    """Return totals keyed by fighter name; raise on challenge/shape changes."""
    if not html or "Checking your browser" in html:
        raise ValueError("UFCStats returned a browser challenge")
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.select("table.b-fight-details__table"):
        rows = table.select("tbody tr")
        if not rows:
            continue
        cells = rows[0].find_all("td", recursive=False)
        if len(cells) < 10:
            continue
        names = _pair(cells[0])
        if not names:
            continue
        sig = _sum_column(rows, 2, _landed)
        total = _sum_column(rows, 4, _landed)
        td = _sum_column(rows, 5, _landed)
        sub = _sum_column(rows, 7, _integer)
        kd = _sum_column(rows, 1, _integer)
        control = _sum_column(rows, 9, _clock)
        if not all(value is not None for value in (sig, total, td, sub, kd, control)):
            continue
        fight_time = _fight_time(soup)
        result = {}
        for side, name in enumerate(names):
            result[name] = {
                "MatchSigStr": sig[side][0],
                "MatchSigStrAttempted": sig[side][1],
                "MatchTotalStr": total[side][0],
                "MatchTotalStrAttempted": total[side][1],
                "MatchTD": td[side][0],
                "MatchTDAttempted": td[side][1],
                "MatchSubAtt": sub[side],
                "MatchKD": kd[side],
                "MatchControlTime": control[side],
                "MatchFightTime": fight_time,
            }
        return result
    raise ValueError("Could not locate a UFCStats totals table")
