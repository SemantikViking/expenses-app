# Architecture Diagrams

This document contains visual representations of the Receipt Processor system architecture.

## System Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI[CLI Interface]
        API[REST API]
        WEB[Web Interface]
    end
    
    subgraph "Core System"
        CORE[Core Processor]
        AI[AI Vision Service]
        FILE[File Manager]
        STORAGE[Storage Manager]
    end
    
    subgraph "Data Layer"
        MODELS[Data Models]
        JSON[JSON Storage]
        LOGS[Log Files]
    end
    
    subgraph "External Services"
        AI_PROVIDER[AI Provider]
        EMAIL[Email Service]
        PAYMENT[Payment Gateway]
    end
    
    CLI --> CORE
    API --> CORE
    WEB --> CORE
    
    CORE --> AI
    CORE --> FILE
    CORE --> STORAGE
    
    AI --> AI_PROVIDER
    CORE --> EMAIL
    CORE --> PAYMENT
    
    STORAGE --> JSON
    STORAGE --> LOGS
    CORE --> MODELS
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Core
    participant AI
    participant Storage
    participant Email
    participant Payment
    
    User->>CLI: Upload image
    CLI->>Core: Process image
    Core->>AI: Extract data
    AI-->>Core: Receipt data
    Core->>Storage: Save log
    Core->>Email: Send notification
    Core->>Payment: Process payment
    Core-->>CLI: Processing result
    CLI-->>User: Success/Error
```

## Component Architecture

```mermaid
graph LR
    subgraph "Presentation Layer"
        CLI_CMD[CLI Commands]
        API_ENDPOINTS[API Endpoints]
        WEB_UI[Web UI]
    end
    
    subgraph "Business Logic Layer"
        PROCESSOR[Receipt Processor]
        WORKFLOW[Workflow Engine]
        VALIDATOR[Data Validator]
    end
    
    subgraph "Service Layer"
        AI_SERVICE[AI Vision Service]
        EMAIL_SERVICE[Email Service]
        PAYMENT_SERVICE[Payment Service]
        FILE_SERVICE[File Service]
    end
    
    subgraph "Data Access Layer"
        STORAGE_MANAGER[Storage Manager]
        LOG_MANAGER[Log Manager]
        CONFIG_MANAGER[Config Manager]
    end
    
    subgraph "Infrastructure Layer"
        JSON_STORAGE[JSON Files]
        LOG_FILES[Log Files]
        CONFIG_FILES[Config Files]
    end
    
    CLI_CMD --> PROCESSOR
    API_ENDPOINTS --> PROCESSOR
    WEB_UI --> PROCESSOR
    
    PROCESSOR --> WORKFLOW
    PROCESSOR --> VALIDATOR
    
    WORKFLOW --> AI_SERVICE
    WORKFLOW --> EMAIL_SERVICE
    WORKFLOW --> PAYMENT_SERVICE
    WORKFLOW --> FILE_SERVICE
    
    AI_SERVICE --> STORAGE_MANAGER
    EMAIL_SERVICE --> STORAGE_MANAGER
    PAYMENT_SERVICE --> STORAGE_MANAGER
    FILE_SERVICE --> STORAGE_MANAGER
    
    STORAGE_MANAGER --> JSON_STORAGE
    LOG_MANAGER --> LOG_FILES
    CONFIG_MANAGER --> CONFIG_FILES
```

## Processing Pipeline

```mermaid
flowchart TD
    START([Image Input]) --> VALIDATE{Validate Image}
    VALIDATE -->|Valid| AI[AI Processing]
    VALIDATE -->|Invalid| ERROR[Error Handling]
    
    AI --> EXTRACT[Extract Data]
    EXTRACT --> VALIDATE_DATA{Validate Data}
    VALIDATE_DATA -->|Valid| SAVE[Save to Storage]
    VALIDATE_DATA -->|Invalid| RETRY{Retry?}
    
    RETRY -->|Yes| AI
    RETRY -->|No| ERROR
    
    SAVE --> RENAME[Rename File]
    RENAME --> EMAIL[Send Email]
    EMAIL --> PAYMENT[Process Payment]
    PAYMENT --> LOG[Log Result]
    LOG --> END([Complete])
    
    ERROR --> LOG_ERROR[Log Error]
    LOG_ERROR --> END
```

## Error Handling Architecture

```mermaid
graph TB
    subgraph "Error Detection"
        EXCEPTION[Exception Occurred]
        VALIDATION[Validation Failed]
        TIMEOUT[Timeout Error]
        NETWORK[Network Error]
    end
    
    subgraph "Error Processing"
        CATEGORIZER[Error Categorizer]
        RETRY_MANAGER[Retry Manager]
        RECOVERY[Recovery Manager]
    end
    
    subgraph "Error Response"
        LOG_ERROR[Log Error]
        NOTIFY[Notify User]
        ALERT[System Alert]
        FALLBACK[Fallback Action]
    end
    
    EXCEPTION --> CATEGORIZER
    VALIDATION --> CATEGORIZER
    TIMEOUT --> CATEGORIZER
    NETWORK --> CATEGORIZER
    
    CATEGORIZER --> RETRY_MANAGER
    RETRY_MANAGER --> RECOVERY
    
    RECOVERY --> LOG_ERROR
    RECOVERY --> NOTIFY
    RECOVERY --> ALERT
    RECOVERY --> FALLBACK
```

## Storage Architecture

```mermaid
graph TB
    subgraph "Data Models"
        RECEIPT[Receipt Data]
        LOG[Processing Log]
        PAYMENT[Payment Data]
        ERROR[Error Log]
    end
    
    subgraph "Storage Layer"
        JSON_MANAGER[JSON Storage Manager]
        ATOMIC[Atomic Operations]
        BACKUP[Backup System]
    end
    
    subgraph "File System"
        JSON_FILES[JSON Files]
        LOG_FILES[Log Files]
        BACKUP_FILES[Backup Files]
    end
    
    RECEIPT --> JSON_MANAGER
    LOG --> JSON_MANAGER
    PAYMENT --> JSON_MANAGER
    ERROR --> JSON_MANAGER
    
    JSON_MANAGER --> ATOMIC
    ATOMIC --> BACKUP
    
    ATOMIC --> JSON_FILES
    BACKUP --> BACKUP_FILES
    JSON_MANAGER --> LOG_FILES
```

## Monitoring Architecture

```mermaid
graph TB
    subgraph "Application"
        PROCESSOR[Receipt Processor]
        DAEMON[Daemon Service]
        CLI[CLI Interface]
    end
    
    subgraph "Monitoring System"
        HEALTH[Health Checker]
        METRICS[Metrics Collector]
        ALERTS[Alert Manager]
    end
    
    subgraph "System Resources"
        CPU[CPU Usage]
        MEMORY[Memory Usage]
        DISK[Disk Usage]
        NETWORK[Network Usage]
    end
    
    subgraph "External Monitoring"
        LOG_AGGREGATOR[Log Aggregator]
        METRICS_STORE[Metrics Store]
        NOTIFICATION[Notification Service]
    end
    
    PROCESSOR --> HEALTH
    DAEMON --> HEALTH
    CLI --> HEALTH
    
    HEALTH --> METRICS
    METRICS --> ALERTS
    
    METRICS --> CPU
    METRICS --> MEMORY
    METRICS --> DISK
    METRICS --> NETWORK
    
    ALERTS --> LOG_AGGREGATOR
    ALERTS --> METRICS_STORE
    ALERTS --> NOTIFICATION
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_LOCAL[Local Development]
        DEV_TEST[Test Environment]
        DEV_STAGING[Staging Environment]
    end
    
    subgraph "Production Environment"
        PROD_WEB[Web Server]
        PROD_API[API Server]
        PROD_WORKER[Worker Process]
    end
    
    subgraph "Infrastructure"
        LOAD_BALANCER[Load Balancer]
        DATABASE[Database]
        STORAGE[File Storage]
        MONITORING[Monitoring]
    end
    
    DEV_LOCAL --> DEV_TEST
    DEV_TEST --> DEV_STAGING
    DEV_STAGING --> PROD_WEB
    
    PROD_WEB --> LOAD_BALANCER
    PROD_API --> LOAD_BALANCER
    PROD_WORKER --> LOAD_BALANCER
    
    LOAD_BALANCER --> DATABASE
    LOAD_BALANCER --> STORAGE
    LOAD_BALANCER --> MONITORING
```

## Security Architecture

```mermaid
graph TB
    subgraph "Authentication"
        AUTH[Authentication Service]
        TOKEN[Token Manager]
        SESSION[Session Manager]
    end
    
    subgraph "Authorization"
        RBAC[Role-Based Access Control]
        PERMISSIONS[Permission Manager]
        POLICIES[Security Policies]
    end
    
    subgraph "Data Protection"
        ENCRYPTION[Data Encryption]
        HASHING[Password Hashing]
        SECURE_STORAGE[Secure Storage]
    end
    
    subgraph "Network Security"
        HTTPS[HTTPS/TLS]
        FIREWALL[Firewall]
        VPN[VPN Access]
    end
    
    AUTH --> TOKEN
    TOKEN --> SESSION
    
    SESSION --> RBAC
    RBAC --> PERMISSIONS
    PERMISSIONS --> POLICIES
    
    POLICIES --> ENCRYPTION
    ENCRYPTION --> HASHING
    HASHING --> SECURE_STORAGE
    
    SECURE_STORAGE --> HTTPS
    HTTPS --> FIREWALL
    FIREWALL --> VPN
```

## Integration Architecture

```mermaid
graph TB
    subgraph "Receipt Processor"
        CORE[Core System]
        API[Internal API]
    end
    
    subgraph "External Integrations"
        AI_PROVIDER[AI Provider]
        EMAIL_SERVICE[Email Service]
        PAYMENT_GATEWAY[Payment Gateway]
        CLOUD_STORAGE[Cloud Storage]
    end
    
    subgraph "Third-Party Services"
        OPENAI[OpenAI API]
        ANTHROPIC[Anthropic API]
        GMAIL[Gmail API]
        STRIPE[Stripe API]
        AWS_S3[AWS S3]
    end
    
    CORE --> API
    API --> AI_PROVIDER
    API --> EMAIL_SERVICE
    API --> PAYMENT_GATEWAY
    API --> CLOUD_STORAGE
    
    AI_PROVIDER --> OPENAI
    AI_PROVIDER --> ANTHROPIC
    EMAIL_SERVICE --> GMAIL
    PAYMENT_GATEWAY --> STRIPE
    CLOUD_STORAGE --> AWS_S3
```

## Performance Architecture

```mermaid
graph TB
    subgraph "Load Balancing"
        LB[Load Balancer]
        HEALTH_CHECK[Health Check]
    end
    
    subgraph "Caching Layer"
        REDIS[Redis Cache]
        MEMORY_CACHE[Memory Cache]
    end
    
    subgraph "Processing Pool"
        WORKER_1[Worker 1]
        WORKER_2[Worker 2]
        WORKER_N[Worker N]
    end
    
    subgraph "Database Layer"
        PRIMARY[Primary DB]
        REPLICA[Read Replica]
        BACKUP[Backup DB]
    end
    
    LB --> HEALTH_CHECK
    HEALTH_CHECK --> WORKER_1
    HEALTH_CHECK --> WORKER_2
    HEALTH_CHECK --> WORKER_N
    
    WORKER_1 --> REDIS
    WORKER_2 --> REDIS
    WORKER_N --> REDIS
    
    REDIS --> MEMORY_CACHE
    MEMORY_CACHE --> PRIMARY
    PRIMARY --> REPLICA
    PRIMARY --> BACKUP
```

These diagrams provide a comprehensive view of the Receipt Processor system architecture, showing how different components interact and how data flows through the system.
