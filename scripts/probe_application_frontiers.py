"""Post-integration Cartan controls, application queries and frontier scaling.

Run with the certified installed-wheel Python and one BLAS/OpenMP thread.
Application fixtures are fixed-parameter QAOA, Trotter and VQE energy evaluations,
not claims of solving an optimization problem or converging a ground state.
"""
import argparse
from dataclasses import asdict
import gc
import json
import math
from pathlib import Path
import statistics
import time
import tracemalloc
from types import MethodType
import numpy as np
from rqm_compiler import Circuit,compile_representation_aware,evaluate_observables
from rqm_compiler.frontier import plan_frontier,evaluate_frontier
from rqm_entanglement import CartanRelation,QuaternionCartanBlock
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from qiskit.quantum_info import Statevector,Pauli


def timed(fn,repeats=5):
    fn();samples=[]
    for _ in range(repeats):
        t=time.perf_counter_ns();value=fn();samples.append(time.perf_counter_ns()-t)
    return value,samples


def memory(fn):
    gc.collect();tracemalloc.start();before=tracemalloc.take_snapshot()
    value=fn();current,peak=tracemalloc.get_traced_memory();after=tracemalloc.take_snapshot();tracemalloc.stop()
    diff=after.compare_to(before,'traceback')
    return dict(peak_bytes=peak,retained_positive_blocks=sum(max(0,x.count_diff) for x in diff),
                retained_positive_bytes=sum(max(0,x.size_diff) for x in diff))


def legacy_promote(self):
    # Exact body of CartanRelation.promote at frozen baseline 34cb69e.
    return QuaternionCartanBlock.from_unitary(self.to_unitary())


def cartan_probe(seed):
    rng=np.random.default_rng(seed);rows=[]
    cases={'positive_noncanonical':(.8,.4,.2),'permuted_noncanonical':(-.2,-.8,0.),
           'outside_chamber':(-math.pi/2-1e-8,0.,0.),'canonical':(-.8,-.4,.2)}
    for name,coords in cases.items():
        relation=CartanRelation(*coords);old=MethodType(legacy_promote,relation);new=relation.promote
        for _ in range(20):old();new()
        pairs=[]
        for block in range(41):
            order=[old,new] if rng.random()<.5 else [new,old];elapsed={}
            for fn in order:
                t=time.perf_counter_ns()
                for _ in range(20):fn()
                elapsed['old' if fn==old else 'new']=(time.perf_counter_ns()-t)/20
            pairs.append(elapsed)
        ratios=np.array([x['old']/x['new'] for x in pairs])
        boot=np.median(ratios[rng.integers(0,len(pairs),(5000,len(pairs)))],axis=1)
        error=float(np.max(np.abs(old().to_unitary()-new().to_unitary())))
        assert error<1e-10
        rows.append(dict(case=name,coordinates=coords,paired_blocks=pairs,median_ratio=float(np.median(ratios)),
            paired_bootstrap_95_interval=list(np.quantile(boot,[.025,.975])),error=error,
            memory_old=[memory(old) for _ in range(3)],memory_new=[memory(new) for _ in range(3)]))
    return dict(seed=seed,rows=rows,inner_calls=20,blocks=41,
        note='Same-process alternating order; interval reflects paired block variation, not cross-machine uncertainty. Legacy expression uses the same installed dependencies as the new method.')


def label(n,items):
    out=['I']*n
    for q,p in items:out[q]=p
    return ''.join(out)


def application(family,n,depth):
    c=Circuit(n);terms=[];offset=0.
    edges=[(q,q+1) for q in range(n-1)]
    if family=='qaoa_maxcut':
        edges.append((n-1,0));weights=[1.+.1*(i%3) for i in range(len(edges))]
        for q in range(n):c.h(q)
        for layer in range(depth):
            gamma=.31+.07*layer;beta=.19+.03*layer
            for (a,b),w in zip(edges,weights):c.rzz(a,b,-gamma*w)
            for q in range(n):c.rx(q,2*beta)
        offset=sum(weights)/2
        terms=[(-w/2,label(n,[(a,'Z'),(b,'Z')])) for (a,b),w in zip(edges,weights)]
    elif family=='heisenberg_quench':
        for q in range(0,n,2):c.x(q)
        # First-order product formula for H=sum(XX+YY+0.7ZZ)+0.23 sum Z.
        for _ in range(depth):
            for a,b in edges:c.rxx(a,b,.18).ryy(a,b,.18).rzz(a,b,.126)
            for q in range(n):c.rz(q,.0414)
        terms=[(w,label(n,[(a,p),(b,p)])) for a,b in edges for p,w in [('X',1.),('Y',1.),('Z',.7)]]
        terms += [(.23,label(n,[(q,'Z')])) for q in range(n)]
    elif family=='vqe_ising':
        # A fixed hardware-efficient ansatz; report energy, not convergence.
        for layer in range(depth):
            for q in range(n):c.ry(q,.17*(q+1)+.11*layer)
            for a,b in edges:c.cx(a,b)
        terms=[(-1.,label(n,[(a,'Z'),(b,'Z')])) for a,b in edges]
        terms += [(-.7,label(n,[(q,'X')])) for q in range(n)]
    else:raise ValueError(family)
    return c,terms,offset


def application_probe():
    rows=[]
    for family in ('qaoa_maxcut','heisenberg_quench','vqe_ising'):
        for n in (6,10,14):
            for depth in (1,3):
                c,terms,offset=application(family,n,depth)
                compiled,compile_ns=timed(lambda:compile_representation_aware(c),3)
                state=Statevector.from_instruction(compiled_circuit_to_qiskit(c))
                output=Statevector.from_instruction(compiled_circuit_to_qiskit(compiled.circuit))
                fidelity=float(abs(np.vdot(state.data,output.data))**2)
                assert abs(1-fidelity)<1e-9
                labels=[p for _,p in terms]
                refs=[complex(state.expectation_value(Pauli(p[::-1]))) for p in labels]
                reference=offset+sum(w*v.real for (w,_),v in zip(terms,refs))
                for cap in (4,8):
                    fn=lambda:evaluate_observables(compiled,labels,max_terms=128,max_frontier_qubits=cap)
                    results,ns=timed(fn,3)
                    error=max((abs(r.value-v) for r,v in zip(results,refs) if r.available),default=0.)
                    assert error<1e-9
                    available=all(r.available for r in results)
                    energy=offset+sum(w*r.value.real for (w,_),r in zip(terms,results)) if available else None
                    if available:assert abs(energy-reference)<1e-9
                    # Keep all per-query telemetry; unavailable terms never become zeros.
                    queries=[]
                    for (w,p),r,v in zip(terms,results,refs):
                        q=asdict(r);q['value']=[r.value.real,r.value.imag];q.update(pauli=p,weight=w,reference=[v.real,v.imag]);queries.append(q)
                    rows.append(dict(family=family,n=n,depth=depth,cap=cap,terms=len(terms),
                        available_terms=sum(r.available for r in results),complete=available,energy=energy,reference_energy=reference,
                        max_term_error=float(error),energy_error=abs(energy-reference) if available else None,
                        compile_ns=compile_ns,query_batch_ns=ns,memory=memory(fn),queries=queries,
                        output_fidelity=fidelity,compiler_promotions=compiled.report.promotion_count,
                        compiler_kak=compiled.report.adaptive_routing.get('kak_invocations',0),
                        query_basis=compiled.report.query_evaluation_basis))
                    print(f'{family} n={n} depth={depth} cap={cap}: {sum(r.available for r in results)}/{len(terms)}',flush=True)
    return dict(rows=rows,pauli_term_cap=128,note=__doc__)


def dense_interactions(n):
    c=Circuit(n)
    for q in range(n):c.ry(q,.13*(q+1))
    for a in range(n):
        for b in range(a+1,n):c.rxx(a,b,.27).ry(a,.13).rzz(a,b,-.11)
    return c


def frontier_probe():
    rows=[]
    for n in (4,6,8,10):
        c=dense_interactions(n);labels='Z'*n
        reference=complex(Statevector.from_instruction(compiled_circuit_to_qiskit(c)).expectation_value(Pauli(labels)))
        for structured in ([True,False] if n<=8 else [True]):
            def fn():
                p=plan_frontier(c,labels,10);p.structured=structured
                return evaluate_frontier(p,labels)
            value,ns=timed(fn,5);err=abs(value-reference);assert err<1e-9
            rows.append(dict(n=n,width=plan_frontier(c,labels,10).width,structured=structured,
                payload_bytes=4**n*(8 if structured else 16),runtime_ns=ns,error=err,memory=memory(fn)))
            print(f'frontier width={n} structured={structured} error={err}',flush=True)
    rejections=[]
    for n in (12,16,24):
        c=dense_interactions(n)
        for cap in (4,8,10):
            plan,ns=timed(lambda:plan_frontier(c,'Z'*n,cap),21)
            assert not plan.accepted
            # evaluate_frontier must reject before either numerical evaluator.
            try:evaluate_frontier(plan,'Z'*n)
            except ValueError:pass
            else:raise AssertionError('over-cap plan evaluated')
            rejections.append(dict(n=n,cap=cap,width=plan.width,runtime_ns=ns,
                hypothetical_real_payload_bytes=8*4**plan.width,numeric_evaluation=False))
    return dict(rows=rows,rejections=rejections,note='Fresh planning and numeric caches per timed call. Complex reference route forced only through width 8. Width 10 is real only; widths 12/16/24 are planning-only rejection probes.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--certification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['cartan','applications','frontiers'],required=True)
    p.add_argument('--seed',type=int,default=1701);a=p.parse_args()
    manifest=json.loads((a.certification/'manifest.json').read_text());assert manifest['status']=='passed'
    import rqm_compiler,rqm_entanglement
    for m in (rqm_compiler,rqm_entanglement):assert str(a.certification.resolve()/'venv') in m.__file__
    result=cartan_probe(a.seed) if a.mode=='cartan' else application_probe() if a.mode=='applications' else frontier_probe()
    result['certification_manifest']=manifest
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('saved',a.output,flush=True)

if __name__=='__main__':main()
