import os

import pandas as pd
import requests
import streamlit as st

# Backend address: the backend container's name on the shared Docker network
BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860").rstrip("/")

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="centered")
st.title("SuperKart Sales Forecast")
st.caption("Forecast the sales revenue of a product in a SuperKart outlet for the upcoming quarter.")

single_tab, batch_tab = st.tabs(["Single forecast", "Batch forecast"])

with single_tab:
    st.subheader("Product details")
    col1, col2 = st.columns(2)
    with col1:
        product_id_char = st.selectbox("Product family (Product_Id prefix)", ["FD", "DR", "NC"],
                                       help="FD = food, DR = drinks, NC = non-consumables")
        product_type_category = st.selectbox("Product category", ["Perishables", "Non Perishables"])
        sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
    with col2:
        mrp = st.number_input("Product MRP", min_value=1.0, max_value=500.0, value=147.0, step=1.0)
        weight = st.number_input("Product weight", min_value=1.0, max_value=50.0, value=12.65, step=0.1)
        area = st.number_input("Allocated display area (ratio)", min_value=0.001, max_value=1.0,
                               value=0.068, step=0.001, format="%.3f")

    st.subheader("Store details")
    col3, col4 = st.columns(2)
    with col3:
        store_type = st.selectbox("Store type", ["Supermarket Type1", "Supermarket Type2",
                                                 "Departmental Store", "Food Mart"])
        store_size = st.selectbox("Store size", ["Small", "Medium", "High"], index=1)
    with col4:
        city_tier = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"], index=1)
        store_age = st.number_input("Store age (years)", min_value=0, max_value=100, value=16, step=1)

    payload = {
        "Product_Weight": weight,
        "Product_Sugar_Content": sugar,
        "Product_Allocated_Area": area,
        "Product_MRP": mrp,
        "Store_Size": store_size,
        "Store_Location_City_Type": city_tier,
        "Store_Type": store_type,
        "Product_Id_char": product_id_char,
        "Store_Age_Years": store_age,
        "Product_Type_Category": product_type_category,
    }

    if st.button("Predict sales", type="primary"):
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if resp.ok:
                st.success("Forecast ready")
                st.metric("Predicted product-store sales", f"{resp.json()['Predicted Sales']:,.2f}")
            else:
                st.error(f"API error {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the forecasting API at {BACKEND_URL}: {exc}")

with batch_tab:
    st.write("Upload a CSV with the columns: `" + "`, `".join(payload.keys()) + "`.")
    uploaded = st.file_uploader("Batch CSV", type="csv")
    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        st.dataframe(batch_df.head(), use_container_width=True)
        if st.button("Predict batch", type="primary"):
            try:
                resp = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                     files={"file": batch_df.to_csv(index=False).encode("utf-8")}, timeout=120)
                if resp.ok:
                    preds = pd.Series(resp.json(), name="Predicted_Sales")
                    preds.index = preds.index.astype(int)
                    result = batch_df.join(preds.sort_index())
                    st.dataframe(result, use_container_width=True)
                    st.metric("Total forecast revenue", f"{result['Predicted_Sales'].sum():,.2f}")
                    st.download_button("Download forecasts", result.to_csv(index=False),
                                       file_name="superkart_forecasts.csv", mime="text/csv")
                else:
                    st.error(f"API error {resp.status_code}: {resp.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the forecasting API at {BACKEND_URL}: {exc}")
