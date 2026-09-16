from rqm_openqse_adapter.openqse.contract import (
    ArtifactContract,
    rqm_quaternionic_compiler_contract,
)


def test_contract_is_machine_readable():
    contract = rqm_quaternionic_compiler_contract()
    data = contract.to_dict()

    assert data["pass_id"] == "rqm.quaternionic.compile"
    assert data["input"]["artifact_type"] == "LogicalCircuit"
    assert data["input"]["encoding"] == "RQMQuaternionicProgram"
    assert data["output"]["artifact_type"] == "LogicalCircuit"
    assert data["provenance"]["openqse_status"] == "experimental-unofficial"


def test_contract_accepts_declared_artifact_and_features():
    contract = rqm_quaternionic_compiler_contract()
    artifact = ArtifactContract(
        artifact_type="LogicalCircuit",
        encoding="RQMQuaternionicProgram",
        encoding_version="0.1",
        feature_profiles=("unitary-gates", "measurement", "extra-feature"),
    )
    assert contract.accepts(artifact)


def test_contract_rejects_wrong_encoding():
    contract = rqm_quaternionic_compiler_contract()
    artifact = ArtifactContract(
        artifact_type="LogicalCircuit",
        encoding="OpenQASM3",
        feature_profiles=("unitary-gates", "measurement"),
    )
    assert not contract.accepts(artifact)
