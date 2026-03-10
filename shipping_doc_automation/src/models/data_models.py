"""데이터 모델 정의 - CI/PL 관련 dataclass"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ProductCategory(Enum):
    VCB = "VCB"
    ACB_HGS = "ACB_HGS"
    ACB_LARGE = "ACB_LARGE"
    MCCB = "MCCB"
    MC = "MC"
    RELAY = "RELAY"
    SPARE = "SPARE"
    UNKNOWN = "UNKNOWN"


class PackingMethod(Enum):
    INDIVIDUAL_WOODEN = "INDIVIDUAL_WOODEN"
    GROUP_WOODEN = "GROUP_WOODEN"
    MIXED_PALLET = "MIXED_PALLET"


@dataclass
class CILineItem:
    """CI(Commercial Invoice) 개별 품목"""
    line_no: int
    description: str
    model_number: str
    quantity: int
    unit: str
    unit_price: float
    amount: float
    category: ProductCategory = ProductCategory.UNKNOWN
    category_header: str = ""
    parent_category: str = ""  # SPARE PART FOR ... 등
    order_number: str = ""     # 합적 주문 시 주문번호

    @property
    def is_spare(self) -> bool:
        return self.category == ProductCategory.SPARE


@dataclass
class CIDocument:
    """CI 전체 문서"""
    filename: str
    order_numbers: list = field(default_factory=list)
    items: list = field(default_factory=list)  # list[CILineItem]
    header_info: dict = field(default_factory=dict)
    is_combined_order: bool = False  # 합적 주문 여부

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def total_amount(self) -> float:
        return sum(item.amount for item in self.items)

    def items_by_category(self) -> dict:
        result = {}
        for item in self.items:
            cat = item.category
            if cat not in result:
                result[cat] = []
            result[cat].append(item)
        return result

    def items_by_order(self) -> dict:
        result = {}
        for item in self.items:
            order = item.order_number or "SINGLE"
            if order not in result:
                result[order] = []
            result[order].append(item)
        return result


@dataclass
class PackedItem:
    """케이스에 적재된 개별 품목"""
    ci_item: CILineItem
    quantity: int
    net_weight: float  # 해당 수량의 순중량

    @property
    def description(self) -> str:
        return self.ci_item.description

    @property
    def model_number(self) -> str:
        return self.ci_item.model_number


@dataclass
class PackedCase:
    """하나의 포장 케이스"""
    case_no: int
    case_type: str  # "WOODEN CASE", "PALLET"
    items: list = field(default_factory=list)  # list[PackedItem]
    dimensions: tuple = (0, 0, 0)  # (L, W, H) in mm
    case_weight: float = 0.0  # 케이스 자체 중량 (kg)
    category: ProductCategory = ProductCategory.UNKNOWN
    category_header: str = ""
    order_number: str = ""
    reason: str = ""

    @property
    def total_quantity(self) -> int:
        return sum(pi.quantity for pi in self.items)

    @property
    def net_weight(self) -> float:
        return sum(pi.net_weight for pi in self.items)

    @property
    def gross_weight(self) -> float:
        return round(self.net_weight + self.case_weight, 2)

    @property
    def cbm(self) -> float:
        """Cubic meter 계산"""
        l, w, h = self.dimensions
        if l == 0 or w == 0 or h == 0:
            return 0.0
        return round((l / 1000) * (w / 1000) * (h / 1000), 3)


@dataclass
class PLDocument:
    """PL(Packing List) 전체 문서"""
    filename: str
    cases: list = field(default_factory=list)  # list[PackedCase]
    header_info: dict = field(default_factory=dict)
    order_numbers: list = field(default_factory=list)
    is_combined_order: bool = False

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def total_quantity(self) -> int:
        return sum(c.total_quantity for c in self.cases)

    @property
    def total_net_weight(self) -> float:
        return round(sum(c.net_weight for c in self.cases), 2)

    @property
    def total_gross_weight(self) -> float:
        return round(sum(c.gross_weight for c in self.cases), 2)

    @property
    def total_cbm(self) -> float:
        return round(sum(c.cbm for c in self.cases), 3)

    def cases_by_category(self) -> dict:
        result = {}
        for case in self.cases:
            cat = case.category
            if cat not in result:
                result[cat] = []
            result[cat].append(case)
        return result

    def cases_by_order(self) -> dict:
        result = {}
        for case in self.cases:
            order = case.order_number or "SINGLE"
            if order not in result:
                result[order] = []
            result[order].append(case)
        return result


@dataclass
class ProductSpec:
    """제품 규격 정보"""
    model_prefix: str
    category: ProductCategory
    unit_weight_kg: float
    frame_type: str = ""
    dimensions_mm: tuple = (0, 0, 0)
    description: str = ""
