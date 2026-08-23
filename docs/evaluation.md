# Evaluation methodology

Known-answer cases cover exact IDs, semantic paraphrases, numeric constraints, revision precedence, failed projects, missing evidence, contradictions, and out-of-range applications. `scripts/evaluate_retrieval.py` runs against the same ranker and stored vectors as the API. Citation and claim validators independently confirm referenced sources, current/superseded treatment, recommendation eligibility, and support links.

The current final local run reports Recall@8 1.0000, Precision@8 0.21875, mean reciprocal rank 0.65327, correct-current-revision 1, citation validity 1.0000, and zero unsupported claims. Exact ordering is retained in `docs/evaluation-results.json`; the known-answer set was not altered for presentation.
