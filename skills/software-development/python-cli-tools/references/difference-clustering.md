# Difference-Based Clustering with Softmax Caps

A novel clustering approach for organic, unsupervised content categorization.
**Knowledge is derived not by similarity, but by differences** — we recognize what's different, and through that determine similarity in relative degrees.

## Core Algorithm

Instead of grouping by similarity (cosine similarity, k-means, topic modeling), each new item is placed where it **differs least** from its neighbors. When a folder exceeds its softmax cap, the most mutually-different items become seeds for new subfolders.

### What makes it different from k-means

| Aspect | k-means / similarity clustering | Difference clustering |
|--------|-------------------------------|----------------------|
| Seed selection | Random or k-means++ | Softmax-weighted from *most different* items |
| Assignment | Minimize distance to centroid | Minimize **difference** to centroid |
| Split trigger | Fixed k, or hierarchy | **Softmax cap** — folder exceeds N items → split |
| Number of clusters | Pre-determined k | Dynamic: proportional to overage |
| Labeling | Centroid-based | **Tag frequency** across cluster members |

## Algorithm Steps

### 1. Compute Pairwise Difference Matrix

```
For every pair of items (A, B):
  content_diff = 1.0 - cosine_similarity(embedding(A), embedding(B))
  tag_diff     = 1.0 - |tags(A) ∩ tags(B)| / |tags(A) ∪ tags(B)|
  type_diff    = 1.0 if A.modality ≠ B.modality else 0.0
  graph_diff   = shortest_path_distance(A, B) in link graph
  composite    = 0.4*content + 0.2*tag + 0.2*type + 0.2*graph
```

### 2. Check Softmax Cap

```
If len(items) <= CAP:  → this is a leaf cluster, stop.
If len(items) > CAP:   → proceed to split.
```

### 3. Pick Seeds (Most-Different Items)

```
For each item:
  mean_diff = avg(composite difference to all other items)

Sort by mean_diff descending.
Take top N*3 candidates, then use softmax-weighted random selection
to pick exactly N seeds (temperature controls randomness).
```

Seeds are the most **distinctive** items — they define the cluster boundaries.

### 4. Assign Items to Seeds (Minimize Difference)

```
For each non-seed item:
  Assign to seed with the LOWEST composite difference
```

Each item goes where it differs least from the centroid.

### 5. Recurse

```
For each new sub-cluster:
  If sub-cluster.size > CAP:
    recurse on sub-cluster items
```

### 6. Label Clusters

```
For each cluster:
  Count tag frequency across ALL descendant pages
  Skip domain-level tags (.com, .org, .dev, .ai, .app, etc.)
  Use most frequent semantic tag as label
  Fallback: first page's meaningful title words
```

## Hyperparameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `softmax_cap` | 20 | Max items per folder before auto-split |
| `temperature` | 1.0 | Softmax temperature (lower = more deterministic seeds) |
| `weight.content` | 0.4 | Embedding similarity weight |
| `weight.tag` | 0.2 | Tag Jaccard distance weight |
| `weight.type` | 0.2 | Modality difference weight |
| `weight.graph` | 0.2 | Link graph distance weight |
| `max_depth` | 10 | Safety limit on recursion depth |

## Number of Sub-Clusters Formula

```
overage = len(items) - softmax_cap
num_clusters = min(max(2, (overage // (cap // 2)) + 2), 8)
```

This produces a proportional number of splits:
- 2 clusters at just-over-cap
- 4-5 clusters at heavy overage
- Max 8 clusters per split (prevents fragmentation)

## Domain Tag Filtering

When using tags for labeling, skip these TLDs to avoid "react.dev" or "arxiv.org" becoming cluster labels:

```python
DOMAIN_TLDS = (".com", ".org", ".io", ".net", ".edu", ".gov",
               ".dev", ".ai", ".app", ".co", ".me", ".tv")
```

## Implementation Pattern

The full implementation follows a clean module structure:

```
project/
├── src/
│   ├── models.py    # Page, ClusterNode, DifferenceMatrix, PageDifference
│   ├── differ.py    # build_cluster_tree, compute_difference_matrix,
│   │                # pick_seeds, assign_to_seeds, softmax
│   ├── wiki.py      # WikiBuilder (renders tree → files)
│   └── eval.py      # WikiEvaluator (cluster purity, linkage density)
```

### Key Model Classes

```python
class PageDifference(BaseModel):
    page_a, page_b: str
    content_diff, tag_diff, type_diff, graph_diff: float = 0.0
    composite: float = 0.0  # weighted sum

class DifferenceMatrix(BaseModel):
    page_ids: list[str]
    pairs: list[PageDifference]

class ClusterNode(BaseModel):
    cluster_id: str
    label: str
    page_ids: list[str]       # only populated on LEAF nodes
    children: list[ClusterNode]
    centroid_id: str | None
```

## Rebalancing vs Non-Rebalancing

This clustering is **MONOTONIC**: pages are only added to clusters, never reassigned across cluster boundaries once placed. Rebalancing only happens WITHIN a single cluster at split time. This means:

- **Prevents oscillation** (pages bouncing between clusters on every rebuild)
- **Supports incremental ingestion** (new pages get assigned to existing nearest cluster)
- **But** requires occasional full-rebuild if the data distribution changes significantly

For a full rebuild, discard and rebuild the cluster tree from scratch. The monotonic property is a design choice, not a limitation.
