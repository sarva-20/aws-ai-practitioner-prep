"""
classify_and_route.py

Reads inbox/note.md, sends it to Fireworks AI to classify into one of the 5 AIF-C01 domains,
then appends the note to the correct domain file and clears inbox/note.md.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")
if not FIREWORKS_API_KEY:
    print("ERROR: FIREWORKS_API_KEY environment variable not set.")
    sys.exit(1)

DEFAULT_FIREWORKS_MODELS = [
    "accounts/fireworks/models/llama-v3p3-70b-instruct",
]

INBOX_FILE = "inbox/note.md"

DOMAIN_FILES = {
    "D1": "domains/D1-fundamentals-of-ai-ml.md",
    "D2": "domains/D2-fundamentals-of-genai.md",
    "D3": "domains/D3-applications-of-foundation-models.md",
    "D4": "domains/D4-responsible-ai.md",
    "D5": "domains/D5-security-compliance-governance.md",
}

DOMAIN_DESCRIPTIONS = """
D1 - Fundamentals of AI and ML:
  Basic AI/ML terms, supervised/unsupervised/reinforcement learning, ML pipeline,
  data types, model evaluation metrics, MLOps, AWS ML services (SageMaker, Transcribe,
  Translate, Comprehend, Lex, Polly), practical use cases for AI.

D2 - Fundamentals of Generative AI:
  Tokens, embeddings, vectors, transformers, LLMs, foundation models, diffusion models,
  prompt engineering basics, GenAI use cases (summarization, chatbots, code gen),
  GenAI advantages and disadvantages (hallucinations, nondeterminism),
  AWS GenAI services (Bedrock, SageMaker JumpStart, PartyRock, Amazon Q).

D3 - Applications of Foundation Models:
  RAG (Retrieval Augmented Generation), vector databases, prompt engineering techniques
  (zero-shot, few-shot, chain-of-thought, prompt templates), fine-tuning methods
  (instruction tuning, RLHF, transfer learning), foundation model evaluation metrics
  (ROUGE, BLEU, BERTScore), inference parameters (temperature, top-p),
  Agents for Amazon Bedrock, model selection criteria.

D4 - Guidelines for Responsible AI:
  Bias and fairness, inclusivity, robustness, transparency, explainability,
  human oversight, legal risks of GenAI (IP, hallucinations, customer trust),
  dataset characteristics, detecting and monitoring bias, SageMaker Clarify,
  Bedrock Guardrails for responsible use.

D5 - Security, Compliance, and Governance for AI Solutions:
  IAM for AI workloads, data encryption, secure model deployment, compliance frameworks,
  data privacy, PII protection, AWS shared responsibility model for AI,
  governance policies, AWS CloudTrail, Macie, audit logging for AI systems.
"""

SYSTEM_PROMPT = f"""You are a classifier for AWS Certified AI Practitioner (AIF-C01) exam study notes.

Given a note written by a student, classify it into exactly one of these domains:
{DOMAIN_DESCRIPTIONS}

Respond with ONLY a JSON object in this exact format, nothing else, no markdown fences:
{{"domain": "D1", "reason": "one sentence explaining why"}}

The domain value must be exactly one of: D1, D2, D3, D4, D5.
"""


def read_inbox():
    if not os.path.exists(INBOX_FILE):
        print("inbox/note.md not found.")
        sys.exit(0)

    with open(INBOX_FILE, "r") as f:
        content = f.read().strip()

    if not content or "DELETE EVERYTHING ABOVE" in content:
        print("inbox/note.md is empty or still has placeholder text. Nothing to route.")
        sys.exit(0)

    return content


def classify_note(note_text):
    url = "https://api.fireworks.ai/inference/v1/chat/completions"

    env_model = os.environ.get("FIREWORKS_MODEL", "").strip()
    model_candidates = [env_model] if env_model else []
    model_candidates.extend(DEFAULT_FIREWORKS_MODELS)

    result = None
    last_error = None

    for model_name in model_candidates:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this study note:\n\n{note_text}"}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {FIREWORKS_API_KEY}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            last_error = f"{e.code} {e.reason}\n{error_body}"

            # Retry with a different model when the current one is unavailable.
            if e.code == 404 and any(token in error_body for token in ["NOT_FOUND", "Model not found"]):
                print(f"Model unavailable on Fireworks: {model_name}. Trying next candidate...")
                continue

            print(f"Fireworks API error: {e.code} {e.reason}")
            print(error_body)
            sys.exit(1)

    if result is None:
        print("Fireworks API error: no usable model found from candidates.")
        print("Tried models:")
        for model_name in model_candidates:
            print(f"- {model_name}")
        if last_error:
            print("Last error:")
            print(last_error)
        sys.exit(1)

    raw = result["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Could not parse Fireworks response as JSON:\n{raw}")
        sys.exit(1)

    domain = parsed.get("domain", "").strip()
    reason = parsed.get("reason", "").strip()

    if domain not in ("D1", "D2", "D3", "D4", "D5"):
        print(f"Invalid domain returned: '{domain}'. Full response:\n{raw}")
        sys.exit(1)

    return domain, reason


def append_to_domain(domain_key, note_text, reason):
    domain_file = DOMAIN_FILES.get(domain_key)
    if not domain_file:
        print(f"Unknown domain key: {domain_key}")
        sys.exit(1)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d")

    entry = f"""
---

**{timestamp}**
_{reason}_

{note_text}
"""

    with open(domain_file, "a") as f:
        f.write(entry)

    print(f"✅ Note appended to {domain_file}")
    print(f"   Domain: {domain_key} — {reason}")


def clear_inbox():
    placeholder = """# Write your note here in plain English

Just write what you understood from the question or concept.
No format needed. No template. Just your words.

Example:
RAG retrieves relevant chunks from a vector DB before the FM generates an answer.
Bedrock Knowledge Bases handles this end-to-end on AWS.
Push this file and it gets auto-classified into the right domain.

---
DELETE EVERYTHING ABOVE AND WRITE YOUR NOTE BELOW:


"""
    with open(INBOX_FILE, "w") as f:
        f.write(placeholder)
    print("📭 inbox/note.md cleared and reset.")


def main():
    print("📥 Reading inbox/note.md...")
    note_text = read_inbox()

    print("🤖 Classifying note with Fireworks AI...")
    domain_key, reason = classify_note(note_text)

    print(f"📂 Routing to {domain_key}...")
    append_to_domain(domain_key, note_text, reason)

    clear_inbox()
    print("\nDone.")


if __name__ == "__main__":
    main()
