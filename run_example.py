from __future__ import annotations

import os
import sys
from pathlib import Path

# Create a QApplication before importing and using any QGraphicsItem
from PyQt6.QtWidgets import QApplication

# Initialize QApplication (necessary for creating QGraphicsItems programmatically)
app = QApplication.instance() or QApplication(sys.argv)

import matplotlib.pyplot as plt
import numpy as np

from analysis import analyze_microgrid
from canvas import MicrogridCanvas
from nodes import ConnectionLine


def run_programmatic_example():
    print("=" * 70)
    print("      新能源微电网拓扑解析、潮流计算与经济性调度示例运行程序")
    print("=" * 70)
    
    # 1. 创建画布与场景 (内部会自动实例化 MicrogridScene)
    print("[1/4] 正在初始化微电网拓扑画布...")
    canvas = MicrogridCanvas()
    
    # 2. 模拟用户拖拽：向画布中添加微电网元件节点
    print("[2/4] 正在构建微电网拓扑系统...")
    # 各节点坐标定位
    positions = {
        "Grid": (-430, -120),
        "AC_Bus": (-170, -120),
        "PV": (-210, -300),
        "WT": (-20, -300),
        "Load": (110, -120),
        "DC_AC": (-170, 70),
        "DC_Bus": (70, 70),
        "Battery": (70, 230),
        "EL": (300, 70),
    }
    
    from PyQt6.QtCore import QPointF
    center = canvas.rect().center()
    nodes = {}
    for symbol, (dx, dy) in positions.items():
        scene_pos = canvas.mapToScene(center) + QPointF(float(dx), float(dy))
        nodes[symbol] = canvas.add_node(symbol, scene_pos)
        print(f"      添加元件: {nodes[symbol].name} ({nodes[symbol].comp_type})，坐标: ({dx}, {dy})")

    # 定义辅助连接函数，模仿连线拖拽交互
    def connect_ports(start_node, start_port_idx, end_node, end_port_idx):
        start_port = start_node.ports[start_port_idx]
        end_port = end_node.ports[end_port_idx]
        line = ConnectionLine(start_port=start_port)
        line.end_port = end_port
        start_port.add_edge(line)
        end_port.add_edge(line)
        canvas.scene.addItem(line)
        line.update_path()
        return line

    # 建立支路连线
    print("\n[3/4] 正在连接各元件引脚建立电气网络...")
    # 大电网 <-> 交流母线
    connect_ports(nodes["Grid"], 1, nodes["AC_Bus"], 0)
    # 光伏发电 <-> 交流母线
    connect_ports(nodes["PV"], 3, nodes["AC_Bus"], 2)
    # 风机发电 <-> 交流母线
    connect_ports(nodes["WT"], 3, nodes["AC_Bus"], 3)
    # 交流母线 <-> 负荷
    connect_ports(nodes["AC_Bus"], 4, nodes["Load"], 0)
    # 交流母线 <-> 逆变器(双向DC/AC)
    connect_ports(nodes["AC_Bus"], 1, nodes["DC_AC"], 0)
    # 逆变器 <-> 直流母线
    connect_ports(nodes["DC_AC"], 1, nodes["DC_Bus"], 0)
    # 直流母线 <-> 电池储能
    connect_ports(nodes["DC_Bus"], 2, nodes["Battery"], 2)
    # 直流母线 <-> 电解槽
    connect_ports(nodes["DC_Bus"], 4, nodes["EL"], 0)
    
    print("      已成功连接 8 条输电/变换支路。拓扑提取就绪。")

    # 3. 提取拓扑数据并运行潮流与经济性分析
    print("\n[4/4] 正在解析拓扑图结构并运行微电网联合仿真计算...")
    graph = canvas.extract_topology()
    node_items = canvas.node_items()
    edge_items = canvas.edge_items()
    
    # 调用底层核心算法
    result = analyze_microgrid(graph, node_items, edge_items)
    
    # 4. 打印分析报告
    print("\n" + "=" * 70)
    print("                        微电网系统分析结果报告")
    print("=" * 70)
    print(f"  [拓扑统计] 节点总数：{result.totals['nodes']:.0f} 个， 输电支路数：{result.totals['edges']:.0f} 条")
    print(f"  [当前功率] 实时发电：{result.totals['generation_kw']:.1f} kW， 实时负荷：{result.totals['load_kw']:.1f} kW")
    print(f"  [运行经济] 日运行成本：{result.totals['operating_cost_yuan_day']:.2f} 元/天")
    print(f"  [建设经济] 估算总投资：{result.totals['capital_cost_yuan'] / 10000:.2f} 万元")
    print(f"  [度电成本] 综合度电成本 (LCOE)：{result.totals['lcoe_yuan_kwh']:.3f} 元/kWh")
    print(f"  [绿色占比] 可再生能源电量占比：{result.totals['renewable_ratio'] * 100:.1f} %")
    print(f"  [网络交换] 日净购电量：{result.totals['grid_exchange_kwh']:.1f} kWh")
    print("-" * 70)
    
    # 打印24小时运行调度表
    print(f"{'小时':<6}{'负荷(kW)':<12}{'光伏(kW)':<12}{'风电(kW)':<12}{'储能功率(kW)':<15}{'电网购电(kW)':<15}{'时段成本(元)':<12}")
    print("-" * 70)
    hourly = result.hourly
    for i in range(24):
        # 储能功率：正为放电，负为充电
        storage_p = hourly["storage"][i]
        storage_str = f"{storage_p:+.1f}" if abs(storage_p) > 0.01 else "0.0"
        print(f"{i:<6d}{hourly['load'][i]:<12.1f}{hourly['pv'][i]:<12.1f}{hourly['wt'][i]:<12.1f}{storage_str:<15}{hourly['grid_import'][i]:<15.1f}{hourly['operating_cost'][i]:<12.2f}")
    print("=" * 70)

    # 5. 绘制24小时运行调度图并保存
    output_image = Path(__file__).parent / "example_result_chart.png"
    print(f"\n正在绘制运行特性曲线并保存至: {output_image.name} ...")
    
    # 设置支持中文的字体
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # 功率平衡图
    hours = hourly["hour"]
    ax1.plot(hours, hourly["load"], color="#2f3542", linewidth=2.5, label="电力总负荷")
    ax1.plot(hours, hourly["pv"], color="#e3a300", linewidth=2, label="光伏出力")
    ax1.plot(hours, hourly["wt"], color="#2374ab", linewidth=2, label="风机出力")
    ax1.plot(hours, hourly["controllable"], color="#c45f2d", linewidth=2, label="微型燃气轮机")
    
    # 储能以柱状图表示，充放电方向相反
    ax1.bar(hours, hourly["storage"], color="#4f9d69", alpha=0.5, label="储能系统 (正:放电 / 负:充电)")
    ax1.set_ylabel("有功功率 (kW)", fontsize=11)
    ax1.set_title("微电网24小时有功功率平衡图", fontsize=13, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=9, framealpha=0.9)
    
    # 成本与电价曲线
    ax2.plot(hours, hourly["operating_cost"], color="#7b2cbf", linewidth=2, marker="o", markersize=4, label="时段运行成本 (元/小时)")
    ax2_twin = ax2.twinx()
    ax2_twin.step(hours, hourly["price"], where="mid", color="#d11a2a", alpha=0.7, linestyle="--", label="分时电价 (元/kWh)")
    
    ax2.set_xlabel("时间轴 (Hour)", fontsize=11)
    ax2.set_ylabel("运行成本 (元/h)", color="#7b2cbf", fontsize=11)
    ax2_twin.set_ylabel("大电网电价 (元/kWh)", color="#d11a2a", fontsize=11)
    
    ax2.set_title("分时运行成本与电网电价走势对比", fontsize=13, fontweight="bold")
    ax2.set_xticks(np.arange(0, 24, 1))
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    # 合并图例
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_image, dpi=120)
    plt.close()
    
    print("      图表保存成功！")
    print("=" * 70)
    print("                [GUI 交互与图形界面联动指南]")
    print("=" * 70)
    print("  本控制台脚本分析的拓扑参数与平台的“图形可视化界面”示例完全一致。")
    print("  若您想在画布中交互式编辑属性参数、查看潮流流向与交互曲线：")
    print("\n  --> 快捷启动方式 (Windows 资源管理器中双击即可)：")
    print("     [双击运行批处理] -> file:///e:/Python_projects/pytools/gridmanagement/run_gui.bat")
    print("     [主入口 Python 代码] -> file:///e:/Python_projects/pytools/gridmanagement/main.py")
    print("\n  --> 命令行手动启动指令：")
    print("     D:/Anaconda3/envs/science/python.exe main.py")
    print("\n  --> GUI 联动操作步骤：")
    print("     1. 启动图形化平台窗口后，点击顶部工具栏的【加载示例系统】。")
    print("     2. 画布中央将自动加载出与本程序完全相同的 9 节点微电网拓扑。")
    print("     3. 双击任何节点(如电池、光伏、负荷)或连线，即可双击编辑其有功、容量及阻抗参数。")
    print("     4. 点击顶部【运行分析】，可动态刷新画布上的潮流方向箭头、颜色深浅，并在右侧直接展示曲线图。")
    print("=" * 70)


if __name__ == "__main__":
    run_programmatic_example()
