# SuperKart Sales Forecast: Model Deployment

A sales-forecasting model for **SuperKart**, a retail chain of supermarkets and food marts. It predicts the revenue a product will generate in a given store, and it is deployed as a **Flask REST API** with a **Streamlit web UI**. Each runs in its own Docker container, and the two are connected over a Docker network inside a GitHub Codespace.

> Project for the *Model Deployment* module of the Post Graduate Program in AI & ML: Business Applications (McCombs School of Business, The University of Texas at Austin).

## Business problem
SuperKart wants accurate quarterly revenue forecasts for each product in each outlet. The forecasts feed inventory and procurement planning and regional sales strategy. The forecasting model also has to be usable from SuperKart's own systems, not just a notebook, so it is served as an API with a simple front end for business users.

## Data
8,763 product–store records with 12 columns, from 4 stores (Departmental Store, Supermarket Type 1 and Type 2, Food Mart) across Tier 1–3 cities. The target is `Product_Store_Sales_Total`.

**Engineered features**, which are also the API input schema:

| Feature | Built from |
|---|---|
| `Product_Id_char` | first two letters of `Product_Id` (FD = food, DR = drinks, NC = non-consumables) |
| `Store_Age_Years` | 2025 − `Store_Establishment_Year` |
| `Product_Type_Category` | `Product_Type` grouped into Perishables / Non Perishables |

## Model
Random Forest and XGBoost were each trained inside a scikit-learn pipeline that includes one-hot encoding, then tuned with `GridSearchCV` (5-fold CV, RMSE scoring).

| Model | Test RMSE | Test R² | Test MAPE | CV RMSE |
|---|---|---|---|---|
| Random Forest (default) | 290.9 | 0.927 | 3.83% | n/a |
| XGBoost (default) | 300.1 | 0.922 | 4.58% | n/a |
| **Random Forest (tuned), final** | **283.2** | **0.930** | **3.67%** | **279.8** |
| XGBoost (tuned) | 284.8 | 0.930 | 3.85% | 282.2 |

The final model is serialized with `joblib` as `backend_files/superkart_model.joblib`. It is a single pipeline, encoder plus model, so it takes the raw feature values directly.

**Key insights**
- Product MRP and weight are the strongest revenue drivers (correlation with sales of 0.79 and 0.74).
- The store matters more than the product. Every product type sells nearly 3× more per item in the Tier 1 Departmental Store than in the Tier 3 Food Mart.
- Display (shelf) area has no relationship with sales (r ≈ 0.00), so shelf space could be reallocated.

## Architecture
```
            ┌──────────────── Docker network: superkart-net ────────────────┐
 User ───▶  │  superkart-frontend (Streamlit, :8501) ──▶ superkart-backend  │ ◀─── API clients
            │                                            (Flask + gunicorn, │      (e.g. Colab,
            │                                             :7860, model)     │       planning systems)
            └────────────────────────────────────────────────────────────────┘
```
The frontend has no model of its own: it calls the backend at `BACKEND_URL` (default `http://superkart-backend:7860`). Either side can be updated or scaled independently.

## API
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/v1/predict` | Online inference: one JSON record → `{"Predicted Sales": value}` |
| POST | `/v1/predictbatch` | Batch inference: CSV file in form field `file` → `{"row index": value, ...}` |

Example request:
```bash
curl -X POST <API_URL>/v1/predict -H "Content-Type: application/json" -d '{
  "Product_Weight": 12.66, "Product_Sugar_Content": "Low Sugar", "Product_Allocated_Area": 0.027,
  "Product_MRP": 117.08, "Store_Size": "Medium", "Store_Location_City_Type": "Tier 2",
  "Store_Type": "Supermarket Type2", "Product_Id_char": "FD", "Store_Age_Years": 16,
  "Product_Type_Category": "Non Perishables"}'
# {"Predicted Sales": 2910.0}
```
Incomplete or invalid input returns HTTP 400 with an explanation. Categories not seen in training are handled safely by the encoder (`handle_unknown="ignore"`).

## Run it
In a GitHub Codespace, or on any machine with Docker:
```bash
bash run_containers.sh
```
This builds both images, creates the `superkart-net` network and starts both containers. The API is on port **7860** and the UI on port **8501**. In a Codespace, set port 7860 to *Public* in the Ports tab to call the API from outside.

## Repository layout
```
backend_files/
  app.py                  # Flask API (online + batch endpoints)
  superkart_model.joblib  # serialized pipeline (encoder + tuned Random Forest)
  requirements.txt        # pinned to the training versions
  Dockerfile              # python:3.12-slim + gunicorn on port 7860
frontend_files/
  app.py                  # Streamlit UI (single + batch forecasts, CSV download)
  requirements.txt
  Dockerfile              # Streamlit on port 8501
run_containers.sh         # builds and runs both containers on a shared network
```

## Tech stack
Python · pandas · scikit-learn · XGBoost · joblib · Flask · gunicorn · Streamlit · Docker · GitHub Codespaces

---
Author: **Anoop Krishnan**
