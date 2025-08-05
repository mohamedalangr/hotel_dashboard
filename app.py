import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="🏨 Hotel Manager Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Load Data --------------------
df = pd.read_csv("cleaned_hotels.csv")
df["arrival_date"] = pd.to_datetime(df["arrival_date"])
df["room_mismatch"] = df["reserved_room_type"] != df["assigned_room_type"]

# -------------------- Sidebar Filters --------------------
st.sidebar.title("🎛️ Dashboard Controls")
st.sidebar.markdown("Filter bookings to update all views.")

# Date filter
min_date, max_date = df["arrival_date"].min(), df["arrival_date"].max()
date_range = st.sidebar.date_input("📆 Arrival Date Range", [min_date, max_date])
start_date, end_date = pd.to_datetime(date_range)

# Other filters
hotel_type = st.sidebar.multiselect("🏨 Hotel Type", df["hotel"].unique(), default=df["hotel"].unique())
status = st.sidebar.multiselect("❌ Booking Status", df["is_canceled"].unique(), default=df["is_canceled"].unique())
customer_type = st.sidebar.multiselect("👤 Customer Type", df["customer_type"].unique(), default=df["customer_type"].unique())

# Filter Data
filtered_df = df[
    (df["arrival_date"] >= start_date) &
    (df["arrival_date"] <= end_date) &
    (df["hotel"].isin(hotel_type)) &
    (df["is_canceled"].isin(status)) &
    (df["customer_type"].isin(customer_type))
]

# -------------------- Header --------------------
st.title("🏨 Hotel Manager Monitoring Dashboard")
st.markdown("""
This dashboard helps hotel managers monitor bookings, cancellations, guest behavior, revenue, and more.
Use the controls to interactively filter and explore your hotel performance.
""")

# -------------------- KPI Section --------------------
st.markdown("### 📊 Key Performance Indicators")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Bookings", filtered_df.shape[0])
col2.metric("Cancellation Rate", f"{round((filtered_df['is_canceled'] == 'Canceled').mean()*100, 2)}%")
col3.metric("Avg. ADR", f"${round(filtered_df['adr'].mean(), 2)}")
col4.metric("Avg. Lead Time", f"{round(filtered_df['lead_time'].mean(), 1)} days")
col5.metric("Guests/Booking", f"{round(filtered_df['total_guests'].mean(), 2)}")
col6.metric("Repeated Guests", f"{round((filtered_df['is_repeated_guest'] == 'Yes').mean()*100, 2)}%")

# -------------------- Time Series --------------------
st.markdown("### 📈 Monthly Booking Trend")
monthly = filtered_df.groupby(pd.to_datetime(filtered_df["arrival_date"]).dt.to_period("M")).size().reset_index(name="Bookings")
monthly["arrival_date"] = monthly["arrival_date"].dt.to_timestamp()
fig_ts = px.line(monthly, x="arrival_date", y="Bookings", markers=True, title="Monthly Bookings")
st.plotly_chart(fig_ts, use_container_width=True)
st.caption("Bookings peaked in summer months — plan for seasonal staff.")

# -------------------- Categorical Insights --------------------
st.markdown("### 📊 Category Insights")
col1, col2 = st.columns(2)
with col1:
    fig = px.histogram(filtered_df, x="lead_time", color="is_canceled", nbins=50, title="Lead Time Distribution")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Guests mostly book far in advance, but cancellations occur at all lead times.")

with col2:
    fig = px.box(filtered_df, x="customer_type", y="adr", color="is_canceled", title="ADR by Customer Type")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Transient customers tend to pay more than contract guests.")

col3, col4 = st.columns(2)
with col3:
    top_countries = filtered_df[filtered_df["is_canceled"] == "Canceled"]["country"].value_counts().nlargest(10)
    fig = px.bar(x=top_countries.index, y=top_countries.values,
                 title="Top 10 Countries by Cancellations", labels={"x": "Country", "y": "Cancellations"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Portugal (PRT) has the highest number of canceled bookings.")

with col4:
    fig = px.histogram(filtered_df, x="meal", color="is_canceled", barmode="group", title="Meal Type vs Cancellation")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Most guests choose BB; meal type has minor effect on cancellation.")

# -------------------- Room Assignment --------------------
st.markdown("### 🛏️ Room Type Mismatch")
fig = px.histogram(filtered_df, x="room_mismatch", color="is_canceled", barmode="group",
                   title="Room Mismatch vs Cancellation", labels={"room_mismatch": "Mismatch"})
st.plotly_chart(fig, use_container_width=True)
st.caption("12.5% of bookings had mismatched rooms, which increases cancellation risk.")

# -------------------- Parking & Special Requests --------------------
st.markdown("### 🚗 Parking & Requests")
col1, col2 = st.columns(2)
with col1:
    parking_month = filtered_df.groupby(filtered_df["arrival_date"].dt.to_period("M"))['required_car_parking_spaces'].mean().reset_index()
    parking_month["arrival_date"] = parking_month["arrival_date"].dt.to_timestamp()
    fig = px.line(parking_month, x="arrival_date", y="required_car_parking_spaces", title="Monthly Avg Parking Spaces")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Parking demand is low overall but should be tracked in peak months.")

with col2:
    fig = px.histogram(filtered_df, x="total_of_special_requests", color="is_canceled", barmode="group",
                       title="Special Requests vs Cancellation")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Most bookings have 0–1 requests; special requests may indicate higher expectations.")

# -------------------- Data Preview & Download --------------------
st.markdown("### 📄 Data Preview & Export")
with st.expander("🔍 Show Filtered Data"):
    st.dataframe(filtered_df.head(50), use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered Data", csv, "filtered_bookings.csv", "text/csv")

# -------------------- Final Insights --------------------
st.markdown("### 🧠 Executive Summary")
st.markdown("- 🔺 Most cancellations come from **Portugal (PRT)**")
st.markdown("- 🛏️ Room mismatches occur in **12.5%** of bookings, mostly at **Resort Hotels**")
st.markdown("- 💵 Cancelled bookings have higher ADR (~$104.96) than confirmed ones (~$99.99)")
st.markdown("- 🍽️ Most guests choose **Bed & Breakfast (BB)**")
st.markdown("- 🔁 Loyalty is low: only **3.19%** of guests are repeat visitors")

# -------------------- Footer --------------------
st.markdown("---")
st.markdown("Built for hotel operations and strategy. | Powered by Streamlit | Mohamed - Task 9")
