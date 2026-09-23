import pandas as pd

from pit_features import build_current_fighter_states, build_point_in_time_features


def bout(date, tag, red, blue, winner, finish, time=300):
    return {
        "Date": date,
        "FightTag": tag,
        "Location": "Test Arena",
        "RedFighter": red,
        "BlueFighter": blue,
        "Winner": winner,
        "Finish": finish,
        "FinishRound": 1,
        "RedHeightCms": 180,
        "BlueHeightCms": 175,
        "RedReachCms": 185,
        "BlueReachCms": 180,
        "RedAge": 30,
        "BlueAge": 29,
        "RedWeightLbs": 155,
        "BlueWeightLbs": 155,
        "RedStance": "Orthodox",
        "BlueStance": "Southpaw",
        "WeightClass": "Lightweight",
        "Gender": "MALE",
        "MatchFightTime": time,
        "RedMatchSigStr": 10,
        "BlueMatchSigStr": 5,
        "RedMatchSigStrAttempted": 20,
        "BlueMatchSigStrAttempted": 15,
        "RedMatchTD": 1,
        "BlueMatchTD": 0,
        "RedMatchTDAttempted": 2,
        "BlueMatchTDAttempted": 1,
        "RedMatchSubAtt": 0,
        "BlueMatchSubAtt": 1,
    }


def test_snapshots_exclude_the_current_bout_result_and_stats():
    rows = [
        bout("2024-01-01", "one", "Alpha", "Bravo", "Red", "KO/TKO"),
        bout("2024-02-01", "two", "Alpha", "Charlie", "Blue", "DEC"),
    ]
    frame = build_point_in_time_features(pd.DataFrame(rows))

    first, second = frame.iloc[0], frame.iloc[1]
    assert first["RedWins"] == 0
    assert first["RedAvgSigStrLanded"] == 0
    assert first["RedElo"] == 1500
    assert second["RedWins"] == 1
    assert second["RedWinsByKO"] == 1
    assert second["RedAvgSigStrLanded"] == 2
    assert second["RedSigStrAbsorbed"] == 1
    assert second["categorical_outcome"] == 5


def test_all_bouts_on_one_event_share_the_pre_event_state():
    rows = [
        bout("2024-01-01", "one", "Alpha", "Bravo", "Red", "KO/TKO"),
        bout("2024-01-01", "two", "Charlie", "Delta", "Blue", "SUB"),
        bout("2024-02-01", "three", "Alpha", "Charlie", "Red", "DEC"),
    ]
    frame = build_point_in_time_features(pd.DataFrame(rows))
    assert frame.loc[0, "RedWins"] == 0
    assert frame.loc[1, "BlueWins"] == 0
    assert frame.loc[2, "RedWins"] == 1
    assert frame.loc[2, "BlueWins"] == 0


def test_current_fighter_states_are_post_event_and_serveable():
    frame = pd.DataFrame([bout("2024-01-01", "one", "Alpha", "Bravo", "Red", "KO/TKO")])
    fighters = build_current_fighter_states(frame)
    alpha = fighters[fighters["fighter_tag"] == "alpha"].iloc[0]
    bravo = fighters[fighters["fighter_tag"] == "bravo"].iloc[0]
    assert alpha["Wins"] == 1
    assert alpha["CurrentWinStreak"] == 1
    assert bravo["Losses"] == 1
    assert bravo["SigStrAbsorbed"] == 2
