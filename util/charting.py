import streamlit as st
import pandas as pd
import plotly.express as px

class TimeSeriesChartModule:
    def __init__(self, initial_data, x_column, y_column, container):
        """
        Initializes the TimeSeriesChartModule with the initial data, column names, and an existing Streamlit container.
        
        Parameters:
        - initial_data (pd.DataFrame): The initial dataset containing the time series data.
        - x_column (str): The name of the column to be used as the x-axis (time).
        - y_column (str): The name of the column to be used as the y-axis (values).
        - container (st.container): An existing Streamlit container to attach the chart to.
        """
        self.data = initial_data
        self.x_column = x_column
        self.y_column = y_column
        self.container = container
        self.fig = None  # Placeholder for the figure
        self.plot()

    def plot(self):
        """
        Creates or updates the Plotly Express line chart in the provided Streamlit container.
        """
        # Generate the line chart
        self.fig = px.line(self.data, x=self.x_column, y=self.y_column)
        self.fig.update_layout(xaxis_title=self.x_column, yaxis_title=self.y_column, width=800, height=400)
        self.fig.update_xaxes(tickformat='%B-%d %I %p')
        # Display the chart in the container
        with self.container:
            st.plotly_chart(self.fig, use_container_width=True)

    def update_data(self, new_data):
        """
        Updates the dataset with new data and refreshes the chart in place.
        
        Parameters:
        - new_data (pd.DataFrame): New data to be added to the existing dataset.
        """
        # Update the dataset with new data only
        self.data = pd.concat([self.data, new_data]).drop_duplicates(subset=[self.x_column], keep='last').tail(len(self.data))
        
        # Ideally, you would update the plot with only new data points here.
        # Since Plotly Express does not support incremental updates directly,
        # the entire dataset is redrawn. For true incremental updates, consider using Plotly GO.
        
        # Re-generate the line chart with the updated dataset
        self.fig = px.line(self.data, x=self.x_column, y=self.y_column)
        
        # Re-display the chart in the container
        with self.container:
            st.plotly_chart(self.fig, use_container_width=True)