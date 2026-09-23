"""Shared orchestration for rebuilding canonical derived UFC tables.

pit_features.py owns the pure point-in-time calculations, this module provides
methods for the db to update state from point-in-time calculations.
"""

import db
import pit_features


def build_canonical_state(master):
    """Build bout snapshots and latest fighter states from raw master data."""
    feature_frame = pit_features.build_point_in_time_features(master)
    fighter_frame = pit_features.build_current_fighter_states(
        master, feature_frame=feature_frame
    )
    return feature_frame, fighter_frame


def persist_canonical_state(feature_frame, fighter_frame):
    """Upsert canonical tables and explicitly label retained legacy fighters."""
    db.upsert_records(
        "fight_features",
        "FightTag",
        pit_features.to_feature_records(feature_frame),
    )
    db.upsert_records("fighters", "fighter_tag", fighter_frame.to_dict(orient="records"))

    canonical_tags = (
        set(fighter_frame["fighter_tag"].astype(str))
        if "fighter_tag" in fighter_frame.columns
        else set()
    )
    existing = db.read_table("fighters")
    legacy_tags = [
        str(tag)
        for tag in existing["fighter_tag"].dropna().unique()
        if str(tag) not in canonical_tags
    ]
    db.upsert_records(
        "fighters",
        "fighter_tag",
        [
            {"fighter_tag": tag, "FeatureVersion": "legacy-retained"}
            for tag in legacy_tags
        ],
    )
    return legacy_tags


def rebuild_canonical_state(apply=False, master=None):
    """Rebuild canonical state, optionally persisting it to Postgres.

    Returns ``(feature_frame, fighter_frame, legacy_tags)``.  Dry runs do not
    query or modify the existing fighter table and return an empty legacy list.
    """
    if master is None:
        master = db.read_table("ufc_master")
    feature_frame, fighter_frame = build_canonical_state(master)
    legacy_tags = persist_canonical_state(feature_frame, fighter_frame) if apply else []
    return feature_frame, fighter_frame, legacy_tags
