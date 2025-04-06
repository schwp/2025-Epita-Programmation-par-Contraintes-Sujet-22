import yaml
from classes.Server import Server
from classes.VirtualMachine import VirtualMachine

def parse_data(filename):
    with open(filename) as file:
        data_parsed = yaml.load(file, Loader=yaml.FullLoader)

    severs = [
            Server(s['id'], s['cpu_capacity'], s['ram_capacity'], s['location']) 
                for s in data_parsed['servers']
            ]
    
    vms = [
            VirtualMachine(vm['id'], vm['cpu'], vm['ram'], vm['type'], vm['priority']) 
                for vm in data_parsed['vms']
            ]

    constraints = data_parsed.get('constraints', {})

    return severs, vms, constraints
