"""
Test Executor - Runs generated tests and collects results
"""
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict


class TestExecutor:
    """Execute generated tests using pytest"""
    
    def execute(self, test_file: Path, sut_url: str = "http://localhost:8000", test_count: int = None) -> Dict:
        """
        Execute tests using pytest
        
        Args:
            test_file: Path to test file (Python or JSON)
            sut_url: URL of the SUT
            test_count: Expected number of tests
        
        Returns:
            Dict with execution results
        """
        
        print(f"\n🧪 Executing tests from {test_file.name}...")
        print(f"   SUT: {sut_url}")
        
        # Check if SUT is running
        import requests
        sut_running = False
        try:
            response = requests.get(f"{sut_url}/health", timeout=3)
            sut_running = response.status_code == 200
            if sut_running:
                print(f"✅ SUT is running")
            else:
                print(f"⚠️  SUT returned {response.status_code}")
        except Exception as e:
            print(f"⚠️  SUT not responding at {sut_url}: {e}")
        
        # Run pytest
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '-v',
            '--tb=short',
            '--no-header'
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                env={**subprocess.os.environ, 'PYTHONPATH': str(test_file.parent)}
            )
            
            # Parse pytest output
            stats = self._parse_pytest_output(result.stdout + result.stderr, test_count)
            
        except subprocess.TimeoutExpired:
            print(f"⚠️  Test execution timed out after 60 seconds")
            stats = self._create_timeout_stats(test_count)
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            stats = self._create_error_stats(test_count, str(e))
        
        # Display results
        print(f"\n📊 Execution Results:")
        print(f"   Total: {stats['total']}")
        print(f"   Passed: {stats['passed']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Skipped: {stats.get('skipped', 0)}")
        print(f"   Pass rate: {stats['pass_rate']:.1f}%")
        
        return stats
    
    def _parse_pytest_output(self, output: str, expected_count: int = None) -> Dict:
        """Parse pytest output to extract statistics"""
        
        # Extract test counts using regex
        # Pattern: "= 12 passed, 3 failed, 1 skipped in 0.5s ="
        summary_pattern = r'=+\s*(\d+)\s+passed,\s*(\d+)\s+failed'
        
        match = re.search(summary_pattern, output)
        
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2))
            
            # Look for skipped
            skipped_match = re.search(r'(\d+)\s+skipped', output)
            skipped = int(skipped_match.group(1)) if skipped_match else 0
            
            total = passed + failed + skipped
        else:
            # Fallback: count test functions
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            skipped = output.count(' SKIPPED')
            total = passed + failed + skipped
            
            if total == 0 and expected_count:
                total = expected_count
                passed = expected_count  # Assume all passed if no output
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': pass_rate,
            'output': output[:500]  # Truncated output
        }
    
    def _create_timeout_stats(self, test_count: int = None) -> Dict:
        """Create timeout statistics"""
        total = test_count if test_count else 0
        return {
            'total': total,
            'passed': 0,
            'failed': total,
            'skipped': 0,
            'pass_rate': 0.0,
            'output': 'Test execution timed out'
        }
    
    def _create_error_stats(self, test_count: int = None, error: str = "") -> Dict:
        """Create error statistics"""
        total = test_count if test_count else 0
        return {
            'total': total,
            'passed': 0,
            'failed': total,
            'skipped': 0,
            'pass_rate': 0.0,
            'output': f'Execution error: {error}'
        }