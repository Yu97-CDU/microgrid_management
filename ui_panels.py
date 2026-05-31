from __future__ import annotations

from PyQt6.QtWidgets import QFormLayout, QGroupBox, QLabel, QLineEdit, QVBoxLayout, QWidget


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.group_box = QGroupBox("选中元件属性")
        self.form_layout = QFormLayout()
        self.group_box.setLayout(self.form_layout)
        layout.addWidget(self.group_box)
        layout.addStretch()
        self.current_item = None
        self.inputs: dict[str, QLineEdit] = {}

    def set_item(self, item):
        self.clear()
        self.current_item = item
        data = getattr(item, "data", getattr(item, "properties", {}))
        for key, value in data.items():
            editor = QLineEdit(str(value))
            editor.textChanged.connect(lambda text, k=key: self.update_property(k, text))
            self.form_layout.addRow(key, editor)
            self.inputs[key] = editor

    def update_property(self, key: str, text: str):
        if self.current_item is None:
            return
        data = getattr(self.current_item, "data", None)
        if data is None:
            data = getattr(self.current_item, "properties", None)
        if data is not None:
            data[key] = text

    def clear(self):
        self.current_item = None
        self.inputs.clear()
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class EconomicPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.result_label = QLabel("暂无分析结果。")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        layout.addStretch()

    def update_results(self, results: dict):
        self.result_label.setText(
            "经济性分析完成\n"
            f"节点数：{results.get('nodes_count', '-')}\n"
            f"线路数：{results.get('edges_count', '-')}\n"
            f"建设投资：{results.get('capital_cost', '-')} 万元\n"
            f"综合度电成本：{results.get('lcoe', '-')} 元/kWh"
        )
