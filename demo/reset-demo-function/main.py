import base64
import datetime
import os
from tempfile import NamedTemporaryFile

import google.auth
import kubernetes
from google.cloud import container_v1

GCP_PROJECT = os.environ["GCP_PROJECT"]
CLUSTER_NAME = os.environ["CLUSTER_NAME"]
DEPLOYMENT_NAME = os.environ["DEPLOYMENT_NAME"]


def reset_demo(event, context):
    # Authenticate to Google using Application Default credentials
    credentials, project = google.auth.default()

    # Fetch all clusters in the project
    cluster_client = container_v1.ClusterManagerClient(credentials=credentials)
    response = cluster_client.list_clusters(GCP_PROJECT, "-")

    # Get the cluster with the requested name from the list of clusters
    cluster = next(
        cluster for cluster in response.clusters if cluster.name == CLUSTER_NAME
    )
    cluster_ip = cluster.endpoint
    cluster_cert = cluster.master_auth.cluster_ca_certificate

    # Configure authentication for Kubernetes API connection
    k8s_config = kubernetes.client.Configuration()
    k8s_config.api_key["authorization"] = credentials.token  # GCP Auth Token
    k8s_config.api_key_prefix["authorization"] = "Bearer"
    k8s_config.host = f"https://{cluster_ip}"
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
    reset_demo()
