from sklearn.model_selection import StratifiedKFold
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from google.cloud import firestore
import data_cleaning
import json
from datetime import date

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

def clean_up_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data using cleaning scripts"""
    df = data_cleaning.clean_up_data(df)
    df = data_cleaning.get_elos_and_streaks(df)
    df = data_cleaning.get_defense_data(df)
    df = data_cleaning.calculate_metrics(df)

    return df

def load_data() -> pd.DataFrame:
    """Load in data from firestore into a pd dataframe"""
    db = firestore.Client(project="ufc-proj", database="ufcdb")
        
    master_ref = db.collection("ufc-master")
    docs = master_ref.stream()
    
    # Converting Firestore docs to a DataFrame
    data_list = list(map(lambda x: x.to_dict(), docs))

    df = pd.DataFrame(data_list)

    return df

def clean_and_scale(data):
    """Clean and scale data"""

    clean_df = clean_up_data(data)

    # Filter out fights where either fighter has 0 wins
    clean_df = clean_df[(clean_df["RedWins"] > 0) & (clean_df["BlueWins"] > 0)]

    # Final features to pass into model
    final_features = [
        "RedWinPct", "BlueWinPct", "WinPctDif","RedKoPct", "BlueKoPct", "KoPctDif",
        "RedSubPct", "BlueSubPct", "SubPctDif","RedDecPct", "BlueDecPct", "DecPctDif","RedLossesByKO", "BlueLossesByKO", "LossesByKODif",
        "RedLossesBySub", "BlueLossesBySub", "LossesBySubDif","RedLossesByDec", "BlueLossesByDec", "LossesByDecDif", "RedWeightLbs",
        "HeightDif", "ReachDif", "AgeDif","RedAge", "BlueAge","SigStrDif", "StrPctDif", "TDDif", "SubAttDif",
        "RedAvgSigStrLanded", "BlueAvgSigStrLanded","RedAvgTDLanded", "BlueAvgTDLanded","RedAvgSigStrPct", "BlueAvgSigStrPct",
        "RedAvgSubAtt", "BlueAvgSubAtt","SigStrAbsorbedDif","RedSigStrAbsorbed", "BlueSigStrAbsorbed","AvgRoundsDif",
        "RedAvgRounds", "BlueAvgRounds","EloDif", "OpponentEloDif","RedElo", "BlueElo", "WinStreakDif",
        "RedCurrentWinStreak", "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5", "FinishL5Dif","FinishPctDif"
    ]

    X = clean_df[final_features].copy()

    # Replace any remaining inf/NaN from edge cases (e.g., 0 total fights for avg rounds)
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)

    # fit + save scaler 
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    y = clean_df["categorical_outcome"].values

    X_train, X_val, y_train, y_val = train_test_split(
        X_scaled, y, 
        test_size=0.2, 
        random_state=42,
        stratify=y
    )

    return X_train, y_train, X_val, y_val, scaler
        

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
    """Compute loss for mixup — weighted combination of losses against both labels."""
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def train_model(X_train, y_train, X_val, y_val):
    """Train and return a neural network model"""

    model = NN(X_train.shape[1], 6)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # initialize parameters
    learning_rate = 0.0005  
    num_epochs = 500  # more epochs to let cosine annealing schedule work
    batch_size = 64  
    val_size = 0.2
    weight_decay = 0.01  # L2 regularization via AdamW

    # Load from our custom ufc dataset
    train_dataset = UFCDataset(X_train, y_train)
    train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
    
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
                best_model_state = model.state_dict().copy()

            else:
                counter += 1
                if counter >= patience:
                    print(f"Early stopping triggered at epoch {epoch+1}")
                    # Restore best model weights before returning
                    if best_model_state is not None:
                        model.load_state_dict(best_model_state)
                        print(f"Restored best model (val_loss: {best_val_loss:.4f})")
                    break
        else:
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss/len(train_loader):.4f}")

    return model, best_val_loss

def export_to_onnx(model, path):
    """Export models from PyTorch to ONNX for inference"""
    
    model.eval()
    dummy_input = torch.randn(1, 56)

    torch.onnx.export(
        model, 
        dummy_input, 
        path,
        export_params=True,
        opset_version=12,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )

    print(f"Model successfully converted to {path}")

def evaluate_ensemble(models, X_val, y_val):
    """Run ensemble inference on validation set and return accuracy metrics.
    
    Returns:
        dict with 'winner' (binary red/blue accuracy) and 'outcome' (6-class accuracy).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    val_dataset = UFCDataset(X_val, y_val)
    val_loader = DataLoader(dataset=val_dataset, batch_size=64)
    
    outcome_correct = 0
    winner_correct = 0
    total = 0
    
    for batch_X, batch_y in val_loader:
        batch_X = batch_X.to(device)
        
        # Collect softmax predictions from each model
        all_probs = []
        for model in models:
            model.eval()
            with torch.no_grad():
                outputs = model(batch_X)
                probs = F.softmax(outputs, dim=1)
                all_probs.append(probs)
        
        # Average probabilities across ensemble
        avg_probs = torch.stack(all_probs).mean(dim=0)
        
        # 6-class outcome accuracy
        _, predicted_outcome = torch.max(avg_probs, 1)
        outcome_correct += (predicted_outcome.cpu() == batch_y).sum().item()
        
        # Binary winner accuracy (classes 0-2 = red, 3-5 = blue)
        predicted_winner = (predicted_outcome >= 3).long()
        actual_winner = (batch_y >= 3).long()
        winner_correct += (predicted_winner.cpu() == actual_winner).sum().item()
        
        total += batch_y.size(0)
    
    print("Ensemble winner accuracy:", winner_correct / total)
    print("Ensemble outcome accuracy:", outcome_correct / total)
    
    return {
        "winner": winner_correct / total,
        "outcome": outcome_correct / total
    }


def get_production_accuracy_from_db():
    """Fetch current production model's winner accuracy from Firestore."""
    db = firestore.Client(project="ufc-proj", database="ufcdb")
    doc = db.collection("metadata").document("model_version").get()
    if doc.exists:
        return doc.to_dict().get("winner_accuracy", 0.0)
    return 0.0

def get_current_version():
    """Fetch the current model version number from Firestore."""
    db = firestore.Client(project="ufc-proj", database="ufcdb")
    doc = db.collection("metadata").document("model_version").get()
    if doc.exists:
        return doc.to_dict().get("version", 0)
    return 0


def update_production_accuracy_in_db(winner_accuracy, version):
    """Update the production model metadata in Firestore."""
    db = firestore.Client(project="ufc-proj", database="ufcdb")
    db.collection("metadata").document("model_version").set({
        "winner_accuracy": winner_accuracy,
        "version": version,
        "trained_at": str(date.today())
    })


def promote_to_production(models, scaler_params, accuracy):
    """Export models + scaler to GCS and update Firestore metadata."""
    from google.cloud import storage
    
    client = storage.Client()
    bucket = client.bucket("ufc-proj-models")
    
    # Push all 4 ONNX files to GCS
    for i, model in enumerate(models):
        path = f"model_{i}.onnx"
        export_to_onnx(model, path)
        bucket.blob(f"production/{path}").upload_from_filename(path)
    
    # Feature order must match what the Go backend uses for calculateFeatures
    final_features = [
        "RedWinPct", "BlueWinPct", "WinPctDif","RedKoPct", "BlueKoPct", "KoPctDif",
        "RedSubPct", "BlueSubPct", "SubPctDif","RedDecPct", "BlueDecPct", "DecPctDif",
        "RedLossesByKO", "BlueLossesByKO", "LossesByKODif",
        "RedLossesBySub", "BlueLossesBySub", "LossesBySubDif",
        "RedLossesByDec", "BlueLossesByDec", "LossesByDecDif", "RedWeightLbs",
        "HeightDif", "ReachDif", "AgeDif","RedAge", "BlueAge",
        "SigStrDif", "StrPctDif", "TDDif", "SubAttDif",
        "RedAvgSigStrLanded", "BlueAvgSigStrLanded","RedAvgTDLanded", "BlueAvgTDLanded",
        "RedAvgSigStrPct", "BlueAvgSigStrPct","RedAvgSubAtt", "BlueAvgSubAtt",
        "SigStrAbsorbedDif","RedSigStrAbsorbed", "BlueSigStrAbsorbed","AvgRoundsDif",
        "RedAvgRounds", "BlueAvgRounds","EloDif", "OpponentEloDif","RedElo", "BlueElo",
        "WinStreakDif","RedCurrentWinStreak", "BlueCurrentWinStreak",
        "RedFinishL5", "BlueFinishL5", "FinishL5Dif","FinishPctDif"
    ]

    # Serialize scaler as name->value maps + saved_order (matches Go's ScalerMetadata struct)
    means = scaler_params.mean_.tolist()
    stds = scaler_params.scale_.tolist()
    scaler_dict = {
        "means": {name: val for name, val in zip(final_features, means)},
        "stds": {name: val for name, val in zip(final_features, stds)},
        "saved_order": final_features
    }
    bucket.blob("production/scaler_params.json").upload_from_string(
        json.dumps(scaler_dict)
    )
    
    # Update version.json so Go backend knows to reload
    version = get_current_version() + 1
    version_data = {
        "version": version,
        "winner_accuracy": accuracy["winner"],
        "trained_at": str(date.today())
    }
    bucket.blob("production/version.json").upload_from_string(
        json.dumps(version_data)
    )
    
    # Update accuracy + version in Firestore
    update_production_accuracy_in_db(accuracy["winner"], version)