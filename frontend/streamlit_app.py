import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Self-Healing Infra Dashboard", layout="wide", page_icon="🚀")

# ---- STYLING ----
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1 {color: #00E676;}
    .stButton>button {width: 100%; border-radius: 8px; background-color: #FF5252; color: white; font-weight: bold;}
    .terminal {font-family: 'Courier New', Courier, monospace; background-color: #1E1E1E; color: #00FF00; padding: 15px; border-radius: 5px; height: 300px; overflow-y: scroll;}
    </style>
""", unsafe_allow_html=True)

st.title("🚀 AI-Powered Self-Healing Infrastructure")
st.markdown("This dashboard simulates the backend **Kubernetes + Prometheus + Isolation Forest MLOps Pipeline**.")

# ---- STATE INITIALIZATION ----
if 'cpu_data' not in st.session_state:
    # Generate 50 points of baseline normal CPU usage (mean=0.1, std=0.02)
    st.session_state.cpu_data = list(np.random.normal(loc=0.1, scale=0.02, size=50))
if 'logs' not in st.session_state:
    st.session_state.logs = [
        "2026-04-25 08:00:00 - INFO - Kubernetes Cluster Initialized.",
        "2026-04-25 08:00:05 - INFO - Prometheus Scraper Started.",
        "2026-04-25 08:00:10 - INFO - ML Anomaly Detector Online (Polling every 15s)."
    ]
if 'replicas' not in st.session_state:
    st.session_state.replicas = 1

col1, col2 = st.columns([3, 1])

# ---- INTERACTIVE BUTTON ----
with col2:
    st.markdown("### ⚙️ Control Panel")
    st.metric(label="Kubernetes Replicas", value=st.session_state.replicas)
    st.markdown("---")
    if st.button("🔥 Simulate CPU Spike"):
        # Append high CPU usage points
        spike = list(np.random.normal(loc=0.85, scale=0.05, size=5))
        st.session_state.cpu_data.extend(spike)
        
        # Add to logs
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.logs.append(f"{timestamp} - WARNING - Sudden CPU traffic surge detected.")

        st.rerun()

# ---- ML ANOMALY DETECTION LOGIC ----
# Limit to last 100 points for visualization
display_data = st.session_state.cpu_data[-100:]
X = np.array(display_data).reshape(-1, 1)

# Fit Isolation Forest
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X)
predictions = model.predict(X)

# Check if the most recent point is an anomaly and high CPU
anomaly_detected = False
if predictions[-1] == -1 and X[-1][0] > 0.5:
    anomaly_detected = True

# Handle the anomaly
if anomaly_detected and "Triggering healer" not in st.session_state.logs[-1]:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"{timestamp} - ML ALARM - ANOMALY DETECTED: high_cpu. Triggering healer web-hook.")
    st.session_state.logs.append(f"{timestamp} - SYSTEM - Self-Healer triggered successfully. Patching Kubernetes API.")
    st.session_state.replicas += 1
    st.session_state.logs.append(f"{timestamp} - K8S - Deployment 'self-healing-app' scaled to {st.session_state.replicas} replicas.")

# Gradually cool down the CPU if replicas increased
if st.session_state.replicas > 1 and len(st.session_state.cpu_data) > 55:
    # If the last 5 points are high, but we scaled, bring them down
    st.session_state.cpu_data.append(np.random.normal(loc=0.2, scale=0.05))
else:
    # Normal polling adds a baseline point
    if len(st.session_state.cpu_data) <= 100 or anomaly_detected == False:
         st.session_state.cpu_data.append(np.random.normal(loc=0.1, scale=0.02))

# ---- VISUALIZATION ----
with col1:
    st.markdown("### 📊 Live Prometheus CPU Metrics")
    
    # Create Plotly Graph
    df = pd.DataFrame({
        'Time': range(len(display_data)),
        'CPU Usage': display_data,
        'Anomaly': predictions
    })
    
    fig = go.Figure()
    
    # Normal data line
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['CPU Usage'],
        mode='lines',
        name='CPU Usage',
        line=dict(color='#00E676', width=2)
    ))
    
    # Highlight Anomalies
    anomalies = df[df['Anomaly'] == -1]
    fig.add_trace(go.Scatter(
        x=anomalies['Time'], y=anomalies['CPU Usage'],
        mode='markers',
        name='Anomaly Detected',
        marker=dict(color='red', size=10, symbol='x')
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(showgrid=False, title="Time (Polling Intervals)"),
        yaxis=dict(showgrid=True, gridcolor='#333333', title="CPU Core Usage"),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ---- LOG TERMINAL ----
st.markdown("### 🖥️ Kubernetes & Healer Logs")
log_text = "<br>".join(st.session_state.logs[-15:]) # Show last 15 logs
st.markdown(f'<div class="terminal">{log_text}</div>', unsafe_allow_html=True)

# Auto-refresh mechanism to simulate live polling
time.sleep(2)
if not anomaly_detected and len(st.session_state.cpu_data) < 200:
    st.rerun()
