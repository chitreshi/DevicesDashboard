import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import requests

testing_type_map = {
    'Basic': 1,
    'Hardware': 2,
    'Online/Offline': 3
}

st.title("📊 Device Testing Analysis Dashboard")

st.sidebar.header("Filters")
selected_type = st.sidebar.selectbox("Select Testing Type", list(testing_type_map.keys()))
print(selected_type)
api_testing_type = testing_type_map[selected_type]
print(api_testing_type)
st.sidebar.header("Date Range Filters")
start_date = st.sidebar.date_input("Start Date", date(2025, 1, 1))
end_date = st.sidebar.date_input("End Date", date.today())

if st.sidebar.button("🔍 Get Data"):
    payload = {
        "startDate": str(start_date),
        "endDate": str(end_date),
        "testingType": api_testing_type
    }

    url = "https://int.alistetechnologies.com/testing/passedSummary"
    headers = {
        "AccessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2MmZiNTU1NjhkYWZlNTJmMjcwMDAwNWYiLCJlbXBsb3llZUlkIjoiQTA0IiwidGltZSI6IjIwMjMtMTItMjlUMDg6NDY6NTAuMzcwWiIsImlhdCI6MTcwMzgzOTYxMH0.iGufSSISTKrsVaHqOEEH5wLysYQY_MJOSeGvD2tjz1s"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            data_json = response.json()
            device_data = data_json.get("data", {}).get("devices", [])
            df = pd.DataFrame(device_data)

            print(data_json)


            if 'timestamp' in df.columns:
             df['timestamp'] = pd.to_datetime(df['timestamp'])
             df['date'] = df['timestamp'].dt.date
             df['time'] = df['timestamp'].dt.time
             df['hour'] = df['timestamp'].dt.hour
             df["device_count"] = 1
            else:
                st.error("timestamp column not found in response data ")
                st.stop()

            st.subheader("📄 Retrieved Data")
            st.dataframe(df.head())

            csv_data = df.to_csv(index=False)
            st.download_button("⬇️ Download CSV", data=csv_data, file_name="device_testing_data.csv", mime="text/csv")

            df_range = df.copy()
            hourly_range = df_range.groupby(['date', 'hour', 'userName'])['device_count'].sum().reset_index()
            avg_hourly_range = (
                hourly_range.groupby(['date', 'userName'])['device_count']
                .mean()
                .reset_index()
                .rename(columns={'device_count': 'Avg Devices per Hour', 'date': 'Date'})
            )

            st.subheader("📊 Stacked & Grouped Charts")
            fig_stacked = px.bar(
                avg_hourly_range, x='Date', y='Avg Devices per Hour',
                color='userName', barmode='stack',
                title='Stacked Avg Devices per Hour by User'
            )
            st.plotly_chart(fig_stacked, use_container_width=True)

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

            st.subheader("📊 Total Devices Tested per Day (by User)")

            fig_total_user_daily = px.bar(
            daily_user_total,
            x='Date',
            y='Total Devices Tested',
            color='userName',
            barmode='stack',
            title='Total Devices Tested Per Day by User'
            )


            for i, row in daily_total.iterrows():
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





            # Per-day breakdown
            st.header("📅 Specific Date View")
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

                st.subheader(f"📋 Devices Tested per Hour on {selected_date}")
                table_pivot = hourly_selected.pivot(index='hour', columns='userName', values='Devices Tested').fillna(0).astype(int)
                st.dataframe(table_pivot)
            else:
                st.warning("No data available for the selected filters.")

        except Exception as e:
            st.error(f" Error processing data: {e}")
    else:
        st.error(f" API request failed with status code {response.status_code}")
