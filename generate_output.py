#!/usr/bin/env python3

import os
import sys
import yaml
import subprocess
import re
from collections import defaultdict
import argparse

def parse_process_allocation(output_text):
    """
    Parse the process allocation information from the main.py output.
    Returns a dictionary mapping servers to their allocated processes.
    """
    # Dictionary to store server -> processes mapping
    server_to_processes = defaultdict(list)
    
    # Regular expressions to extract information
    process_pattern = r"📦 Process: (.*?) \(Policy: (.*?)\)"
    location_pattern = r"  📍 Location: (.*)"
    replica_pattern = r"    🔄 Replica (\d+) → Server: (.*)"
    
    current_process = None
    current_location = None
    
    # Parse the output line by line
    for line in output_text.split('\n'):
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
            process_info = {
                "name": current_process,
                "replica": int(replica_num),
                "location": current_location
            }
            server_to_processes[server_name].append(process_info)
    
    return server_to_processes

def generate_yaml_output(server_to_processes):
    """
    Generate a structured YAML representation of the process allocation.
    """
    # Create output structure
    output = {
        "servers": []
    }
    
    for server_name, processes in server_to_processes.items():
        server_info = {
            "name": server_name,
            "processes": processes
        }
        output["servers"].append(server_info)
    
    return output

def run_main_script(preset_name):
    """
    Run the main.py script with the specified preset and capture its output.
    """
    preset_path = f"./presets/{preset_name}"
    
    # Run the main.py script and capture its output
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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate YAML output for process allocation.')
    parser.add_argument('preset', help='Preset name to use (e.g., tiny-x)')
    parser.add_argument('--output-dir', default='.', help='Directory to write output files')
    args = parser.parse_args()
    
    preset_name = args.preset
    output_dir = args.output_dir
    
    print(f"🚀 Running allocation for preset: {preset_name}")
    
    # Run the main script and capture its output
    output_text = run_main_script(preset_name)
    
    # Check if solution was found
    if "❌ No feasible solution found" in output_text:
        print("❌ No feasible solution was found. Cannot generate output YAML.")
        sys.exit(1)
    
    # Parse the output to extract process allocation
    server_to_processes = parse_process_allocation(output_text)
    
    if not server_to_processes:
        print("⚠️ Warning: Could not parse any process allocation information.")
        sys.exit(1)
    
    # Generate YAML output
    output_data = generate_yaml_output(server_to_processes)
    
    # Write YAML to file
    output_filename = f"output-processes-dispatch-{preset_name}.yml"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ YAML output written to {output_path}")
    print(f"📊 Allocation summary:")
    print(f"   - Servers used: {len(server_to_processes)}")
    print(f"   - Total processes allocated: {sum(len(processes) for processes in server_to_processes.values())}")

if __name__ == "__main__":
    main()
