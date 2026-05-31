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

import csv
import html
import json
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QAction, QActionGroup, QDrag
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDockWidget,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from analysis import analyze_microgrid
from canvas import MicrogridCanvas
from charts import EconomicChartWidget
from nodes import COMPONENT_LIBRARY, ConnectionLine, component_abbreviation
from teaching_content import (
    FORMULA_REFERENCE_HTML,
    GREEN_LOW_CARBON_HTML,
    PARAMETER_SOURCE_HTML,
    SIMPLIFIED_MODEL_NOTE,
    SIMPLIFIED_FLOW_ASSUMPTIONS_HTML,
    TEACHING_TASKS_HTML,
    component_principle_html,
    error_cases_html,
    layer_note_html,
)
from topology_rules import component_tip, port_connection_warning


class ComponentTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("微电网元件库")
        self.setDragEnabled(True)
        self.setRootIsDecorated(True)
        self.setStyleSheet(
            """
            QTreeWidget {
                background: #ffffff;
                border: 1px solid #d8dee9;
                border-radius: 6px;
                font-size: 13px;
            }
            QTreeWidget::item {
                min-height: 28px;
                padding: 3px 6px;
            }
            QTreeWidget::item:hover {
                background: #eef6ff;
            }
            QTreeWidget::item:selected {
                background: #dbeafe;
                color: #1d4ed8;
            }
            """
        )
        self._init_tree()

    def _init_tree(self):
        for group_name, entries in COMPONENT_LIBRARY.items():
            group = QTreeWidgetItem(self, [group_name])
            group.setFlags(group.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            for display_name, symbol, _ in entries:
                item = QTreeWidgetItem(group, [f"{display_name} ({component_abbreviation(symbol)})"])
                item.setData(0, Qt.ItemDataRole.UserRole, symbol)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
        self.expandAll()

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item or item.parent() is None:
            return
        symbol = item.data(0, Qt.ItemDataRole.UserRole)
        if not symbol:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-microgrid-symbol", str(symbol).encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.hint = QLabel("从左侧拖入元件，连接端口后点击“运行分析”。")
        self.hint.setTextFormat(Qt.TextFormat.RichText)
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #475569; padding: 8px;")
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["指标", "结果"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.hint)
        layout.addWidget(self.table)

    def update_result(self, result):
        totals = result.totals
        rows = [
            ("节点数量", f"{totals['nodes']:.0f}"),
            ("线路数量", f"{totals['edges']:.0f}"),
            ("当前发电功率", f"{totals['generation_kw']:.1f} kW"),
            ("当前负荷功率", f"{totals['load_kw']:.1f} kW"),
            ("日负荷电量", f"{totals['load_energy_kwh']:.1f} kWh"),
            ("日可再生能源电量", f"{totals['renewable_energy_kwh']:.1f} kWh"),
            ("可再生能源占比", f"{totals['renewable_ratio'] * 100:.1f}%"),
            ("本地新能源消纳电量", f"{totals['renewable_local_used_kwh']:.1f} kWh"),
            ("本地新能源消纳率", f"{totals['renewable_utilization_rate'] * 100:.1f}%"),
            ("新能源外送电量", f"{totals['renewable_export_kwh']:.1f} kWh"),
            ("弃新能源电量", f"{totals['renewable_curtailed_kwh']:.1f} kWh"),
            ("线路总损耗功率", f"{totals['line_loss_kw']:.3f} kW"),
            ("日线路损耗电量", f"{totals['line_loss_energy_kwh']:.2f} kWh"),
            ("日线路损耗成本", f"{totals['line_loss_cost_yuan_day']:.2f} 元"),
            ("变换器损耗功率", f"{totals['converter_loss_kw']:.3f} kW"),
            ("日变换器损耗电量", f"{totals['converter_loss_energy_kwh']:.2f} kWh"),
            ("日变换器损耗成本", f"{totals['converter_loss_cost_yuan_day']:.2f} 元"),
            ("日净购电量", f"{totals['grid_exchange_kwh']:.1f} kWh"),
            ("外购电减少量", f"{totals['grid_purchase_reduction_kwh']:.1f} kWh"),
            ("日碳减排量", f"{totals['carbon_reduction_kg_day']:.1f} kgCO2"),
            ("碳减排收益", f"{totals['carbon_benefit_yuan_day']:.2f} 元"),
            ("日运行成本", f"{totals['operating_cost_yuan_day']:.2f} 元"),
            ("低碳修正运行成本", f"{totals['low_carbon_operating_cost_yuan_day']:.2f} 元"),
            ("估算建设投资", f"{totals['capital_cost_yuan'] / 10000:.2f} 万元"),
            ("综合度电成本", f"{totals['lcoe_yuan_kwh']:.3f} 元/kWh"),
        ]
        self.table.setRowCount(len(rows))
        for row, (name, value) in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(value))
        self.hint.setText(self._format_messages(result.messages))

    def _format_messages(self, messages):
        if not messages:
            return "<span style='color:#111827;'>分析完成，潮流方向、线路损耗和负载率已标注在连接线上。</span>"

        lines = []
        for message in messages:
            color = self._message_color(message)
            lines.append(f"<div style='color:{color}; margin:2px 0;'>{html.escape(message)}</div>")
        return "".join(lines)

    def _message_color(self, message: str) -> str:
        error_keywords = ["错误", "失败", "无法", "不匹配", "不建议直接", "尚未连接", "请从左侧"]
        warning_keywords = ["警告", "越限", "拓扑建议", "建议", "超过", "负载率"]
        if any(keyword in message for keyword in error_keywords):
            return "#dc2626"
        if any(keyword in message for keyword in warning_keywords):
            return "#b7791f"
        return "#111827"


class TeachingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(False)
        self.viewer.setStyleSheet(
            """
            QTextBrowser {
                background: #ffffff;
                border: 1px solid #d8dee9;
                border-radius: 6px;
                padding: 10px;
                color: #111827;
                font-size: 13px;
                line-height: 1.45;
            }
            """
        )
        layout.addWidget(self.viewer)
        self.show_html(
            "教学版说明",
            f"<p>{html.escape(SIMPLIFIED_MODEL_NOTE)}</p>"
            "<p>建议先查看“教学任务案例”，再运行示例系统；涉及计算结果时，请同步查看“简化潮流假设”和“参数来源说明”。</p>"
            f"{layer_note_html('energy')}",
        )

    def show_html(self, title: str, body: str):
        self.viewer.setHtml(
            "<html><body>"
            f"<h2>{html.escape(title)}</h2>"
            f"{body}"
            "</body></html>"
        )

    def show_component(self, node):
        self.show_html("元件原理与接入建议", component_principle_html(node.symbol, node.name))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("新能源微电网运行与经济性分析平台")
        self.resize(1380, 840)
        self.current_result = None
        self.teaching_mode = True
        self.layer_mode = "energy"
        self._init_ui()

    def _init_ui(self):
        self.canvas = MicrogridCanvas(self)
        self.setCentralWidget(self.canvas)

        self.component_dock = QDockWidget("元件库", self)
        self.component_dock.setMinimumWidth(230)
        self.component_dock.setWidget(ComponentTreeWidget())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.component_dock)

        self.tabs = QTabWidget()
        self.result_panel = ResultPanel()
        self.chart_widget = EconomicChartWidget()
        self.teaching_panel = TeachingPanel()
        self.tabs.addTab(self.result_panel, "分析结果")
        self.tabs.addTab(self.chart_widget, "运行曲线")
        self.tabs.addTab(self.teaching_panel, "教学说明")

        self.result_dock = QDockWidget("运行与经济性分析", self)
        self.result_dock.setMinimumWidth(430)
        self.result_dock.setWidget(self.tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.result_dock)

        self._init_toolbar()
        self.canvas.node_added.connect(self.show_component_tip)
        self.canvas.node_selected.connect(self.show_component_tip)
        self.canvas.connection_created.connect(self.show_connection_tip)
        self.result_panel.hint.setText(f"<span style='color:#111827;'>{html.escape(SIMPLIFIED_MODEL_NOTE)}</span>")
        self.statusBar().showMessage("就绪：拖入元件并从端口拉线建立微电网拓扑。")
        author_label = QLabel("Yu Jiang, Chengdu University, jiangyu@cdu.edu.cn")
        author_label.setStyleSheet("color: #64748b; padding-right: 10px;")
        self.statusBar().addPermanentWidget(author_label)
        self.resizeDocks([self.component_dock, self.result_dock], [230, 450], Qt.Orientation.Horizontal)

    def _init_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        run_action = QAction("运行分析", self)
        run_action.triggered.connect(self.run_analysis)
        toolbar.addAction(run_action)

        example_action = QAction("加载示例系统", self)
        example_action.triggered.connect(self.load_example)
        toolbar.addAction(example_action)

        integrated_action = QAction("加载综合示例", self)
        integrated_action.triggered.connect(self.load_integrated_example)
        toolbar.addAction(integrated_action)

        clear_action = QAction("清空画布", self)
        clear_action.triggered.connect(self.clear_canvas)
        toolbar.addAction(clear_action)

        export_action = QAction("导出结果", self)
        export_action.triggered.connect(self.export_result)
        toolbar.addAction(export_action)

        save_action = QAction("保存工程", self)
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)

        load_action = QAction("加载工程", self)
        load_action.triggered.connect(self.load_project)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        self.teaching_action = QAction("教学模式", self)
        self.teaching_action.setCheckable(True)
        self.teaching_action.setChecked(True)
        self.teaching_action.triggered.connect(self.toggle_teaching_mode)
        toolbar.addAction(self.teaching_action)

        task_action = QAction("教学任务案例", self)
        task_action.triggered.connect(self.show_teaching_tasks)
        toolbar.addAction(task_action)

        error_action = QAction("典型错误案例", self)
        error_action.triggered.connect(self.load_typical_error_case)
        toolbar.addAction(error_action)

        formula_action = QAction("公式与参数来源", self)
        formula_action.triggered.connect(self.show_formula_reference)
        toolbar.addAction(formula_action)

        green_action = QAction("绿色低碳指标", self)
        green_action.triggered.connect(self.show_green_low_carbon)
        toolbar.addAction(green_action)

        parameter_action = QAction("参数来源说明", self)
        parameter_action.triggered.connect(self.show_parameter_sources)
        toolbar.addAction(parameter_action)

        assumptions_action = QAction("简化潮流假设", self)
        assumptions_action.triggered.connect(self.show_simplified_flow_assumptions)
        toolbar.addAction(assumptions_action)

        toolbar.addSeparator()

        self.layer_actions = QActionGroup(self)
        self.layer_actions.setExclusive(True)
        for text, mode in [
            ("物理拓扑层", "physical"),
            ("能量流层", "energy"),
            ("经济结果层", "economic"),
        ]:
            action = QAction(text, self)
            action.setCheckable(True)
            action.setData(mode)
            action.setChecked(mode == self.layer_mode)
            action.triggered.connect(lambda checked=False, m=mode: self.set_layer_mode(m))
            self.layer_actions.addAction(action)
            toolbar.addAction(action)

    def toggle_teaching_mode(self, checked: bool):
        self.teaching_mode = checked
        if checked:
            self.teaching_panel.show_html(
                "教学模式已开启",
                f"<p>{html.escape(SIMPLIFIED_MODEL_NOTE)}</p>"
                "<p>课堂建议：先按任务案例建立问题，再通过参数来源和简化假设解释结果边界。</p>"
                f"{layer_note_html(self.layer_mode)}",
            )
            self.tabs.setCurrentWidget(self.teaching_panel)
            self.statusBar().showMessage("教学模式已开启：点击元件可查看原理和接入建议。", 8000)
        else:
            self.statusBar().showMessage("教学模式已关闭：点击元件仅显示简短状态提示。", 8000)

    def set_layer_mode(self, mode: str):
        self.layer_mode = mode
        self.apply_layer_mode_to_edges()
        self.teaching_panel.show_html("分层视图说明", layer_note_html(mode))
        if mode == "economic":
            self.tabs.setCurrentWidget(self.result_panel)
        elif self.teaching_mode:
            self.tabs.setCurrentWidget(self.teaching_panel)
        layer_names = {"physical": "物理拓扑层", "energy": "能量流层", "economic": "经济结果层"}
        self.statusBar().showMessage(f"当前视图层：{layer_names.get(mode, mode)}", 8000)

    def apply_layer_mode_to_edges(self):
        for edge, _, _ in self.canvas.edge_items():
            edge.display_layer = self.layer_mode
            edge.update()

    def show_teaching_tasks(self):
        self.teaching_panel.show_html("任务式教学案例", TEACHING_TASKS_HTML)
        self.tabs.setCurrentWidget(self.teaching_panel)
        self.statusBar().showMessage("已显示任务式教学案例。", 8000)

    def show_formula_reference(self):
        self.teaching_panel.show_html(
            "公式与参数来源",
            f"{FORMULA_REFERENCE_HTML}<hr>{GREEN_LOW_CARBON_HTML}<hr>{PARAMETER_SOURCE_HTML}<hr>{SIMPLIFIED_FLOW_ASSUMPTIONS_HTML}",
        )
        self.tabs.setCurrentWidget(self.teaching_panel)
        self.statusBar().showMessage("已显示公式与参数来源说明。", 8000)

    def show_green_low_carbon(self):
        self.teaching_panel.show_html("绿色低碳指标", GREEN_LOW_CARBON_HTML)
        self.tabs.setCurrentWidget(self.teaching_panel)
        self.statusBar().showMessage("已显示绿色低碳指标说明。", 8000)

    def show_parameter_sources(self):
        self.teaching_panel.show_html("参数来源说明", PARAMETER_SOURCE_HTML)
        self.tabs.setCurrentWidget(self.teaching_panel)
        self.statusBar().showMessage("已显示参数来源说明。", 8000)

    def show_simplified_flow_assumptions(self):
        self.teaching_panel.show_html("简化潮流假设", SIMPLIFIED_FLOW_ASSUMPTIONS_HTML)
        self.tabs.setCurrentWidget(self.teaching_panel)
        self.statusBar().showMessage("已显示简化潮流模型假设。", 8000)

    def show_typical_error_explanation(self):
        self.teaching_panel.show_html("典型错误案例", error_cases_html())
        self.tabs.setCurrentWidget(self.teaching_panel)

    def run_analysis(self):
        graph = self.canvas.extract_topology()
        node_items = self.canvas.node_items()
        edge_items = self.canvas.edge_items()
        result = analyze_microgrid(graph, node_items, edge_items)
        self.current_result = result

        for edge, flow in result.flows.items():
            edge.update_power_flow(
                flow,
                result.line_losses.get(edge, 0.0),
                result.line_currents.get(edge, 0.0),
                result.line_loading.get(edge, 0.0),
            )
        self.result_panel.update_result(result)
        self.chart_widget.plot_result(result)
        self.apply_layer_mode_to_edges()
        if self.teaching_mode and result.messages:
            self.teaching_panel.show_html(
                "运行结果解读",
                "<p>结果面板中，红色表示连接错误或模型无法合理解释的问题；黄色表示拓扑建议、设备越限或需要学生进一步检查的警告；黑色表示正常信息。</p>"
                f"<p>{html.escape(SIMPLIFIED_MODEL_NOTE)}</p>",
            )

        self.statusBar().showMessage(
            f"分析完成：发电 {result.totals['generation_kw']:.1f} kW，"
            f"负荷 {result.totals['load_kw']:.1f} kW，"
            f"日运行成本 {result.totals['operating_cost_yuan_day']:.2f} 元。"
        )

    def show_component_tip(self, node):
        tip = component_tip(node.symbol)
        if not tip:
            return
        message = f"{node.name} 接入提示：{tip}"
        self.statusBar().showMessage(message, 12000)
        if hasattr(self, "result_panel"):
            self.result_panel.hint.setText(f"<span style='color:#111827;'>{html.escape(message)}</span>")
        if self.teaching_mode and hasattr(self, "teaching_panel"):
            self.teaching_panel.show_component(node)
            self.tabs.setCurrentWidget(self.teaching_panel)

    def show_connection_tip(self, line, start_node, end_node):
        line.display_layer = self.layer_mode
        warning = port_connection_warning(line, start_node, end_node)
        if not warning:
            self.statusBar().showMessage(f"已连接：{start_node.name} - {end_node.name}", 6000)
            return
        self.statusBar().showMessage(warning, 15000)
        color = self.result_panel._message_color(warning)
        self.result_panel.hint.setText(f"<span style='color:{color};'>拓扑提示：{html.escape(warning)}</span>")
        if self.teaching_mode:
            self.teaching_panel.show_html(
                "连接错误或拓扑警告",
                f"<p style='color:{color};'>{html.escape(warning)}</p>{error_cases_html()}",
            )
            self.tabs.setCurrentWidget(self.teaching_panel)

    def clear_canvas(self):
        self.canvas.clear_all()
        self.current_result = None
        self.chart_widget.plot_empty()
        self.result_panel.hint.setText("<span style='color:#111827;'>画布已清空。可以从左侧重新拖入元件。</span>")
        self.result_panel.table.setRowCount(0)
        if hasattr(self, "teaching_panel"):
            self.teaching_panel.show_html(
                "教学版说明",
                f"<p>{html.escape(SIMPLIFIED_MODEL_NOTE)}</p>"
                "<p>可通过“教学任务案例”“参数来源说明”“简化潮流假设”重新组织课堂演示。</p>"
                f"{layer_note_html(self.layer_mode)}",
            )
        self.statusBar().showMessage("画布已清空。")

    def load_example(self):
        self.clear_canvas()
        positions = {
            "Grid": (-620, -220),
            "AC_Bus": (-330, -220),
            "Load": (-40, -220),
            "DC_AC": (-330, -70),
            "DC_Bus": (-330, 90),
            "PV": (-620, 250),
            "DC_DC": (-450, 250),
            "WT": (-200, 250),
            "AC_DC": (-200, 90),
            "Battery": (-20, 250),
            "EL": (-40, 90),
        }
        nodes = {symbol: self.canvas.add_node(symbol, self.canvas.mapToScene(self.rect().center()) + self._point(dx, dy)) for symbol, (dx, dy) in positions.items()}
        nodes["BESS_BIDIR"] = self.canvas.add_node("BIDIR_DC_DC", self.canvas.mapToScene(self.rect().center()) + self._point(-20, 90))
        nodes["AC_Bus"].data["母线长度 (px)"] = "360"
        nodes["AC_Bus"]._update_bus_ports()
        nodes["DC_Bus"].data["母线长度 (px)"] = "360"
        nodes["DC_Bus"]._update_bus_ports()
        nodes["DC_AC"].data["额定容量 (kW)"] = "800"
        nodes["DC_DC"].data["额定容量 (kW)"] = "300"
        nodes["AC_DC"].data["额定容量 (kW)"] = "700"
        nodes["BESS_BIDIR"].data["额定容量 (kW)"] = "300"
        self._connect(nodes["Grid"], 1, nodes["AC_Bus"], 0, "hvh")
        self._connect(nodes["AC_Bus"], 6, nodes["Load"], 0, "hvh")
        self._connect(nodes["AC_Bus"], 3, nodes["DC_AC"], 1, "vhv")
        self._connect(nodes["DC_AC"], 0, nodes["DC_Bus"], 3, "vhv")
        self._connect(nodes["PV"], 1, nodes["DC_DC"], 0, "hvh")
        self._connect(nodes["DC_DC"], 1, nodes["DC_Bus"], 0, "vhv", 30)
        self._connect(nodes["WT"], 3, nodes["AC_DC"], 2, "vhv")
        self._connect(nodes["AC_DC"], 1, nodes["DC_Bus"], 4, "hvh")
        self._connect(nodes["Battery"], 3, nodes["BESS_BIDIR"], 2, "vhv")
        self._connect(nodes["BESS_BIDIR"], 1, nodes["DC_Bus"], 5, "hvh")
        self._connect(nodes["DC_Bus"], 6, nodes["EL"], 0, "hvh", -35)
        self.run_analysis()
        self.canvas.fit_all()

    def load_integrated_example(self):
        self.clear_canvas()
        center = self.canvas.mapToScene(self.rect().center())
        positions = {
            "Grid": (-760, -260),
            "AC_Bus": (-380, -260),
            "Load": (20, -260),
            "DC_AC": (-380, -80),
            "DC_Bus": (-380, 90),
            "PV": (-760, 300),
            "PV_DC_DC": (-560, 300),
            "WT": (-400, 300),
            "WT_AC_DC": (-400, 190),
            "Battery": (-130, 300),
            "BESS_BIDIR": (60, 300),
            "SC": (-130, 430),
            "SC_BIDIR": (60, 430),
            "FC": (160, 190),
            "FC_DC_DC": (0, 190),
            "EL": (180, 90),
            "PCS": (-560, -80),
            "FES": (-760, -80),
        }
        nodes = {
            key: self.canvas.add_node(
                "PV" if key == "PV" else
                "WT" if key == "WT" else
                "DC_DC" if key in {"PV_DC_DC", "FC_DC_DC"} else
                "AC_DC" if key == "WT_AC_DC" else
                "BIDIR_DC_DC" if key in {"BESS_BIDIR", "SC_BIDIR"} else
                key,
                center + self._point(x, y),
            )
            for key, (x, y) in positions.items()
        }

        nodes["AC_Bus"].data["母线长度 (px)"] = "520"
        nodes["AC_Bus"]._update_bus_ports()
        nodes["DC_Bus"].data["母线长度 (px)"] = "560"
        nodes["DC_Bus"]._update_bus_ports()
        converter_capacity = {
            "DC_AC": "900",
            "PV_DC_DC": "400",
            "WT_AC_DC": "700",
            "BESS_BIDIR": "300",
            "SC_BIDIR": "250",
            "FC_DC_DC": "200",
            "PCS": "300",
        }
        for key, value in converter_capacity.items():
            nodes[key].data["额定容量 (kW)"] = value
        nodes["PV"].data["额定功率 (kW)"] = "300"
        nodes["WT"].data["额定功率 (kW)"] = "600"
        nodes["FC"].data["当前工作功率 (kW)"] = "80"
        nodes["EL"].data["实时功率 (kW)"] = "120"
        nodes["SC"].data["最大功率 (kW)"] = "200"

        self._connect(nodes["Grid"], 1, nodes["AC_Bus"], 0, "hvh")
        self._connect(nodes["AC_Bus"], 6, nodes["Load"], 0, "hvh")
        self._connect(nodes["AC_Bus"], 3, nodes["DC_AC"], 1, "vhv")
        self._connect(nodes["DC_AC"], 0, nodes["DC_Bus"], 3, "vhv")
        self._connect(nodes["PV"], 1, nodes["PV_DC_DC"], 0, "hvh")
        self._connect(nodes["PV_DC_DC"], 1, nodes["DC_Bus"], 0, "vhv", 40)
        self._connect(nodes["WT"], 3, nodes["WT_AC_DC"], 2, "vhv")
        self._connect(nodes["WT_AC_DC"], 1, nodes["DC_Bus"], 2, "vhv", 20)
        self._connect(nodes["Battery"], 1, nodes["BESS_BIDIR"], 0, "hvh")
        self._connect(nodes["BESS_BIDIR"], 1, nodes["DC_Bus"], 4, "vhv", 25)
        self._connect(nodes["SC"], 1, nodes["SC_BIDIR"], 0, "hvh")
        self._connect(nodes["SC_BIDIR"], 1, nodes["DC_Bus"], 5, "vhv", 55)
        self._connect(nodes["FC"], 0, nodes["FC_DC_DC"], 1, "hvh")
        self._connect(nodes["FC_DC_DC"], 0, nodes["DC_Bus"], 1, "vhv", -25)
        self._connect(nodes["DC_Bus"], 6, nodes["EL"], 0, "hvh")
        self._connect(nodes["FES"], 1, nodes["PCS"], 0, "hvh")
        self._connect(nodes["PCS"], 1, nodes["AC_Bus"], 1, "vhv", -25)
        self.run_analysis()
        self.canvas.fit_all()

    def load_typical_error_case(self):
        self.clear_canvas()
        center = self.canvas.mapToScene(self.rect().center())
        positions = {
            "AC_Bus": (-80, -40),
            "PV": (-460, -160),
            "Battery": (-460, 120),
            "Load": (260, -40),
        }
        nodes = {
            symbol: self.canvas.add_node(symbol, center + self._point(x, y))
            for symbol, (x, y) in positions.items()
        }
        nodes["AC_Bus"].data["母线长度 (px)"] = "420"
        nodes["AC_Bus"]._update_bus_ports()
        nodes["PV"].data["额定功率 (kW)"] = "300"
        nodes["Battery"].data["最大功率 (kW)"] = "200"
        nodes["Load"].data["实时功率 (kW)"] = "-450"

        self._connect(nodes["PV"], 1, nodes["AC_Bus"], 1, "hvh", -40)
        self._connect(nodes["Battery"], 1, nodes["AC_Bus"], 5, "hvh", 40)
        self._connect(nodes["AC_Bus"], 6, nodes["Load"], 0, "hvh")
        self.show_typical_error_explanation()
        self.run_analysis()
        self.canvas.fit_all()

    def _point(self, x: int, y: int):
        return QPointF(float(x), float(y))

    def _connect(
        self,
        start_node,
        start_port_index: int,
        end_node,
        end_port_index: int,
        route_style: str = "auto",
        route_offset: float = 0.0,
    ):
        start_port = start_node.ports[start_port_index]
        end_port = end_node.ports[end_port_index]
        line = ConnectionLine(start_port=start_port)
        line.end_port = end_port
        line.route_style = route_style
        line.route_offset = route_offset
        line.display_layer = self.layer_mode
        start_port.add_edge(line)
        end_port.add_edge(line)
        self.canvas.scene.addItem(line)
        line.update_path()

    def export_result(self):
        if self.current_result is None:
            QMessageBox.information(self, "导出结果", "请先运行一次分析。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出结果", str(Path.cwd() / "microgrid_result.csv"), "CSV 文件 (*.csv)")
        if not path:
            return

        hourly = self.current_result.hourly
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                "hour",
                "irradiance_w_m2",
                "ambient_temp_c",
                "wind_speed_m_s",
                "load_kw",
                "pv_kw",
                "wt_kw",
                "controllable_kw",
                "storage_kw",
                "storage_soc",
                "line_loss_kw",
                "converter_loss_kw",
                "grid_import_kw",
                "grid_export_kw",
                "renewable_local_used_kwh",
                "renewable_export_kwh",
                "renewable_curtailed_kwh",
                "grid_purchase_reduction_kwh",
                "carbon_reduction_kg",
                "carbon_benefit_yuan",
                "operating_cost_yuan",
                "low_carbon_operating_cost_yuan",
            ])
            for idx, hour in enumerate(hourly["hour"]):
                writer.writerow(
                    [
                        int(hour),
                        f"{hourly['pv_irradiance'][idx]:.3f}",
                        f"{hourly['ambient_temp'][idx]:.3f}",
                        f"{hourly['wind_speed'][idx]:.3f}",
                        f"{hourly['load'][idx]:.3f}",
                        f"{hourly['pv'][idx]:.3f}",
                        f"{hourly['wt'][idx]:.3f}",
                        f"{hourly['controllable'][idx]:.3f}",
                        f"{hourly['storage'][idx]:.3f}",
                        f"{hourly['storage_soc'][idx]:.4f}",
                        f"{hourly['line_loss'][idx]:.3f}",
                        f"{hourly['converter_loss'][idx]:.3f}",
                        f"{hourly['grid_import'][idx]:.3f}",
                        f"{hourly['grid_export'][idx]:.3f}",
                        f"{hourly['renewable_local_used'][idx]:.3f}",
                        f"{hourly['renewable_export'][idx]:.3f}",
                        f"{hourly['renewable_curtailed'][idx]:.3f}",
                        f"{hourly['grid_purchase_reduction'][idx]:.3f}",
                        f"{hourly['carbon_reduction_kg'][idx]:.3f}",
                        f"{hourly['carbon_benefit'][idx]:.3f}",
                        f"{hourly['operating_cost'][idx]:.3f}",
                        f"{hourly['low_carbon_operating_cost'][idx]:.3f}",
                    ]
                )
        self.statusBar().showMessage(f"结果已导出：{path}")

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存工程", str(Path.cwd() / "microgrid_project.json"), "JSON 文件 (*.json)")
        if not path:
            return
        nodes = []
        for node in self.canvas.node_items():
            nodes.append(
                {
                    "name": node.name,
                    "symbol": node.symbol,
                    "x": node.pos().x(),
                    "y": node.pos().y(),
                    "data": node.data,
                }
            )
        lines = []
        for edge, start, end in self.canvas.edge_items():
            start_node = edge.start_port.parentItem()
            end_node = edge.end_port.parentItem()
            lines.append(
                {
                    "start": start,
                    "start_port": start_node.ports.index(edge.start_port),
                    "end": end,
                    "end_port": end_node.ports.index(edge.end_port),
                    "data": edge.data,
                    "route_style": edge.route_style,
                    "route_offset": edge.route_offset,
                }
            )
        payload = {"version": 1, "nodes": nodes, "lines": lines}
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.statusBar().showMessage(f"工程已保存：{path}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载工程", str(Path.cwd()), "JSON 文件 (*.json)")
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.clear_canvas()
            by_name = {}
            for node_data in payload.get("nodes", []):
                node = self.canvas.add_node(node_data["symbol"], QPointF(float(node_data["x"]), float(node_data["y"])))
                node.name = node_data["name"]
                node.data.update(node_data.get("data", {}))
                if "Bus" in node.symbol:
                    node._update_bus_ports()
                by_name[node.name] = node
                suffix = node.name.rsplit("_", 1)[-1]
                if suffix.isdigit():
                    self.canvas._node_counter[node.symbol] = max(self.canvas._node_counter.get(node.symbol, 0), int(suffix))
            for line_data in payload.get("lines", []):
                start_node = by_name[line_data["start"]]
                end_node = by_name[line_data["end"]]
                line = ConnectionLine(start_node.ports[int(line_data["start_port"])])
                line.end_port = end_node.ports[int(line_data["end_port"])]
                line.data.update(line_data.get("data", {}))
                line.route_style = line_data.get("route_style", "auto")
                line.route_offset = float(line_data.get("route_offset", 0.0))
                line.display_layer = self.layer_mode
                line.start_port.add_edge(line)
                line.end_port.add_edge(line)
                self.canvas.scene.addItem(line)
                line.update_path()
            self.run_analysis()
            self.statusBar().showMessage(f"工程已加载：{path}")
        except Exception as exc:
            QMessageBox.warning(self, "加载工程失败", str(exc))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        """
        QMainWindow { background: #f8fafc; }
        QDockWidget {
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            font-weight: 600;
            color: #1f2937;
        }
        QDockWidget::title {
            background: #eef2f7;
            padding: 7px 10px;
            border-bottom: 1px solid #d8dee9;
        }
        QToolBar {
            spacing: 6px;
            padding: 4px;
            background: #ffffff;
            border-bottom: 1px solid #d8dee9;
        }
        QToolButton {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            background: #ffffff;
        }
        QToolButton:hover { background: #eef6ff; }
        QTableWidget {
            background: #ffffff;
            gridline-color: #e5e7eb;
            alternate-background-color: #f8fafc;
        }
        """
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
