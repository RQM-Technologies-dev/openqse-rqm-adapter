"""Compare selective compilation and batch reuse on certified installed wheels."""
import argparse,json,time,statistics
from pathlib import Path
from rqm_compiler import (Circuit,AdaptiveCartanPolicy,compile_representation_aware,
                         plan_and_evaluate,evaluate_observable,evaluate_observables,
                         lower_circuit_for_backend)
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from qiskit.quantum_info import Statevector,Pauli


def timed(fn):
    fn();samples=[]
    for _ in range(5):
        t=time.perf_counter_ns();result=fn();samples.append(time.perf_counter_ns()-t)
    return result,samples


def pair_windows(n,overlap):
    c=Circuit(n)
    for q in range(n):c.ry(q,.13*(q+1))
    pairs=[(q,q+1) for q in range(n-1)] if overlap else [(q,q+1) for q in range(0,n-1,2)]
    for a,b in pairs:
        for k in range(6):c.cx(a,b).ry(a,.17+.03*k).rz(b,-.23).rxx(a,b,.31)
    return c


def main():
    p=argparse.ArgumentParser();p.add_argument('--certification',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();m=json.loads((args.certification/'manifest.json').read_text())
    import rqm_compiler
    assert m['status']=='passed'
    assert str(args.certification.resolve()/'venv') in rqm_compiler.__file__
    args.output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for n in (4,8,12):
        for overlap in (False,True):
            c=pair_windows(n,overlap)
            state=Statevector.from_instruction(compiled_circuit_to_qiskit(c))
            for name in ('safe','balanced','aggressive'):
                policy=AdaptiveCartanPolicy.safe() if name=='safe' else getattr(AdaptiveCartanPolicy,name)(len(c.operations))
                compiled,ns=timed(lambda:compile_representation_aware(c,adaptive_policy=policy))
                labels=[x*n for x in 'XYZ']
                queried,qn=timed(lambda:evaluate_observables(compiled,labels))
                actual=[evaluate_observable(compiled.circuit,x) for x in labels]
                refs=[state.expectation_value(Pauli(x[::-1])) for x in labels]
                error=max(abs(r.value-v) for r,v in zip(queried+actual,refs+refs))
                assert all(r.available for r in queried+actual) and error<1e-9
                lowered=lower_circuit_for_backend(compiled.circuit,backend_family='braket_gate_model')
                rows.append(dict(n=n,family='overlapping_pairs' if overlap else 'disjoint_pairs',policy=name,
                    compile_ns=ns,query_batch_ns=qn,error=float(error),input_operations=len(c.operations),
                    compiled_operations=len(compiled.circuit.operations),lowered_operations=len(lowered.operations),
                    lowered_two_qubit_operations=sum(len(set(o.targets)|set(o.controls))==2 for o in lowered.operations),
                    input_two_qubit_operations=sum(len(set(o.targets)|set(o.controls))==2 for o in c.operations),
                    promotions=compiled.report.promotion_count,kak_invocations=compiled.report.adaptive_routing.get('kak_invocations',0),
                    representation_size=compiled.report.representation_complexity,verification=compiled.report.equivalence_status))
    reuse=[]
    for n in (8,12,32):
        c=Circuit(n).ry(0,.43)
        for q in range(1,n):c.rxx(0,q,.17).ry(0,.21).cx(q,0)
        compiled=compile_representation_aware(c)
        reference={}
        if n<=12:
            state=Statevector.from_instruction(compiled_circuit_to_qiskit(c))
            reference={a*n:complex(state.expectation_value(Pauli(a*n))) for a in 'XYZ'}
        for count in (1,10,100):
            labels=['XYZ'[i%3]*n for i in range(count)]
            independent,tn=timed(lambda:[plan_and_evaluate(compiled,label) for label in labels])
            batch,bn=timed(lambda:evaluate_observables(compiled,labels))
            assert all(r.available for r in batch+independent)
            assert max(abs(a.value-b.value) for a,b in zip(batch,independent))<1e-9
            error=max(abs(r.value-reference[label]) for r,label in zip(batch,labels)) if reference else None
            if error is not None:assert error<1e-9
            reuse.append(dict(n=n,queries=count,independent_ns=tn,batch_ns=bn,
                ratio=statistics.median(tn)/statistics.median(bn),reused_plans=sum(r.plan_reused for r in batch),
                max_error=error,oracle='Qiskit Statevector' if reference else 'uncached route agreement only',
                largest_intermediate=max(r.largest_intermediate for r in batch)))
    payload=dict(certification=m,policies=rows,reuse=reuse,repeats=5,
                 note='KAK counts are attempts; promotions are committed replacements. Lowered operation counts are actual Braket-profile descriptors, not hardware duration. At n=32 only cached/uncached agreement is checked.')
    (args.output/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(dict(policy_conditions=len(rows),reuse_conditions=len(reuse),max_error=max(r['error'] for r in rows))))

if __name__=='__main__':main()
