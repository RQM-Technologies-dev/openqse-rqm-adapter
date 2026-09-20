#!/usr/bin/env python3
"""Build fixed source revisions, install wheels in a fresh venv, certify offline.

No editable installs. Tests are copied out of source trees to prevent accidental
source imports. Output is never reused; failed runs retain logs and a failed status.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import xml.etree.ElementTree as ET

NAMES = ('rqm-core', 'rqm-circuits', 'rqm-entanglement', 'rqm-compiler',
         'rqm-qiskit', 'rqm-optimize', 'rqm-braket', 'openqse-rqm-adapter')
MODULES = [x.replace('-', '_') for x in NAMES[:-1]] + ['rqm_openqse_adapter']


def run(cmd, cwd, log, env=None):
    with log.open('a') as stream:
        stream.write('\n' + repr([str(x) for x in cmd]) + '\n'); stream.flush()
        subprocess.run([str(x) for x in cmd], cwd=cwd, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--constraints', type=Path)
    parser.add_argument('--revisions', type=Path, help='JSON name -> exact commit SHA')
    args = parser.parse_args()
    root, out = args.sources.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    log = out / 'certification.log'
    manifest = {'status': 'running', 'repositories': {}, 'wheels': {},
                'hardware_execution': False, 'python': sys.version}
    def save():
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    save()
    try:
        expected = json.loads(args.revisions.read_text()) if args.revisions else None
        for name in NAMES:
            source = root / name
            sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
            tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=source, text=True).strip()
            dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=source, text=True)
            if dirty or (expected is not None and expected.get(name) != sha):
                raise RuntimeError(f'{name}: dirty source or candidate revision mismatch')
            manifest['repositories'][name] = {'commit': sha, 'tree': tree}
        save()
        wheels = out / 'wheels'; wheels.mkdir()
        # Build from git archives, not working copies (including untracked files).
        snapshots = out / 'sources'; snapshots.mkdir()
        for name in NAMES:
            dest = snapshots / name
            run(['git', 'clone', '--no-local', '--no-checkout', root / name, dest], out, log)
            run(['git', 'checkout', '--detach', manifest['repositories'][name]['commit']], dest, log)
            run([sys.executable, '-m', 'pip', 'wheel', '--no-deps',
                 '--wheel-dir', wheels, dest], out, log)
        for wheel in sorted(wheels.glob('*.whl')):
            manifest['wheels'][wheel.name] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        save()
        envdir = out / 'venv'; venv.create(envdir, with_pip=True)
        py = envdir / 'bin/python'
        constraints = ['-c', args.constraints.resolve()] if args.constraints else []
        run([py, '-m', 'pip', 'install', *constraints, *sorted(wheels.glob('*.whl')),
             'pytest', 'pytest-cov', 'qiskit-aer==0.17.2', 'qiskit-qasm3-import==0.6.0',
             'qiskit-ibm-runtime>=0.48,<0.49', 'flask'], out, log)
        run([py, '-m', 'pip', 'check'], out, log)
        frozen = subprocess.check_output([py, '-m', 'pip', 'freeze'], text=True)
        (out / 'requirements-observed.txt').write_text(frozen)
        (out / 'constraints.txt').write_text('\n'.join(x for x in frozen.splitlines() if ' @ ' not in x) + '\n')
        env = dict(os.environ, PYTHONPATH='', AWS_EC2_METADATA_DISABLED='true', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        # Confirm every tested module comes from this environment's site-packages.
        check = ('import importlib,json; from pathlib import Path; '
                 f'm={{n:importlib.import_module(n).__file__ for n in {MODULES!r}}}; '
                 f'assert all(str(Path(p).resolve()).startswith({str(envdir)!r}) for p in m.values()),m; '
                 'print(json.dumps(m,indent=2))')
        manifest['installed_modules'] = json.loads(subprocess.check_output([py, '-c', check], cwd=out, env=env, text=True))
        save()
        counts = {}; failures = []
        for name in NAMES:
            source = snapshots / name
            xml = out / f'{name}.xml'
            try:
                run([py, '-m', 'pytest', source / 'tests', '-q', '--tb=short',
                     '--import-mode=importlib', '-o', 'pythonpath=', f'--junitxml={xml}'], out, log, env)
            except subprocess.CalledProcessError:
                failures.append(name)
            if xml.exists():
                suites = list(ET.parse(xml).iter('testsuite'))
                entry = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
                         for key in ('tests', 'failures', 'errors', 'skipped')}
                entry['passed'] = entry['tests'] - entry['failures'] - entry['errors'] - entry['skipped']
                counts[name] = entry
            print(name, counts.get(name), flush=True)
        manifest['test_counts'] = counts
        save()
        if failures:
            raise RuntimeError(f'Failed suites: {failures}')
        demo = ('import json; from pathlib import Path; '
                'from rqm_openqse_adapter.ecosystem.pipeline import run_clean_demonstration; '
                f'r=run_clean_demonstration(ecosystem_root=Path({str(root)!r})).to_dict(); '
                f'r["repository_shas"]={ {n:v['commit'] for n,v in manifest['repositories'].items()}!r}; '
                'Path("conformance.json").write_text(json.dumps(r,indent=2,default=str))')
        run([py, '-c', demo], out, log, env)
        manifest['status'] = 'passed'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['failure'] = str(exc)
        raise
    finally:
        save()


if __name__ == '__main__':
    main()
