"""Unit tests for the red/blue corner-swap augmentation.

These run without the training stack (numpy only), so they stay fast in CI.
"""

import numpy as np

from augment import (
    FINAL_FEATURES,
    LABEL_SWAP,
    build_swap_indices,
    swap_augment,
)


def test_feature_schema_has_expected_size():
    # The Go backend and scaler metadata both assume 56 features in this order.
    assert len(FINAL_FEATURES) == 56
    assert len(set(FINAL_FEATURES)) == len(FINAL_FEATURES)  # no duplicates


def test_build_swap_indices_pairs_red_and_blue_columns():
    swap_order, negate_mask = build_swap_indices(FINAL_FEATURES)

    for i, feat in enumerate(FINAL_FEATURES):
        if feat.startswith("Red"):
            blue = "Blue" + feat[3:]
            if blue in FINAL_FEATURES:
                j = FINAL_FEATURES.index(blue)
                # Red<->Blue columns exchange positions.
                assert swap_order[i] == j
                assert swap_order[j] == i


def test_build_swap_indices_negates_only_difference_columns():
    _, negate_mask = build_swap_indices(FINAL_FEATURES)

    for i, feat in enumerate(FINAL_FEATURES):
        if feat.endswith("Dif"):
            assert negate_mask[i] == -1.0
        else:
            assert negate_mask[i] == 1.0


def test_swapping_twice_is_identity():
    swap_order, negate_mask = build_swap_indices(FINAL_FEATURES)
    # Distinct value per column so any misplacement is detectable.
    X = np.arange(len(FINAL_FEATURES), dtype=float).reshape(1, -1)

    once = X[:, swap_order] * negate_mask
    twice = once[:, swap_order] * negate_mask

    assert np.allclose(twice, X)


def test_label_swap_is_an_involution():
    for label, swapped in LABEL_SWAP.items():
        assert LABEL_SWAP[swapped] == label


def test_swap_augment_doubles_data_and_preserves_originals():
    X = np.array(
        [
            [1.0] * len(FINAL_FEATURES),
            [2.0] * len(FINAL_FEATURES),
        ]
    )
    y = np.array([0, 4])

    X_aug, y_aug = swap_augment(X, y)

    # Original rows are kept unchanged as the first half.
    assert X_aug.shape == (4, len(FINAL_FEATURES))
    assert np.allclose(X_aug[:2], X)
    assert list(y_aug[:2]) == [0, 4]
    # Mirrored labels: 0 -> 3, 4 -> 1.
    assert list(y_aug[2:]) == [3, 1]


def test_swap_augment_mirror_matches_manual_swap():
    swap_order, negate_mask = build_swap_indices(FINAL_FEATURES)
    rng = np.random.default_rng(0)
    X = rng.standard_normal((5, len(FINAL_FEATURES)))
    y = rng.integers(0, 6, size=5)

    X_aug, y_aug = swap_augment(X, y)

    expected_mirror = X[:, swap_order] * negate_mask
    assert np.allclose(X_aug[5:], expected_mirror)
    assert list(y_aug[5:]) == [LABEL_SWAP[int(label)] for label in y]


def test_difference_feature_flips_sign_when_mirrored():
    idx = FINAL_FEATURES.index("WinPctDif")
    X = np.zeros((1, len(FINAL_FEATURES)))
    X[0, idx] = 0.42
    y = np.array([2])

    X_aug, _ = swap_augment(X, y)

    assert X_aug[1, idx] == -0.42
