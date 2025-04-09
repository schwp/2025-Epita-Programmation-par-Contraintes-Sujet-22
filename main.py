from ortools.sat.python import cp_model
import yaml
import math
import sys
import os

def load_yaml(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot find configuration file: {file_path}")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def calculate_energy_consumption(server, ram_used, cpu_used):
    """Calculate energy consumption based on server formula if available"""
    return (cpu_used * 24 + ram_used * 5) / 1000
    
def safe_percentage(value, default=100):
    """Safely parse percentage strings to integers"""
    if value is None:
        return default
    
    try:
        if isinstance(value, str) and '%' in value:
            return int(value.strip('%'))
        return int(value)
    except (ValueError, TypeError):
        print(f"Warning: Could not parse percentage value '{value}', using default: {default}%")
        return default

# Helper function for absolute value and other common constraints
def AddAbsoluteValueConstraint(model, variable, abs_variable):
    """Adds constraint that abs_variable == |variable|"""
    model.Add(abs_variable >= variable)
    model.Add(abs_variable >= -variable)
    # For optimization purposes, also push it to be as small as possible
    model.Add(abs_variable <= max(abs(model.Max(variable)), abs(model.Min(variable))))

def main():
    try:
        # 1. Load configuration files
        try:
            # Allow command-line arguments to specify preset directory
            preset_dir = sys.argv[1] if len(sys.argv) > 1 else './presets/tiny-x'
            
            print(f"Loading configuration from {preset_dir}")
            servers_file = f'{preset_dir}/servers.yml'
            processes_file = f'{preset_dir}/processes.yml'
            constraints_file = f'{preset_dir}/constraints.yml'
            
            servers_config = load_yaml(servers_file)
            processes_config = load_yaml(processes_file)
            constraints_config = load_yaml(constraints_file)
        except Exception as e:
            print(f"Error loading configuration files: {e}")
            return

        servers = servers_config.get('servers', [])
        processes = processes_config.get('processes', [])
        constraints = constraints_config.get('constraints', {})

        if not servers:
            print("No servers defined in configuration files.")
            return
        if not processes:
            print("No processes defined in configuration files.")
            return

        # Validate required fields
        for i, server in enumerate(servers):
            if 'ram' not in server or 'cpu' not in server or 'disk' not in server or 'bandwidth' not in server:
                print(f"Warning: Server at index {i} is missing required fields (ram, cpu, disk, or bandwidth)")
                
        for i, process in enumerate(processes):
            if 'ram' not in process or 'disk' not in process or 'bandwidth' not in process:
                print(f"Warning: Process at index {i} is missing required fields (ram, disk, or bandwidth)")

        # The rest of the code remains the same

        # 2. Create the CP-SAT model
        model = cp_model.CpModel()

        # Define scaling factors for floating-point to integer conversion
        SCALE = 1000  # Use a large scaling factor to maintain precision

        # 3. Define variables for process-to-server assignments
        # assignment[p][r][s] = 1 if replica r of process p is assigned to server s
        assignment = {}
        
        for p_idx, process in enumerate(processes):
            assignment[p_idx] = {}
            
            # Determine actual number of replicas based on location policy
            location_policy = process.get('location-policy')
            allowed_locations = process.get('location', [])
            base_replicas = process.get('replicas', 1)
            
            # For redundant policy, we need replicas * locations
            total_replicas = base_replicas
            if location_policy == 'redundant' and allowed_locations:
                total_replicas = base_replicas * len(allowed_locations)
                print(f"Process {process['name']} uses redundant policy: {base_replicas} replicas in each of {len(allowed_locations)} locations = {total_replicas} total replicas")
            
            for r in range(total_replicas):
                assignment[p_idx][r] = {}
                
                for s_idx, server in enumerate(servers):
                    assignment[p_idx][r][s_idx] = model.NewBoolVar(f'proc_{p_idx}_replica_{r}_server_{s_idx}')

        # 4. Add constraints
        
        # 4.1 Each process replica must be assigned to exactly one server
        for p_idx, process in enumerate(processes):
            location_policy = process.get('location-policy')
            allowed_locations = process.get('location', [])
            base_replicas = process.get('replicas', 1)
            
            total_replicas = base_replicas
            if location_policy == 'redundant' and allowed_locations:
                total_replicas = base_replicas * len(allowed_locations)
                
            for r in range(total_replicas):
                model.Add(sum(assignment[p_idx][r][s_idx] for s_idx in range(len(servers))) == 1)

        # 4.2 Location policy constraints
        for p_idx, process in enumerate(processes):
            allowed_locations = process.get('location', [])
            location_policy = process.get('location-policy')
            base_replicas = process.get('replicas', 1)
            
            total_replicas = base_replicas
            if location_policy == 'redundant' and allowed_locations:
                total_replicas = base_replicas * len(allowed_locations)
            
            # Only assign to servers in allowed locations
            if allowed_locations:
                for r in range(total_replicas):
                    for s_idx, server in enumerate(servers):
                        server_location = server.get('geographical-location')
                        if server_location not in allowed_locations:
                            model.Add(assignment[p_idx][r][s_idx] == 0)
            
            # For redundant policy, ensure each location gets the correct number of replicas
            if location_policy == 'redundant' and allowed_locations:
                for loc_idx, location in enumerate(allowed_locations):
                    # Calculate which replicas belong to this location
                    start_replica = loc_idx * base_replicas
                    end_replica = (loc_idx + 1) * base_replicas
                    
                    # Create a list of servers in this location
                    location_servers = [s_idx for s_idx, server in enumerate(servers) 
                                       if server.get('geographical-location') == location]
                    
                    if location_servers:
                        # Ensure exactly base_replicas are assigned to servers in this location
                        model.Add(
                            sum(assignment[p_idx][r][s_idx] 
                                for r in range(start_replica, end_replica)
                                for s_idx in location_servers) == base_replicas
                        )
                        
                        # Ensure replicas for this location are only on servers in this location
                        for r in range(start_replica, end_replica):
                            model.Add(
                                sum(assignment[p_idx][r][s_idx] for s_idx in location_servers) == 1
                            )
            
            # If redundant policy, ensure replicas are on different servers
            if location_policy == 'redundant' and total_replicas > 1:
                for loc_idx, location in enumerate(allowed_locations):
                    start_replica = loc_idx * base_replicas
                    end_replica = (loc_idx + 1) * base_replicas
                    
                    if base_replicas > 1:
                        for r1 in range(start_replica, end_replica):
                            for r2 in range(r1 + 1, end_replica):
                                for s_idx in range(len(servers)):
                                    # Can't have both replicas on the same server
                                    model.Add(assignment[p_idx][r1][s_idx] + assignment[p_idx][r2][s_idx] <= 1)
            
            # For single policy with multiple replicas, ensure they're on different servers
            elif location_policy == 'single' and base_replicas > 1:
                for r1 in range(base_replicas):
                    for r2 in range(r1 + 1, base_replicas):
                        for s_idx in range(len(servers)):
                            # Can't have both replicas on the same server
                            model.Add(assignment[p_idx][r1][s_idx] + assignment[p_idx][r2][s_idx] <= 1)

        # 4.3 OS compatibility constraints
        for p_idx, process in enumerate(processes):
            process_os = process.get('os')
            if process_os:
                replicas = process.get('replicas', 1)
                for r in range(replicas):
                    for s_idx, server in enumerate(servers):
                        server_os = server.get('os')
                        if server_os and server_os != process_os:
                            model.Add(assignment[p_idx][r][s_idx] == 0)

        # 4.4 Process scope constraints
        for p_idx, process in enumerate(processes):
            process_scope = process.get('scope')
            if process_scope:
                replicas = process.get('replicas', 1)
                for r in range(replicas):
                    for s_idx, server in enumerate(servers):
                        server_scope = server.get('process-scope', [])
                        if server_scope and process_scope not in server_scope:
                            model.Add(assignment[p_idx][r][s_idx] == 0)

        # 4.5 Process affinity and non-affinity constraints
        # Create a process name to index mapping for quick lookups
        process_name_to_idx = {}
        for p_idx, process in enumerate(processes):
            if 'name' in process:
                process_name = process['name']
                # Handle duplicate names by using a list of indices
                if process_name not in process_name_to_idx:
                    process_name_to_idx[process_name] = []
                process_name_to_idx[process_name].append(p_idx)
        
        # Apply affinity constraints - processes must be together
        for p_idx, process in enumerate(processes):
            # Skip if the process doesn't have affinity requirements
            if 'affinity' not in process or not process['affinity']:
                continue
                
            # For each process name in the affinity list
            for affinity_name in process['affinity']:
                # Skip if the affinity process doesn't exist
                if affinity_name not in process_name_to_idx:
                    print(f"⚠️  Warning: Process '{process.get('name')}' has affinity with non-existent process '{affinity_name}'. Constraint will be ignored.")
                    continue
                
                # Get all processes matching this name
                affinity_process_indices = process_name_to_idx[affinity_name]
                
                print(f"🔗 Setting up affinity: '{process.get('name')}' with '{affinity_name}'")
                
                # For each replica of the current process
                for r1 in range(process.get('replicas', 1)):
                    # Create a constraint that ensures this replica must be on the same server
                    # as at least one replica of the affinity process
                    
                    # For each server
                    for s_idx in range(len(servers)):
                        # This replica is on this server
                        current_on_server = assignment[p_idx][r1][s_idx]
                        
                        # If this replica is on this server, at least one affinity replica must also be here
                        affinity_replicas_on_server = []
                        
                        for affinity_p_idx in affinity_process_indices:
                            # Skip self-affinity
                            if affinity_p_idx == p_idx:
                                continue
                            
                            affinity_process = processes[affinity_p_idx]
                            # For each replica of the affinity process, check if it's on this server
                            for r2 in range(affinity_process.get('replicas', 1)):
                                affinity_replicas_on_server.append(assignment[affinity_p_idx][r2][s_idx])
                        
                        # If there are no affinity processes (only self), skip
                        if not affinity_replicas_on_server:
                            continue
                            
                        # If current process is on this server, at least one affinity replica must also be here
                        # current_on_server -> (affinity1 OR affinity2 OR...)
                        # This is equivalent to: NOT current_on_server OR (affinity1 OR affinity2 OR...)
                        model.AddBoolOr([current_on_server.Not()] + affinity_replicas_on_server)
                        
                    print(f"   ✅ Replica {r1+1} of '{process.get('name')}' must be co-located with any replica of '{affinity_name}'")
        
        # Apply non-affinity constraints - processes must be apart
        for p_idx, process in enumerate(processes):
            # Skip if the process doesn't have non-affinity requirements
            if 'non-affinity' not in process or not process['non-affinity']:
                continue
                
            # For each process name in the non-affinity list
            for non_affinity_name in process['non-affinity']:
                # Skip if the non-affinity process doesn't exist
                if non_affinity_name not in process_name_to_idx:
                    print(f"⚠️  Warning: Process '{process.get('name')}' has non-affinity with non-existent process '{non_affinity_name}'. Constraint will be ignored.")
                    continue
                
                # Get all processes matching this name
                non_affinity_process_indices = process_name_to_idx[non_affinity_name]
                
                # For each replica of the current process
                for r1 in range(process.get('replicas', 1)):
                    # For each process with the non-affinity name
                    for non_affinity_p_idx in non_affinity_process_indices:
                        # Skip self-non-affinity (redundant and could cause conflicts)
                        if non_affinity_p_idx == p_idx:
                            continue
                            
                        non_affinity_process = processes[non_affinity_p_idx]
                        # For each replica of the non-affinity process
                        for r2 in range(non_affinity_process.get('replicas', 1)):
                            # Create constraint: both can't be on the same server
                            for s_idx in range(len(servers)):
                                # Either the first process is on this server or the second, but not both
                                model.Add(assignment[p_idx][r1][s_idx] + assignment[non_affinity_p_idx][r2][s_idx] <= 1)
                                
        # 4.6 Resource constraints
        # Calculate the resource usage on each server
        ram_usage = {}
        cpu_usage = {}
        disk_usage = {}
        bandwidth_usage = {}
        process_count = {}
        energy_cost = {}
        
        for s_idx in range(len(servers)):
            server = servers[s_idx]
            
            # Sum of RAM usage on this server - scale to integers
            ram_usage[s_idx] = sum(
                assignment[p_idx][r][s_idx] * int(processes[p_idx]['ram'] * SCALE)
                for p_idx in range(len(processes))
                for r in range(processes[p_idx].get('replicas', 1))
            )
            
            # CPU usage calculation - ensure integers only
            cpu_usage[s_idx] = sum(
                assignment[p_idx][r][s_idx] * int(
                    processes[p_idx].get('cpu', (processes[p_idx]['ram'] / server['ram']) * server['cpu']) * SCALE
                )
                for p_idx in range(len(processes))
                for r in range(processes[p_idx].get('replicas', 1))
            )
            
            # Sum of disk usage on this server - scale to integers
            disk_usage[s_idx] = sum(
                assignment[p_idx][r][s_idx] * int(processes[p_idx]['disk'] * SCALE)
                for p_idx in range(len(processes))
                for r in range(processes[p_idx].get('replicas', 1))
            )
            
            # Fix bandwidth scaling to ensure consistency - scale to integers
            bandwidth_usage[s_idx] = sum(
                assignment[p_idx][r][s_idx] * int(processes[p_idx]['bandwidth'] * SCALE)
                for p_idx in range(len(processes))
                for r in range(processes[p_idx].get('replicas', 1))
            )
            
            # Count of processes on this server
            process_count[s_idx] = sum(
                assignment[p_idx][r][s_idx]
                for p_idx in range(len(processes))
                for r in range(processes[p_idx].get('replicas', 1))
            )
            
            # Apply resource constraints with scale factors for integer arithmetic
            max_ram_pct = safe_percentage(constraints.get('max-ram-usage-per-server'), 100)
            model.Add(ram_usage[s_idx] <= int(server['ram'] * max_ram_pct * SCALE / 100))
            
            max_cpu_pct = safe_percentage(constraints.get('max-cpu-usage-per-server'), 100)
            model.Add(cpu_usage[s_idx] <= int(server['cpu'] * max_cpu_pct * SCALE / 100))
            
            max_disk_pct = safe_percentage(constraints.get('max-disk-usage-per-server'), 100)
            model.Add(disk_usage[s_idx] <= int(server['disk'] * max_disk_pct * SCALE / 100))
            
            max_bandwidth_pct = safe_percentage(constraints.get('max-network-bandwidth-per-server'), 100)
            model.Add(bandwidth_usage[s_idx] <= int(server['bandwidth'] * max_bandwidth_pct * SCALE / 100))
            
            # Maximum processes per server
            max_processes = constraints.get('max-processes-per-server', sys.maxsize)
            model.Add(process_count[s_idx] <= max_processes)

        # 4.6 Isolate critical processes
        if constraints.get('isolate-critical-processes', False):
            critical_processes = [p_idx for p_idx, process in enumerate(processes) if process.get('critical', False)]
            non_critical_processes = [p_idx for p_idx, process in enumerate(processes) if not process.get('critical', False)]
            
            for s_idx in range(len(servers)):
                # If a critical process is on this server, no non-critical processes allowed
                for p_critical in critical_processes:
                    for r_critical in range(processes[p_critical].get('replicas', 1)):
                        for p_non_critical in non_critical_processes:
                            for r_non_critical in range(processes[p_non_critical].get('replicas', 1)):
                                model.Add(
                                    assignment[p_critical][r_critical][s_idx] + 
                                    assignment[p_non_critical][r_non_critical][s_idx] <= 1
                                )

        # 4.7 Energy consumption constraints
        max_energy = constraints.get('max-energy-consumption-per-server')
        if max_energy:
            for s_idx, server in enumerate(servers):
                # Integer-based energy approximation
                energy_usage = sum(
                    assignment[p_idx][r][s_idx] * int(
                        # CPU component (scaled)
                        (processes[p_idx]['ram'] / server['ram'] * server['cpu']) * 10 * SCALE + 
                        # Log component (scaled)
                        math.log(1 + processes[p_idx]['ram']) * SCALE
                    )
                    for p_idx in range(len(processes))
                    for r in range(processes[p_idx].get('replicas', 1))
                )
                model.Add(energy_usage <= int(max_energy * SCALE))
        
        # 4.8 Energy cost constraints
        max_daily_cost = constraints.get('max-daily-cost')
        if max_daily_cost is not None:
            try:
                # Convert to dollars if it's a percentage (for backward compatibility)
                if isinstance(max_daily_cost, str) and '%' in max_daily_cost:
                    max_cost_pct = safe_percentage(max_daily_cost, 100)
                    max_daily_cost = 100 * max_cost_pct / 100  # Default $100 × percentage
                else:
                    # Use directly as dollar amount
                    max_daily_cost = float(max_daily_cost)
                
                # Calculate energy costs using our simplified model
                total_energy_cost = 0
                
                for s_idx, server in enumerate(servers):
                    if server.get('energy-cost'):
                        # Create a boolean variable to indicate if server is used
                        server_is_used = model.NewBoolVar(f'server_{s_idx}_is_used')
                        
                        # Link this boolean with actual server usage
                        # If any process is assigned to this server, it's considered used
                        process_on_server = sum(
                            assignment[p_idx][r][s_idx]
                            for p_idx in range(len(processes))
                            for r in range(processes[p_idx].get('replicas', 1))
                        )
                        
                        # server_is_used is true if any process is on the server
                        model.Add(process_on_server >= 1).OnlyEnforceIf(server_is_used)
                        model.Add(process_on_server == 0).OnlyEnforceIf(server_is_used.Not())
                        
                        # Energy used by processes (CPU + RAM)
                        process_energy_cost = sum(
                            assignment[p_idx][r][s_idx] * int(
                                # Process power in watts: CPU cores * 10 + RAM in GB
                                (processes[p_idx].get('cpu', 1) * 10 + processes[p_idx]['ram']) *
                                # Convert to kWh and multiply by cost
                                24 / 1000 * server['energy-cost'] * 100  # × 100 for cents precision
                            )
                            for p_idx in range(len(processes))
                            for r in range(processes[p_idx].get('replicas', 1))
                        )
                        
                        # Idle power cost - only applied if server is used
                        idle_power_factor = int(50 * 24 / 1000 * server['energy-cost'] * 100)  # 50W idle power
                        
                        # Use the boolean to conditionally add idle cost
                        server_idle_cost = model.NewIntVar(0, idle_power_factor, f'idle_power_{s_idx}')
                        model.Add(server_idle_cost == idle_power_factor).OnlyEnforceIf(server_is_used)
                        model.Add(server_idle_cost == 0).OnlyEnforceIf(server_is_used.Not())
                        
                        # Total server cost
                        server_cost = process_energy_cost + server_idle_cost
                        total_energy_cost += server_cost
                
                # Apply constraint: total cost must be less than or equal to max cost in cents
                max_cost_cents = int(max_daily_cost * 100)
                model.Add(total_energy_cost <= max_cost_cents)
                
            except Exception as e:
                print(f"Warning: Could not apply daily cost constraint (${max_daily_cost:.2f}). "
                      f"The solution might exceed your budget.")
                # Only print detailed errors in debug mode
                if os.environ.get('DEBUG'):
                    import traceback
                    traceback.print_exc()
        
        # 4.9 Server redundancy constraint - Keep some servers unused
        servers_for_redundancy = constraints.get('servers-for-redundancy', 0)
        if servers_for_redundancy > 0:
            # Create boolean variables to track which servers are used
            server_used = []
            for s_idx in range(len(servers)):
                # A server is used if any process is assigned to it
                is_used = model.NewBoolVar(f'is_server_{s_idx}_used')
                
                # Sum of all processes on this server
                processes_on_server = sum(
                    assignment[p_idx][r][s_idx]
                    for p_idx in range(len(processes))
                    for r in range(processes[p_idx].get('replicas', 1))
                )
                
                # Link the boolean is_used with the actual usage
                model.Add(processes_on_server >= 1).OnlyEnforceIf(is_used)
                model.Add(processes_on_server == 0).OnlyEnforceIf(is_used.Not())
                
                server_used.append(is_used)
            
            # Constraint: at least servers_for_redundancy servers must be unused
            num_used_servers = sum(server_used)
            model.Add(num_used_servers <= len(servers) - servers_for_redundancy)
            
            print(f"Applying server redundancy constraint: {servers_for_redundancy} servers must remain unused")

        # 5. Define objective function
        objective_terms = []
        
        # Define default weights for different objectives
        default_weights = {
            'load-balancing': 10000,
            'green-energy': 1000,
            'cost': 100
        }
        
        # Get the optimization priorities from config or use default
        priorities = constraints.get('optimization-priorities', ['load-balancing', 'green-energy', 'cost'])
        
        # Validate priorities and filter out any invalid ones
        valid_priorities = [p for p in priorities if p in default_weights]
        if len(valid_priorities) != len(priorities):
            invalid_priorities = set(priorities) - set(default_weights.keys())
            print(f"⚠️  Warning: Invalid optimization priorities: {invalid_priorities}. Will be ignored.")
        
        # Assign weights based on priority order
        weights = {}
        for i, priority in enumerate(valid_priorities):
            # Exponentially decreasing weights: 10000, 1000, 100 (based on position)
            weights[priority] = 10 ** (4 - i)
        
        # Fill in default weights for any missing priorities
        for priority, default_weight in default_weights.items():
            if priority not in weights:
                weights[priority] = default_weight // 10  # Give lower weight to unspecified priorities
        
        print("📊 Applying optimization priorities:")
        for i, priority in enumerate(valid_priorities):
            priority_name = {
                'load-balancing': 'Load Balancing',
                'green-energy': 'Green Energy',
                'cost': 'Cost Minimization'
            }.get(priority, priority)
            print(f"  {i+1}. {priority_name} (Weight: {weights[priority]})")
        
        # Apply load balancing strategy (if prioritized)
        load_balancing_strategy = constraints.get('load-balancing-strategy')
        
        if load_balancing_strategy:
            print(f"🔄 Applying load balancing strategy: {load_balancing_strategy}")
            
            if load_balancing_strategy == 'round-robin':
                # Strategy: Distribute processes evenly (minimize maximum)
                max_processes_per_server = model.NewIntVar(0, 100, 'max_processes')
                for s_idx in range(len(servers)):
                    model.Add(process_count[s_idx] <= max_processes_per_server)
                objective_terms.append(max_processes_per_server * -weights['load-balancing'])  # Use configured weight
                
            elif load_balancing_strategy == 'bin-packing':
                # Strategy: Pack processes onto fewer servers (power saving)
                server_used_vars = []
                for s_idx in range(len(servers)):
                    # Create a boolean to indicate if server is used
                    is_server_used = model.NewBoolVar(f'is_server_{s_idx}_used_for_lb')
                    
                    # Server is used if it has at least one process
                    model.Add(process_count[s_idx] >= 1).OnlyEnforceIf(is_server_used)
                    model.Add(process_count[s_idx] == 0).OnlyEnforceIf(is_server_used.Not())
                    
                    # Minimize number of servers used
                    server_used_vars.append(is_server_used)
                    
                # Minimize the number of servers used
                objective_terms.append(sum(server_used_vars) * -weights['load-balancing'])
                
            elif load_balancing_strategy == 'weighted-capacity':
                # Strategy: Distribute load proportionally to server capacity
                total_ram = sum(server['ram'] for server in servers)
                total_cpu = sum(server['cpu'] for server in servers)
                
                for s_idx, server in enumerate(servers):
                    # Calculate target process count based on server capacity
                    capacity_ratio = (server['ram'] / total_ram + server['cpu'] / total_cpu) / 2
                    target_process_count = int(sum(p.get('replicas', 1) for p in processes) * capacity_ratio)
                    
                    # Create variables for deviation from target
                    deviation = model.NewIntVar(-100, 100, f'process_deviation_{s_idx}')
                    abs_deviation = model.NewIntVar(0, 100, f'abs_process_deviation_{s_idx}')
                    
                    # Set deviation = actual - target
                    model.Add(deviation == process_count[s_idx] - target_process_count)
                    
                    # Set abs_deviation = |deviation|
                    model.Add(abs_deviation >= deviation)
                    model.Add(abs_deviation >= -deviation)
                    
                    # Minimize absolute deviation
                    objective_terms.append(abs_deviation * -weights['load-balancing'])  # Use configured weight
            
            else:
                print(f"Warning: Unknown load balancing strategy '{load_balancing_strategy}'. Using default behavior.")

        # Apply green energy preference (if prioritized)
        if constraints.get('prioritize-green-energy', False):
            for p_idx in range(len(processes)):
                for r in range(processes[p_idx].get('replicas', 1)):
                    for s_idx, server in enumerate(servers):
                        # Add a bonus for assigning to green energy servers
                        if server.get('green-enegery', False):  # Note: This is the spelling in the YAML
                            objective_terms.append(assignment[p_idx][r][s_idx] * weights['green-energy'])  # Use configured weight
        
        # Apply energy cost optimization (if prioritized)
        # Calculate the theoretical maximum cost to use for scaling
        max_possible_cost = 0
        for s_idx, server in enumerate(servers):
            if server.get('energy-cost'):
                # Find the most expensive process-server combination for scaling
                for p_idx in range(len(processes)):
                    process = processes[p_idx]
                    # Calculate cost of this process on this server
                    process_energy = (process.get('cpu', 1) * 10 + process['ram']) * 24 / 1000  # kWh
                    process_cost = process_energy * server['energy-cost'] * 100  # cents
                    if process_cost > max_possible_cost:
                        max_possible_cost = process_cost
        
        # Create cost-based weights for each process-server assignment
        if max_possible_cost > 0:  # Avoid division by zero
            for p_idx, process in enumerate(processes):
                for r in range(process.get('replicas', 1)):
                    for s_idx, server in enumerate(servers):
                        if server.get('energy-cost'):
                            # Calculate expected energy usage
                            process_cpu = process.get('cpu', 1)
                            process_ram = process['ram']
                            energy_kwh = (process_cpu * 10 + process_ram) * 24 / 1000
                            
                            # Calculate cost in cents
                            cost_cents = energy_kwh * server['energy-cost'] * 100
                            
                            # Create a negative weight (since we're maximizing)
                            weight = -int(cost_cents * weights['cost'] / max_possible_cost)  # Use configured weight
                            objective_terms.append(assignment[p_idx][r][s_idx] * weight)
        
        # Set the objective
        if objective_terms:
            model.Maximize(sum(objective_terms))

        # 6. Solve the model
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # 7. Output the results
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("\n===== 🚀 OPTIMAL PROCESS ALLOCATION 🚀 =====\n")
            
            # Calculate and display resource utilization
            server_resources = {s_idx: {
                'ram': 0, 'cpu': 0, 'disk': 0, 'bandwidth': 0, 'processes': 0, 'energy': 0, 'cost': 0
            } for s_idx in range(len(servers))}
            
            # Display process assignments
            for p_idx, process in enumerate(processes):
                print(f"📦 Process: {process['name']} (Policy: {process.get('location-policy', 'none')})")
                
                location_policy = process.get('location-policy')
                allowed_locations = process.get('location', [])
                base_replicas = process.get('replicas', 1)
                
                total_replicas = base_replicas
                if location_policy == 'redundant' and allowed_locations:
                    total_replicas = base_replicas * len(allowed_locations)
                    
                # Group by location for better output formatting
                replicas_by_location = {}
                
                for r in range(total_replicas):
                    for s_idx, server in enumerate(servers):
                        if solver.Value(assignment[p_idx][r][s_idx]) == 1:
                            location = server.get('geographical-location', 'Unknown')
                            if location not in replicas_by_location:
                                replicas_by_location[location] = []
                            
                            # Use the modulus for redundant policy to get proper replica numbering
                            if location_policy == 'redundant':
                                replica_num = (r % base_replicas) + 1
                            else:
                                replica_num = r + 1
                                
                            replicas_by_location[location].append((replica_num, server['name']))
                            
                            # Update server resource usage
                            server_resources[s_idx]['ram'] += process['ram']
                            server_resources[s_idx]['cpu'] += process.get('cpu', (process['ram'] / server['ram']) * server['cpu'])
                            server_resources[s_idx]['disk'] += process['disk']
                            server_resources[s_idx]['bandwidth'] += process['bandwidth']
                            server_resources[s_idx]['processes'] += 1
                
                # Display replicas grouped by location
                for location, replicas in replicas_by_location.items():
                    print(f"  📍 Location: {location}")
                    for replica_num, server_name in replicas:
                        print(f"    🔄 Replica {replica_num} → Server: {server_name}")

            # Display server usage information
            print("\n===== 🖥️  SERVER UTILIZATION 🖥️  =====\n")
            total_cost = 0
            for s_idx, server in enumerate(servers):
                print(f"🏢 Server: {server['name']} ({server.get('geographical-location')})")
                usage = server_resources[s_idx]
                
                # Remove this calculation since we now directly accumulate actual CPU usage
                # ram_ratio = usage['ram'] / server['ram']
                # usage['cpu'] = ram_ratio * server['cpu']
                
                # Calculate energy if formula exists
                try:
                    usage['energy'] = calculate_energy_consumption(
                        server, usage['ram'], usage['cpu']
                    )
                except Exception as e:
                    print(f"Error calculating energy for server {server.get('name')}: {e}")
                    
                # Calculate cost safely
                try:
                    if server.get('energy-cost') and usage['energy']:
                        usage['cost'] = usage['energy'] * server['energy-cost'] * 24  # daily cost
                        total_cost += usage['cost']
                except Exception as e:
                    print(f"Error calculating cost for server {server.get('name')}: {e}")
                
                print(f"  💾 RAM: {usage['ram']}/{server['ram']} GB ({usage['ram']/server['ram']*100:.1f}%)")
                print(f"  ⚙️  CPU: {usage['cpu']}/{server['cpu']} cores ({usage['cpu']/server['cpu']*100:.1f}%)")
                print(f"  💿 Disk: {usage['disk']}/{server['disk']} GB ({usage['disk']/server['disk']*100:.1f}%)")
                print(f"  🌐 Bandwidth: {usage['bandwidth']}/{server['bandwidth']} GB/s ({usage['bandwidth']/server['bandwidth']*100:.1f}%)")
                print(f"  🧩 Processes: {usage['processes']}")
                if usage['energy']:
                    print(f"  ⚡ Daily Energy Consumption: {usage['energy']:.2f} kWh")
                if server.get('green-enegery'):
                    print("  🍃 Green Energy")
                if usage['cost']:
                    print(f"  💰 Daily Energy Cost: ${usage['cost']:.2f}")
                print()
                
            if total_cost > 0:
                print(f"\n💲 Total Daily Energy Cost: ${total_cost:.2f}")
                
                # Verify if the cost constraint was met
                max_daily_cost = constraints.get('max-daily-cost')
                if max_daily_cost is not None:
                    # Convert to dollars if it's a percentage (for backward compatibility)
                    if isinstance(max_daily_cost, str) and '%' in max_daily_cost:
                        max_cost_pct = safe_percentage(max_daily_cost, 100)
                        max_daily_cost = 100 * max_cost_pct / 100  # Default $100 × percentage
                    else:
                        max_daily_cost = float(max_daily_cost)
                    
                    if total_cost > max_daily_cost:
                        print(f"\n⚠️  WARNING: The total daily cost (${total_cost:.2f}) exceeds your budget constraint (${max_daily_cost:.2f}).")
                        print("   💸 This might happen due to differences between the estimated cost used in the constraint")
                        print("   💸 and the actual cost calculated from the final allocation.")
                        print("   💡 To strictly enforce the budget, try reducing the max-daily-cost constraint by 5-10%.")
                
            # Count used/unused servers
            used_servers = 0
            for s_idx in range(len(servers)):
                if server_resources[s_idx]['processes'] > 0:
                    used_servers += 1
            
            print(f"\n🔢 Servers used: {used_servers}/{len(servers)}")
            
            # Check if the server redundancy constraint was met
            servers_for_redundancy = constraints.get('servers-for-redundancy', 0)
            if servers_for_redundancy > 0:
                unused_servers = len(servers) - used_servers
                if unused_servers < servers_for_redundancy:
                    print(f"\n⚠️  WARNING: Only {unused_servers} servers remain unused, " 
                          f"but {servers_for_redundancy} were requested for redundancy.")
                else:
                    print(f"\n✅ Server redundancy constraint satisfied: "
                          f"{unused_servers} servers remain unused (requested: {servers_for_redundancy})")
            
            # Summary statistics with emojis
            print("\n===== 📊 SUMMARY STATISTICS 📊 =====")
            print(f"🔄 Total processes deployed: {sum(p.get('replicas', 1) for p in processes)}")
            print(f"💻 Active servers: {used_servers} / {len(servers)}")
            
            # Calculate total resource usage
            total_ram = sum(server_resources[s_idx]['ram'] for s_idx in range(len(servers)))
            total_ram_capacity = sum(server['ram'] for server in servers)
            total_cpu = sum(server_resources[s_idx]['cpu'] for s_idx in range(len(servers)))
            total_cpu_capacity = sum(server['cpu'] for server in servers)
            
            print(f"💾 Total RAM usage: {total_ram}/{total_ram_capacity} GB ({(total_ram/total_ram_capacity)*100:.1f}%)")
            print(f"⚙️  Total CPU usage: {total_cpu:.1f}/{total_cpu_capacity} cores ({(total_cpu/total_cpu_capacity)*100:.1f}%)")
            
            # Energy statistics
            green_servers = sum(1 for server in servers if server.get('green-enegery', False) and 
                               server_resources[servers.index(server)]['processes'] > 0)
            if green_servers > 0:
                print(f"🍃 Using {green_servers} green energy servers!")
                
            print(f"💰 Total daily cost: ${total_cost:.2f}")
            
            # Overall assessment
            if status == cp_model.OPTIMAL:
                print("\n🏆 Found optimal solution! 🎉")
            else:
                print("\n🎯 Found feasible solution (may not be optimal) 👍")
                
        else:
            print("❌ No feasible solution found. You may need to adjust your constraints. 😞")

    except Exception as e:
        print(f"❗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
