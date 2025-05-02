import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import requests

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2MmZiNTU1NjhkYWZlNTJmMjcwMDAwNWYiLCJlbXBsb3llZUlkIjoiQTA0IiwidGltZSI6IjIwMjMtMTItMjlUMDg6NDY6NTAuMzcwWiIsImlhdCI6MTcwMzgzOTYxMH0.iGufSSISTKrsVaHqOEEH5wLysYQY_MJOSeGvD2tjz1s"

headers = {
    "AccessToken": ACCESS_TOKEN
}

testing_type_map = {
    'Basic Testing': 1,
    'Hardware Testing': 2,
    'Online/Offline Testing': 3
}

st.sidebar.header("Filters")

analysis_type = st.sidebar.selectbox("Select Analysis Type", ["Testing Analysis", "Device Programming Analysis"])

if analysis_type == "Testing Analysis":
    selected_type = st.sidebar.selectbox("Select Testing Type", list(testing_type_map.keys()))
    api_testing_type = testing_type_map[selected_type]
else:
    api_testing_type = None  

from datetime import date, datetime

today = date.today()
first_of_month = date(today.year, today.month, 1)
start_date = st.sidebar.date_input("Start Date", first_of_month)

end_date = st.sidebar.date_input("End Date", date.today())

fetch_data = st.sidebar.button("🔍 Fetch Data")

st.title("📊 Testing and Devices Data Dashboard")

if fetch_data:

    if analysis_type == "Testing Analysis":
        st.header("🧪 Testing Analysis")

        payload_testing = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "testingType": api_testing_type
        }

        url_testing = "https://int.alistetechnologies.com/testing/passedSummary"
        response_testing = requests.post(url_testing, json=payload_testing, headers=headers)

        if response_testing.status_code == 200:
            try:
                data_json = response_testing.json()
                device_data = data_json.get("data", {}).get("devices", [])
                df_testing = pd.DataFrame(device_data)

                if 'timestamp' in df_testing.columns:
                    df_testing['timestamp'] = pd.to_datetime(df_testing['timestamp'])
                    df_testing['date'] = df_testing['timestamp'].dt.date
                    df_testing['hour'] = df_testing['timestamp'].dt.hour
                    df_testing["device_count"] = 1
                else:
                    st.error("timestamp column not found in testing response data.")
                    st.stop()

                st.subheader("📄 Retrieved Testing Data")
                st.dataframe(df_testing.head())

                csv_data = df_testing.to_csv(index=False)
                st.download_button("⬇️ Download Testing Data CSV", data=csv_data, file_name="device_testing_data.csv", mime="text/csv")

                df_range = df_testing.copy()

                hourly_range = df_range.groupby(['date', 'hour', 'userName'])['device_count'].sum().reset_index()
                avg_hourly_range = (
                    hourly_range.groupby(['date', 'userName'])['device_count']
                    .mean()
                    .reset_index()
                    .rename(columns={'device_count': 'Avg Devices per Hour', 'date': 'Date'})
                )

                st.subheader("📊 Avg Devices per Hour (Stacked)")
                fig_stacked = px.bar(
                    avg_hourly_range, x='Date', y='Avg Devices per Hour',
                    color='userName', barmode='stack',
                    title='Stacked Avg Devices per Hour by User'
                )
                st.plotly_chart(fig_stacked, use_container_width=True)

                st.subheader("📊 Avg Devices per Hour (Grouped)")
                fig_grouped = px.bar(
                    avg_hourly_range, x='Date', y='Avg Devices per Hour',
                    color='userName', barmode='group',
                    title='Grouped Avg Devices per Hour by User'
                )
                st.plotly_chart(fig_grouped, use_container_width=True)

                daily_user_total = df_range.groupby(['date', 'userName'])['device_count'].sum().reset_index()
                daily_user_total.rename(columns={'device_count': 'Total Devices Tested', 'date': 'Date'}, inplace=True)

                daily_total = df_range.groupby('date')['device_count'].sum().reset_index()
                daily_total.rename(columns={'device_count': 'Daily Total', 'date': 'Date'}, inplace=True)

                st.subheader("📊 Total Devices Tested per Day by User")
                fig_total_user_daily = px.bar(
                    daily_user_total,
                    x='Date',
                    y='Total Devices Tested',
                    color='userName',
                    barmode='stack',
                    title='Total Devices Tested Per Day by User'
                )

                for _, row in daily_total.iterrows():
                    fig_total_user_daily.add_annotation(
                        x=row['Date'],
                        y=row['Daily Total'],
                        text=str(row['Daily Total']),
                        showarrow=False,
                        yshift=10,
                        font=dict(size=12, color="white")
                    )

                fig_total_user_daily.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig_total_user_daily, use_container_width=True)

                st.header("📅 Specific Date Breakdown (Testing Data)")
                available_dates = sorted(df_range['date'].unique())

                if available_dates:
                    selected_date = st.selectbox("Select a Specific Date", available_dates)

                    df_selected = df_range[df_range['date'] == selected_date]
                    hourly_selected = df_selected.groupby(['hour', 'userName'])['device_count'].sum().reset_index()
                    hourly_selected.rename(columns={'device_count': 'Devices Tested'}, inplace=True)

                    avg_selected = (
                        hourly_selected.groupby('userName')['Devices Tested']
                        .mean().reset_index().rename(columns={'Devices Tested': 'Avg Devices per Hour'})
                    )

                    st.subheader(f"📊 Avg Devices per Hour on {selected_date}")
                    fig_date = px.bar(
                        avg_selected, x='userName', y='Avg Devices per Hour', color='userName',
                        title=f'Avg Devices per Hour by User on {selected_date}'
                    )
                    st.plotly_chart(fig_date, use_container_width=True)

                    st.subheader(f"📋 Devices Tested per Hour Table on {selected_date}")
                    table_pivot = hourly_selected.pivot(index='hour', columns='userName', values='Devices Tested').fillna(0).astype(int)
                    st.dataframe(table_pivot)
                else:
                    st.warning("No testing data available for selected range.")

            except Exception as e:
                st.error(f"Error processing testing data: {e}")
        else:
            st.error(f"Testing API request failed with status code {response_testing.status_code}")

    elif analysis_type == "Device Programming Analysis":
        st.header("🔧 Device Programming Analysis")

        payload_assign = {
            "startTime": str(start_date),
            "endTime": str(end_date)
        }

        url_assign = "https://int.alistetechnologies.com/deviceIdAssign/createdBetweenTime"
        response_assign = requests.post(url_assign, json=payload_assign, headers=headers)

        if response_assign.status_code == 200:
            try:
                data_assign = response_assign.json()
                assigned_devices = data_assign.get("data", {}).get("devices", [])
                df_assign = pd.DataFrame(assigned_devices)

                if not df_assign.empty:
                    df_assign['createdAt'] = pd.to_datetime(df_assign['createdAt'])
                    df_assign['date'] = df_assign['createdAt'].dt.date
                    df_assign['hour'] = df_assign['createdAt'].dt.hour
                    df_assign['device_count'] = 1

                    st.subheader("📄 Retrieved Assigned Devices Data")
                    st.dataframe(df_assign.head())

                    total_per_day_code = df_assign.groupby(['date', 'deviceCode'])['device_count'].sum().reset_index()
                    st.subheader("📊 Total Devices Programmed Per Day by Device Code")
                    fig_total_per_day = px.bar(
                        total_per_day_code, x='date', y='device_count', color='deviceCode',
                        labels={'date': 'Date', 'device_count': 'Total Devices Programmed'},
                        barmode='stack',
                        text_auto=True
                    )
                    st.plotly_chart(fig_total_per_day, use_container_width=True)

                    hourly_code_data = df_assign.groupby(['date', 'hour', 'deviceCode'])['device_count'].sum().reset_index()
                    avg_per_day_code = (
                        hourly_code_data.groupby(['date', 'deviceCode'])['device_count']
                        .mean()
                        .reset_index()
                        .rename(columns={'device_count': 'Avg Devices per Hour'})
                    )

                    st.subheader("📊 Average Devices Programmed Per Hour Each Day by Device Code")
                    fig_avg_per_day = px.bar(
                        avg_per_day_code, x='date', y='Avg Devices per Hour',
                        color='deviceCode', barmode='group',
                        labels={'date': 'Date', 'Avg Devices per Hour': 'Avg Devices Programmed'},
                        text_auto=True
                    )
                    st.plotly_chart(fig_avg_per_day, use_container_width=True)

                else:
                    st.warning("No assigned devices found for selected range.")

            except Exception as e:
                st.error(f"Error processing assigned device data: {e}")
        else:
            st.error(f"Assigned Devices API request failed with status code {response_assign.status_code}")
