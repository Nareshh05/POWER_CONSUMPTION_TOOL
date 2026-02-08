import pandas as pd
from prophet import Prophet
import plotly.express as px
from meteostat import Point, Daily
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import os
import platform
import plotly.io as pio
import plotly.graph_objects as go

cur = os.path.dirname(os.path.realpath(__file__))
tamilnadu_file_path =  cur+'/static/datasets/tamilnadu.csv'
tamilnadu_peak_file_path = cur+'/static/datasets/tamilnadu_peak.csv'

# Tamilnadu Location
tamilnadu_location = Point(11.1271, 78.6569)

def model1(val):
    tamilnadu = pd.read_csv(tamilnadu_file_path)
    tamilnadu['Month'] = pd.to_datetime(tamilnadu['Month'])
    tamilnadu.sort_values('Month', inplace=True)
    
    # Rename columns for Prophet
    tamilnadu.rename(columns={'Month': 'ds', 'energy_requirement': 'y', 'tmax': 'tavg'}, inplace=True)
    tamilnadu['ds'] = pd.to_datetime(tamilnadu['ds'])

    # Clean data: Drop NaNs and ensure numeric
    tamilnadu['y'] = pd.to_numeric(tamilnadu['y'], errors='coerce')
    tamilnadu['tavg'] = pd.to_numeric(tamilnadu['tavg'], errors='coerce')
    tamilnadu.dropna(subset=['ds', 'y', 'tavg'], inplace=True)

    # Train model
    model = Prophet()
    model.add_regressor('tavg')
    model.fit(tamilnadu[['ds', 'y', 'tavg']])
    
    # Future dataframe
    future = model.make_future_dataframe(periods=val, freq='MS')

    # Get weather data for future
    # (Simplified for robustness)
    
    # Robustly fill tavg in future
    mean_temp = tamilnadu['tavg'].mean()
    if pd.isna(mean_temp):
         mean_temp = 30.0 # Fallback
         
    if 'tavg' not in future.columns:
        future['tavg'] = mean_temp
    else:
        future['tavg'] = future['tavg'].fillna(mean_temp)

    forecast = model.predict(future)
    
    fig = px.line(forecast, x='ds', y='yhat', title='Forecasted Energy Requirement')
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Power in MW',
        autosize=True
    )
    return forecast, fig

def model2(val):
    tamilnadu = pd.read_csv(tamilnadu_peak_file_path)
    tamilnadu['Month'] = pd.to_datetime(tamilnadu['Month'])
    tamilnadu.sort_values('Month', inplace=True)
    
    tamilnadu.rename(columns={'Month': 'ds', 'peak_demand': 'y', 'tmax': 'tavg'}, inplace=True)
    tamilnadu['ds'] = pd.to_datetime(tamilnadu['ds'])

    # Clean data
    tamilnadu['y'] = pd.to_numeric(tamilnadu['y'], errors='coerce')
    tamilnadu['tavg'] = pd.to_numeric(tamilnadu['tavg'], errors='coerce')
    tamilnadu.dropna(subset=['ds', 'y', 'tavg'], inplace=True)

    model = Prophet()
    model.add_regressor('tavg')
    model.fit(tamilnadu[['ds', 'y', 'tavg']])
    
    future = model.make_future_dataframe(periods=val, freq='MS')
    
    mean_temp = tamilnadu['tavg'].mean()
    if pd.isna(mean_temp):
        mean_temp = 30.0

    if 'tavg' not in future.columns:
        future['tavg'] = mean_temp
    else:
        future['tavg'] = future['tavg'].fillna(mean_temp)

    forecast = model.predict(future)
    
    fig = px.line(forecast, x='ds', y='yhat', title='Forecasted Peak')
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Peak Power in MW',
        autosize=True
    )
    return forecast, fig

def model3():
    # Helper for dashboard widgets
    # We need current month peak, forecast, and avg temp
    # Use small val for faster calc
    try:
        forecast1, _ = model1(1)
        forecast2, _ = model2(1)
        
        current_month = datetime.now().month
        
        # Try to find current month in forecast, or last available
        try:
            current_month_forecast = forecast1[forecast1['ds'].dt.month == current_month].iloc[0]
        except:
            current_month_forecast = forecast1.iloc[-1] if not forecast1.empty else {'yhat': 0}
            
        try:
            current_month_peak = forecast2[forecast2['ds'].dt.month == current_month].iloc[0]
        except:
            current_month_peak = forecast2.iloc[-1] if not forecast2.empty else {'yhat': 0}
            
    except Exception as e:
        print(f"Model Error: {e}")
        # Return fallback values if models fail violently
        return {'yhat': 0}, {'yhat': 0}, 30.0

    # Avg Temp Today
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    try:
        weather_data_today = Daily(tamilnadu_location, start=today, end=today)
        weather_data_today = weather_data_today.fetch()
        
        avg_temp_today = "N/A"
        if weather_data_today is not None and not weather_data_today.empty:
            avg_temp_today = weather_data_today['tavg'].mean()
        else:
            weather_data_yesterday = Daily(tamilnadu_location, start=yesterday, end=yesterday)
            weather_data_yesterday = weather_data_yesterday.fetch()
            if weather_data_yesterday is not None and not weather_data_yesterday.empty:
                avg_temp_today = weather_data_yesterday['tavg'].mean()
    except Exception:
        avg_temp_today = 30.0 # Fallback
    
    return current_month_peak, current_month_forecast, avg_temp_today

def model4(val):
    _, img1 = model1(val)
    _, img2 = model2(val)
    img1_json = pio.to_json(img1)
    img2_json = pio.to_json(img2)
    return img1_json, img2_json
