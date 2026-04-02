#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Make phase0 and phase1 packages importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'kimvieware-phase0-validator' / 'src'))
sys.path.insert(0, str(ROOT / 'kimvieware-phase1-extractor' / 'src'))

from validators.language_detector import LanguageDetector
from extractors.python_extractor import PythonExtractor
from extractors.c_extractor import CExtractor
from extractors.java_extractor import JavaExtractor


SUT_ROOT = Path.home() / 'KIMVIWARE' / 'KIMVIEware-System-kimvieware-sut-timetables'
OUT = Path('/tmp/extraction_metrics.json')


def analyze_python(sut_path: Path):
    ext = PythonExtractor()
    py_files = ext._find_python_files(sut_path)
    analysis = ext._analyze_control_flow(py_files)
    trajectories = ext._generate_trajectories(analysis)
    return {
        'files': len(py_files),
        'analysis': analysis,
        'trajectories': len(trajectories)
    }


def analyze_c(sut_path: Path):
    ext = CExtractor(max_paths=500)
    trajectories = ext.extract_paths(sut_path)
    return {
        'trajectories': len(trajectories)
    }


def analyze_java(sut_path: Path):
    ext = JavaExtractor(max_paths=500)
    trajectories = ext.extract_paths(sut_path)
    return {
        'trajectories': len(trajectories)
    }


def main():
    if not SUT_ROOT.exists():
        print(f"SUT root not found: {SUT_ROOT}")
        return

    results = []

    for child in sorted(SUT_ROOT.iterdir()):
        if not child.is_dir():
            continue
        print(f"Analyzing {child.name}...")

        lang_info = LanguageDetector.detect(child)
        lang = lang_info['language']

        entry = lang_info.get('entry_point')

        rec = {
            'sut': child.name,
            'language': lang,
            'files_count': lang_info.get('file_count', 0),
            'entry_point': str(entry) if entry else None,
        }

        try:
            if lang == 'python':
                rec.update(analyze_python(child))
            elif lang in ('c', 'cpp'):
                rec.update(analyze_c(child))
            elif lang == 'java':
                rec.update(analyze_java(child))
            else:
                rec['note'] = 'unsupported'
        except Exception as e:
            rec['error'] = str(e)

        results.append(rec)

    OUT.write_text(json.dumps(results, indent=2))
    print(f"Wrote results to {OUT}")


if __name__ == '__main__':
    main()
