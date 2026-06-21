# D3 — Applications of Foundation Models
> 28% of exam (heaviest!) | Topics: Design considerations, prompt engineering, fine-tuning, evaluation

---

<!-- Notes get appended below this line automatically -->

---

**2026-06-21**
_heuristic fallback from note content_

* For greater accuracy by fine-tuning and using task-specific labeled dataset, should use **Provisioned Throughput Mode**, which allows to reserve a specific amount of capacity in advance (Healthcare Analytics company)
* RAG retrieves relevant chunks from a vector DB before the FM generates an answer. Bedrock Knowledge Bases handles this on AWS
* Zero-shot prompting gives the model instructions without examples, while few-shot includes examples to guide output style and accuracy.
* Bedrock Guardrails can filter unsafe outputs and help enforce responsible AI policies by blocking topics, masking PII, and reducing harmful responses.
* Amazon Q can help with enterprise knowledge retrieval and developer productivity by answering questions from indexed sources and AWS context.
* In AWS AI Practitioner prep, temperature controls randomness: lower values are more deterministic, while higher values produce more varied responses when sampling with top-p, careful prompt design, and the right model.
*
