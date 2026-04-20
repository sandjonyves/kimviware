# """
# Mutation Testing
# Evaluates test suite quality using mutation analysis
# """
# import subprocess
# import re
# from pathlib import Path
# from typing import Dict

# class MutationTester:
#     """
#     Mutation Testing using MutPy
    
#     Generates mutants of the SUT and checks if tests detect them
#     Mutation Score = (Killed Mutants / Total Mutants) × 100%
#     """
    
#     def __init__(self):
#         pass
    
#     def run_mutation_testing(
#         self,
#         sut_path: Path,
#         test_file: Path,
#         target_modules: list = None
#     ) -> Dict:
#         """
#         Run mutation testing
        
#         Args:
#             sut_path: Path to SUT source code
#             test_file: Path to test file
#             target_modules: List of modules to mutate (e.g., ['src.routes.auth'])
        
#         Returns:
#             Mutation testing statistics
#         """
        
#         print(f"\n🧬 Mutation Testing")
#         print(f"{'='*60}")
#         print(f"SUT: {sut_path}")
#         print(f"Tests: {test_file}")
        
#         if not target_modules:
#             # Default: mutate main modules
#             target_modules = self._find_target_modules(sut_path)
        
#         print(f"Target modules: {', '.join(target_modules)}")
        
#         # Run MutPy (simplified - full MutPy requires complex setup)
#         # For demo, we simulate mutation testing results
        
#         print(f"\n🔬 Generating mutants...")
        
#         # Simulate mutation analysis
#         stats = self._simulate_mutation_testing(sut_path, len(target_modules))
        
#         print(f"\n📊 Mutation Testing Results:")
#         print(f"   Total mutants: {stats['total_mutants']}")
#         print(f"   Killed: {stats['killed']}")
#         print(f"   Survived: {stats['survived']}")
#         print(f"   Timeout: {stats['timeout']}")
#         print(f"   Mutation Score: {stats['mutation_score']:.1f}%")
        
#         # Quality assessment
#         if stats['mutation_score'] >= 90:
#             quality = "Excellent"
#         elif stats['mutation_score'] >= 80:
#             quality = "Good"
#         elif stats['mutation_score'] >= 70:
#             quality = "Acceptable"
#         else:
#             quality = "Needs Improvement"
        
#         print(f"   Quality: {quality}")
#         print(f"{'='*60}\n")
        
#         return stats
    
#     def _find_target_modules(self, sut_path: Path) -> list:
#         """Find Python modules to mutate"""
#         modules = []
        
#         # Find all .py files in src/
#         src_dir = sut_path / 'src'
#         if src_dir.exists():
#             for py_file in src_dir.rglob('*.py'):
#                 if py_file.name != '__init__.py':
#                     # Convert path to module name
#                     rel_path = py_file.relative_to(sut_path)
#                     module = str(rel_path.with_suffix('')).replace('/', '.')
#                     modules.append(module)
        
#         return modules[:3]  # Limit to 3 modules for demo
    
#     def _simulate_mutation_testing(self, sut_path: Path, module_count: int) -> Dict:
#         """
#         Simulate mutation testing results
        
#         In production, this would run actual MutPy:
#         mut.py --target MODULE --unit-test TEST_FILE --runner pytest
        
#         For demo, we generate realistic statistics
#         """
        
#         # Estimate mutants based on code size
#         py_files = list(sut_path.rglob('*.py'))
#         total_lines = 0
        
#         for py_file in py_files:
#             try:
#                 total_lines += len(py_file.read_text().splitlines())
#             except:
#                 pass
        
#         # Realistic mutation estimates
#         # ~1 mutant per 3 lines of code
#         total_mutants = max(30, total_lines // 3)
        
#         # Simulate detection rates
#         # Good test suite kills 85-95% of mutants
#         import random
#         random.seed(42)  # Deterministic for demo
        
#         killed = int(total_mutants * (0.88 + random.random() * 0.07))  # 88-95%
#         timeout = int(total_mutants * 0.02)  # 2% timeout
#         survived = total_mutants - killed - timeout
        
#         mutation_score = (killed / total_mutants * 100) if total_mutants > 0 else 0
        
#         return {
#             'total_mutants': total_mutants,
#             'killed': killed,
#             'survived': survived,
#             'timeout': timeout,
#             'mutation_score': mutation_score,
#             'method': 'simulated'  # In production: 'mutpy'
#         }











"""
Mutation Tester - VERSION RÉELLE (MutPy)
Exécute une véritable campagne de mutation sur le code source.
"""
import subprocess
import re
import sys
import os
from pathlib import Path
from typing import Dict

class MutationTester:
    def __init__(self):
        pass

    def run_mutation_testing(self, sut_path: Path, test_file: Path) -> Dict:
        """
        AXE 4 : Lancement de MutPy via subprocess.
        """
        print(f"\n🧬 ANALYSE DE MUTATION RÉELLE (MUTPY)")
        
        # 1. Identification du module à muter
        # MutPy a besoin du chemin vers le fichier source principal
        target_file = self._find_main_source(sut_path)
        if not target_file:
            print("❌ Erreur : Aucun fichier source .py trouvé.")
            return {"mutation_score": 0.0, "status": "FAILED"}

        # 2. Préparation de la commande
        # mut.py --target [source] --unit-test [test_file] --runner pytest
        cmd = [
            sys.executable.replace("python", "mut.py"), # Trouve l'exécutable mut.py
            "--target", str(target_file),
            "--unit-test", str(test_file),
            "--runner", "pytest"
        ]

        print(f"🔬 MutPy : Analyse de {target_file.name} avec {test_file.name}...")

        try:
            # 3. Exécution réelle de MutPy
            # On définit le PYTHONPATH pour que MutPy trouve les modules du projet
            env = os.environ.copy()
            env["PYTHONPATH"] = str(sut_path) + os.pathsep + env.get("PYTHONPATH", "")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120, # Délai max car la mutation est gourmande
                env=env
            )
            
            # 4. Extraction du score depuis la sortie console de MutPy
            # MutPy affiche typiquement : "Mutation score [0.123 s]: 85.0%"
            output = result.stdout
            score_match = re.search(r"Mutation score \[.*\]: (\d+\.\d+)%", output)
            
            if score_match:
                score = float(score_match.group(1))
                print(f"✅ Score de Mutation Réel : {score}%")
                return {
                    "mutation_score": score,
                    "total_mutants": output.count("all:"),
                    "killed": output.count("killed:"),
                    "status": "SUCCESS"
                }
            else:
                print("⚠️  MutPy n'a pas pu calculer de score. Vérifiez les tests.")
                return {"mutation_score": 0.0, "status": "NO_SCORE"}

        except subprocess.TimeoutExpired:
            print("❌ Erreur : Temps d'exécution MutPy dépassé.")
            return {"mutation_score": 0.0, "status": "TIMEOUT"}
        except Exception as e:
            print(f"❌ Erreur système : {e}")
            return {"mutation_score": 0.0, "status": "ERROR"}

    def _find_main_source(self, sut_path: Path) -> Path:
        """Trouve le fichier source principal dans le dossier du SUT"""
        for py_file in sut_path.rglob("*.py"):
            if py_file.name not in ["__init__.py", "test_generated.py"]:
                return py_file
        return None