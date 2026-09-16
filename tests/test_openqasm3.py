import math

import pytest

from rqm_openqse_adapter.diagnostics import UnsupportedConstructError
from rqm_openqse_adapter.openqasm3 import dumps_openqasm3, loads_openqasm3


BELL = '''OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c[0] = measure q[0];
c[1] = measure q[1];
'''


def test_openqasm3_bell_round_trip():
    program = loads_openqasm3(BELL, name="bell")
    assert program.num_qubits == 2
    assert program.num_clbits == 2
    emitted = dumps_openqasm3(program)
    assert "OPENQASM 3;" in emitted
    assert "h q[0];" in emitted
    assert "cx q[0], q[1];" in emitted
    reparsed = loads_openqasm3(emitted)
    assert reparsed.num_qubits == 2
    assert len(reparsed.to_module().operations) == 4


def test_openqasm3_rotation_pi_expression():
    program = loads_openqasm3('''OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
rx(pi/2) q[0];
''')
    value = program.to_module().operations[0].parameters[0].value
    assert value == pytest.approx(math.pi / 2)


def test_openqasm3_rejects_unknown_gate():
    with pytest.raises(UnsupportedConstructError):
        loads_openqasm3('''OPENQASM 3;
qubit[1] q;
unknown q[0];
''')
