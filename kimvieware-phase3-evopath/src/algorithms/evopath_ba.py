"""
EvoPath-BA: Bat Algorithm for test suite optimization
Implementation inspired by Xin-She Yang (2010)
Adapted for binary test selection problem
"""
import numpy as np
import random
from typing import List, Tuple, Set
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'kimvieware-shared' / 'src'))
from kimvieware_shared.models import Trajectory


class EvoPathBA:
    """
    Bat Algorithm for optimal test suite selection
    
    Multi-objective fitness function (same as GA):
    F(C) = w1·cov(C) + w2·(1 - cost(C)/maxCost) + w3·(1 - |C|/|T|)
    """
    
    def __init__(
        self,
        w1: float = 0.5,        # Coverage weight
        w2: float = 0.3,        # Cost weight  
        w3: float = 0.2,        # Size weight
        population_size: int = 40,
        generations: int = 100,
        loudness: float = 0.5,   # A (initial loudness)
        pulse_rate: float = 0.5,  # r (initial pulse rate)
        f_min: float = 0.0,
        f_max: float = 2.0,
        alpha: float = 0.9,      # Loudness decay
        gamma: float = 0.9       # Pulse rate increase
    ):
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self.pop_size = population_size
        self.generations = generations
        self.loudness_init = loudness
        self.pulse_rate_init = pulse_rate
        self.f_min = f_min
        self.f_max = f_max
        self.alpha = alpha
        self.gamma = gamma
    
    def optimize(self, trajectories: List[Trajectory]) -> Tuple[List[Trajectory], dict]:
        """Optimize test suite using Bat Algorithm"""
        
        print(f"\n{'='*60}")
        print(f"🦇 EvoPath-BA: Bat Algorithm Optimization")
        print(f"{'='*60}")
        print(f"Input: {len(trajectories)} trajectories")
        print(f"Parameters:")
        print(f"   Population: {self.pop_size}")
        print(f"   Generations: {self.generations}")
        print(f"   Loudness (A): {self.loudness_init}")
        print(f"   Pulse rate (r): {self.pulse_rate_init}")
        print(f"   Frequency: [{self.f_min}, {self.f_max}]")
        
        # Setup problem data
        self.trajectories = trajectories
        self.n = len(trajectories)
        self.all_branches = self._get_all_branches(trajectories)
        self.max_cost = sum(t.cost for t in trajectories)
        
        print(f"\n   Total branches: {len(self.all_branches)}")
        print(f"   Max cost: {self.max_cost:.3f}")
        
        # Initialize bat population
        bats = self._init_population()
        velocities = [np.zeros(self.n) for _ in range(self.pop_size)]
        frequencies = [0.0 for _ in range(self.pop_size)]
        loudness = [self.loudness_init for _ in range(self.pop_size)]
        pulse_rate = [self.pulse_rate_init for _ in range(self.pop_size)]
        
        # Evaluate fitness
        fitness = [self._fitness(bat) for bat in bats]
        
        # Find global best
        best_idx = np.argmax(fitness)
        best_bat = bats[best_idx].copy()
        best_fitness = fitness[best_idx]
        
        # Track convergence
        best_fitness_history = [best_fitness]
        
        print(f"\n🔬 Evolution:")
        
        # Main loop
        for gen in range(self.generations):
            for i in range(self.pop_size):
                # Generate new frequency
                frequencies[i] = self.f_min + (self.f_max - self.f_min) * random.random()
                
                # Update velocity
                velocities[i] = velocities[i] + (bats[i] - best_bat) * frequencies[i]
                
                # Update position (binary sigmoid)
                new_bat = self._sigmoid_transform(bats[i] + velocities[i])
                
                # Local search (random walk) if random number > pulse_rate
                if random.random() > pulse_rate[i]:
                    new_bat = self._local_search(best_bat, loudness[i])
                
                # Evaluate new candidate
                new_fitness = self._fitness(new_bat)
                
                # Accept if better and random < loudness
                if new_fitness > fitness[i] and random.random() < loudness[i]:
                    bats[i] = new_bat
                    fitness[i] = new_fitness
                    
                    # Update loudness and pulse rate
                    loudness[i] = self.alpha * loudness[i]
                    pulse_rate[i] = self.pulse_rate_init * (1 - np.exp(-self.gamma * gen))
                
                # Update global best
                if new_fitness > best_fitness:
                    best_bat = new_bat.copy()
                    best_fitness = new_fitness
            
            best_fitness_history.append(best_fitness)
            
            if gen % 20 == 0:
                print(f"   Gen {gen:3d}: Best fitness = {best_fitness:.4f}")
        
        # Extract optimized trajectories
        optimized_indices = [i for i, bit in enumerate(best_bat) if bit == 1]
        if not optimized_indices:
            # Fallback: keep at least one trajectory
            optimized_indices = [np.argmax([self._fitness_bit(i) for i in range(self.n)])]
        
        optimized_set = [self.trajectories[i] for i in optimized_indices]
        
        # Statistics
        stats = self._compute_stats(self.trajectories, optimized_set, best_fitness_history)
        
        print(f"\n✅ EvoPath-BA Results:")
        print(f"   |T| = {len(self.trajectories)} → |C| = {len(optimized_set)}")
        print(f"   Size reduction: {stats['size_reduction']*100:.1f}%")
        print(f"   Cost reduction: {stats['cost_reduction']*100:.1f}%")
        print(f"   Coverage: {stats['coverage_rate']*100:.1f}%")
        print(f"   Best fitness: {stats['best_fitness']:.4f}")
        print(f"{'='*60}\n")
        
        return optimized_set, stats
    
    def _init_population(self) -> List[np.ndarray]:
        """Initialize population of bats (random binary vectors)"""
        population = []
        for _ in range(self.pop_size):
            # Random binary vector with ~30% ones (like GA initial population)
            bat = np.random.choice([0, 1], size=self.n, p=[0.7, 0.3])
            population.append(bat)
        return population
    
    def _sigmoid_transform(self, x: np.ndarray) -> np.ndarray:
        """
        Transform real-valued position to binary using sigmoid function
        S(x) = 1 / (1 + e^{-x})
        """
        sigmoid = 1.0 / (1.0 + np.exp(-x))
        return (np.random.rand(self.n) < sigmoid).astype(int)
    
    def _local_search(self, best_bat: np.ndarray, loudness: float) -> np.ndarray:
        """
        Local search around best solution (random walk)
        x_new = x_best + ε * A_mean
        """
        epsilon = np.random.randn(self.n)  # Gaussian noise
        new_position = best_bat + epsilon * loudness
        return self._sigmoid_transform(new_position)
    
    def _fitness(self, individual: np.ndarray) -> float:
        """Compute fitness for a binary vector"""
        selected_indices = [i for i, bit in enumerate(individual) if bit == 1]
        
        if len(selected_indices) == 0:
            return 0.0
        
        selected = [self.trajectories[i] for i in selected_indices]
        
        # Coverage
        covered = self._get_all_branches(selected)
        cov = len(covered) / len(self.all_branches) if self.all_branches else 0
        
        # Cost
        total_cost = sum(t.cost for t in selected)
        cost_norm = 1 - (total_cost / self.max_cost) if self.max_cost > 0 else 1
        
        # Size
        size_norm = 1 - (len(selected) / self.n)
        
        # Combined fitness (same as GA)
        fitness = self.w1 * cov + self.w2 * cost_norm + self.w3 * size_norm
        
        return fitness
    
    def _fitness_bit(self, idx: int) -> float:
        """Fitness for a single trajectory (used for fallback)"""
        return self._fitness(np.eye(self.n)[idx])
    
    def _get_all_branches(self, trajectories: List[Trajectory]) -> Set:
        branches = set()
        for t in trajectories:
            branches.update(t.branches_covered)
        return branches
    
    def _compute_stats(self, original: List[Trajectory], optimized: List[Trajectory],
                       fitness_history: List[float]) -> dict:
        original_branches = self._get_all_branches(original)
        optimized_branches = self._get_all_branches(optimized)
        
        return {
            'original_count': len(original),
            'optimized_count': len(optimized),
            'size_reduction': 1 - (len(optimized) / len(original)) if original else 0,
            'original_cost': sum(t.cost for t in original),
            'optimized_cost': sum(t.cost for t in optimized),
            'cost_reduction': 1 - (sum(t.cost for t in optimized) / sum(t.cost for t in original)) if original else 0,
            'total_branches': len(original_branches),
            'covered_branches': len(optimized_branches),
            'coverage_rate': len(optimized_branches) / len(original_branches) if original_branches else 1.0,
            'best_fitness': max(fitness_history),
            'generations': len(fitness_history),
            'convergence_history': fitness_history,
            'algorithm': 'Bat Algorithm (BA)'
        }