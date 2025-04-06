import yaml
from classes.Server import Server
from classes.VirtualMachine import VirtualMachine

def parse_data():
    with open("config.yml") as file:
        data_parsed = yaml.load(file, Loader=yaml.FullLoader)

    # FIXME: should we consider constraints in the data to parse ?
    data = {
        "servers" : [
            Server(s['id'], s['cpu_capacity'], s['ram_capacity'], s['location']) 
                for s in data_parsed['servers']
            ],
        "vms" : [
            VirtualMachine(vm['id'], vm['cpu'], vm['ram'], vm['type']) 
                for vm in data_parsed['vms']
            ]
    }

    print("\033[1m Servers: \033[0m")
    for server in data['servers']:
        print(server)
        print('-' * 10)

    print("\033[1m \n VMs: \033[0m")
    for vm in data['vms']:
        print(vm)
        print('-' * 10)
    

if __name__ == '__main__':
    parse_data()