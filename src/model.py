import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from .feature_engineering import get_X_y
from .data_cleaning import get_clean_data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from sklearn.model_selection import StratifiedKFold

# Custom Dataset class for our UFC data
# Inherits from torch.utils.data.Dataset, converts data to tensors
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
        self.fc1 = nn.Linear(input_size, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.dropout1 = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.dropout2 = nn.Dropout(0.2)
        
        self.fc3 = nn.Linear(64, 32)
        self.bn3 = nn.BatchNorm1d(32)
        self.dropout3 = nn.Dropout(0.1)
        
        self.fc4 = nn.Linear(32, output_size)
    
    # Forward function
    def forward(self, x):
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        x = F.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)
        
        x = self.fc4(x)
        return x
    
# Build a model based on input size and output size
def build_model(input_size, output_size):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = NN(input_size, output_size).to(device)
    return model

# train the model
def train_model(model, X_train, y_train, X_val, y_val, breakpoint):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # initialize parameters
    learning_rate = 0.0005  
    num_epochs = 200 
    batch_size = 64  
    val_size = 0.2

    # Load from our custom ufc dataset
    train_dataset = UFCDataset(X_train, y_train)
    train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
    
    # If we have validation data, load it
    if X_val is not None and y_val is not None:
        val_dataset = UFCDataset(X_val, y_val)
        val_loader = DataLoader(dataset=val_dataset, batch_size=batch_size)
    
    # Initialize loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=6, factor=0.5)

    # Initialize best validation accuracy and patience
    best_val_acc = 0.0
    patience = 6
    counter = 0

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0

        # Iterate through the training data
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
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
            scheduler.step(avg_val_loss)
            
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss/len(train_loader):.4f}, Val Loss: {avg_val_loss:.4f}, Val Accuracy: {val_acc:.2f}%")
            
            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                counter = 0
            if val_acc > breakpoint:
                break
            else:
                counter += 1
                if counter >= patience:
                    print(f"Early stopping triggered at epoch {epoch+1}")
                    break
        else:
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {running_loss/len(train_loader):.4f}")

    return model, val_acc

def predict(model, features):
    # Pass features through model, softmax output to get probabilities
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()
    with torch.no_grad():
        features = torch.FloatTensor(features).to(device)
        outputs = model(features)
        # Apply softmax to get probabilities
        probabilities = F.softmax(outputs, dim=1)
        probabilities = probabilities.cpu().numpy()

    return probabilities

def build_models(known_odds, predicting_winner, models_needed, threshold, save_path, output_size):
    # Get data specific to known odds or unknown odds
    df = get_clean_data()
    X, y = get_X_y(df, known_odds=known_odds, predicting_winner=predicting_winner)

    i = 0
    while i < models_needed:
        # Stratified K-Fold Cross Validation
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=np.random.randint(0, 1000))
        for train_idx, val_idx in skf.split(X, y):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            model = build_model(X_train.shape[1], output_size)
            model, val_acc = train_model(model, X_train, y_train, X_val, y_val, threshold)

            # Save model if it has >threshold accuracy
            if val_acc > threshold:
                torch.save(model.state_dict(), f"{save_path}/ufc_model_{i}.pth")
                i += 1
                break


def main():

    print("Do you want to overwrite the existing models? (y/n)")
    overwrite = input()
    if overwrite != "y":
        return
    
    # build_models(False, False, 6, 40, "../Models/Unknown_Odds", 6)
    # build_models(True, False, 6, 41.5, "../Models/Known_Odds", 6)
    # build_models(False, True, 6, 70, "../Models/Predicting_Winner", 2)
    build_models(True, True, 6, 72, "../Models/Predicting_Winner_Odds", 2)

        


if __name__ == "__main__":
    main()