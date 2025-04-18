import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json


with open("tested_Device.json", "r") as f:
    data = json.load(f)


records = []
for item in data:
    doc = item["_doc"]
    created_at = doc.get("createdAt")
    
    
    for test in doc.get("testing_history", []):
        records.append({
            "deviceId": doc.get("deviceId"),
            "tester": test.get("tester"),
            "test_type": test.get("type"),
            "createdAt": created_at
        })

df = pd.DataFrame(records)

df["createdAt"] = pd.to_datetime(df["createdAt"])
df["hour"] = df["createdAt"].dt.hour
df["day"] = df["createdAt"].dt.date

test_type_map = {1: "Basic", 2: "Hardware", 3: "Online/Offline"}
df["test_category"] = df["test_type"].map(test_type_map)

st.sidebar.header("Filter by Date")
unique_dates = sorted(df["day"].unique())
selected_date = st.sidebar.date_input("Select a date", value=unique_dates[0], min_value=min(unique_dates), max_value=max(unique_dates)) 
daily_df = df[df["day"] == pd.to_datetime(selected_date).date()]

st.sidebar.header("Filter by Tester")
unique_testers = sorted(df["tester"].dropna().unique())
selected_tester = st.sidebar.selectbox("Select a Tester", options=["All"] + unique_testers)

daily_df = df[df["day"] == pd.to_datetime(selected_date).date()]

if selected_tester != "All":
    daily_df = daily_df[daily_df["tester"] == selected_tester]



ddaily_df = df[df["day"] == pd.to_datetime(selected_date).date()]
if selected_tester != "All":
    daily_df = daily_df[daily_df["tester"] == selected_tester]

hourly_counts = daily_df.groupby(["hour", "test_category"]).size().reset_index(name="count")
fig_hourly = px.bar(hourly_counts, x="hour", y="count", color="test_category", barmode="group",
                    title=f"Devices Tested Hourly on {selected_date}", labels={"count": "Devices Tested"})

daywise_counts = df.groupby(["day", "test_category"]).size().reset_index(name="count")
fig_daywise = px.line(daywise_counts, x="day", y="count", color="test_category",
                      title="Day-wise Devices Tested", markers=True)

st.title("Device Testing Dashboard")
st.plotly_chart(fig_hourly, use_container_width=True)
st.plotly_chart(fig_daywise, use_container_width=True)

st.subheader("User-wise Device Count per Hour")
user_hourly_counts = daily_df.groupby(["tester", "hour", "test_category"]).size().reset_index(name="count")
st.dataframe(user_hourly_counts.sort_values(by=["tester", "hour"]), use_container_width=True)

fig_user_hour = px.bar(user_hourly_counts, x="hour", y="count", color="test_category",
                       facet_col="tester", facet_col_wrap=3,
                       title="Hourly Devices Tested by Each User",
                       labels={"count": "Devices Tested"})
st.plotly_chart(fig_user_hour, use_container_width=True)
