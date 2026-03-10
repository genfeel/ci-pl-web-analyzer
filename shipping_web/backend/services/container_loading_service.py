"""컨테이너 적재 시뮬레이션 — Layer-based Greedy 알고리즘

컨테이너 내부 치수(mm) 기준으로 케이스를 적재 시뮬레이션.
"""
from typing import List, Dict, Any

from src.models.data_models import PackedCase

# 컨테이너 규격 (내부 치수 mm, 최대 적재중량 kg)
CONTAINER_SPECS = {
    "20ft": {
        "length": 5898,
        "width": 2352,
        "height": 2393,
        "max_payload": 21770,
    },
    "40ft": {
        "length": 12032,
        "width": 2352,
        "height": 2393,
        "max_payload": 26680,
    },
    "40ft_hc": {
        "length": 12032,
        "width": 2352,
        "height": 2698,
        "max_payload": 26460,
    },
}

# 레이어 높이 허용 오차 (mm)
HEIGHT_TOLERANCE = 50


def simulate_container_loading(
    cases: List[PackedCase], container_type: str
) -> Dict[str, Any]:
    """컨테이너 적재 시뮬레이션 실행"""
    spec = CONTAINER_SPECS.get(container_type)
    if not spec:
        raise ValueError(f"Unknown container type: {container_type}")

    c_length = spec["length"]
    c_width = spec["width"]
    c_height = spec["height"]
    max_payload = spec["max_payload"]

    # 유효한 케이스만 필터 (dimensions가 0이 아닌 것)
    valid_cases = []
    zero_dim_cases = []
    for case in cases:
        l, w, h = case.dimensions
        if l > 0 and w > 0 and h > 0:
            valid_cases.append(case)
        else:
            zero_dim_cases.append(case)

    # 1. 높이 내림차순 정렬
    sorted_cases = sorted(valid_cases, key=lambda c: c.dimensions[2], reverse=True)

    # 2. 레이어 그룹핑 (유사 높이 ±HEIGHT_TOLERANCE)
    layers = _group_into_layers(sorted_cases)

    # 3. 레이어별 2D 배치 + 적층
    placed = []
    unplaced_nos = [c.case_no for c in zero_dim_cases]
    current_z = 0
    total_weight = 0.0

    for layer_index, layer_cases in enumerate(layers):
        layer_height = max(c.dimensions[2] for c in layer_cases)

        # 높이 초과 체크
        if current_z + layer_height > c_height:
            unplaced_nos.extend(c.case_no for c in layer_cases)
            continue

        # 2D Shelf 배치
        placements = _shelf_pack_2d(layer_cases, c_length, c_width)

        for case, x, y, placed_l, placed_w, rotated in placements:
            # 중량 체크
            if total_weight + case.gross_weight > max_payload:
                unplaced_nos.append(case.case_no)
                continue

            placed.append({
                "case_no": case.case_no,
                "position": [float(x), float(y), float(current_z)],
                "dimensions": [float(placed_l), float(placed_w), float(case.dimensions[2])],
                "rotated": rotated,
                "category": case.category.value,
                "reason": case.reason or "",
                "layer_index": layer_index,
                "gross_weight": round(case.gross_weight, 2),
            })
            total_weight += case.gross_weight

        # 미배치 케이스 (2D 배치 실패)
        placed_nos = {p["case_no"] for p in placed}
        for case in layer_cases:
            if case.case_no not in placed_nos and case.case_no not in unplaced_nos:
                unplaced_nos.append(case.case_no)

        current_z += layer_height

    # 활용률 계산
    container_volume = c_length * c_width * c_height
    used_volume = sum(
        p["dimensions"][0] * p["dimensions"][1] * p["dimensions"][2]
        for p in placed
    )
    volume_util = (used_volume / container_volume * 100) if container_volume > 0 else 0
    weight_util = (total_weight / max_payload * 100) if max_payload > 0 else 0

    return {
        "container_type": container_type,
        "container_dims": [float(c_length), float(c_width), float(c_height)],
        "placed_cases": placed,
        "unplaced_cases": sorted(set(unplaced_nos)),
        "volume_utilization_pct": round(volume_util, 1),
        "weight_utilization_pct": round(weight_util, 1),
        "total_placed_weight": round(total_weight, 2),
        "max_payload": float(max_payload),
    }


def _group_into_layers(sorted_cases: List[PackedCase]) -> List[List[PackedCase]]:
    """유사 높이 케이스를 같은 레이어로 그룹핑"""
    if not sorted_cases:
        return []

    layers = []
    current_layer = [sorted_cases[0]]
    ref_height = sorted_cases[0].dimensions[2]

    for case in sorted_cases[1:]:
        h = case.dimensions[2]
        if abs(h - ref_height) <= HEIGHT_TOLERANCE:
            current_layer.append(case)
        else:
            layers.append(current_layer)
            current_layer = [case]
            ref_height = h

    if current_layer:
        layers.append(current_layer)

    return layers


def _shelf_pack_2d(
    cases: List[PackedCase], floor_length: int, floor_width: int
) -> List[tuple]:
    """Shelf 알고리즘으로 2D 바닥 배치

    Returns: [(case, x, y, placed_length, placed_width, rotated), ...]
    """
    # 바닥 면적 내림차순 정렬
    area_sorted = sorted(cases, key=lambda c: c.dimensions[0] * c.dimensions[1], reverse=True)

    placements = []
    # 셸프 리스트: [(shelf_y, shelf_height_remaining_width, current_x)]
    shelves = []  # [(y_start, shelf_depth, next_x)]

    for case in area_sorted:
        l, w, h = case.dimensions
        placed = False

        # 양방향 회전 시도
        orientations = [(l, w, False), (w, l, True)]

        for try_l, try_w, rotated in orientations:
            if try_l > floor_length or try_w > floor_width:
                continue

            # 기존 셸프에 배치 시도
            for i, (shelf_y, shelf_depth, next_x) in enumerate(shelves):
                if try_w <= shelf_depth and next_x + try_l <= floor_length:
                    placements.append((case, next_x, shelf_y, try_l, try_w, rotated))
                    shelves[i] = (shelf_y, shelf_depth, next_x + try_l)
                    placed = True
                    break

            if placed:
                break

            # 새 셸프 생성
            total_used_depth = sum(s[1] for s in shelves)
            if total_used_depth + try_w <= floor_width and try_l <= floor_length:
                shelf_y = total_used_depth
                shelves.append((shelf_y, try_w, try_l))
                placements.append((case, 0, shelf_y, try_l, try_w, rotated))
                placed = True
                break

    return placements
