import joblib
from sklearn.preprocessing import StandardScaler
import json


scaler, saved_order = joblib.load("scaler.pkl")

mean, std = scaler.mean_, scaler.scale_

json_object = {"means":{}, "stds":{}, "saved_order":[]}

for i, val in enumerate(saved_order):
    json_object["means"][val] = mean[i]
    json_object["stds"][val] = std[i]
    json_object["saved_order"].append(val)

fp = open("scaler.json", "w")

json.dump(json_object, fp, indent=4)


print(len(scaler.mean_))