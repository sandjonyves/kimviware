#!/usr/bin/env python3
"""
KIMVIWARE - Multi-Language Orchestration Test
Tests auth-service implementations in Python, C, and Java
"""

import json
import uuid
import time
import sys
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class MultiLanguageOrchestrator:
    def __init__(self):
        self.base = Path.home() / "KIMVIWARE"
        self.results = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'framework': 'KIMVIWARE v1.0',
            'orchestration': 'Multi-Language Test',
            'tests': []
        }
        
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def get_language_suts(self) -> Dict[str, Path]:
        """Get SUTs for each language"""
        suts_dir = self.base / "KIMVIEware-System-kimvieware-sut-timetables"
        
        suts = {
            'Python': suts_dir / "auth-service",
            'C': suts_dir / "auth-service-c",
            'Java': suts_dir / "auth-service-java"
        }
        
        available = {}
        for lang, path in suts.items():
            if path.exists():
                available[lang] = path
        
        return available
    
    def create_sut_zips(self):
        """Create ZIP files for all SUTs"""
        self.print_header("📦 PREPARING SERVICES UNDER TEST")
        
        suts = self.get_language_suts()
        zip_files = {}
        
        for lang, sut_dir in suts.items():
            zip_path = sut_dir.parent / f"{sut_dir.name}.zip"
            
            if zip_path.exists():
                size_kb = zip_path.stat().st_size / 1024
                logger.info(f"  {lang:10s} - Using existing {sut_dir.name}.zip ({size_kb:.0f} KB)")
                zip_files[lang] = zip_path
            else:
                logger.info(f"  {lang:10s} - Creating ZIP for {sut_dir.name}...")
                import subprocess
                result = subprocess.run(
                    f"cd {sut_dir.parent} && zip -r -q {sut_dir.name}.zip {sut_dir.name} -x '*__pycache__/*' '*.pyc' '*.class' '*.o' '*.a'",
                    shell=True,
                    capture_output=True
                )
                
                if result.returncode == 0:
                    size_kb = zip_path.stat().st_size / 1024
                    logger.info(f"  {lang:10s} - Created {sut_dir.name}.zip ({size_kb:.0f} KB)")
                    zip_files[lang] = zip_path
        
        return zip_files
    
    def submit_sut(self, language: str, sut_zip: Path) -> str:
        """Submit SUT to pipeline"""
        import pika
        
        job_id = str(uuid.uuid4())
        
        credentials = pika.PlainCredentials('admin', 'kimvie2025')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue='submission.new', durable=True)
        
        message = {
            'job_id': job_id,
            'sut_path': str(sut_zip),
            'user_id': 'orchestrator',
            'language': language,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'sut_name': f'auth-service-{language.lower()}'
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='submission.new',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        
        return job_id
    
    def wait_for_job(self, job_id: str, language: str, timeout: int = 600):
        """Wait for job completion"""
        from pymongo import MongoClient
        
        logger.info(f"  {language:10s} - Job {job_id[:8]}... processing")
        
        client = MongoClient('mongodb://admin:kimvie2025@localhost:27017/')
        db = client['kimvieware']
        jobs_coll = db['jobs']
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            try:
                job = jobs_coll.find_one({'job_id': job_id})
                
                if job:
                    status = job.get('status', 'unknown')
                    phase = job.get('current_phase', 'unknown')
                    
                    if status != last_status:
                        logger.info(f"  {language:10s} - {status} (Phase: {phase})")
                        last_status = status
                    
                    if status == 'completed':
                        logger.info(f"  {language:10s} - ✅ Completed")
                        return job
                    elif status == 'failed':
                        logger.error(f"  {language:10s} - ❌ Failed: {job.get('error')}")
                        return job
                
                time.sleep(10)
            except Exception as e:
                logger.error(f"  {language:10s} - Error: {e}")
                time.sleep(5)
        
        logger.error(f"  {language:10s} - ⏱️ Timeout")
        return None
    
    def run_orchestration(self):
        """Run multi-language orchestration"""
        self.print_header("🎯 KIMVIWARE MULTI-LANGUAGE ORCHESTRATION TEST")
        
        # Step 1: Create ZIPs
        zip_files = self.create_sut_zips()
        
        if not zip_files:
            logger.error("No SUT ZIPs available")
            return False
        
        logger.info(f"\n✅ {len(zip_files)} services ready for testing\n")
        
        # Step 2: Submit all jobs
        self.print_header("📤 SUBMITTING JOBS")
        
        job_map = {}
        for language, sut_zip in zip_files.items():
            logger.info(f"Submitting {language:10s}: {sut_zip.name}")
            job_id = self.submit_sut(language, sut_zip)
            job_map[language] = job_id
            logger.info(f"  Job ID: {job_id}\n")
            time.sleep(2)  # Stagger submissions
        
        # Step 3: Monitor all jobs
        self.print_header("⏳ MONITORING ALL JOBS")
        
        logger.info(f"Monitoring {len(job_map)} jobs in parallel...\n")
        
        jobs_data = {}
        for language, job_id in job_map.items():
            logger.info(f"\n{language} ({job_id[:8]}...):")
            job_data = self.wait_for_job(job_id, language, timeout=600)
            jobs_data[language] = {
                'job_id': job_id,
                'data': job_data
            }
        
        # Step 4: Display results
        self.print_results(jobs_data)
        
        return True
    
    def print_results(self, jobs_data: Dict):
        """Print comprehensive results"""
        self.print_header("📊 ORCHESTRATION RESULTS")
        
        print(f"{'Language':<12} {'Status':<15} {'Phase 1':<12} {'Phase 2':<12} {'Phase 3':<12} {'Mutation':<12}")
        print("-" * 90)
        
        for language, result in jobs_data.items():
            job_data = result['data']
            
            if not job_data:
                print(f"{language:<12} {'ERROR':<15} {'—':<12} {'—':<12} {'—':<12} {'—':<12}")
                continue
            
            status = job_data.get('status', 'unknown')
            phases = job_data.get('phases', {})
            
            p1 = phases.get('phase1', {}).get('trajectories_count', '—')
            p2 = phases.get('phase2', {}).get('reduced_trajectories_count', '—')
            p3 = phases.get('phase3', {}).get('optimized_trajectories_count', '—')
            mutation = f"{phases.get('phase4', {}).get('mutation_score', 0):.0%}" if phases.get('phase4', {}).get('mutation_score') else '—'
            
            status_icon = "✅" if status == 'completed' else "⏳" if status == 'running' else "❌"
            print(f"{language:<12} {status_icon} {status:<13} {str(p1):<12} {str(p2):<12} {str(p3):<12} {mutation:<12}")
        
        self.print_header("📈 DETAILED RESULTS")
        
        for language, result in jobs_data.items():
            job_data = result['data']
            
            if not job_data:
                continue
            
            print(f"\n{language}:")
            print(f"  Job ID: {result['job_id']}")
            print(f"  Status: {job_data.get('status')}")
            
            phases = job_data.get('phases', {})
            
            if phases.get('phase0'):
                p0 = phases['phase0']
                print(f"  Phase 0: {p0.get('language')} ({p0.get('confidence', 0):.0%})")
            
            if phases.get('phase1'):
                p1 = phases['phase1']
                print(f"  Phase 1: {p1.get('trajectories_count')} trajectories")
            
            if phases.get('phase2'):
                p2 = phases['phase2']
                print(f"  Phase 2: {p2.get('reduced_trajectories_count')} ({p2.get('reduction_rate', 0):.0%} reduction)")
            
            if phases.get('phase3'):
                p3 = phases['phase3']
                print(f"  Phase 3: {p3.get('optimized_trajectories_count')} tests (fitness: {p3.get('best_fitness', 0):.3f})")
            
            if phases.get('phase4'):
                p4 = phases['phase4']
                print(f"  Phase 4: {p4.get('mutation_score', 0):.1%} mutation score")
        
        print("\n" + "="*80)
        print("✅ ORCHESTRATION COMPLETE")
        print("="*80 + "\n")

def main():
    """Main execution"""
    orchestrator = MultiLanguageOrchestrator()
    
    try:
        success = orchestrator.run_orchestration()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Orchestration interrupted")
        return 0
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
