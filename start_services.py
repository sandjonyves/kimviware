#!/usr/bin/env python3
"""
Start all KIMVIWARE phase services
"""

import subprocess
import time
import sys
import os
from pathlib import Path

class ServiceStarter:
    def __init__(self):
        self.base_path = Path('/home/davie/KIMVIWARE')
        self.venv = self.base_path / 'venv_kimvieware/bin/python'
        self.processes = {}
    
    def start_service(self, name: str, service_path: str, script_name: str = 'src/worker.py') -> bool:
        """Start a single service"""
        script = Path(service_path) / script_name
        
        if not script.exists():
            # Try alternative names
            for alt_name in ['src/extractor_service.py', 'src/*_service.py']:
                alts = Path(service_path).glob(alt_name)
                for alt in alts:
                    if '_service' in alt.name:
                        script = alt
                        break
        
        if not script.exists():
            print(f"❌ {name}: Script not found at {script}")
            return False
        
        print(f"🚀 Starting {name}...")
        try:
            # Set environment variables
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Start service in background
            proc = subprocess.Popen(
                [str(self.venv), str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            
            self.processes[name] = proc
            print(f"✅ {name} started (PID: {proc.pid})")
            return True
        except Exception as e:
            print(f"❌ {name}: {e}")
            return False
    
    def start_all(self):
        """Start all phase services"""
        print("\n" + "="*80)
        print("  🎯 STARTING KIMVIWARE PHASE SERVICES")
        print("="*80 + "\n")
        
        services = [
            ('Phase 0 - Validator', '/home/davie/KIMVIWARE/kimvieware-phase0-validator', 'src/validator_service.py'),
            ('Phase 1 - Extractor', '/home/davie/KIMVIWARE/kimvieware-phase1-extractor', 'src/worker.py'),
            ('Phase 2 - SGATS', '/home/davie/KIMVIWARE/kimvieware-phase2-sgats', 'src/sgats_service.py'),
            ('Phase 3 - EvoPath', '/home/davie/KIMVIWARE/kimvieware-phase3-evopath', 'src/evopath_service.py'),
            ('Phase 4 - Executor', '/home/davie/KIMVIWARE/kimvieware-phase4-executor', 'src/executor_service.py'),
        ]
        
        started_count = 0
        for name, path, script in services:
            if self.start_service(name, path, script):
                started_count += 1
            time.sleep(1)  # Give each service time to start
        
        print(f"\n✅ Started {started_count}/{len(services)} services\n")
        
        # Monitor services
        print("="*80)
        print("  📊 SERVICE MONITORING")
        print("="*80 + "\n")
        
        try:
            while True:
                alive = 0
                for name, proc in self.processes.items():
                    if proc.poll() is None:  # Still running
                        alive += 1
                        status = "✅ Running"
                    else:
                        status = f"❌ Stopped (code: {proc.returncode})"
                    
                    print(f"  {name:<30} {status}")
                
                if alive == 0:
                    print("\n⚠️  All services have stopped!")
                    break
                
                print(f"\n  Active: {alive}/{len(self.processes)} services")
                print("  (Press Ctrl+C to stop)\n")
                
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all services...")
            self.stop_all()
    
    def stop_all(self):
        """Stop all services"""
        for name, proc in self.processes.items():
            if proc.poll() is None:
                print(f"  Stopping {name}...", end=" ")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print("✅")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print("❌ (force killed)")

def main():
    starter = ServiceStarter()
    try:
        starter.start_all()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
