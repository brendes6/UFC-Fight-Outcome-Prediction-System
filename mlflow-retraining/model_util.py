import copy
import os
import random

import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import db
from sqlalchemy import text
from augment import FINAL_FEATURES, swap_augment
import pit_features

if FINAL_FEATURES != pit_features.FINAL_FEATURES:
    raise RuntimeError("model and point-in-time feature contracts are out of sync")
from datetime import date


TRAINING_SEED = int(os.environ.get("TRAINING_SEED", "42"))


def seed_everything(seed=TRAINING_SEED):
    """Make local training runs reproducible across Python, NumPy, and Torch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# Custom dataset for loading UFC data
class UFCDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.FloatTensor(features)
        self.labels = torch.LongTensor(labels)
        
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

# Our neural network class
class NN(nn.Module):
    # Initialize the network layers, add batch normalization and dropout
    def __init__(self, input_size, output_size):
        super(NN, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(256, 128)
        self.bn2 = nn.BatchNorm1d(128)
        self.dropout2 = nn.Dropout(0.2)
        
        self.fc3 = nn.Linear(128, 64)
        self.bn3 = nn.BatchNorm1d(64)
        self.dropout3 = nn.Dropout(0.1)

        self.fc4 = nn.Linear(64, 32)
        self.bn4 = nn.BatchNorm1d(32)
        self.dropout4 = nn.Dropout(0.1)
        
        self.fc5 = nn.Linear(32, output_size)

        # GELU provides smoother gradients than ReLU, often better for
        # tabular data where subtle feature interactions matter
        self.activation = nn.GELU()
    
    # Forward function
    def forward(self, x):
        x = self.activation(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        
        x = self.activation(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        x = self.activation(self.bn3(self.fc3(x)))
        x = self.dropout3(x)

        x = self.activation(self.bn4(self.fc4(x)))
        x = self.dropout4(x)
        
        x = self.fc5(x)
        return x

# Final feature list and the red/blue swap-augmentation logic live in augment.py
# (numpy-only) so they can be unit-tested without the full training stack.


def scaler_to_metadata(scaler):
    """Serialize scaler params in the exact format consumed by the Go backend."""
    means = scaler.mean_.tolist()
    stds = scaler.scale_.tolist()
    return {
        "feature_version": pit_features.FEATURE_VERSION,
        "means": {name: val for name, val in zip(FINAL_FEATURES, means)},
        "stds": {name: val for name, val in zip(FINAL_FEATURES, stds)},
        "saved_order": FINAL_FEATURES
    }


def clean_up_data(df: pd.DataFrame) -> pd.DataFrame:
    """Build the canonical pre-event feature snapshots from raw bouts."""
    if set(FINAL_FEATURES).issubset(df.columns):
        if "feature_version" not in df.columns:
            raise ValueError(
                "precomputed training features are missing feature_version"
            )
        if df["feature_version"].isna().any():
            raise ValueError("precomputed training features contain null feature_version")
        versions = set(df["feature_version"].unique())
        if versions != {pit_features.FEATURE_VERSION}:
            raise ValueError(
                "training data contains unsupported feature versions: "
                f"{sorted(versions)}; expected {pit_features.FEATURE_VERSION}"
            )
        return df.copy()
    return pit_features.build_point_in_time_features(df)

def load_data() -> pd.DataFrame:
    """Load the versioned, leakage-safe training table."""
    return db.read_table("fight_features")

def clean_and_scale(data):
    """Clean, augment, and scale data with temporal split and corner debiasing."""

    clean_df = clean_up_data(data)

    # Only bouts with a real winner/method label are supervised examples.
    # Debuts remain valid rows: their pre-fight state is simply a neutral,
    # zero-history state rather than a reason to discard the bout.
    clean_df = clean_df[clean_df["categorical_outcome"].notna()].copy()

    X = clean_df[FINAL_FEATURES].copy()

    X = X.replace([np.inf, -np.inf], np.nan)
    if X.isna().any().any():
        missing = X.columns[X.isna().any()].tolist()
        raise ValueError(f"point-in-time feature contract contains nulls: {missing}")

    # pandas promotes the nullable label column to float because unlabeled
    # draw/NC rows are represented as NaN.  Supervised model APIs require
    # integer class ids after those rows have been filtered out.
    y = clean_df["categorical_outcome"].astype(int).to_numpy()

    # Temporal split on complete events, never by rows within the same card.
    event_dates = pd.to_datetime(clean_df["event_date"], format="mixed")
    unique_events = event_dates.sort_values().drop_duplicates().to_numpy()
    split_idx = max(1, int(len(unique_events) * 0.8))
    cutoff = unique_events[min(split_idx, len(unique_events) - 1)]
    train_mask = event_dates.to_numpy() < cutoff
    val_mask = ~train_mask
    if not train_mask.any() or not val_mask.any():
        raise ValueError("temporal split needs at least one training and validation event")
    X_train_raw, X_val_raw = X.values[train_mask], X.values[val_mask]
    y_train_raw, y_val_raw = y[train_mask], y[val_mask]

    # Red/blue swap augmentation on training data only
    # Doubles training data and removes corner bias
    X_train_aug, y_train_aug = swap_augment(X_train_raw, y_train_raw)

    # Fit scaler on augmented training data, apply to both sets
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_aug)
    X_val_scaled = scaler.transform(X_val_raw)

    # X_val_raw (unscaled) is returned so the registered pyfunc model — which
    # scales internally — can be parity-checked against the in-process ensemble.
    return X_train_scaled, y_train_aug, X_val_scaled, y_val_raw, X_val_raw, scaler
        

def mixup_data(x, y, alpha=0.2):
    """Mixup augmentation: interpolates between random pairs of training examples.
    
    Creates synthetic samples by blending features and labels, which smooths
    decision boundaries and acts as a strong regularizer for tabular data.
    alpha controls the Beta distribution — 0.2 gives mild interpolation.
    """
    lam = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    batch_size = x.size(0)
    index = torch.randperm(batch_size, device=x.device)
    
    mixed_x = lam * x + (1 - lam) * x[index]
    y_a, y_b = y, y[index]
    return mixed_x, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    """Compute loss for mixup - weighted combination of losses against both labels."""
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def train_model(X_train, y_train, X_val, y_val, seed=TRAINING_SEED):
    """Train and return a neural network model"""

    seed_everything(seed)
    model = NN(X_train.shape[1], 6)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # initialize parameters
    learning_rate = 0.0005  
    num_epochs = 500  # more epochs to let cosine annealing schedule work
    batch_size = 64  
    weight_decay = 0.01  # L2 regularization via AdamW

    # Load from our custom ufc dataset
    train_dataset = UFCDataset(X_train, y_train)
    generator = torch.Generator()
    generator.manual_seed(seed)
    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )
    
    # If we have validation data, load it
    if X_val is not None and y_val is not None:
        val_dataset = UFCDataset(X_val, y_val)
        val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size)
    
    # Initialize loss function and optimizer
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=30, T_mult=2)

    # Early stopping based on validation loss (more stable signal than accuracy)
    best_val_loss = float('inf')
    patience = 15  # more patience to allow cosine annealing restarts
    counter = 0

    best_model_state = None

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0

        # Iterate through the training data
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            # Mixup: blend random pairs of samples to create synthetic training data
            # This smooths decision boundaries and reduces overfitting
            mixed_X, y_a, y_b, lam = mixup_data(batch_X, batch_y)
            
            optimizer.zero_grad()
            outputs = model(mixed_X)
            loss = mixup_criterion(criterion, outputs, y_a, y_b, lam)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
        
        # If we have validation data, validate the model
        if X_val is not None and y_val is not None:

            # put in eval mode
            model.eval()
            correct = 0
            total = 0
            val_loss = 0.0

            # No gradients for validation
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs, 1)
                    total += batch_y.size(0)
                    correct += (predicted==batch_y).sum().item()
            
            # Calculate validation accuracy and loss
            val_acc = 100 * correct / total
            avg_val_loss = val_loss / len(val_loader)
            # Step cosine scheduler each epoch
            scheduler.step(epoch + 1)
            
            current_lr = optimizer.param_groups[0]['lr']
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss/len(train_loader):.4f}, Val Loss: {avg_val_loss:.4f}, Val Accuracy: {val_acc:.2f}%, LR: {current_lr:.6f}")
            
            # Early stopping based on val loss (more stable than accuracy)
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                counter = 0
                # Save best model weights to restore later
                # A shallow dict copy still aliases the live parameter tensors,
                # so early stopping would restore the final weights instead of
                # the best validation checkpoint.
                best_model_state = copy.deepcopy(model.state_dict())

            else:
                counter += 1
                if counter >= patience:
                    print(f"Early stopping triggered at epoch {epoch+1}")
                    break
        else:
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss/len(train_loader):.4f}")

    # Restore the best checkpoint both after early stopping and after a run
    # that reaches the epoch cap without exhausting patience.
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f"Restored best model (val_loss: {best_val_loss:.4f})")

    return model, best_val_loss


def train_xgboost(X_train, y_train, X_val, y_val, seed=TRAINING_SEED):
    """Train and return an XGBoost classifier.
    
    XGBoost learns step-function decision boundaries that complement 
    the NN's smooth surfaces, giving real ensemble diversity.
    """
    xgb_model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=6,
        eval_metric="mlogloss",
        early_stopping_rounds=20,
        random_state=seed,
        verbosity=0,
    )

    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # Evaluate on validation set
    val_probs = xgb_model.predict_proba(X_val)
    val_preds = np.argmax(val_probs, axis=1)
    val_acc = np.mean(val_preds == y_val)
    val_loss = -np.mean(np.log(val_probs[np.arange(len(y_val)), y_val] + 1e-10))

    print(f"XGBoost val accuracy: {val_acc:.4f}, val logloss: {val_loss:.4f}")

    return xgb_model, val_loss


def export_nn_to_onnx(model, path):
    """Export NN model from PyTorch to ONNX for inference"""
    
    model.eval()
    dummy_input = torch.randn(1, len(FINAL_FEATURES))

    torch.onnx.export(
        model, 
        dummy_input, 
        path,
        export_params=True,
        opset_version=12,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
        dynamo=False,
    )

    print(f"NN model successfully converted to {path}")


def export_xgb_to_onnx(xgb_model, path):
    """Export XGBoost model to ONNX for inference in Go backend.
    
    Uses onnxmltools to convert, with zipmap disabled so probabilities
    come out as a proper tensor matching our ONNX runtime setup.
    """
    import onnxmltools
    from onnxmltools.convert.common.data_types import FloatTensorType

    initial_type = [('input', FloatTensorType([None, len(FINAL_FEATURES)]))]
    onnx_model = onnxmltools.convert_xgboost(
        xgb_model.get_booster(),
        initial_types=initial_type,
        target_opset=12
    )

    onnxmltools.utils.save_model(onnx_model, path)
    print(f"XGBoost model successfully converted to {path}")


def evaluate_ensemble(nn_model, xgb_model, X_val, y_val):
    """Run heterogeneous ensemble inference on validation set.
    
    Averages softmax probabilities from the NN and predicted probabilities
    from XGBoost. Different model families provide real diversity.
    
    Returns:
        dict with 'winner' (binary red/blue accuracy) and 'outcome' (6-class accuracy).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Get NN probabilities
    val_dataset = UFCDataset(X_val, y_val)
    val_loader = DataLoader(dataset=val_dataset, batch_size=64)
    
    nn_probs_list = []
    nn_model.eval()
    with torch.no_grad():
        for batch_X, _ in val_loader:
            batch_X = batch_X.to(device)
            outputs = nn_model(batch_X)
            probs = F.softmax(outputs, dim=1)
            nn_probs_list.append(probs.cpu().numpy())
    nn_probs = np.vstack(nn_probs_list)
    
    # Get XGBoost probabilities
    xgb_probs = xgb_model.predict_proba(X_val)
    
    # Average probabilities from both models
    avg_probs = (nn_probs + xgb_probs) / 2.0
    
    # 6-class outcome accuracy
    predicted_outcome = np.argmax(avg_probs, axis=1)
    outcome_correct = np.sum(predicted_outcome == y_val)
    
    # Binary winner accuracy uses summed side probability, matching production.
    red_win_probs = avg_probs[:, 0:3].sum(axis=1)
    blue_win_probs = avg_probs[:, 3:6].sum(axis=1)
    predicted_winner = (blue_win_probs > red_win_probs).astype(int)
    actual_winner = (y_val >= 3).astype(int)
    winner_correct = np.sum(predicted_winner == actual_winner)
    
    total = len(y_val)
    
    print(f"Ensemble winner accuracy: {winner_correct / total:.4f}")
    print(f"Ensemble outcome accuracy: {outcome_correct / total:.4f}")
    
    # Print individual model accuracies for comparison
    nn_preds = np.argmax(nn_probs, axis=1)
    xgb_preds = np.argmax(xgb_probs, axis=1)
    nn_winners = (nn_probs[:, 3:6].sum(axis=1) > nn_probs[:, 0:3].sum(axis=1)).astype(int)
    xgb_winners = (xgb_probs[:, 3:6].sum(axis=1) > xgb_probs[:, 0:3].sum(axis=1)).astype(int)
    print(f"  NN alone — winner: {np.mean(nn_winners == actual_winner):.4f}, outcome: {np.mean(nn_preds == y_val):.4f}")
    print(f"  XGB alone — winner: {np.mean(xgb_winners == actual_winner):.4f}, outcome: {np.mean(xgb_preds == y_val):.4f}")
    
    return {
        "winner": float(winner_correct / total),
        "outcome": float(outcome_correct / total)
    }


def ensemble_probs(nn_model, xgb_model, X_scaled):
    """Averaged NN(softmax) + XGBoost probabilities for already-scaled rows.

    Mirrors production inference and is used to parity-check the registered
    pyfunc model against the in-process models.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    nn_model.eval()
    with torch.no_grad():
        logits = nn_model(torch.FloatTensor(np.asarray(X_scaled)).to(device))
        nn_p = F.softmax(logits, dim=1).cpu().numpy()
    xgb_p = xgb_model.predict_proba(np.asarray(X_scaled))
    return (nn_p + xgb_p) / 2.0


def get_current_version():
    """Fetch the current model version number from the model_version row."""
    with db.get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT version FROM model_version WHERE id = 'current'")
        ).fetchone()
    return row[0] if row else 0


def update_production_accuracy_in_db(winner_accuracy, version):
    """Upsert the single production model_version row."""
    with db.get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO model_version (id, winner_accuracy, version, trained_at)
                VALUES ('current', :acc, :ver, :trained_at)
                ON CONFLICT (id) DO UPDATE
                  SET winner_accuracy = EXCLUDED.winner_accuracy,
                      version = EXCLUDED.version,
                      trained_at = EXCLUDED.trained_at
                """
            ),
            {"acc": float(winner_accuracy), "ver": int(version), "trained_at": str(date.today())},
        )
