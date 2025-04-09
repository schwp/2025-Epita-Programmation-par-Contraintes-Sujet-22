# Load Balancing Strategies

This document describes the available load balancing strategies that can be used in the constraints configuration.

## Configuration

In your `constraints.yml` file, set the `load-balancing-strategy` to one of the following values:

```yaml
constraints:
  load-balancing-strategy: bin-packing  # Choose your preferred strategy
```

## Available Strategies

### round-robin

Distributes processes as evenly as possible across all available servers. This strategy minimizes the maximum number of processes on any server.

**Best for**: High availability and evenly distributed workload.

### bin-packing

Consolidates processes onto as few servers as possible. This strategy tries to maximize the number of empty servers.

**Best for**: Energy efficiency, allowing unused servers to be shut down.

### weighted-capacity

Distributes processes proportionally to each server's capacity. Servers with more RAM and CPU get assigned proportionally more processes.

**Best for**: Heterogeneous server environments with varying capacities.

## Choosing the Right Strategy

- **For cost efficiency**: Use `bin-packing`
- **For mixed server types**: Use `weighted-capacity`
- **For general purpose**: Use `round-robin`
