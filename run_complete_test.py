#!/usr/bin/env python3
"""
Complete Multi-Language Test Orchestration & Dashboard
Launches all services and processes multi-language jobs
"""

import subprocess
import time
import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
import pika

class CompleteOrchestratorDashboard:
    def __init__(self):
        self.base_path = Path('/home/davie/KIMVIWARE')
        self.venv = self.base_path / 'venv_kimvieware/bin/python'
        self.processes = {}
        
        # MongoDB connection
        try:
            self.client = MongoClient('mongodb://admin:kimvie2025@localhost:27017/')
            self.db = self.client['kimvieware']
            self.jobs_coll = self.db['jobs']
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            sys.exit(1)
    
    def start_service(self, name: str, service_path: str, script_name: str):
        """Start a service and capture errors"""
        script = Path(service_path) / script_name
        
        if not script.exists():
            print(f"❌ {name}: Script not found at {script}")
            return False
        
        print(f"🚀 {name:<30}", end=" ", flush=True)
        
        try:
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Start with output capture
            proc = subprocess.Popen(
                [str(self.venv), str(script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            self.processes[name] = proc
            time.sleep(1)  # Give it time to start
            
            if proc.poll() is None:  # Still running
                print("✅ Running")
                return True
            else:
                print(f"❌ Crashed (exit code: {proc.returncode})")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def start_all_services(self):
        """Start all phase services"""
        print("\n" + "="*100)
        print("  🎯 STARTING KIMVIWARE SERVICES")
        print("="*100 + "\n")
        
        services = [
            ('Phase 0 - Validator', '/home/davie/KIMVIWARE/kimvieware-phase0-validator', 'src/validator_service.py'),
            ('Phase 1 - Extractor', '/home/davie/KIMVIWARE/kimvieware-phase1-extractor', 'src/worker.py'),
            ('Phase 2 - SGATS', '/home/davie/KIMVIWARE/kimvieware-phase2-sgats', 'src/sgats_service.py'),
            ('Phase 3 - EvoPath', '/home/davie/KIMVIWARE/kimvieware-phase3-evopath', 'src/evopath_service.py'),
            ('Phase 4 - Executor', '/home/davie/KIMVIWARE/kimvieware-phase4-executor', 'src/executor_service.py'),
        ]
        
        started = 0
        for name, path, script in services:
            if self.start_service(name, path, script):
                started += 1
        
        print(f"\n✅ Started {started}/{len(services)} services\n")
        return started == len(services)
    
    def submit_jobs(self):
        """Resubmit jobs to RabbitMQ if not already in queue"""
        print("="*100)
        print("  📤 CHECKING JOBS IN QUEUE")
        print("="*100 + "\n")
        
        try:
            credentials = pika.PlainCredentials('admin', 'kimvie2025')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
            )
            channel = connection.channel()
            
            # Check submission queue
            queue = channel.queue_declare('submission.new', passive=True, durable=True)
            message_count = queue.method.message_count
            
            print(f"📬 Messages in queue 'submission.new': {message_count}")
            
            connection.close()
            
            if message_count > 0:
                print("✅ Jobs already queued for processing\n")
                return True
            else:
                print("⚠️  No messages in queue - this shouldn't happen!\n")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def monitor_jobs(self, timeout_minutes: int = 120):
        """Monitor jobs in real-time"""
        print("="*100)
        print("  📊 REAL-TIME JOB MONITORING")
        print("="*100 + "\n")
        
        job_ids = {
            'Python': '754a8655-db88-4205-bcd2-75d11fc9d306',
            'C': '1e547230-9123-457c-b331-8c5d4e7a4574',
            'Java': 'b9b46a41-4962-4f1b-b22c-d0be5c12b78f'
        }
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        last_status = {}
        
        while time.time() - start_time < timeout_seconds:
            print(f"\033[2J\033[H")  # Clear screen
            
            # Print header
            print("\n" + "="*100)
            print(f"  🎯 MONITORING - {datetime.now().strftime('%H:%M:%S')} | Elapsed: {int((time.time()-start_time)/60)}m")
            print("="*100 + "\n")
            
            all_done = True
            for language, job_id in job_ids.items():
                try:
                    job = self.jobs_coll.find_one({'_id': job_id})
                    
                    if not job:
                        print(f"  ⏳ {language:<10} - Waiting for job to be created")
                        all_done = False
                        continue
                    
                    status = job.get('status', 'unknown')
                    phase = job.get('current_phase', '—')
                    phases = job.get('phases', {})
                    
                    # Status emoji
                    if status == 'completed':
                        status_icon = "✅"
                        print(f"  {status_icon} {language:<10} - COMPLETED")
                    elif status == 'running':
                        status_icon = "⏳"
                        print(f"  {status_icon} {language:<10} - Running Phase {phase}")
                        all_done = False
                    elif status == 'failed':
                        status_icon = "❌"
                        print(f"  {status_icon} {language:<10} - FAILED: {job.get('error', 'Unknown error')}")
                        all_done = False
                    else:
                        status_icon = "ℹ️ "
                        print(f"  {status_icon} {language:<10} - {status}")
                        all_done = False
                    
                    # Show phase details if available
                    if phases.get('phase1') and phases['phase1'].get('trajectories_count'):
                        p1 = phases['phase1']['trajectories_count']
                        print(f"     ✓ Phase 1: {p1} trajectories")
                    
                    if phases.get('phase2') and phases['phase2'].get('reduced_trajectories_count'):
                        p2 = phases['phase2']['reduced_trajectories_count']
                        p1 = phases.get('phase1', {}).get('trajectories_count', 1)
                        reduction = 100 * (p1 - p2) / p1 if p1 > 0 else 0
                        print(f"     ✓ Phase 2: {p2} trajectories ({reduction:.1f}% reduction)")
                    
                    if phases.get('phase3') and phases['phase3'].get('optimized_trajectories_count'):
                        p3 = phases['phase3']['optimized_trajectories_count']
                        p2 = phases.get('phase2', {}).get('reduced_trajectories_count', 1)
                        additional = 100 * (p2 - p3) / p2 if p2 > 0 else 0
                        print(f"     ✓ Phase 3: {p3} trajectories ({additional:.1f}% optimization)")
                    
                    if phases.get('phase4') and phases['phase4'].get('mutation_score'):
                        mutation = phases['phase4']['mutation_score']
                        print(f"     ✓ Phase 4: {mutation:.1%} mutation score")
                    
                    print()
                
                except Exception as e:
                    print(f"  ❌ {language:<10} - Error: {e}\n")
                    all_done = False
            
            if all_done:
                print("✅ All jobs completed!\n")
                break
            
            # Wait before next check
            time.sleep(5)
        
        return all_done
    
    def display_final_results(self):
        """Display final results"""
        print("\n" + "="*100)
        print("  🎯 FINAL MULTI-LANGUAGE TEST RESULTS")
        print("="*100 + "\n")
        
        job_ids = {
            'Python': '754a8655-db88-4205-bcd2-75d11fc9d306',
            'C': '1e547230-9123-457c-b331-8c5d4e7a4574',
            'Java': 'b9b46a41-4962-4f1b-b22c-d0be5c12b78f'
        }
        
        # Fetch results
        results = {}
        for language, job_id in job_ids.items():
            try:
                job = self.jobs_coll.find_one({'_id': job_id})
                if job:
                    phases = job.get('phases', {})
                    results[language] = {
                        'status': job.get('status', 'unknown'),
                        'p1': phases.get('phase1', {}).get('trajectories_count', 0),
                        'p2': phases.get('phase2', {}).get('reduced_trajectories_count', 0),
                        'p3': phases.get('phase3', {}).get('optimized_trajectories_count', 0),
                        'p4': phases.get('phase4', {}).get('mutation_score', 0)
                    }
            except:
                results[language] = {'status': 'unknown'}
        
        # Print summary table
        print(f"{'Language':<12} {'Status':<12} {'Phase 1':<12} {'Phase 2':<12} {'Reduction':<12} {'Phase 3':<12} {'Mutation':<12}")
        print("="*100)
        
        for language in ['Python', 'C', 'Java']:
            if language in results:
                r = results[language]
                status = "✅ Completed" if r['status'] == 'completed' else f"❌ {r['status']}"
                p1_str = str(r['p1']) if r['p1'] > 0 else "—"
                p2_str = str(r['p2']) if r['p2'] > 0 else "—"
                p3_str = str(r['p3']) if r['p3'] > 0 else "—"
                p4_str = f"{r['p4']:.1%}" if r['p4'] > 0 else "—"
                
                reduction = 100 * (r['p1'] - r['p2']) / r['p1'] if r['p1'] > 0 else 0
                reduction_str = f"{reduction:.1f}%" if reduction > 0 else "—"
                
                print(f"{language:<12} {status:<12} {p1_str:<12} {p2_str:<12} {reduction_str:<12} {p3_str:<12} {p4_str:<12}")
        
        print("="*100 + "\n")
        
        # Save to file
        with open('/home/davie/KIMVIWARE/final_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'job_ids': job_ids
            }, f, indent=2)
        
        print(f"✅ Final results saved to /home/davie/KIMVIWARE/final_results.json\n")
    
    def run(self):
        """Main execution"""
        try:
            # Start services
            if not self.start_all_services():
                print("⚠️  Some services failed to start, but continuing...\n")
            
            # Check jobs in queue
            if not self.submit_jobs():
                print("⚠️  No jobs in queue\n")
            
            # Monitor jobs
            print("Waiting for jobs to complete... (this may take several minutes)")
            time.sleep(5)  # Let services start processing
            
            self.monitor_jobs(timeout_minutes=120)
            
            # Display results
            time.sleep(2)
            self.display_final_results()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all services...")
            self.stop_all_services()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_all_services(self):
        """Stop all services"""
        for name, proc in self.processes.items():
            if proc.poll() is None:
                proc.terminate()

def main():
    """Main entry point"""
    orchestrator = CompleteOrchestratorDashboard()
    orchestrator.run()

if __name__ == '__main__':
    sys.exit(main() or 0)
