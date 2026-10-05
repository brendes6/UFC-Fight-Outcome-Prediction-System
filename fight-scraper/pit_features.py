"""Point-in-time UFC feature construction.

Every row is snapshotted before the event is applied, and then every
fighter stat update is applied ONLY after all bouts on that event have occured.
"""

from collections import defaultdict
import re

import numpy as np
import pandas as pd


FEATURE_VERSION = "pit-v2"

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
    "BlueWeightLbs", "WeightLbsDif", "RedDaysSinceLastFight", "BlueDaysSinceLastFight",
    "DaysSinceLastFightDif", "RedExperience", "BlueExperience", "ExperienceDif",
    "RedTDAccuracy", "BlueTDAccuracy", "TDAccuracyDif", "RedTDDefense", "BlueTDDefense",
    "TDDefenseDif", "RedSigStrDefense", "BlueSigStrDefense", "SigStrDefenseDif",
    "RedAvgTDAttempted", "BlueAvgTDAttempted", "TDAttemptedDif", "RedRecentWinPct",
    "BlueRecentWinPct", "RecentWinPctDif", "RedRecentSigStrLanded", "BlueRecentSigStrLanded",
    "RecentSigStrDif", "RedRecentSigStrPct", "BlueRecentSigStrPct", "RecentSigStrPctDif",
    "RedRecentTDLanded", "BlueRecentTDLanded", "RecentTDLandedDif", "RedRecentTDDefense",
    "BlueRecentTDDefense", "RecentTDDefenseDif", "RedRecentSubAtt", "BlueRecentSubAtt",
    "RecentSubAttDif", "RedRecentFinishPct", "BlueRecentFinishPct", "RecentFinishPctDif",
    "RedRecentFightTime", "BlueRecentFightTime", "RecentFightTimeDif", "IsTitleBout",
    "NumberOfRounds", "IsFiveRoundBout", "IsMaleBout", "IsFlyweight", "IsBantamweight",
    "IsFeatherweight", "IsLightweight", "IsWelterweight", "IsMiddleweight",
    "IsLightHeavyweight", "IsHeavyweight", "IsStrawweight", "IsCatchweight", "IsOpenweight",
    "RedOrthodox", "BlueOrthodox", "RedSouthpaw", "BlueSouthpaw", "RedSwitch", "BlueSwitch",
    "SameStance", "OppositeStance",
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
        "td_landed": 0.0, "td_attempted": 0.0, "td_landed_against": 0.0,
        "td_attempted_against": 0.0, "sub_att": 0.0, "sig_absorbed": 0.0,
        "sig_attempted_against": 0.0, "total_rounds": 0.0, "fights": 0,
        "last_fight_date": None, "history": [],
    }


def _ratio(numerator, denominator, default=0.0):
    return numerator / denominator if denominator else default


def _recent_snapshot(state, window=5):
    history = state["history"][-window:]
    if not history:
        return {
            "RecentWinPct": 0.0, "RecentSigStrLanded": 0.0,
            "RecentSigStrPct": 0.0, "RecentTDLanded": 0.0,
            "RecentTDDefense": 0.5, "RecentSubAtt": 0.0,
            "RecentFinishPct": 0.0, "RecentFightTime": 0.0,
        }
    time = sum(item["time_minutes"] for item in history)
    sig_landed = sum(item["sig_landed"] for item in history)
    sig_attempted = sum(item["sig_attempted"] for item in history)
    td_landed = sum(item["td_landed"] for item in history)
    td_attempted_against = sum(item["td_attempted_against"] for item in history)
    td_against = sum(item["td_landed_against"] for item in history)
    return {
        "RecentWinPct": sum(item["win"] for item in history) / len(history),
        "RecentSigStrLanded": _ratio(sig_landed, time),
        "RecentSigStrPct": _ratio(sig_landed, sig_attempted),
        "RecentTDLanded": _ratio(td_landed, time) * 15 if time else 0.0,
        "RecentTDDefense": 1.0 - _ratio(td_against, td_attempted_against, 0.5),
        "RecentSubAtt": _ratio(sum(item["sub_att"] for item in history), time) * 15 if time else 0.0,
        "RecentFinishPct": sum(item["finish"] for item in history) / len(history),
        "RecentFightTime": time / len(history),
    }


def _snapshot(state):
    bouts = state["wins"] + state["losses"]
    wins = max(state["wins"], 1)
    time = state["time_minutes"]
    snapshot = {
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
        "Experience": state["fights"],
        "TDAccuracy": _ratio(state["td_landed"], state["td_attempted"]),
        "TDDefense": 1.0 - _ratio(state["td_landed_against"], state["td_attempted_against"], 0.5),
        "SigStrDefense": 1.0 - _ratio(state["sig_absorbed"], state["sig_attempted_against"], 0.5),
        "AvgTDAttempted": _ratio(state["td_attempted"], time) * 15 if time else 0.0,
        "LastFightDate": state["last_fight_date"],
    }
    snapshot.update(_recent_snapshot(state))
    return snapshot


def _row_value(row, column, default=0.0):
    return _number(row.get(column), default)


def _days_since(last_date, event_date):
    if last_date is None or event_date is None:
        return 0.0
    return float(max((event_date - last_date).days, 0))


def _flag(value):
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return 1.0 if str(value or "").strip().lower() in {"true", "1", "yes", "y"} else 0.0


def _weight_flags(value):
    text = str(value or "").lower().replace("-", " ")
    return {
        "IsFlyweight": float("flyweight" in text and "light heavyweight" not in text),
        "IsBantamweight": float("bantamweight" in text),
        "IsFeatherweight": float("featherweight" in text),
        "IsLightweight": float("lightweight" in text),
        "IsWelterweight": float("welterweight" in text),
        "IsMiddleweight": float("middleweight" in text and "light" not in text),
        "IsLightHeavyweight": float("light heavyweight" in text),
        "IsHeavyweight": float("heavyweight" in text and "light" not in text),
        "IsStrawweight": float("strawweight" in text),
        "IsCatchweight": float("catchweight" in text or "catch weight" in text),
        "IsOpenweight": float("openweight" in text or "open weight" in text),
    }


def _stance_flags(value):
    text = str(value or "").lower()
    return {
        "Orthodox": float("orthodox" in text),
        "Southpaw": float("southpaw" in text),
        "Switch": float("switch" in text),
    }


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
    red_sig = _row_value(row, "RedMatchSigStr")
    blue_sig = _row_value(row, "BlueMatchSigStr")
    red_sig_attempted = _row_value(row, "RedMatchSigStrAttempted")
    blue_sig_attempted = _row_value(row, "BlueMatchSigStrAttempted")
    red_td = _row_value(row, "RedMatchTD")
    blue_td = _row_value(row, "BlueMatchTD")
    red_td_attempted = _row_value(row, "RedMatchTDAttempted")
    blue_td_attempted = _row_value(row, "BlueMatchTDAttempted")
    red_sub = _row_value(row, "RedMatchSubAtt")
    blue_sub = _row_value(row, "BlueMatchSubAtt")
    red["fights"] += 1
    blue["fights"] += 1
    red["sig_landed"] += red_sig
    blue["sig_landed"] += blue_sig
    red["sig_attempted"] += red_sig_attempted
    blue["sig_attempted"] += blue_sig_attempted
    red["td_landed"] += red_td
    blue["td_landed"] += blue_td
    red["td_attempted"] += red_td_attempted
    blue["td_attempted"] += blue_td_attempted
    red["td_landed_against"] += blue_td
    blue["td_landed_against"] += red_td
    red["td_attempted_against"] += blue_td_attempted
    blue["td_attempted_against"] += red_td_attempted
    red["sub_att"] += red_sub
    blue["sub_att"] += blue_sub
    red["sig_absorbed"] += blue_sig
    blue["sig_absorbed"] += red_sig
    red["sig_attempted_against"] += blue_sig_attempted
    blue["sig_attempted_against"] += red_sig_attempted
    if red_time > 0:
        red["time_minutes"] += red_time
        blue["time_minutes"] += red_time

    rounds = _row_value(row, "FinishRound")
    if rounds > 0:
        red["total_rounds"] += rounds
        blue["total_rounds"] += rounds

    red["opponent_elos"].append(pre_elos[blue_name])
    blue["opponent_elos"].append(pre_elos[red_name])

    event_date = row.get("_event_date")
    if event_date is not None:
        event_date = pd.Timestamp(event_date).date()
    red["last_fight_date"] = event_date
    blue["last_fight_date"] = event_date

    red["history"].append({
        "win": int(winner == "Red"), "finish": int(winner == "Red" and kind in {"ko", "sub"}),
        "sig_landed": red_sig, "sig_attempted": red_sig_attempted,
        "td_landed": red_td, "td_attempted": red_td_attempted,
        "td_landed_against": blue_td, "td_attempted_against": blue_td_attempted,
        "sub_att": red_sub, "time_minutes": red_time,
    })
    blue["history"].append({
        "win": int(winner == "Blue"), "finish": int(winner == "Blue" and kind in {"ko", "sub"}),
        "sig_landed": blue_sig, "sig_attempted": blue_sig_attempted,
        "td_landed": blue_td, "td_attempted": blue_td_attempted,
        "td_landed_against": red_td, "td_attempted_against": red_td_attempted,
        "sub_att": blue_sub, "time_minutes": red_time,
    })

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
    out["BlueWeightLbs"] = _row_value(row, "BlueWeightLbs")
    out["WeightLbsDif"] = out["RedWeightLbs"] - out["BlueWeightLbs"]

    event_date = pd.Timestamp(row["_event_date"]).date()
    red_days = _days_since(red["LastFightDate"], event_date)
    blue_days = _days_since(blue["LastFightDate"], event_date)
    out["RedDaysSinceLastFight"] = red_days
    out["BlueDaysSinceLastFight"] = blue_days
    out["DaysSinceLastFightDif"] = red_days - blue_days

    for name, key in [
        ("Experience", "Experience"), ("TDAccuracy", "TDAccuracy"),
        ("TDDefense", "TDDefense"), ("SigStrDefense", "SigStrDefense"),
        ("AvgTDAttempted", "AvgTDAttempted"), ("RecentWinPct", "RecentWinPct"),
        ("RecentSigStrLanded", "RecentSigStrLanded"), ("RecentSigStrPct", "RecentSigStrPct"),
        ("RecentTDLanded", "RecentTDLanded"), ("RecentTDDefense", "RecentTDDefense"),
        ("RecentSubAtt", "RecentSubAtt"), ("RecentFinishPct", "RecentFinishPct"),
        ("RecentFightTime", "RecentFightTime"),
    ]:
        out[f"Red{name}"] = red[key]
        out[f"Blue{name}"] = blue[key]
        diff_name = {
            "AvgTDAttempted": "TDAttemptedDif",
            "RecentSigStrLanded": "RecentSigStrDif",
        }.get(name, f"{name}Dif")
        out[diff_name] = red[key] - blue[key]

    out["IsTitleBout"] = _flag(row.get("TitleBout"))
    default_rounds = 5.0 if out["IsTitleBout"] else 3.0
    rounds = _row_value(row, "NumberOfRounds", default_rounds) or default_rounds
    out["NumberOfRounds"] = rounds
    out["IsFiveRoundBout"] = float(rounds >= 5)
    out["IsMaleBout"] = float(str(row.get("Gender") or "").strip().upper() == "MALE")
    out.update(_weight_flags(row.get("WeightClass")))

    red_stance = _stance_flags(row.get("RedStance"))
    blue_stance = _stance_flags(row.get("BlueStance"))
    for stance in ("Orthodox", "Southpaw", "Switch"):
        out[f"Red{stance}"] = red_stance[stance]
        out[f"Blue{stance}"] = blue_stance[stance]
    out["SameStance"] = float(
        any(red_stance[s] and blue_stance[s] for s in ("Orthodox", "Southpaw", "Switch"))
    )
    out["OppositeStance"] = float(
        (red_stance["Orthodox"] and blue_stance["Southpaw"])
        or (red_stance["Southpaw"] and blue_stance["Orthodox"])
    )

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
    sort_columns = ["_event_date", "_event_key"]
    if "FightTag" in df.columns:
        sort_columns.append("FightTag")
    sort_columns.append("_source_order")
    df = df.sort_values(sort_columns, kind="mergesort")
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
                "Experience": snap["Experience"], "TDAccuracy": snap["TDAccuracy"],
                "TDDefense": snap["TDDefense"], "SigStrDefense": snap["SigStrDefense"],
                "AvgTDAttempted": snap["AvgTDAttempted"], "RecentWinPct": snap["RecentWinPct"],
                "RecentSigStrLanded": snap["RecentSigStrLanded"],
                "RecentSigStrPct": snap["RecentSigStrPct"], "RecentTDLanded": snap["RecentTDLanded"],
                "RecentTDDefense": snap["RecentTDDefense"], "RecentSubAtt": snap["RecentSubAtt"],
                "RecentFinishPct": snap["RecentFinishPct"], "RecentFightTime": snap["RecentFightTime"],
                "LastFightDate": snap["LastFightDate"].isoformat() if snap["LastFightDate"] else None,
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
