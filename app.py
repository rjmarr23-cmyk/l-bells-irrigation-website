import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Lucas Bells Irrigation Website",
    page_icon="💧",
    layout="wide"
)

# --------------------------
# Custom styling
# --------------------------
st.markdown("""
<style>
.stApp {
    background-color: #f3f7f4;
}

.top-banner {
    background: linear-gradient(90deg, #1d7a5e, #58a27c);
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    color: white;
    margin-bottom: 20px;
}

.top-banner h1 {
    margin: 0;
    font-size: 40px;
}

.top-banner p {
    margin: 5px 0 0 0;
    font-size: 17px;
}

.info-card {
    background: white;
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 15px;
    border-left: 6px solid #2e8b57;
}

.recommend-box {
    background: #ffffff;
    border-radius: 16px;
    padding: 18px;
    margin-top: 10px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

.small-text {
    color: #4b5563;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-banner">
    <h1>💧 Lucas Bells Irrigation Website</h1>
    <p>Weather-based irrigation scheduling dashboard</p>
</div>
""", unsafe_allow_html=True)

# --------------------------
# Upload section
# --------------------------
st.markdown('<div class="info-card">', unsafe_allow_html=True)
st.subheader("Upload CSV File")
uploaded_file = st.file_uploader("Upload your irrigation CSV", type=["csv"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()

df = pd.read_csv(uploaded_file)

# --------------------------
# Required columns check
# --------------------------
required_columns = [
    "Year",
    "Month",
    "Date",
    "Temperature_High_F",
    "Temperature_Low_F",
    "Precipitation_inches",
    "ET_inches"
]

missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    st.error(f"Missing columns: {missing_cols}")
    st.stop()

# --------------------------
# Data preparation
# --------------------------
df["Full_Date"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Date"].astype(str),
    errors="coerce"
)

if df["Full_Date"].isna().any():
    st.error("There is a problem with the date values in your file.")
    st.stop()

df["Month_Name"] = df["Full_Date"].dt.strftime("%B")
df["Day_Num"] = df["Full_Date"].dt.day
df["Temp_Avg"] = (df["Temperature_High_F"] + df["Temperature_Low_F"]) / 2
df["Precip_Cum"] = df["Precipitation_inches"].cumsum()
df["ET_Cum"] = df["ET_inches"].cumsum()

# --------------------------
# Irrigation logic
# --------------------------
MAD = 1.0
max_irrigation = 1.0

df["Irrigation_daily"] = 0.0
df["Irrigation_Cum"] = 0.0

deficit = 0.0

for i in range(len(df)):
    deficit += df.loc[i, "ET_inches"] - df.loc[i, "Precipitation_inches"]

    if deficit > MAD:
        irrigation = min(deficit, max_irrigation)
        df.loc[i, "Irrigation_daily"] = irrigation
        deficit -= irrigation

    if i > 0:
        df.loc[i, "Irrigation_Cum"] = df.loc[i - 1, "Irrigation_Cum"] + df.loc[i, "Irrigation_daily"]
    else:
        df.loc[i, "Irrigation_Cum"] = df.loc[i, "Irrigation_daily"]

df["Water_Cum"] = df["Precip_Cum"] + df["Irrigation_Cum"]

# --------------------------
# Sidebar controls
# --------------------------
st.sidebar.header("Controls")

selected_month = st.sidebar.selectbox(
    "Select month",
    df["Month_Name"].unique()
)

month_df = df[df["Month_Name"] == selected_month]

selected_day = st.sidebar.selectbox(
    "Select day",
    month_df["Day_Num"].unique()
)

day_data = month_df[month_df["Day_Num"] == selected_day].iloc[0]

# --------------------------
# Metrics
# --------------------------
m1, m2, m3, m4 = st.columns(4)

m1.metric("Date", f"{selected_month} {selected_day}")
m2.metric("ET", f"{day_data['ET_inches']:.2f} in")
m3.metric("Rain", f"{day_data['Precipitation_inches']:.2f} in")
m4.metric("Irrigation", f"{day_data['Irrigation_daily']:.2f} in")

# --------------------------
# Recommendation
# --------------------------
if day_data["Irrigation_daily"] > 0:
    st.markdown(
        f'<div class="recommend-box">Apply {day_data["Irrigation_daily"]:.2f} inches of irrigation today</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="recommend-box">No irrigation needed today</div>',
        unsafe_allow_html=True
    )

st.markdown(
    f'<p class="small-text">Average temperature for the selected day: {day_data["Temp_Avg"]:.1f} °F</p>',
    unsafe_allow_html=True
)

# --------------------------
# Two-column chart layout
# --------------------------
left_col, right_col = st.columns(2)

with left_col:
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.subheader("Daily Rainfall and ET")

    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(df.index, df["Precipitation_inches"], label="Rainfall")
    ax1.plot(df.index, df["ET_inches"], label="ET")
    ax1.set_xlabel("Day Index")
    ax1.set_ylabel("Inches")
    ax1.grid(alpha=0.3)
    ax1.legend()

    st.pyplot(fig1)
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.subheader("Cumulative Water Balance")

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.plot(df.index, df["Water_Cum"], label="Rain + Irrigation")
    ax2.plot(df.index, df["ET_Cum"], label="Cumulative ET")
    ax2.set_xlabel("Day Index")
    ax2.set_ylabel("Inches")
    ax2.grid(alpha=0.3)
    ax2.legend()

    st.pyplot(fig2)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# Data table
# --------------------------
st.markdown('<div class="info-card">', unsafe_allow_html=True)
st.subheader("Processed Dataset")
st.dataframe(df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
