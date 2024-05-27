#!/bin/bash

# Apply PersistentVolumeClaim (PVC) for shared storage
kubectl apply -f persistent-volume-claim.yml

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f postgres/deployment.yml
kubectl apply -f postgres/service.yml

# Deploy Odoo
echo "Deploying Odoo..."
kubectl apply -f odoo/deployment.yml
kubectl apply -f odoo/service.yml

# Deploy Asterisk
echo "Deploying Asterisk..."
kubectl apply -f asterisk/deployment.yml
kubectl apply -f asterisk/service.yml

# Deploy Asterisk-Logs
echo "Deploying Asterisk-Logs..."
kubectl apply -f asterisk-logs/deployment.yml
kubectl apply -f asterisk-logs/service.yml

# Deploy Asterisk-Numbers
echo "Deploying Asterisk-Numbers..."
kubectl apply -f asterisk-numbers/deployment.yml
kubectl apply -f asterisk-numbers/service.yml

# Display services information
echo "Services:"
kubectl get services
