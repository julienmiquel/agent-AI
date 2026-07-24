"""Explicit Pydantic JSON Schemas for Company Multi-Agent Tools.

Defines strict input and output validation models for all agent tools to constrain LLM
arguments, enforce parameter boundaries, and provide structured payloads.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class ToolResponseMeta(BaseModel):
    """Common metadata embedded in structured tool responses."""
    status: str = Field(..., description="Execution status: 'SUCCESS', 'VALIDATION_ERROR', 'ERROR', or 'PENDING_CONFIRMATION'.")
    error: Optional[str] = Field(None, description="Detailed error description if execution failed.")
    recovery_instruction: Optional[str] = Field(None, description="Explicit, actionable instructions for the LLM on how to self-correct or prompt the user.")
    message: Optional[str] = Field(None, description="Human-readable summary of the tool outcome.")


# ---------------------------------------------------------------------------
# 1. Yield Analytics Tool Schemas
# ---------------------------------------------------------------------------
class QueryYieldDataInput(BaseModel):
    """Input schema for querying daily campsite yield analytics."""
    cluster_id: str = Field(..., description="Campsite cluster identifier (e.g., 'MEDITERRANEAN_SOUTH', 'ATLANTIC_NORTH').")
    start_date: str = Field("2026-07-01", description="Start date of the analysis window in YYYY-MM-DD format.")
    end_date: str = Field("2026-07-31", description="End date of the analysis window in YYYY-MM-DD format.")
    target_market: Optional[str] = Field(None, description="Optional target market segment country code (e.g., 'NL', 'FR', 'DE').")

    @validator("cluster_id")
    def validate_cluster_id(cls, v: str) -> str:
        clean = str(v).strip().upper()
        if not clean:
            raise ValueError("cluster_id cannot be empty.")
        return clean


class QueryYieldDataOutput(ToolResponseMeta):
    """Output schema for daily yield analytics query."""
    sql_queries: List[str] = Field(default_factory=list, description="List of parameterized BigQuery SQL queries executed.")
    metrics: Optional[Dict[str, float]] = Field(None, description="Computed yield metrics including occupancy_rate, avpn_eur, and revpar_eur.")
    widget: Optional[Dict[str, Any]] = Field(None, description="Visual widget payload for frontend rendering.")


class CompareYieldDataInput(BaseModel):
    """Input schema for comparative period-over-period yield analytics."""
    cluster_id: str = Field(..., description="Campsite cluster identifier (e.g., 'MEDITERRANEAN_SOUTH', 'ATLANTIC_NORTH').")
    current_start: str = Field("2026-07-01", description="Current period start date (YYYY-MM-DD).")
    current_end: str = Field("2026-07-31", description="Current period end date (YYYY-MM-DD).")
    prior_start: str = Field("2025-07-01", description="Prior comparative period start date (YYYY-MM-DD).")
    prior_end: str = Field("2025-07-31", description="Prior comparative period end date (YYYY-MM-DD).")
    target_market: Optional[str] = Field(None, description="Optional target market country code (e.g., 'NL', 'FR', 'DE').")
    campsite_id: Optional[str] = Field(None, description="Optional specific campsite identifier (e.g., 'LA_SIRENE_06').")


class CompareYieldDataOutput(ToolResponseMeta):
    """Output schema for comparative yield analytics."""
    sql_queries: List[str] = Field(default_factory=list, description="Comparative BigQuery SQL queries executed.")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Comparative metrics comparing current vs. prior period.")
    held_back_units: List[Dict[str, Any]] = Field(default_factory=list, description="List of identified held-back mobil-home units causing revenue bottlenecks.")
    widget: Optional[Dict[str, Any]] = Field(None, description="Visual comparative analytics widget payload.")


# ---------------------------------------------------------------------------
# 2. PMS Operations Tool Schemas
# ---------------------------------------------------------------------------
class ResalysUpdateInventoryInput(BaseModel):
    """Input schema for updating mobil-home unit inventory status in Resalys PMS."""
    campsite_id: str = Field("LA_SIRENE_06", description="Campsite identifier (e.g., 'LA_SIRENE_06', 'DOLMEN_COVE_02').")
    unit_ids: List[str] = Field(..., description="List of mobil-home unit IDs to update (e.g., ['MH-102', 'MH-103']).")
    new_status: str = Field("AVAILABLE_FOR_SALE", description="New inventory status. Allowed values: 'AVAILABLE_FOR_SALE', 'UNDER_MAINTENANCE', 'BLOCKED'.")
    unit_type: str = Field("PREMIUM_3_BEDROOMS", description="Mobil-home category / unit type.")

    @validator("new_status")
    def validate_status(cls, v: str) -> str:
        valid = {"AVAILABLE_FOR_SALE", "UNDER_MAINTENANCE", "BLOCKED", "HELD_BACK"}
        clean = str(v).strip().upper()
        if clean not in valid:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {sorted(valid)}")
        return clean


class ResalysUpdateInventoryOutput(ToolResponseMeta):
    """Output schema for PMS inventory status update."""
    campsite_id: Optional[str] = Field(None, description="Campsite identifier.")
    unit_ids: List[str] = Field(default_factory=list, description="List of units successfully updated.")
    updated_count: int = Field(0, description="Total number of units updated.")
    new_status: Optional[str] = Field(None, description="The applied inventory status.")
    endpoint: Optional[str] = Field(None, description="Apigee REST gateway endpoint invoked.")
    widget: Optional[Dict[str, Any]] = Field(None, description="Interactive PMS inventory control widget payload.")


class ResalysGetSupportTicketsInput(BaseModel):
    """Input schema for retrieving customer support and maintenance claim tickets."""
    status: str = Field("ALL", description="Ticket status filter: 'ALL', 'OPEN', 'IN_PROGRESS', or 'RESOLVED'.")
    campsite_id: Optional[str] = Field(None, description="Optional campsite ID filter.")


class ResalysGetSupportTicketsOutput(ToolResponseMeta):
    """Output schema for support tickets query."""
    tickets: List[Dict[str, Any]] = Field(default_factory=list, description="List of support claim tickets retrieved.")
    count: int = Field(0, description="Total number of matching tickets.")
    widget: Optional[Dict[str, Any]] = Field(None, description="Support tickets management widget payload.")


# ---------------------------------------------------------------------------
# 3. Marketing Campaign Tool Schemas
# ---------------------------------------------------------------------------
class CRMCreateFlashCampaignInput(BaseModel):
    """Input schema for staging a flash promotion marketing campaign in CRM.
    
    CRITICAL RULE: When calling this tool, you must always generate an accompanying introductory explanation in your public text response summarizing the campaign parameters for user confirmation. Never invoke this tool with an empty text response.
    """
    campaign_name: str = Field(..., description="Descriptive campaign title (e.g., 'Offre Spéciale Été 2026').")
    target_segment_id: str = Field(..., description="Target audience CRM segment ID (e.g., 'SEG_NL_PAST_GUESTS_2025').")
    discount_percentage: int = Field(15, ge=0, le=50, description="Discount percentage integer between 0 and 50.")
    estimated_revenue_loss_eur: float = Field(13950.0, ge=0.0, description="Estimated revenue loss in Euros from unmade sales.")
    copywriting_text: Optional[str] = Field(None, description="Localized promotional copywriting text.")
    image_asset_gcs_uri: Optional[str] = Field(None, description="Google Cloud Storage URI for campaign banner graphic.")
    target_market: str = Field("NL", description="Target market country code ('NL', 'FR', 'DE', 'UK').")
    cluster: str = Field("MEDITERRANEAN_SOUTH", description="Target campsite cluster name.")

    @validator("discount_percentage")
    def validate_discount(cls, v: int) -> int:
        if v > 50:
            raise ValueError("Discount percentage exceeds maximum guardrail threshold of 50%.")
        return v


class CRMCreateFlashCampaignOutput(ToolResponseMeta):
    """Output schema for staged CRM flash campaign."""
    campaign_id: Optional[str] = Field(None, description="Unique CRM campaign identifier generated upon staging.")
    campaign_name: Optional[str] = Field(None, description="Campaign title.")
    discount_percentage: Optional[int] = Field(None, description="Applied discount percentage.")
    target_market: Optional[str] = Field(None, description="Target market code.")
    copywriting_text: Optional[str] = Field(None, description="Localized promo copywriting.")
    image_asset_gcs_uri: Optional[str] = Field(None, description="GCS URI of campaign banner.")
    widget: Optional[Dict[str, Any]] = Field(None, description="CRM Flash Campaign staging widget payload.")


class GeneratePromotionalCopyInput(BaseModel):
    """Input schema for generating localized promotional copywriting."""
    target_market: str = Field("NL", description="Target market country code ('NL', 'FR', 'DE', 'UK').")
    cluster: str = Field("MEDITERRANEAN_SOUTH", description="Target campsite cluster identifier.")
    discount_percentage: int = Field(15, ge=0, le=50, description="Discount percentage integer between 0 and 50.")


class GeneratePromotionalCopyOutput(ToolResponseMeta):
    """Output schema for promotional copy generation."""
    copywriting_text: str = Field(..., description="Localized promotional copy text.")
    target_market: str = Field(..., description="Target market country code.")
