import os

import joblib
import pandas as pd
from flask import Flask, jsonify, request

# Initialise the Flask app
superkart_api = Flask("SuperKart Sales Forecast API")

# Load the serialized pipeline once at start-up (it sits next to this file)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superkart_model.joblib")
model = joblib.load(MODEL_PATH)

# Features the model expects, in training order
FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type",
    "Product_Id_char", "Store_Age_Years", "Product_Type_Category",
]
NUMERIC = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def to_frame(records):
    """Turn a list of dicts into a model-ready DataFrame with numeric columns cast to float."""
    df = pd.DataFrame(records)[FEATURES]
    df[NUMERIC] = df[NUMERIC].astype(float)
    return df


@superkart_api.get("/")
def home():
    """Health check."""
    return "Welcome to the SuperKart Sales Forecast API"


@superkart_api.post("/v1/predict")
def predict_sales():
    """Online inference: one JSON record in, one sales forecast out."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    missing = [f for f in FEATURES if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400
    try:
        prediction = float(model.predict(to_frame([data]))[0])
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid input: {exc}"}), 400
    return jsonify({"Predicted Sales": round(prediction, 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Batch inference: CSV file (form field 'file') in, {row index: forecast} out."""
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file in the 'file' form field"}), 400
    batch = pd.read_csv(request.files["file"])
    missing = [f for f in FEATURES if f not in batch.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {missing}"}), 400
    try:
        predictions = model.predict(to_frame(batch.to_dict(orient="records")))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid input: {exc}"}), 400
    return jsonify({str(idx): round(float(p), 2) for idx, p in zip(batch.index, predictions)})


if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
