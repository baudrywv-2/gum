"""Cluster related evidence by shared token similarity."""

from __future__ import annotations

import uuid
from collections import defaultdict

from opportunity_engine.tokens import jaccard, tokenize
from packages.contracts.claim_tags import ClaimTag
from packages.contracts.evidence import EvidenceRecord
from packages.contracts.opportunities import EvidenceCluster
from packages.contracts.providers import ProviderName


def cluster_evidence(
    evidence: list[EvidenceRecord],
    *,
    min_cluster_size: int = 2,
    similarity_threshold: float = 0.2,
) -> list[EvidenceCluster]:
    """Greedy clustering: attach a record to the first cluster above threshold."""
    usable = [e for e in evidence if e.id is not None]
    if not usable:
        return []

    token_sets = {
        e.id: tokenize(e.title, e.summary, e.provenance.query or "") for e in usable
    }

    # Union-find style via parent map
    parent: dict = {e.id: e.id for e in usable}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    ids = [e.id for e in usable]
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            if jaccard(token_sets[left], token_sets[right]) >= similarity_threshold:
                union(left, right)

    buckets: dict = defaultdict(list)
    for record in usable:
        buckets[find(record.id)].append(record)

    clusters: list[EvidenceCluster] = []
    for members in buckets.values():
        if len(members) < min_cluster_size:
            # Keep singleton clusters only when they are multi-provider rare signals?
            # M4 prefers clusters of related evidence — skip tiny ones.
            continue
        shared: set[str] = set.intersection(*(token_sets[m.id] for m in members))
        if not shared:
            # Fall back to most common tokens across members
            counts: dict[str, int] = defaultdict(int)
            for m in members:
                for token in token_sets[m.id]:
                    counts[token] += 1
            shared = {
                t for t, c in counts.items() if c >= max(2, len(members) // 2)
            }
        providers = sorted(
            {m.provenance.provider for m in members}, key=lambda p: p.value
        )
        kinds = sorted({m.kind.value for m in members})
        label_bits = sorted(shared)[:4] or [members[0].title[:48]]
        label = " / ".join(label_bits)
        clusters.append(
            EvidenceCluster(
                id=uuid.uuid4(),
                label=label,
                evidence_ids=[m.id for m in members if m.id is not None],
                providers=providers,
                kinds=kinds,
                shared_tokens=sorted(shared)[:12],
                size=len(members),
                claim_tag=ClaimTag.AI_INTERPRETATION,
                limitations=[
                    "Clusters are formed by lexical similarity (AI_INTERPRETATION).",
                    "Similarity is not proof of a single real-world problem.",
                ],
            )
        )

    clusters.sort(key=lambda c: (-c.size, c.label))
    return clusters


def correlate_clusters(
    clusters: list[EvidenceCluster],
    evidence: list[EvidenceRecord],
) -> list:
    from packages.contracts.opportunities import CrossSourceCorrelation

    by_id = {e.id: e for e in evidence if e.id is not None}
    correlations = []
    for cluster in clusters:
        members = [by_id[i] for i in cluster.evidence_ids if i in by_id]
        search_count = sum(1 for m in members if m.kind.value == "search")
        discussion_count = sum(1 for m in members if m.kind.value == "discussion")
        providers = sorted(
            {m.provenance.provider for m in members}, key=lambda p: p.value
        )
        if len(providers) < 2 and not (search_count and discussion_count):
            continue
        correlations.append(
            CrossSourceCorrelation(
                cluster_label=cluster.label,
                providers=providers,
                search_count=search_count,
                discussion_count=discussion_count,
                evidence_ids=cluster.evidence_ids,
                claim_tag=ClaimTag.AI_INTERPRETATION,
                limitations=[
                    "Cross-source correlation means independent providers mentioned related tokens.",
                    "Not measured market size or conversion evidence.",
                ],
            )
        )
    return correlations
