from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


class PropertyDialog(QDialog):
    def __init__(self, title: str, data_dict: dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.data_dict = data_dict.copy()
        self.line_edits: dict[str, QLineEdit] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        for key, value in self.data_dict.items():
            editor = QLineEdit(str(value))
            editor.setMinimumWidth(180)
            form.addRow(key, editor)
            self.line_edits[key] = editor

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict[str, str]:
        return {key: editor.text().strip() for key, editor in self.line_edits.items()}
