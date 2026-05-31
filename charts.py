from __future__ import annotations

import matplotlib
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QVBoxLayout, QWidget


matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
matplotlib.rcParams["axes.unicode_minus"] = False


class EconomicChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.plot_empty()

    def plot_empty(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "运行分析后显示功率与成本曲线", ha="center", va="center", fontsize=11)
        ax.set_axis_off()
        self.canvas.draw()

    def plot_result(self, result):
        hourly = result.hourly
        hours = hourly["hour"]
        self.figure.clear()

        ax1 = self.figure.add_subplot(211)
        ax1.plot(hours, hourly["load"], color="#2f3542", linewidth=2, label="负荷")
        ax1.plot(hours, hourly["pv"], color="#e3a300", linewidth=2, label="光伏")
        ax1.plot(hours, hourly["wt"], color="#2374ab", linewidth=2, label="风电")
        ax1.plot(hours, hourly["controllable"], color="#c45f2d", linewidth=2, label="可控电源")
        if "line_loss" in hourly:
            ax1.plot(hours, hourly["line_loss"], color="#8d99ae", linewidth=1.8, linestyle="--", label="线路损耗")
        if "converter_loss" in hourly:
            ax1.plot(hours, hourly["converter_loss"], color="#b08968", linewidth=1.8, linestyle=":", label="变换器损耗")
        ax1.bar(hours, hourly["storage"], color="#4f9d69", alpha=0.35, label="储能(+放电/-充电)")
        ax1.set_title("24小时功率平衡")
        ax1.set_ylabel("功率 (kW)")
        ax1.set_xticks(np.arange(0, 24, 4))
        ax1.grid(True, linestyle="--", alpha=0.35)
        ax1.legend(loc="upper left", ncols=3, fontsize=8)

        ax2 = self.figure.add_subplot(212)
        ax2.plot(hours, hourly["operating_cost"], color="#7b2cbf", linewidth=2, marker="o", markersize=3, label="运行成本")
        if "storage_soc" in hourly and hourly["storage_soc"].max() > 0:
            ax_soc = ax2.twinx()
            ax_soc.plot(hours, hourly["storage_soc"] * 100, color="#2d6a4f", linewidth=1.6, alpha=0.7, label="储能SOC")
            ax_soc.set_ylabel("SOC (%)")
            ax_soc.set_ylim(0, 100)
        ax2.set_title("分时运行成本")
        ax2.set_xlabel("时间 (h)")
        ax2.set_ylabel("成本 (元/h)")
        ax2.set_xticks(np.arange(0, 24, 4))
        ax2.grid(True, linestyle="--", alpha=0.35)
        ax2.legend(loc="upper left", fontsize=8)

        self.figure.tight_layout()
        self.canvas.draw()
