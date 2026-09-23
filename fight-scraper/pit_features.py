"""Point-in-time UFC feature construction.

Every row is snapshotted before the event is applied, and then every
fighter stat update is applied ONLY after all bouts on that event have occured.
"""

from collections import defaultdict
import re

import numpy as np
import pandas as pd


FEATURE_VERSION = "pit-v1"

FINAL_FEATURES = [
    "RedWinPct", "BlueWinPct", "WinPctDif", "RedKoPct", "BlueKoPct", "KoPctDif",
    "RedSubPct", "BlueSubPct", "SubPctDif", "RedDecPct", "BlueDecPct", "DecPctDif",
    "RedLossesByKO", "BlueLossesByKO", "LossesByKODif", "RedLossesBySub",
    "BlueLossesBySub", "LossesBySubDif", "RedLossesByDec", "BlueLossesByDec",
    "LossesByDecDif", "RedWeightLbs", "HeightDif", "ReachDif", "AgeDif", "RedAge",
    "BlueAge", "SigStrDif", "StrPctDif", "TDDif", "SubAttDif", "RedAvgSigStrLanded",
    "BlueAvgSigStrLanded", "RedAvgTDLanded", "BlueAvgTDLanded", "RedAvgSigStrPct",
    "BlueAvgSigStrPct", "RedAvgSubAtt", "BlueAvgSubAtt", "SigStrAbsorbedDif",
    "RedSigStrAbsorbed", "BlueSigStrAbsorbed", "AvgRoundsDif", "RedAvgRounds",
    "BlueAvgRounds", "EloDif", "OpponentEloDif", "RedElo", "BlueElo", "WinStreakDif",
    "RedCurrentWinStreak", "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5",
    "FinishL5Dif", "FinishPctDif",
]

_NUMERIC = {
    "MatchFightTime", "TotalFightTimeSecs", "FinishRound", "RedAge", "BlueAge",
}


def _number(value, default=0.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return default if not np.isfinite(value) else value


def _tag(name):
    return re.sub(r"\s+", "_", str(name).lower().replace("-", " ").strip())


def _finish_kind(value):
    text = str(value or "").strip().upper()
    if text in {"KO/TKO", "KO", "TKO"}:
        return "ko"
    if text in {"SUB", "SUBMISSION"}:
        return "sub"
    if text in {"U-DEC", "S-DEC", "M-DEC", "DEC", "DECISION"}:
        return "dec"
    return "other"


def _event_key(row):
    date = pd.Timestamp(row["_event_date"]).date().isoformat()
    location = str(row.get("Location") or "").strip().lower()
    return f"{date}|{location}"


def _new_state():
    return {
        "wins": 0, "losses": 0, "wins_ko": 0, "wins_sub": 0, "wins_dec": 0,
        "losses_ko": 0, "losses_sub": 0, "losses_dec": 0, "streak": 0,
        "finish_history": [], "elo": 1500.0, "opponent_elos": [],
        "time_minutes": 0.0, "sig_landed": 0.0, "sig_attempted": 0.0,
        "td_landed": 0.0, "sub_att": 0.0, "sig_absorbed": 0.0,
        "total_rounds": 0.0,
    }


def _snapshot(state):
    bouts = state["wins"] + state["losses"]
    wins = max(state["wins"], 1)
    time = state["time_minutes"]
    return {
        "Wins": state["wins"],
        "Losses": state["losses"],
        "WinsByKO": state["wins_ko"],
        "WinsBySubmission": state["wins_sub"],
        "WinsByDecision": state["wins_dec"],
        "LossesByKO": state["losses_ko"],
        "LossesBySub": state["losses_sub"],
        "LossesByDec": state["losses_dec"],
        "WinPct": state["wins"] / max(bouts, 1),
        "KoPct": state["wins_ko"] / wins,
        "SubPct": state["wins_sub"] / wins,
        "DecPct": state["wins_dec"] / wins,
        "AvgSigStrLanded": state["sig_landed"] / time if time else 0.0,
        "AvgTDLanded": state["td_landed"] / time * 15 if time else 0.0,
        "AvgSigStrPct": state["sig_landed"] / state["sig_attempted"] if state["sig_attempted"] else 0.0,
        "AvgSubAtt": state["sub_att"] / time * 15 if time else 0.0,
        "SigStrAbsorbed": state["sig_absorbed"] / time if time else 0.0,
        "AvgRounds": state["total_rounds"] / max(bouts, 1),
        "Elo": state["elo"],
        "OpponentElo": float(np.mean(state["opponent_elos"])) if state["opponent_elos"] else 1500.0,
        "CurrentWinStreak": state["streak"],
        "FinishL5": (sum(state["finish_history"][-5:]) * 5 / len(state["finish_history"]))
        if 0 < len(state["finish_history"]) < 5 else sum(state["finish_history"][-5:]),
        "TotalRoundsFought": int(state["total_rounds"]),
    }


def _row_value(row, column, default=0.0):
    return _number(row.get(column), default)


def _detail_complete(row):
    required = [
        "MatchFightTime", "RedMatchSigStr", "BlueMatchSigStr",
        "RedMatchSigStrAttempted", "BlueMatchSigStrAttempted",
        "RedMatchTD", "BlueMatchTD", "RedMatchTDAttempted", "BlueMatchTDAttempted",
        "RedMatchSubAtt", "BlueMatchSubAtt",
    ]
    return all(pd.notna(row.get(column)) for column in required)


def _apply_bout(state_by_fighter, row, pre_elos):
    red_name, blue_name = row["RedFighter"], row["BlueFighter"]
    red, blue = state_by_fighter[red_name], state_by_fighter[blue_name]
    winner = str(row.get("Winner") or "").strip()
    kind = _finish_kind(row.get("Finish"))

    red_time = _row_value(row, "MatchFightTime") / 60.0
    if red_time > 0:
        red_sig = _row_value(row, "RedMatchSigStr")
        blue_sig = _row_value(row, "BlueMatchSigStr")
        red["time_minutes"] += red_time
        blue["time_minutes"] += red_time
        red["sig_landed"] += red_sig
        blue["sig_landed"] += blue_sig
        red["sig_attempted"] += _row_value(row, "RedMatchSigStrAttempted")
        blue["sig_attempted"] += _row_value(row, "BlueMatchSigStrAttempted")
        red["td_landed"] += _row_value(row, "RedMatchTD")
        blue["td_landed"] += _row_value(row, "BlueMatchTD")
        red["sub_att"] += _row_value(row, "RedMatchSubAtt")
        blue["sub_att"] += _row_value(row, "BlueMatchSubAtt")
        red["sig_absorbed"] += blue_sig
        blue["sig_absorbed"] += red_sig

    rounds = _row_value(row, "FinishRound")
    if rounds > 0:
        red["total_rounds"] += rounds
        blue["total_rounds"] += rounds

    red["opponent_elos"].append(pre_elos[blue_name])
    blue["opponent_elos"].append(pre_elos[red_name])

    if winner not in {"Red", "Blue"}:
        return

    winner_name, loser_name = (red_name, blue_name) if winner == "Red" else (blue_name, red_name)
    winning, losing = state_by_fighter[winner_name], state_by_fighter[loser_name]
    winning["wins"] += 1
    losing["losses"] += 1
    winning["streak"] += 1
    losing["streak"] = 0
    winning["finish_history"].append(1 if kind in {"ko", "sub"} else 0)
    losing["finish_history"].append(0)

    if kind == "ko":
        winning["wins_ko"] += 1
        losing["losses_ko"] += 1
    elif kind == "sub":
        winning["wins_sub"] += 1
        losing["losses_sub"] += 1
    elif kind == "dec":
        winning["wins_dec"] += 1
        losing["losses_dec"] += 1

    k = 40 if kind in {"ko", "sub"} else 30 if kind == "dec" and str(row.get("Finish")).upper() == "U-DEC" else 20 if kind == "dec" else 25
    red_expected = 1 / (1 + 10 ** ((pre_elos[blue_name] - pre_elos[red_name]) / 400))
    blue_expected = 1 - red_expected
    deltas = row.get("_elo_deltas")
    if deltas is None:
        deltas = defaultdict(float)
    if winner == "Red":
        deltas[red_name] += k * (1 - red_expected)
        deltas[blue_name] += k * (0 - blue_expected)
    else:
        deltas[blue_name] += k * (1 - blue_expected)
        deltas[red_name] += k * (0 - red_expected)


def _populate_features(out, row, red, blue):
    values = {"Red": red, "Blue": blue}
    for side, state in values.items():
        for key, value in state.items():
            out[f"{side}{key}"] = value

    out["RedWinPct"] = red["WinPct"]
    out["BlueWinPct"] = blue["WinPct"]
    out["WinPctDif"] = red["WinPct"] - blue["WinPct"]
    out["KoPctDif"] = red["KoPct"] - blue["KoPct"]
    out["SubPctDif"] = red["SubPct"] - blue["SubPct"]
    out["DecPctDif"] = red["DecPct"] - blue["DecPct"]
    out["LossesByKODif"] = red["LossesByKO"] - blue["LossesByKO"]
    out["LossesBySubDif"] = red["LossesBySub"] - blue["LossesBySub"]
    out["LossesByDecDif"] = red["LossesByDec"] - blue["LossesByDec"]
    out["HeightDif"] = _row_value(row, "RedHeightCms") - _row_value(row, "BlueHeightCms")
    out["ReachDif"] = _row_value(row, "RedReachCms") - _row_value(row, "BlueReachCms")
    out["AgeDif"] = _row_value(row, "RedAge") - _row_value(row, "BlueAge")
    out["RedAge"] = _row_value(row, "RedAge")
    out["BlueAge"] = _row_value(row, "BlueAge")
    for name, red_key, blue_key in [
        ("SigStrDif", "AvgSigStrLanded", "AvgSigStrLanded"),
        ("StrPctDif", "AvgSigStrPct", "AvgSigStrPct"),
        ("TDDif", "AvgTDLanded", "AvgTDLanded"),
        ("SubAttDif", "AvgSubAtt", "AvgSubAtt"),
        ("SigStrAbsorbedDif", "SigStrAbsorbed", "SigStrAbsorbed"),
        ("AvgRoundsDif", "AvgRounds", "AvgRounds"),
        ("EloDif", "Elo", "Elo"),
        ("OpponentEloDif", "OpponentElo", "OpponentElo"),
        ("WinStreakDif", "CurrentWinStreak", "CurrentWinStreak"),
    ]:
        out[name] = red[red_key] - blue[blue_key]
    out["FinishL5Dif"] = red["FinishL5"] - blue["FinishL5"]
    out["FinishPctDif"] = (red["KoPct"] + red["SubPct"]) - (blue["KoPct"] + blue["SubPct"])
    out["RedWeightLbs"] = _row_value(row, "RedWeightLbs")

    winner = str(row.get("Winner") or "").strip()
    kind = _finish_kind(row.get("Finish"))
    out["categorical_outcome"] = {
        ("Red", "ko"): 0, ("Red", "sub"): 1, ("Red", "dec"): 2,
        ("Blue", "ko"): 3, ("Blue", "sub"): 4, ("Blue", "dec"): 5,
    }.get((winner, kind))
    out["winner_number"] = {"Red": 0, "Blue": 1}.get(winner)


def _build(data, return_states=False):
    df = data.copy()
    if df.empty:
        empty = pd.DataFrame(columns=list(df.columns) + FINAL_FEATURES)
        return (empty, {}) if return_states else empty
    required = {"Date", "RedFighter", "BlueFighter", "Winner"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required fight columns: {sorted(missing)}")
    df["_event_date"] = pd.to_datetime(df["Date"].astype(str).str.replace("/ ", "/", regex=False), format="mixed", errors="coerce")
    if df["_event_date"].isna().any():
        raise ValueError("one or more fight dates could not be parsed")
    df["_source_order"] = np.arange(len(df))
    df["_event_key"] = df.apply(_event_key, axis=1)
    df = df.sort_values(["_event_date", "_event_key", "_source_order"])
    states = defaultdict(_new_state)
    result_rows = []

    for _, event in df.groupby(["_event_date", "_event_key"], sort=True, dropna=False):
        names = set(event["RedFighter"]).union(event["BlueFighter"])
        for name in names:
            states[name]
        before = {name: _snapshot(states[name]) for name in names}
        pre_elos = {name: states[name]["elo"] for name in names}
        for _, row in event.iterrows():
            out = row.to_dict()
            _populate_features(out, row, before[row["RedFighter"]], before[row["BlueFighter"]])
            out["event_date"] = row["_event_date"].date()
            out["event_key"] = row["_event_key"]
            out["feature_version"] = FEATURE_VERSION
            out["raw_detail_complete"] = _detail_complete(row)
            out["eligible"] = out["categorical_outcome"] is not None
            result_rows.append(out)

        deltas = defaultdict(float)
        for _, row in event.iterrows():
            row = row.copy()
            row["_elo_deltas"] = deltas
            _apply_bout(states, row, pre_elos)
        for name, delta in deltas.items():
            states[name]["elo"] += delta

    result = pd.DataFrame(result_rows).sort_values("_source_order").reset_index(drop=True)
    return (result, states) if return_states else result


def build_point_in_time_features(data):
    """Build clean, pre-event snapshots for every historical bout."""
    return _build(data, return_states=False)


def build_current_fighter_states(data, feature_frame=None, states=None):
    """Return the latest post-event state used by the serving API."""
    if feature_frame is None or states is None:
        feature_frame, states = _build(data, return_states=True)
    if feature_frame.empty:
        return pd.DataFrame()
    latest = feature_frame.sort_values(["_event_date", "_source_order"], ascending=[False, False])
    seen = set()
    rows = []
    for _, row in latest.iterrows():
        for side in ("Red", "Blue"):
            name = row[f"{side}Fighter"]
            if name in seen:
                continue
            seen.add(name)
            snap = _snapshot(states[name])
            values = {
                "Fighter": name,
                "fighter_tag": _tag(name),
                "Wins": snap["Wins"], "WinsByKO": snap["WinsByKO"],
                "WinsBySubmission": snap["WinsBySubmission"], "WinsByDecision": snap["WinsByDecision"],
                "Losses": snap["Losses"], "HeightCms": _number(row.get(f"{side}HeightCms")),
                "ReachCms": _number(row.get(f"{side}ReachCms")), "AvgSigStrLanded": snap["AvgSigStrLanded"],
                "AvgTDLanded": snap["AvgTDLanded"], "AvgSigStrPct": snap["AvgSigStrPct"],
                "AvgSubAtt": snap["AvgSubAtt"], "Stance": row.get(f"{side}Stance") or "Unknown",
                "WeightLbs": int(_number(row.get(f"{side}WeightLbs"))), "Age": int(_number(row.get(f"{side}Age"))),
                "KoPct": snap["KoPct"], "SubPct": snap["SubPct"], "DecPct": snap["DecPct"],
                "AvgRounds": snap["AvgRounds"], "Elo": snap["Elo"], "OpponentElo": snap["OpponentElo"],
                "SigStrAbsorbed": snap["SigStrAbsorbed"], "CurrentWinStreak": snap["CurrentWinStreak"],
                "FinishL5": snap["FinishL5"], "LossesByKO": snap["LossesByKO"],
                "LossesBySub": snap["LossesBySub"], "LossesByDec": snap["LossesByDec"],
                "WinPct": snap["WinPct"], "TotalRoundsFought": snap["TotalRoundsFought"],
                "WeightClass": row.get("WeightClass") or "Unknown", "Gender": row.get("Gender") or "UNKNOWN",
                "FeatureVersion": FEATURE_VERSION,
                "StateAsOfDate": row["_event_date"].date(),
            }
            rows.append(values)
    return pd.DataFrame(rows)


def to_feature_records(frame):
    """Convert the feature frame to the typed fight_features table contract."""
    metadata = ["FightTag", "event_date", "event_key", "feature_version", "raw_detail_complete", "eligible", "categorical_outcome", "winner_number", "RedFighter", "BlueFighter", "Winner", "Finish"]
    columns = metadata + FINAL_FEATURES
    return frame[[c for c in columns if c in frame]].replace({np.nan: None}).to_dict(orient="records")
