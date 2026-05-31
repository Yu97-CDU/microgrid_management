# ==============================================================================
# 版权声明与免责条款 (License & Disclaimer)
# 
# 作者: 蒋 宇/Yu Jiang
# 机构: 成都大学/Chengdu University
# 邮箱: jiangyu@cdu.edu.cn
# 
# 本文件是“新能源微电网运行与经济性分析平台”的一部分。
# 仅供学术研究和课堂教学使用。未经作者书面明确授权，严禁用于任何商业行为。
# 
# 作者对本软件模型计算的绝对准确性不作保证。使用者因使用本软件或其计算结果
# 而产生的任何直接或间接损失（包括设备损坏、经济损失或法律纠纷），作者概不负责。
# ==============================================================================
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np

from topology_rules import validate_topology


GENERATOR_TYPES = {"PV", "WT", "MT", "FC"}
STORAGE_TYPES = {"Battery", "SC", "FES", "SMES"}
LOAD_TYPES = {"Load", "EL"}
GRID_TYPES = {"Grid"}
PASSIVE_TYPES = {"AC_Bus", "DC_Bus", "DC_AC", "DC_DC", "BIDIR_DC_DC", "PCS", "AC_DC"}
CONVERTER_TYPES = {"DC_AC", "DC_DC", "BIDIR_DC_DC", "PCS", "AC_DC"}
GRID_EMISSION_FACTOR_KG_PER_KWH = 0.570
CARBON_PRICE_YUAN_PER_TON = 80.0


@dataclass
class AnalysisResult:
    hourly: dict[str, np.ndarray]
    totals: dict[str, float]
    flows: dict[Any, float]
    line_losses: dict[Any, float]
    line_currents: dict[Any, float]
    line_loading: dict[Any, float]
    node_power: dict[str, float]
    messages: list[str]


def parse_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default

    keep = []
    for char in text:
        if char.isdigit() or char in ".-+eE":
            keep.append(char)
        elif keep:
            break
    try:
        return float("".join(keep))
    except ValueError:
        return default


def get_param(data: dict[str, Any], keys: list[str], default: float = 0.0) -> float:
    for key in keys:
        if key in data:
            return parse_number(data.get(key), default)
    return default


def _node_symbol(node_item: Any) -> str:
    return getattr(node_item, "symbol", getattr(node_item, "comp_type", ""))


def _line_length_km(line_item: Any) -> float:
    data = getattr(line_item, "data", {})
    return max(get_param(data, ["线路长度 (km)", "Length (km)"], 0.2), 0.001)


def _line_resistance_ohm(line_item: Any) -> float:
    data = getattr(line_item, "data", {})
    total_r = get_param(data, ["电阻 R (Ω)", "Resistance (ohm)"], -1.0)
    if total_r >= 0:
        return max(total_r, 0.0)
    return max(_line_length_km(line_item) * get_param(data, ["单位电阻 R (Ω/km)", "Resistance (ohm/km)"], 0.10), 0.0)


def _line_reactance_ohm(line_item: Any) -> float:
    data = getattr(line_item, "data", {})
    total_x = get_param(data, ["电抗 X (Ω)", "Reactance (ohm)"], -1.0)
    if total_x > 0:
        return total_x
    return max(_line_length_km(line_item) * get_param(data, ["单位电抗 X (Ω/km)", "Reactance (ohm/km)"], 0.05), 0.001)


def _node_voltage_kv(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    preferred_keys = [
        "额定电压等级 (kV)",
        "接入电压等级 (kV)",
        "输出交流电压 (kV)",
        "输出直流电压 (kV)",
        "输入交流电压 (kV)",
        "输入直流电压 (kV)",
    ]
    for key in preferred_keys:
        if key in data:
            value = parse_number(data.get(key), 0.0)
            if value > 0:
                return value
    for key, value in data.items():
        if "电压" in key:
            parsed = parse_number(value, 0.0)
            if parsed > 0:
                return parsed
    return 0.4


def _percent_or_ratio(value: float) -> float:
    if value > 1.0:
        value /= 100.0
    return min(max(value, 0.0), 1.0)


def _pv_power_kw(node_item: Any, irradiance_w_m2: float | None = None, ambient_temp_c: float | None = None) -> float:
    data = getattr(node_item, "data", {})
    rated = _rated_power(node_item)
    irradiance = irradiance_w_m2 if irradiance_w_m2 is not None else get_param(data, ["光照强度 (W/m2)"], 800.0)
    ambient = ambient_temp_c if ambient_temp_c is not None else get_param(data, ["环境温度 (C)", "工作温度 (C)"], 25.0)
    noct = get_param(data, ["NOCT标称工作温度 (C)"], 45.0)
    temp_coeff = get_param(data, ["功率温度系数 (1/C)"], -0.004)
    shading = _percent_or_ratio(get_param(data, ["遮挡/积灰修正系数"], 0.95))
    dc_eff = _percent_or_ratio(get_param(data, ["DC/DC效率 (%)"], 98.0))

    irradiance_ratio = max(irradiance, 0.0) / 1000.0
    cell_temp = ambient + (noct - 20.0) / 800.0 * max(irradiance, 0.0)
    temp_factor = max(0.0, 1.0 + temp_coeff * (cell_temp - 25.0))
    return rated * irradiance_ratio * temp_factor * shading * dc_eff


def _wind_power_kw(node_item: Any, wind_speed_m_s: float | None = None, air_density: float | None = None) -> float:
    data = getattr(node_item, "data", {})
    rated = _rated_power(node_item)
    wind_speed = wind_speed_m_s if wind_speed_m_s is not None else get_param(data, ["当前风速 (m/s)"], 12.0)
    cut_in = get_param(data, ["切入风速 (m/s)"], 3.0)
    rated_speed = max(get_param(data, ["额定风速 (m/s)"], 12.0), cut_in + 0.1)
    cut_out = max(get_param(data, ["切出风速 (m/s)"], 25.0), rated_speed + 0.1)
    rho = air_density if air_density is not None else get_param(data, ["空气密度 (kg/m3)"], 1.225)
    rho_ref = max(get_param(data, ["参考空气密度 (kg/m3)"], 1.225), 0.01)
    converter_eff = _percent_or_ratio(get_param(data, ["变流器效率 (%)"], 97.0))

    if wind_speed < cut_in or wind_speed > cut_out:
        base_power = 0.0
    elif wind_speed >= rated_speed:
        base_power = rated
    else:
        numerator = wind_speed**3 - cut_in**3
        denominator = max(rated_speed**3 - cut_in**3, 1e-6)
        base_power = rated * max(0.0, numerator / denominator)

    density_factor = max(rho, 0.0) / rho_ref
    return min(rated, base_power * density_factor) * converter_eff


def _estimate_line_loss_kw(line_item: Any, start_node: Any, end_node: Any, flow_kw: float) -> float:
    resistance = _line_resistance_ohm(line_item)
    if resistance <= 0 or abs(flow_kw) <= 1e-9:
        return 0.0

    voltage_kv = max((_node_voltage_kv(start_node) + _node_voltage_kv(end_node)) / 2.0, 0.22)
    symbols = {_node_symbol(start_node), _node_symbol(end_node)}
    is_dc_path = any(symbol in {"DC_Bus", "DC_DC"} for symbol in symbols)
    if is_dc_path:
        current_a = abs(flow_kw) / voltage_kv
        return (current_a**2 * resistance) / 1000.0

    power_factor = 0.95
    current_a = abs(flow_kw) / (np.sqrt(3) * voltage_kv * power_factor)
    return (3.0 * current_a**2 * resistance) / 1000.0


def _estimate_line_metrics(line_item: Any, start_node: Any, end_node: Any, flow_kw: float) -> tuple[float, float, float]:
    resistance = _line_resistance_ohm(line_item)
    voltage_kv = max((_node_voltage_kv(start_node) + _node_voltage_kv(end_node)) / 2.0, 0.22)
    symbols = {_node_symbol(start_node), _node_symbol(end_node)}
    is_dc_path = any(symbol in {"DC_Bus", "DC_DC"} for symbol in symbols)
    if abs(flow_kw) <= 1e-9:
        current_a = 0.0
    elif is_dc_path:
        current_a = abs(flow_kw) / voltage_kv
    else:
        current_a = abs(flow_kw) / (np.sqrt(3) * voltage_kv * 0.95)
    loss_kw = (current_a**2 * resistance) / 1000.0 if is_dc_path else (3.0 * current_a**2 * resistance) / 1000.0
    max_current = max(get_param(getattr(line_item, "data", {}), ["最大载流量 (A)"], 500.0), 1.0)
    loading = current_a / max_current * 100.0
    return loss_kw, current_a, loading


def _converter_efficiency(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    if _node_symbol(node_item) == "BIDIR_DC_DC":
        charge = get_param(data, ["充电效率 (%)"], 98.0)
        discharge = get_param(data, ["放电效率 (%)"], 98.0)
        value = (charge + discharge) / 2.0
    else:
        value = get_param(data, ["转换效率 (%)"], 98.0)
    if value > 1.0:
        value /= 100.0
    return min(max(value, 0.01), 1.0)


def _converter_capacity_kw(node_item: Any) -> float:
    return max(get_param(getattr(node_item, "data", {}), ["额定容量 (kW)"], 150.0), 0.001)


def _rated_power(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    sym = _node_symbol(node_item)
    if sym == "PV":
        return get_param(data, ["额定功率 (kW)"], 200.0)
    if sym == "WT":
        return get_param(data, ["额定功率 (kW)"], 500.0)
    if sym == "MT":
        return get_param(data, ["最大输出功率 (kW)"], 150.0)
    if sym == "FC":
        return get_param(data, ["额定电功率 (kW)"], 100.0)
    if sym == "Battery":
        return get_param(data, ["最大充放电功率 (kW)", "额定容量 (kWh)"], 250.0)
    if sym == "SC":
        return get_param(data, ["最大功率 (kW)"], 500.0)
    if sym == "FES":
        return get_param(data, ["最大充放电功率 (kW)"], 200.0)
    if sym == "SMES":
        return get_param(data, ["储能容量 (MJ)"], 25.0) * 0.2778
    if sym == "EL":
        return get_param(data, ["额定输入功率 (kW)"], 150.0)
    if sym == "Load":
        return get_param(data, ["有功负荷 (kW)"], 350.0)
    if sym in CONVERTER_TYPES:
        return get_param(data, ["额定容量 (kW)"], 150.0)
    if sym == "Grid":
        return get_param(data, ["变压器容量 (kVA)"], 2500.0)
    return get_param(data, ["额定功率 (kW)"], 100.0)


def current_power(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    sym = _node_symbol(node_item)

    if sym == "PV":
        if any(key in data for key in ["光照强度 (W/m2)", "环境温度 (C)", "NOCT标称工作温度 (C)", "功率温度系数 (1/C)"]):
            return _pv_power_kw(node_item)
        return _rated_power(node_item) * get_param(data, ["当前出力系数"], 0.8)
    if sym == "WT":
        return _wind_power_kw(node_item)
    if sym == "MT":
        return get_param(data, ["当前出力 (kW)"], 100.0)
    if sym == "FC":
        return get_param(data, ["当前工作功率 (kW)"], 50.0)
    if sym == "Load":
        return -get_param(data, ["有功负荷 (kW)"], 350.0)
    if sym == "EL":
        return -get_param(data, ["实时功率 (kW)"], 80.0)
    return 0.0


def _capital_cost(node_item: Any) -> float:
    sym = _node_symbol(node_item)
    unit_cost = {
        "PV": 3800,
        "WT": 6200,
        "MT": 4500,
        "FC": 9000,
        "Battery": 1200,
        "SC": 1800,
        "FES": 2400,
        "SMES": 6500,
        "Grid": 800,
        "Load": 0,
        "EL": 4200,
        "AC_Bus": 300,
        "DC_Bus": 320,
        "DC_AC": 600,
        "DC_DC": 450,
        "BIDIR_DC_DC": 520,
        "PCS": 700,
        "AC_DC": 520,
    }.get(sym, 1000)
    return _rated_power(node_item) * unit_cost


def _storage_energy_kwh(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    sym = _node_symbol(node_item)
    if sym == "Battery":
        return get_param(data, ["额定容量 (kWh)"], 1000.0)
    if sym == "FES":
        return get_param(data, ["额定能量 (kWh)"], 50.0)
    if sym == "SMES":
        return get_param(data, ["储能容量 (MJ)"], 25.0) * 0.2778
    if sym == "SC":
        capacitance = get_param(data, ["额定电容 (F)"], 5000.0)
        voltage = get_param(data, ["额定电压 (V)"], 480.0)
        return 0.5 * capacitance * voltage**2 / 3.6e6
    return 0.0


def _storage_efficiency(node_item: Any) -> float:
    data = getattr(node_item, "data", {})
    value = get_param(data, ["充放电效率", "转换效率"], 0.92)
    if value > 1.0:
        value /= 100.0
    return min(max(value, 0.01), 1.0)


def _storage_initial_soc(node_item: Any) -> float:
    value = get_param(getattr(node_item, "data", {}), ["初始SOC (%)"], 60.0)
    if value > 1.0:
        value /= 100.0
    return min(max(value, 0.05), 0.95)


def build_hourly_profiles(node_items: list[Any], horizon: int = 24, fixed_loss_kw: float = 0.0) -> dict[str, np.ndarray]:
    hours = np.arange(horizon)
    solar_shape = np.maximum(0.0, np.sin((hours - 6) / 12 * np.pi))
    ambient_shape = 25.0 + 6.0 * np.sin((hours - 8) / 24 * 2 * np.pi)
    wind_shape = 1.0 + 0.22 * np.sin((hours + 2) / 24 * 2 * np.pi) + 0.08 * np.sin((hours * 3) / 24 * 2 * np.pi)
    load_shape = 0.72 + 0.18 * np.sin((hours - 7) / 24 * 2 * np.pi) + 0.16 * np.sin((hours - 18) / 24 * 2 * np.pi)
    price = np.array([0.42] * 7 + [0.68] * 4 + [0.92] * 6 + [0.74] * 4 + [0.50] * 3)

    pv = np.zeros(horizon)
    wt = np.zeros(horizon)
    controllable = np.zeros(horizon)
    load = np.zeros(horizon)
    storage_power = np.zeros(horizon)
    storage_soc = np.zeros(horizon)

    storage_capacity = 0.0
    storage_max_power = 0.0
    storage_eff_weighted = 0.92
    storage_initial_energy = 0.0
    pv_irradiance_profile = np.zeros(horizon)
    ambient_temp_profile = ambient_shape.copy()
    wind_speed_profile = np.zeros(horizon)
    pv_count = 0
    wt_count = 0

    for item in node_items:
        sym = _node_symbol(item)
        if sym == "PV":
            base_irradiance = get_param(getattr(item, "data", {}), ["光照强度 (W/m2)"], 800.0)
            base_temp = get_param(getattr(item, "data", {}), ["环境温度 (C)", "工作温度 (C)"], 25.0)
            pv_count += 1
            for i, shape in enumerate(solar_shape):
                irradiance = base_irradiance * shape / max(np.max(solar_shape), 1e-6)
                ambient = base_temp + (ambient_shape[i] - 25.0)
                pv_irradiance_profile[i] += irradiance
                pv[i] += _pv_power_kw(item, irradiance, ambient)
        elif sym == "WT":
            base_wind = get_param(getattr(item, "data", {}), ["当前风速 (m/s)"], 12.0)
            wt_count += 1
            for i, shape in enumerate(wind_shape):
                wind_speed = max(base_wind * shape, 0.0)
                wind_speed_profile[i] += wind_speed
                wt[i] += _wind_power_kw(item, wind_speed)
        elif sym in {"MT", "FC"}:
            controllable += max(current_power(item), 0.0)
        elif sym in LOAD_TYPES:
            load += abs(current_power(item)) * load_shape
        elif sym in STORAGE_TYPES:
            energy = _storage_energy_kwh(item)
            storage_capacity += energy
            storage_max_power += max(_rated_power(item), 0.0)
            storage_initial_energy += energy * _storage_initial_soc(item)
            storage_eff_weighted += _storage_efficiency(item) * max(energy, 1.0)

    if storage_capacity > 0:
        storage_eff = min(max(storage_eff_weighted / (storage_capacity + 1.0), 0.01), 1.0)
        storage_energy = min(max(storage_initial_energy, 0.05 * storage_capacity), 0.95 * storage_capacity)
    else:
        storage_eff = 0.92
        storage_energy = 0.0

    if pv_count > 0:
        pv_irradiance_profile = pv_irradiance_profile / pv_count
    if wt_count > 0:
        wind_speed_profile = wind_speed_profile / wt_count

    renewable = pv + wt
    fixed_loss = np.full(horizon, max(float(fixed_loss_kw), 0.0))
    net_before_storage = load + fixed_loss - renewable - controllable
    for i, need in enumerate(net_before_storage):
        if storage_max_power <= 0 or storage_capacity <= 0:
            storage_power[i] = 0.0
        elif need > 0 and price[i] >= np.percentile(price, 60):
            available_to_grid = max(storage_energy - 0.10 * storage_capacity, 0.0) * storage_eff
            discharge = min(need, storage_max_power, available_to_grid)
            storage_power[i] = discharge
            storage_energy -= discharge / storage_eff
        elif need < 0 and price[i] <= np.percentile(price, 45):
            room_from_grid = max(0.90 * storage_capacity - storage_energy, 0.0) / storage_eff
            charge = min(abs(need), storage_max_power, room_from_grid)
            storage_power[i] = -charge
            storage_energy += charge * storage_eff
        storage_soc[i] = storage_energy / storage_capacity if storage_capacity > 0 else 0.0

    grid_import = np.maximum(load + fixed_loss - renewable - controllable - storage_power, 0.0)
    grid_export = np.maximum(renewable + controllable + storage_power - load - fixed_loss, 0.0)
    storage_charge = np.maximum(-storage_power, 0.0)
    renewable_local_demand = np.maximum(load + fixed_loss + storage_charge, 0.0)
    renewable_local_used = np.minimum(renewable, renewable_local_demand)
    renewable_surplus = np.maximum(renewable - renewable_local_demand, 0.0)
    renewable_export = np.minimum(grid_export, renewable_surplus)
    renewable_curtailed = np.maximum(renewable_surplus - renewable_export, 0.0)
    baseline_grid_import = load.copy()
    grid_purchase_reduction = np.maximum(baseline_grid_import - grid_import, 0.0)
    carbon_reduction_kg = grid_purchase_reduction * GRID_EMISSION_FACTOR_KG_PER_KWH
    carbon_benefit = carbon_reduction_kg / 1000.0 * CARBON_PRICE_YUAN_PER_TON
    fuel_cost = controllable * 0.58
    storage_cycle_cost = np.abs(storage_power) * 0.06
    grid_cost = grid_import * price - grid_export * price * 0.55
    operating_cost = fuel_cost + storage_cycle_cost + grid_cost
    low_carbon_operating_cost = operating_cost - carbon_benefit

    return {
        "hour": hours,
        "pv": pv,
        "wt": wt,
        "controllable": controllable,
        "load": load,
        "storage": storage_power,
        "storage_soc": storage_soc,
        "fixed_loss": fixed_loss,
        "grid_import": grid_import,
        "grid_export": grid_export,
        "renewable_local_used": renewable_local_used,
        "renewable_export": renewable_export,
        "renewable_curtailed": renewable_curtailed,
        "baseline_grid_import": baseline_grid_import,
        "grid_purchase_reduction": grid_purchase_reduction,
        "carbon_reduction_kg": carbon_reduction_kg,
        "carbon_benefit": carbon_benefit,
        "price": price,
        "pv_irradiance": pv_irradiance_profile,
        "ambient_temp": ambient_temp_profile,
        "wind_speed": wind_speed_profile,
        "operating_cost": operating_cost,
        "low_carbon_operating_cost": low_carbon_operating_cost,
    }


def _solve_component_flows(
    graph: nx.Graph,
    component: set[str],
    scene_nodes: dict[str, Any],
    scene_edges: list[tuple[Any, str, str]],
    node_power: dict[str, float],
) -> dict[Any, float]:
    comp_nodes = list(component)
    if len(comp_nodes) <= 1:
        return {}

    total_injection = sum(node_power.get(name, 0.0) for name in comp_nodes)
    balancers = [
        name
        for name in comp_nodes
        if _node_symbol(scene_nodes[name]) in (GRID_TYPES | STORAGE_TYPES)
    ]
    if balancers:
        share = -total_injection / len(balancers)
        for name in balancers:
            node_power[name] = node_power.get(name, 0.0) + share

    node_to_idx = {name: idx for idx, name in enumerate(comp_nodes)}
    slack = next((n for n in comp_nodes if _node_symbol(scene_nodes[n]) == "Grid"), comp_nodes[0])
    slack_idx = node_to_idx[slack]
    n = len(comp_nodes)
    b_matrix = np.zeros((n, n))

    for item, start, end in scene_edges:
        if start not in component or end not in component:
            continue
        x_val = _line_reactance_ohm(item)
        x_val = x_val if x_val > 0 else 0.05
        b_val = 1.0 / x_val
        i, j = node_to_idx[start], node_to_idx[end]
        b_matrix[i, i] += b_val
        b_matrix[j, j] += b_val
        b_matrix[i, j] -= b_val
        b_matrix[j, i] -= b_val

    non_slack = [idx for idx in range(n) if idx != slack_idx]
    if not non_slack:
        return {}

    reduced = b_matrix[np.ix_(non_slack, non_slack)]
    injections = np.array([node_power.get(comp_nodes[idx], 0.0) for idx in non_slack])
    flows: dict[Any, float] = {}

    try:
        theta_reduced = np.linalg.solve(reduced, injections)
        theta = np.zeros(n)
        for idx, value in zip(non_slack, theta_reduced):
            theta[idx] = value
        for item, start, end in scene_edges:
            if start not in component or end not in component:
                continue
            x_val = _line_reactance_ohm(item)
            x_val = x_val if x_val > 0 else 0.05
            i, j = node_to_idx[start], node_to_idx[end]
            flows[item] = (theta[i] - theta[j]) / x_val
    except np.linalg.LinAlgError:
        for item, start, end in scene_edges:
            if start in component and end in component:
                flows[item] = (node_power.get(start, 0.0) - node_power.get(end, 0.0)) / 2.0
    return flows


def analyze_microgrid(
    graph: nx.Graph,
    node_items: list[Any],
    edge_items: list[tuple[Any, str, str]],
) -> AnalysisResult:
    scene_nodes = {item.name: item for item in node_items}
    messages: list[str] = []
    node_power = {item.name: current_power(item) for item in node_items}
    flows: dict[Any, float] = {edge: 0.0 for edge, _, _ in edge_items}

    for component in nx.connected_components(graph):
        comp_flows = _solve_component_flows(graph, set(component), scene_nodes, edge_items, node_power)
        flows.update(comp_flows)

    line_losses: dict[Any, float] = {}
    line_currents: dict[Any, float] = {}
    line_loading: dict[Any, float] = {}
    for edge, start, end in edge_items:
        start_node = scene_nodes.get(start)
        end_node = scene_nodes.get(end)
        if start_node is None or end_node is None:
            line_losses[edge] = 0.0
            line_currents[edge] = 0.0
            line_loading[edge] = 0.0
            continue
        loss_kw, current_a, loading = _estimate_line_metrics(edge, start_node, end_node, flows.get(edge, 0.0))
        line_losses[edge] = loss_kw
        line_currents[edge] = current_a
        line_loading[edge] = loading

    total_line_loss_kw = float(sum(line_losses.values()))
    converter_losses: dict[str, float] = {}
    converter_loading: dict[str, float] = {}
    for item in node_items:
        if _node_symbol(item) not in CONVERTER_TYPES:
            continue
        incident = [
            abs(flows.get(edge, 0.0))
            for edge, start, end in edge_items
            if start == item.name or end == item.name
        ]
        throughput = max(incident) if incident else 0.0
        eff = _converter_efficiency(item)
        converter_losses[item.name] = throughput * max(1.0 - eff, 0.0)
        converter_loading[item.name] = throughput / _converter_capacity_kw(item) * 100.0

    total_converter_loss_kw = float(sum(converter_losses.values()))
    fixed_loss_kw = total_line_loss_kw + total_converter_loss_kw
    hourly = build_hourly_profiles(node_items, fixed_loss_kw=fixed_loss_kw)
    hourly["line_loss"] = np.full_like(hourly["load"], total_line_loss_kw, dtype=float)
    hourly["converter_loss"] = np.full_like(hourly["load"], total_converter_loss_kw, dtype=float)
    total_generation = sum(max(current_power(item), 0.0) for item in node_items if _node_symbol(item) in GENERATOR_TYPES)
    total_load = sum(abs(current_power(item)) for item in node_items if _node_symbol(item) in LOAD_TYPES)
    grid_exchange = float(np.sum(hourly["grid_import"] - hourly["grid_export"]))
    renewable_energy = float(np.sum(hourly["pv"] + hourly["wt"]))
    renewable_local_used = float(np.sum(hourly["renewable_local_used"]))
    renewable_export = float(np.sum(hourly["renewable_export"]))
    renewable_curtailed = float(np.sum(hourly["renewable_curtailed"]))
    load_energy = float(np.sum(hourly["load"]))
    baseline_grid_import = float(np.sum(hourly["baseline_grid_import"]))
    grid_import_energy = float(np.sum(hourly["grid_import"]))
    grid_purchase_reduction = float(np.sum(hourly["grid_purchase_reduction"]))
    carbon_reduction_kg = float(np.sum(hourly["carbon_reduction_kg"]))
    carbon_benefit = float(np.sum(hourly["carbon_benefit"]))
    line_loss_energy = float(np.sum(hourly["line_loss"]))
    converter_loss_energy = float(np.sum(hourly["converter_loss"]))
    line_loss_cost = line_loss_energy * float(np.mean(hourly["price"]))
    converter_loss_cost = converter_loss_energy * float(np.mean(hourly["price"]))
    operating_cost = float(np.sum(hourly["operating_cost"]))
    low_carbon_operating_cost = float(np.sum(hourly["low_carbon_operating_cost"]))
    capital_cost = float(sum(_capital_cost(item) for item in node_items))
    annualized_capital = capital_cost * 0.085
    annual_load = max(load_energy * 365, 1.0)
    lcoe = (annualized_capital + operating_cost * 365) / annual_load

    if not node_items:
        messages.append("请从左侧元件库拖入设备后再运行分析。")
    elif not edge_items:
        messages.append("当前设备尚未连接，潮流结果仅反映单设备功率估算。")

    for warning in validate_topology(node_items, edge_items):
        messages.append(f"拓扑建议：{warning}")

    for edge, start, end in edge_items:
        if line_loading.get(edge, 0.0) > 100.0:
            messages.append(f"线路越限：{start} - {end} 负载率 {line_loading[edge]:.1f}%，超过最大载流量。")
    for name, loading in converter_loading.items():
        if loading > 100.0:
            messages.append(f"变换器越限：{name} 负载率 {loading:.1f}%，超过额定容量。")
    if renewable_energy > 1e-6 and renewable_local_used / renewable_energy < 0.80:
        messages.append(
            f"低碳提示：本地新能源消纳率 {renewable_local_used / renewable_energy * 100:.1f}%，"
            "可通过储能、电解槽、柔性负荷或并网外送提高消纳能力。"
        )

    totals = {
        "nodes": float(len(node_items)),
        "edges": float(len(edge_items)),
        "generation_kw": float(total_generation),
        "load_kw": float(total_load),
        "renewable_energy_kwh": renewable_energy,
        "renewable_local_used_kwh": renewable_local_used,
        "renewable_export_kwh": renewable_export,
        "renewable_curtailed_kwh": renewable_curtailed,
        "renewable_utilization_rate": renewable_local_used / max(renewable_energy, 1.0),
        "renewable_curtailed_rate": renewable_curtailed / max(renewable_energy, 1.0),
        "load_energy_kwh": load_energy,
        "baseline_grid_import_kwh": baseline_grid_import,
        "grid_import_kwh": grid_import_energy,
        "grid_purchase_reduction_kwh": grid_purchase_reduction,
        "grid_emission_factor_kg_per_kwh": GRID_EMISSION_FACTOR_KG_PER_KWH,
        "carbon_price_yuan_per_ton": CARBON_PRICE_YUAN_PER_TON,
        "carbon_reduction_kg_day": carbon_reduction_kg,
        "carbon_benefit_yuan_day": carbon_benefit,
        "line_loss_kw": total_line_loss_kw,
        "line_loss_energy_kwh": line_loss_energy,
        "line_loss_cost_yuan_day": line_loss_cost,
        "converter_loss_kw": total_converter_loss_kw,
        "converter_loss_energy_kwh": converter_loss_energy,
        "converter_loss_cost_yuan_day": converter_loss_cost,
        "grid_exchange_kwh": grid_exchange,
        "operating_cost_yuan_day": operating_cost,
        "low_carbon_operating_cost_yuan_day": low_carbon_operating_cost,
        "capital_cost_yuan": capital_cost,
        "lcoe_yuan_kwh": float(lcoe),
        "renewable_ratio": renewable_energy / max(load_energy, 1.0),
    }
    return AnalysisResult(
        hourly=hourly,
        totals=totals,
        flows=flows,
        line_losses=line_losses,
        line_currents=line_currents,
        line_loading=line_loading,
        node_power=node_power,
        messages=messages,
    )
