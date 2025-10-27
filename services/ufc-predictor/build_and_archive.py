import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import subprocess
import shutil
import inspect

# Configuring variables of our model
NUM_FEATURES = 56
OUTPUT_SIZE = 6 
WEIGHTS_FILE_PATH = 'model.pth' # Make sure this path is correct
BUILD_DIR = 'final_model_package_statedict'
MAR_EXPORT_PATH = 'model_store'
MODEL_VERSION = '2.0'

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

# Due to TorchServe restrictions on using a seperate model class in the same
# file as our handler, we turn essentially our entire handler
# script into a string that will be created and ran in a coming function.
HANDLER_CONTENT = """
import torch
import torch.nn.functional as F
from ts.torch_handler.base_handler import BaseHandler
from model import NN
import os

class UfcModelHandler(BaseHandler):
    def initialize(self, context):
        properties = context.system_properties
        self.map_location = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(self.map_location)
        self.manifest = context.manifest
        model_dir = properties.get("model_dir")
        model_file_path = os.path.join(model_dir, "model.pth")
        
        self.model = NN(input_size=56, output_size=6)
        self.model.load_state_dict(torch.load(model_file_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        self.initialized = True
        print("UFC model loaded from state_dict successfully.")

    def preprocess(self, data):
        instances = data[0]
        
        # Create the tensor
        tensor = torch.tensor(instances, dtype=torch.float32).to(self.device)
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)
            
        return tensor

    def inference(self, model_input):
        # Inference should only return the raw tensor output from the model
        with torch.no_grad():
            output = self.model(model_input)
        return output

    def postprocess(self, inference_output):
        # Postprocess converts the tensor to a JSON-friendly list and applies softmax
        probabilities = F.softmax(inference_output, dim=1)
        return [{"predictions": probabilities.tolist()}]
"""

# Our build function. This builds our custom handler and
# execute model archiver in a seperate directory from this service.
def build_model_archive():
    print("--- Starting state_dict build and archive process ---")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    model_source = inspect.getsource(NN)
    with open(os.path.join(BUILD_DIR, 'model.py'), 'w') as f:
        f.write("import torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n\n")
        f.write(model_source)
    print(f"Saved model class to {BUILD_DIR}/model.py")

    shutil.copy(WEIGHTS_FILE_PATH, os.path.join(BUILD_DIR, "model.pth"))
    print(f"Copied weights file to {BUILD_DIR}/")

    with open(os.path.join(BUILD_DIR, 'handler.py'), 'w') as f:
        f.write(HANDLER_CONTENT)
    print(f"Saved handler to {BUILD_DIR}/handler.py")

    command = [
        'torch-model-archiver', '--model-name', 'ufc_predictor', '--version', MODEL_VERSION,
        '--model-file', os.path.join(BUILD_DIR, 'model.py'),
        '--handler', os.path.join(BUILD_DIR, 'handler.py'),
        '--extra-files', os.path.join(BUILD_DIR, "model.pth"),
        '--export-path', MAR_EXPORT_PATH, '--force'
    ]
    
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("--- ERROR: torch-model-archiver failed ---"); print(result.stderr)
    else:
        print("--- SUCCESS ---"); print(result.stdout)

if __name__ == '__main__':
    build_model_archive()