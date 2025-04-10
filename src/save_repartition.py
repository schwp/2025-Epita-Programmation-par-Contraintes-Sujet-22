#!/usr/bin/env python3

import os
import yaml
from collections import defaultdict

def generate_yaml_output(result: dict):
    """
    Generate a structured YAML representation of the process allocation.
    """
    # Create output structure
    output = {
        "servers": []
    }

    server_to_processes = defaultdict(list)
    processes = result['processes']

    for process in processes:
        for replica in process['replicas']:
            server_name = replica['server']
            process_info = {
                'name': process['name'],
                'replica': replica['replica'],
                'location': process['location']
            }

            server_to_processes[server_name].append(process_info)

    for server_name, processes in server_to_processes.items():
        server_info = {
            "name": server_name,
            "processes": processes
        }
        output["servers"].append(server_info)
    
    return output, server_to_processes

def save_processes_repartition(vm_scheduling_result: dict, output_dir: str, preset_name: str):
    print(f"🚀 Running allocation for preset: {preset_name}")
    
    if vm_scheduling_result is None:
        print("❌ No feasible solution was found. Cannot generate output YAML.")
        return
    
    output_data, server_to_processes = generate_yaml_output(vm_scheduling_result)
    
    # # Write YAML to file
    output_filename = f"processes-repartition-{preset_name}.yml"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ YAML output written to {output_path}")
    print(f"📊 Allocation summary:")
    print(f"   - Servers used: {len(server_to_processes)}")
    print(f"   - Total processes allocated: {sum(len(processes) for processes in server_to_processes.values())}")

