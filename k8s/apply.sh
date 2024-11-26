#!/bin/bash

kubectl apply -f dashboard-deployment.yaml
kubectl apply -f dashboard-service.yaml
kubectl apply -f jd-s3-deployment.yaml
kubectl apply -f jd-s3-service.yaml
kubectl apply -f jd-upload-deployment.yaml
kubectl apply -f jd-upload-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
kubectl apply -f resume-s3-deployment.yaml
kubectl apply -f resume-s3-service.yaml
kubectl apply -f resume-upload-deployment.yaml
kubectl apply -f resume-upload-service.yaml
kubectl apply -f viewer-deployment.yaml
kubectl apply -f viewer-service.yaml
kubectl apply -f candidate-master-deployment.yaml
kubectl apply -f candidate-master-service.yaml
kubectl apply -f client-master-deployment.yaml
kubectl apply -f client-master-service.yaml
kubectl apply -f intermediate-master-deployment.yaml
kubectl apply -f intermediate-master-service.yaml
kubectl apply -f requirements-master-deployment.yaml
kubectl apply -f requirements-master-service.yaml


