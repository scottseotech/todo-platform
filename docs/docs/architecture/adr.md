# Architecture Decision Records

## Why Document Decisions

Production systems evolve over time. **Architecture Decision Records (ADRs)** capture the reasoning behind key technical choices, making it easier for teams to understand:

- **What** decisions were made
- **Why** those decisions were made
- **What alternatives** were considered
- **What tradeoffs** were accepted

This prevents repeated debates, helps onboard new team members, and provides historical context for future refactoring.


## ADR-000: Use a Todo List Application as the Core Demo

**Status:** Accepted

??? note "Show details"
    **Context:**

    The goal of this project is not to build another task management application, but to demonstrate end-to-end production practices across modern DevOps disciplines — including infrastructure as code, GitOps, CI/CD, observability, and self-hosted automation runners.

    A lightweight app such as a todo list provides just enough complexity (API, database, UI) to anchor the supporting infrastructure while staying simple enough to keep focus on the platform engineering aspects.

    **Decision:**

    Use a simple todo list application as the reference workload for demonstrating:
    - Kubernetes-based deployment
    - ArgoCD-driven GitOps workflows
    - ChatOps integrations via Slack for operational feedback and control
    - Observability stack (Prometheus, Grafana, Tempo, Loki)
    - CI/CD pipelines executing on a self-hosted GitHub Actions Runner Controller (ARC)
    - Documentation and automation with MkDocs, Kustomzie, and IaC tooling

    The application itself remains minimal — serving as a stable target to validate automation, reliability, and environment consistency.

    **Alternatives Considered:**

    1. **Custom complex microservice project** – Would showcase more application logic but obscure the infrastructure focus and slow iteration.
    2. **Off-the-shelf benchmark app (e.g., Sock Shop, Hipster Shop)** – Provides realistic architecture but adds unnecessary moving parts and less control over the full lifecycle.

    **Consequences:**

    ✅ **Positive:**
    - Keeps cognitive load low while demonstrating full production-grade DevOps stack
    - Enables reproducible demos of CI/CD, GitOps, and ChatOps workflows
    - Clear isolation of infrastructure competency from application logic
    - Simplifies troubleshooting, monitoring, and performance testing

    ❌ **Negative:**
    - Application is not innovative or feature-rich, so less compelling as a product demo
    - May undersell application-level engineering depth to non-technical audiences
    - Requires extra explanation that the value lies in platform automation, not app features

---

## ADR-001: GitOps with ArgoCD

**Status:** Accepted

??? note "Show details"
    **Context:**

    Deployments need to be:
    - Reproducible and auditable
    - Automated without manual kubectl commands
    - Version-controlled with rollback capability
    - Accessible to the entire team without requiring cluster credentials

    **Decision:**

    Use ArgoCD for GitOps-based continuous deployment where:
    - Git repository is the single source of truth
    - All infrastructure and application manifests are declared in Git
    - ArgoCD automatically syncs cluster state to match Git
    - Deployments happen through Git commits, not imperative commands

    **Alternatives Considered:**

    1. **FluxCD** - Another GitOps tool, but ArgoCD has better UI and visualization
    2. **Manual kubectl** - Not scalable, no audit trail, requires cluster access
    3. **Helm + CI/CD** - Imperative, doesn't continuously reconcile state

    **Consequences:**

    ✅ **Positive:**
    - Complete audit trail of all changes
    - Easy rollback via Git revert
    - No need to distribute kubeconfig
    - Self-healing (ArgoCD reconciles drift)
    - Visual UI for deployment status

    ❌ **Negative:**
    - Additional component to manage
    - Learning curve for GitOps workflow
    - Slightly slower than direct kubectl apply

---

## ADR-002: Self-Hosted GitHub Actions Runners

**Status:** Accepted

??? note "Show details"
    **Context:**

    CI/CD pipelines need to:
    - Build and push Docker images
    - Update Kubernetes manifests
    - Verify deployments in the cluster
    - Control costs for high-frequency builds

    GitHub-hosted runners have limitations:
    - No access to in-cluster resources
    - Limited to public IP addresses
    - No persistent caching
    - Can be expensive at scale

    **Decision:**

    Use Actions Runner Controller (ARC) to run self-hosted GitHub Actions runners inside the Kubernetes cluster.

    **Alternatives Considered:**

    1. **GitHub-hosted runners** - No cluster access, higher cost, no caching
    2. **Jenkins** - More complex, requires separate infrastructure
    3. **GitLab CI** - Would require migrating from GitHub

    **Consequences:**

    ✅ **Positive:**
    - Direct kubectl access for deployment verification
    - Faster builds with Docker layer caching
    - Lower cost (runs on existing cluster resources)
    - Custom runner images with pre-installed tools
    - Auto-scaling based on job queue

    ❌ **Negative:**
    - Additional infrastructure to maintain
    - Security considerations (runners have cluster access)
    - Need to manage runner lifecycle

---

## ADR-003: OpenTelemetry for Observability

**Status:** Accepted

??? note "Show details"
    **Context:**

    Distributed systems need comprehensive observability:
    - Trace requests across service boundaries
    - Correlate logs with traces
    - Monitor performance metrics
    - Avoid vendor lock-in with proprietary agents

    **Decision:**

    Use OpenTelemetry SDK for instrumentation with:
    - OTLP protocol for traces → Tempo
    - Structured JSON logs → Fluent Bit → Loki
    - Prometheus metrics exposition
    - W3C Trace Context propagation

    **Alternatives Considered:**

    1. **Datadog/New Relic APM** - Proprietary, expensive, vendor lock-in
    2. **Jaeger SDK** - Traces only, not the industry standard going forward
    3. **Custom logging** - No standardization, difficult to correlate

    **Consequences:**

    ✅ **Positive:**
    - Vendor-neutral (can swap backends without code changes)
    - Industry standard (CNCF graduated project)
    - Single SDK for traces, metrics, and logs
    - W3C standard trace propagation
    - Strong community and tooling support

    ❌ **Negative:**
    - Slightly more complex than vendor SDKs
    - Performance overhead (mitigated with sampling)
    - Need to run backend infrastructure (Tempo, Loki, Prometheus)

---

## ADR-004: CloudNativePG for PostgreSQL

**Status:** Accepted

??? note "Show details"
    **Context:**

    Application needs a production-grade PostgreSQL database with:
    - High availability and automatic failover
    - Automated backups and point-in-time recovery
    - Declarative Kubernetes-native configuration
    - Minimal operational overhead

    **Decision:**

    Use CloudNativePG operator to manage PostgreSQL clusters:
    - Declarative cluster definition
    - Automatic failover and self-healing
    - Continuous backup to S3 (MinIO)
    - Built-in monitoring and metrics

    **Alternatives Considered:**

    1. **StatefulSet + manual setup** - No automation, complex failover
    2. **Zalando Postgres Operator** - More complex, less active development
    3. **Managed RDS/Cloud SQL** - Vendor lock-in, higher cost, external dependency
    4. **CrunchyData Operator** - Commercial focus, heavier resource usage

    **Consequences:**

    ✅ **Positive:**
    - Fully automated HA with no manual intervention
    - Backup automation with retention policies
    - Kubernetes-native (CRDs and operators)
    - Active CNCF sandbox project
    - Great documentation and community

    ❌ **Negative:**
    - Operator adds complexity
    - Learning curve for CNPG concepts
    - Resource overhead (multiple pods for HA)

---

## ADR-005: Model Context Protocol (MCP) for AI Integration

**Status:** Accepted

??? note "Show details"
    **Context:**

    Platform needs AI-powered natural language interface:
    - Allow users to manage todos via conversation
    - Integrate with modern LLMs (OpenAI, Claude, etc.)
    - Avoid tight coupling to specific AI vendors
    - Provide structured tool calling interface

    **Decision:**

    Implement Model Context Protocol (MCP) server:
    - Standardized protocol for AI-application integration
    - Tool-based interface for todo operations
    - Compatible with any MCP-compliant AI system
    - Clean abstraction between AI and business logic

    **Alternatives Considered:**

    1. **Direct OpenAI API integration** - Vendor lock-in, no portability
    2. **LangChain** - Heavy framework, Python-centric
    3. **Custom REST API + prompting** - No standardization, reinventing the wheel

    **Consequences:**

    ✅ **Positive:**
    - Future-proof against AI vendor changes
    - Industry standard protocol (Anthropic-backed)
    - Clean separation of concerns
    - Reusable across different AI frontends
    - Demonstrates modern AI integration patterns

    ❌ **Negative:**
    - Emerging standard (not fully mature)
    - Limited tooling compared to established frameworks
    - Additional service to maintain

---

## ADR-006: Kustomize over Helm

**Status:** Accepted

??? note "Show details"
    **Context:**

    Kubernetes manifests need:
    - Environment-specific customization (dev, staging, prod)
    - Image version management
    - No complex templating logic
    - Integration with GitOps workflow

    **Decision:**

    Use Kustomize for manifest management:
    - Declarative patches over base manifests
    - Built-in image tag management
    - Native kubectl integration
    - ArgoCD has first-class Kustomize support

    **Alternatives Considered:**

    1. **Helm** - Template complexity, values.yaml indirection, package management not needed
    2. **Plain YAML** - No reusability, duplication across environments
    3. **Jsonnet/Dhall** - Requires learning new language, less ecosystem support

    **Consequences:**

    ✅ **Positive:**
    - Simple overlay model (easy to understand)
    - No templating language to learn
    - Built into kubectl
    - Clean image version updates via CLI
    - ArgoCD native support

    ❌ **Negative:**
    - Less powerful than Helm for complex scenarios
    - No package registry/versioning
    - Cannot conditionally include resources easily

---

## ADR-007: MinIO for S3-Compatible Storage

**Status:** Accepted

??? note "Show details"
    **Context:**

    Platform needs object storage for:
    - PostgreSQL continuous backups (CNPG)
    - Log archival (Loki)
    - Potential future use cases (file uploads, exports)
    - Local development and testing
    - Cost control

    **Decision:**

    Use MinIO as S3-compatible object storage:
    - Self-hosted within Kubernetes cluster
    - S3 API compatibility
    - Integrated with CNPG and Loki

    **Alternatives Considered:**

    1. **AWS S3** - Vendor lock-in, requires AWS account, egress costs
    2. **Local filesystem** - Not durable, no replication
    3. **Longhorn** - Block storage, not object storage

    **Consequences:**

    ✅ **Positive:**
    - S3 API compatibility (portable to cloud if needed)
    - Self-contained (no external dependencies)
    - No egress costs
    - Great for local development
    - Production-ready with replication

    ❌ **Negative:**
    - Additional service to manage
    - Storage capacity limited by cluster nodes
    - Need to handle backup/disaster recovery for MinIO itself

---

## Future ADRs

As the platform evolves, consider documenting:

- **ADR-008**: Monitoring and alerting rules

## ADR Template

When adding new ADRs, use this structure:

```markdown
## ADR-XXX: [Short Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded]

??? note "Show details"
    **Context:**

    What is the issue that we're seeing that is motivating this decision or change?

    **Decision:**

    What is the change that we're proposing and/or doing?

    **Alternatives Considered:**

    1. **Option 1** - Why not chosen
    2. **Option 2** - Why not chosen

    **Consequences:**

    ✅ **Positive:**
    - What becomes easier
    - What improves

    ❌ **Negative:**
    - What becomes more difficult
    - What tradeoffs we're accepting
```

## Related Documentation

- [Architecture Overview](overview.md)
- [Deployment Guide](../deployment/kubernetes.md)
- [Observability](../observability/observability.md)
