import pandas as pd
from prophet import Prophet
import plotly.express as px
import plotly.io as pio
from meteostat import Point, daily as Daily
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import os
import sys

# Mock paths
cur = "/Users/nareshkumar/Downloads/SIH-SmartAutomation-Electricity-AI-Consumption-main/main"
file1 =  cur+'/static/datasets/power_Generation.json'
file2 = cur+'/static/datasets/rene_energy.json'

print(f"File1 exists: {os.path.exists(file1)}")
print(f"File2 exists: {os.path.exists(file2)}")

def thermal(year):
    print("\n--- Testing Thermal ---")
    try:
        Power_Generation = pd.read_json(file1)
        print(f"Initial shape: {Power_Generation.shape}")
        
        Power_Generation['fy'] = pd.to_datetime(Power_Generation['fy'].str[:4], format='%Y')
        Power_Generation['Month'] = pd.to_datetime(Power_Generation['Month'], format='%b-%Y')
        
        thermal_df = Power_Generation[Power_Generation['mode']=='THERMAL'].copy()
        print(f"Thermal Only shape: {thermal_df.shape}")
        
        thermal_df.rename(columns={'Month':'ds','bus':'y'},inplace=True)
        
        # Clean Data
        thermal_df['y'] = pd.to_numeric(thermal_df['y'], errors='coerce')
        before_drop = len(thermal_df)
        thermal_df.dropna(subset=['ds', 'y'], inplace=True)
        after_drop = len(thermal_df)
        print(f"Rows before/after dropna: {before_drop} / {after_drop}")
        
        if thermal_df.empty:
             print("Thermal DF is empty after cleaning")
             return "{}"

        print(thermal_df[['ds', 'y']].head())

        husn = Prophet()
        husn.fit(thermal_df[['ds','y']])
        future = husn.make_future_dataframe(periods=year, freq='MS')
        forecast = husn.predict(future)
        print("Thermal Forecast generated")
        fig = px.line(forecast, x='ds', y='yhat', title='Thermal Production')
        return "JSON_OK"
    except Exception as e:
        print(f"Thermal Model Error: {e}")
        import traceback
        traceback.print_exc()
        return "{}"

def renewable(year):
    print("\n--- Testing Renewable ---")
    try:
        ren_df = pd.read_json(file2)
        print(f"Initial shape: {ren_df.shape}")
        
        ren_df['Month'] = pd.to_datetime(ren_df['Month'], format='%b-%Y')
        ren_df = ren_df[ren_df['State']=='Tamil Nadu']
        print(f"Tamil Nadu shape: {ren_df.shape}")
        
        if len(ren_df) > 1:
            fil_df = ren_df.iloc[1:].copy()
        else:
            fil_df = ren_df.copy()
            
        tamilnadu_df = fil_df[['Month','total']].copy()
        tamilnadu_df.rename(columns={'Month':'ds','total':'y'},inplace=True)
        
        # Clean Data
        tamilnadu_df['y'] = pd.to_numeric(tamilnadu_df['y'], errors='coerce')
        before_drop = len(tamilnadu_df)
        tamilnadu_df.dropna(subset=['ds', 'y'], inplace=True)
        after_drop = len(tamilnadu_df)
        print(f"Rows before/after dropna: {before_drop} / {after_drop}")
        
        if tamilnadu_df.empty:
            print("Renewable DF is empty after cleaning")
            return "{}"
            
        print(tamilnadu_df[['ds', 'y']].head())

        Gul = Prophet()
        Gul.fit(tamilnadu_df[['ds','y']])
        future = Gul.make_future_dataframe(periods=year,freq='MS')
        forecast = Gul.predict(future)
        print("Renewable Forecast generated")
        fig = px.line(forecast,x='ds',y='yhat',title='Renewable Energy Production')
        return "JSON_OK"
    except Exception as e:
        print(f"Renewable Model Error: {e}")
        import traceback
        traceback.print_exc()
        return "{}"

if __name__ == "__main__":
    t_res = thermal(5)
    print(f"Thermal Result: {t_res}")
    r_res = renewable(5)
    print(f"Renewable Result: {r_res}")
