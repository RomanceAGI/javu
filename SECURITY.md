# Security Guidelines for REAL-AGI

This document outlines the baseline security posture for the REAL‑AGI project.  It is intended for developers, operators and auditors who deploy or modify the system.

## Secret Management

- **No hard‑coded secrets**: never store API keys, tokens or passwords directly in source files.  Use environment variables or a dedicated secrets manager.  See `config/` for examples of how to reference secrets at runtime.
- **Least privilege**: services and agents should operate with the minimum set of permissions required.  Avoid using root/administrative accounts when service‑level accounts suffice.
- **Rotation**: rotate all credentials on a regular schedule and immediately after any suspected compromise.

## Dependency and Supply‑Chain

- Maintain locked dependency manifests (`requirements.txt`, `pyproject.toml`, etc.) and review updates for known CVEs before upgrading.
- Generate and audit a Software Bill of Materials (SBOM) for each release.  Use tools such as `pip-audit` and `npm audit` during CI to identify vulnerable packages.
- Verify integrity of third‑party downloads via checksums or signatures where available.

## Code Hygiene

- Avoid using dangerous dynamic execution constructs (`eval`, `exec`, `pickle.load`, `yaml.load` without `safe_load`).  When such constructs are unavoidable, document the threat and mitigate via input validation and sandboxing.
- Validate and sanitize all untrusted input, particularly data that is passed to system commands or used to construct SQL queries.
- Use structured exception handling (`except Exception:`) rather than bare `except:` blocks to avoid masking errors.

## Network and Runtime

- All external connections should use TLS.  Validate certificates and pin hosts where possible.
- Expose only required ports and endpoints in container and firewall configurations.
- Enable rate limiting and request throttling on public endpoints to mitigate abuse.

## Logging and Monitoring

- Emit structured logs and metrics for security‑relevant events (authentication failures, permission denials, anomalous requests).  Avoid logging secrets or personal data.
- Regularly review logs for unusual activity.  Maintain alert rules for critical security incidents.

## Incident Response

- In the event of a suspected breach, follow the procedures outlined in `RUNBOOK.md` to contain, eradicate and recover.
- Document all incidents in post‑mortem reports, including root cause analysis and corrective actions.