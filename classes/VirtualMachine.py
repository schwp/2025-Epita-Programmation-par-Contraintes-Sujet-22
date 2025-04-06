class VirtualMachine:
    def __init__(self, id, cpu, ram, type, priority):
        self.id = id
        self.cpu = cpu
        self.ram = ram
        self.type = type
        self.priority = priority

    def __str__(self):
        return f'VM {self.id}: \nCPU : {self.cpu}\nRAM : {self.ram}\nType : {self.type}\nPriority: {self.priority}'