import json
from google.cloud import firestore


db = firestore.Client(project="ufc-proj", database="ufcdb")
    
# 2. Load your JSON file
with open("scaler.json", 'r') as f:
    scaling_data = json.load(f)

# 3. Reference (or create) a 'metadata' collection and 'scaler' document
# Using 'set' will create the document if it doesn't exist
doc_ref = db.collection("metadata").document("scaler_constants")

# 4. Upload the data
# Firestore supports maps (dictionaries) natively
doc_ref.set(scaling_data)