#!/usr/bin/env python3
"""
Run extraction -> SGATS -> EvoPath pipeline for each SUT and save stats.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Make project packages importable
sys.path.insert(0, str(ROOT / 'kimvieware-shared' / 'src'))
sys.path.insert(0, str(ROOT / 'kimvieware-phase1-extractor' / 'src'))
sys.path.insert(0, str(ROOT / 'kimvieware-phase2-sgats' / 'src'))
sys.path.insert(0, str(ROOT / 'kimvieware-phase3-evopath' / 'src'))
sys.path.insert(0, str(ROOT / 'kimvieware-phase0-validator' / 'src'))

from validators.language_detector import LanguageDetector
from extractors.python_extractor import PythonExtractor
from extractors.c_extractor import CExtractor
from extractors.java_extractor import JavaExtractor
from algorithms.sgats import SGATS

OUT = Path('/tmp/sgats_evopath_results.json')
SUT_ROOT = Path.home() / 'KIMVIWARE' / 'KIMVIEware-System-kimvieware-sut-timetables'


def process_sut(sut_path: Path):
    rec = {'sut': sut_path.name}

    lang_info = LanguageDetector.detect(sut_path)
    lang = lang_info['language']
    rec['language'] = lang

    # Extract trajectories
    try:
        if lang == 'python':
            ext = PythonExtractor()
            trajectories = ext.extract_paths(sut_path)
        elif lang in ('c', 'cpp'):
            ext = CExtractor(max_paths=1000)
            trajectories = ext.extract_paths(sut_path)
        elif lang == 'java':
            ext = JavaExtractor(max_paths=1000)
            trajectories = ext.extract_paths(sut_path)
        else:
            rec['error'] = 'unsupported language'
            return rec
    except Exception as e:
        rec['error'] = f'extraction failed: {e}'
        return rec

    rec['initial_count'] = len(trajectories)

    # Run SGATS
    try:
        sg = SGATS()
        reduced_set, stats_sg = sg.reduce(trajectories)
        rec['sgats'] = stats_sg
        rec['reduced_count'] = len(reduced_set)
    except Exception as e:
        rec['sgats_error'] = str(e)
        return rec

    # Run EvoPath (if available)
    try:
        from algorithms.evopath_ga import EvoPathGA
        ev = EvoPathGA(population_size=30, generations=60)
        optimized_set, stats_ev = ev.optimize(reduced_set)
        rec['evopath'] = stats_ev
        rec['optimized_count'] = len(optimized_set)
    except Exception as e:
        rec['evopath_error'] = str(e)

    return rec


def main():
    if not SUT_ROOT.exists():
        print(f"SUT root not found: {SUT_ROOT}")
        return

    results = []

    for child in sorted(SUT_ROOT.iterdir()):
        if not child.is_dir():
            continue
        print(f"\n=== Processing {child.name} ===")
        res = process_sut(child)
        results.append(res)

    OUT.write_text(json.dumps(results, indent=2))
    print(f"Wrote results to {OUT}")


if __name__ == '__main__':
    main()
