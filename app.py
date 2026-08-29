import streamlit as st
import os
import json
from PIL import Image
import pandas as pd
from src.pipeline import ReceiptPipeline

st.set_page_config(
    page_title="Carbon Crunch - Receipt OCR System",
    layout="wide"
)

st.markdown("""
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .header-container {
        background-color: #1e293b;
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 4px;
        margin-bottom: 0;
    }
    .stMetric {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 14px;
    }
    .status-badge-green {
        background-color: #15803d;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    .status-badge-red {
        background-color: #b91c1c;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    .footer-container {
        border-top: 1px solid #e2e8f0;
        padding: 16px 0;
        margin-top: 40px;
        text-align: center;
        color: #64748b;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <div class="header-title">CARBON CRUNCH</div>
    <div class="header-subtitle">Receipt OCR Information Extraction & Financial Intelligence Platform</div>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def get_pipeline():
    return ReceiptPipeline(gpu=False)

pipeline = get_pipeline()

raw_dir = "data/raw_receipts"
output_dir = "outputs"
json_dir = os.path.join(output_dir, "receipts_json")
summary_file = os.path.join(output_dir, "expense_summary.json")

tab1, tab2, tab3 = st.tabs(["Single Receipt Extractor", "Financial Summary & Items Breakdown", "Batch Processing"])

with tab1:
    st.header("Extract Receipt Information")

    receipt_files = []
    if os.path.exists(raw_dir):
        receipt_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    c_select, c_upload = st.columns([3, 1])
    with c_select:
        selected_file = st.selectbox("Select Receipt File:", receipt_files if receipt_files else ["None"])
    with c_upload:
        uploaded_file = st.file_uploader("Upload Image:", type=["jpg", "jpeg", "png"])

    active_image_path = None
    if uploaded_file is not None:
        temp_path = os.path.join("scratch", uploaded_file.name)
        os.makedirs("scratch", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        active_image_path = temp_path
    elif selected_file and selected_file != "None":
        active_image_path = os.path.join(raw_dir, selected_file)

    if active_image_path and os.path.exists(active_image_path):
        if st.button("Run Processing", type="primary"):
            with st.spinner("Processing image..."):
                res = pipeline.process_single_receipt(active_image_path, save_visualization=True, output_dir=output_dir)

            col_img, col_vis, col_data = st.columns(3)
            with col_img:
                st.subheader("Original Image")
                st.image(active_image_path, use_container_width=True)
            with col_vis:
                st.subheader("Text Overlay")
                if res["visualization_path"] and os.path.exists(res["visualization_path"]):
                    st.image(res["visualization_path"], use_container_width=True)
                else:
                    st.info("No overlay available.")
            with col_data:
                st.subheader("Extracted Fields")
                conf_data = res["confidence_output"]

                store_conf = conf_data["store_name"]["confidence"]
                store_badge = '<span class="status-badge-green">HIGH</span>' if store_conf >= 0.7 else '<span class="status-badge-red">LOW</span>'
                st.markdown(f"**Store Name**: `{conf_data['store_name']['value']}` {store_badge} (Conf: `{store_conf}`)", unsafe_allow_html=True)

                date_conf = conf_data["date"]["confidence"]
                date_badge = '<span class="status-badge-green">HIGH</span>' if date_conf >= 0.7 else '<span class="status-badge-red">LOW</span>'
                st.markdown(f"**Transaction Date**: `{conf_data['date']['value']}` {date_badge} (Conf: `{date_conf}`)", unsafe_allow_html=True)

                tot_conf = conf_data["total_amount"]["confidence"]
                tot_badge = '<span class="status-badge-green">HIGH</span>' if tot_conf >= 0.7 else '<span class="status-badge-red">LOW</span>'
                st.markdown(f"**Total Amount**: `${conf_data['total_amount']['value']}` {tot_badge} (Conf: `{tot_conf}`)", unsafe_allow_html=True)

                items = conf_data["items"]["value"]
                st.markdown(f"**Line Items ({len(items)})**:")
                if items:
                    st.dataframe(pd.DataFrame(items), use_container_width=True)
                else:
                    st.write("No items detected.")

                st.subheader("Structured JSON Output")
                st.json(conf_data)

with tab2:
    st.header("Financial Expense Summary & Purchase Analytics")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        fin = summary_data.get("financial_summary", {})
        rel = summary_data.get("reliability_summary", {})

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Spend", f"${fin.get('total_spend', 0.0):,.2f}")
        m2.metric("Transactions", fin.get("number_of_transactions", 0))
        m3.metric("Items Purchased", fin.get("total_items_purchased", 0))
        m4.metric("Avg Transaction", f"${fin.get('average_transaction_spend', 0.0):,.2f}")
        m5.metric("Reliability Rate", f"{rel.get('reliability_percentage', 0.0)}%")

        st.divider()
        st.subheader("Purchased Items Breakdown")
        st.write("Itemized summary of purchased items, quantities, and total expenditure across all receipts:")

        items_breakdown = fin.get("purchased_items_breakdown", [])
        if items_breakdown:
            df_items = pd.DataFrame(items_breakdown)
            df_items.columns = ["Item Description", "Quantity Purchased", "Total Spent ($)", "Avg Unit Price ($)"]

            col_item_table, col_item_chart = st.columns([3, 2])
            with col_item_table:
                st.dataframe(df_items, use_container_width=True)
            with col_item_chart:
                st.write("**Top Purchased Items by Total Spend ($)**")
                df_top_items = df_items.head(10)
                st.bar_chart(data=df_top_items, x="Item Description", y="Total Spent ($)")
        else:
            st.info("No line items extracted from processed receipts.")

        st.divider()
        st.subheader("Spend by Vendor / Store")
        store_data = fin.get("spend_per_store", {})
        if store_data:
            df_store = pd.DataFrame.from_dict(store_data, orient="index").reset_index()
            df_store.rename(columns={
                "index": "Vendor Name",
                "total_spend": "Total Spend ($)",
                "transaction_count": "Transactions",
                "average_spend": "Avg Spend ($)",
                "percentage_of_total": "Share (%)"
            }, inplace=True)

            c_chart, c_table = st.columns([1, 1])
            with c_chart:
                st.bar_chart(data=df_store, x="Vendor Name", y="Total Spend ($)")
            with c_table:
                st.dataframe(df_store, use_container_width=True)

        st.divider()
        st.subheader("Transaction Register")
        tx_list = summary_data.get("all_transactions", [])
        if tx_list:
            df_tx = pd.DataFrame(tx_list)
            st.dataframe(df_tx, use_container_width=True)
    else:
        st.warning("No summary available. Run batch processing first.")

with tab3:
    st.header("Batch Process Receipts")
    st.write(f"Process all receipt images in `{raw_dir}`.")
    if st.button("Start Batch Execution", type="primary"):
        with st.spinner("Processing dataset..."):
            batch_res = pipeline.process_directory(raw_dir, output_dir)
            st.success(f"Finished processing {batch_res['processed_count']} receipts.")
            st.rerun()

st.markdown("""
<div class="footer-container">
    Atharva Tiwari | Carbon Crunch Shortlisting Assignment
</div>
""", unsafe_allow_html=True)
