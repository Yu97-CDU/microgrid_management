from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


COMPONENT_TIPS = {
    "PV": "光伏输出为直流，推荐接入路径：PV -> DC/DC -> DC母线 -> DC/AC -> AC母线。",
    "WT": "风机输出频率和幅值随风速波动，推荐接入路径：WT -> AC/DC -> DC母线 -> DC/AC -> AC母线。",
    "Battery": "电池储能本体为直流储能，推荐接入路径：Battery -> 双向DC/DC -> DC母线；若作为交流侧储能单元，可通过 PCS 接入 AC母线。",
    "SC": "超级电容为直流侧快速储能，推荐通过双向DC/DC接入直流母线，或通过PCS接入交流侧。",
    "FES": "飞轮储能通常经电力电子接口接入母线，接交流侧建议配置变换器。",
    "SMES": "超导储能为直流电磁储能装置，接交流侧建议配置 DC/AC 变换器。",
    "EL": "电解槽通常由直流供电；若从交流母线取电，建议通过 AC/DC 整流器。",
    "DC_AC": "DC/AC 用于直流侧接入交流母线，是光伏、储能、直流母线并网的常用接口。",
    "AC_DC": "AC/DC 用于交流侧整流到直流侧，可用于风机全功率变流或交流供电制氢。",
    "DC_DC": "DC/DC 用于直流电压匹配和 MPPT，常用于光伏或储能接入直流母线。",
    "BIDIR_DC_DC": "双向DC/DC 用于储能充放电管理、电压匹配和功率双向控制，常挂接在直流母线侧。",
    "PCS": "PCS 储能变流器用于储能系统与交流母线/电网之间的双向功率交换。",
}


def component_tip(symbol: str) -> str:
    return COMPONENT_TIPS.get(symbol, "")


def _symbol(item: Any) -> str:
    return getattr(item, "symbol", "")


def connection_warning(start_item: Any, end_item: Any) -> str:
    symbols = {_symbol(start_item), _symbol(end_item)}
    names = f"{getattr(start_item, 'name', '')} - {getattr(end_item, 'name', '')}"

    if "PV" in symbols and symbols & {"AC_Bus", "Grid", "Load"}:
        return f"{names}：光伏为直流电源，不建议直接接入交流侧；请增加 DC/DC 和 DC/AC 接口。"
    if "WT" in symbols and symbols & {"AC_Bus", "Grid", "Load"}:
        return f"{names}：风机输出为波动交流，不建议直接接入工频交流母线；请增加 AC/DC 与 DC/AC 变换环节。"
    if symbols & {"Battery", "SC", "FES", "SMES"} and symbols & {"AC_Bus", "Grid", "Load"}:
        return f"{names}：储能本体通常为直流侧设备，直接接交流侧不严谨；建议通过 PCS 储能变流器。"
    if "EL" in symbols and symbols & {"AC_Bus", "Grid"}:
        return f"{names}：电解槽通常需要直流供电，从交流侧供电时建议增加 AC/DC 整流器。"
    if "DC_Bus" in symbols and symbols & {"AC_Bus", "Grid", "Load"}:
        return f"{names}：直流母线与交流侧之间建议通过 DC/AC 或 AC/DC 变换器连接。"
    return ""


def port_connection_warning(line_item: Any, start_item: Any, end_item: Any) -> str:
    base_warning = connection_warning(start_item, end_item)
    if base_warning:
        return base_warning

    start_type = getattr(getattr(line_item, "start_port", None), "port_type", "ANY")
    end_type = getattr(getattr(line_item, "end_port", None), "port_type", "ANY")
    names = f"{getattr(start_item, 'name', '')} - {getattr(end_item, 'name', '')}"

    if "ANY" in {start_type, end_type}:
        return ""
    if start_type == end_type:
        return ""
    allowed = {("AC_VAR", "AC"), ("AC", "AC_VAR")}
    if (start_type, end_type) in allowed:
        if "AC_DC" in {_symbol(start_item), _symbol(end_item)}:
            return ""
        return f"{names}：变频交流端口不宜直接接工频交流端口，建议增加 AC/DC + DC/AC 全功率变流链路。"
    return f"{names}：端口类型不匹配（{start_type} 与 {end_type}），建议通过相应电力电子变换器连接。"


def _has_path_with_symbols(start: str, target_symbols: set[str], required_symbols: set[str], by_name: dict[str, Any], adjacency: dict[str, set[str]]) -> bool:
    queue = deque([(start, {_symbol(by_name[start])})])
    visited = {start}
    while queue:
        name, seen_symbols = queue.popleft()
        if name != start and _symbol(by_name[name]) in target_symbols:
            return required_symbols <= seen_symbols
        for nxt in adjacency.get(name, set()):
            if nxt in visited:
                continue
            visited.add(nxt)
            queue.append((nxt, seen_symbols | {_symbol(by_name[nxt])}))
    return True


def validate_topology(node_items: list[Any], edge_items: list[tuple[Any, str, str]]) -> list[str]:
    by_name = {item.name: item for item in node_items}
    adjacency: dict[str, set[str]] = defaultdict(set)
    neighbor_symbols: dict[str, set[str]] = defaultdict(set)
    warnings: list[str] = []

    for line, start, end in edge_items:
        start_item = by_name.get(start)
        end_item = by_name.get(end)
        if start_item is None or end_item is None:
            continue
        adjacency[start].add(end)
        adjacency[end].add(start)
        neighbor_symbols[start].add(_symbol(end_item))
        neighbor_symbols[end].add(_symbol(start_item))
        warning = port_connection_warning(line, start_item, end_item)
        if warning:
            warnings.append(warning)

    for item in node_items:
        sym = _symbol(item)
        neighbors = neighbor_symbols.get(item.name, set())
        if not neighbors:
            continue
        if sym == "PV" and not neighbors & {"DC_DC", "DC_Bus", "DC_AC"}:
            warnings.append(f"{item.name}：光伏输出为直流，建议先接 DC/DC 或直流母线，再通过 DC/AC 接入交流侧。")
        elif sym == "WT" and not neighbors & {"AC_DC", "DC_AC"}:
            warnings.append(f"{item.name}：风机并网建议配置全功率变流链路，优先使用 AC/DC + DC/AC。")
        elif sym in {"Battery", "SC", "FES", "SMES"} and not neighbors & {"BIDIR_DC_DC", "DC_Bus", "PCS"}:
            warnings.append(f"{item.name}：储能设备建议通过双向 DC/DC 接入直流母线，或通过 PCS 接入交流侧。")
        elif sym == "EL" and not neighbors & {"DC_Bus", "AC_DC"}:
            warnings.append(f"{item.name}：电解槽建议接直流母线，或从交流侧经 AC/DC 整流后供电。")

        if sym == "PV" and not _has_path_with_symbols(item.name, {"AC_Bus", "Grid"}, {"DC_DC", "DC_AC"}, by_name, adjacency):
            warnings.append(f"{item.name}：若接入交流侧，完整路径建议包含 DC/DC 和 DC/AC。")
        elif sym == "WT" and not _has_path_with_symbols(item.name, {"AC_Bus", "Grid"}, {"AC_DC", "DC_AC"}, by_name, adjacency):
            warnings.append(f"{item.name}：若接入工频交流侧，完整路径建议包含 AC/DC 和 DC/AC。")
        elif sym in {"Battery", "SC", "FES", "SMES"} and "DC_Bus" in neighbors and "BIDIR_DC_DC" not in neighbors:
            warnings.append(f"{item.name}：当前直接接入直流母线；工程上常通过双向 DC/DC 管理充放电和电压匹配。")

    deduped = []
    for warning in warnings:
        if warning not in deduped:
            deduped.append(warning)
    return deduped
