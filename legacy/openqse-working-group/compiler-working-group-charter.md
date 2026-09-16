# openQSE Compiler Working Group

**Contact:** [Michael Ferguson](mailto:michael.ferguson@hpe.com), [Narasinga Rao Miniskar](mailto:miniskarnr@ornl.gov)

## Charter and Scope

The openQSE Compiler Working Group will define the middleware compilation layer that connects quantum software development kits to QPU-facing execution systems. The layer will provide portable translation and compilation paths across SDK outputs, compiler intermediate representations, circuit interchange formats, and provider-specific inputs.

The goal is to support vendor-neutral quantum and hybrid quantum-classical workflows without requiring every SDK to integrate separately with every QPU. The group will define stable interfaces at major compilation boundaries while allowing compiler implementations to use the representations and passes best suited to each stage.

### In Scope

- Define the openQSE middleware compiler component and its interfaces within the reference architecture.
- Identify preferred compiler IRs at major stage or system boundaries while supporting a multi-IR compilation model.
- Identify preferred circuit interchange formats and provide adapters for additional SDK and provider formats.
- Define translation paths between SDK outputs and QPU- or provider-facing inputs.
- Describe compiler stages such as synthesis, lowering, mapping, optimization, and backend generation so that stages can be extended or replaced.
- Support application-specific and hardware-specific passes through clear extension points, and promote reusable passes when common patterns emerge.
- Address hybrid quantum-classical programs, including control flow, mid-circuit measurement, feed-forward, and real-time or near-time execution constraints.
- Include FTQC and QEC requirements in the compiler architecture, IR analysis, and reference implementation design.
- Define the target properties and constraints required from resource interfaces, runtimes, provider services, and control layers.
- Develop and evaluate a prototype reference implementation that connects existing compiler components.
- Produce compiler requirements for the broader openQSE architecture and a survey of quantum compiler technologies.

### Out of Scope

- Replacing the complete compilation stacks provided by SDKs, QPU vendors, or provider services.
- Requiring one universal IR for all compiler stages or one implementation technology for all openQSE compilers.
- Mandating a single vendor-associated compiler stack or circuit format.
- Owning resource discovery, scheduling, allocation, or runtime dispatch.
- Defining the serialization or API used by the Quantum Resource Interface to expose target information.
- Standardizing pulse generation, firmware behavior, device-control protocols, or other control-electronics implementation details.

## Milestones and Actionable Items

### Working Group Launch

- Establish a biweekly, one-hour meeting cadence and confirm named participants.
- Gather presentations on candidate compiler and IR approaches, including Qiskit, Hugr, MLIR-based compilers, Amazon Braket, and other SDK or tool ecosystems.
- Establish shared definitions for compiler IRs, interchange formats, compiler stages, and hybrid execution boundaries.
- Inventory existing quantum compilers, their IRs, supported passes, target formats, test strategies, and quantum-classical capabilities.
- Collect compiler requirements from the Quantum Resource Interface, System Architecture, Runtime, and Control Electronics working groups.

### Six-Month Milestones

- Produce a draft survey paper covering quantum compiler IRs and passes, commonality and divergence among tools, and available testing approaches.
- Document FTQC and QEC assumptions that affect representations, passes, cost models, scalability, and target requirements.
- Compare support for hybrid quantum-classical control and identify the boundaries between real-time and near-time processing.
- Define criteria for selecting preferred IRs and interchange formats at openQSE interfaces.
- Evaluate how candidate tools scale with qubit count, gate count, circuit size, and serialized payload size.

### Twelve-Month Milestones

- Deliver compiler-related requirements for the openQSE architecture documentation.
- Draft a specification for the openQSE compiler component, stage boundaries, extension points, and interfaces with adjacent components.
- Build a prototype reference implementation that connects selected SDK, compiler, runtime, and provider components through defined interfaces.
- Demonstrate translation across representative input and output formats and document gaps discovered through the prototype.
- Keep the prototype FTQC-aware by preserving extension points and information required for QEC-oriented compilation, without treating full FTQC support as a first-year deliverable.

## Participants

### Working Group Leads

- Michael Ferguson, HPE — lead
- Narasinga Rao Miniskar, ORNL — co-lead

### Contributors

- Edison Murairi, Alice & Bob
- Kevin Kissel, Alice & Bob
- Nils Quetschlich, Amazon
- Matt Treinish, IBM
- Matthias Traube, MQSC
- Lukas Burgholzer, MQSC
- Simon Hofmann, MQSC
- Santiago Nunez Corrales, ORNL
- Sangram Deshpande, ORNL student contributor
- Ulrik De Meulenaere, ORNL student contributor
- Marco Ghibaudi, Riverlane
- Adam Melvin, Riverlane
- Neal Erickson, Quantinuum
- Stefan Krastanov, QuEra
- Neal Erickson, Quantinuum

### Workshop Contributors

- Jeff Heckey, AWS Braket — OpenQASM 3 functional-coverage presentation
- Santiago Núñez-Corrales, Illinois — quantum abstract-machine presentation
- Narasinga Rao Miniskar, ORNL — FTQC compiler and Q-IRIS runtime

## Interaction With Other Working Groups

### Quantum Resource Interface

The Compiler Working Group will define the target information needed for translation, mapping, optimization, and backend generation. Required properties are expected to include target identity, qubit capacity, modality, supported operations, and accepted interchange formats. Optional properties may include connectivity, per-qubit or per-operation data, error rates, calibration data, and topology. Custom properties can express modality- or provider-specific constraints consumed by matching compiler passes.

FTQC targets may also need to expose logical error rates, supported error-correction capabilities, available runtime QEC operations, and which compilation tasks the backend can perform. The Compiler Working Group will specify the semantics of the information it consumes. The Quantum Resource Interface Working Group will own the schemas, APIs, and transport mechanisms used to expose that information.

The groups will also define the handoff to provider- or device-side compilers, including target queries, accepted program formats, and error reporting when a compiled artifact is incompatible with a selected resource.

### System Architecture

The Compiler Working Group will coordinate with the System Architecture Working Group to place adapters, compiler services, provider compilation, and execution handoffs within the openQSE reference architecture. The architecture must support compilation on local systems, HPC resources, provider services, or a combination of these locations without changing application-level intent.

The compiler group will provide requirements for preferred interchange formats, IR boundaries, component interfaces, deployment choices, and extension points. The System Architecture Working Group will use those requirements to define how the compiler participates in end-to-end hybrid workflows and how it interacts with SDKs, data services, security boundaries, and QPU providers.

### Runtime

The Compiler and Runtime working groups will jointly define what is compiled before submission and what remains configurable or transformable during execution. Their interface should carry compiled artifacts, target assumptions, entry points, parameter bindings, control-flow information, execution constraints, and any metadata needed to decide whether recompilation is required.

Coordination is especially important for mid-circuit measurement, feed-forward, dynamic circuits, runtime QEC operations, and latency-sensitive classical processing. The groups will distinguish coherence-time-critical behavior from near-time runtime services and identify which component owns each decision.

The interface should also allow runtime resource selection or capability changes to trigger compiler validation, target-specific lowering, or recompilation without embedding compiler internals in the runtime.

### Control Electronics

The Compiler Working Group will coordinate with the Control Electronics Working Group on the boundary between compiled programs and device-level execution. The control layer should describe the supported operations, timing constraints, feedback capabilities, calibration dependencies, QEC primitives, and accepted low-level representations that affect compilation.

The compiler will preserve and lower the program semantics needed at this boundary. Pulse generation, firmware sequencing, decoder integration, and hardware-specific feedback loops remain responsibilities of the control system or provider stack. Some final lowering may occur near the device when it depends on fresh calibration data or tight timing constraints.

The groups will define artifact versioning, capability matching, diagnostics, and failure behavior so that unsupported operations or stale assumptions are detected before device execution whenever possible.
