"""Red/blue corner-swap data augmentation.

UFC data has a positional bias: the "Red" corner wins noticeably more often
(books tend to assign the favorite to red). Left unchecked, a model can
learn "red == winner" instead of learning from the actual fighter stats. To
remove that bias we mirror every training sample into the opposite corner and
train on both.

"""

import numpy as np

# Canonical feature order. This is the contract shared with the Go inference
# backend (see backend/main.go `finalFeatures`) and the scaler metadata.
FINAL_FEATURES = [
    "RedWinPct", "BlueWinPct", "WinPctDif", "RedKoPct", "BlueKoPct", "KoPctDif",
    "RedSubPct", "BlueSubPct", "SubPctDif", "RedDecPct", "BlueDecPct", "DecPctDif", "RedLossesByKO", "BlueLossesByKO", "LossesByKODif",
    "RedLossesBySub", "BlueLossesBySub", "LossesBySubDif", "RedLossesByDec", "BlueLossesByDec", "LossesByDecDif", "RedWeightLbs",
    "HeightDif", "ReachDif", "AgeDif", "RedAge", "BlueAge", "SigStrDif", "StrPctDif", "TDDif", "SubAttDif",
    "RedAvgSigStrLanded", "BlueAvgSigStrLanded", "RedAvgTDLanded", "BlueAvgTDLanded", "RedAvgSigStrPct", "BlueAvgSigStrPct",
    "RedAvgSubAtt", "BlueAvgSubAtt", "SigStrAbsorbedDif", "RedSigStrAbsorbed", "BlueSigStrAbsorbed", "AvgRoundsDif",
    "RedAvgRounds", "BlueAvgRounds", "EloDif", "OpponentEloDif", "RedElo", "BlueElo", "WinStreakDif",
    "RedCurrentWinStreak", "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5", "FinishL5Dif", "FinishPctDif",
]

# Label mapping when corners swap:
# RedKO(0)<->BlueKO(3), RedSub(1)<->BlueSub(4), RedDec(2)<->BlueDec(5)
LABEL_SWAP = {0: 3, 1: 4, 2: 5, 3: 0, 4: 1, 5: 2}


def build_swap_indices(final_features=FINAL_FEATURES):
    """Build the index mapping used to mirror a feature matrix's corners.

    Returns (swap_order, negate_mask):
        swap_order:  indices that rearrange each Red<->Blue feature pair
        negate_mask: +1/-1 per column; difference ("*Dif") features flip sign
                     when the corners are swapped
    """
    n = len(final_features)
    swap_order = list(range(n))
    negate_mask = np.ones(n)

    for i, feat in enumerate(final_features):
        # Find Red<->Blue swappable pairs
        if feat.startswith("Red"):
            blue_name = "Blue" + feat[3:]
            if blue_name in final_features:
                j = final_features.index(blue_name)
                swap_order[i] = j
                swap_order[j] = i
        # Negate difference features (they flip sign when corners swap)
        if feat.endswith("Dif"):
            negate_mask[i] = -1.0

    return np.array(swap_order), negate_mask


SWAP_ORDER, NEGATE_MASK = build_swap_indices(FINAL_FEATURES)


def swap_augment(X, y, swap_order=SWAP_ORDER, negate_mask=NEGATE_MASK, label_swap=LABEL_SWAP):
    """Return (X_aug, y_aug): the data plus a corner-swapped mirror copy.

    For each sample the mirror copy has:
      - Red and Blue individual features swapped positions
      - difference features negated
      - labels swapped (RedKO<->BlueKO, RedSub<->BlueSub, RedDec<->BlueDec)
    """
    X_swapped = X[:, swap_order] * negate_mask
    y_swapped = np.array([label_swap[label] for label in y])

    X_aug = np.vstack([X, X_swapped])
    y_aug = np.concatenate([y, y_swapped])

    return X_aug, y_aug
