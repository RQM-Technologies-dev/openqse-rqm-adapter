"""Independent Qiskit checks for generalized transfer and frontier queries."""
import itertools
import random
import numpy as np
import pytest
from qiskit.quantum_info import Statevector,Pauli
from rqm_compiler import Circuit, compile_representation_aware, evaluate_observable, evaluate_observables, AdaptiveCartanPolicy
from rqm_compiler.direct_readout import global_z_star
from rqm_qiskit.convert import compiled_circuit_to_qiskit


def oracle(c, label):
    return Statevector.from_instruction(compiled_circuit_to_qiskit(c)).expectation_value(Pauli(label[::-1]))


@pytest.mark.parametrize('hub',[0,1,2])
def test_hub_relabeling_and_all_product_observables(hub):
    c=Circuit(3)
    for q in range(3):c.ry(q,.23+.19*q)
    for q in range(3):
        if q!=hub:c.rxx(hub,q,.31+.11*q).cx(hub,q)
    assert abs(global_z_star(c,hub).value-oracle(c,'ZZZ'))<1e-9
    for q in range(3):c.rx(q,.17+.07*q).ry(q,-.23)
    for label in map(''.join,itertools.product('IXYZ',repeat=3)):
        r=evaluate_observable(c,label)
        assert r.available and abs(r.value-oracle(c,label))<1e-9
        assert r.method in ('star_product_transfer','direct_star_relational')


@pytest.mark.parametrize('seed',range(12))
def test_frontier_random_angles_orderings_and_queries(seed):
    rng=random.Random(seed);n=5;c=Circuit(n)
    for q in range(n):c.ry(q,rng.uniform(-2,2)).rz(q,rng.uniform(-2,2))
    for _ in range(12):
        a,b=rng.sample(range(n),2)
        c.rxx(a,b,rng.uniform(-2,2)).cx(a,b).ry(b,rng.uniform(-2,2))
    compiled=compile_representation_aware(c)
    labels=[''.join(rng.choice('IXYZ') for _ in range(n)) for _ in range(8)]
    results=evaluate_observables(compiled,labels,max_frontier_qubits=5)
    for label,r in zip(labels,results):
        assert r.available and abs(r.value-oracle(c,label))<1e-9
        assert r.largest_intermediate<=4**5


@pytest.mark.parametrize('angle',[0.,1e-14,1e-9,np.pi-1e-12,.31])
def test_frontier_interleaved_near_cancellation_and_revisit(angle):
    c=Circuit(4).h(2)
    c.rxx(2,0,angle).ry(2,.3).rzz(2,1,-angle).cx(1,2).rxx(2,0,-angle).ry(3,.7)
    for label in ('XYZZ','ZIII','IYII','IIII'):
        r=evaluate_observable(c,label,max_frontier_qubits=4)
        assert r.available and abs(r.value-oracle(c,label))<1e-9


def test_frontier_with_selectively_compiled_output_and_mutation():
    c=Circuit(4)
    for j in range(6):c.cx(3,1).ry(3,.13+j*.07).rz(1,-.17).rxx(3,1,.3)
    c.cx(1,0).ry(1,.8).cx(0,2)
    compiled=compile_representation_aware(c,adaptive_policy=AdaptiveCartanPolicy.aggressive(len(c.operations)))
    compiled.circuit.ry(2,.21) # invalidate source reuse; exercise actual compiled SU4 output
    for label,r in zip(['XYZZ','ZXYY'],evaluate_observables(compiled,['XYZZ','ZXYY'])):
        assert r.available and abs(r.value-oracle(compiled.circuit,label))<1e-9
