# REAL‑AGI Model Card

This model card describes the machine learning components of the REAL‑AGI system, including intended use, architecture, training data, evaluation metrics and known limitations.  It is intended to promote transparency and responsible deployment.

## Overview

REAL‑AGI integrates multiple models to reason, plan and act across diverse domains.  The core consists of a large language model (LLM) for natural language understanding and generation, surrounded by specialised modules for tool use, retrieval‑augmented generation, vision and audio processing.

## Intended Use

- **Scope**: human‑level assistance across text, code, vision and audio tasks.  The system is designed to be beneficial, ethical and pro‑human.
- **Users**: researchers and developers building AGI‑powered applications.  End users interact via conversational interfaces.
- **Restrictions**: the model should not be used to generate harmful content, commit fraud, or perform tasks that violate laws or user policies.  High‑impact decisions (e.g. medical, legal) require human oversight.

## Training Data

The LLM was pre‑trained on a diverse corpus of publicly available text and code, then fine‑tuned with supervised and reinforcement learning.  Training data may contain biases present in the sources.

## Evaluation Metrics

- **Capability**: measured via standard benchmarks (e.g. MMLU, code generation, multi‑modal tasks) and internal tasks defined in `evaluation/`.
- **Safety**: adversarial evaluations (prompt injection, jailbreak, tool abuse) located in `evaluation/adversarial_suite/` measure refusal rates and filter efficacy.
- **Efficiency**: resource usage and latency monitored during load tests.

## Limitations

- **Hallucination**: the model may generate plausible but incorrect information.  Guardrails and critical‑thinking steps are in place, but users should verify outputs.
- **Bias**: like many LLMs, outputs may reflect biases in the training data.  Efforts are underway to measure and mitigate these biases.
- **Resource Intensity**: running REAL‑AGI requires significant compute.  The system may not be suitable for low‑resource environments.

## Ethical Considerations

- The system incorporates content filters, role‑based access controls, confirmation checkpoints and human‑in‑the‑loop for high‑risk actions.
- Data retention follows the principle of minimisation: only the data necessary for functioning is stored, and retention policies are documented.