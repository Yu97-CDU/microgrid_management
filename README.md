项目简介 (Description)

“新能源微电网运行与经济性分析平台”是一款集交互式建模、潮流分析与经济性评估于一体的桌面端可视化工具。

本项目为高校微电网/智能电网课程教学与基础研究设计，平台基于 Python 和 PyQt6 打造，提供直观的“拖拽式”绘图面板，用户可自由连接光伏（PV）、风电（WT）、储能（BESS）、燃料电池（FC）及各类交直流母线与变换器，快速构建定制化的交直流混合微电网拓扑。

软件内置了稳态能量流求解器，不仅能自动校验拓扑连接的合法性，还能精确计算系统在 24 小时周期内的多项关键指标。核心计算涵盖：线路与变换器损耗、新能源消纳率（弃风弃光率）、碳减排量、日运行综合成本以及全生命周期平准化度电成本（LCOE）。

本项目为教学版（Teaching）版本：侧重于原理剖析与课堂互动。内置详细的公式推导、设备选型建议与典型错误拓扑案例，帮助学生快速掌握微电网底层的运行逻辑与调度假设。
本项目仅供学术与教育目的开源共享，严禁未经授权的商业用途。

The "Renewable Energy Microgrid Operation and Economic Analysis Platform" is an interactive desktop application integrating visual topology modeling, steady-state power flow analysis, and economic evaluation.

Designed specifically for academic research and university-level power systems teaching, Built with Python and PyQt6, the platform features an intuitive drag-and-drop canvas. Users can freely connect components—including Photovoltaic (PV), Wind Turbines (WT), Battery Energy Storage Systems (BESS), Fuel Cells (FC), and various AC/DC buses/converters—to rapidly construct customized hybrid AC/DC microgrid topologies.

The software embeds a steady-state energy flow solver that not only validates topological connections automatically but also accurately computes key metrics over a 24-hour cycle. Core analyses cover: line and converter power losses, renewable energy utilization (and curtailment) rates, carbon emission reductions, daily operating costs, and the Levelized Cost of Energy (LCOE).

The project is a Teaching Version: Focuses on pedagogical interaction. It includes built-in formula derivations, component principles, and typical error case studies, helping students grasp the underlying logic and scheduling assumptions of microgrids.

This repository is open-sourced strictly for academic and educational purposes. Commercial use is strictly prohibited without explicit authorization.
