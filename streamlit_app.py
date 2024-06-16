import datetime
import time

import streamlit as st
import numpy as np
import scipy
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import altair as alt
import plotly.express as px

from watttime import WattTimeMyAccess, WattTimeHistorical, WattTimeForecast

# Page title
st.set_page_config(
    page_title="EcoWatt",
    page_icon="⚡️",
    layout="wide",
)
 
st.image('ecowatt_logo.webp', width=300)
st.header('EcoWatt')
st.subheader('An interactive dashboard to explore your home energy usage and emissions impact')

with st.expander('About this app'):
  st.markdown('**What can this app do?**')
  st.info('This app shows the use of Pandas for data wrangling, Altair for chart creation and editable dataframe for data interaction.')
  st.markdown('**How to use the app?**')
  st.warning('To engage with the app, 1. Select genres of your interest in the drop-down selection box and then 2. Select the year duration from the slider widget. As a result, this should generate an updated editable DataFrame and line plot.')
  
st.subheader('When is the best time to save electricity?')

# ppl_net = (
#   pd.read_csv('data/consumed.csv')
# )
# ppl_net['timestamp'] = pd.to_datetime(
#   ppl_net['date'].astype(str).str.slice(stop=10) + ' ' + ppl_net['time'].astype(str).str.slice(stop=8))
# ppl_net = ppl_net[['timestamp', 'kWh']]

ppl_net = (
  pd.read_csv('data/consumption.csv', index_col='timestamp', parse_dates=True))


# Generate a forecast of the time series data in `ppl_net` using the ARIMA model
# forecast = ARIMA(ppl_net['kWh'], order=(5, 1, 0)).fit()


# forecast_data = forecast.predict(start=0, end=4 * 24 * 90, typ='levels')
# forecast_data = pd.DataFrame(
#   {
#     'kWh': forecast_data.values,
#     'timestamp': pd.date_range( 
#       start=ppl_net.timestamp.iloc[-1] + pd.Timedelta('15min'),
#       periods=len(forecast_data),
#       freq='15min')
#   }
# )
# forecast_data.to_csv('data/forecast.csv', index=False)

# ppl_net = ppl_net[ppl_net.timestamp > today datetime.datetime(2024, 4, 1)]


# Create a class definition of a TimeSeriesChartModule, which is used to create a plotly express line chart and attach it to a st.container.
# class TimeSeriesChartModule:
#     def __init__(self, data, x, y, title, labels):
#         self.data = data



current_date = pd.Timestamp.now()

first_day_current_month = current_date.replace(day=1)

# Step 3: Find the first day of the last month
first_day_last_month = (first_day_current_month - pd.DateOffset(months=1))

# Step 4: Filter the DataFrame for the last month
# ppl_net_last_month = ppl_net[(ppl_net['timestamp'] >= first_day_last_month) & (ppl_net['timestamp'] < first_day_current_month)]
ppl_peaks, _ = scipy.signal.find_peaks(ppl_net['value'], height=1, width=3)
peak_rows = ppl_net.iloc[ppl_peaks]
# print(ppl_peaks)
# 

# wt_hist = WattTimeHistorical(


# ).get_historical_pandas(
#   start=datetime.datetime.now() - datetime.timedelta(days=7),
#   end=datetime.datetime.now(),
#   region='CAISO_NORTH',

#   signal_type='co2_moer', ).set_index('point_time').resample('15min').max().reset_index()

wt_hist = pd.read_csv('data/emissions.csv', index_col='timestamp', parse_dates=True)

tab1, tab2, tab3 = st.tabs(["⚡️Usage", "💰Costs", "🔥Carbon"])

# electricity rates
hours = range(24)

# Determine the rate for each hour
rates = [0.5237 if 16 <= hour <= 21 else 0.4954 for hour in hours]

# Combine into a DataFrame
electricity_rates_df = pd.DataFrame({
    "hour": hours,
    "rate_usd_per_kwh": rates
})



from util.charting import TimeSeriesChartModule 

def split_data(data, days_back):
  today = datetime.datetime.today()
  past = data[
    (data.index > today - datetime.timedelta(days=days_back)) &
    (data.index < today)]
  future = data[data.index >= today]
  return past, future

with tab1:
  ppl_past, ppl_future = split_data(ppl_net, 1)
  
  # main_chart_1 = st.container(border=True)
  # with main_chart_1:
  main_chart_1 = st.container(border=True)
  with main_chart_1:
    st.header("Usage")
    c = st.empty()

    with c.container():
    
      usage_chart = TimeSeriesChartModule(c, ppl_past, 24 * 4, 'kWh', None, 'value')
      



with tab2:
  main_chart_2 = st.container(border=True)
  with main_chart_2:
    st.header("Bill Spending")
    c = st.empty()
  # with st.container(border=True):
  #   st.header("Costs")
  #   st.write("Electricity costs over the last month")
    with c.container():
      costs = ppl_net.copy().reset_index()

      costs['hour'] = costs['timestamp'].dt.hour
      costs = costs.merge(electricity_rates_df, on='hour',)
      costs['value'] = costs['value'] * costs['rate_usd_per_kwh']
      costs = costs[['timestamp', 'value']].set_index('timestamp')
      costs_past, costs_future = split_data(costs, 1)
      cost_chart = TimeSeriesChartModule(c, costs_past, 24 * 4, '$', None, 'value')
    
  #   costs = costs.merge(electricity_rates_df, on='hour')
    
    
  #   fig = px.line(costs, x='timestamp', y='net_cost', labels={'net_cost': 'Cost'}, title='Electricity costs over the last month')

  #   # format y-axis as currency
  #   fig.update_layout(yaxis_tickformat='$,.2f')

  #   # Display the figure in Streamlit
  #   st.plotly_chart(fig, use_container_width=False)
  col1, col2, col3 = st.columns(3)
  
  with col1:
    with st.container(border=True):
      st.subheader("Today")
      
      # Calculate the total cost for the last 24 hours only
      cost_24h = costs['value'].tail(24).sum()
      cost_7d_lag = costs['value'].tail(24*8).head(24).sum()
      cost_48h = costs['value'].tail(48).head(24).sum()
      cost_8d_lag = costs['value'].tail(24*9).head(24).sum()
      delta = cost_24h - cost_48h
      
      st.metric(label="Cost for last 24h", value=f"${cost_24h:.2f}", delta=f"${delta:.2f} relative to last week", label_visibility='collapsed', delta_color="inverse")
  with col2:
    with st.container(border=True):
      st.subheader("Yesterday")
      delta = cost_48h - cost_8d_lag
      st.metric(label="# **Yesterday**", value=f"${cost_48h:.2f}", delta=f"${delta:.2f} relative to last week", label_visibility='collapsed', delta_color="inverse")
      
      

with tab3:
  main_chart_3 = st.container(border=True)
  with main_chart_3:
    st.header("Carbon emissions")
    c = st.empty()
    with c.container():
      carbon = ppl_net.copy().rename({'value': 'kWh',}, axis=1)
      
      carbon = carbon.join(wt_hist.rename({'value': 'carbon_intensity'},  axis=1))
      carbon['value'] = carbon['kWh'] / 1000. * carbon['carbon_intensity']
      print(carbon.head())
      carbon = carbon[['value']]

      # carbon['value'] = 
      # costs['value'] = costs['value'] * costs['rate_usd_per_kwh']
      # costs = costs[['timestamp', 'value']].set_index('timestamp')
      # cost_chart = TimeSeriesChartModule(c, costs, 24, '$', None, 'value')
      carbon_past, carbon_future = split_data(carbon, 1)
      
      emissions_chart = TimeSeriesChartModule(c, carbon_past, 24 * 4, 'lbs CO2', None, 'value')
    
  # fig = px.line(wt_hist, x='timestamp', y='value', labels={'value': 'lbs/MWh'}, title='Marginal carbon emissions over the last month')

  # # Display the figure in Streamlit
  # st.plotly_chart(fig, use_container_width=False)


alerts = st.container(border=True)
with alerts:
  st.header("Alerts")



for i in range(len(ppl_future)):
  time.sleep(1)

  usage_chart.update_data(ppl_future.iloc[i:i+1])
  cost_chart.update_data(costs_future.iloc[i:i+1])
  emissions_chart.update_data(carbon_future.iloc[i:i+1])

  with alerts:
    
    # print(usage_chart.data.index[-1])
    latest_usage = usage_chart.data.iloc[-1]
  
    if latest_usage['value'] > 2.4 and usage_chart.data.index[-1].hour >= 15 and usage_chart.data.index[-1].hour < 19:
      st.warning("💰💰 Savings alert (Time of Use Rate): High energy usage detected during peak hours! Cut down on usage to save costs and reduce emissions.", icon="💰")
    
    latest_carbon = emissions_chart.data.iloc[-4:]
    if latest_carbon['value'].sum() > 2.0:
      st.warning("""🔥🔥 Emissions alert: High carbon emissions detected!
                 Consider shifting your usage to off-peak to reduce your carbon footprint.""", icon="🍃")
    # remove latest st.warning
  





# Load data
# df = pd.read_csv('data/movies_genres_summary.csv')
# df.year = df.year.astype('int')

# # Input widgets
# ## Genres selection
# genres_list = df.genre.unique()
# genres_selection = st.multiselect('Select genres', genres_list, ['Action', 'Adventure', 'Biography', 'Comedy', 'Drama', 'Horror'])

# ## Year selection
# year_list = df.year.unique()
# year_selection = st.slider('Select year duration', 1986, 2024, (2000, 2024))
# year_selection_list = list(np.arange(year_selection[0], year_selection[1]+1))

# df_selection = df[df.genre.isin(genres_selection) & df['year'].isin(year_selection_list)]
# reshaped_df = df_selection.pivot_table(index='year', columns='genre', values='gross', aggfunc='sum', fill_value=0)
# reshaped_df = reshaped_df.sort_values(by='year', ascending=False)


# Display DataFrame

# df_editor = st.data_editor(reshaped_df, height=212, use_container_width=True,
#                             column_config={"year": st.column_config.TextColumn("Year")},
#                             num_rows="dynamic")
# df_chart = pd.melt(df_editor.reset_index(), id_vars='year', var_name='genre', value_name='gross')

# # Display chart
# chart = alt.Chart(df_chart).mark_line().encode(
#             x=alt.X('year:N', title='Year'),
#             y=alt.Y('gross:Q', title='Gross earnings ($)'),
#             color='genre:N'
#             ).properties(height=320)
# st.altair_chart(chart, use_container_width=True)






# Add annotations for peaks
      # for index, row in peak_rows.iterrows():
      #     fig.add_annotation(x=row['timestamp'], y=row['kWh'],
      #                       text=str(row['kWh']),
      #                       showarrow=True, arrowhead=1, ax=0, ay=-40,
      #                       bgcolor="red", font=dict(color="white"))
      # print('hi')
    
      
      # for t in range(200):
      #   time.sleep(1)
      #   usage_chart.forecast(1)
      #   c.empty()
      #   usage_chart.plot()
      # time.sleep(5)
      # c.empty()
    # main_chart_1.empty()

  # for seconds in range(200):
  #   usage_chart.forecast(1)
  #   with main_chart_1.empty():
  #     usage_chart.plot()
    # st.write(f"Forecasting {seconds+1} steps into the future...")
    # st.write(f"Forecasted value: {forecast_data.iloc[-1]['kWh']:.2f} kWh")
    # st.write(f"Forecasted time: {forecast_data.iloc[-1]['timestamp']}")

  # Create the line chart using Plotly Express
  # fig = px.line(ppl_net_last_month, x='timestamp', y='kWh', title='Electricity usage over the last month', labels={'timestamp': 'Date', 'kWh': 'kWh'})
  
  # Customize the chart's appearance
  # fig.update_layout(xaxis_title='Date', yaxis_title='kWh', width=800, height=400)
  # fig.update_xaxes(tickformat='%B-%d %I %p')

  # Add circular tooltips for peaks using plotly express
  # fig.add_trace(px.scatter(peak_rows, x='timestamp', y='kWh', text='kWh', hover_data=['timestamp', 'kWh'],).data[0])
  # fig.update_traces(marker=dict(size=5, line=dict(width=2, )), selector=dict(mode='markers'))

  # Add new point to the chart and update in real time
  # new_point = pd.DataFrame({'timestamp': [pd.Timestamp.now()], 'kWh': forecast_data[-1]})
  # fig.add_trace(px.scatter(new_point, x='timestamp', y='kWh', text='kWh', hover_data=['timestamp', 'kWh'],).data[0])
  # fig.update_traces(marker=dict(size=5, line=dict(width=2, )), selector=dict(mode='markers'))

  # add another line chart to the chart, with forecast_data
    # print(forecast_data.tail())
  # fig.add_trace(px.line(forecast_data, x='timestamp', y='kWh', title='Electricity usage over the last month', labels={'timestamp': 'Date', 'kWh': 'kWh'}).data[0]).update_traces(line=dict(color='red', dash='dot'))

  
  # Add annotations for peaks
  # for index, row in peak_rows.iterrows():
  #     fig.add_annotation(x=row['timestamp'], y=row['kWh'],
  #                       text=str(row['kWh']),
  #                       showarrow=True, arrowhead=1, ax=0, ay=-40,
  #                       bgcolor="red", font=dict(color="white"))

  # st.plotly_chart(fig, use_container_width=True)
  
  # ppl_chart = alt.Chart(ppl_net_last_month).mark_line().encode(
  #   x=alt.X('timestamp:T', title='date', axis=alt.Axis(format='%B-%d %I %p')),
  #   y=alt.Y('kWh:Q', title='kWh')
  # ).properties(width=800, height=400, title='Electricity usage over the last month')
  # annotations = peak_rows
    
  # # Annotations layer
  # text_annotations = alt.Chart(annotations).mark_point(
  #    color='red',
  #    size=100
  # ).encode(
  #     x='timestamp:T',
  #     y=alt.Y('kWh:Q', axis=alt.Axis(title='')),
  #     tooltip=[alt.Tooltip('timestamp:T', title='time'), alt.Tooltip('kWh:Q', title='kWh')],
  #     # text=alt.Text('kWh:Q')  # Display the kWh value as text
  # )
  
  # # Combine the chart and the annotations
  # annotated_chart = ppl_chart + text_annotations


  
  # st.altair_chart(annotated_chart, use_container_width=True)