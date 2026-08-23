# Retrieval and comparable-design ranking

Evidence retrieval combines normalized 384-dimensional cosine similarity, token overlap, numerical proximity, structured hard constraints, current-revision weight, and validation outcome.

Project score (0–100):

`35% semantic + 15% keyword + 20% numerical proximity + 15% hard-constraint compatibility + 5% current-status + 10% validation outcome`.

The browser constructs one canonical, labeled text representation from every application requirement, embeds it with the pinned local model, and sends that same vector to both comparable-project ranking and preliminary analysis. The API rejects ranking/analysis requests without a 384-dimensional vector. PostgreSQL calculates cosine similarity with pgvector; source IDs map the returned similarity back to each historical-project record before weighting.

Evidence documents use `55% semantic + 20% keyword + 10% architecture applicability + 10% current-status + 5% document-type priority`. Exact identifiers receive a deterministic boost. Scores are breakdowns, not “AI confidence.” Superseded or failed records remain discoverable and visibly marked but cannot become the recommended starting design.

Evaluation fixtures report Recall@k, Precision@k, MRR, correct-current-revision retrieval, citation validity, and unsupported-claim count.
