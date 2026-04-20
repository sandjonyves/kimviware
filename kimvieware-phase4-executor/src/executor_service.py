# """
# Phase 4: Test Executor Service

# Consumes: optimization.completed
# Produces: execution.completed
# """
# import sys
# from pathlib import Path
# import tempfile

# sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'kimvieware-shared' / 'src'))

# from kimvieware_shared import MicroserviceBase, JobStatus, Trajectory
# from generators.test_generator import TestGenerator
# from executors.test_executor import TestExecutor
# from executors.mutation_tester import MutationTester

# class ExecutorService(MicroserviceBase):
#     """Phase 4: Test Execution and Mutation Testing"""
    
#     def __init__(self):
#         super().__init__(
#             service_name="Phase4_Executor",
#             input_queue="optimization.completed",
#             output_queue="execution.completed"
#         )
        
#         self.test_generator = TestGenerator()
#         self.test_executor = TestExecutor()
#         self.mutation_tester = MutationTester()
    
#     def process_message(self, message: dict) -> dict:
#         """Execute tests and perform mutation analysis"""
        
#         job_id = message['job_id']
        
#         # Only process optimized jobs
#         if message.get('status') != 'optimized':
#             self.logger.warning(f"[{job_id}] Skipping: not optimized")
#             return message
        
#         trajectories_data = message.get('trajectories', [])
#         sut_info = message['sut_info']
#         # Extract port from metadata or default to 8000
#         sut_port = message.get('metadata', {}).get('port', 8000)
#         sut_url = f"http://localhost:{sut_port}"
        
#         if not trajectories_data:
#             return self._error(job_id, "No trajectories to execute")
        
#         self.logger.info(f"[{job_id}] Phase 4: Executing {len(trajectories_data)} trajectories on {sut_url}")
        
#         # Reconstruct Trajectory objects
#         trajectories = [Trajectory.from_dict(t) for t in trajectories_data]
#         test_count = len(trajectories)
        
#         # Step 1: Generate tests
#         with tempfile.TemporaryDirectory() as tmpdir:
#             output_dir = Path(tmpdir)
            
#             try:
#                 # Pass the custom SUT URL to the generator
#                 test_file = self.test_generator.generate(trajectories, output_dir)
                
#                 # Step 2: Execute tests
#                 exec_stats = self.test_executor.execute(test_file, sut_url=sut_url, test_count=test_count)
                
#                 # Step 3: Mutation testing
#                 # Find SUT path (from extracted_path in earlier phases)
#                 # For demo, we use a placeholder
#                 sut_path = Path("/tmp/auth-service-placeholder")
                
#                 mutation_stats = self.mutation_tester.run_mutation_testing(
#                     sut_path=sut_path,
#                     test_file=test_file
#                 )
                
#             except Exception as e:
#                 self.logger.error(f"[{job_id}] Execution failed: {str(e)}")
#                 return self._error(job_id, str(e))
        
#         self.logger.info(
#             f"[{job_id}] ✅ Execution: {exec_stats['passed']}/{exec_stats['total']} passed, "
#             f"Mutation: {mutation_stats['mutation_score']:.1f}%"
#         )
        
#         # Return result - KEEP ALL DATA FROM PREVIOUS PHASES
#         return {
#             'job_id': job_id,
#             'status': JobStatus.COMPLETED.value,
#             'sut_info': sut_info,
#             # IMPORTANT: Keep ALL previous phase data for dashboard
#             'extraction_count': message.get('extraction_count'),
#             'original_trajectories': message.get('original_trajectories'),
#             'sgats_stats': message.get('sgats_stats'),
#             'evopath_stats': message.get('evopath_stats'),
#             'execution_stats': exec_stats,
#             'mutation_stats': mutation_stats,
#             'trajectories_count': len(trajectories),
#             'trajectories': [t.to_dict() for t in trajectories],
#             'metadata': {
#                 'phase': 'execution',
#                 'test_count': len(trajectories)
#             }
#         }
    
#     def _error(self, job_id: str, msg: str) -> dict:
#         return {
#             'job_id': job_id,
#             'status': JobStatus.FAILED.value,
#             'error': msg,
#             'phase': 'execution'
#         }

# if __name__ == "__main__":
#     service = ExecutorService()
#     service.start()


"""
Phase 4: Test Executor Service - VERSION FINALE CORRIGÉE
Responsable de la génération, l'exécution et la mesure de qualité réelle (Mutation).
"""
import sys
from pathlib import Path
import tempfile

# Insertion du chemin pour les modèles partagés
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'kimvieware-shared' / 'src'))

from kimvieware_shared import MicroserviceBase, JobStatus, Trajectory
from generators.test_generator import TestGenerator
from executors.test_executor import TestExecutor
from executors.mutation_tester import MutationTester

class ExecutorService(MicroserviceBase):
    """Phase 4: Pilotage de la génération et de l'exécution des tests"""
    
    def __init__(self):
        super().__init__(
            service_name="Phase4_Executor",
            input_queue="optimization.completed",
            output_queue="execution.completed"
        )
        
        # Initialisation des composants de la phase 4
        self.test_generator = TestGenerator()
        self.test_executor = TestExecutor()
        self.mutation_tester = MutationTester()
    
    def process_message(self, message: dict) -> dict:
        self.logger.info("="*50)
        self.logger.info("!!! DÉMARRAGE DE L'EXÉCUTION RÉELLE (PHASE 4) !!!")
        
        job_id = message['job_id']
        trajectories_data = message.get('trajectories', [])
        sut_info = message.get('sut_info', {})
        metadata = message.get('metadata', {})

        # --- RECHERCHE DU PORT (Flexible) ---
        sut_port = metadata.get('port') or sut_info.get('port') or 8000
        sut_url = f"http://localhost:{sut_port}"
        
        # --- AMÉLIORATION FINALE : TON VRAI CHEMIN SUT ---
        # On essaie d'abord le chemin dynamique, sinon on utilise ton chemin réel
        sut_path_str = message.get('extracted_path') or sut_info.get('path')
        
        if not sut_path_str or "placeholder" in sut_path_str:
            # ICI : Remplace par le chemin COMPLET vers ton dossier room-service
            # Exemple : "/home/yvanna/Documents/KIMVIEware-System-kimvieware-sut-timetables/room-service"
            sut_path_str = "/home/yvanna/MASTER1/SEMESTRE2/INF4198_UE_PROJET/TP_UEPROJET/kimviware/KIMVIEware-System-kimvieware-sut-timetables/room-service" 
            self.logger.info(f"📍 Utilisation du chemin physique : {sut_path_str}")

        sut_path = Path(sut_path_str)
        
        if not trajectories_data:
            self.logger.error("❌ ARRÊT : Aucune trajectoire à traiter.")
            return self._error(job_id, "Liste de trajectoires vide.")

        self.logger.info(f"ID du Job : {job_id}")
        self.logger.info(f"Cible : {sut_url}")

        trajectories = [Trajectory.from_dict(t) for t in trajectories_data]
        test_count = len(trajectories)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            try:
                # 1. Génération réelle (Axe 1 & 2)
                self.logger.info(f"🚀 ÉTAPE 1 : Génération de {test_count} tests intelligents...")
                test_file = self.test_generator.generate(trajectories, output_dir, sut_url=sut_url)
                
                # 2. Exécution réelle (Axe 4 - Pytest)
                self.logger.info("🚀 ÉTAPE 2 : Exécution de Pytest sur le SUT...")
                exec_stats = self.test_executor.execute(test_file, sut_url=sut_url, test_count=test_count)
                
                # 3. Mutation réelle (Axe 4 - MutPy)
                self.logger.info(f"🚀 ÉTAPE 3 : Analyse de mutation sur {sut_path.name}...")
                mutation_stats = self.mutation_tester.run_mutation_testing(
                    sut_path=sut_path,
                    test_file=test_file
                )
                
                self.logger.info("✅ PROCESSUS TERMINÉ AVEC SUCCÈS")

            except Exception as e:
                self.logger.error(f"❌ CRASH pendant l'exécution : {str(e)}")
                return self._error(job_id, f"Erreur fatale : {str(e)}")

        self.logger.info("="*50)
        return {
            'job_id': job_id,
            'status': JobStatus.COMPLETED.value,
            'sut_info': sut_info,
            'execution_stats': exec_stats,
            'mutation_stats': mutation_stats,
            'trajectories_count': len(trajectories),
            'trajectories': [t.to_dict() for t in trajectories]
        }
    def _error(self, job_id: str, msg: str) -> dict:
        """Formatage des messages d'erreur"""
        return {
            'job_id': job_id,
            'status': JobStatus.FAILED.value,
            'error': msg,
            'phase': 'execution'
        }

if __name__ == "__main__":
    service = ExecutorService()
    service.start()