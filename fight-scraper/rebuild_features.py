"""Manual rebuild from a raw ufc_master table, to be used as a 
script to make a manual update.
"""

import argparse

from rebuild_canonical import rebuild_canonical_state


def rebuild(apply=False):
    frame, fighters, legacy_tags = rebuild_canonical_state(apply=apply)
    eligible = int(frame["eligible"].sum()) if not frame.empty else 0
    detail = int(frame["raw_detail_complete"].sum()) if not frame.empty else 0
    print(
        f"bouts={len(frame)} eligible_labels={eligible} "
        f"complete_detail={detail} fighters={len(fighters)}"
    )
    if apply:
        print(
            "Applied canonical fight_features and fighters upserts; "
            f"marked legacy-retained fighters={len(legacy_tags)}"
        )
    else:
        print("Dry run: pass --apply to write")
    return frame, fighters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rebuild(args.apply)


if __name__ == "__main__":
    main()
