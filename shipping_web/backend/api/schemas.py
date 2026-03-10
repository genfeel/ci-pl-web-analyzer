"""Pydantic 요청/응답 모델"""
from typing import List, Optional
from pydantic import BaseModel


class PackedItemResponse(BaseModel):
    description: str
    model_number: str
    quantity: int
    net_weight: float


class PackedCaseResponse(BaseModel):
    case_no: int
    case_type: str
    category: str
    reason: str
    total_quantity: int
    net_weight: float
    gross_weight: float
    dimensions: List[float]
    cbm: float
    items: List[PackedItemResponse]


class ValidationResponse(BaseModel):
    passed: bool
    errors: List[str]
    warnings: List[str]
    metrics: dict


class CategorySummary(BaseModel):
    category: str
    case_count: int
    total_quantity: int
    total_net_weight: float
    total_gross_weight: float


class UploadResponse(BaseModel):
    result_id: str
    filename: str
    total_cases: int
    total_quantity: int
    total_net_weight: float
    total_gross_weight: float
    total_cbm: float
    is_combined_order: bool
    order_numbers: List[str]
    cases: List[PackedCaseResponse]
    category_summary: List[CategorySummary]
    validation: ValidationResponse


class ContainerLoadRequest(BaseModel):
    container_type: str  # "20ft", "40ft", "40ft_hc"


class PlacedCaseResponse(BaseModel):
    case_no: int
    position: List[float]
    dimensions: List[float]
    rotated: bool
    category: str
    reason: str
    layer_index: int
    gross_weight: float


class ContainerLoadResponse(BaseModel):
    container_type: str
    container_dims: List[float]
    placed_cases: List[PlacedCaseResponse]
    unplaced_cases: List[int]
    volume_utilization_pct: float
    weight_utilization_pct: float
    total_placed_weight: float
    max_payload: float
