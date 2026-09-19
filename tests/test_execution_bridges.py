"""Software-only checks of both SDK routes on an asymmetric three-qubit fixture."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector
from braket.devices import LocalSimulator
from rqm_compiler import Circuit, compile_representation_aware, lower_circuit_for_backend
from rqm_braket.translator import to_backend_circuit
from rqm_qiskit.convert import compiled_circuit_to_qiskit
from rqm_openqse_adapter.ecosystem.pipeline import _verify_qiskit_operators


def test_both_bridges_preserve_asymmetric_compiled_program():
    source = Circuit(3)
    source.h(2); source.ry(0, .37); source.rxx(2, 0, .29)
    source.rzz(1, 2, -.43); source.cx(2, 1); source.rx(1, .19)
    oracle = QuantumCircuit(3)
    oracle.h(2); oracle.ry(.37, 0); oracle.rxx(.29, 2, 0)
    oracle.rzz(-.43, 1, 2); oracle.cx(2, 1); oracle.rx(.19, 1)
    candidate = compile_representation_aware(source)
    assert candidate.report.equivalence_verified
    lowered = lower_circuit_for_backend(candidate.circuit, backend_family='braket_gate_model')
    qiskit_output = compiled_circuit_to_qiskit(lowered)
    assert _verify_qiskit_operators(oracle, qiskit_output, boundary='Qiskit bridge') < 1e-9
    braket_output = to_backend_circuit(lowered, optimize=False)
    # Braket orders q0 as the most significant bit; Qiskit uses the least.
    permutation = [int(f'{i:03b}'[::-1], 2) for i in range(8)]
    unitary = braket_output.to_unitary()[np.ix_(permutation, permutation)]
    assert _verify_qiskit_operators(oracle, Operator(unitary), boundary='Braket bridge') < 1e-9
    braket_output.probability(target=[0, 1, 2])
    probabilities = LocalSimulator().run(braket_output, shots=0).result().values[0]
    np.testing.assert_allclose(np.asarray(probabilities)[permutation],
                               Statevector.from_instruction(oracle).probabilities(), atol=1e-9, rtol=0)
