from fight_detail_stats import parse_fight_detail_stats


def test_parser_preserves_landed_attempted_pairs_and_sums_totals():
    cells = [
        "<p>Red Fighter</p><p>Blue Fighter</p>",
        "<p>1</p><p>0</p>",
        "<p>10 of 20</p><p>5 of 15</p>",
        "<p>ignored</p><p>ignored</p>",
        "<p>30 of 40</p><p>12 of 25</p>",
        "<p>2 of 4</p><p>1 of 3</p>",
        "<p>ignored</p><p>ignored</p>",
        "<p>1</p><p>0</p>",
        "<p>ignored</p><p>ignored</p>",
        "<p>1:00</p><p>0:30</p>",
    ]
    html = (
        '<div class="b-fight-details__text-item"><i>Round:</i> 2</div>'
        '<div class="b-fight-details__text-item"><i>Time:</i> 1:30</div>'
        '<table class="b-fight-details__table"><tbody><tr>'
        + "".join(f"<td>{cell}</td>" for cell in cells)
        + "</tr></tbody></table>"
    )

    result = parse_fight_detail_stats(html)

    assert result["Red Fighter"]["MatchSigStr"] == 10
    assert result["Red Fighter"]["MatchSigStrAttempted"] == 20
    assert result["Blue Fighter"]["MatchTotalStrAttempted"] == 25
    assert result["Red Fighter"]["MatchTDAttempted"] == 4
    assert result["Red Fighter"]["MatchFightTime"] == 390
