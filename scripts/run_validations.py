#!/usr/bin/env python3
# Run validator over all SUT folders and collect results.
import json
import shutil
from pathlib import Path
import tempfile
import uuid
import sys

# Ensure phase0 src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / 'kimvieware-phase0-validator' / 'src'))
from validator_service import ValidatorService


ROOT = Path.home() / 'KIMVIWARE' / 'KIMVIEware-System-kimvieware-sut-timetables'
OUT = Path('/tmp/validation_results.json')


def make_archive_for(folder: Path) -> Path:
    tmp = tempfile.gettempdir()
    base = Path(tmp) / f"{folder.name}-{uuid.uuid4().hex}"
    archive_path = shutil.make_archive(str(base), 'zip', root_dir=str(folder))
    return Path(archive_path)


def main():
    if not ROOT.exists():
        print(f"SUT root not found: {ROOT}")
        return

    service = ValidatorService()
    results = []

    for child in sorted(ROOT.iterdir()):
        if not child.is_dir():
            continue
        print(f"Validating {child.name}...")
        archive = make_archive_for(child)
        msg = {'job_id': str(uuid.uuid4()), 'sut_path': str(archive)}
        try:
            res = service.process_message(msg)
        except Exception as e:
            res = {'job_id': msg['job_id'], 'status': 'failed', 'error': str(e)}
        res['sut_name'] = child.name
        results.append(res)

    OUT.write_text(json.dumps(results, indent=2))
    print(f"Wrote results to {OUT}")


if __name__ == '__main__':
    main()
