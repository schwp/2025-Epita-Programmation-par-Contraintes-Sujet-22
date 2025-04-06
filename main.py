from classes.VMScheduler import VMScheduler
from utils.ploting import print_allocation, visualize_allocation

if __name__ == '__main__':
    VMS = VMScheduler('config.yml')
    VMS.build_model()
    res = VMS.solve()

    print_allocation(res, VMS.servers)
    visualize_allocation(res)