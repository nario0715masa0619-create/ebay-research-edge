"""
Streamlit Dashboard for eBay-Research-Edge
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import config

st.set_page_config(
    page_title="eBay-Research-Edge",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔍 eBay-Research-Edge")
st.markdown("**Research Support Tool for Japanese eBay Sellers**")
st.markdown(f"Category: {config.category_name} ({config.category_name_ja})")

with st.sidebar:
    st.header("⚙️ Settings")
    
    keyword = st.text_input(
        "Search Keyword",
        value="pokemon card",
        help="Enter the product keyword to search"
    )
    
    limit = st.slider(
        "Max Listings per Source",
        min_value=10,
        max_value=100,
        value=50,
        step=10
    )
    
    if st.button("🚀 Run Research", use_container_width=True, type="primary"):
        st.session_state.run_pipeline = True
    
    st.divider()
    
    st.subheader("ℹ️ About")
    st.info("This tool compares eBay Sold data with domestic prices (Mercari)")

if st.session_state.get('run_pipeline', False):
    with st.spinner("⏳ Running research pipeline..."):
        try:
            from app import run_research_pipeline
            output_path = run_research_pipeline(keyword=keyword, limit=limit)
            
            if output_path:
                st.success("✅ Research completed!")
            else:
                st.error("❌ Pipeline failed")
            st.session_state.run_pipeline = False
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.session_state.run_pipeline = False

st.header("📊 Results")

processed_dir = config.processed_data_dir
csv_files = list(processed_dir.glob("candidates_*.csv"))

if csv_files:
    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest_file = csv_files[0]
    
    df = pd.read_csv(latest_file)
    
    st.subheader("📈 Summary Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Candidates", len(df))
    
    with col2:
        list_count = len(df[df['decision_status'] == 'list_candidate'])
        st.metric("List Candidates", list_count)
    
    with col3:
        hold_count = len(df[df['decision_status'] == 'hold'])
        st.metric("Hold", hold_count)
    
    with col4:
        skip_count = len(df[df['decision_status'] == 'skip'])
        st.metric("Skip", skip_count)
    
    st.divider()
    
    st.subheader("🔍 Filter & Sort")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Decision Status",
            options=df['decision_status'].unique(),
            default=df['decision_status'].unique()
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            options=['candidate_score', 'estimated_profit_jpy', 'str', 'sold_30d']
        )
    
    with col3:
        sort_order = st.radio("Order", options=['Descending', 'Ascending'], horizontal=True)
    
    df_filtered = df[df['decision_status'].isin(status_filter)].copy()
    df_filtered = df_filtered.sort_values(
        by=sort_by,
        ascending=(sort_order == 'Ascending')
    )
    
    st.divider()
    
    st.subheader("📋 Candidate List")
    
    display_cols = [
        'item_name', 'sold_30d', 'median_price_usd', 'domestic_min_price_jpy',
        'estimated_profit_jpy', 'str', 'candidate_score', 'decision_status'
    ]
    
    st.dataframe(
        df_filtered[display_cols],
        use_container_width=True,
        height=400
    )
    
    st.divider()
    
    st.subheader("💾 Download Results")
    
    csv_data = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv_data,
        file_name="research_results.csv",
        mime="text/csv",
        use_container_width=True
    )
    
else:
    st.info("💡 No results yet. Run research pipeline.")

st.divider()
st.markdown("**eBay-Research-Edge** | Phase 3 Dashboard")
