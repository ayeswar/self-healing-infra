import time
import os
import requests
import numpy as np
from sklearn.ensemble import IsolationForest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-server.monitoring.svc.cluster.local:80")
HEALER_URL = os.getenv("HEALER_URL", "http://self-healer-svc.default.svc.cluster.local:5000")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

def fetch_metric(query, duration="30m", step="15s"):
    """Fetch metric data from Prometheus"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': f'{query}[{duration}:{step}]'}
        )
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'success' and data['data']['result']:
            # Extract values
            values = data['data']['result'][0]['values']
            # Return list of floats
            return [float(v[1]) for v in values]
        return []
    except Exception as e:
        logger.error(f"Error fetching metric {query}: {e}")
        return []

def send_alert(alert_type, details):
    """Send alert to the self-healing bot"""
    try:
        logger.warning(f"ANOMALY DETECTED: {alert_type}. Triggering healer.")
        payload = {
            "alert_type": alert_type,
            "details": details,
            "timestamp": time.time()
        }
        response = requests.post(f"{HEALER_URL}/heal", json=payload)
        response.raise_for_status()
        logger.info("Healer triggered successfully.")
    except Exception as e:
        logger.error(f"Failed to trigger healer: {e}")

def main():
    logger.info("Starting ML Anomaly Detector...")
    
    # Isolation Forest Model
    # contamination is the expected proportion of outliers
    model_cpu = IsolationForest(contamination=0.05, random_state=42)
    model_mem = IsolationForest(contamination=0.05, random_state=42)
    
    while True:
        # 1. Fetch CPU Usage (rate over 1m)
        cpu_query = 'sum(rate(container_cpu_usage_seconds_total{pod=~"self-healing-app-.*"}[1m]))'
        cpu_data = fetch_metric(cpu_query)
        
        # 2. Fetch Memory Usage
        mem_query = 'sum(container_memory_usage_bytes{pod=~"self-healing-app-.*"})'
        mem_data = fetch_metric(mem_query)
        
        if len(cpu_data) > 5:
            X_cpu = np.array(cpu_data).reshape(-1, 1)
            model_cpu.fit(X_cpu[:-1]) # Train on all but last
            prediction = model_cpu.predict(X_cpu[-1:]) # Predict last
            if prediction[0] == -1 and X_cpu[-1][0] > np.mean(X_cpu):
                send_alert("high_cpu", f"CPU usage anomaly detected: {X_cpu[-1][0]}")
                
        if len(mem_data) > 5:
            X_mem = np.array(mem_data).reshape(-1, 1)
            model_mem.fit(X_mem[:-1])
            prediction = model_mem.predict(X_mem[-1:])
            # If anomaly and value is significantly higher than mean
            if prediction[0] == -1 and X_mem[-1][0] > np.mean(X_mem) * 1.2:
                send_alert("memory_leak", f"Memory leak anomaly detected: {X_mem[-1][0]} bytes")
                
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
