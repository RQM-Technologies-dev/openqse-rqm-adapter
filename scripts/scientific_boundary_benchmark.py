#!/usr/bin/env python3
"""Deterministic hinge-query boundary experiment against Aer statevector.

Run with the certification venv. Timings use five warmed repetitions; memory is
measured separately with tracemalloc and does not contaminate timing samples.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import platform
import random
import statistics
import time
import tracemalloc
from pathlib import Path

from rqm_compiler import Circuit, compile_representation_aware, plan_and_evaluate
from rqm_compiler.direct_readout import global_z_star
from rqm_compiler.stable_prototype import global_z_chain
from rqm_compiler.topology_readout import recognize
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from qiskit import transpile
from qiskit.quantum_info import Pauli
from qiskit_aer import AerSimulator


def circuit(family, n):
    c = Circuit(n)
    if family in ('star', 'interleaved_star', 'revisited_star', 'chain'):
        c.h(0)
        for j in range(1, n):
            a, b = (j-1, j) if family == 'chain' else (0, j)
            c.rxx(a, b, .13+.003*j); c.rzz(a, b, -.071-.002*j); c.cx(a, b)
            if family == 'interleaved_star' and j == 1:
                c.ry(0, .23)
        if family == 'revisited_star':
            c.rxx(0, 1, .31)
    elif family.startswith('hardware_'):
        for layer in range(int(family.split('_')[1])):
            for q in range(n):
                c.rz(q, .071*(q+1)*(layer+1)); c.rx(q, .137*(q+2)*(layer+1))
            for q in range(n-1): c.cx(q, q+1)
    elif family == 'random_noncommuting':
        rng = random.Random(7300+n)
        for q in range(n): c.h(q)
        for layer in range(3):
            for q in range(n): c.ry(q, rng.uniform(-1, 1))
            for _ in range(n):
                a, b = rng.sample(range(n), 2)
                c.rxx(a, b, rng.uniform(-1, 1)); c.rzz(a, b, rng.uniform(-1, 1))
    return c


def timed(fn, repeats):
    fn()  # warm up outside recorded samples
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns(); result = fn(); samples.append(time.perf_counter_ns()-start)
    return result, samples


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--certification', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--repeats', type=int, default=5)
    args = p.parse_args()
    manifest = json.loads((args.certification/'manifest.json').read_text())
    if manifest['status'] != 'passed': raise RuntimeError('Certification must pass first')
    import rqm_compiler
    if str(args.certification.resolve()/'venv') not in str(Path(rqm_compiler.__file__).resolve()):
        raise RuntimeError('Use the certified installed-artifact environment')
    backend = AerSimulator(method='statevector', max_parallel_threads=1)
    out = args.output; out.mkdir(parents=True, exist_ok=False)
    families = ('star', 'chain', 'hardware_2', 'hardware_4', 'hardware_5',
                'interleaved_star', 'revisited_star', 'random_noncommuting')
    rows = []
    for family in families:
        for n in (4, 8, 12):
            c = circuit(family, n)
            compiled, ct = timed(lambda: compile_representation_aware(c), args.repeats)
            qc = compiled_circuit_to_qiskit(c)
            tqc, qt = timed(lambda: transpile(qc, basis_gates=['rz','sx','x','cx'],
                optimization_level=3, seed_transpiler=17), args.repeats)
            # Measure each recognizer's rejection independently. Accepted star/
            # chain calls also evaluate; never label those durations detection-only.
            rejection = {}
            for label, fn in [('star', lambda: global_z_star(c)), ('chain', lambda: global_z_chain(c)),
                              ('hardware', lambda: recognize(c))]:
                result, samples = timed(fn, args.repeats)
                rejected = result is None if label == 'hardware' else not result.available
                rejection[label] = {'rejected': rejected,
                    'rejection_ns': int(statistics.median(samples)) if rejected else None}
            for query_name, pauli in [('global_Z', 'Z'*n), ('local_X', 'X'+'I'*(n-1))]:
                runqc = tqc.copy()
                runqc.save_expectation_value(Pauli(pauli[::-1]), list(range(n)), label='observable')
                oracle, at = timed(lambda: float(backend.run(runqc).result().data(0)['observable']), args.repeats)
                for budget in (64, 4096):
                    answer, rt = timed(lambda: plan_and_evaluate(compiled, pauli, max_terms=budget), args.repeats)
                    tracemalloc.start()
                    plan_and_evaluate(compiled, pauli, max_terms=budget)
                    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
                    error = abs(complex(answer.value)-oracle) if answer.available else None
                    valid = bool(answer.available and answer.exact and math.isfinite(error) and error <= 1e-9)
                    row = dict(family=family, n=n, query=query_name, pauli=pauli, max_terms=budget,
                        available=answer.available, exact_within_tolerance=valid,
                        answer_real=answer.value.real if answer.available else None,
                        answer_imag=answer.value.imag if answer.available else None,
                        reference=oracle, abs_error=error, route=answer.method, reason=answer.reason,
                        query_work_units=answer.work_units, query_work_unit=compiled.report.query_complexity_unit,
                        largest_intermediate=answer.largest_intermediate, intermediate_unit=answer.intermediate_unit,
                        query_promotions=answer.query_promotion_count, compiler_promotions=compiled.report.promotion_count,
                        query_fallback=compiled.report.query_fallback_used,
                        compilation_fallback=compiled.report.fallback_reason,
                        representation_size=compiled.closure.minimum_closed_representation_size,
                        query_tracemalloc_peak_bytes=peak, recognizer_rejections=rejection,
                        rqm_compile_ns=ct, rqm_query_ns=rt, qiskit_compile_ns=qt, aer_query_ns=at,
                        end_to_end_ratio=(statistics.median(qt)+statistics.median(at))/
                            (statistics.median(ct)+statistics.median(rt)) if valid else None)
                    rows.append(row)
                    (out/'rows.json').write_text(json.dumps(rows, indent=2)+'\n')
                    print(f'{family} n={n} {query_name} cap={budget} {answer.method} available={answer.available} error={error}', flush=True)
                    if answer.available and not valid: raise AssertionError(row)
    payload = dict(certification_manifest=manifest, repeats=args.repeats, seed=7300,
        benchmark_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        platform=platform.platform(), processor=platform.processor(),
        thread_settings={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')},
        timing_unit='nanoseconds', tolerance=1e-9,
        memory_measure='tracemalloc traced allocations during query only; not process RSS',
        intermediate_note='Largest individual array/tensor entries or retained Pauli terms, not total memory. '
                          'Star/chain bound is 16 complex entries; circuit storage remains O(n). '
                          'Pauli cap is tested after gate expansion and can overshoot. '
                          'Floating point evaluators prune coefficients below 1e-13; exact denotes the algebraic route.',
        baseline='Qiskit level-3 compilation plus single-thread Aer statevector native expectation; no full statevector export',
        rows=rows)
    (out/'benchmark.json').write_text(json.dumps(payload, indent=2)+'\n')


if __name__ == '__main__': main()
