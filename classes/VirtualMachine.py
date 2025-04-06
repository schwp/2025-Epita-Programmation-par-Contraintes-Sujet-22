class VirtualMachine:
    def __init__(self, id, cpu, ram, type):
        self.id = id
        self.cpu = cpu
        self.ram = ram
        self.type = type

    def __str__(self):
        return f'VM {self.id}: \nCPU : {self.cpu}\nRAM : {self.ram}\nType : {self.type}'