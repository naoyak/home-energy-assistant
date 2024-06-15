import datetime

import streamlit as st
import numpy as np
import scipy
import pandas as pd
import altair as alt
import plotly.express as px

from watttime import WattTimeMyAccess, WattTimeHistorical, WattTimeForecast

# Page title
st.set_page_config(
    page_title="Home Energy Copilot",
    page_icon="⚡️",
    layout="wide",
)
st.title('📊 Home Energy Usage Copilot')
st.subheader('An interactive dashboard to explore your home energy usage and emissions impact')

with st.expander('About this app'):
  st.markdown('**What can this app do?**')
  st.info('This app shows the use of Pandas for data wrangling, Altair for chart creation and editable dataframe for data interaction.')
  st.markdown('**How to use the app?**')
  st.warning('To engage with the app, 1. Select genres of your interest in the drop-down selection box and then 2. Select the year duration from the slider widget. As a result, this should generate an updated editable DataFrame and line plot.')
  
st.subheader('When is the best time to save electricity?')

# year_selection = st.slider()'Select year duration', 1986, 2024, (2000, 2024))

ppl_net = (
  pd.read_csv('data/consumed.csv')
)
ppl_net['timestamp'] = pd.to_datetime(
  ppl_net['date'].astype(str).str.slice(stop=10) + ' ' + ppl_net['time'].astype(str).str.slice(stop=8))
ppl_net = ppl_net[['timestamp', 'kWh']]

# ppl_net = ppl_net[ppl_net.timestamp > today datetime.datetime(2024, 4, 1)]


current_date = pd.Timestamp.now()

first_day_current_month = current_date.replace(day=1)

# Step 3: Find the first day of the last month
first_day_last_month = (first_day_current_month - pd.DateOffset(months=1))

# Step 4: Filter the DataFrame for the last month
ppl_net_last_month = ppl_net[(ppl_net['timestamp'] >= first_day_last_month) & (ppl_net['timestamp'] < first_day_current_month)]
ppl_peaks, _ = scipy.signal.find_peaks(ppl_net_last_month['kWh'], height=1, width=3)
peak_rows = ppl_net_last_month.iloc[ppl_peaks]
# 
# ppl_net_last_month['rolling_sum_4'] = ppl_net_last_month['kWh'].rolling(window=4).sum()

print(ppl_net_last_month.head())
print(ppl_net.head())

# ppl_net['date'] = pd.to_datetime(ppl_net[['date', 'time']])
# ppl_editor = st.data_editor(ppl_net_last_month)

print(st.secrets)
print(st.secrets['WATTTIME_USER'])

wt_hist = WattTimeHistorical(


).get_historical_pandas(
  start=datetime.datetime.now() - datetime.timedelta(days=7),
  end=datetime.datetime.now(),
  region='CAISO_NORTH',

  signal_type='co2_moer', ).set_index('point_time').resample('15min').max().reset_index()
print(wt_hist.head())


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

print(electricity_rates_df)

with tab1:
  st.header("Usage")
  ppl_chart = alt.Chart(ppl_net_last_month).mark_line().encode(
    x=alt.X('timestamp:T', title='date', axis=alt.Axis(format='%B-%d %I %p')),
    y=alt.Y('kWh:Q', title='kWh')
  ).properties(width=800, height=400, title='Electricity usage over the last month')
  annotations = peak_rows
    
  # Annotations layer
  text_annotations = alt.Chart(annotations).mark_point(
     color='red',
     size=100
  ).encode(
      x='timestamp:T',
      y=alt.Y('kWh:Q', axis=alt.Axis(title='')),
      tooltip=[alt.Tooltip('timestamp:T', title='time'), alt.Tooltip('kWh:Q', title='kWh')],
      # text=alt.Text('kWh:Q')  # Display the kWh value as text
  )
  
  # Combine the chart and the annotations
  annotated_chart = ppl_chart + text_annotations


  
  st.altair_chart(annotated_chart, use_container_width=True)



with tab2:
  with st.container(border=True):
    st.header("Costs")
    costs = ppl_net_last_month.copy().set_index('timestamp').resample('h').sum().reset_index()
    costs['hour'] = costs['timestamp'].dt.hour
    print(costs.head())
    costs = costs.merge(electricity_rates_df, on='hour')
    costs['net_cost'] = costs['kWh'] * costs['rate_usd_per_kwh']
    
    fig = px.line(costs, x='timestamp', y='net_cost', labels={'net_cost': 'Cost'}, title='Electricity costs over the last month')

    # format y-axis as currency
    fig.update_layout(yaxis_tickformat='$,.2f')

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=False)
  col1, col2, col3 = st.columns(3)
  
  with col1:
    with st.container(border=True):
      st.subheader("Today")
      print(costs['kWh'].tail(24).sum())
      
      
      # Calculate the total cost for the last 24 hours only
      cost_24h = costs['net_cost'].tail(24).sum()
      cost_7d_lag = costs['net_cost'].tail(24*8).head(24).sum()
      cost_48h = costs['net_cost'].tail(48).head(24).sum()
      cost_8d_lag = costs['net_cost'].tail(24*9).head(24).sum()
      delta = cost_24h - cost_48h
      
      st.metric(label="Cost for last 24h", value=f"${cost_24h:.2f}", delta=f"${delta:.2f} relative to last week", label_visibility='collapsed', delta_color="inverse")
  with col2:
    with st.container(border=True):
      st.subheader("Yesterday")
      delta = cost_48h - cost_8d_lag
      st.metric(label="# **Yesterday**", value=f"${cost_48h:.2f}", delta=f"${delta:.2f} relative to last week", label_visibility='collapsed', delta_color="inverse")
      
      

with tab3:
  st.header("Carbon emissions")
    
  fig = px.line(wt_hist, x='point_time', y='value', labels={'value': 'lbs/MWh'}, title='Marginal carbon emissions over the last month')

  # Display the figure in Streamlit
  st.plotly_chart(fig, use_container_width=False)



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

print(ppl_net['kWh'].tail(24 * 4).sum())