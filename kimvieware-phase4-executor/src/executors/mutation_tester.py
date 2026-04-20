"""
Mutation Testing - Real data from actual code
"""
import subprocess
import re
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional


class MutationTester:
    """Mutation Testing using real code from the SUT"""
    
    def __init__(self):
        self.has_mutpy = self._check_mutpy()
        self.mutpy_cmd = self._find_mutpy_command()
    
    def _check_mutpy(self) -> bool:
        try:
            import mutpy
            print(f"✅ MutPy {mutpy.__version__} found")
            return True
        except ImportError:
            print(f"❌ MutPy not found")
            return False
    
    def _find_mutpy_command(self) -> Optional[str]:
        """Find the correct path to mut.py"""
        
        # First, try to find mut.py in the virtual environment bin directory
        env_bin = Path(sys.executable).parent
        mutpy_path = env_bin / 'mut.py'
        
        if mutpy_path.exists():
            print(f"✅ Found mut.py at: {mutpy_path}")
            return str(mutpy_path)
        
        # Try other possible locations
        possible_paths = [
            Path('/home/mouope/Documents/MASTER1/SEMESTRE 2/INF4098/kimviware/env/bin/mut.py'),
            Path(sys.executable).parent / 'mut.py',
            Path('/usr/local/bin/mut.py'),
            Path('/usr/bin/mut.py'),
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"✅ Found mut.py at: {path}")
                return str(path)
        
        # Try which command
        try:
            result = subprocess.run(
                ['which', 'mut.py'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                print(f"✅ Found mut.py via which: {path}")
                return path
        except:
            pass
        
        print(f"❌ Could not find mut.py command")
        return None
    
    def run_mutation_testing(
        self,
        sut_path: Path,
        test_file: Path,
        target_modules: Optional[List[str]] = None
    ) -> Dict:
        
        print(f"\n🧬 MUTATION TESTING (REAL CODE)")
        print(f"{'='*60}")
        print(f"SUT: {sut_path}")
        print(f"Tests: {test_file}")
        
        if not self.has_mutpy:
            return {
                'total_mutants': 0,
                'killed': 0,
                'survived': 0,
                'mutation_score': 0.0,
                'error': 'MutPy not installed',
                'message': '❌ IMPOSSIBLE: MutPy is not installed. Run: pip install mutpy'
            }
        
        if not self.mutpy_cmd:
            return {
                'total_mutants': 0,
                'killed': 0,
                'survived': 0,
                'mutation_score': 0.0,
                'error': 'mut.py not found',
                'message': '❌ IMPOSSIBLE: mut.py command not found even though MutPy is installed'
            }
        
        # Find real Python modules in the SUT
        if not target_modules:
            target_modules = self._find_real_python_modules(sut_path)
        
        if not target_modules:
            return {
                'total_mutants': 0,
                'killed': 0,
                'survived': 0,
                'mutation_score': 0.0,
                'error': 'No Python modules found',
                'message': '❌ IMPOSSIBLE: No Python modules with executable logic found in SUT'
            }
        
        print(f"Found {len(target_modules)} Python module(s)")
        
        # Try each module
        all_stats = {
            'total_mutants': 0,
            'killed': 0,
            'survived': 0,
            'modules_tested': [],
            'failed_modules': []
        }
        
        for module in target_modules:
            print(f"\n   📦 Testing: {module}")
            stats = self._try_mutate_module(sut_path, test_file, module)
            
            if stats.get('error'):
                print(f"      ❌ {stats['message']}")
                all_stats['failed_modules'].append({
                    'module': module,
                    'error': stats['error'],
                    'message': stats['message']
                })
            else:
                all_stats['total_mutants'] += stats['total_mutants']
                all_stats['killed'] += stats['killed']
                all_stats['survived'] += stats['survived']
                all_stats['modules_tested'].append({
                    'module': module,
                    'mutants': stats['total_mutants'],
                    'killed': stats['killed'],
                    'score': stats['mutation_score']
                })
                print(f"      ✅ {stats['killed']}/{stats['total_mutants']} killed ({stats['mutation_score']:.1f}%)")
        
        # Calculate final score
        if all_stats['total_mutants'] > 0:
            all_stats['mutation_score'] = (all_stats['killed'] / all_stats['total_mutants']) * 100
            all_stats['status'] = 'SUCCESS'
        elif all_stats['modules_tested']:
            all_stats['mutation_score'] = 0
            all_stats['status'] = 'PARTIAL'
            all_stats['message'] = '⚠️ Modules found but no mutants generated (code may have no mutable statements)'
        else:
            all_stats['mutation_score'] = 0
            all_stats['status'] = 'FAILED'
            all_stats['message'] = '❌ IMPOSSIBLE: Could not generate mutants for any module'
        
        self._display_results(all_stats)
        return all_stats
    
    def _find_real_python_modules(self, sut_path: Path) -> List[str]:
        """Find real Python modules with actual logic"""
        modules = []
        
        print(f"   🔍 Searching for Python files in: {sut_path}")
        
        for py_file in sut_path.rglob('*.py'):
            # Skip Django/Flask boilerplate
            skip_patterns = [
                '__init__', 'test_', 'conftest', 'setup', 'manage', 
                'migrations', 'apps.py', 'admin.py', 'wsgi.py', 'asgi.py',
                'urls.py', 'settings.py', 'serializers.py', 'permissions.py',
                'validators.py', 'forms.py', 'middleware.py'
            ]
            
            if any(pattern in py_file.name for pattern in skip_patterns):
                continue
            
            # Check if file has actual logic
            try:
                content = py_file.read_text()
                # Look for functions, classes, or logic
                has_functions = bool(re.search(r'^\s*def\s+\w+\s*\(', content, re.MULTILINE))
                has_classes = bool(re.search(r'^\s*class\s+\w+', content, re.MULTILINE))
                has_logic = bool(re.search(r'\bif\b|\bfor\b|\bwhile\b|\breturn\b', content))
                
                if has_functions or (has_classes and has_logic):
                    rel_path = py_file.relative_to(sut_path)
                    module = str(rel_path.with_suffix('')).replace('/', '.').replace('\\', '.')
                    module = module.replace('-', '_')
                    if module and not module.startswith('.'):
                        modules.append(module)
                        print(f"      ✅ Found: {module} ({py_file.name})")
            except:
                pass
        
        return list(set(modules))[:5]
    
    def _try_mutate_module(self, sut_path: Path, test_file: Path, module: str) -> Dict:
        """Try to generate mutants for a module"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            output_file = Path(tmp.name)
        
        try:
            # Set up environment
            env = os.environ.copy()
            pythonpath = str(sut_path)
            if 'PYTHONPATH' in env:
                pythonpath = pythonpath + os.pathsep + env['PYTHONPATH']
            env['PYTHONPATH'] = pythonpath
            
            # Use mut.py directly
            cmd = [
                sys.executable,
                '-m',
                'mutpy',
                '--target', module,
                '--unit-test', str(test_file),
                '--runner', 'pytest'
            ]
            
            print(f"   Running: {self.mutpy_cmd} --target {module}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(sut_path),
                env=env
            )
            
            output_file.write_text(result.stdout + result.stderr)
            output = result.stdout + result.stderr
            
            # Check for specific error messages
            if "No module named" in output:
                return {
                    'error': 'ImportError',
                    'message': f'❌ IMPOSSIBLE: Module "{module}" cannot be imported (missing dependencies)'
                }
            
            if "No statements to mutate" in output:
                return {
                    'error': 'NoStatements',
                    'message': f'❌ IMPOSSIBLE: No mutable statements found in "{module}" (code may be declarative only)'
                }
            
            # Parse results
            stats = self._parse_mutpy_output(output_file, output)
            
            if stats['total_mutants'] == 0:
                return {
                    'error': 'NoMutants',
                    'message': f'⚠️ No mutants generated for "{module}" (no logical operations to mutate)'
                }
            
            return stats
            
        except subprocess.TimeoutExpired:
            return {
                'error': 'Timeout',
                'message': f'❌ IMPOSSIBLE: Mutation testing timed out for "{module}" (may be too complex)'
            }
        except Exception as e:
            return {
                'error': str(e),
                'message': f'❌ IMPOSSIBLE: Error during mutation: {str(e)}'
            }
        finally:
            if output_file.exists():
                output_file.unlink()
    
    def _parse_mutpy_output(self, output_file: Path, console: str) -> Dict:
        output = console
        if output_file.exists():
            output = output_file.read_text() + "\n" + output
        
        total = 0
        killed = 0
        survived = 0
        
        # Try different patterns
        patterns = [
            (r'(\d+)\s+mutants?\s+generated', 'total'),
            (r'Total\s+mutants?:\s*(\d+)', 'total'),
            (r'Killed\s*:\s*(\d+)', 'killed'),
            (r'Survived\s*:\s*(\d+)', 'survived'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                if key == 'total':
                    total = int(match.group(1))
                elif key == 'killed':
                    killed = int(match.group(1))
                elif key == 'survived':
                    survived = int(match.group(1))
        
        # If we have killed/survived but no total
        if total == 0 and (killed > 0 or survived > 0):
            total = killed + survived
        
        # Try to count from inline results
        if total == 0:
            killed = len(re.findall(r'KILLED', output, re.IGNORECASE))
            survived = len(re.findall(r'SURVIVED', output, re.IGNORECASE))
            total = killed + survived
        
        score = (killed / total * 100) if total > 0 else 0
        
        return {
            'total_mutants': total,
            'killed': killed,
            'survived': survived,
            'mutation_score': score
        }
    
    def _display_results(self, stats: Dict):
        print(f"\n📊 MUTATION TESTING RESULTS")
        print(f"{'='*60}")
        
        if stats.get('status') == 'FAILED':
            print(f"   Status: ❌ FAILED")
            print(f"   Message: {stats.get('message', 'Unknown error')}")
        elif stats.get('status') == 'PARTIAL':
            print(f"   Status: ⚠️ PARTIAL")
            print(f"   Message: {stats.get('message', '')}")
        else:
            print(f"   Status: ✅ COMPLETED")
        
        print(f"   Total mutants: {stats['total_mutants']}")
        print(f"   Killed: {stats['killed']}")
        print(f"   Survived: {stats['survived']}")
        print(f"   Mutation Score: {stats['mutation_score']:.1f}%")
        
        if stats['total_mutants'] > 0:
            score = stats['mutation_score']
            if score >= 90:
                quality = "Excellent"
            elif score >= 80:
                quality = "Good"
            elif score >= 70:
                quality = "Acceptable"
            else:
                quality = "Needs Improvement"
            print(f"   Quality: {quality}")
        
        # Show successful modules
        if stats.get('modules_tested'):
            print(f"\n   ✅ Successful modules ({len(stats['modules_tested'])}):")
            for mod in stats['modules_tested']:
                print(f"      - {mod['module']}: {mod['killed']}/{mod['mutants']} killed ({mod['score']:.1f}%)")
        
        # Show failed modules
        if stats.get('failed_modules'):
            print(f"\n   ❌ Failed modules ({len(stats['failed_modules'])}):")
            for mod in stats['failed_modules']:
                print(f"      - {mod['module']}: {mod['message']}")
        
        print(f"{'='*60}\n")


import logging
MutationTester.logger = logging.getLogger("MutationTester")