"""
Phase 3: EvoPath-BA Optimization Service (Bat Algorithm)

Consumes: reduction.completed
Produces: optimization.completed
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'kimvieware-shared' / 'src'))

from kimvieware_shared import MicroserviceBase, JobStatus, Trajectory
from algorithms.evopath_ba import EvoPathBA  # ← import BA au lieu de GA


class EvoPathService(MicroserviceBase):
    """Phase 3: Bat Algorithm Optimization"""
    
    def __init__(self):
        super().__init__(
            service_name="Phase3_EvoPath",
            input_queue="reduction.completed",
            output_queue="optimization.completed"
        )
        
        self.evopath = EvoPathBA(
            w1=0.5,   # Coverage weight
            w2=0.3,   # Cost weight
            w3=0.2,   # Size weight
            population_size=40,      # Légèrement moins que GA (plus efficace)
            generations=100,
            loudness=0.5,            # A0
            pulse_rate=0.5,          # r0
            f_min=0.0,
            f_max=2.0,
            alpha=0.9,
            gamma=0.9
        )
    
    def process_message(self, message: dict) -> dict:
        """Optimize trajectory set using Bat Algorithm"""
        
        job_id = message['job_id']
        
        if message.get('status') != 'reduced':
            self.logger.warning(f"[{job_id}] Skipping: not reduced")
            return message
        
        trajectories_data = message.get('trajectories', [])
        
        if not trajectories_data:
            return self._error(job_id, "No trajectories to optimize")
        
        self.logger.info(f"[{job_id}] EvoPath-BA optimization on {len(trajectories_data)} trajectories")
        
        trajectories = [Trajectory.from_dict(t) for t in trajectories_data]
        optimized_set, stats = self.evopath.optimize(trajectories)
        
        self.logger.info(
            f"[{job_id}] ✅ Optimized {stats['original_count']} → {stats['optimized_count']} "
            f"({stats['size_reduction']*100:.1f}% reduction, "
            f"{stats['cost_reduction']*100:.1f}% cost saved)"
        )
        
        return {
            'job_id': job_id,
            'status': JobStatus.OPTIMIZED.value,
            'sut_info': message['sut_info'],
            'trajectories_count': len(optimized_set),
            'trajectories': [t.to_dict() for t in optimized_set],
            'extraction_count': message.get('extraction_count', message.get('trajectories_count')),
            'original_trajectories': message.get('original_trajectories', message.get('trajectories', [])),
            'sgats_stats': message.get('sgats_stats'),
            'evopath_stats': stats,
            'metadata': {
                'phase': 'evopath_optimization',
                'algorithm': 'bat_algorithm'
            }
        }
    
    def _error(self, job_id: str, msg: str) -> dict:
        return {
            'job_id': job_id,
            'status': JobStatus.FAILED.value,
            'error': msg,
            'phase': 'evopath'
        }


if __name__ == "__main__":
    service = EvoPathService()
    service.start()