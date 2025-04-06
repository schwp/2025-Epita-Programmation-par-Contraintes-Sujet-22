class Server:
    def __init__(self, id, cpu, ram, location):
        self.id = id
        self.cpu_cap = cpu
        self.ram_cap = ram
        self.location = location

    def __str__(self):
        return f'Server {self.id}: \nCPU : {self.cpu_cap}\nRAM : {self.ram_cap}\nLocation : {self.location}'