import matplotlib.pyplot as plt

def visualize_allocation(result):
        """
        Visualiser l'allocation des VMs aux serveurs
        """
        if not result['success']:
            print(f"Impossible de visualiser : {result['status']}")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
        
        cpu_data = {}
        ram_data = {}
        
        for server_id, metrics in result['server_utilization'].items():
            cpu_data[f"Serveur {server_id}"] = metrics['cpu']['percentage']
            ram_data[f"Serveur {server_id}"] = metrics['ram']['percentage']
        
        ax1.bar(cpu_data.keys(), cpu_data.values(), color='skyblue')
        ax1.set_title('Utilisation CPU par serveur (%)')
        ax1.set_ylabel('Pourcentage d\'utilisation')
        ax1.axhline(y=80, color='r', linestyle='--', label='Seuil critique (80%)')
        ax1.legend()
        
        ax2.bar(ram_data.keys(), ram_data.values(), color='lightgreen')
        ax2.set_title('Utilisation RAM par serveur (%)')
        ax2.set_ylabel('Pourcentage d\'utilisation')
        ax2.axhline(y=80, color='r', linestyle='--', label='Seuil critique (80%)')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('vm_allocation_results.png')
        plt.show()
        
        return fig

def print_allocation(result, servers):
        """
        Afficher de manière lisible l'allocation des VMs
        """
        if not result['success']:
            print(f"Pas de solution trouvée. Statut: {result['status']}")
            return
        
        print(f"\n=== Résultats d'allocation ({result['status']}) ===")
        print(f"Temps de résolution : {result['solve_time']:.3f} secondes")
        print(f"Nombre de serveurs utilisés : {result['num_used_servers']} sur {len(servers)}")
        
        # Organiser par serveur
        server_allocations = {}
        for allocation in result['allocation']:
            server_id = allocation['server_id']
            if server_id not in server_allocations:
                server_allocations[server_id] = []
            server_allocations[server_id].append(allocation)
        
        # Afficher par serveur
        for server_id, allocations in sorted(server_allocations.items()):
            util = result['server_utilization'][server_id]
            print(f"\nServeur {server_id}:")
            print(f"  CPU: {util['cpu']['used']}/{util['cpu']['capacity']} ({util['cpu']['percentage']:.1f}%)")
            print(f"  RAM: {util['ram']['used']}/{util['ram']['capacity']} ({util['ram']['percentage']:.1f}%)")
            print("  VMs:")
            
            for vm in sorted(allocations, key=lambda x: x['vm_id']):
                print(f"    - VM {vm['vm_id']} ({vm['vm_type']}): {vm['cpu']} CPU, {vm['ram']} RAM")