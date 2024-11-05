#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found!"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$HARBOR_USERNAME" ] || [ -z "$HARBOR_PASSWORD" ]; then
    echo "HARBOR_USERNAME or HARBOR_PASSWORD is not set in the .env file"
    exit 1
fi

# Default Variables
HARBOR_URL="harbor.arpansahu.me/library"
LOCAL_IMAGE="talent_bridged"
TAG="latest"
NAMESPACE="default"
SECRET_NAME="scrape-optimus-secret"
ENV_FILE=".env"
SERVICE_FILE="service.yaml"

# Function to print error message and exit
function error_exit {
    echo "$1" 1>&2
    exit 1
}

# Function to build Docker image
function build_docker_image {
    echo "Building Docker image..."
    sudo docker build -t ${LOCAL_IMAGE}:${TAG} . || error_exit "Failed to build Docker image."
}

# Function to tag Docker image
function tag_docker_image {
    echo "Tagging Docker image..."
    sudo docker tag ${LOCAL_IMAGE}:${TAG} ${HARBOR_URL}/${IMAGE_NAME}:${TAG} || error_exit "Failed to tag Docker image."
}

# Function to login to Harbor
function login_harbor {
    echo "Logging in to Harbor..."
    echo ${HARBOR_PASSWORD} | sudo docker login ${HARBOR_URL} --username ${HARBOR_USERNAME} --password-stdin || error_exit "Failed to log in to Harbor."
}

# Function to push Docker image to Harbor
function push_docker_image {
    echo "Pushing Docker image to Harbor..."
    sudo docker push ${HARBOR_URL}/${IMAGE_NAME}:${TAG} || error_exit "Failed to push Docker image to Harbor."
}

# Function to manage Kubernetes secret
function manage_kube_secret {
    echo "Deleting existing Kubernetes secret (if it exists)..."
    kubectl delete secret ${SECRET_NAME} -n ${NAMESPACE} --ignore-not-found

    echo "Creating Kubernetes secret..."
    kubectl create secret generic ${SECRET_NAME} --from-env-file=${ENV_FILE} -n ${NAMESPACE} || error_exit "Failed to create Kubernetes secret."
}

# Function to apply Kubernetes configurations
function apply_kube_configs {
    echo "Applying service configuration..."
    kubectl apply -f ${SERVICE_FILE} -n ${NAMESPACE} || error_exit "Failed to apply service configuration."

    echo "Applying deployment configuration..."
    kubectl apply -f ${DEPLOYMENT_FILE} -n ${NAMESPACE} || error_exit "Failed to apply deployment configuration."
}

# Function to verify deployment rollout
function verify_rollout {
    echo "Verifying the deployment rollout..."
    kubectl rollout status deployment/${KUBE_DEPLOYMENT} -n ${NAMESPACE} || error_exit "Failed to rollout Kubernetes deployment."
    echo "Deployment rolled out successfully!"
}

# Function to set default specific variables
function set_default_variables {
    IMAGE_NAME="talent_bridged"
    KUBE_DEPLOYMENT="scrape-optimus-app"
    DEPLOYMENT_FILE="deployment.yaml"
}

# Function to set mac specific variables
function set_mac_variables {
    IMAGE_NAME="talent_bridged_mac"
    KUBE_DEPLOYMENT="scrape-optimus-mac-app"
    DEPLOYMENT_FILE="deployment-mac.yaml"
}

# Main script execution
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 {default|mac}"
    exit 1
fi

case $1 in
    default)
        set_default_variables
        ;;
    mac)
        set_mac_variables
        ;;
    *)
        echo "Invalid option. Usage: $0 {default|mac}"
        exit 1
        ;;
esac

build_docker_image
tag_docker_image
login_harbor
push_docker_image
manage_kube_secret
apply_kube_configs
verify_rollout

echo "Deployment updated successfully!"