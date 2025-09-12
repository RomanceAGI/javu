# REAL‑AGI Threat Model

This document summarises key assets, potential threats, and mitigations for the REAL‑AGI system.  It should be reviewed and updated with each major release.

## Assets

- **User data**: conversation transcripts, long‑term memory entries and metadata.
- **Model weights and prompts**: proprietary models and fine‑tuned parameters.
- **Secrets**: API keys, service tokens and configuration values.
- **Compute resources**: CPU/GPU time and network bandwidth.

## Adversaries

- **External attackers** seeking to exfiltrate data or abuse compute resources.
- **Malicious users** attempting prompt injection, jailbreaks or tool abuse.
- **Insider threats** misusing access privileges.

## Threats and Mitigations

| Threat | Impact | Mitigation |
|-------|--------|-----------|
| **Prompt Injection / Jailbreak** | Model produces unsafe output or executes unintended actions | Implement rigorous input sanitisation, prefix prompts with safety context, and employ a layered safety checker; see `safety_filters` for details. |
| **Tool Abuse** | Users trick the agent into performing unauthorised operations (e.g. making purchases) | Enforce strict preconditions and confirmation checkpoints before any external side effect; hard‑code allowlists for tools and endpoints. |
| **Data Exfiltration** | Sensitive user data is leaked via responses or external calls | Use role‑based access controls, redact sensitive fields in logs, and monitor for unusual data flows. |
| **Supply‑Chain Attack** | Malicious dependency injects code at build/runtime | Maintain pinned dependency versions, verify signatures, and audit SBOMs regularly. |
| **Denial of Service** | Resource exhaustion leading to downtime | Apply rate limiting, circuit breakers and resource quotas; monitor and autoscale where appropriate. |
| **Privilege Escalation** | Compromise of one component grants access to sensitive systems | Apply principle of least privilege for service accounts, use network segmentation, and regularly rotate credentials. |

## Assumptions

- The runtime environment is patched and monitored for known vulnerabilities.
- Operators follow the procedures outlined in `RUNBOOK.md` for deployments and incident response.