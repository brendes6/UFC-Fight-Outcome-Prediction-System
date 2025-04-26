import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from feature_engineering import get_X_y
from data_cleaning import get_clean_data
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


def main():

    print("Do you want to overwrite the existing models? (y/n)")
    overwrite = input()
    if overwrite != "y":
        return
    
    # Get data for unknown odds dataset
    df1 = get_clean_data()
    X1, y1 = get_X_y(df1, known_odds=False)
    
    # We want 6 models with >39% accuracy
    models_needed = 6
    threshold = 39

    i = 0
    while i < models_needed:
        k = 5

        # Stratified K-Fold Cross Validation
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=np.random.randint(0, 1000))
        accuracies = []
        for fold, (train_idx, val_idx) in enumerate(skf.split(X1, y1)):
            X1_train, X1_val = X1[train_idx], X1[val_idx]
            y1_train, y1_val = y1[train_idx], y1[val_idx]
            model = build_model(X1_train.shape[1], 6)
            model, val_acc = train_model(model, X1_train, y1_train, X1_val, y1_val, 40)
            accuracies.append(val_acc)

            # If model has >39% accuracy, save the model
            if val_acc > threshold:
                torch.save(model.state_dict(), f"../Models/Unknown_Odds/ufc_model_{i}.pth")
                i += 1
                break
        
    # Get data for known odds dataset
    df2 = get_clean_data()
    X2, y2 = get_X_y(df2, known_odds=True)

    # We want 6 models with >41.5% accuracy
    models_needed = 6
    threshold = 41.5

    i = 0
    while i < models_needed:
        k = 5
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=np.random.randint(0, 1000))
        for fold, (train_idx, val_idx) in enumerate(skf.split(X2, y2)):
            X2_train, X2_val = X2[train_idx], X2[val_idx]
            y2_train, y2_val = y2[train_idx], y2[val_idx]
            model = build_model(X2_train.shape[1], 6)
            model, val_acc = train_model(model, X2_train, y2_train, X2_val, y2_val, 41.5)
        
            if val_acc > threshold:
                torch.save(model.state_dict(), f"../Models/Known_Odds/ufc_model_{i}.pth")
                i += 1
                break

        


if __name__ == "__main__":
    main()