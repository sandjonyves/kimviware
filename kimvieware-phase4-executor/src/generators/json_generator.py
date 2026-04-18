"""
JSON Test Case Generator
Converts trajectories to JSON test cases
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'kimvieware-shared' / 'src'))
from kimvieware_shared.models import Trajectory


class JSONTestGenerator:
    """Generate JSON test cases from trajectories"""
    
    def __init__(self):
        pass
    
    def generate(self, trajectories: List[Trajectory], output_dir: Path, base_url: str = "http://localhost:8000") -> Path:
        """
        Generate JSON test cases file
        
        Args:
            trajectories: List of trajectory objects
            output_dir: Output directory
            base_url: Base URL for the SUT
        
        Returns:
            Path to generated JSON file
        """
        
        output_dir.mkdir(parents=True, exist_ok=True)
        json_file = output_dir / 'test_cases.json'
        
        print(f"\n🔧 Generating JSON test cases from {len(trajectories)} trajectories...")
        
        # Build complete JSON structure
        test_suite = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_tests": len(trajectories),
                "base_url": base_url,
                "version": "2.0"
            },
            "test_cases": []
        }
        
        # Convert each trajectory to JSON test case
        for traj in trajectories:
            test_case = self._trajectory_to_json(traj, base_url)
            test_suite["test_cases"].append(test_case)
        
        # Write JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_suite, f, indent=2, ensure_ascii=False)
        
        # Also save a pretty version for humans
        pretty_file = output_dir / 'test_cases_pretty.json'
        with open(pretty_file, 'w', encoding='utf-8') as f:
            json.dump(test_suite, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated: {json_file}")
        print(f"   {len(trajectories)} test cases in JSON format")
        
        return json_file
    
    def _trajectory_to_json(self, traj: Trajectory, base_url: str) -> Dict[str, Any]:
        """Convert a single trajectory to JSON test case"""
        
        # Extract data from trajectory
        input_data = self._extract_input_data(traj)
        expected = self._extract_expected_output(traj)
        method = self._infer_http_method(traj)
        endpoint = self._infer_endpoint(traj)
        
        # Get branches as list
        branches = list(traj.branches_covered) if hasattr(traj, 'branches_covered') else []
        
        return {
            "test_id": traj.path_id,
            "description": self._generate_description(traj),
            "branches_covered": branches[:15],  # Limit for readability
            "branches_count": len(branches),
            "cost": traj.cost if hasattr(traj, 'cost') else 0.0,
            "request": {
                "method": method,
                "url": f"{base_url}{endpoint}",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "body": input_data
            },
            "expected": expected
        }
    
    def _extract_input_data(self, traj: Trajectory) -> Dict[str, Any]:
        """Extract input data from trajectory"""
        
        # If trajectory has real input data, use it
        if hasattr(traj, 'input_data') and traj.input_data:
            return traj.input_data
        
        # Otherwise, infer from path_id or branches
        branches = str(traj.branches_covered).lower() if hasattr(traj, 'branches_covered') else ""
        
        # Infer from path_id (common pattern)
        path_id = traj.path_id.lower() if hasattr(traj, 'path_id') else ""
        
        if 'post' in branches or 'create' in path_id:
            return {
                "action": "create",
                "data": {
                    "name": f"test_{traj.path_id}",
                    "value": "sample_value"
                }
            }
        elif 'put' in branches or 'update' in path_id:
            return {
                "action": "update",
                "id": 1,
                "data": {
                    "name": "updated_name",
                    "value": "updated_value"
                }
            }
        elif 'delete' in branches or 'remove' in path_id:
            return {
                "action": "delete",
                "id": 1
            }
        elif 'login' in path_id or 'auth' in branches:
            return {
                "username": "testuser",
                "password": "testpass123"
            }
        elif 'register' in path_id:
            return {
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "password123"
            }
        else:  # GET or default
            return {
                "params": {
                    "limit": 10,
                    "offset": 0
                }
            }
    
    def _extract_expected_output(self, traj: Trajectory) -> Dict[str, Any]:
        """Extract expected output from trajectory"""
        
        # If trajectory has real expected output, use it
        if hasattr(traj, 'output_expected') and traj.output_expected:
            return traj.output_expected
        
        # Otherwise, infer from branches
        branches = str(traj.branches_covered).lower() if hasattr(traj, 'branches_covered') else ""
        
        if 'success' in branches or 'valid' in branches:
            return {
                "status_code": 200,
                "body": {"status": "success", "message": "Operation completed"}
            }
        elif 'created' in branches:
            return {
                "status_code": 201,
                "body": {"status": "created", "id": "any"}
            }
        elif 'error' in branches or 'invalid' in branches:
            return {
                "status_code": 400,
                "body": {"status": "error", "message": "Invalid input"}
            }
        elif 'unauthorized' in branches or 'forbidden' in branches:
            return {
                "status_code": 401,
                "body": {"status": "error", "message": "Unauthorized access"}
            }
        elif 'not_found' in branches:
            return {
                "status_code": 404,
                "body": {"status": "error", "message": "Resource not found"}
            }
        elif 'conflict' in branches:
            return {
                "status_code": 409,
                "body": {"status": "error", "message": "Resource already exists"}
            }
        
        # Default
        return {
            "status_code": 200,
            "body": {"status": "ok"}
        }
    
    def _infer_http_method(self, traj: Trajectory) -> str:
        """Infer HTTP method from trajectory branches or path_id"""
        
        branches = str(traj.branches_covered).lower() if hasattr(traj, 'branches_covered') else ""
        path_id = traj.path_id.lower() if hasattr(traj, 'path_id') else ""
        
        if 'post' in branches or 'create' in path_id:
            return "POST"
        elif 'put' in branches or 'update' in path_id:
            return "PUT"
        elif 'delete' in branches or 'remove' in path_id:
            return "DELETE"
        elif 'patch' in branches:
            return "PATCH"
        else:
            return "GET"
    
    def _infer_endpoint(self, traj: Trajectory) -> str:
        """Infer API endpoint from trajectory"""
        
        branches = str(traj.branches_covered).lower() if hasattr(traj, 'branches_covered') else ""
        path_id = traj.path_id.lower() if hasattr(traj, 'path_id') else ""
        
        # Common REST endpoints
        if 'post' in branches or 'posts' in path_id:
            return "/api/posts"
        elif 'comment' in branches:
            return "/api/comments"
        elif 'user' in branches or 'auth' in path_id:
            return "/api/users"
        elif 'login' in path_id:
            return "/api/auth/login"
        elif 'register' in path_id:
            return "/api/auth/register"
        elif 'verify' in path_id:
            return "/api/auth/verify"
        elif 'health' in path_id:
            return "/health"
        else:
            return "/api/endpoint"
    
    def _generate_description(self, traj: Trajectory) -> str:
        """Generate a human-readable description for the test"""
        
        method = self._infer_http_method(traj)
        endpoint = self._infer_endpoint(traj)
        branches_count = len(traj.branches_covered) if hasattr(traj, 'branches_covered') else 0
        
        return f"{method} {endpoint} - Test case with {branches_count} branches covered"