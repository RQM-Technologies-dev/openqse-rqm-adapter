"""Check observable construction against known initial-state energies."""
import importlib.util
from pathlib import Path
import pytest
from qiskit.quantum_info import Statevector,Pauli
from rqm_qiskit.convert import compiled_circuit_to_qiskit

spec=importlib.util.spec_from_file_location('application_probes',Path(__file__).parents[1]/'scripts/probe_application_frontiers.py')
probes=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probes)

@pytest.mark.parametrize('family,expected',[
    ('qaoa_maxcut',(1.+1.1+1.2+1.)/2),
    ('heisenberg_quench',-.7*3),
    ('vqe_ising',-3.),
])
def test_zero_depth_application_energy(family,expected):
    circuit,terms,offset=probes.application(family,4,0)
    state=Statevector.from_instruction(compiled_circuit_to_qiskit(circuit))
    energy=offset+sum(w*state.expectation_value(Pauli(p[::-1])).real for w,p in terms)
    assert energy==pytest.approx(expected,abs=1e-12)
