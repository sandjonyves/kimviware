"""
SGATS: Similarity-Guided Automatic Test Selection
Implementation of Algorithm 3.1 from thesis
"""
import numpy as np
from typing import List, Set, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'kimvieware-shared' / 'src'))
from kimvieware_shared.models import Trajectory

class SGATS:
    """
    Similarity-Guided Automatic Test Selection
    
    Reduces trajectory set T to Tred while preserving coverage
    
    Key formulas (from thesis):
    
    1. Priority function (Equation 3.1):
       ρ(t) = α·cost(t) + β·|branches(t)| + γ·length(t)
    
    2. Similarity function (Equation 3.2):
       sim(ti, tj) = |branches(ti) ∩ branches(tj)| / |branches(ti) ∪ branches(tj)|
    
    3. Fusion criterion:
       Merge ti and tj if sim(ti, tj) > θ (threshold = 0.8)
    """
    
    def __init__(
        self,
        alpha: float = 0.4,  # Cost weight
        beta: float = 0.3,   # Coverage weight
        gamma: float = 0.3,  # Length weight
        similarity_threshold: float = 0.8
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.theta = similarity_threshold  # θ threshold
    
    def reduce(self, trajectories: List[Trajectory]) -> Tuple[List[Trajectory], dict]:
        """
        Main SGATS reduction algorithm
        
        Args:
            trajectories: Initial trajectory set T
            
        Returns:
            (reduced_set, statistics)
        """
        
        print(f"\n{'='*60}")
        print(f"🔬 SGATS: Similarity-Guided Test Selection")
        print(f"{'='*60}")
        print(f"Input: |T| = {len(trajectories)} trajectories")
        
        # Step 1: Calculate priorities for all trajectories
        print(f"\n📊 Step 1: Calculating priorities (ρ)...")
        priorities = self._calculate_priorities(trajectories)
        
        # Step 2: Sort by priority (descending)
        sorted_indices = np.argsort(priorities)[::-1]
        sorted_trajectories = [trajectories[i] for i in sorted_indices]
        
        print(f"   Priority range: [{priorities.min():.3f}, {priorities.max():.3f}]")
        
        # Step 3: Greedy selection with similarity fusion
        print(f"\n🔀 Step 2: Greedy selection with fusion (θ={self.theta})...")
        reduced_set, coverage = self._greedy_selection(sorted_trajectories)
        
        # Step 4: Statistics
        total_branches = self._get_all_branches(trajectories)
        covered_branches = self._get_all_branches(reduced_set)
        
        stats = {
            'initial_count': len(trajectories),
            'reduced_count': len(reduced_set),
            'reduction_rate': 1 - (len(reduced_set) / len(trajectories)),
            'total_branches': len(total_branches),
            'covered_branches': list(covered_branches), # Convert set to list for JSON serialization
            'coverage_rate': len(covered_branches) / len(total_branches) if total_branches else 1.0,
            'initial_cost': sum(t.cost for t in trajectories),
            'reduced_cost': sum(t.cost for t in reduced_set),
            'cost_reduction': 1 - (sum(t.cost for t in reduced_set) / sum(t.cost for t in trajectories))
        }
        
        print(f"\n✅ SGATS Results:")
        print(f"   |T| = {stats['initial_count']} → |Tred| = {stats['reduced_count']}")
        print(f"   Reduction: {stats['reduction_rate']*100:.1f}%")
        print(f"   Coverage: {stats['coverage_rate']*100:.1f}%")
        print(f"   Cost reduction: {stats['cost_reduction']*100:.1f}%")
        print(f"{'='*60}\n")
        
        return reduced_set, stats
    
    def _calculate_priorities(self, trajectories: List[Trajectory]) -> np.ndarray:
        """
        Calculate priority ρ(t) for each trajectory
        
        Formula (Eq 3.1):
        ρ(t) = α·cost(t) + β·|branches(t)| + γ·length(t)
        """
        n = len(trajectories)
        priorities = np.zeros(n)
        
        for i, t in enumerate(trajectories):
            cost_norm = t.cost
            branch_count = len(t.branches_covered)
            length = len(t.basic_blocks)
            
            # Apply formula
            priorities[i] = (
                self.alpha * cost_norm +
                self.beta * branch_count +
                self.gamma * length
            )
        
        # Normalize to [0, 1]
        if priorities.max() > 0:
            priorities = priorities / priorities.max()
        
        return priorities
    
    def _calculate_similarity(self, ti: Trajectory, tj: Trajectory) -> float:
        """
        Calculate Jaccard similarity between two trajectories
        
        Formula (Eq 3.2):
        sim(ti, tj) = |branches(ti) ∩ branches(tj)| / |branches(ti) ∪ branches(tj)|
        """
        branches_i = ti.branches_covered
        branches_j = tj.branches_covered
        
        intersection = len(branches_i & branches_j)
        union = len(branches_i | branches_j)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _greedy_selection(self, sorted_trajectories: List[Trajectory]) -> Tuple[List[Trajectory], Set]:
        """
        Greedy selection with similarity-based fusion
        
        Algorithm:
        1. Select trajectory t* with highest priority
        2. Add to Tred
        3. Mark all similar trajectories (sim > θ) as covered
        4. Repeat until all branches covered
        """
        reduced_set = []
        covered_branches = set()
        remaining = list(sorted_trajectories)
        
        iteration = 0
        
        while remaining:
            iteration += 1
            
            # Select best candidate
            best = remaining[0]
            remaining = remaining[1:]
            
            # Check if adds new coverage
            new_branches = best.branches_covered - covered_branches
            
            if len(new_branches) == 0:
                # No new coverage, skip
                continue
            
            # Add to reduced set
            reduced_set.append(best)
            covered_branches.update(best.branches_covered)
            
            print(f"   Iteration {iteration}: Selected {best.path_id}")
            print(f"      New branches: {len(new_branches)}, Total: {len(covered_branches)}")
            
            # Remove similar trajectories (fusion)
            to_remove = []
            for t in remaining:
                sim = self._calculate_similarity(best, t)
                if sim > self.theta:
                    to_remove.append(t)
            
            if to_remove:
                print(f"      Fused {len(to_remove)} similar trajectories (sim > {self.theta})")
                for t in to_remove:
                    remaining.remove(t)
            
            # Early termination if all original branches covered
            # (In practice, we continue until no more unique coverage)
        
        return reduced_set, covered_branches
    
    def _get_all_branches(self, trajectories: List[Trajectory]) -> Set:
        """Get union of all branches in trajectory set"""
        all_branches = set()
        for t in trajectories:
            all_branches.update(t.branches_covered)
        return all_branches
