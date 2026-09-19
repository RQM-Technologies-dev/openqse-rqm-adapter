"""Supplement policy measurements with actual Qiskit basis synthesis counts.

This is a downstream compiler comparison, not a device execution measurement.
"""
import argparse,json
from pathlib import Path
from qiskit import transpile
from rqm_compiler import AdaptiveCartanPolicy,compile_representation_aware,lower_circuit_for_backend
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from probe_frontier_policies import pair_windows

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rows=[]
for n in (4,8,12):
 for overlap in (False,True):
  c=pair_windows(n,overlap)
  for name in ('safe','balanced','aggressive'):
   policy=AdaptiveCartanPolicy.safe() if name=='safe' else getattr(AdaptiveCartanPolicy,name)(len(c.operations))
   compiled=compile_representation_aware(c,adaptive_policy=policy)
   lowered=lower_circuit_for_backend(compiled.circuit,backend_family='braket_gate_model')
   qc=compiled_circuit_to_qiskit(lowered)
   row=dict(n=n,family='overlapping_pairs' if overlap else 'disjoint_pairs',policy=name,
            lowered_gate_names=sorted(set(o.gate for o in lowered.operations)))
   for level in (0,3):
    native=transpile(qc,basis_gates=['rz','sx','x','cx'],optimization_level=level,seed_transpiler=17)
    row[f'qiskit_level_{level}_cx']=int(native.count_ops().get('cx',0))
    row[f'qiskit_level_{level}_operations']=len(native.data)
   rows.append(row)
a.output.write_text(json.dumps({'basis':['rz','sx','x','cx'],'seed_transpiler':17,'rows':rows},indent=2)+'\n')
