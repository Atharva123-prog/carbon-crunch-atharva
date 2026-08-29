import streamlit as st
import os
import json
from PIL import Image
import pandas as pd
from src.pipeline import ReceiptPipeline

st.set_page_config(
    page_title="CARBON CRUNCH - Receipt OCR & Financial Intelligence",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e364f;
    }
    .badge-high {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-low {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_pipeline():
    return ReceiptPipeline(gpu=False)

pipeline = get_pipeline()

st.title("🧾 CARBON CRUNCH - Receipt OCR & Financial Intelligence")
st.markdown("Automated receipt parsing, field extraction, multi-factor confidence scoring & expense summary analytics.")

raw_dir = "data/raw_receipts"
output_dir = "outputs"
json_dir = os.path.join(output_dir, "receipts_json")
summary_file = os.path.join(output_dir, "expense_summary.json")

tab1, tab2, tab3 = st.tabs(["🔍 Receipt Extractor", "📊 Expense Dashboard", "⚡ Batch Processor"])

with tab1:
    st.header("Single Receipt Information Extraction")

    receipt_files = []
    if os.path.exists(raw_dir):
        receipt_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

    col_input, col_action = st.columns([3, 1])
    with col_input:
        selected_file = st.selectbox("Select Receipt Image from Dataset:", receipt_files if receipt_files else ["None"])
    with col_action:
        uploaded_file = st.file_uploader("Or Upload Receipt Image", type=["jpg", "jpeg", "png"])

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
        if st.button("Process & Extract Key Information", type="primary"):
            with st.spinner("Processing image, running EasyOCR and confidence scorer..."):
                res = pipeline.process_single_receipt(active_image_path, save_visualization=True, output_dir=output_dir)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("Original Image")
                st.image(active_image_path, use_container_width=True)
            with c2:
                st.subheader("Bounding Box Overlay")
                if res["visualization_path"] and os.path.exists(res["visualization_path"]):
                    st.image(res["visualization_path"], use_container_width=True)
                else:
                    st.info("Visualization unavailable")
            with c3:
                st.subheader("Extracted Metadata")
                conf_data = res["confidence_output"]

                store_conf = conf_data["store_name"]["confidence"]
                store_badge = '<span class="badge-high">HIGH</span>' if store_conf >= 0.7 else '<span class="badge-low">LOW</span>'
                st.markdown(f"**Store Name**: `{conf_data['store_name']['value']}` {store_badge} (Conf: `{store_conf}`)", unsafe_allow_html=True)

                date_conf = conf_data["date"]["confidence"]
                date_badge = '<span class="badge-high">HIGH</span>' if date_conf >= 0.7 else '<span class="badge-low">LOW</span>'
                st.markdown(f"**Date**: `{conf_data['date']['value']}` {date_badge} (Conf: `{date_conf}`)", unsafe_allow_html=True)

                tot_conf = conf_data["total_amount"]["confidence"]
                tot_badge = '<span class="badge-high">HIGH</span>' if tot_conf >= 0.7 else '<span class="badge-low">LOW</span>'
                st.markdown(f"**Total Amount**: `${conf_data['total_amount']['value']}` {tot_badge} (Conf: `{tot_conf}`)", unsafe_allow_html=True)

                items = conf_data["items"]["value"]
                st.markdown(f"**Extracted Items ({len(items)})**:")
                if items:
                    st.dataframe(pd.DataFrame(items), use_container_width=True)
                else:
                    st.write("No item lines identified")

                st.subheader("Structured JSON Output")
                st.json(conf_data)

with tab2:
    st.header("Financial Expense Analytics Summary")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        fin = summary_data.get("financial_summary", {})
        rel = summary_data.get("reliability_summary", {})

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Expense", f"${fin.get('total_spend', 0.0):,.2f}")
        m2.metric("Total Transactions", fin.get("number_of_transactions", 0))
        m3.metric("Avg Transaction Spend", f"${fin.get('average_transaction_spend', 0.0):,.2f}")
        m4.metric("Reliability Rate", f"{rel.get('reliability_percentage', 0.0)}%")

        st.divider()
        st.subheader("Spend per Store Breakdown")
        store_data = fin.get("spend_per_store", {})
        if store_data:
            df_store = pd.DataFrame.from_dict(store_data, orient="index").reset_index()
            df_store.rename(columns={"index": "Store Name"}, inplace=True)

            c_chart, c_table = st.columns([1, 1])
            with c_chart:
                st.bar_chart(data=df_store, x="Store Name", y="total_spend")
            with c_table:
                st.dataframe(df_store, use_container_width=True)

        st.divider()
        st.subheader("Transaction Register")
        tx_list = summary_data.get("all_transactions", [])
        if tx_list:
            df_tx = pd.DataFrame(tx_list)
            st.dataframe(df_tx, use_container_width=True)
    else:
        st.warning("Expense summary file not generated yet. Please run batch processing.")

with tab3:
    st.header("Batch Processing Engine")
    st.write(f"Process all receipt images located in `{raw_dir}`.")
    if st.button("Run Pipeline Batch Processing"):
        with st.spinner("Processing dataset receipts..."):
            batch_res = pipeline.process_directory(raw_dir, output_dir)
            st.success(f"Batch processing completed! Processed {batch_res['processed_count']} receipts.")
            st.rerun()
