import scipy
import streamlit as st
import pandas as pd
import plotly.express as px
from statsmodels.tsa.arima.model import ARIMA

class TimeSeriesChartModule:
    def __init__(self, container, initial_data, window_size, unit, x_column=None, y_column='value'):
        """
        Initializes the TimeSeriesChartModule with the initial data, column names, and an existing Streamlit container.
        
        Parameters:
        - initial_data (pd.DataFrame): The initial dataset containing the time series data.
        - x_column (str): The name of the column to be used as the x-axis (time).
        - y_column (str): The name of the column to be used as the y-axis (values).
        - container (st.container): An existing Streamlit container to attach the chart to.
        """
        self.data = initial_data
        self.window_size = window_size
        self.unit = unit
        self.x_column = x_column
        if self.x_column:
            self.dates = self.data[self.x_column]
        else:
            self.dates = self.data.index
            self.x_column = self.data.index.name
        self.y_column = y_column
        self.container = container
        self.fig = None  # Placeholder for the figure
        
        # self.model = ARIMA(self.data[self.y_column], freq='15min', dates=pd.DatetimeIndex(self.dates), order=(5, 1, 0),).fit()
        self.plot()


    def plot(self):
        """
        Creates or updates the Plotly Express line chart in the provided Streamlit container.
        """
        # Generate the line chart
        self.fig = px.line(self.data.tail(self.window_size), x=self.data.tail(self.window_size).index, y=self.y_column)
        self.fig.update_layout(xaxis_title=self.x_column, yaxis_title=self.unit, width=800, height=400)
        self.fig.update_xaxes(tickformat='%B-%d %I %p')
        # Display the chart in the container
        with self.container:
            st.plotly_chart(self.fig, use_container_width=True)

    def forecast(self, steps):
        """
        Forecasts future values in the time series using the ARIMA model and updates the chart.
        
        Parameters:
        - steps (int): The number of steps (time periods) to forecast into the future.
        """
        # Forecast future values
        forecast = self.model.forecast(steps=steps)
        print(forecast)
        print(steps+1)
        print(self.data.tail(1))
        print(pd.date_range(
                    start=self.data[self.x_column].max(),
                    periods=steps+1, freq='15min', inclusive='right',
                    ).to_list())
        # Create a new DataFrame for the forecast data
        forecast_data = pd.DataFrame(
            {
                self.x_column: pd.date_range(
                    start=self.data[self.x_column].max(),
                    periods=steps+1, freq='15min', inclusive='right',
                    ).to_list(),
                    self.y_column: forecast
                    }
        )
                    
        self.update_data(forecast_data)
        # Add the forecast data to the existing dataset
        # self.data = pd.concat([self.data, forecast_data]).tail(len(self.data))
        print(self.data.tail())
        # Re-fit the ARIMA model with the updated dataset
        self.model = ARIMA(self.data[self.y_column],freq='15min', dates=self.data[self.x_column], order=(5, 1, 0)).fit()
        
        # Re-generate the line chart with the updated dataset and forecast data
        # self.fig = px.line(self.data, x=self.x_column, y=self.y_column)
        # self.fig.update_layout(xaxis_title=self.x_column, yaxis_title=self.y_column, width=800, height=400)
        # self.fig.update_xaxes(tickformat='%B-%d %I %p')
        # self.container.empty()
        # # Display the chart in the container
        # with self.container:
        #     st.plotly_chart(self.fig, use_container_width=True)



    def update_data(self, new_data):
        """
        Updates the dataset with new data and refreshes the chart in place.
        
        Parameters:
        - new_data (pd.DataFrame): New data to be added to the existing dataset.
        """
        # Update the dataset with new data only
        self.data = pd.concat([self.data, new_data])
        self.dates = self.data.index
        
        # Ideally, you would update the plot with only new data points here.
        # Since Plotly Express does not support incremental updates directly,
        # the entire dataset is redrawn. For true incremental updates, consider using Plotly GO.
        # Re-generate the line chart with the updated dataset
        viz_data = self.data.tail(self.window_size)
        self.fig = px.line(viz_data, x=viz_data.index, y=self.y_column)

        self.compute_peaks()

        self.fig.update_layout(xaxis_title=self.x_column, yaxis_title=self.unit, width=800, height=400)
        self.fig.update_xaxes(tickformat='%b %d %I %p')
        
        # Re-display the chart in the container
        with self.container:
            st.plotly_chart(self.fig, use_container_width=True)

    def compute_peaks(self):
        """
        Identifies peaks in the time series data and updates the chart with annotations.
        """
        # Find peaks in the data
        
        peak_indices, _ = scipy.signal.find_peaks(self.data[self.y_column], prominence=0.3, width=1)
        peaks = self.data.iloc[peak_indices]
    
    

        # peaks = self.data[self.y_column].diff().gt(0) & self.data[self.y_column].diff(-1).lt(0)
        # peak_dates = self.data.index[peaks]
        # peak_values = self.data[self.y_column][peaks]
        # print(peak_values)
        # print(peak_values)

        # Add annotations for the peaks to the line chart
        for date, value in zip(peaks.index, peaks['value'] ):
            if date >= self.data.index[-self.window_size]:
                self.fig.add_annotation(
                    x=date, y=value, text=f'{value:.2f} {self.unit}', yshift=5,
                    showarrow=True, arrowhead=1, bgcolor='red', arrowcolor="red"
                )

        # Re-display the chart  with annotations in the container
        # with self.container:
        #     st.plotly_chart(self.fig, use_container_width=True)