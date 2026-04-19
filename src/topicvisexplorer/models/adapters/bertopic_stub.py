"""Stub adapter for BERTopic (Grootendorst 2022).

Ships as a Protocol-conformant skeleton so users can subclass and
override :meth:`extract` to plug their own BERTopic models in without
waiting for the v1.1 official adapter. The shipped class raises
``NotImplementedError`` on call.

Why not implement now?
----------------------
BERTopic's ``c-TF-IDF`` topic representation has a different statistical
semantics than the term-probability matrix that LDAvis expects. A naive
``model.c_tf_idf_`` -> row-stochastic conversion gives visually-OK but
*numerically* meaningless coordinates in the 2D topic map. Doing it
properly requires either (a) re-fitting BERTopic with a probabilistic
calibration head or (b) using a different MDS callable that respects
c-TF-IDF semantics. We're deferring the design decision to v1.1 with
adequate user feedback.
"""

from __future__ import annotations

from typing import Any

from ..protocol import TopicModelData


class BERTopicAdapter:
    """Stub adapter; subclass and override :meth:`extract` to use today.

    Example
    -------
    >>> class MyBERTopic(BERTopicAdapter):
    ...     def extract(self, model, corpus, **kwargs):
    ...         # convert model.c_tf_idf_ etc. into TopicModelData
    ...         ...
    """

    name = "bertopic"

    def extract(self, model: Any, corpus: Any, **kwargs: Any) -> TopicModelData:
        raise NotImplementedError(
            "BERTopic support is scheduled for v1.1. Subclass BERTopicAdapter "
            "and override .extract() to use it today, or open an issue at "
            "https://github.com/<owner>/TopicVisExplorer/issues to vote on it."
        )
