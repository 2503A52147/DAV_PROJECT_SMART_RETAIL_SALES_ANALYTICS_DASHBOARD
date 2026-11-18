
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Smart Retail Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

# Original dashboard design - preserved
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.dashboard-title {text-align:center; color:#243b80; font-weight:800;}
.dashboard-subtitle {text-align:center; color:#555; margin-bottom:1.4rem;}
div[data-testid="stMetric"] {
    background: #eef2ff;
    border: 1px solid #dce4ff;
    padding: 14px 16px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<h1 class="dashboard-title">SMART RETAIL SALES ANALYTICS DASHBOARD</h1>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="dashboard-subtitle">Explore sales, profit, products, customers, and regional performance</p>',
    unsafe_allow_html=True
)


# Bright colors for individual bars
BRIGHT_COLORS = [
    "#FF5733",
    "#FFC300",
    "#00C9A7",
    "#845EC2",
    "#FF6F91",
    "#008E9B",
    "#F9A826",
    "#D65DB1",
    "#4D96FF",
    "#00C49A",
    "#FF8066",
    "#A66CFF",
    "#2EC4B6",
    "#F15BB5",
    "#70E000"
]


# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data(uploaded_file, local_path):
    if uploaded_file is not None:
        try:
            raw = pd.read_csv(uploaded_file, encoding="cp1252")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            raw = pd.read_csv(uploaded_file, encoding="latin1")
    else:
        try:
            raw = pd.read_csv(local_path, encoding="cp1252")
        except UnicodeDecodeError:
            raw = pd.read_csv(local_path, encoding="latin1")

    return raw


st.sidebar.header("📁 Dataset")
st.sidebar.write("Use your existing Sample - Superstore.csv file.")
uploaded_file = st.sidebar.file_uploader(
    "Or upload the CSV here",
    type=["csv"]
)

csv_path = "Sample - Superstore.csv"

try:
    df_original = load_data(uploaded_file, csv_path)

except FileNotFoundError:
    st.error(
        "Could not find `Sample - Superstore.csv`. Put your CSV file "
        "in the same folder as `app.py`, or upload it using the file "
        "uploader in the left sidebar."
    )
    st.stop()

except Exception as e:
    st.error(f"Could not read the CSV file: {e}")
    st.stop()


# ==========================================================
# DATA CLEANING
# ==========================================================

# Keep original data unchanged for an honest before/after comparison.
df_original.columns = df_original.columns.astype(str).str.strip()
df_clean = df_original.copy()

# Clean whitespace in text fields.
for col in df_clean.select_dtypes(include=["object", "string"]).columns:
    df_clean[col] = df_clean[col].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )

# Convert date columns.
date_columns = [
    col for col in ["Order Date", "Ship Date"]
    if col in df_clean.columns
]

for col in date_columns:
    df_clean[col] = pd.to_datetime(
        df_clean[col],
        errors="coerce"
    )

# Convert numeric columns.
numeric_columns = [
    col for col in [
        "Sales", "Profit", "Quantity",
        "Discount", "Postal Code"
    ]
    if col in df_clean.columns
]

for col in numeric_columns:
    df_clean[col] = pd.to_numeric(
        df_clean[col],
        errors="coerce"
    )


# ==========================================================
# DATA QUALITY REPORT
# ==========================================================

original_rows, original_cols = df_original.shape

original_missing_cells = int(
    df_original.isna().sum().sum()
)

missing_before = df_original.isna().sum().rename(
    "Missing values before"
)

missing_after_conversion = df_clean.isna().sum().rename(
    "Missing values after type conversion"
)

missing_report = pd.concat(
    [missing_before, missing_after_conversion],
    axis=1
)

missing_report["Missing % before"] = (
    missing_report["Missing values before"]
    / max(original_rows, 1) * 100
).round(2)

missing_report["Missing % after"] = (
    missing_report["Missing values after type conversion"]
    / max(len(df_clean), 1) * 100
).round(2)

exact_duplicates = int(df_clean.duplicated().sum())

df_clean = df_clean.drop_duplicates().copy()

cleaned_rows, cleaned_cols = df_clean.shape

removed_duplicates = original_rows - cleaned_rows

conversion_created_missing = {}

for col in date_columns + numeric_columns:
    before_count = int(df_original[col].isna().sum())
    after_count = int(df_clean[col].isna().sum())

    conversion_created_missing[col] = max(
        after_count - before_count,
        0
    )


required = [
    "Sales", "Profit", "Quantity", "Discount",
    "Order Date", "Order ID", "Customer ID",
    "Region", "Category", "Segment",
    "Product Name", "State"
]

missing_required = [
    c for c in required
    if c not in df_clean.columns
]

if missing_required:
    st.error(
        "These required columns are missing from your CSV: "
        + ", ".join(missing_required)
    )
    st.write("Columns found:", list(df_clean.columns))
    st.stop()


# ==========================================================
# DATA CLEANING REPORT
# ==========================================================

with st.expander("🧹 Data Cleaning & Quality Report", expanded=False):

    st.markdown("### 1. Before-and-after summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Original rows", f"{original_rows:,}")
    c2.metric("Original columns", f"{original_cols:,}")
    c3.metric("Exact duplicate rows found", f"{exact_duplicates:,}")
    c4.metric("Rows after duplicate removal", f"{cleaned_rows:,}")

    c5, c6, c7 = st.columns(3)

    c5.metric("Missing cells before", f"{original_missing_cells:,}")

    c6.metric(
        "Missing cells after conversion",
        f"{int(df_clean.isna().sum().sum()):,}"
    )

    c7.metric(
        "Duplicate rows removed",
        f"{removed_duplicates:,}"
    )

    st.markdown("### 2. Cleaning actions applied")

    st.markdown("""
    - Removed leading and trailing spaces from column names.
    - Removed leading and trailing spaces from text values.
    - Converted `Order Date` and `Ship Date` to date/time format where available.
    - Converted `Sales`, `Profit`, `Quantity`, `Discount`, and `Postal Code` to numeric format where available.
    - Counted exact duplicate rows and removed exact duplicate records only.
    - Preserved repeated Order IDs and Customer IDs because they may be valid in transaction data.
    - Values that cannot be converted to the requested type become missing values (`NaT` or `NaN`) and are reported below.
    """)

    st.markdown("### 3. Missing values by column")

    st.dataframe(
        missing_report,
        use_container_width=True
    )

    st.markdown("### 4. Data types after cleaning")

    dtype_report = pd.DataFrame({
        "Column": df_clean.columns,
        "Data type after cleaning": [
            str(dtype) for dtype in df_clean.dtypes
        ],
        "Missing values": [
            int(df_clean[col].isna().sum())
            for col in df_clean.columns
        ],
    })

    st.dataframe(
        dtype_report,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 5. Validation checks")

    validation_rows = []

    for col in ["Sales", "Profit", "Quantity", "Discount"]:

        if col in df_clean.columns:

            values = df_clean[col].dropna()

            validation_rows.append({
                "Check": f"{col}: negative values",
                "Count": int((values < 0).sum()),
                "Meaning": (
                    "Review the context; negative profit is normal "
                    "for loss-making sales, and negative sales may "
                    "need checking."
                )
            })

    if "Quantity" in df_clean.columns:

        validation_rows.append({
            "Check": "Quantity: zero or negative",
            "Count": int(
                (df_clean["Quantity"].dropna() <= 0).sum()
            ),
            "Meaning": "Review records with zero or negative quantity."
        })

    if "Discount" in df_clean.columns:

        validation_rows.append({
            "Check": "Discount outside 0 to 1",
            "Count": int(
                (
                    (df_clean["Discount"] < 0)
                    | (df_clean["Discount"] > 1)
                ).sum()
            ),
            "Meaning": (
                "For this dataset, discounts are usually stored "
                "as fractions, e.g. 0.2 means 20%."
            )
        })

    if "Order Date" in df_clean.columns:

        validation_rows.append({
            "Check": "Missing or invalid Order Date",
            "Count": int(df_clean["Order Date"].isna().sum()),
            "Meaning": (
                "Includes blank dates and values that could not be parsed."
            )
        })

    st.dataframe(
        pd.DataFrame(validation_rows),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 6. Download cleaned data and reports")

    cleaned_csv = df_clean.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Download cleaned dataset (CSV)",
        data=cleaned_csv,
        file_name="Sample_Superstore_Cleaned.csv",
        mime="text/csv",
        key="download_cleaned_dataset",
    )

    missing_csv = missing_report.to_csv().encode("utf-8-sig")

    st.download_button(
        "Download missing-values report (CSV)",
        data=missing_csv,
        file_name="missing_values_report.csv",
        mime="text/csv",
        key="download_missing_report",
    )


# ==========================================================
# DASHBOARD FILTERS
# ==========================================================

df = df_clean.copy()

st.sidebar.header("🔎 Dashboard Filters")

valid_dates = df["Order Date"].dropna()

if not valid_dates.empty:

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "Order date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

else:
    date_range = None


def options_for(column):
    return sorted(
        df[column].dropna().astype(str).unique().tolist()
    )


region_options = options_for("Region")
category_options = options_for("Category")
segment_options = options_for("Segment")
state_options = options_for("State")

selected_regions = st.sidebar.multiselect(
    "Region",
    region_options,
    default=region_options
)

selected_categories = st.sidebar.multiselect(
    "Category",
    category_options,
    default=category_options
)

selected_segments = st.sidebar.multiselect(
    "Segment",
    segment_options,
    default=segment_options
)

selected_states = st.sidebar.multiselect(
    "State",
    state_options,
    default=state_options
)


filtered = df[
    df["Region"].astype(str).isin(selected_regions)
    & df["Category"].astype(str).isin(selected_categories)
    & df["Segment"].astype(str).isin(selected_segments)
    & df["State"].astype(str).isin(selected_states)
].copy()


if (
    date_range
    and isinstance(date_range, (tuple, list))
    and len(date_range) == 2
):

    start_date, end_date = date_range

    filtered = filtered[
        filtered["Order Date"].notna()
        & (filtered["Order Date"].dt.date >= start_date)
        & (filtered["Order Date"].dt.date <= end_date)
    ]


if filtered.empty:

    st.warning(
        "No rows match the selected filters. "
        "Change one or more filters in the sidebar."
    )

    st.stop()


# ==========================================================
# KPI CARDS
# ==========================================================

total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()

unique_orders = filtered["Order ID"].nunique()
unique_customers = filtered["Customer ID"].nunique()

total_quantity = filtered["Quantity"].sum()

profit_margin = (
    total_profit / total_sales * 100
    if total_sales else 0
)

m1, m2, m3 = st.columns(3)

m1.metric("Total Sales", f"${total_sales:,.2f}")
m2.metric("Total Profit", f"${total_profit:,.2f}")
m3.metric("Unique Orders", f"{unique_orders:,}")

m4, m5, m6 = st.columns(3)

m4.metric("Unique Customers", f"{unique_customers:,}")
m5.metric("Quantity Sold", f"{total_quantity:,.0f}")
m6.metric("Profit Margin", f"{profit_margin:.2f}%")

st.caption(
    f"Showing {len(filtered):,} cleaned rows out of "
    f"{len(df):,} cleaned rows after applying filters."
)

st.divider()


# ==========================================================
# 1. MONTHLY SALES TREND
# ==========================================================

st.subheader("1. Monthly Sales Trend")

monthly = (
    filtered.dropna(subset=["Order Date"])
    .assign(
        Month=lambda x:
        x["Order Date"].dt.to_period("M").astype(str)
    )
    .groupby("Month", as_index=False)["Sales"]
    .sum()
    .sort_values("Month")
)

if not monthly.empty:

    fig = px.line(
        monthly,
        x="Month",
        y="Sales",
        markers=True,
        title="Sales total for each month"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Sales ($)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No valid order dates are available for the monthly trend."
    )


# ==========================================================
# 2. SALES BY CATEGORY
# Bright individual colors added
# ==========================================================

left, right = st.columns(2)

with left:

    st.subheader("2. Sales by Category")

    cat_sales = (
        filtered.groupby("Category", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
    )

    fig = px.bar(
        cat_sales,
        x="Category",
        y="Sales",
        color="Category",
        color_discrete_sequence=BRIGHT_COLORS,
        text_auto=".2s",
        title="Which product category sells most?"
    )

    fig.update_traces(
        marker_line_color="white",
        marker_line_width=1.2
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Sales ($)",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# 3. PROFIT BY REGION
# Bright individual colors added
# ==========================================================

with right:

    st.subheader("3. Profit by Region")

    region_profit = (
        filtered.groupby("Region", as_index=False)["Profit"]
        .sum()
        .sort_values("Profit", ascending=False)
    )

    fig = px.bar(
        region_profit,
        x="Region",
        y="Profit",
        color="Region",
        color_discrete_sequence=BRIGHT_COLORS,
        text_auto=".2s",
        title="Compare profit across regions"
    )

    fig.update_traces(
        marker_line_color="white",
        marker_line_width=1.2
    )

    fig.update_layout(
        xaxis_title="Region",
        yaxis_title="Profit ($)",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# 4. TOP 10 PRODUCTS BY SALES
# Bright individual colors added
# ==========================================================

left, right = st.columns(2)

with left:

    st.subheader("4. Top 10 Products by Sales")

    top_products = (
        filtered.groupby("Product Name", as_index=False)["Sales"]
        .sum()
        .nlargest(10, "Sales")
        .sort_values("Sales")
    )

    fig = px.bar(
        top_products,
        x="Sales",
        y="Product Name",
        orientation="h",
        color="Product Name",
        color_discrete_sequence=BRIGHT_COLORS,
        text_auto=".2s",
        title="Products generating the highest sales"
    )

    fig.update_traces(
        marker_line_color="white",
        marker_line_width=1
    )

    fig.update_layout(
        xaxis_title="Sales ($)",
        yaxis_title="Product",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# 5. 3D SALES VS PROFIT SCATTER PLOT
# Replaces the original 2D scatter plot
# ==========================================================

with right:

    st.subheader("5. 3D Sales vs Profit")

    scatter_df = filtered.dropna(
        subset=["Sales", "Profit", "Quantity", "Category"]
    ).copy()

    if not scatter_df.empty:

        fig = px.scatter_3d(
            scatter_df,
            x="Sales",
            y="Profit",
            z="Quantity",
            color="Category",
            color_discrete_sequence=[
                "#A855F7",
                "#00C2FF",
                "#FF9F43",
                "#06D6A0",
                "#F43F5E"
            ],
            hover_data=[
                "Product Name",
                "State",
                "Region"
            ],
            title="Interactive 3D Relationship between Sales, Profit and Quantity",
            opacity=0.80
        )

        fig.update_traces(
            marker=dict(
                size=5,
                line=dict(
                    color="white",
                    width=0.4
                )
            )
        )

        fig.update_layout(
            height=500,
            margin=dict(
                l=0,
                r=0,
                t=55,
                b=0
            ),
            scene=dict(
                xaxis=dict(
                    title="Sales ($)",
                    backgroundcolor="#F8FAFC",
                    gridcolor="#DCE6F5",
                    showbackground=True
                ),
                yaxis=dict(
                    title="Profit ($)",
                    backgroundcolor="#F8FAFC",
                    gridcolor="#DCE6F5",
                    showbackground=True
                ),
                zaxis=dict(
                    title="Quantity",
                    backgroundcolor="#F8FAFC",
                    gridcolor="#DCE6F5",
                    showbackground=True
                ),
                camera=dict(
                    eye=dict(
                        x=1.6,
                        y=1.6,
                        z=1.2
                    )
                ),
                aspectmode="auto"
            ),
            legend=dict(
                title="Category"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "No complete Sales, Profit and Quantity records "
            "are available for the 3D scatter plot."
        )


# ==========================================================
# 6. SALES SHARE BY SEGMENT
# ==========================================================

st.subheader("6. Sales Share by Segment")

seg_sales = (
    filtered.groupby("Segment", as_index=False)["Sales"]
    .sum()
)

fig = px.pie(
    seg_sales,
    names="Segment",
    values="Sales",
    hole=0.45,
    color="Segment",
    color_discrete_sequence=BRIGHT_COLORS,
    title="Share of sales from each customer segment"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================================
# 7. USA MAP - SALES BY STATE
# Original map design preserved
# ==========================================================

st.subheader("7. USA Map — Sales by State")

st.caption(
    "Each state is shaded according to its total sales after "
    "the selected dashboard filters are applied. Hover over "
    "a state to see its sales value."
)

state_abbreviations = {
    "Alabama": "AL", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL",
    "Georgia": "GA", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY"
}

map_sales = (
    filtered.groupby("State", as_index=False)["Sales"]
    .sum()
)

map_sales["State Code"] = map_sales["State"].map(
    state_abbreviations
)

map_sales = map_sales.dropna(
    subset=["State Code"]
)

if not map_sales.empty:

    fig_map = px.choropleth(
        map_sales,
        locations="State Code",
        locationmode="USA-states",
        color="Sales",
        scope="usa",
        color_continuous_scale="Blues",
        hover_name="State",
        hover_data={
            "Sales": ":$,.2f",
            "State Code": False
        },
        labels={"Sales": "Sales (USD)"},
        title="Total sales across US states"
    )

    fig_map.update_layout(
        margin={
            "r": 0,
            "t": 50,
            "l": 0,
            "b": 0
        },
        geo_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig_map,
        use_container_width=True
    )

else:

    st.info(
        "No recognized US state names are available to draw the map."
    )


# ==========================================================
# 8. TOP 10 STATES BY SALES
# Bright individual colors added
# ==========================================================

left, right = st.columns(2)

with left:

    st.subheader("8. Top 10 States by Sales")

    state_sales = (
        filtered.groupby("State", as_index=False)["Sales"]
        .sum()
        .nlargest(10, "Sales")
        .sort_values("Sales")
    )

    fig = px.bar(
        state_sales,
        x="Sales",
        y="State",
        orientation="h",
        color="State",
        color_discrete_sequence=BRIGHT_COLORS,
        text_auto=".2s",
        title="States contributing the most sales"
    )

    fig.update_traces(
        marker_line_color="white",
        marker_line_width=1
    )

    fig.update_layout(
        xaxis_title="Sales ($)",
        yaxis_title="State",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# 9. PROFIT DISTRIBUTION
# ==========================================================

with right:

    st.subheader("9. Profit Distribution")

    profit_df = filtered.dropna(
        subset=["Profit"]
    )

    fig = px.histogram(
        profit_df,
        x="Profit",
        nbins=40,
        title="How often different profit values occur"
    )

    fig.update_layout(
        xaxis_title="Profit ($)",
        yaxis_title="Number of records"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# FILTERED DATA
# ==========================================================

st.divider()

with st.expander("View filtered data"):

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = filtered.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "Download filtered data as CSV",
        csv_bytes,
        "filtered_superstore_data.csv",
        "text/csv"
    )


# ==========================================================
# DATASET OVERVIEW
# ==========================================================

with st.expander("Dataset overview"):

    st.write(
        f"Original rows: **{len(df_original):,}**"
    )

    st.write(
        f"Columns: **{len(df_original.columns)}**"
    )

    st.write(
        f"Exact duplicate rows in original dataset: **{exact_duplicates:,}**"
    )

    st.write("Original missing values by column:")

    st.dataframe(
        df_original.isna().sum().rename(
            "Missing values"
        ).to_frame(),
        use_container_width=True
    )
