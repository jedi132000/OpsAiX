#!/bin/bash

# OpsAiX Kubernetes Deployment Script
# Supports multi-cloud deployment across AWS, Azure, GCP

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CLOUD=""
REGION=""
NAMESPACE="opsaix"
HELM_RELEASE="opsaix"
VALUES_FILE=""
DRY_RUN=false
MULTI_CLOUD=false
PRIMARY_CLOUD=""
SECONDARY_CLOUD=""
TERTIARY_CLOUD=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
🚀 OpsAiX Multi-Cloud Kubernetes Deployment Script

Usage: $0 [OPTIONS]

Single Cloud Deployment:
    --cloud <aws|azure|gcp>     Target cloud provider
    --region <region>           Cloud region (e.g., us-east-1, eastus, us-central1)

Multi-Cloud Deployment:
    --multi-cloud              Enable multi-cloud deployment
    --primary <cloud>          Primary cloud provider
    --secondary <cloud>        Secondary cloud provider  
    --tertiary <cloud>         Tertiary cloud provider (optional)

General Options:
    --namespace <namespace>    Kubernetes namespace (default: opsaix)
    --release <name>          Helm release name (default: opsaix)
    --values <file>           Custom values file
    --dry-run                 Perform dry run without actual deployment
    --help                    Show this help message

Cloud-Specific Examples:
    # AWS EKS deployment
    $0 --cloud aws --region us-east-1

    # Azure AKS deployment  
    $0 --cloud azure --region eastus

    # GCP GKE deployment
    $0 --cloud gcp --region us-central1

Multi-Cloud Examples:
    # Deploy across AWS and Azure
    $0 --multi-cloud --primary aws --secondary azure

    # Deploy across all three clouds
    $0 --multi-cloud --primary aws --secondary azure --tertiary gcp

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cloud)
            CLOUD="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --release)
            HELM_RELEASE="$2"
            shift 2
            ;;
        --values)
            VALUES_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --multi-cloud)
            MULTI_CLOUD=true
            shift
            ;;
        --primary)
            PRIMARY_CLOUD="$2"
            shift 2
            ;;
        --secondary)
            SECONDARY_CLOUD="$2"
            shift 2
            ;;
        --tertiary)
            TERTIARY_CLOUD="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate cloud providers
validate_cloud() {
    local cloud=$1
    case $cloud in
        aws|azure|gcp)
            return 0
            ;;
        *)
            print_error "Unsupported cloud provider: $cloud"
            print_error "Supported providers: aws, azure, gcp"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed"
        exit 1
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_error "Please ensure kubectl is configured and cluster is accessible"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Deploy to single cloud
deploy_single_cloud() {
    local cloud=$1
    local region=$2
    
    print_status "Deploying OpsAiX to $cloud in region $region..."
    
    # Validate cloud provider
    validate_cloud $cloud
    
    # Set cloud-specific values
    local values_args=""
    if [ ! -z "$VALUES_FILE" ]; then
        values_args="--values $VALUES_FILE"
    fi
    
    # Set cloud-specific values
    values_args="$values_args --set global.cloud=$cloud --set global.region=$region"
    
    # Cloud-specific configurations
    case $cloud in
        aws)
            values_args="$values_args --set ingress.className=aws-load-balancer-controller"
            values_args="$values_args --set global.storageClass=gp3"
            ;;
        azure)
            values_args="$values_args --set ingress.className=azure/application-gateway"  
            values_args="$values_args --set global.storageClass=managed-premium"
            ;;
        gcp)
            values_args="$values_args --set ingress.className=gce"
            values_args="$values_args --set global.storageClass=standard-rwo"
            ;;
    esac
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Add Bitnami repo for dependencies
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    # Deploy with Helm
    local helm_cmd="helm upgrade --install $HELM_RELEASE k8s/helm/opsaix/ --namespace $NAMESPACE $values_args"
    
    if [ "$DRY_RUN" = true ]; then
        helm_cmd="$helm_cmd --dry-run"
        print_warning "Performing dry run deployment..."
    fi
    
    print_status "Executing: $helm_cmd"
    eval $helm_cmd
    
    if [ "$DRY_RUN" = false ]; then
        print_success "OpsAiX deployed successfully to $cloud!"
        print_deployment_info $cloud
    else
        print_success "Dry run completed successfully"
    fi
}

# Deploy to multiple clouds
deploy_multi_cloud() {
    print_status "Deploying OpsAiX in multi-cloud configuration..."
    
    # Validate cloud providers
    validate_cloud $PRIMARY_CLOUD
    if [ ! -z "$SECONDARY_CLOUD" ]; then
        validate_cloud $SECONDARY_CLOUD
    fi
    if [ ! -z "$TERTIARY_CLOUD" ]; then
        validate_cloud $TERTIARY_CLOUD
    fi
    
    # Deploy to primary cloud
    print_status "Deploying to primary cloud: $PRIMARY_CLOUD"
    CLOUD=$PRIMARY_CLOUD
    deploy_single_cloud $PRIMARY_CLOUD "auto"
    
    # Deploy to secondary cloud
    if [ ! -z "$SECONDARY_CLOUD" ]; then
        print_status "Deploying to secondary cloud: $SECONDARY_CLOUD"
        HELM_RELEASE="$HELM_RELEASE-secondary"
        CLOUD=$SECONDARY_CLOUD  
        deploy_single_cloud $SECONDARY_CLOUD "auto"
    fi
    
    # Deploy to tertiary cloud
    if [ ! -z "$TERTIARY_CLOUD" ]; then
        print_status "Deploying to tertiary cloud: $TERTIARY_CLOUD"
        HELM_RELEASE="$HELM_RELEASE-tertiary"
        CLOUD=$TERTIARY_CLOUD
        deploy_single_cloud $TERTIARY_CLOUD "auto"
    fi
    
    print_success "Multi-cloud deployment completed successfully!"
}

# Print deployment information
print_deployment_info() {
    local cloud=$1
    
    echo
    echo "🎉 Deployment Summary ($cloud):"
    echo "================================"
    echo "Namespace: $NAMESPACE"  
    echo "Release: $HELM_RELEASE"
    echo "Cloud: $cloud"
    echo "Region: $REGION"
    echo
    
    print_status "Checking deployment status..."
    kubectl get pods -n $NAMESPACE
    
    echo
    print_status "Getting service information..."
    kubectl get svc -n $NAMESPACE
    
    echo
    print_status "Getting ingress information..."
    kubectl get ingress -n $NAMESPACE
    
    echo
    print_success "OpsAiX is ready! 🚀"
    echo "Dashboard URL will be available once ingress is configured"
    echo
    echo "Useful commands:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl logs -f deployment/$HELM_RELEASE -n $NAMESPACE"
    echo "  helm status $HELM_RELEASE -n $NAMESPACE"
}

# Main execution
main() {
    echo "🚨 OpsAiX Multi-Cloud Kubernetes Deployment 🚀"
    echo "==============================================="
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Validate inputs and deploy
    if [ "$MULTI_CLOUD" = true ]; then
        if [ -z "$PRIMARY_CLOUD" ]; then
            print_error "Primary cloud must be specified for multi-cloud deployment"
            usage
            exit 1
        fi
        deploy_multi_cloud
    else
        if [ -z "$CLOUD" ] || [ -z "$REGION" ]; then
            print_error "Cloud and region must be specified for single cloud deployment"
            usage
            exit 1
        fi
        deploy_single_cloud $CLOUD $REGION
    fi
}

# Run main function
main