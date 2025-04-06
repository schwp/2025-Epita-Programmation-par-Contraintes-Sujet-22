from ortools.sat.python import cp_model
import time

from utils.parser import parse_data

class VMScheduler:
    """
    Planificateur d'allocation de machines virtuelles aux serveurs physiques
    en utilisant la programmation par contraintes.
    """
    
    def __init__(self, config_file):
        """
        Initialiser le planificateur avec un fichier de configuration
        
        :param config_file: Chemin vers le fichier YAML de configuration
        """
        self.servers, self.vms, self.constraints = parse_data(config_file)
        
        self.model = None
        self.vm_assignments = {}
        self.solver = None
        
        print(f"Configuration chargée : {len(self.servers)} serveurs, {len(self.vms)} VMs")
    
    def build_model(self):
        """
        Construire le modèle de programmation par contraintes
        """
        self.model = cp_model.CpModel()
        
        for vm in self.vms:
            for server in self.servers:
                var_name = f'vm_{vm.id}_on_server_{server.id}'
                self.vm_assignments[(vm.id, server.id)] = self.model.NewBoolVar(var_name)
        
        for vm in self.vms:
            constraint_terms = []
            for server in self.servers:
                constraint_terms.append(self.vm_assignments[(vm.id, server.id)])
            self.model.Add(sum(constraint_terms) == 1)
        

        # Ajout des contraintes
        self._add_capacity_constraints()
        self._add_affinity_constraints()
        self._set_objective_function()
        
        return self.model
    
    def _add_capacity_constraints(self):
        """
        Ajouter les contraintes de capacité pour chaque serveur
        """
        # Vérifier qu'il n'y ait pas de dépassements des capacités serveur
        for server in self.servers:
            cpu_usage = []
            for vm in self.vms:
                cpu_usage.append(
                    self.vm_assignments[(vm.id, server.id)] * vm.cpu
                )
            self.model.Add(sum(cpu_usage) <= server.cpu_cap)
            
            ram_usage = []
            for vm in self.vms:
                ram_usage.append(
                    self.vm_assignments[(vm.id, server.id)] * vm.ram
                )
            self.model.Add(sum(ram_usage) <= server.ram_cap)
    
    def _add_affinity_constraints(self):
        """
        Ajouter les contraintes d'affinité et anti-affinité
        """
        # Les VMs doivent être sur les mêmes serveurs
        if 'affinity' in self.constraints:
            for group in self.constraints['affinity']:
                vms = group['vms']

                for i in range(len(vms) - 1):
                    vm1_id = vms[i]
                    vm2_id = vms[i+1]

                    for server in self.servers:
                        # vm1 et vm2 doivent être sur le même serveur
                        self.model.Add(
                            self.vm_assignments[(vm1_id, server.id)] == 
                            self.vm_assignments[(vm2_id, server.id)]
                        )
        
        # Les VMs doivent être sur des serveurs différents
        if 'anti_affinity' in self.constraints:
            for group in self.constraints['anti_affinity']:
                vms = group['vms']

                for i in range(len(vms)):
                    for j in range(i+1, len(vms)):
                        vm1_id = vms[i]
                        vm2_id = vms[j]

                        for server in self.servers:
                            # vm1 et vm2 ne peuvent pas être sur le même serveur
                            self.model.Add(
                                self.vm_assignments[(vm1_id, server.id)] + 
                                self.vm_assignments[(vm2_id, server.id)] <= 1
                            )
    
    def _set_objective_function(self):
        """
        Définir la fonction objectif pour l'optimisation
        """
        # Création de variables pour savoir si un serveur est utilisé ou non
        server_used = {}
        for server in self.servers:
            server_used[server.id] = self.model.NewBoolVar(f'server_{server.id}_used')
            
            vm_on_server = []
            for vm in self.vms:
                vm_on_server.append(self.vm_assignments[(vm.id, server.id)])
            
            self.model.AddBoolOr(vm_on_server).OnlyEnforceIf(server_used[server.id])
            self.model.AddBoolAnd([vm.Not() for vm in vm_on_server]).OnlyEnforceIf(server_used[server.id].Not())
        
        # On cherche à minimiser le nombre de serveur utilisé
        self.model.Minimize(sum(server_used.values()))
        
    
    def solve(self, time_limit_seconds=30):
        """
        Résoudre le problème d'allocation
        
        :param time_limit_seconds: Limite de temps de résolution en secondes
        :return: Dictionnaire des résultats avec l'allocation, le statut et les statistiques
        """
        # Si le modèle n'est pas encore construit, le faire
        if self.model is None:
            self.build_model()
        
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        
        start_time = time.time()
        status = self.solver.Solve(self.model)
        solve_time = time.time() - start_time
        
        result = {
            'status': self._get_status_string(status),
            'success': status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            'solve_time': solve_time,
            'allocation': [],
            'used_servers': set(),
            'stats': {
                'branches': self.solver.NumBranches(),
                'conflicts': self.solver.NumConflicts()
            }
        }
        
        if result['success']:
            for vm in self.vms:
                for server in self.servers:
                    if self.solver.Value(self.vm_assignments[(vm.id, server.id)]) == 1:
                        allocation = {
                            'vm_id': vm.id,
                            'vm_type': vm.type,
                            'server_id': server.id,
                            'cpu': vm.cpu,
                            'ram': vm.ram
                        }
                        result['allocation'].append(allocation)
                        result['used_servers'].add(server.id)
            
            result['num_used_servers'] = len(result['used_servers'])
            result['server_utilization'] = self._calculate_utilization(result['allocation'])
        
        return result
    
    def _get_status_string(self, status):
        """
        Convertir le code de statut du solveur en chaîne lisible
        """
        if status == cp_model.OPTIMAL:
            return "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            return "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            return "INFEASIBLE"
        elif status == cp_model.MODEL_INVALID:
            return "MODEL_INVALID"
        else:
            return "UNKNOWN"
    
    def _calculate_utilization(self, allocation):
        """
        Calculer l'utilisation des ressources pour chaque serveur
        """
        utilization = {}
        
        for server in self.servers:
            server_id = server.id
            utilization[server_id] = {
                'cpu': {
                    'used': 0,
                    'capacity': server.cpu_cap,
                    'percentage': 0
                },
                'ram': {
                    'used': 0,
                    'capacity': server.ram_cap,
                    'percentage': 0
                }
            }
        
        for item in allocation:
            server_id = item['server_id']
            utilization[server_id]['cpu']['used'] += item['cpu']
            utilization[server_id]['ram']['used'] += item['ram']
        
        for server_id, metrics in utilization.items():
            metrics['cpu']['percentage'] = (metrics['cpu']['used'] / metrics['cpu']['capacity']) * 100
            metrics['ram']['percentage'] = (metrics['ram']['used'] / metrics['ram']['capacity']) * 100
        
        return utilization
