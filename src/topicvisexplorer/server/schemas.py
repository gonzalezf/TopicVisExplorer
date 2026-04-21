"""Pydantic schemas for the FastAPI request/response contract.

These models intentionally mirror the *exact* JSON shapes the legacy
Flask front end already sends (see ``static/js/topicvisexplorer.js``).
The class names are CamelCase but the field aliases match the legacy
snake_case + camelCase blend so we don't have to touch the JS.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TopicSplitRequest(BaseModel):
    """Request body for ``POST /Topic_Splitting_Document_Based``."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    topic_id: int = Field(..., description="1-based id of the topic to split.", ge=1)
    current_number_of_topics: int = Field(..., description="K *before* the split.", ge=2)
    old_circle_positions: dict[str, list[list[float]]] = Field(
        ..., description="omega -> 2D layout shown to the user right now."
    )
    new_document_seeds: dict[str, list[dict[str, Any]]] = Field(
        default_factory=lambda: {"TopicA": [], "TopicB": []},
        description="User-supplied document seeds for the two children.",
    )


class TopicMergeRequest(BaseModel):
    """Request body for ``POST /get_new_topic_vector`` (merge endpoint)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    index_topic_name_1: int = Field(..., description="0-based index of first topic.", ge=0)
    index_topic_name_2: int = Field(..., description="0-based index of second topic.", ge=0)
    relevantDocumentsDict_new: list[dict[str, Any]] = Field(default_factory=list)
    lamData_new: dict[str, Any] = Field(default_factory=dict)
    old_circle_positions: dict[str, list[list[float]]] = Field(default_factory=dict)


class AddRemoveWordRequest(BaseModel):
    """Request for the new ``POST /Add_Remove_Word`` endpoint."""

    topic_id: int = Field(..., ge=1)
    word: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(add|remove)$")


class ExcludeDocumentRequest(BaseModel):
    """Request for the new ``POST /Exclude_Document`` endpoint."""

    topic_id: int = Field(..., ge=1)
    doc_id: int = Field(..., ge=0)


class TopicSplitResponse(BaseModel):
    """Response of the split endpoint - same keys as legacy."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    relevantDocumentsDict_fromPython: str = Field(
        ..., description="JSON-encoded list of relevant-document dicts."
    )
    PreparedDataObtained_fromPython: dict[str, Any]
    new_circle_positions: str = Field(..., description="JSON-encoded omega -> layout dict.")


class HealthResponse(BaseModel):
    """``GET /health`` payload."""

    status: str
    version: str
    n_sessions: int
    max_sessions: int
