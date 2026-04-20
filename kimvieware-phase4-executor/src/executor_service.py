"""
Phase 4: Test Executor Service

Consumes: optimization.completed
Produces: execution.completed
"""
import sys
from pathlib import Path
import tempfile
import json
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'kimvieware-shared' / 'src'))

from kimvieware_shared import MicroserviceBase, JobStatus, Trajectory
from generators.json_generator import JSONTestGenerator
from executors.test_executor import TestExecutor
from executors.mutation_tester import MutationTester


class ExecutorService(MicroserviceBase):
    """Phase 4: Test Execution and Mutation Testing"""
    
    # 📁 Dossier pour sauvegarder les test cases (à la racine du projet)
    TEST_CASES_DIR = Path(__file__).parent.parent.parent / "test_cases"
    
    def __init__(self):
        super().__init__(
            service_name="Phase4_Executor",
            input_queue="optimization.completed",
            output_queue="execution.completed"
        )
        
        self.json_generator = JSONTestGenerator()
        self.test_executor = TestExecutor()
        self.mutation_tester = MutationTester()
        
        # Créer le dossier test_cases s'il n'existe pas
        self.TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📁 Test cases directory: {self.TEST_CASES_DIR}")
    
    def process_message(self, message: dict) -> dict:
        """Execute tests and perform mutation analysis"""
        
        job_id = message['job_id']
        
        # Only process optimized jobs
        if message.get('status') != 'optimized':
            self.logger.warning(f"[{job_id}] Skipping: not optimized")
            return message
        
        trajectories_data = message.get('trajectories', [])
        sut_info = message['sut_info']
        
        # Extract port from metadata or default to 8000
        sut_port = message.get('metadata', {}).get('port', 8000)
        sut_url = f"http://localhost:{sut_port}"
        
        # Extract SUT path for mutation testing
        extracted_path = message.get('extracted_path', '/tmp/kimvieware_validator/' + job_id)
        sut_path = Path(extracted_path)
        
        if not trajectories_data:
            return self._error(job_id, "No trajectories to execute")
        
        self.logger.info(f"[{job_id}] Phase 4: Executing {len(trajectories_data)} trajectories on {sut_url}")
        
        # Reconstruct Trajectory objects
        trajectories = [Trajectory.from_dict(t) for t in trajectories_data]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            try:
                # Step 1: Generate JSON test cases
                json_file = self.json_generator.generate(trajectories, output_dir, sut_url)
                
                # Step 2: Generate executable test runner from JSON
                test_runner = self._generate_test_runner(json_file, output_dir)
                
                # Step 3: Execute tests
                exec_stats = self.test_executor.execute(
                    test_runner, 
                    sut_url=sut_url, 
                    test_count=len(trajectories)
                )
                
                # Step 4: Mutation testing on real SUT code
                mutation_stats = self.mutation_tester.run_mutation_testing(
                    sut_path=sut_path,
                    test_file=test_runner
                )
                
            except Exception as e:
                self.logger.error(f"[{job_id}] Execution failed: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return self._error(job_id, str(e))
        
        self.logger.info(
            f"[{job_id}] ✅ Execution: {exec_stats['passed']}/{exec_stats['total']} passed, "
            f"Mutation: {mutation_stats['mutation_score']:.1f}%"
        )
        
        # Sauvegarder les test cases JSON dans le dossier permanent
        test_cases_file = self._export_test_cases(trajectories, job_id, exec_stats, mutation_stats)
        
        # Return result - KEEP ALL DATA FROM PREVIOUS PHASES
        return {
            'job_id': job_id,
            'status': JobStatus.COMPLETED.value,
            'sut_info': sut_info,
            # IMPORTANT: Keep ALL previous phase data for dashboard
            'extraction_count': message.get('extraction_count'),
            'original_trajectories': message.get('original_trajectories'),
            'sgats_stats': message.get('sgats_stats'),
            'evopath_stats': message.get('evopath_stats'),
            'execution_stats': exec_stats,
            'mutation_stats': mutation_stats,
            'trajectories_count': len(trajectories),
            'trajectories': [t.to_dict() for t in trajectories],
            'test_cases_file': str(test_cases_file) if test_cases_file else None,
            'metadata': {
                'phase': 'execution',
                'test_count': len(trajectories),
                'json_generated': True
            }
        }
    
    def _generate_test_runner(self, json_file: Path, output_dir: Path) -> Path:
        """Generate a test file compatible with MutPy"""
        
        runner_code = f'''"""
Test Runner for MutPy - Executes test cases from JSON
Auto-generated by KIMVIEware Phase 4
"""
import json
import pytest
import requests
from pathlib import Path

JSON_FILE = Path("{json_file}")

def load_test_cases():
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

test_suite = load_test_cases()


# Test function that runs all cases (MutPy compatible)
@pytest.mark.parametrize("test_case", test_suite["test_cases"])
def test_all_cases(test_case):
    """Single test function that runs all cases (MutPy compatible)"""
    request_data = test_case["request"]
    expected = test_case["expected"]
    
    response = requests.request(
        method=request_data["method"],
        url=request_data["url"],
        json=request_data.get("body"),
        headers=request_data.get("headers", {{}}),
        timeout=10
    )
    
    assert response.status_code == expected["status_code"], \\
        f"Expected status {{expected['status_code']}}, got {{response.status_code}}"
    
    if "body" in expected and expected["body"]:
        response_data = response.json() if response.content else {{}}
        for key, value in expected["body"].items():
            if value == "any":
                assert key in response_data, f"Missing '{{key}}' in response"
            else:
                assert response_data.get(key) == value, \\
                    f"Expected '{{key}}' = {{value}}, got {{response_data.get(key)}}"


# Individual test functions for better reporting
def test_summary():
    """Print summary of loaded test cases"""
    print(f"\\n📋 Loaded {{len(test_suite['test_cases'])}} test cases")
    print(f"   Generated: {{test_suite['metadata']['generated_at']}}")
    print(f"   Base URL: {{test_suite['metadata']['base_url']}}")
    print(f"   Test IDs:")
    for tc in test_suite['test_cases']:
        print(f"      - {{tc['test_id']}} ({{tc['request']['method']}} {{tc['request']['url']}})")


# Create individual test functions using a closure
def create_test_function(test_id, request_data, expected):
    """Factory function that creates a test function for a specific test case"""
    def test_func():
        response = requests.request(
            method=request_data["method"],
            url=request_data["url"],
            json=request_data.get("body"),
            headers=request_data.get("headers", {{}}),
            timeout=10
        )
        assert response.status_code == expected["status_code"], \\
            f"Expected status {{expected['status_code']}}, got {{response.status_code}}"
    
    test_func.__name__ = f"test_{{test_id}}"
    test_func.__doc__ = f"Test for {{test_id}}: {{request_data['method']}} {{request_data['url']}}"
    return test_func


# Dynamically create individual test functions
for test_case in test_suite["test_cases"]:
    test_id = test_case["test_id"]
    request_data = test_case["request"]
    expected = test_case["expected"]
    
    # Create and register the test function
    test_func = create_test_function(test_id, request_data, expected)
    globals()[test_func.__name__] = test_func
'''
        
        runner_file = output_dir / 'run_tests.py'
        runner_file.write_text(runner_code)
        
        self.logger.info(f"✅ Generated test runner: {runner_file}")
        
        # Verify the generated file is valid
        try:
            import ast
            with open(runner_file, 'r') as f:
                ast.parse(f.read())
            self.logger.info(f"   ✅ Test runner syntax is valid")
        except SyntaxError as e:
            self.logger.error(f"   ❌ Generated test runner has syntax error: {e}")
        
        return runner_file
    
    def _export_test_cases(self, trajectories: list, job_id: str, exec_stats: dict, mutation_stats: dict) -> Path:
        """Export test cases as JSON for external analysis - Sauvegarde dans le dossier permanent"""
        
        # Créer un sous-dossier pour ce job
        job_dir = self.TEST_CASES_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        export_file = job_dir / 'test_cases.json'
        
        test_suite = {
            "job_id": job_id,
            "exported_at": datetime.now().isoformat(),
            "total_tests": len(trajectories),
            "execution_stats": {
                "passed": exec_stats.get('passed', 0),
                "failed": exec_stats.get('failed', 0),
                "pass_rate": exec_stats.get('pass_rate', 0)
            },
            "mutation_stats": {
                "score": mutation_stats.get('mutation_score', 0),
                "killed": mutation_stats.get('killed', 0),
                "survived": mutation_stats.get('survived', 0),
                "total_mutants": mutation_stats.get('total_mutants', 0)
            },
            "test_cases": []
        }
        
        for traj in trajectories:
            test_suite["test_cases"].append({
                "test_id": traj.path_id,
                "branches_covered": list(traj.branches_covered) if hasattr(traj, 'branches_covered') else [],
                "branches_count": len(traj.branches_covered) if hasattr(traj, 'branches_covered') else 0,
                "cost": traj.cost if hasattr(traj, 'cost') else 0.0,
                "input_data": traj.input_data if hasattr(traj, 'input_data') else None,
                "output_expected": traj.output_expected if hasattr(traj, 'output_expected') else None
            })
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(test_suite, f, indent=2, ensure_ascii=False)
        
        # Créer aussi un fichier README dans le dossier
        readme_file = job_dir / 'README.md'
        readme_content = f"""# Test Cases pour {job_id}

## 📊 Résumé
- **Date**: {datetime.now().isoformat()}
- **Nombre de tests**: {len(trajectories)}
- **Taux de réussite**: {exec_stats.get('pass_rate', 0):.1f}%
- **Score de mutation**: {mutation_stats.get('mutation_score', 0):.1f}%

## 📁 Fichiers
- `test_cases.json` - Les cas de test au format JSON

## 🔍 Visualisation
Tu peux visualiser ce fichier JSON avec n'importe quel éditeur de texte ou outil JSON.
"""
        readme_file.write_text(readme_content)
        
        self.logger.info(f"💾 Exported test cases: {export_file}")
        self.logger.info(f"📁 Dossier: {job_dir}")
        
        return export_file
    
    def _error(self, job_id: str, msg: str) -> dict:
        return {
            'job_id': job_id,
            'status': JobStatus.FAILED.value,
            'error': msg,
            'phase': 'execution'
        }


if __name__ == "__main__":
    service = ExecutorService()
    service.start()