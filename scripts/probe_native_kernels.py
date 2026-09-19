"""Reproducible native-kernel probes; run unchanged in baseline/candidate wheel envs.

Timing, call instrumentation, and tracemalloc are separate runs. Snapshot blocks
are retained allocations, NOT cumulative allocator traffic. NumPy counters are
named API invocations, NOT unique allocations (nested calls can overlap).
"""
import argparse
from collections import Counter
from contextlib import ExitStack
import importlib
import json
from pathlib import Path
import statistics
import time
import tracemalloc
from unittest.mock import patch
import numpy as np
from rqm_compiler import Circuit
from rqm_compiler.observables import expectation_pauli
from rqm_compiler.direct_readout import product_star
from rqm_compiler.stable_prototype import global_z_chain
from rqm_compiler.frontier import plan_frontier,evaluate_frontier
from rqm_entanglement import CartanRelation,QuaternionCartanBlock
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from qiskit.quantum_info import Statevector,Pauli


def measure(fn):
    fn();samples=[]
    for _ in range(21):
        start=time.perf_counter_ns();result=fn();samples.append(time.perf_counter_ns()-start)
    calls=Counter()
    def counted(name,original):
        def wrapper(*a,**kw):
            calls[name]+=1
            return original(*a,**kw)
        return wrapper
    with ExitStack() as stack:
        for name in ('su4_blocks','observables','direct_readout','frontier','stable_prototype'):
            mod=importlib.import_module('rqm_compiler.'+name)
            for helper in ('_single_qubit_matrix','_operation_matrix'):
                if hasattr(mod,helper):stack.enter_context(patch.object(mod,helper,counted(name+'.'+helper,getattr(mod,helper))))
        for helper in ('array','zeros','empty','empty_like','outer','kron'):
            stack.enter_context(patch.object(np,helper,counted('numpy.'+helper,getattr(np,helper))))
        for cls,method in ((CartanRelation,'to_unitary'),(QuaternionCartanBlock,'from_unitary')):
            stack.enter_context(patch.object(cls,method,counted(cls.__name__+'.'+method,getattr(cls,method))))
        fn()
    tracemalloc.start();before=tracemalloc.take_snapshot();held=fn();current,peak=tracemalloc.get_traced_memory();after=tracemalloc.take_snapshot();tracemalloc.stop()
    diffs=after.compare_to(before,'traceback')
    return result,dict(runtime_ns=samples,median_ns=statistics.median(samples),calls=dict(calls),
        traced_peak_bytes=peak,retained_positive_blocks=sum(max(0,d.count_diff) for d in diffs),
        retained_positive_bytes=sum(max(0,d.size_diff) for d in diffs))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--label',required=True);args=p.parse_args()
    rows=[]
    for n in (4,12,32):
        local=Circuit(n)
        for q in range(n):local.ry(q,.11).rz(q,.31).rx(q,-.19)
        # One measured local support avoids exponential expansion in this stage.
        cases=[('local_observable',local,'X'+'I'*(n-1),lambda c,s:expectation_pauli(c,s).value)]
        star=Circuit(n)
        for q in range(n):star.ry(q,.11+.01*q)
        for q in range(1,n):star.rxx(0,q,.27).rzz(0,q,-.31).cx(q,0)
        cases.append(('hinge_star',star,'Z'*n,lambda c,s:product_star(c,s).value))
        chain=Circuit(n).ry(0,.41)
        for q in range(n-1):chain.rxx(q,q+1,.23).rzz(q,q+1,-.37).cx(q,q+1)
        cases.append(('hinge_chain',chain,'Z'*n,lambda c,s:global_z_chain(c).value))
        frontier=Circuit(n).ry(0,.43)
        for q in range(1,n):frontier.rxx(0,q,.17).ry(0,.21).cx(q,0)
        cases.append(('frontier',frontier,'Z'*n,lambda c,s:evaluate_frontier(plan_frontier(c,s,4),s)))
        for stage,c,labels,fn in cases:
            value,metrics=measure(lambda:fn(c,labels))
            ref=complex(Statevector.from_instruction(compiled_circuit_to_qiskit(c)).expectation_value(Pauli(labels[::-1]))) if n<=12 else None
            error=float(abs(value-ref)) if ref is not None else None
            if error is not None:assert error<1e-10,(stage,n,value,ref)
            rows.append(dict(stage=stage,n=n,value=[value.real,value.imag],error=error,**metrics))
    for n in (3,4,6):
        for generic in (False,True):
            c=Circuit(n)
            for q in range(n):c.ry(q,.17*(q+1))
            for a in range(n):
                for b in range(a+1,n):
                    c.rxx(a,b,.27).ry(a,.13)
                    if generic:c.cz(a,b)
            labels='Z'*n
            value,metrics=measure(lambda:evaluate_frontier(plan_frontier(c,labels,6),labels))
            ref=Statevector.from_instruction(compiled_circuit_to_qiskit(c)).expectation_value(Pauli(labels))
            error=float(abs(value-ref));assert error<1e-10
            plan=plan_frontier(c,labels,6)
            rows.append(dict(stage='generic_frontier' if generic else 'wide_frontier',n=n,
                frontier_width=plan.width,coefficient_payload_bytes=4**plan.width*(8 if getattr(plan,'structured',False) else 16),
                error=error,**metrics))
    for coords in ((-.8,-.4,.2),(.8,.4,.2)):
        relation=CartanRelation(*coords)
        result,metrics=measure(relation.promote)
        error=float(np.max(np.abs(result.to_unitary()-relation.to_unitary())))
        assert error<1e-10
        rows.append(dict(stage='canonical_cartan' if coords[0]<0 else 'noncanonical_cartan',n=2,error=error,**metrics))
    # Frontier boundary is structural and checked before numerical evaluation.
    boundaries=[]
    for n in (4,8,12):
        c=Circuit(n)
        for a in range(n):
            for b in range(a+1,n):c.rxx(a,b,.27).ry(a,.13)
        for cap in (2,4,8):
            plan,metrics=measure(lambda:plan_frontier(c,'Z'*n,cap))
            boundaries.append(dict(n=n,cap=cap,width=plan.width,accepted=plan.accepted,**metrics))
    import rqm_compiler,rqm_entanglement
    payload=dict(label=args.label,compiler_path=rqm_compiler.__file__,entanglement_path=rqm_entanglement.__file__,
        rows=rows,boundaries=boundaries,notes=__doc__,repeats=21)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(dict(rows=len(rows),boundaries=len(boundaries),max_error=max(r['error'] for r in rows if r['error'] is not None))))

if __name__=='__main__':main()
