"""Pydantic JSON Schema definitions for Company Multi-Agent System."""

from src.schemas.tools import (
    ToolResponseMeta,
    QueryYieldDataInput,
    QueryYieldDataOutput,
    CompareYieldDataInput,
    CompareYieldDataOutput,
    ResalysUpdateInventoryInput,
    ResalysUpdateInventoryOutput,
    ResalysGetSupportTicketsInput,
    ResalysGetSupportTicketsOutput,
    CRMCreateFlashCampaignInput,
    CRMCreateFlashCampaignOutput,
    GeneratePromotionalCopyInput,
    GeneratePromotionalCopyOutput,
)

__all__ = [
    "ToolResponseMeta",
    "QueryYieldDataInput",
    "QueryYieldDataOutput",
    "CompareYieldDataInput",
    "CompareYieldDataOutput",
    "ResalysUpdateInventoryInput",
    "ResalysUpdateInventoryOutput",
    "ResalysGetSupportTicketsInput",
    "ResalysGetSupportTicketsOutput",
    "CRMCreateFlashCampaignInput",
    "CRMCreateFlashCampaignOutput",
    "GeneratePromotionalCopyInput",
    "GeneratePromotionalCopyOutput",
]
