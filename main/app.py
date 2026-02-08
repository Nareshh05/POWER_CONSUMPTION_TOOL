from flask import Flask, redirect, render_template, request, jsonify, url_for, session
from flask_socketio import SocketIO, emit
from table import *
from functools import wraps
from model import *
import io
import base64
import plotly.io as pio
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.io import to_image
from flask_caching import Cache
from tmodel import *
import random
import time
import threading
import os

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db.init_app(app)
app.app_context().push()
app.secret_key = "APtlnuRu04uv"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

with app.app_context():
    db.create_all()

# Global Device Monitoring (Simulated IoT State)
DEVICE_STATE = {
    'ac': False,
    'fan': True,
    'light': True,
    'tv': False,
    'fridge': True
}

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Mock Alert System -> Real Alert System
def send_email_alert(recipient_email, message):
    """Sends a real email alert using SMTP."""
    sender_email = "sih.smartenergy@gmail.com" # Replace with your email
    sender_password = "xxxx xxxx xxxx xxxx" # Replace with your App Password
    
    # If credentials are not set (placeholders), fallback to mock to prevent crash
    if "xxxx" in sender_password:
        print(f"\n[ALERT SYSTEM] 📧 (Mock) Email would be sent to {recipient_email}: {message}\n")
        print("[SETUP REQUIRED] Please configure 'sender_email' and 'sender_password' in app.py to enable real emails.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Smart Energy Alert: High Consumption Detected"

        msg.attach(MIMEText(message, 'plain'))

        # Connect to Gmail SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        print(f"\n[ALERT SYSTEM] ✅ Real Email sent successfully to {recipient_email}\n")
    except Exception as e:
        print(f"\n[ALERT SYSTEM] ❌ Failed to send email: {e}\n")

def send_sms_alert(phone, message):
    """Simulates sending an SMS alert (Requires Twilio/etc for real implementation)."""
    # Keeping SMS as mock for now unless API keys provided
    print(f"\n[ALERT SYSTEM] 📱 Sending SMS to {phone}: {message}\n")

ALERT_COUNT = 0 # Global counter for alerts

# Live Data Simulator
def background_thread():
    """Example of how to send server generated events to clients."""
    global ALERT_COUNT
    while True:
        socketio.sleep(3)
        # Calculate Load based on REAL User State
        # AC ~ 1500W, Fan ~ 75W, Light ~ 20W, TV ~ 150W, Fridge ~ 200W + Base Load noise
        # Reduced base load to realistic standby levels (10-50W) instead of 500-1000W
        base_load = random.uniform(10, 50)
        
        # Calculate individual loads
        ac_load = (1500 + random.uniform(-50, 50)) if DEVICE_STATE['ac'] else 0
        fan_load = (75 + random.uniform(-5, 5)) if DEVICE_STATE['fan'] else 0
        light_load = (20 + random.uniform(-2, 2)) if DEVICE_STATE['light'] else 0
        tv_load = (150 + random.uniform(-10, 10)) if DEVICE_STATE['tv'] else 0
        fridge_load = (200 + random.uniform(-20, 20)) if DEVICE_STATE['fridge'] else 0
        
        current_load = base_load + ac_load + fan_load + light_load + tv_load + fridge_load
        
        # Prepare device load data (in Watts)
        device_loads = {
            'ac': round(ac_load, 2),
            'fan': round(fan_load, 2),
            'light': round(light_load, 2),
            'tv': round(tv_load, 2),
            'fridge': round(fridge_load, 2)
        }

        # Projected Daily Usage (simple extrapolation: current load * 24h)
        projected_daily_kwh = (current_load * 24) / 1000

        # Threshold Monitor & Targeted Alert
        # Increased threshold to 2000W so alerts only trigger for actual high usage (e.g., AC + others)
        if current_load > 2000: # High consumption threshold
            health = "Critical"
            
            # Message for alerts
            alert_msg = f"High Power Consumption Detected: {current_load:.2f} W. AC is {'ON' if DEVICE_STATE['ac'] else 'OFF'}."
            
            # Alert Logic:
            # 1. UI Alerts: Limit to 1 time ONLY ("one time alone").
            # 2. Email/SMS: Continue sending for all detections.
            
            if ALERT_COUNT < 1:
                 # Trigger UI Popup via SocketIO
                socketio.emit('email_alert', {
                    'email': 'nareshnandy889@gmail.com', # Hardcoded as per user context or session
                    'message': alert_msg,
                    'timestamp': time.strftime('%H:%M:%S')
                })
            
            # Always send backend notifications (Email/SMS)
            send_email_alert('nareshnandy889@gmail.com', alert_msg)
            send_sms_alert('9080123138', alert_msg)
            
            ALERT_COUNT += 1
            
            socketio.emit('alert', {
                'message': f"High Load: {current_load:.2f} W",
                'timestamp': time.strftime('%H:%M:%S')
            })
        else:
            health = "Stable"
            # Reset alert count if needed? User didn't specify reset logic, so assuming 1 per session.
        
        socketio.emit('live_data', {
            'load': f"{current_load:.2f}",
            'health': health,
            'timestamp': time.strftime('%H:%M:%S'),
            'devices': DEVICE_STATE,
            'device_loads': device_loads,
            'projected_daily': f"{projected_daily_kwh:.2f}"
        })

@socketio.on('toggle_device')
def handle_toggle(data):
    device = data.get('device')
    if device in DEVICE_STATE:
        DEVICE_STATE[device] = not DEVICE_STATE[device]
        print(f"Toggled {device} to {DEVICE_STATE[device]}")
        # Emit immediate update to all clients to reflect change instantly
        socketio.emit('device_update', DEVICE_STATE)

@socketio.on('connect')
def test_connect():
    print('Client connected')
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

thread = None
thread_lock = threading.Lock()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route('/upload_dataset', methods=['POST'])
@login_required
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        # Save to the datasets directory, replacing the default if needed or as a new one
        save_path = os.path.join('main', 'static', 'datasets', 'tamilnadu.csv')
        try:
            file.save(save_path)
            # Clear cache so new data is picked up immediately
            cache.clear()
            return jsonify({'success': 'Dataset uploaded successfully. Model will update on reload.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file type. Please upload a CSV.'}), 400

@app.route('/')
def index():
    return redirect('/dashbord')

@app.route('/dashbord')
@cache.cached(timeout=1)
@login_required
def main():
    current_month_peak,current_month_forecast,avg_temp_today = model3()
    current_month = datetime.now().strftime("%b")
    today = datetime.now()
    date = today.strftime("%d %b %y")
    context = {
        "cur_peak" :f"{current_month_peak['yhat']:.2f} MWH",
        "cur_forec" : f"{current_month_forecast['yhat']:.2f} MWH",
        "avg_temp" : f"{avg_temp_today:.2f}" if isinstance(avg_temp_today, (int, float)) else avg_temp_today,
        "month" : current_month,
        "date" : date
    }
    return render_template('index.html',**context)

@app.route('/model',methods=["POST","GET"])
@login_required
def calc():
    if request.method=='GET':
        current_month_peak,current_month_forecast,avg_temp_today = model3()
        current_month = datetime.now().strftime("%b")
        today = datetime.now()
        date = today.strftime("%d %b %y")
        context = {
            "cur_peak" :f"{current_month_peak['yhat']:.2f} MWH",
            "cur_forec" : f"{current_month_forecast['yhat']:.2f} MWH",
            "avg_temp" : f"{avg_temp_today:.2f}" if isinstance(avg_temp_today, (int, float)) else avg_temp_today,
            "month" : current_month,
            "date" : date
        }
        return render_template('modelchoose.html',**context)
    else:
        val = request.form['get']
        val = int(val)
        img1,img2 = model4(val)
        return render_template('output.html',img11=img1,img21=img2)

@app.route('/tmodel',methods=["POST","GET"])
@login_required
def calcmode():
    if request.method=='GET':
        current_month_peak,current_month_forecast,avg_temp_today = model3()
        current_month = datetime.now().strftime("%b")
        today = datetime.now()
        date = today.strftime("%d %b %y")
        context = {
            "cur_peak" :f"{current_month_peak['yhat']:.2f} MWH",
            "cur_forec" : f"{current_month_forecast['yhat']:.2f} MWH",
            "avg_temp" : f"{avg_temp_today:.2f}" if isinstance(avg_temp_today, (int, float)) else avg_temp_today,
            "month" : current_month,
            "date" : date
        }
        return render_template('tmodelchoose.html',**context)
    else:
        val = request.form['get']
        val = int(val)
        img2 = renewable(val)
        val1 = request.form['get1']
        val1 = int(val1)
        img3,img4 = stats(val1)
        img1 = thermal(val)
        return render_template('toutput.html',img11=img1,img21=img2,img31=img3,img41=img4)
    
@app.route('/blogs')
@login_required
def blogs():
    return render_template('blogs.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/feedback', methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        query = request.form.get('query')
        new_blog = Blog(name=name, emailid=email, query1=query)
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/dashbord')
    return render_template('feedback.html')

@app.route('/google-login')
def google_login():
    session['user'] = "Google User"
    # Use the existing dashboard route (note typo in original codebase 'dashbord')
    return redirect('/dashbord')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        # Simulated logic
        return redirect('/dashbord')
    return render_template('sign-in.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Simulated logic
        return redirect('/dashbord')
    return render_template('sign-up.html')

@app.route('/logout')
def logout():
    return redirect('/sign-in')

@app.route('/forget-password')
def forget_password():
    return render_template('forget-password.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
