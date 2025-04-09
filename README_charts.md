# Process Allocation Charts Generator

This tool generates visualizations of server resource usage and process allocations based on the solution from the main.py program.

## Requirements

The chart generator requires the following Python packages:
- matplotlib
- numpy
- pyyaml

You can install these with pip:
```bash
pip install matplotlib numpy pyyaml
```

## Usage

Run the script with the preset name as an argument:

```bash
python generate_charts.py tiny-x
```

This will:
1. Run the main.py script using the specified preset (or use a pre-generated YAML file)
2. Parse the process allocation results
3. Generate various charts showing resource utilization
4. Create a comprehensive dashboard image combining all charts
5. Save all chart files to the output directory

### Command Line Options

- `preset`: (Required) The name of the preset folder to use (e.g., tiny-x)
- `--output-dir`: (Optional) Directory where to save the chart files. Defaults to "./charts"
- `--yaml-file`: (Optional) Path to a pre-generated YAML output file instead of running main.py

Example:
```bash
python generate_charts.py tiny-x --output-dir ./my-charts --yaml-file output-processes-dispatch-tiny-x.yml
```

## Generated Charts

The script generates the following charts:

1. **Resource Usage Charts**:
   - RAM usage per server
   - CPU usage per server
   - Disk usage per server
   - Bandwidth usage per server
   - Process count per server

2. **Energy and Cost Charts**:
   - Combined chart showing energy consumption and costs
   - Highlights green energy servers

3. **Process Distribution**:
   - Shows how processes are distributed across servers
   - Color-coded by process type

4. **Overall Resource Utilization**:
   - Summary of total resource utilization across all servers

5. **Summary Dashboard**:
   - A combined view with all major charts on one image
   - Provides a complete overview of the allocation

## Example Output

The individual charts and dashboard will be saved in the specified output directory with filenames following the pattern:
- `cpu_usage_tiny-x.png`
- `ram_usage_tiny-x.png`
- `disk_usage_tiny-x.png`
- `energy_cost_tiny-x.png`
- `process_distribution_tiny-x.png`
- `overall_resources_tiny-x.png`
- `dashboard_tiny-x.png`
