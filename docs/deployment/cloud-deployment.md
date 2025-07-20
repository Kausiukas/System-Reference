# Cloud Deployment Guide

## 🎯 **Overview**

This guide provides comprehensive instructions for deploying the Cloud-Dedicated Real-Time Repository Processing System across major cloud providers (AWS, GCP, Azure) with production-ready configurations, monitoring, and scaling capabilities.

## ☁️ **Cloud Provider Selection**

### **AWS (Amazon Web Services)**
- **Best for**: Enterprise workloads, global presence, extensive service ecosystem
- **Strengths**: Mature Kubernetes (EKS), managed databases, advanced monitoring
- **Cost**: Competitive pricing with reserved instances

### **GCP (Google Cloud Platform)**
- **Best for**: AI/ML workloads, container-native applications, global networking
- **Strengths**: Native Kubernetes (GKE), AI/ML services, global load balancing
- **Cost**: Sustained use discounts, preemptible instances

### **Azure (Microsoft Azure)**
- **Best for**: Microsoft ecosystem integration, hybrid cloud, enterprise compliance
- **Strengths**: AKS, Active Directory integration, compliance certifications
- **Cost**: Enterprise agreements, hybrid benefits

## 🏗️ **Infrastructure Architecture**

### **Multi-Zone Deployment**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Global Load Balancer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Zone A (Primary) │ Zone B (Secondary) │ Zone C (Tertiary)                  │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐                   │
│  │ Kubernetes  │  │  │ Kubernetes  │  │  │ Kubernetes  │                   │
│  │ Cluster     │  │  │ Cluster     │  │  │ Cluster     │                   │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘                   │
│                   │                   │                                     │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐                   │
│  │ Database    │  │  │ Database    │  │  │ Database    │                   │
│  │ (Primary)   │  │  │ (Replica)   │  │  │ (Replica)   │                   │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Network Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Internet Gateway                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                            Public Subnets                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │ │
│  │  │ Load        │  │ Bastion     │  │ NAT         │                     │ │
│  │  │ Balancer    │  │ Host        │  │ Gateway     │                     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           Private Subnets                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │ │
│  │  │ Kubernetes  │  │ Database    │  │ Cache       │                     │ │
│  │  │ Workers     │  │ Cluster     │  │ (Redis)     │                     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 **AWS Deployment**

### **Prerequisites**

```bash
# Install required tools
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs)"
sudo apt-get update && sudo apt-get install terraform
```

### **Infrastructure Setup with Terraform**

#### **1. Main Terraform Configuration**

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    bucket = "system-reference-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "System-Reference"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  
  node_groups = {
    general = {
      desired_capacity = 3
      max_capacity     = 10
      min_capacity     = 1
      
      instance_types = ["t3.medium", "t3.large"]
      capacity_type  = "ON_DEMAND"
      
      labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
      
      taints = []
    }
    
    processing = {
      desired_capacity = 2
      max_capacity     = 20
      min_capacity     = 1
      
      instance_types = ["c5.large", "c5.xlarge"]
      capacity_type  = "ON_DEMAND"
      
      labels = {
        Environment = var.environment
        NodeGroup   = "processing"
      }
      
      taints = [{
        key    = "dedicated"
        value  = "processing"
        effect = "NO_SCHEDULE"
      }]
    }
  }
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  identifier        = var.database_identifier
  engine            = "postgres"
  engine_version    = "14.7"
  instance_class    = var.database_instance_class
  allocated_storage = var.database_allocated_storage
  
  db_name  = var.database_name
  username = var.database_username
  password = var.database_password
  
  vpc_security_group_ids = [module.vps.security_group_id]
  subnet_ids             = module.vpc.database_subnet_ids
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = true
  skip_final_snapshot = false
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"
  
  cluster_id           = var.redis_cluster_id
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_cache_nodes
  parameter_group_name = "default.redis6.x"
  
  vpc_security_group_ids = [module.vps.security_group_id]
  subnet_ids             = module.vpc.private_subnet_ids
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
}

# S3 Buckets
module "storage" {
  source = "./modules/storage"
  
  bucket_names = [
    "system-reference-repositories",
    "system-reference-backups",
    "system-reference-logs",
    "system-reference-terraform-state"
  ]
  
  environment = var.environment
}
```

#### **2. VPC Module**

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.environment}-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.azs[count.index]
  
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.environment}-public-${var.azs[count.index]}"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + length(var.azs))
  availability_zone = var.azs[count.index]
  
  tags = {
    Name = "${var.environment}-private-${var.azs[count.index]}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "database" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 2 * length(var.azs))
  availability_zone = var.azs[count.index]
  
  tags = {
    Name = "${var.environment}-database-${var.azs[count.index]}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.environment}-igw"
  }
}

resource "aws_nat_gateway" "main" {
  count         = length(var.azs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = {
    Name = "${var.environment}-nat-${var.azs[count.index]}"
  }
}

resource "aws_eip" "nat" {
  count = length(var.azs)
  vpc   = true
  
  tags = {
    Name = "${var.environment}-eip-${var.azs[count.index]}"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = length(var.azs)
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = {
    Name = "${var.environment}-private-rt-${var.azs[count.index]}"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_security_group" "main" {
  name_prefix = "${var.environment}-sg"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.environment}-sg"
  }
}
```

### **Kubernetes Deployment**

#### **1. Namespace Configuration**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: system-reference
  labels:
    name: system-reference
    environment: production
```

#### **2. ConfigMap and Secrets**

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: system-reference-config
  namespace: system-reference
data:
  app.yaml: |
    environment: production
    log_level: INFO
    max_workers: 20
    processing_timeout: 1800
  
  database.yaml: |
    host: system-reference-db.cluster-xyz.us-west-2.rds.amazonaws.com
    port: 5432
    name: system_reference_prod
    ssl: true
  
  redis.yaml: |
    host: system-reference-redis.xyz.cache.amazonaws.com
    port: 6379
    ssl: true
  
  ai.yaml: |
    model: gpt-4
    temperature: 0.3
    max_tokens: 2000
    embedding_model: all-MiniLM-L6-v2
```

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: system-reference-secrets
  namespace: system-reference
type: Opaque
data:
  database_password: <base64-encoded-password>
  openai_api_key: <base64-encoded-key>
  github_token: <base64-encoded-token>
  jwt_secret: <base64-encoded-secret>
```

#### **3. Application Deployments**

```yaml
# k8s/deployments.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-ui
  namespace: system-reference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-ui
  template:
    metadata:
      labels:
        app: web-ui
    spec:
      containers:
      - name: web-ui
        image: system-reference/web-ui:latest
        ports:
        - containerPort: 8501
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: system-reference-secrets
              key: database_url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: system-reference-secrets
              key: redis_url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: real-time-orchestrator
  namespace: system-reference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: real-time-orchestrator
  template:
    metadata:
      labels:
        app: real-time-orchestrator
    spec:
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "processing"
        effect: "NoSchedule"
      containers:
      - name: orchestrator
        image: system-reference/orchestrator:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: system-reference-secrets
              key: database_url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: system-reference-secrets
              key: redis_url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

#### **4. Services**

```yaml
# k8s/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-ui-service
  namespace: system-reference
spec:
  selector:
    app: web-ui
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
  namespace: system-reference
spec:
  selector:
    app: real-time-orchestrator
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: ClusterIP
```

#### **5. Ingress Configuration**

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: system-reference-ingress
  namespace: system-reference
  annotations:
    kubernetes.io/ingress.class: "alb"
    alb.ingress.kubernetes.io/scheme: "internet-facing"
    alb.ingress.kubernetes.io/target-type: "ip"
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:us-west-2:123456789012:certificate/xyz"
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  rules:
  - host: system-reference.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-ui-service
            port:
              number: 80
```

### **Monitoring and Logging**

#### **1. Prometheus Configuration**

```yaml
# monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "alert_rules.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093
    
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name
```

#### **2. Grafana Dashboards**

```yaml
# monitoring/grafana-dashboards.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: monitoring
data:
  system-reference-dashboard.json: |
    {
      "dashboard": {
        "title": "System Reference Dashboard",
        "panels": [
          {
            "title": "Processing Duration",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, processing_duration_seconds_bucket)",
                "legendFormat": "95th percentile"
              }
            ]
          },
          {
            "title": "Success Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(processing_success_total[5m])",
                "legendFormat": "Success Rate"
              }
            ]
          },
          {
            "title": "Active Repositories",
            "type": "gauge",
            "targets": [
              {
                "expr": "active_repositories",
                "legendFormat": "Active Repositories"
              }
            ]
          }
        ]
      }
    }
```

## 🔧 **GCP Deployment**

### **Prerequisites**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install kubectl
gcloud components install kubectl

# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs)"
sudo apt-get update && sudo apt-get install terraform
```

### **GKE Cluster Setup**

```bash
# Create GKE cluster
gcloud container clusters create system-reference-cluster \
  --zone us-west1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials system-reference-cluster --zone us-west1-a
```

### **Cloud SQL Setup**

```bash
# Create Cloud SQL instance
gcloud sql instances create system-reference-db \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-4096 \
  --region=us-west1 \
  --storage-type=SSD \
  --storage-size=100GB \
  --backup-start-time=03:00 \
  --enable-backup

# Create database
gcloud sql databases create system_reference_prod --instance=system-reference-db

# Create user
gcloud sql users create system-reference-user \
  --instance=system-reference-db \
  --password=secure-password
```

## 🔧 **Azure Deployment**

### **Prerequisites**

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Install kubectl
az aks install-cli

# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs)"
sudo apt-get update && sudo apt-get install terraform
```

### **AKS Cluster Setup**

```bash
# Create resource group
az group create --name system-reference-rg --location westus2

# Create AKS cluster
az aks create \
  --resource-group system-reference-rg \
  --name system-reference-cluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10

# Get credentials
az aks get-credentials --resource-group system-reference-rg --name system-reference-cluster
```

## 🚀 **Deployment Scripts**

### **Automated Deployment Script**

```bash
#!/bin/bash
# deploy.sh

set -e

# Configuration
ENVIRONMENT=${1:-production}
CLOUD_PROVIDER=${2:-aws}
REGION=${3:-us-west-2}

echo "Deploying System Reference to $ENVIRONMENT on $CLOUD_PROVIDER in $REGION"

# Validate prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check required tools
    command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but not installed. Aborting." >&2; exit 1; }
    command -v terraform >/dev/null 2>&1 || { echo "terraform is required but not installed. Aborting." >&2; exit 1; }
    
    # Check cloud provider specific tools
    case $CLOUD_PROVIDER in
        aws)
            command -v aws >/dev/null 2>&1 || { echo "aws CLI is required but not installed. Aborting." >&2; exit 1; }
            ;;
        gcp)
            command -v gcloud >/dev/null 2>&1 || { echo "gcloud CLI is required but not installed. Aborting." >&2; exit 1; }
            ;;
        azure)
            command -v az >/dev/null 2>&1 || { echo "azure CLI is required but not installed. Aborting." >&2; exit 1; }
            ;;
    esac
    
    echo "Prerequisites check passed."
}

# Deploy infrastructure
deploy_infrastructure() {
    echo "Deploying infrastructure..."
    
    cd terraform/$CLOUD_PROVIDER
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="region=$REGION" \
        -out=tfplan
    
    # Apply deployment
    terraform apply tfplan
    
    cd ../..
}

# Build and push Docker images
build_images() {
    echo "Building and pushing Docker images..."
    
    # Set Docker registry based on cloud provider
    case $CLOUD_PROVIDER in
        aws)
            REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com
            aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REGISTRY
            ;;
        gcp)
            REGISTRY=gcr.io/$(gcloud config get-value project)
            gcloud auth configure-docker
            ;;
        azure)
            REGISTRY=$(az acr show --name systemreference --query loginServer --output tsv)
            az acr login --name systemreference
            ;;
    esac
    
    # Build images
    docker build -t $REGISTRY/web-ui:latest src/web-ui/
    docker build -t $REGISTRY/orchestrator:latest src/orchestrator/
    docker build -t $REGISTRY/processor:latest src/processor/
    docker build -t $REGISTRY/ai-engine:latest src/ai-engine/
    
    # Push images
    docker push $REGISTRY/web-ui:latest
    docker push $REGISTRY/orchestrator:latest
    docker push $REGISTRY/processor:latest
    docker push $REGISTRY/ai-engine:latest
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    echo "Deploying Kubernetes resources..."
    
    # Update image tags in deployment files
    sed -i "s|IMAGE_REGISTRY|$REGISTRY|g" k8s/deployments.yaml
    
    # Apply Kubernetes resources
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/deployments.yaml
    kubectl apply -f k8s/services.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for deployments to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/web-ui -n system-reference
    kubectl wait --for=condition=available --timeout=300s deployment/real-time-orchestrator -n system-reference
}

# Deploy monitoring
deploy_monitoring() {
    echo "Deploying monitoring stack..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus
    kubectl apply -f monitoring/prometheus-config.yaml
    kubectl apply -f monitoring/prometheus-deployment.yaml
    
    # Deploy Grafana
    kubectl apply -f monitoring/grafana-config.yaml
    kubectl apply -f monitoring/grafana-deployment.yaml
    
    # Deploy AlertManager
    kubectl apply -f monitoring/alertmanager-config.yaml
    kubectl apply -f monitoring/alertmanager-deployment.yaml
}

# Verify deployment
verify_deployment() {
    echo "Verifying deployment..."
    
    # Check pod status
    kubectl get pods -n system-reference
    kubectl get pods -n monitoring
    
    # Check services
    kubectl get services -n system-reference
    
    # Check ingress
    kubectl get ingress -n system-reference
    
    # Run health checks
    kubectl run health-check --image=curlimages/curl --rm -it --restart=Never -- \
        curl -f http://web-ui-service.system-reference.svc.cluster.local/health
}

# Main deployment flow
main() {
    check_prerequisites
    deploy_infrastructure
    build_images
    deploy_kubernetes
    deploy_monitoring
    verify_deployment
    
    echo "Deployment completed successfully!"
    echo "Access the application at: https://system-reference.example.com"
}

# Run main function
main "$@"
```

## 📊 **Cost Optimization**

### **Resource Optimization**

```yaml
# k8s/hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-ui-hpa
  namespace: system-reference
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-ui
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **Spot Instances (AWS)**

```hcl
# terraform/aws/spot-instances.tf
resource "aws_eks_node_group" "spot" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "spot"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = aws_subnet.private[*].id
  
  capacity_type = "SPOT"
  
  scaling_config {
    desired_size = 2
    max_size     = 10
    min_size     = 1
  }
  
  instance_types = ["t3.medium", "t3.large", "c5.large"]
  
  labels = {
    Environment = var.environment
    NodeGroup   = "spot"
  }
  
  taints = [{
    key    = "spot"
    value  = "true"
    effect = "NO_SCHEDULE"
  }]
}
```

This comprehensive cloud deployment guide provides everything needed to deploy the System-Reference platform across major cloud providers with production-ready configurations, monitoring, and cost optimization strategies. 