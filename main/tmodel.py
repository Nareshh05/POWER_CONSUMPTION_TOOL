import pandas as pd
from prophet import Prophet
import plotly.express as px
import plotly.io as pio
from meteostat import Point, daily as Daily
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import os

cur = os.path.dirname(os.path.realpath(__file__))
file1 =  cur+'/static/datasets/power_Generation.json'
file2 = cur+'/static/datasets/rene_energy.json'

def get_empty_fig_json(title="No Data Available"):
    fig = go.Figure()
    fig.update_layout(title=title, xaxis={"visible": False}, yaxis={"visible": False}, annotations=[
        {"text": "No Data Available", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 20}}
    ])
    return pio.to_json(fig)

def stats(year):
    try:
        Power_Generation = pd.read_json(file1)
        Power_Generation['fy'] = pd.to_datetime(Power_Generation['fy'].str[:4], format='%Y')
        Power_Generation['Month'] = pd.to_datetime(Power_Generation['Month'], format='%b-%Y')
        Power_Generation['Month'] = Power_Generation['Month'].dt.month
        Power_y = Power_Generation.loc[Power_Generation['fy'].dt.year == year]
        
        if Power_y.empty:
             empty_json = get_empty_fig_json(f"No Data for Year {year}")
             return empty_json, empty_json
             
        share_df = Power_y.groupby(['mode'])['bus'].sum().reset_index()
        fig = px.pie(share_df, values='bus', names='mode', title='Contribution from each source in the year '+str(year))
        
        thermal_val = share_df.loc[share_df['mode'] == 'THERMAL', 'bus'].values[0] if not share_df.loc[share_df['mode'] == 'THERMAL', 'bus'].empty else 0
        nuclear_val = share_df.loc[share_df['mode'] == 'NUCLEAR', 'bus'].values[0] if not share_df.loc[share_df['mode'] == 'NUCLEAR', 'bus'].empty else 0
        hydro_val = share_df.loc[share_df['mode'] == 'HYDRO', 'bus'].values[0] if not share_df.loc[share_df['mode'] == 'HYDRO', 'bus'].empty else 0
    
        cat = ['Thermal', 'Nuclear', 'Hydro']
        values = [thermal_val, nuclear_val, hydro_val]
    
        fig1 = go.Figure([go.Bar(x=cat, y=values)])
        fig1.update_layout(
            title="Production in Different Sectors in the year "+str(year),
            xaxis_title="Modes",
            yaxis_title="Power (GW)"
        )
        return pio.to_json(fig),pio.to_json(fig1)
    except Exception as e:
        print(f"Stats Error: {e}")
        empty_json = get_empty_fig_json("Error Loading Data")
        return empty_json, empty_json

def thermal(year):
    try:
        Power_Generation = pd.read_json(file1)
        Power_Generation['fy'] = pd.to_datetime(Power_Generation['fy'].str[:4], format='%Y')
        Power_Generation['Month'] = pd.to_datetime(Power_Generation['Month'], format='%b-%Y')
        
        thermal_df = Power_Generation[Power_Generation['mode']=='THERMAL'].copy()
        thermal_df.rename(columns={'Month':'ds','bus':'y'},inplace=True)
        
        # Clean Data
        thermal_df['y'] = pd.to_numeric(thermal_df['y'], errors='coerce')
        thermal_df.dropna(subset=['ds', 'y'], inplace=True)
        
        if thermal_df.empty or len(thermal_df) < 2:
             return get_empty_fig_json("Insufficient Data for Thermal Model")

        husn = Prophet()
        husn.fit(thermal_df[['ds','y']])
        future = husn.make_future_dataframe(periods=year, freq='MS')
        forecast = husn.predict(future)
        fig = px.line(forecast, x='ds', y='yhat', title='Thermal Production')
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Power(GW)',
            autosize=True
        )
        return pio.to_json(fig)
    except Exception as e:
        print(f"Thermal Model Error: {e}")
        return get_empty_fig_json(f"Error: {str(e)}")

def renewable(year):
    try:
        ren_df = pd.read_json(file2)
        ren_df['Month'] = pd.to_datetime(ren_df['Month'], format='%b-%Y')
        ren_df = ren_df[ren_df['State']=='Tamil Nadu']
        
        # Original logic skipped first row? keeping it but ensuring safety
        if len(ren_df) > 1:
            fil_df = ren_df.iloc[1:].copy()
        else:
            fil_df = ren_df.copy()
            
        tamilnadu_df = fil_df[['Month','total']].copy()
        tamilnadu_df.rename(columns={'Month':'ds','total':'y'},inplace=True)
        
        # Clean Data
        tamilnadu_df['y'] = pd.to_numeric(tamilnadu_df['y'], errors='coerce')
        tamilnadu_df.dropna(subset=['ds', 'y'], inplace=True)
        
        if tamilnadu_df.empty or len(tamilnadu_df) < 2:
            return get_empty_fig_json("Insufficient Data for Renewable Model")

        Gul = Prophet()
        Gul.fit(tamilnadu_df[['ds','y']])
        future = Gul.make_future_dataframe(periods=year,freq='MS')
        forecast = Gul.predict(future)
        fig = px.line(forecast,x='ds',y='yhat',title='Renewable Energy Production')
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Power(GW)',
            autosize = True
        )
        return pio.to_json(fig)
    except Exception as e:
        print(f"Renewable Model Error: {e}")
        return get_empty_fig_json(f"Error: {str(e)}") 
