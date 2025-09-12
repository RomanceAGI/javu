# REAL‑AGI Operations Runbook

This runbook documents operational procedures for deploying, monitoring and incident handling for the REAL‑AGI system.  It is intended for SREs and on‑call engineers.

## Deployment

1. **Prepare environment**
   - Ensure all required secrets and configuration values are present in the environment or secrets manager.
   - Verify that dependency manifests are up to date and pass security audits.
2. **Build artefacts**
   - Use the provided Dockerfiles or build scripts (`Makefile`) to produce container images.  Tag artefacts with the release version.
   - Generate an SBOM for each image and store it alongside the release artefacts.
3. **Rollout**
   - Deploy to staging first.  Run the full evaluation suite (`evaluation/`), monitor logs and metrics for anomalies.
   - If staging passes all health checks, promote the artefact to production.  Use blue‑green or canary deployments where possible.
4. **Post‑deployment**
   - Confirm that monitoring dashboards reflect the expected SLOs (latency, error rate, resource usage).
   - Update the `CHANGELOG.md` with the release notes.

## Monitoring

- **Metrics**: track request rate, success/error counts, latency percentiles (p50/p95), CPU/memory usage and queue depths.  Define Service Level Objectives (SLOs) for key metrics.
- **Logging**: enable structured logs with correlation IDs.  Log incoming user queries, tool invocations, safety filter triggers and exceptions.
- **Tracing**: instrument critical paths using OpenTelemetry or an equivalent library to trace interactions across components.
- **Alerting**: configure alerts on SLO breaches, repeated safety filter hits, unusually high error rates, and resource exhaustion.  Use paging for high‑severity alerts.

## Incident Response

1. **Detection**: when an alert fires or unusual behaviour is observed, acknowledge the incident in your incident tracking system.
2. **Containment**: if the incident is user‑visible or impacts safety, consider pausing agent execution or enabling a feature flag to disable the affected subsystem.
3. **Diagnosis**: gather context from logs, metrics and traces.  Identify the failing component and scope of impact.
4. **Mitigation**: apply a fix, rollback to a prior known‑good artefact or scale resources as needed to stabilise the system.
5. **Recovery**: monitor the system to ensure metrics return to baseline.  Once stable, declare the incident resolved.
6. **Post‑mortem**: document the timeline, root cause analysis and follow‑up actions in a post‑mortem report.  Update this runbook as needed.

## Backup and Restore

- Regularly back up persistent state (e.g. long‑term memory, configuration files) to secure offsite storage.
- Test restore procedures in staging at least quarterly to ensure backups are usable.