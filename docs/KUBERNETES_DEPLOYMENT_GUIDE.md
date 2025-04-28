# Kubernetes Deployment Guide

*Last updated: April 27, 2025*

This guide provides detailed instructions for deploying and managing the Research System application in a Kubernetes environment using the `k8s_manager.sh` script.

## Overview

The Research System can be deployed in multiple ways:
1. Local development with the Flask development server (using TinyDB)
2. Container-based deployment using Docker/Podman Compose (with PostgreSQL)
3. Full Kubernetes deployment (with PostgreSQL)

This guide focuses on options 2 and 3, using our automation scripts to simplify the process.

## Prerequisites

Before starting, ensure you have the following tools installed:

- **Podman** (version 4.0 or higher)
- **Minikube** (version 1.25 or higher)
- **kubectl** (compatible with your Minikube version)
- **GNU coreutils** (for the `gtimeout` command)

The `k8s_manager.sh` script can check and install these dependencies for you.

## The k8s_manager.sh Script

The `k8s_manager.sh` script automates setup, deployment, and management of the Research System in both Kubernetes and Podman-only environments. 

### Key Features

- Dependency verification and installation
- Kubernetes environment setup with Minikube
- Research System deployment to Kubernetes
- PostgreSQL database setup
- Health and status checking
- Podman-only mode for local testing

### Common Commands

```bash
# Check and install dependencies
./scripts/k8s_manager.sh setup

# Start Kubernetes environment
./scripts/k8s_manager.sh start

# Deploy Research System to Kubernetes
./scripts/k8s_manager.sh deploy

# Check environment status
./scripts/k8s_manager.sh status

# View application logs
./scripts/k8s_manager.sh logs

# Stop Kubernetes environment
./scripts/k8s_manager.sh stop

# Clean up all resources
./scripts/k8s_manager.sh clean

# Show help message
./scripts/k8s_manager.sh help
```

### Podman-only Mode

For local development without Kubernetes, you can use the Podman-only mode:

```bash
# Start containers using podman-compose
./scripts/k8s_manager.sh podman-start

# Stop podman containers
./scripts/k8s_manager.sh podman-stop
```

## Deployment Process

### 1. Setting Up the Environment

First, check and install required dependencies:

```bash
./scripts/k8s_manager.sh setup
```

This command will:
- Check for Homebrew, Podman, Minikube, kubectl, and podman-compose
- Install missing dependencies (with `--auto-install` flag)
- Ensure Podman machine is running

### 2. Starting Kubernetes

To start the Kubernetes environment with Minikube:

```bash
./scripts/k8s_manager.sh start
```

Options:
- `--driver=<driver>`: Kubernetes driver (podman, docker, hyperkit)
- `--memory=<MB>`: Memory allocation in MB (default: 3072)
- `--cpus=<count>`: CPU count (default: 2)
- `--force`: Force recreation of the environment

This creates a Minikube cluster with appropriate settings for the Research System.

### 3. Deploying the Research System

Once Kubernetes is running, deploy the Research System:

```bash
./scripts/k8s_manager.sh deploy
```

This command:
1. Builds the Research System container image
2. Loads the image into Minikube
3. Creates necessary namespaces
4. Deploys secrets and ConfigMaps
5. Deploys PostgreSQL database
6. Deploys the Research System application
7. Creates required services
8. Waits for deployments to be ready

### 4. Accessing the Application

After deployment, the script will provide information about accessing the service:

```bash
# In a separate terminal, run:
kubectl port-forward svc/research-system 8181:80

# Then access the application at:
http://localhost:8181
```

You can also check the application status:

```bash
./scripts/k8s_manager.sh status
```

### 5. Viewing Logs

To view application logs:

```bash
./scripts/k8s_manager.sh logs
```

### 6. Stopping and Cleaning Up

To stop the Kubernetes environment:

```bash
./scripts/k8s_manager.sh stop
```

To clean up all resources:

```bash
./scripts/k8s_manager.sh clean
```

## Podman-only Deployment

For development or testing without Kubernetes, you can use Podman-only mode:

```bash
# Start the application with PostgreSQL
./scripts/k8s_manager.sh podman-start

# Stop the application
./scripts/k8s_manager.sh podman-stop
```

This mode uses podman-compose to start the Research System and PostgreSQL containers directly, without Kubernetes overhead.

## Troubleshooting

### Image Loading Issues

If you encounter problems with image loading in Minikube:

```
Failed to load image into minikube.
```

Try using the Podman-only mode or check:
- Minikube driver compatibility
- Available disk space
- Network connectivity

### Database Connection Issues

If the application can't connect to PostgreSQL:

1. Check PostgreSQL pod status:
   ```bash
   kubectl get pods -l app=postgres
   ```

2. View PostgreSQL logs:
   ```bash
   kubectl logs -l app=postgres
   ```

3. Verify ConfigMap and Secret were applied correctly:
   ```bash
   kubectl get configmap
   kubectl get secret
   ```

### Resource Limitations

If pods fail to start due to resource limits:

1. Check available resources:
   ```bash
   kubectl describe nodes
   ```

2. Adjust the Minikube settings:
   ```bash
   ./scripts/k8s_manager.sh start --memory=4096 --cpus=4
   ```

## Best Practices

1. **Use the setup command first**: Always run the setup command before attempting to deploy
2. **Check status regularly**: Use the status command to verify system health
3. **Clean up when done**: Run the clean command to free resources when finished
4. **Use podman-start for quick testing**: The podman-only mode is faster for development
5. **Check logs when troubleshooting**: Logs provide valuable information about issues

## Additional Resources

- [Research System Development Plan](./RESEARCH_SYSTEM_DEV_PLAN.md)
- [Database Documentation](./DATABASE.md)
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)
- [Kubernetes Official Documentation](https://kubernetes.io/docs/home/)
- [Podman Documentation](https://docs.podman.io/)