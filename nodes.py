from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem


COMPONENT_LIBRARY = {
    "分布式电源": [
        ("光伏", "PV", QColor(255, 230, 128)),
        ("风机", "WT", QColor(142, 205, 244)),
        ("微燃机", "MT", QColor(255, 189, 128)),
        ("燃料电池", "FC", QColor(229, 178, 255)),
    ],
    "储能系统": [
        ("电池储能", "Battery", QColor(136, 219, 142)),
        ("超级电容", "SC", QColor(246, 220, 105)),
        ("飞轮储能", "FES", QColor(156, 219, 183)),
        ("超导储能", "SMES", QColor(184, 184, 245)),
    ],
    "变换设备": [
        ("逆变器", "DC_AC", QColor(247, 160, 125)),
        ("直流变换器", "DC_DC", QColor(147, 218, 207)),
        ("双向DC/DC", "BIDIR_DC_DC", QColor(122, 201, 167)),
        ("储能PCS", "PCS", QColor(232, 163, 96)),
        ("整流器", "AC_DC", QColor(160, 184, 225)),
    ],
    "电网与负荷": [
        ("大电网", "Grid", QColor(196, 171, 244)),
        ("交流母线", "AC_Bus", QColor(80, 88, 96)),
        ("直流母线", "DC_Bus", QColor(151, 67, 67)),
        ("电力负荷", "Load", QColor(244, 133, 133)),
        ("电解槽", "EL", QColor(111, 213, 224)),
    ],
}


SYMBOL_ABBREVIATIONS = {
    "PV": "PV",
    "WT": "WT",
    "MT": "MT",
    "FC": "FC",
    "Battery": "BESS",
    "SC": "SC",
    "FES": "FES",
    "SMES": "SMES",
    "Grid": "Grid",
    "AC_Bus": "AC Bus",
    "DC_Bus": "DC Bus",
    "Load": "Load",
    "EL": "EL",
    "DC_AC": "DC/AC",
    "DC_DC": "DC/DC",
    "BIDIR_DC_DC": "Bi-DC/DC",
    "PCS": "PCS",
    "AC_DC": "AC/DC",
}


def component_abbreviation(symbol: str) -> str:
    return SYMBOL_ABBREVIATIONS.get(symbol, symbol)


def component_name(symbol: str) -> str:
    for entries in COMPONENT_LIBRARY.values():
        for name, item_symbol, _ in entries:
            if item_symbol == symbol:
                return name
    return symbol


def component_color(symbol: str) -> QColor:
    for entries in COMPONENT_LIBRARY.values():
        for _, item_symbol, color in entries:
            if item_symbol == symbol:
                return QColor(color)
    return QColor(220, 220, 220)


def parse_float(value, default: float) -> float:
    try:
        text = str(value).strip()
        keep = []
        for char in text:
            if char.isdigit() or char in ".-+eE":
                keep.append(char)
            elif keep:
                break
        return float("".join(keep)) if keep else default
    except ValueError:
        return default


def default_node_data(symbol: str) -> dict[str, str]:
    defaults = {
        "PV": {
            "额定功率 (kW)": "200",
            "当前出力系数": "0.80",
            "光照强度 (W/m2)": "800",
            "环境温度 (C)": "25",
            "NOCT标称工作温度 (C)": "45",
            "功率温度系数 (1/C)": "-0.004",
            "遮挡/积灰修正系数": "0.95",
            "DC/DC效率 (%)": "98.0",
            "接入电压等级 (kV)": "0.75",
        },
        "WT": {
            "额定功率 (kW)": "500",
            "当前出力系数": "0.60",
            "切入风速 (m/s)": "3.0",
            "额定风速 (m/s)": "12.0",
            "切出风速 (m/s)": "25.0",
            "当前风速 (m/s)": "12.0",
            "空气密度 (kg/m3)": "1.225",
            "参考空气密度 (kg/m3)": "1.225",
            "风轮半径 (m)": "35",
            "功率系数 Cp": "0.42",
            "变流器效率 (%)": "97.0",
            "接入电压等级 (kV)": "0.4",
        },
        "MT": {
            "最大输出功率 (kW)": "150",
            "最小输出功率 (kW)": "30",
            "当前出力 (kW)": "100",
            "发电效率": "0.35",
            "余热利用率": "0.45",
            "接入电压等级 (kV)": "0.4",
        },
        "FC": {
            "额定电功率 (kW)": "100",
            "氢气消耗率 (g/kWh)": "60",
            "发电效率": "0.55",
            "当前工作功率 (kW)": "50",
            "接入电压等级 (kV)": "0.75",
        },
        "Battery": {
            "额定容量 (kWh)": "1000",
            "最大充放电功率 (kW)": "250",
            "初始SOC (%)": "60",
            "充放电效率": "0.92",
            "接入电压等级 (kV)": "0.75",
        },
        "SC": {
            "额定电容 (F)": "5000",
            "额定电压 (V)": "480",
            "最大功率 (kW)": "500",
            "初始SOC (%)": "50",
            "充放电效率": "0.98",
            "接入电压等级 (kV)": "0.75",
        },
        "FES": {
            "额定能量 (kWh)": "50",
            "额定转速 (rpm)": "20000",
            "最大充放电功率 (kW)": "200",
            "自放电率 (%/h)": "0.5",
            "充放电效率": "0.90",
            "接入电压等级 (kV)": "0.75",
        },
        "SMES": {
            "线圈电感 (H)": "50",
            "额定电流 (A)": "1000",
            "储能容量 (MJ)": "25",
            "响应时间 (ms)": "2",
            "转换效率": "0.96",
            "接入电压等级 (kV)": "0.75",
        },
        "Grid": {
            "额定电压等级 (kV)": "10.0",
            "变压器容量 (kVA)": "2500",
            "买电电价 (元/kWh)": "0.85",
            "卖电电价 (元/kWh)": "0.35",
        },
        "AC_Bus": {
            "额定电压等级 (kV)": "0.4",
            "布置方向 (H/V)": "H",
            "母线长度 (px)": "180",
            "电压上限偏差 (%)": "5.0",
            "电压下限偏差 (%)": "-5.0",
            "实时电压 (p.u.)": "1.00",
        },
        "DC_Bus": {
            "额定电压等级 (kV)": "0.75",
            "布置方向 (H/V)": "H",
            "母线长度 (px)": "180",
            "电压上限偏差 (%)": "5.0",
            "电压下限偏差 (%)": "-5.0",
            "实时电压 (p.u.)": "1.00",
        },
        "Load": {
            "有功负荷 (kW)": "350",
            "无功负荷 (kVar)": "150",
            "负荷功率因数": "0.92",
            "接入电压等级 (kV)": "0.4",
        },
        "EL": {
            "额定输入功率 (kW)": "150",
            "制氢效率 (%)": "75.0",
            "最低运行负荷 (kW)": "15",
            "实时功率 (kW)": "80",
            "接入电压等级 (kV)": "0.75",
        },
        "DC_AC": {
            "额定容量 (kW)": "150",
            "转换效率 (%)": "98.5",
            "输入直流电压 (kV)": "0.75",
            "输出交流电压 (kV)": "0.4",
        },
        "DC_DC": {
            "额定容量 (kW)": "100",
            "转换效率 (%)": "99.0",
            "输入直流电压 (kV)": "0.38",
            "输出直流电压 (kV)": "0.75",
        },
        "BIDIR_DC_DC": {
            "额定容量 (kW)": "250",
            "充电效率 (%)": "98.0",
            "放电效率 (%)": "98.0",
            "低压侧直流电压 (kV)": "0.38",
            "高压侧直流电压 (kV)": "0.75",
            "控制模式": "双向充放电",
        },
        "PCS": {
            "额定容量 (kW)": "250",
            "转换效率 (%)": "97.5",
            "直流侧电压 (kV)": "0.75",
            "交流侧电压 (kV)": "0.4",
            "功率因数": "0.98",
            "控制模式": "并网PQ",
        },
        "AC_DC": {
            "额定容量 (kW)": "150",
            "转换效率 (%)": "98.0",
            "输入交流电压 (kV)": "0.4",
            "输出直流电压 (kV)": "0.75",
        },
    }
    return defaults.get(symbol, {"额定功率 (kW)": "100", "接入电压等级 (kV)": "0.4"}).copy()


class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port: "NodePort", parent=None):
        super().__init__(parent)
        self.start_port = start_port
        self.end_port: NodePort | None = None
        self.end_pos = start_port.scenePos()
        self.power_flow = 0.0
        self.loss_kw = 0.0
        self.current_a = 0.0
        self.loading_percent = 0.0
        self.route_style = "auto"
        self.route_offset = 0.0
        self.display_layer = "energy"
        self.data = {
            "线路长度 (km)": "0.20",
            "单位电阻 R (Ω/km)": "0.10",
            "单位电抗 X (Ω/km)": "0.05",
            "最大载流量 (A)": "1000",
            "线路名称": "Line",
        }
        self.setZValue(-2)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_path()

    def mouseDoubleClickEvent(self, event):
        from dialogs import PropertyDialog

        dialog = PropertyDialog("线路参数", self.data)
        if dialog.exec():
            self.data = dialog.get_data()
            self.update()
        super().mouseDoubleClickEvent(event)

    def set_end_pos(self, pos: QPointF):
        self.end_pos = pos
        self.update_path()

    def update_path(self):
        self.prepareGeometryChange()
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos() if self.end_port else self.end_pos
        path = QPainterPath()
        path.moveTo(p1)

        style = self.route_style
        if style == "auto":
            style = "hvh" if abs(p2.x() - p1.x()) >= abs(p2.y() - p1.y()) else "vhv"

        if style == "vhv":
            mid_y = (p1.y() + p2.y()) / 2.0 + self.route_offset
            path.lineTo(p1.x(), mid_y)
            path.lineTo(p2.x(), mid_y)
        else:
            mid_x = (p1.x() + p2.x()) / 2.0 + self.route_offset
            path.lineTo(mid_x, p1.y())
            path.lineTo(mid_x, p2.y())
        path.lineTo(p2)
        self.setPath(path)

    def update_power_flow(
        self,
        power_value: float,
        loss_kw: float | None = None,
        current_a: float | None = None,
        loading_percent: float | None = None,
    ):
        self.power_flow = float(power_value)
        if loss_kw is not None:
            self.loss_kw = float(loss_kw)
        if current_a is not None:
            self.current_a = float(current_a)
        if loading_percent is not None:
            self.loading_percent = float(loading_percent)
        self.update()

    def boundingRect(self):
        return self.path().boundingRect().adjusted(-70, -45, 70, 55)

    def _route_points(self) -> list[QPointF]:
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos() if self.end_port else self.end_pos
        style = self.route_style
        if style == "auto":
            style = "hvh" if abs(p2.x() - p1.x()) >= abs(p2.y() - p1.y()) else "vhv"

        if style == "vhv":
            mid_y = (p1.y() + p2.y()) / 2.0 + self.route_offset
            return [p1, QPointF(p1.x(), mid_y), QPointF(p2.x(), mid_y), p2]

        mid_x = (p1.x() + p2.x()) / 2.0 + self.route_offset
        return [p1, QPointF(mid_x, p1.y()), QPointF(mid_x, p2.y()), p2]

    def _polyline_midpoint(self) -> QPointF:
        points = self._route_points()
        lengths = []
        total = 0.0
        for start, end in zip(points, points[1:]):
            length = ((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2) ** 0.5
            lengths.append(length)
            total += length
        if total <= 1e-9:
            return points[0]

        halfway = total / 2.0
        covered = 0.0
        for length, start, end in zip(lengths, points, points[1:]):
            if covered + length >= halfway and length > 0:
                ratio = (halfway - covered) / length
                return QPointF(start.x() + (end.x() - start.x()) * ratio, start.y() + (end.y() - start.y()) * ratio)
            covered += length
        return points[-1]

    def _point_and_angle_at_fraction(self, fraction: float) -> tuple[QPointF, float]:
        points = self._route_points()
        segments: list[tuple[float, QPointF, QPointF]] = []
        total = 0.0
        for start, end in zip(points, points[1:]):
            length = ((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2) ** 0.5
            if length <= 1e-9:
                continue
            segments.append((length, start, end))
            total += length
        if total <= 1e-9:
            return points[0], 0.0

        target = max(0.0, min(1.0, fraction)) * total
        covered = 0.0
        for length, start, end in segments:
            if covered + length >= target:
                ratio = (target - covered) / length
                point = QPointF(start.x() + (end.x() - start.x()) * ratio, start.y() + (end.y() - start.y()) * ratio)
                angle = math.atan2(end.y() - start.y(), end.x() - start.x())
                return point, angle
            covered += length

        length, start, end = segments[-1]
        return end, math.atan2(end.y() - start.y(), end.x() - start.x())

    def _draw_flow_arrow(self, painter: QPainter, color: QColor, flow: float, size: int = 11):
        if not self.end_port:
            return
        fraction = 0.78 if flow >= 0 else 0.22
        center, angle = self._point_and_angle_at_fraction(fraction)
        if flow < 0:
            angle += math.pi
        p_left = center - QPointF(math.cos(angle - math.pi / 6) * size, math.sin(angle - math.pi / 6) * size)
        p_right = center - QPointF(math.cos(angle + math.pi / 6) * size, math.sin(angle + math.pi / 6) * size)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([center, p_left, p_right]))

    def paint(self, painter: QPainter, option, widget=None):
        if self.display_layer == "physical":
            color = QColor(96, 108, 120)
            style = Qt.PenStyle.DashLine if self.isSelected() else Qt.PenStyle.SolidLine
            painter.setPen(QPen(color, 2, style))
            painter.drawPath(self.path())
            self._draw_flow_arrow(painter, color, self.power_flow, 9)
            return

        if self.display_layer == "economic":
            color = QColor(122, 96, 148)
            style = Qt.PenStyle.DashLine if self.isSelected() else Qt.PenStyle.DotLine
            painter.setPen(QPen(color, 2, style))
            painter.drawPath(self.path())
            self._draw_flow_arrow(painter, color, self.power_flow, 9)
            return

        flow = self.power_flow
        abs_flow = abs(flow)
        if abs_flow > 300:
            color = QColor(196, 47, 47)
            width = 4
        elif abs_flow > 100:
            color = QColor(225, 132, 36)
            width = 3
        else:
            color = QColor(41, 131, 86)
            width = 2

        if self.isSelected():
            painter.setPen(QPen(QColor(30, 100, 210), width + 1, Qt.PenStyle.DashLine))
        else:
            painter.setPen(QPen(color, width))
        painter.drawPath(self.path())

        self._draw_flow_arrow(painter, color, flow)

        if self.end_port:
            text = f"P {flow:+.1f} kW"
            if self.loss_kw > 0.001:
                text += f"\n损耗 {self.loss_kw:.2f} kW"
            if self.loading_percent > 0:
                text += f"\n负载率 {self.loading_percent:.0f}%"
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            metrics = painter.fontMetrics()
            lines = text.splitlines()
            width_text = max(metrics.horizontalAdvance(line) for line in lines)
            height_text = metrics.height() * len(lines)
            label_center = self._polyline_midpoint()
            rect = QRectF(label_center.x() - width_text / 2 - 7, label_center.y() - height_text / 2 - 4, width_text + 14, height_text + 8)
            painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
            painter.setPen(QPen(color, 1))
            painter.drawRoundedRect(rect, 4, 4)
            painter.setPen(QPen(color.darker(135), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


class NodePort(QGraphicsItem):
    def __init__(self, parent=None, port_type: str = "ANY"):
        super().__init__(parent)
        self.radius = 6
        self.hit_radius = 10
        self.port_type = port_type
        self.edges: list[ConnectionLine] = []
        self._hovered = False
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def add_edge(self, edge: ConnectionLine):
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge: ConnectionLine):
        if edge in self.edges:
            self.edges.remove(edge)

    def boundingRect(self):
        return QRectF(-self.hit_radius, -self.hit_radius, self.hit_radius * 2, self.hit_radius * 2)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        type_color = {
            "AC": QColor(247, 247, 255),
            "DC": QColor(255, 247, 232),
            "AC_VAR": QColor(239, 250, 255),
            "ANY": QColor(245, 248, 250),
        }.get(self.port_type, QColor(245, 248, 250))
        color = QColor(48, 110, 220) if self._hovered else type_color
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(80, 90, 100), 1.2))
        painter.drawEllipse(QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2))


class MicrogridNode(QGraphicsObject):
    def __init__(self, name: str, symbol: str):
        super().__init__()
        self.name = name
        self.symbol = symbol
        self.comp_type = component_name(symbol)
        self.base_color = component_color(symbol)
        self.data = default_node_data(symbol)
        self.ports: list[NodePort] = []

        if "Bus" in symbol:
            self.width = parse_float(self.data.get("母线长度 (px)"), 180.0)
            self.height = 10
        else:
            self.width = 82
            self.height = 62

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._init_ports()

    def _init_ports(self):
        self.ports.clear()
        if "Bus" in self.symbol:
            length = max(80.0, parse_float(self.data.get("母线长度 (px)"), 180.0))
            coords = [length * ratio for ratio in [-0.45, -0.30, -0.15, 0.0, 0.15, 0.30, 0.45]]
            port_type = "AC" if self.symbol == "AC_Bus" else "DC"
            for pos in coords:
                port = NodePort(self, port_type=port_type)
                port.setPos(pos, 0)
                self.ports.append(port)
            return

        port_types = self._default_port_types()
        points = [
            QPointF(-self.width / 2, 0),
            QPointF(self.width / 2, 0),
            QPointF(0, -self.height / 2),
            QPointF(0, self.height / 2),
        ]
        for point, port_type in zip(points, port_types):
            port = NodePort(self, port_type=port_type)
            port.setPos(point)
            self.ports.append(port)

    def _default_port_types(self) -> list[str]:
        if self.symbol in {"PV", "FC", "Battery", "SC", "FES", "SMES", "EL", "DC_DC", "BIDIR_DC_DC"}:
            return ["DC", "DC", "DC", "DC"]
        if self.symbol in {"Grid", "Load", "MT"}:
            return ["AC", "AC", "AC", "AC"]
        if self.symbol == "WT":
            return ["AC_VAR", "AC_VAR", "AC_VAR", "AC_VAR"]
        if self.symbol == "DC_AC":
            return ["DC", "AC", "DC", "AC"]
        if self.symbol == "AC_DC":
            return ["AC", "DC", "AC", "DC"]
        if self.symbol == "PCS":
            return ["DC", "AC", "DC", "AC"]
        return ["ANY", "ANY", "ANY", "ANY"]

    def _update_bus_ports(self):
        orientation = self.data.get("布置方向 (H/V)", "H").strip().upper()
        length = max(80.0, parse_float(self.data.get("母线长度 (px)"), 180.0))
        coords_value = [length * ratio for ratio in [-0.45, -0.30, -0.15, 0.0, 0.15, 0.30, 0.45]]
        if orientation == "V":
            self.width, self.height = 10, length
            coords = [QPointF(0, y) for y in coords_value]
        else:
            self.width, self.height = length, 10
            coords = [QPointF(x, 0) for x in coords_value]
        for port, coord in zip(self.ports, coords):
            port.setPos(coord)
            for edge in port.edges:
                edge.update_path()

    def mouseDoubleClickEvent(self, event):
        from dialogs import PropertyDialog

        dialog = PropertyDialog(f"{self.name} 参数", self.data)
        if dialog.exec():
            self.data = dialog.get_data()
            if "Bus" in self.symbol:
                self.prepareGeometryChange()
                self._update_bus_ports()
            self.update()
        super().mouseDoubleClickEvent(event)

    def boundingRect(self):
        label_space = 28 if "Bus" not in self.symbol else 18
        return QRectF(-self.width / 2 - 18, -self.height / 2 - label_space, self.width + 36, self.height + label_space + 20)

    def paint(self, painter: QPainter, option, widget=None):
        body = QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
        if self.isSelected():
            painter.setPen(QPen(QColor(210, 62, 62), 2, Qt.PenStyle.DashLine))
        else:
            painter.setPen(QPen(QColor(67, 76, 86), 2))
        painter.setBrush(QBrush(self.base_color))
        radius = 2 if "Bus" in self.symbol else 7
        painter.drawRoundedRect(body, radius, radius)

        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255) if "Bus" in self.symbol else QColor(30, 35, 40))
        label = "AC" if self.symbol == "AC_Bus" else "DC" if self.symbol == "DC_Bus" else self.comp_type
        painter.drawText(body, Qt.AlignmentFlag.AlignCenter, label)

        name_rect = QRectF(-self.width / 2 - 28, -self.height / 2 - 24, self.width + 56, 18)
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.setPen(QColor(30, 35, 40))
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, self.name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.ports:
                for edge in port.edges:
                    edge.update_path()
        return super().itemChange(change, value)
