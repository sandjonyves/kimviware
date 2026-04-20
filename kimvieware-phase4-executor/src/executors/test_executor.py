# """
# Test Executor
# Runs generated tests and collects results
# """
# import subprocess
# from pathlib import Path
# import json

# class TestExecutor:
#     """Execute generated tests"""
    
#     def execute(self, test_file: Path, sut_url: str = "http://localhost:8000", test_count: int = None) -> dict:
#         """
#         Execute tests using pytest
        
#         Returns:
#             dict with execution results
#         """
        
#         print(f"\n🧪 Executing tests from {test_file.name}...")
#         print(f"   SUT: {sut_url}")
        
#         # Check if SUT is running
#         import requests
#         try:
#             response = requests.get(f"{sut_url}/health", timeout=2)
#             sut_running = response.status_code == 200
#             if sut_running:
#                 print(f"✅ SUT is running")
#             else:
#                 print(f"⚠️  SUT returned {response.status_code}")
#                 sut_running = False
#         except Exception as e:
#             print(f"⚠️  SUT not responding at {sut_url}: {e}")
#             print(f"   Trying with mock SUT...")
#             sut_running = False
        
#         # If SUT not running, use simulated results
#         if not sut_running:
#             return self._simulate_execution(test_file, test_count)
        
#         # Run pytest - with proper error handling
#         import sys
#         cmd = [
#             sys.executable, '-m', 'pytest',
#             str(test_file),
#             '-v',
#             '--tb=short'
#         ]
        
#         # Check if tests exist first
#         collect_cmd = cmd + ['--collect-only']
#         collect_result = subprocess.run(collect_cmd, capture_output=True, text=True, timeout=10)
#         collect_output = collect_result.stdout + collect_result.stderr
        
#         # Count collected tests
#         test_count = collect_output.count('::test_') + collect_output.count('<Function')
        
#         if test_count == 0:
#             print(f"⚠️  No tests collected!")
#             print(f"Collected output: {collect_output[:500]}")
#             return self._simulate_execution(test_file, test_count if test_count > 0 else None)
        
#         # Run actual tests
#         result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
#         # Parse results
#         output = result.stdout + result.stderr
        
#         passed = output.count(' PASSED') or output.count(' passed')
#         failed = output.count(' FAILED') or output.count(' failed')
#         total = passed + failed
        
#         # Debug output
#         if total == 0:
#             print(f"DEBUG: pytest exit code: {result.returncode}")
#             print(f"DEBUG: pytest output:\n{output[:1000]}")
        
#         stats = {
#             'total': max(total, test_count),  # Use collected count if parse failed
#             'passed': passed,
#             'failed': failed,
#             'pass_rate': (passed / total * 100) if total > 0 else 0,
#             'output': output
#         }
        
#         print(f"\n📊 Execution Results:")
#         print(f"   Total: {stats['total']}")
#         print(f"   Passed: {stats['passed']}")
#         print(f"   Failed: {stats['failed']}")
#         print(f"   Pass rate: {stats['pass_rate']:.1f}%")
        
#         return stats
    
#     def _simulate_execution(self, test_file: Path, test_count: int = None) -> dict:
#         """Generate realistic simulated test results based on test file complexity"""
        
#         # Use provided test count or try to extract from file
#         if test_count is None:
#             try:
#                 content = test_file.read_text()
#                 test_count = content.count('def test_')
#             except:
#                 test_count = 50
        
#         # Simulate realistic pass rate (70-95%)
#         import random
#         pass_rate = random.uniform(0.70, 0.95)
#         passed = int(test_count * pass_rate)
#         failed = test_count - passed
        
#         stats = {
#             'total': test_count,
#             'passed': passed,
#             'failed': failed,
#             'pass_rate': pass_rate * 100,
#             'output': f"Simulated: {passed}/{test_count} tests passed"
#         }
        
#         print(f"\n📊 Execution Results (SIMULATED):")
#         print(f"   Total: {stats['total']}")
#         print(f"   Passed: {stats['passed']}")
#         print(f"   Failed: {stats['failed']}")
#         print(f"   Pass rate: {stats['pass_rate']:.1f}%")
        
#         return stats





















"""
Test Executor - VERSION RÉELLE
Exécute les tests via Pytest et analyse les résultats sans simulation.
"""
import subprocess
import sys
import re
import requests
from pathlib import Path

class TestExecutor:
    """Exécuteur de tests professionnel pour KIMVIEware"""
    
    def execute(self, test_file: Path, sut_url: str, test_count: int = None) -> dict:
        """
        Exécute les tests pytest et analyse le rapport de sortie.
        """
        print(f"\n🧪 EXÉCUTION RÉELLE sur : {sut_url}")
        
        # 1. Vérification réelle de la disponibilité du SUT
        sut_running = self._is_sut_available(sut_url)
        
        if not sut_running:
            print("❌ ERREUR : Le SUT ne répond pas. Impossible d'exécuter les tests.")
            return self._error_stats("SUT_UNREACHABLE", test_count)

        # 2. Préparation de la commande Pytest
        # On utilise -q (quiet) et --tb=no pour simplifier l'analyse de la sortie
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "--tb=no",
            "-q"
        ]

        try:
            # 3. Lancement des tests
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr

            # 4. Analyse rigoureuse de la ligne de résumé de Pytest
            # Exemple : "2 passed, 1 failed in 0.12s"
            stats = self._parse_pytest_output(output, test_count)
            
            print(f"📊 Résultats : {stats['passed']} Réussis, {stats['failed']} Échecs")
            return stats

        except Exception as e:
            print(f"❌ Erreur pendant l'exécution : {e}")
            return self._error_stats(str(e), test_count)

    def _is_sut_available(self, url: str) -> bool:
        """Vérifie si le SUT est vivant (Code 200, 401, 404 sont acceptés, mais pas de réponse = Mort)"""
        try:
            # On tente une requête simple. Si le serveur répond, c'est qu'il est lancé.
            requests.get(url, timeout=3)
            return True
        except:
            return False

    def _parse_pytest_output(self, output: str, expected_count: int) -> dict:
        """Extrait les chiffres exacts de la console Pytest via Regex"""
        
        # On cherche le pattern standard de Pytest : "X passed, Y failed, Z error"
        passed = re.search(r"(\d+) passed", output)
        failed = re.search(r"(\d+) failed", output)
        errors = re.search(r"(\d+) error", output)

        n_passed = int(passed.group(1)) if passed else 0
        n_failed = int(failed.group(1)) if failed else 0
        n_errors = int(errors.group(1)) if errors else 0
        
        total = n_passed + n_failed + n_errors
        
        return {
            'total': total if total > 0 else (expected_count or 0),
            'passed': n_passed,
            'failed': n_failed + n_errors,
            'pass_rate': (n_passed / total * 100) if total > 0 else 0,
            'output': output[:500] # On garde un extrait des logs
        }

    def _error_stats(self, reason: str, count: int) -> dict:
        """Retourne un état d'échec réel (Zéro simulation)"""
        return {
            'total': count or 0,
            'passed': 0,
            'failed': count or 0,
            'pass_rate': 0,
            'output': f"Échec de l'exécution : {reason}"
        }