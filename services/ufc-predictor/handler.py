import torch
import torch.nn as nn
import torch.nn.functional as F
import os

# Our custom model class
class NN(nn.Module):
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
    
    def forward(self, x):
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        x = F.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)
        x = self.fc4(x)
        return x

class EndpointHandler:
    def __init__(self, model_dir):
        # Load our custom model here
        self.model_path = os.path.join(model_dir, "model.pt")

        state_dict = torch.load(self.model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = NN(input_size=56, output_size=6).to(self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def __call__(self, data):
        # Process the input data and generate predictions using our model
        instances = data.get("inputs")
        tensor = torch.tensor(instances, dtype=torch.float32).to(self.device)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
        with torch.no_grad():
            output = self.model(tensor)

        probabilities = F.softmax(output, dim=1)
        return [{"predictions": probabilities.tolist()}]
