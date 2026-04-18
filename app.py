##1. app.py

import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid
from core import calculate_rfm
from reports import (
    final_report_to_email,
    final_report_to_marketing,
    build_rfm_pivot
)
from plots import plot_segment_donut, plot_heatmap

#=========================first block====================================

# Page configuration
st.set_page_config(
    page_title="RFM Analyser", 
    page_icon="📊", 
    layout="wide"
)

# Data loading function with caching for large files optimization
@st.cache_data(show_spinner="Loading and processing file...")
def load_data(file):
    """Reads file depending on extension. 
    For large data volumes, CSV is recommended."""
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        # Warning: large .xlsx files can heavily impact memory
        return pd.read_excel(file)

def find_columns(df):
    """Automatic column index search by keywords"""
    cols = [c.lower() for c in df.columns]

    keywords = {
        'id': ['id', 'client', 'customer', 'клиент', 'покупатель', 'номер'],
        'date': ['date', 'time', 'дата', 'день', 'заказ'],
        'revenue': ['revenue', 'amount', 'sales', 'цена', 'сумма', 'выручка', 'total']
    }

    def get_index(keys):
        for i, col in enumerate(cols):
            if any(k in col for k in keys):
                return i
        return None

    return {
        'id': get_index(keywords['id']),
        'date': get_index(keywords['date']),
        'revenue': get_index(keywords['revenue'])
    }

# Session state initialization
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# Interface header
st.markdown("<h2 style='text-align: center; color: white;'>RFM Customer Base Analysis</h2>", unsafe_allow_html=True)#📊 

# Demo mode block
demo_button = st.button("Try DEMO", use_container_width=True) #🚀 

if demo_button:
    st.session_state.demo_mode = True

st.info(
    "**Instruction:** Upload a file with customer transactions.\n"
    "The file must contain:\n"
    "- 🆔 Customer ID\n"
    "- 📅 Purchase date\n"
    "- 💰 Purchase amount"
)

# File upload by user
uploaded_file = st.file_uploader("Upload your data", type=['xlsx', 'csv'], key="file_uploader_key")#📂 

# Data source selection logic
if st.session_state.demo_mode:
    try:
        df = pd.read_excel("data/abc_xyz_analisis_table.xlsx")
        st.success("Demo dataset loaded") #✅  
    except FileNotFoundError:
        df = pd.read_excel("/home/dmitrii/Jupyter_Python_SQL/rfm_project/data/abc_xyz_analisis_table.xlsx")
        st.success("Demo dataset loaded") #✅ 

elif uploaded_file is not None:
    df = load_data(uploaded_file)

else:
    st.info("ℹ️ Upload your data or click the DEMO button above")
    st.stop()

# Data clearing button
col1, col2 = st.columns(2)
with col1:
    submitted = st.button(
        label="🗑️ Clear data",
        use_container_width=True, 
        type="secondary"
    )

if submitted:
    keys_to_clear = [
        "demo_mode",
        "analysis_done",
        "col_id",
        "col_date",
        "col_amount",
        "file_uploader_key"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

st.write("Your source data (first 3 rows):")#👀
st.dataframe(df.head(3))

# Automatic column detection
found_indices = find_columns(df)
auto_success = all(v is not None for v in found_indices.values())


# Column mapping
if auto_success:
    col_id = df.columns[found_indices['id']]
    col_date = df.columns[found_indices['date']]
    col_amount = df.columns[found_indices['revenue']]
    auto_run = True
else:
    st.warning("⚠️ Could not automatically detect columns. Select them manually below.")

# Column mapping settings (continued)
    with st.expander("Column Mapping Settings", expanded=True): #⚙️ 
        col_id = st.selectbox("Customer ID", df.columns)
        col_date = st.selectbox("Order Date", df.columns)
        col_amount = st.selectbox("Revenue", df.columns)

        auto_run = False
#=========================second block====================================
# Manual run button creation
# Button is displayed ONLY if automatic detection failed
rfm_button = False

if not auto_run:
    rfm_button = st.button("RUN RFM ANALYSIS", use_container_width=True)#🚀 

# Manual column selection validation       
if rfm_button:
    if col_id is None or col_date is None or col_amount is None:
        st.warning("⚠️ Please select all required columns!")
        st.stop()

    # Prevent selecting the same column for different metrics
    if len({col_id, col_date, col_amount}) < 3:
        st.warning("⚠️ Cannot select the same column multiple times!")
        st.stop()

# Analysis readiness determination       
# Option 1: File uploaded and auto-detection succeeded
if uploaded_file and auto_run:      
    st.session_state.analysis_done = True

# Option 2: File uploaded, auto-detection failed, but manual run button pressed
elif uploaded_file and rfm_button:  
    st.session_state.analysis_done = True

# Option 3: Demo mode activated
elif st.session_state.get("demo_mode", False):  
    st.session_state.analysis_done = True

# RFM analysis execution
if st.session_state.get("analysis_done", False):

    # Create working dataframe from selected columns
    rfm_df = df[[col_id, col_date, col_amount]].copy()

    # Assign unified technical column names
    rfm_df.columns = ['customer_id', 'order_date', 'revenue']
    st.session_state.analysis_done = True

    # Minimum data volume check for correct analysis
    if len(rfm_df) < 5:
        st.warning("⚠️ Insufficient data for analysis (minimum 5 records required).") 
        st.stop()

    # Unique customers count check
    if rfm_df['customer_id'].nunique() < 3:
        st.warning("⚠️ Too few unique customers for correct segment distribution.")
        st.stop()

    # Data types validation (most resource-intensive part for large files)
    with st.spinner("🔄 Checking data formats and cleaning missing values..."):
        rfm_df['order_date'] = pd.to_datetime(rfm_df['order_date'], errors='coerce')
        rfm_df['revenue'] = pd.to_numeric(rfm_df['revenue'], errors='coerce')

        # Check for empty values after type conversion
        if rfm_df.isnull().any().any():
            st.error("❌ Data error: some values could not be converted to date or number.")
            st.write("👀 Problematic rows (first 5):")

            # Show rows with errors for manual debugging by user
            st.dataframe(rfm_df[rfm_df.isnull().any(axis=1)].head())       
            st.stop()

    # In the next part we call RFM analysis functions...

#=========================third block====================================
        # Call RFM analysis functions
        with st.spinner("📊 Calculating RFM metrics..."):
            rfm = calculate_rfm(rfm_df)

            # Assuming these functions are also optimized
            email_report = final_report_to_email(rfm)
            marketing_report = final_report_to_marketing(rfm)
            pivot = build_rfm_pivot(rfm)

# Dropdown styling
    st.markdown("""
        <style>
        div[data-baseweb="select"] {
            cursor: pointer !important;
        }

        div[data-baseweb="select"] > div:hover {
            background-color: var(--secondary-background-color) !important;
            transition: background-color 0.02s ease-in-out !important;
        }
        </style>
    """, unsafe_allow_html=True)

# =========================== KPI Metrics =========================== 

    # 1. First let user select a segment
    segment_options = ["All Segments"] + list(rfm['Segment'].unique())
    segment = st.selectbox(
        "👀 Select customer segment for filtering:",
        options=segment_options,
        index=None,
        placeholder="Click to select a segment..." 
    )

    # 2. Filter data ABOVE metrics output
    rfm_filtered = rfm.copy()
    if segment is not None and segment != "All Segments":
        rfm_filtered = rfm_filtered[rfm_filtered['Segment'] == segment]

    # 3. Calculate and display KPIs for filtered data
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Customers in segment",
        f"{rfm_filtered['customer_id'].nunique():,}".replace(",", " ")
    )

    col2.metric(
        "Segment revenue",
        f"{int(rfm_filtered['monetary'].sum()):,}".replace(",", " ") + " $"
    )

    col3.metric(
        "Average order value",
        f"{int(rfm_filtered['monetary'].mean()):,}".replace(",", " ") + " $"
    )

    # 4. Display the table itself
    st.subheader(
        "RFM Results Table", 
        help="This is your complete customer base with calculated scores: "
             "Recency, Frequency, and Monetary."
    )

    # For very large datasets, displaying the entire table in browser may slow it down.
    # Streamlit handles this well via lazy loading in st.dataframe, but it's worth mentioning.
    st.dataframe(rfm_filtered, use_container_width=True)

# =========================== Special Reports Generation =========================== 

    # 1. "Rescue Group" report (Losing loyal and at-risk customers)
    rescue_segments = ['At Risk (Churn Risk)', 'Loyal']
    rescue_report = rfm[rfm['Segment'].isin(rescue_segments)].copy()

    # Keep only columns needed by marketing and sort by days since purchase (recency)
    rescue_report = rescue_report[['customer_id', 'Segment', 'recency', 'monetary']].sort_values(by='recency', ascending=False)

    # 2. "Potential Stars" report (Newcomers and average customers)
    stars_segments = ['New Customers', 'Average']
    stars_report = rfm[rfm['Segment'].isin(stars_segments)].copy()

    # Keep needed columns and sort by purchase amount (monetary) to see most promising
    stars_report = stars_report[['customer_id', 'Segment', 'frequency', 'monetary']].sort_values(by='monetary', ascending=False)    

#=========================fourth block====================================
    # 1. Create main header for reports block
    st.subheader("Ready Analytics Reports")

    # 2. Create 4 tabs (fill all 4)
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📧 For Email",
            "📈 For Marketing",
            "🆘 Rescue Group",
            "⭐ Potential Stars",
        ]
    )

    # === TAB 1: Email Report ===
    with tab1:
        st.info(
            "📧 For Email / CRM: Ready list of customers with their segments. "
            "Upload this file to your email service or CRM to make targeted offers to different groups."
        )
        st.dataframe(email_report, use_container_width=True)

        # Prepare Excel file in memory
        buffer_email = io.BytesIO()
        with pd.ExcelWriter(buffer_email, engine="xlsxwriter") as writer:
            email_report.to_excel(writer, sheet_name="Email Report", index=False)
        excel_data_email = buffer_email.getvalue()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=excel_data_email,
                file_name="rfm_email_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="📥 Download CSV",
                data=email_report.to_csv(index=False),
                file_name="rfm_email_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # === TAB 2: Marketing Report ===
    with tab2:
        st.info(
            "📈 For Marketing: Summary report on each segment's effectiveness. "
            "Helps see which customer groups bring you the most money and where average order value is higher."
        )
        st.dataframe(marketing_report, use_container_width=True)

        # Prepare Excel file in memory
        buffer_marketing = io.BytesIO()
        with pd.ExcelWriter(buffer_marketing, engine="xlsxwriter") as writer:
            marketing_report.to_excel(writer, sheet_name="Marketing Report", index=False)
        excel_data_marketing = buffer_marketing.getvalue()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=excel_data_marketing,
                file_name="rfm_marketing_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="📥 Download CSV",
                data=marketing_report.to_csv(index=False),
                file_name="rfm_marketing_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # === TAB 3: Rescue Group ===
    with tab3:
        st.info(
            "🆘 Rescue Group: Customers who bought frequently or in large amounts "
            "but haven't ordered anything for a long time. Contact them urgently!"
        )
        st.dataframe(rescue_report, use_container_width=True)

        # Prepare Excel file in memory
        buffer_rescue = io.BytesIO()
        with pd.ExcelWriter(buffer_rescue, engine="xlsxwriter") as writer:
            rescue_report.to_excel(writer, sheet_name="Rescue Group", index=False)
        excel_data_rescue = buffer_rescue.getvalue()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=excel_data_rescue,
                file_name="rfm_rescue_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="📥 Download CSV",
                data=rescue_report.to_csv(index=False),
                file_name="rfm_rescue_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # === TAB 4: Potential Stars ===
    with tab4:
        st.info(
            "⭐ Potential Stars: Newcomers and average customers with good order value. "
            "They are loyal and have potential to become your VIP clients. Offer them a bonus for their next purchase!"
        )
        st.dataframe(stars_report, use_container_width=True)

        # Prepare Excel file in memory
        buffer_stars = io.BytesIO()
        with pd.ExcelWriter(buffer_stars, engine="xlsxwriter") as writer:
            stars_report.to_excel(writer, sheet_name="Potential Stars", index=False)
        excel_data_stars = buffer_stars.getvalue()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=excel_data_stars,
                file_name="rfm_stars_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="📥 Download CSV",
                data=stars_report.to_csv(index=False),
                file_name="rfm_stars_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

#=========================fifth block====================================
# =================== Visualization: Charts and Maps ===================

    st.subheader("Customer Base Analysis")

    col_left, col_right = st.columns(2)

    with col_left:
        st.write("**Customer Distribution by Segments**")
        # Display interactive Plotly chart
        st.plotly_chart(plot_segment_donut(rfm), use_container_width=True)

    with col_right:
        st.write("**RFM Revenue Matrix (Heatmap)**")
        # Display static matplotlib heatmap
        st.pyplot(plot_heatmap(pivot), use_container_width=True)


# Google Sheets connection function with resource caching
@st.cache_resource
def get_gspread_client():
    """
    Secure authorization in Google Sheets API.
    Supports both local development via key file 
    and production in Streamlit Cloud via Secrets.
    """
    try:
        # Try authorization via Streamlit Cloud Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict, 
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
    except Exception:
        # Local development via local JSON key file
        SERVICE_ACCOUNT_FILE = "/home/dmitrii/Jupyter_Python_SQL/rfm_project/credentials.json"
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
    return gspread.authorize(creds)


# =================== Universal Lead Form (Waitlist) ===================
if st.session_state.analysis_done:
    st.divider()

    # Lead form content for DEMO mode
    if st.session_state.get("demo_mode", False):
        st.subheader("Like the DEMO?")
        st.info(
            "Beta mode: 50% discount forever!\n\n"
            "We are actively testing the app before launching full functionality and accepting payments. "
            "Leave your email right now to lock in a permanent 50% discount on all future services!"
        )

    # Lead form content for PRODUCTION mode with real user data
    else:
        st.subheader("Want more accurate segmentation?")

        st.info(
            "If your data contains anomalous orders (outliers) that exceed "
            "average order value by several orders of magnitude, we recommend ordering Professional Audit.\n\n"
            "What's included in the audit:\n"         
            "- Deep data cleaning and outlier handling\n"
            "- More accurate custom segmentation for your niche\n"
            "- Personalized marketing recommendations\n\n"
            "Act now: Leave your email and get a permanent 50% discount after official release!"
        )

#=========================sixth block====================================
    # Lead collection form (Waitlist)
    with st.form("waitlist_form", clear_on_submit=True):
        email = st.text_input("Your email:", placeholder="example@mail.com")
        comment = "" 

        submitted_waitlist = st.form_submit_button("🎁 Get 50% Discount", use_container_width=True) 

        if submitted_waitlist:
            # Simple email validation
            if email and "@" in email and "." in email:
                try:
                    # Quick connection thanks to caching @st.cache_resource
                    client = get_gspread_client()
                    spreadsheet = client.open("streamlit_order_form")

                    # Check if waitlist sheet exists or create new one
                    try:
                        worksheet = spreadsheet.worksheet("waitlist")
                    except Exception:
                        worksheet = spreadsheet.add_worksheet(title="waitlist", rows="1000", cols="10")
                        worksheet.append_row(["date", "email", "comment", "mode", "version"])

                    # Write customer data
                    worksheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        email,
                        comment,
                        "demo" if st.session_state.get("demo_mode", False) else "real",
                        "1.0"
                    ])
                    st.success("You're in the list! 50% discount reserved. Stay tuned!")
                except Exception:
                    st.error("Failed to save data. Please try again.")
            else:
                st.error("Please enter a valid email!")

# =================== Feedback Form ===================

if st.session_state.analysis_done: 
    st.divider()

    with st.form("feedback_form", clear_on_submit=True):
        st.subheader("Help us improve!")

        # Interactive star collection (new in Streamlit)
        score = st.feedback("stars") 

        features = [] # Keep empty as in your code

        comment_feedback = st.text_area("Your suggestions:")

        col1, col2 = st.columns(2)
        with col1:
            submitted_feedback = st.form_submit_button(
                label="Submit Feedback",
                use_container_width=True
            )

    # Feedback submission logic to Google Sheets
    if submitted_feedback:
        try:
            client = get_gspread_client()
            spreadsheet = client.open("streamlit_order_form")

            # Check if scorelist sheet exists or create new one
            try:  
                worksheet = spreadsheet.worksheet("scorelist")
            except Exception:
                worksheet = spreadsheet.add_worksheet(title="scorelist", rows="1000", cols="10")
                worksheet.append_row(["date", "score", "features", "comment", "app_version"])

            # Calculate score (since star index starts from 0)
            final_score = str(score + 1) if score is not None else "No rating"

            worksheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                final_score,
                ", ".join(features),
                comment_feedback,
                "1.0"
            ])
            st.success("Thank you! Your feedback has been saved.")
        except Exception:
            st.error("Connection failed. Wait 5 seconds and click 'Submit Feedback' again.")

