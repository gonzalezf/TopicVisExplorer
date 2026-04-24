# Coherence metrics

The collapsible **Coherence** panel in the top-right of the single-corpus view
(label plus optional Σ) reports four per-topic quality scores. This page
explains what they mean and when each one is and isn't trustworthy.

All four are computed by `topicvisexplorer.coherence.report()` and
exposed via `GET /coherence`. The panel caches the response on first
expand and reuses it thereafter.

## NPMI

**Normalized Pointwise Mutual Information** of the top-N keywords of
each topic. A pair of keywords that co-occur more than chance gets a
positive NPMI; independent keywords score ~0; anti-correlated keywords
score negative. Range `[-1, 1]`, higher is better.

- **Use it when**: your corpus is large enough that top-N keyword pairs
  have stable co-document counts. As a rule of thumb: 200+ documents
  per topic.
- **Don't trust it when**: the corpus is small enough that many pairs
  never co-occur — you'll see a lot of −1 and the panel will display
  `—` for those. The demo fixture (4 documents) is a toy example.

Reference: Lau, Newman, Baldwin, *"Machine reading tea leaves"*,
EACL 2014.

## C_v

Röder, Both & Hinneburg's **sliding-window coherence** using indirect
cosine similarity over a context-vector representation. Range
`[0, 1]`, higher is better. Often tracks human judgments of topic
quality better than NPMI on news and web corpora.

- **Use it when**: you want a second opinion on NPMI.
- **Don't trust it when**: the raw texts are very short (tweets,
  captions); the sliding window has nothing to slide over.

Reference: Röder, Both, Hinneburg, *"Exploring the space of topic
coherence measures"*, WSDM 2015.

## Topic segregation

`1 − mean pairwise top-keyword Jaccard overlap with all other topics.`
Range `[0, 1]`, higher = topic is more lexically distinct from its
siblings.

Segregation complements coherence: a topic can be internally coherent
(high NPMI) while being redundant with another topic (low
segregation). In practice you'll want both to be high. The paper calls
this out in Section 6 as a missing UI signal.

## Document coverage

Fraction of documents for which this topic is the argmax assignment.
Range `[0, 1]`. A topic with coverage near 0 is rarely the dominant
topic of any document — often a sign that it should be merged away.

## Multi-corpus mode

The panel is hidden in the multi-corpus Sankey view (`type_vis == 1`
Jinja guard). Multi-corpus coherence is on the v1.1 roadmap; see
[`ROADMAP.md`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/ROADMAP.md).

## Programmatic access

```python
from topicvisexplorer.coherence import report

rep = report(
    prepared=prepared,
    doc_topic_dists=md.doc_topic_dists,
    tokenized_texts=tokenized,
    top_n=10,
)
print(rep.npmi, rep.c_v, rep.segregation, rep.coverage)
print(rep.mean_npmi, rep.mean_c_v)
```

See [`reference/coherence.md`](reference/coherence.md) for the full
signature.
