#!/usr/bin/env python3

import os
import sys
import yaml
import argparse
import subprocess
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import re

def parse_process_allocation(output_text=None, yaml_file=None):
    """
    Parse process allocation data either from main.py output text or from a YAML file.
    Returns server resource data and process allocation information.
    """
    if yaml_file and os.path.exists(yaml_file):
        # Read from YAML file
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # TODO: Process the YAML data to extract server resources
        # This is a placeholder and would need to be updated based on the exact YAML structure
        return {}, data
    
    if not output_text:
        raise ValueError("Either output_text or yaml_file must be provided")
    
    # Dictionary to store server -> resources mapping
    server_resources = {}
    process_allocation = defaultdict(list)
    
    # Regular expressions to extract information
    process_pattern = r"📦 Process: (.*?) \(Policy: (.*?)\)"
    location_pattern = r"  📍 Location: (.*)"
    replica_pattern = r"    🔄 Replica (\d+) → Server: (.*)"
    server_pattern = r"🏢 Server: (.*?) \((.*?)\)"
    ram_pattern = r"  💾 RAM: (.*?)/(.*?) GB \((.*?)%\)"
    cpu_pattern = r"  ⚙️  CPU: (.*?)/(.*?) cores \((.*?)%\)"
    disk_pattern = r"  💿 Disk: (.*?)/(.*?) GB \((.*?)%\)"
    bandwidth_pattern = r"  🌐 Bandwidth: (.*?)/(.*?) GB/s \((.*?)%\)"
    processes_pattern = r"  🧩 Processes: (\d+)"
    energy_pattern = r"  ⚡ Daily Energy Consumption: (.*?) kWh"
    cost_pattern = r"  💰 Daily Energy Cost: \$(.*)"
    green_pattern = r"  🍃 Green Energy"
    
    current_process = None
    current_location = None
    current_server = None
    
    # Parse the output line by line
    lines = output_text.split('\n')
    for i, line in enumerate(lines):
        # Process information
        process_match = re.search(process_pattern, line)
        if process_match:
            current_process = process_match.group(1)
            continue
            
        location_match = re.search(location_pattern, line)
        if location_match and current_process:
            current_location = location_match.group(1)
            continue
            
        replica_match = re.search(replica_pattern, line)
        if replica_match and current_process and current_location:
            replica_num = replica_match.group(1)
            server_name = replica_match.group(2)
            
            # Add this process to the server's list
            process_allocation[server_name].append({
                "name": current_process,
                "replica": int(replica_num),
                "location": current_location
            })
            continue
        
        # Server information
        server_match = re.search(server_pattern, line)
        if server_match:
            current_server = server_match.group(1)
            server_location = server_match.group(2)
            server_resources[current_server] = {
                "name": current_server,
                "location": server_location,
                "green": False  # Default
            }
            continue
            
        if current_server:
            # RAM information
            ram_match = re.search(ram_pattern, line)
            if ram_match:
                server_resources[current_server]["ram_used"] = float(ram_match.group(1))
                server_resources[current_server]["ram_total"] = float(ram_match.group(2))
                server_resources[current_server]["ram_percent"] = float(ram_match.group(3))
                continue
                
            # CPU information
            cpu_match = re.search(cpu_pattern, line)
            if cpu_match:
                server_resources[current_server]["cpu_used"] = float(cpu_match.group(1))
                server_resources[current_server]["cpu_total"] = float(cpu_match.group(2))
                server_resources[current_server]["cpu_percent"] = float(cpu_match.group(3))
                continue
                
            # Disk information
            disk_match = re.search(disk_pattern, line)
            if disk_match:
                server_resources[current_server]["disk_used"] = float(disk_match.group(1))
                server_resources[current_server]["disk_total"] = float(disk_match.group(2))
                server_resources[current_server]["disk_percent"] = float(disk_match.group(3))
                continue
                
            # Bandwidth information
            bandwidth_match = re.search(bandwidth_pattern, line)
            if bandwidth_match:
                server_resources[current_server]["bandwidth_used"] = float(bandwidth_match.group(1))
                server_resources[current_server]["bandwidth_total"] = float(bandwidth_match.group(2))
                server_resources[current_server]["bandwidth_percent"] = float(bandwidth_match.group(3))
                continue
                
            # Process count
            processes_match = re.search(processes_pattern, line)
            if processes_match:
                server_resources[current_server]["process_count"] = int(processes_match.group(1))
                continue
                
            # Energy consumption
            energy_match = re.search(energy_pattern, line)
            if energy_match:
                server_resources[current_server]["energy"] = float(energy_match.group(1))
                continue
                
            # Cost
            cost_match = re.search(cost_pattern, line)
            if cost_match:
                server_resources[current_server]["cost"] = float(cost_match.group(1))
                continue
                
            # Green energy
            if green_pattern in line:
                server_resources[current_server]["green"] = True
                
    return server_resources, process_allocation

def run_main_script(preset_name):
    """Run the main.py script with the specified preset and capture its output."""
    preset_path = f"./presets/{preset_name}"
    
    try:
        result = subprocess.run(
            [sys.executable, 'main.py', preset_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running main.py: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def load_constraints(preset_name):
    """Load constraints from the constraints YAML file"""
    constraints_file = f"./presets/{preset_name}/constraints.yml"
    if os.path.exists(constraints_file):
        with open(constraints_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('constraints', {})
    return {}

def parse_percentage(value, default=100):
    """Parse percentage values from constraints"""
    if not value:
        return default / 100.0
    
    if isinstance(value, str) and '%' in value:
        return float(value.strip('%')) / 100.0
    
    try:
        return float(value) / 100.0
    except (ValueError, TypeError):
        return default / 100.0

def generate_resource_usage_chart(server_resources, resource_type, output_dir, preset_name, constraints=None):
    """Generate a chart showing resource usage across servers with constraint lines."""
    plt.figure(figsize=(12, 8))
    
    # Extract data
    servers = list(server_resources.keys())
    
    # Get usage and total values for the resource type
    if resource_type == 'processes':
        usage_values = [server_resources[s].get('process_count', 0) for s in servers]
        # For processes, we'll just show the count rather than percentage
        plt.bar(servers, usage_values)
        plt.ylabel('Number of Processes')
        plt.title(f'Process Count per Server')
        
        # Add max processes constraint line if available
        if constraints and 'max-processes-per-server' in constraints:
            max_processes = int(constraints['max-processes-per-server'])
            plt.axhline(y=max_processes, color='r', linestyle='-', linewidth=2, 
                      label=f'Max Processes: {max_processes}')
            plt.legend()
            
    else:
        usage_key = f"{resource_type}_used"
        total_key = f"{resource_type}_total"
        percent_key = f"{resource_type}_percent"
        
        usage_values = [server_resources[s].get(usage_key, 0) for s in servers]
        total_values = [server_resources[s].get(total_key, 0) for s in servers]
        
        # Create a stacked bar chart showing used and available resources
        unused_values = [total - used for total, used in zip(total_values, usage_values)]
        
        # Create the plot
        bar_width = 0.6
        
        # First bar: Used resources
        plt.bar(servers, usage_values, bar_width, label='Used', color='#1f77b4')
        # Second bar: Unused resources, stacked on top of used
        plt.bar(servers, unused_values, bar_width, bottom=usage_values, color='#d3d3d3', label='Available')
        
        # Labels and title adjustments based on resource type
        constraint_key = None
        if resource_type == 'ram':
            plt.ylabel('RAM (GB)')
            plt.title(f'RAM Usage per Server')
            constraint_key = 'max-ram-usage-per-server'
        elif resource_type == 'cpu':
            plt.ylabel('CPU Cores')
            plt.title(f'CPU Usage per Server')
            constraint_key = 'max-cpu-usage-per-server'
        elif resource_type == 'disk':
            plt.ylabel('Disk Space (GB)')
            plt.title(f'Disk Usage per Server')
            constraint_key = 'max-disk-usage-per-server'
        elif resource_type == 'bandwidth':
            plt.ylabel('Bandwidth (GB/s)')
            plt.title(f'Bandwidth Usage per Server')
            constraint_key = 'max-network-bandwidth-per-server'
            
        # Add constraint line if available
        if constraints and constraint_key in constraints:
            # Parse the constraint percentage
            max_percent = parse_percentage(constraints[constraint_key], 100)
            
            # Add lines representing max allowed values for each server
            for i, (server, total) in enumerate(zip(servers, total_values)):
                max_value = total * max_percent
                plt.plot([i-bar_width/2, i+bar_width/2], [max_value, max_value], 
                         'r-', linewidth=2)
            
            # Add a line in the legend for the constraint
            from matplotlib.lines import Line2D
            percent_display = int(max_percent * 100)
            legend_elements = plt.gca().get_legend_handles_labels()[0] + [
                Line2D([0], [0], color='r', lw=2, label=f'Max {resource_type.upper()}: {percent_display}%')
            ]
            plt.legend(handles=legend_elements)
        else:
            plt.legend()
    
    # Add percentage labels on top of the bars
    if resource_type != 'processes':
        for i, server in enumerate(servers):
            percent = server_resources[server].get(f"{resource_type}_percent", 0)
            plt.text(i, usage_values[i] / 2, f"{percent:.1f}%", 
                    ha='center', va='center', color='white', fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the figure
    output_path = os.path.join(output_dir, f"{resource_type}_usage_{preset_name}.png")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_energy_cost_chart(server_resources, output_dir, preset_name):
    """Generate a chart showing energy consumption and cost across servers."""
    plt.figure(figsize=(12, 8))
    
    servers = list(server_resources.keys())
    energy_values = [server_resources[s].get('energy', 0) for s in servers]
    cost_values = [server_resources[s].get('cost', 0) for s in servers]
    
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # First axis for energy consumption (bars)
    colors = ['#1f77b4' if not server_resources[s].get('green', False) else '#2ca02c' for s in servers]
    bars = ax1.bar(servers, energy_values, alpha=0.7, color=colors)
    ax1.set_ylabel('Energy Consumption (kWh)')
    ax1.set_title('Energy Consumption and Cost per Server')
    
    # Add a second y-axis for cost
    ax2 = ax1.twinx()
    ax2.plot(servers, cost_values, 'ro-', marker='D', linewidth=2)
    ax2.set_ylabel('Cost ($)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    # Add a legend for green vs. non-green energy
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ca02c', label='Green Energy'),
        Patch(facecolor='#1f77b4', label='Standard Energy')
    ]
    ax1.legend(handles=legend_elements, loc='upper left')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the figure
    output_path = os.path.join(output_dir, f"energy_cost_{preset_name}.png")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_process_distribution_chart(process_allocation, output_dir, preset_name):
    """Generate a chart showing process distribution across servers."""
    plt.figure(figsize=(14, 10))
    
    # Get unique process names
    all_processes = set()
    for server, processes in process_allocation.items():
        for process in processes:
            all_processes.add(process['name'])
    
    all_processes = sorted(list(all_processes))
    servers = sorted(list(process_allocation.keys()))
    
    # Create a matrix of process counts per server
    data = np.zeros((len(all_processes), len(servers)))
    
    for s_idx, server in enumerate(servers):
        for process in process_allocation[server]:
            p_idx = all_processes.index(process['name'])
            data[p_idx, s_idx] += 1
    
    # Create stacked bar chart
    bar_bottom = np.zeros(len(servers))
    
    # Choose a colorful palette
    colors = plt.cm.tab20(np.linspace(0, 1, len(all_processes)))
    
    for p_idx, process in enumerate(all_processes):
        plt.bar(servers, data[p_idx], bottom=bar_bottom, label=process, color=colors[p_idx % len(colors)])
        bar_bottom += data[p_idx]
    
    plt.xlabel('Servers')
    plt.ylabel('Number of Processes')
    plt.title('Process Distribution Across Servers')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Processes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Save the figure
    output_path = os.path.join(output_dir, f"process_distribution_{preset_name}.png")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_overall_resource_chart(server_resources, output_dir, preset_name):
    """Generate a chart showing overall resource utilization."""
    # Calculate overall utilization percentages
    total_ram_used = sum(s.get('ram_used', 0) for s in server_resources.values())
    total_ram_capacity = sum(s.get('ram_total', 0) for s in server_resources.values())
    
    total_cpu_used = sum(s.get('cpu_used', 0) for s in server_resources.values())
    total_cpu_capacity = sum(s.get('cpu_total', 0) for s in server_resources.values())
    
    total_disk_used = sum(s.get('disk_used', 0) for s in server_resources.values())
    total_disk_capacity = sum(s.get('disk_total', 0) for s in server_resources.values())
    
    total_bandwidth_used = sum(s.get('bandwidth_used', 0) for s in server_resources.values())
    total_bandwidth_capacity = sum(s.get('bandwidth_total', 0) for s in server_resources.values())
    
    # Calculate percentages
    ram_percent = (total_ram_used / total_ram_capacity * 100) if total_ram_capacity > 0 else 0
    cpu_percent = (total_cpu_used / total_cpu_capacity * 100) if total_cpu_capacity > 0 else 0
    disk_percent = (total_disk_used / total_disk_capacity * 100) if total_disk_capacity > 0 else 0
    bandwidth_percent = (total_bandwidth_used / total_bandwidth_capacity * 100) if total_bandwidth_capacity > 0 else 0
    
    # Create figure
    plt.figure(figsize=(10, 8))
    
    # Data for the chart
    resources = ['RAM', 'CPU', 'Disk', 'Bandwidth']
    used_values = [ram_percent, cpu_percent, disk_percent, bandwidth_percent]
    unused_values = [100 - p for p in used_values]
    
    # Create horizontal bar chart
    y_pos = np.arange(len(resources))
    
    # Plot used resources
    plt.barh(y_pos, used_values, color='#1f77b4', label='Used (%)')
    # Plot unused resources
    plt.barh(y_pos, unused_values, left=used_values, color='#d3d3d3', label='Available (%)')
    
    # Add percentage labels
    for i, percent in enumerate(used_values):
        plt.text(percent / 2, i, f"{percent:.1f}%", 
                ha='center', va='center', color='white', fontweight='bold')
    
    plt.yticks(y_pos, resources)
    plt.xlabel('Percentage (%)')
    plt.title('Overall Resource Utilization')
    plt.xlim(0, 100)
    plt.legend()
    
    # Save the figure
    output_path = os.path.join(output_dir, f"overall_resources_{preset_name}.png")
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_summary_dashboard(chart_files, output_dir, preset_name):
    """Generate a combined dashboard with all charts."""
    from matplotlib.gridspec import GridSpec
    
    # Create a larger figure to accommodate more charts
    fig = plt.figure(figsize=(20, 30))  # Increase height for more charts
    gs = GridSpec(4, 2, figure=fig)  # Use 4 rows instead of 3
    
    # First row: CPU and RAM
    ax1 = fig.add_subplot(gs[0, 0])
    cpu_img = plt.imread(chart_files['cpu'])
    ax1.imshow(cpu_img)
    ax1.axis('off')
    ax1.set_title('CPU Usage', fontsize=16)
    
    ax2 = fig.add_subplot(gs[0, 1])
    ram_img = plt.imread(chart_files['ram'])
    ax2.imshow(ram_img)
    ax2.axis('off')
    ax2.set_title('RAM Usage', fontsize=16)
    
    # Second row: Energy/Cost and Process Distribution
    ax3 = fig.add_subplot(gs[1, 0])
    energy_img = plt.imread(chart_files['energy_cost'])
    ax3.imshow(energy_img)
    ax3.axis('off')
    ax3.set_title('Energy and Cost', fontsize=16)
    
    ax4 = fig.add_subplot(gs[1, 1])
    process_img = plt.imread(chart_files['process_distribution'])
    ax4.imshow(process_img)
    ax4.axis('off')
    ax4.set_title('Process Distribution', fontsize=16)
    
    # Third row: Overall Resources and Disk Usage
    ax5 = fig.add_subplot(gs[2, 0])
    overall_img = plt.imread(chart_files['overall_resources'])
    ax5.imshow(overall_img)
    ax5.axis('off')
    ax5.set_title('Overall Resource Usage', fontsize=16)
    
    ax6 = fig.add_subplot(gs[2, 1])
    disk_img = plt.imread(chart_files['disk'])
    ax6.imshow(disk_img)
    ax6.axis('off')
    ax6.set_title('Disk Usage', fontsize=16)
    
    # Fourth row: Bandwidth and Processes (or any other remaining chart)
    ax7 = fig.add_subplot(gs[3, 0])
    bandwidth_img = plt.imread(chart_files['bandwidth'])
    ax7.imshow(bandwidth_img)
    ax7.axis('off')
    ax7.set_title('Bandwidth Usage', fontsize=16)
    
    ax8 = fig.add_subplot(gs[3, 1])
    processes_img = plt.imread(chart_files['processes'])
    ax8.imshow(processes_img)
    ax8.axis('off')
    ax8.set_title('Process Count', fontsize=16)
    
    plt.tight_layout()
    
    # Save the dashboard
    output_path = os.path.join(output_dir, f"dashboard_{preset_name}.png")
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    return output_path

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate charts for process allocation.')
    parser.add_argument('preset', help='Preset name to use (e.g., tiny-x)')
    parser.add_argument('--output-dir', default='./charts', help='Directory to write chart files')
    parser.add_argument('--yaml-file', help='Path to YAML output file (if already generated)')
    args = parser.parse_args()
    
    preset_name = args.preset
    output_dir = args.output_dir
    yaml_file = args.yaml_file
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🚀 Generating charts for preset: {preset_name}")
    
    # Load constraints for adding to charts
    constraints = load_constraints(preset_name)
    print(f"📏 Loaded constraints for maximum resource usage visualization")
    
    # Get allocation data
    if yaml_file:
        print(f"Reading allocation data from {yaml_file}")
        server_resources, process_allocation = parse_process_allocation(yaml_file=yaml_file)
    else:
        print("Running allocation and parsing output...")
        output_text = run_main_script(preset_name)
        server_resources, process_allocation = parse_process_allocation(output_text=output_text)
    
    if not server_resources:
        print("⚠️ Warning: No server resource data found.")
    
    if not process_allocation:
        print("⚠️ Warning: No process allocation data found.")
    
    # Generate individual charts with constraint lines
    chart_files = {}
    
    print("Generating resource usage charts with constraint lines...")
    chart_files['ram'] = generate_resource_usage_chart(
        server_resources, 'ram', output_dir, preset_name, constraints)
    chart_files['cpu'] = generate_resource_usage_chart(
        server_resources, 'cpu', output_dir, preset_name, constraints)
    chart_files['disk'] = generate_resource_usage_chart(
        server_resources, 'disk', output_dir, preset_name, constraints)
    chart_files['bandwidth'] = generate_resource_usage_chart(
        server_resources, 'bandwidth', output_dir, preset_name, constraints)
    chart_files['processes'] = generate_resource_usage_chart(
        server_resources, 'processes', output_dir, preset_name, constraints)
    
    print("Generating energy and cost chart...")
    chart_files['energy_cost'] = generate_energy_cost_chart(
        server_resources, output_dir, preset_name)
    
    print("Generating process distribution chart...")
    chart_files['process_distribution'] = generate_process_distribution_chart(
        process_allocation, output_dir, preset_name)
    
    print("Generating overall resource usage chart...")
    chart_files['overall_resources'] = generate_overall_resource_chart(
        server_resources, output_dir, preset_name)
    
    print("Generating summary dashboard with all charts...")
    dashboard_path = generate_summary_dashboard(chart_files, output_dir, preset_name)
    
    print(f"✅ All charts generated successfully!")
    print(f"📊 Individual charts saved to {output_dir}")
    print(f"🖼️ Summary dashboard saved to {dashboard_path}")

if __name__ == "__main__":
    main()
