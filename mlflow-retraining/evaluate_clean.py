"""Train and evaluate the point-in-time dataset without MLflow model registry/promotion.
"""

import numpy as np
import torch

from model_util import (
    clean_and_scale,
    evaluate_ensemble,
    load_data,
    train_model,
    train_xgboost,
)


def main():
    np.random.seed(7)
    torch.manual_seed(7)

    data = load_data()
    labeled = data[data["categorical_outcome"].notna()]
    print(
        f"dataset_rows={len(data)} labeled_rows={len(labeled)} "
        f"feature_versions={data['feature_version'].value_counts(dropna=False).to_dict()}"
    )

    X_train, y_train, X_val, y_val, _, _ = clean_and_scale(data)
    print(
        f"train_rows_augmented={len(X_train)} validation_rows={len(X_val)} "
        f"features={X_train.shape[1]}"
    )

    nn_model, nn_val_loss = train_model(X_train, y_train, X_val, y_val)
    print(f"nn_validation_loss={nn_val_loss:.6f}")

    xgb_model, xgb_val_loss = train_xgboost(X_train, y_train, X_val, y_val)
    print(f"xgb_validation_loss={xgb_val_loss:.6f}")

    accuracy = evaluate_ensemble(nn_model, xgb_model, X_val, y_val)
    print(
        f"clean_walk_forward_winner_accuracy={accuracy['winner']:.6f} "
        f"clean_walk_forward_outcome_accuracy={accuracy['outcome']:.6f}"
    )


if __name__ == "__main__":
    main()
