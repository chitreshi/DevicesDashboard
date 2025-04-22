import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

df = pd.read_csv("finalDevicescsv.csv")

df['testingType'] = df['testingType'].astype(str).str.strip().str.lower().str.replace("_", " ").str.title()

df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df['date_only'] = pd.to_datetime(df['date']).dt.date
df['hour'] = pd.to_datetime(df['time']).dt.hour
df['device_count'] = 1  

st.title("📊 Device Testing Analysis Dashboard")

st.sidebar.header("Filters")
testing_types = sorted(df['testingType'].unique())
selected_type = st.sidebar.selectbox("Select Testing Type", testing_types)

df_filtered = df[df['testingType'] == selected_type]

st.sidebar.header("Date Range Filters")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime(df_filtered['date_only'].min()).date())
end_date = st.sidebar.date_input("End Date", pd.to_datetime(df_filtered['date_only'].max()).date())

df_range = df_filtered[(df_filtered['date_only'] >= start_date) & (df_filtered['date_only'] <= end_date)]

hourly_range = df_range.groupby(['date_only', 'hour', 'userName'])['device_count'].sum().reset_index()
avg_hourly_range = (
    hourly_range
    .groupby(['date_only', 'userName'])['device_count']
    .mean()
    .reset_index()
    .rename(columns={'device_count': 'Avg Devices per Hour', 'date_only': 'Date'})
)


fig_stacked = px.bar(
    avg_hourly_range,
    x='Date',
    y='Avg Devices per Hour',
    color='userName',
    barmode='stack',
    title='Stacked Avg Devices per Hour by User',
    labels={'userName': 'User'}
)
st.plotly_chart(fig_stacked, use_container_width=True)

fig_grouped = px.bar(
    avg_hourly_range,
    x='Date',
    y='Avg Devices per Hour',
    color='userName',
    barmode='group',
    title='Grouped Avg Devices per Hour by User',
    labels={'userName': 'User'}
)
st.plotly_chart(fig_grouped, use_container_width=True)

st.header("📅 Specific Date View")
st.sidebar.header("Specific Date Filter")
available_dates = sorted(df_range['date_only'].unique())
if available_dates:
    selected_date = st.sidebar.selectbox("Select a Specific Date", available_dates)

    df_selected = df_range[df_range['date_only'] == selected_date]
    hourly_selected = (
        df_selected.groupby(['hour', 'userName'])['device_count']
        .sum()
        .reset_index()
        .rename(columns={'device_count': 'Devices Tested'})
    )

    avg_selected = (
        df_selected.groupby(['hour', 'userName'])['device_count']
        .sum()
        .groupby(['userName'])
        .mean()
        .reset_index()
        .rename(columns={'device_count': 'Avg Devices per Hour'})
    )

    st.subheader(f"📊 Bar Chart for {selected_date}")
    fig_date = px.bar(
        avg_selected,
        x='userName',
        y='Avg Devices per Hour',
        color='userName',
        title=f'Avg Devices per Hour by User on {selected_date}',
        labels={'userName': 'User'}
    )
    st.plotly_chart(fig_date, use_container_width=True)

    st.subheader(f"📋 Devices Tested per Hour by User on {selected_date}")
    table_pivot = hourly_selected.pivot(index='hour', columns='userName', values='Devices Tested').fillna(0).astype(int)
    st.dataframe(table_pivot)
else:
    st.warning("No data available for the selected testing type and date range.")
