# ORNL QCUP application — CSC751

## Submission record

| Field | Submitted value / recorded status |
| --- | --- |
| Program | OLCF Quantum Computing User Program (QCUP), Oak Ridge National Laboratory |
| Project ID | **CSC751** |
| Project title | Hardware Validation of Representation-Aware Quantum Compilation |
| Applicant | RQM Technologies LLC |
| Principal investigator | John Garman Van Geem |
| PI role | CEO; Professional Staff |
| Research area | Computer Science |
| Submission date | October 1, 2026 |
| Project duration | 12 months, as set by the application form |
| Requested resource | IBM Quantum through QCUP |
| Funding source | Other |
| Funding statement | No external research grant identified; requesting no-cost QCUP quantum computing allocation for RQM Technologies research. |
| Status | Application submitted; receipt confirmed by myOLCF. Project ID reported by the PI from ORNL correspondence. Approval, activation, and resource allocation are not established by this record. |

The PI supplied the following confirmation excerpt on October 1, 2026:

> note that your proposal has been assigned Project ID **CSC751**

This is a repository record of the submitted research request, not an ORNL-issued award or a raw form export. Research narrative fields below preserve the submitted wording; administrative selections are summarized. Private contact, address, citizenship, and account details are omitted.

We requested **no-cost quantum computing research access**, not a cash grant. The form displayed **0 allocated hours** in a disabled field. This is not a request for zero useful compute or evidence of an awarded allocation: the proposal commits to estimating vendor-billable time and requesting a specific allocation after project approval.

## Project Summary

This project will test whether representation-aware compilation of standard quantum circuits can reduce physical execution cost while preserving computational semantics on real quantum hardware. RQM Technologies will compare a frozen RQM compiler pipeline against a matched Qiskit baseline using small spin-model time-evolution circuits, shallow hardware-efficient circuits, and diagnostic one- and two-qubit blocks. The scientific question is when compact SU(2) and two-qubit relational representations translate into lower native gate counts or depth and more accurate measured observables after hardware mapping, and when they provide no benefit.

We request an initial IBM Quantum pilot through QCUP, using the existing RQM-to-Qiskit bridge. All proposed workloads use public, synthetic circuits and standard quantum mechanics. Ideal simulation and numerical equivalence checks will precede hardware execution. Paired experiments will hold the backend, layout policy, transpiler settings, shots, and measurement definitions fixed, with repeated interleaved runs to assess drift. Outputs will include reproducible circuit artifacts, compiler reports, hardware results, statistical uncertainty, and negative results. Classical observable-evaluation speedups will be reported separately from physical hardware performance; no hardware advantage is assumed.

## Scientific Significance

Quantum hardware performance depends on the compiled native circuit, not only on the source algorithm. Equivalent circuit representations can affect synthesis, routing, gate count, and execution duration, but a smaller intermediate representation does not necessarily produce a better physical experiment. This study will establish the conditions under which structure-preserving SU(2) and Cartan-based compilation improves, matches, or worsens measured observables for small quantum-simulation workloads. Spin-model observables provide a scientifically meaningful application with classically verifiable reference values. Publishing the complete workload set, fallback cases, and uncertainty will help distinguish representation-level savings from actual hardware benefits and inform interoperable quantum compiler interfaces.

## Scientific Objectives

1. Verify preservation of standard circuit semantics through RQM optimization, Qiskit lowering, and native backend transpilation using ideal reference calculations and documented numerical tolerances.
2. Quantify changes in native two-qubit gate count, two-qubit depth, total depth, and scheduled duration where available. Measure compilation wall time separately.
3. Compare measured local Z and nearest-neighbor ZZ observables against exact references for small spin-model evolution and shallow variational-style circuits. For diagnostic circuits, compare output distributions without treating distribution agreement as full state/process fidelity.
4. Identify workload structure and target constraints associated with gains, no change, regressions, and conservative fallback. No universal speedup or fidelity advantage is presumed.
5. Release a reproducible, version-pinned benchmark and analysis with confidence intervals, backend/calibration metadata, and all attempted conditions, including unsuccessful or null outcomes.

## Proposed Technical Approach

Freeze source commits, package versions, circuit generators, parameter seeds, and the analysis plan before QPU execution. Construct 30 source conditions spanning diagnostic SU(2)/two-qubit blocks, 4-8-qubit spin-chain product-formula evolution, and shallow hardware-efficient circuits. Include structure-breaking controls. Use terminal computational-basis measurements; local Z and ZZ observables can be obtained from the same bitstrings. Dynamic circuits, pulse-level control, and QEC claims are outside this pilot.

For each condition compare (A) source circuit followed by a pinned Qiskit transpilation pipeline and (B) RQM optimization and verified Qiskit lowering followed by the same final transpilation pipeline. Match backend target, initial layout policy, transpiler seeds, optimization level, and measurement mapping. Retain conservative fallback circuits and report their frequency. Verify small blocks numerically and check full-circuit ideal outputs at these small sizes before submission. Reject discrepancies beyond the declared tolerance rather than interpreting hardware noise as a correctness test.

Run a six-condition smoke test at 1,024 shots per pipeline, followed by 30 conditions x 2 pipelines x 4,096 shots x 3 interleaved repeat batches on one IBM backend. This is 749,568 total planned shots including the smoke test. Estimate billable QPU time from the actual ISA circuits using the vendor estimator before requesting allocation; shot count alone is not a time estimate. Reduce scope if required by the approved budget. No automatic resubmission of chargeable jobs will occur without checking job status and recorded identifiers.

Report native gate counts, depth, duration where available, and compilation latency. Primary hardware endpoints are absolute local-Z/ZZ observable errors relative to exact simulation and paired differences between pipelines. Report finite-shot confidence intervals and variation across repeat batches; randomize/interleave execution order to reduce calibration-drift confounding. Raw unmitigated results are primary. Any optional mitigation must be applied symmetrically and reported separately. Publish reproducible artifacts and null or negative findings.

### Workload arithmetic

| Phase | Calculation | Planned shots |
| --- | --- | ---: |
| Smoke test | 6 conditions × 2 pipelines × 1,024 shots | 12,288 |
| Paired comparison | 30 conditions × 2 pipelines × 4,096 shots × 3 repeat batches | 737,280 |
| Total | Smoke test + paired comparison | **749,568** |

These are proposed experiments, not completed runs or approved credits.

## Team Members

Proposed principal investigator: John Van Geem, CEO, RQM Technologies LLC. Responsible for compiler integration, experiment preparation, execution, analysis, and public reporting. No additional project members or ORNL collaborators are claimed in this application.

## Justification for Resources

Real QPU access is needed to determine whether verified compiler transformations improve measured observables under physical noise, calibration drift, connectivity, and native gate constraints. Ideal simulation establishes reference semantics but cannot establish these hardware outcomes. IBM Quantum is the initial requested platform because an RQM-to-Qiskit execution bridge already exists. The proposed bounded pilot uses at most 8 qubits and 749,568 shots on one backend (12,288 smoke-test shots plus 737,280 comparison shots). This is a proposed workload budget, not a completed resource estimate or approved allocation. Before execution, transpile to an available QCUP target and submit a vendor-based estimate of QPU time, including applicable overhead, through the QCUP allocation process. No dedicated long-duration reservation or large HPC allocation is requested for this pilot.

## Simulations

Existing public repository evidence documents numerical semantic verification, OpenQASM 3 export/re-import checks, and exact-observable comparisons in the RQM ecosystem. The openqse-rqm-adapter README records a clean ecosystem demonstration with 1,874 passed and 11 skipped tests, and links later fixed-candidate scientific evidence with 2,255 passed and 11 skipped tests. These are historical recorded software results, not new runs for this application and not proof of hardware advantage. Sources: https://github.com/RQM-Technologies-dev/openqse-rqm-adapter and its docs/CONFORMANCE_EVIDENCE.md and evidence/scientific-candidate-2026-09-19/. The exact proposed 30-condition hardware corpus, backend-specific noise simulations, and billable-time estimates will be generated and checked before a hardware allocation request.

## Prepared Code

Prepared software includes rqm-core (quaternion/SU(2) mathematics), rqm-entanglement (two-qubit relational and Cartan mathematics), rqm-circuits (public circuit schema), rqm-compiler (representation-aware optimization with verification and fallback), and rqm-qiskit (Qiskit lowering, execution, result handling, and numerical assurance). The openqse-rqm-adapter provides a reproducible OpenQASM 3 interoperability demonstration and evidence reports. The proposed study will use frozen, tested commits rather than assume README version labels or unreleased candidates are production releases. Existing tests and execution interfaces are available; the dedicated matched hardware benchmark harness and resource estimate remain preparation tasks.

## Software Used including website URLs

Python; Qiskit, Qiskit Aer, and qiskit-ibm-runtime (https://github.com/Qiskit); NumPy and SciPy. RQM research packages: https://github.com/RQM-Technologies-dev/rqm-core ; https://github.com/RQM-Technologies-dev/rqm-circuits ; https://github.com/RQM-Technologies-dev/rqm-entanglement ; https://github.com/RQM-Technologies-dev/rqm-compiler ; https://github.com/RQM-Technologies-dev/rqm-qiskit . Interoperability demonstration: https://github.com/RQM-Technologies-dev/openqse-rqm-adapter . Use public source with pinned versions/commits and recorded licenses; access to IBM hardware is through the approved QCUP allocation.

## Data Models Used

Synthetic standard gate-model quantum circuits, OpenQASM 3 exchange artifacts, RQM circuit descriptors and compiler reports, and native Qiskit circuits. Reference data consists of ideal state-vector probabilities and local Pauli expectation values for small circuits. Experimental data consists of measurement counts, shot counts, backend/job identifiers, timing, available calibration metadata, and statistical summaries. No trained machine-learning model or personal/clinical dataset is required. Proposed data-management plan: version circuit generators and analysis scripts, retain raw results and provenance with checksums, remove credentials and account-sensitive metadata before publication, and publish a reproducible research dataset with the final report subject to vendor data-sharing terms.

## Data Management Plan

Version and preserve source circuits, parameter seeds, package versions/commit identifiers, compiler and transpiler configuration, numerical verification results, native circuit metrics, raw measurement counts, shot counts, job identifiers, execution dates, available calibration metadata, and analysis scripts. Maintain checked copies of raw data and a machine-readable manifest with checksums; never store authentication tokens in research artifacts. Publish the synthetic workload corpus, reproducible analysis, and results including null or negative findings in a public RQM research repository and a suitable archival repository with the final report, subject to vendor data-sharing terms. Exclude credentials, account identifiers, and other access-sensitive metadata from public exports. No personal, clinical, classified, or controlled research dataset is proposed. Retain sufficient provenance for independent reproduction and submit required QCUP reporting.

## Classification and policy selections

The submitted project was classified as publishable, fundamental/publicly available research. The application answered No to use or generation of proprietary or sensitive/restricted data, use of proprietary software, human health data, military/spacecraft/satellite/missile work, nuclear-reactor or enrichment work, 128-bit-or-greater encryption source/object code, weapons of mass destruction, and ITAR work. These answers describe this proposed open compiler benchmark, not every activity of RQM or the PI.

All five policies were accepted: OLCF Computing, Data Management, Security, Institutional User Agreement, and Project Reporting. The PI authorized the final accuracy certification and submission. The following clarification was included in the Comments field.

## Comments submitted

RQM Technologies LLC requests no-cost QCUP research access. We agree to abide by the OLCF policies and to execute any required Institutional User Agreement with UT-Battelle before project activation or resource access. We cannot confirm that an institutional agreement is currently on file; our policy acceptance is a commitment to comply, not a representation that an agreement has already been executed. Please provide any required agreement and onboarding instructions. We understand from OLCF accounts and QCUP access guidance that agreement paperwork is addressed during project activation following proposal approval.

## Follow-up checklist

- [x] Submit project application and receive myOLCF receipt.
- [x] Record ORNL-assigned Project ID **CSC751** from PI-provided correspondence.
- [ ] Receive and record the proposal review decision.
- [ ] Complete any required PI/institutional agreements and account activation.
- [ ] Freeze tested source commits, dependencies, circuit corpus, seeds, and analysis plan.
- [ ] Build the matched hardware benchmark harness and run numerical/simulator checks.
- [ ] Produce vendor-specific QPU runtime estimates and request a bounded allocation.
- [ ] Execute the smoke test, then approved paired comparisons.
- [ ] Publish reproducible evidence and required project reports.

Project-ID assignment alone does not establish approval, hardware access, an awarded compute budget, ORNL collaboration, or OpenQSE endorsement.

## Official application and onboarding references

- [myOLCF project application](https://my.olcf.ornl.gov/project-application-new)
- [QCUP access, review, activation, and credit allocation guidance](https://docs.olcf.ornl.gov/quantum/quantum_access.html)
- [OLCF project activation and institutional agreements](https://docs.olcf.ornl.gov/accounts/accounts_and_projects.html)
- [OLCF policies](https://docs.olcf.ornl.gov/accounts/olcf_policy_guide.html)

This record captures the October 1, 2026 submission. Later changes to the experiment or award status should be recorded separately rather than silently rewriting the submitted scope.
