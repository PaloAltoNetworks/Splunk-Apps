import base64
import datetime
import logging
import os
import sys
from tempfile import NamedTemporaryFile

import google.auth
import json_logging
import kubernetes.client
from google.cloud import container_v1

# Set up logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
json_logging.init_non_web(enable_json=True)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler(sys.stdout))

# Collect env vars
GCP_PROJECT = os.environ["GCP_PROJECT"]
CLUSTER_NAME = os.environ["CLUSTER_NAME"]
DEPLOYMENT_NAME = os.environ["DEPLOYMENT_NAME"]


def reset_demo(event, context):
    # Authenticate to Google using Application Default credentials
    credentials, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
        ]
    )

    # Fetch all clusters in the project
    cluster_client = container_v1.ClusterManagerClient(credentials=credentials)
    request = container_v1.ListClustersRequest(
        parent=f"projects/{GCP_PROJECT}/locations/-"
    )
    response = cluster_client.list_clusters(request=request)

    logger.debug(f"Found {len(response.clusters)} clusters")

    # Get the cluster with the requested name from the list of clusters
    cluster = next(
        cluster for cluster in response.clusters if cluster.name == CLUSTER_NAME
    )
    cluster_ip = cluster.endpoint
    cluster_cert = cluster.master_auth.cluster_ca_certificate
    logger.debug(f"cluster_ip: {cluster_ip}")

    # Configure authentication for Kubernetes API connection
    k8s_config = kubernetes.client.Configuration()
    k8s_config.host = f"https://{cluster_ip}"
    k8s_config.verify_ssl = True
    if not credentials.valid:
        logger.debug("Credentials not valid, refreshing")
        credentials.refresh(
            google.auth.transport.requests.Request()
        )  # Create GCP Auth Token
    credentials.apply(k8s_config.api_key)

    # Create a temporary file containing the CA cert to validate Kubernetes
    # cluster TLS certificate
    with NamedTemporaryFile(delete=False) as cert:
        cert.write(base64.decodebytes(cluster_cert.encode()))
        k8s_config.ssl_ca_cert = cert.name

    # Create the Kubernetes API client
    k8s_client = kubernetes.client.AppsV1Api(kubernetes.client.ApiClient(k8s_config))

    # Payload to reset a pod (see https://stackoverflow.com/a/59051313)
    reset_request = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.datetime.now().isoformat()
                    }
                }
            }
        }
    }

    # Perform a `kubectl rollout restart` to restart the pod
    response = k8s_client.patch_namespaced_deployment(
        DEPLOYMENT_NAME, "default", reset_request
    )


if __name__ == "__main__":
    reset_demo({}, {})
