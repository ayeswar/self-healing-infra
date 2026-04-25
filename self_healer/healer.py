from flask import Flask, request, jsonify
from kubernetes import client, config
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load Kubernetes configuration
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config.")
except config.ConfigException:
    try:
        config.load_kube_config()
        logger.info("Loaded local kubeconfig.")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes config: {e}")

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

NAMESPACE = os.getenv("NAMESPACE", "default")
TARGET_DEPLOYMENT = os.getenv("TARGET_DEPLOYMENT", "self-healing-app")

@app.route('/heal', methods=['POST'])
def heal():
    data = request.json
    alert_type = data.get("alert_type")
    details = data.get("details")
    
    logger.info(f"Received heal request: {alert_type} - {details}")
    
    if alert_type == "memory_leak":
        return restart_deployment()
    elif alert_type == "high_cpu":
        return scale_deployment()
    elif alert_type == "high_error_rate":
        return restart_deployment()
        
    return jsonify({"status": "ignored", "message": "Unknown alert type"}), 400

def restart_deployment():
    """Restarts the deployment by patching its annotations (forces a rolling update)."""
    try:
        import datetime
        now = datetime.datetime.utcnow().isoformat("T") + "Z"
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now
                        }
                    }
                }
            }
        }
        apps_v1.patch_namespaced_deployment(
            name=TARGET_DEPLOYMENT,
            namespace=NAMESPACE,
            body=body
        )
        logger.info(f"Deployment {TARGET_DEPLOYMENT} restarted.")
        return jsonify({"status": "success", "action": "restarted_deployment"})
    except Exception as e:
        logger.error(f"Failed to restart deployment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def scale_deployment():
    """Scales the deployment up by 1 replica (up to a max of 5)."""
    try:
        deployment = apps_v1.read_namespaced_deployment(name=TARGET_DEPLOYMENT, namespace=NAMESPACE)
        current_replicas = deployment.spec.replicas
        
        if current_replicas >= 5:
            logger.info("Deployment is already at max replicas (5). Will not scale.")
            return jsonify({"status": "ignored", "action": "max_replicas_reached"})
            
        deployment.spec.replicas = current_replicas + 1
        apps_v1.patch_namespaced_deployment_scale(
            name=TARGET_DEPLOYMENT,
            namespace=NAMESPACE,
            body=deployment
        )
        logger.info(f"Deployment {TARGET_DEPLOYMENT} scaled to {current_replicas + 1}.")
        return jsonify({"status": "success", "action": "scaled_deployment", "replicas": current_replicas + 1})
    except Exception as e:
        logger.error(f"Failed to scale deployment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
