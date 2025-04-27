# Architecture Diagrams

These diagrams illustrate the architecture of the K8s Python App.

## High-Level Architecture

```mermaid
graph TD
    subgraph "Client"
        User[User/API Consumer]
    end

    subgraph "Kubernetes Cluster"
        subgraph "K8s Service"
            Service[K8s Service]
        end
        
        subgraph "Pod Replicas"
            Pod1[Pod Instance 1]
            Pod2[Pod Instance 2]
            Pod3[Pod Instance N...]
        end
        
        subgraph "Container Architecture"
            subgraph "Flask Application Container"
                Flask[Web Layer - Flask App] --> BL[Business Logic Layer]
                Flask --> Health[Health Monitoring]
                Flask --> Log[Logging System]
            end
        end
    end
    
    subgraph "Standalone Mode (macOS/Podman)"
        Podman[Podman Container] --> |SSH Port Forwarding| Mac[macOS Host]
    end
    
    User --> Service
    Service --> Pod1
    Service --> Pod2
    Service --> Pod3
    
    Pod1 --> Flask
    Pod2 --> Flask
    Pod3 --> Flask
    
    User --> Mac
    
    subgraph "Management"
        Script[app_manager.sh Script]
    end
    
    Script --> |Manages| Podman
    Script --> |Manages| Pod1
    Script --> |Manages| Pod2
    Script --> |Manages| Pod3
    
    subgraph "Configuration"
        EnvVars[Environment Variables]
        ConfigFile[config.yaml]
    end
    
    EnvVars --> Flask
    ConfigFile --> Flask
```

## Detailed Component Architecture

```mermaid
flowchart TD
    subgraph "Application Components"
        subgraph "Web Layer"
            Flask[Flask Web Application]
            Routes[URL Routes]
            APIEndpoints[API Endpoints]
            
            Flask --> Routes
            Flask --> APIEndpoints
        end
        
        subgraph "Business Logic Layer"
            CoreLogic[Core Application Logic]
            DataProcessing[Data Processing]
            Validation[Input Validation]
            
            CoreLogic --> DataProcessing
            CoreLogic --> Validation
        end
        
        subgraph "Health Monitoring"
            HealthEndpoint["/health Endpoint"]
            StatusCheck[Status Checking]
            DiagnosticTools[Diagnostic Tools]
            
            HealthEndpoint --> StatusCheck
            HealthEndpoint --> DiagnosticTools
        end
        
        subgraph "Logging System"
            Logger[Logger]
            StructuredLogs[Structured Logs]
            LogRotation[Log Rotation]
            
            Logger --> StructuredLogs
            Logger --> LogRotation
        end
        
        Routes --> CoreLogic
        APIEndpoints --> CoreLogic
        CoreLogic --> Logger
        StatusCheck --> Logger
    end
    
    subgraph "Deployment & Configuration"
        AppManager[app_manager.sh]
        EnvVars[Environment Variables]
        ConfigFile[config.yaml]
        K8sManifests[Kubernetes Manifests]
        
        AppManager --> EnvVars
        AppManager --> ConfigFile
        AppManager --> K8sManifests
    end
    
    EnvVars --> Flask
    ConfigFile --> Flask
    K8sManifests --> Flask
```
