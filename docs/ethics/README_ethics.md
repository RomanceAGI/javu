```markdown
# Ethics & Governance (Operational Guidance)

Goal: Operasionalisasikan nilai-nilai pro-human, pro-dunia, damai, dan etis di level sistem.

1) Deny-by-default for high-risk actions
   - Any action involving secrets, exploit instructions, mass exfiltration, or audit tampering must be blocked.

2) Human-in-the-loop for high or uncertain severity
   - Use the human approval queue for medium/high severity decisions.
   - Approval decisions must be recorded to approvals/decisions.jsonl.

3) Explainability & provenance
   - All autonomous decisions must produce an audit record (who, what, why, when).
   - Artifacts must be redacted before persistence.

4) Fail-safe & circuit breaker
   - On spikes of failures or risky events, trip circuit-breaker to stop automated flows.

5) Robust testing & red-team
   - Always run red-team simulations in sandbox; real red-team execution must be supervised.

6) Transparency
   - Maintain logs, snapshots, and human-readable summaries for audits.

7) Continuous evaluation
   - Periodically run evaluation scenarios (safety, alignment, robustness) and act on regressions.

This README is an operational guide and should be adapted to organizational policies and legal/regulatory constraints.
```