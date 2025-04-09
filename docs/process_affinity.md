# Process Affinity and Non-Affinity

This document explains how to use process affinity and non-affinity constraints in your deployment configurations.

## Overview

Process affinity allows you to:
- Force certain processes to be deployed on the same server (affinity)
- Ensure processes are deployed on different servers (non-affinity)

## Configuration

In your process definition, add `affinity` and `non-affinity` lists specifying which processes should be co-located or separated:

```yaml
processes:
  - name: "web-server"
    ram: 2
    cpu: 1
    disk: 5
    bandwidth: 1
    # Other process attributes...
    
    # Process affinity - these processes MUST be on the same server
    affinity:
      - "cache-service"
      - "auth-handler"
    
    # Process non-affinity - these processes MUST be on different servers
    non-affinity:
      - "database"
      - "heavy-batch-job"
```

## Usage Examples

### Example 1: Co-locating Related Services

For performance reasons, you might want to co-locate services that frequently communicate with each other:

```yaml
- name: "api-service"
  affinity:
    - "redis-cache"  # Keep API and its cache together for low latency
```

### Example 2: Separating Competing Resources

For stability reasons, you might want to keep resource-intensive processes apart:

```yaml
- name: "data-analyzer"
  non-affinity:
    - "media-encoder"  # Keep CPU-intensive processes on separate servers
```

### Example 3: Redundancy

For high-availability services, you might want to ensure replicas are on different servers:

```yaml
- name: "primary-database"
  non-affinity:
    - "secondary-database"  # Keep database replicas on separate servers
```

## Technical Details

The process affinity feature:
1. Creates constraints in the constraint solver to enforce co-location or separation
2. Works with process replicas (each replica follows the affinity rules)
3. Validates that referenced processes exist (with warnings for non-existent processes)
