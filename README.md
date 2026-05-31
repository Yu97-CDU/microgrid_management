项目简介 (Description)

“新能源微电网运行与经济性分析平台”是一款集交互式建模、潮流分析与经济性评估于一体的桌面端可视化工具。

本项目为高校微电网/智能电网课程教学与基础研究设计，平台基于 Python 和 PyQt6 打造，提供直观的“拖拽式”绘图面板，用户可自由连接光伏（PV）、风电（WT）、储能（BESS）、燃料电池（FC）及各类交直流母线与变换器，快速构建定制化的交直流混合微电网拓扑。

软件内置了稳态能量流求解器，不仅能自动校验拓扑连接的合法性，还能精确计算系统在 24 小时周期内的多项关键指标。核心计算涵盖：线路与变换器损耗、新能源消纳率（弃风弃光率）、碳减排量、日运行综合成本以及全生命周期平准化度电成本（LCOE）。

本项目为教学版（Teaching）版本：侧重于原理剖析与课堂互动。内置详细的公式推导、设备选型建议与典型错误拓扑案例，帮助学生快速掌握微电网底层的运行逻辑与调度假设。


## 版权与免责声明
本项目（含全部源代码、文档及 UI 设计）仅供**学术研究**与**课堂教学**使用。
**限制与声明：**
1. **严禁商用**：未经作者明确书面授权，严禁将本项目用于任何商业目的（包括但不限于封装为商业软件出售、用于企业内部盈利项目、提供商业咨询服务等）。
2. **免责声明**：本项目按“原样”提供。作者对模型计算的绝对准确性不作任何保证。使用者因使用本软件或其计算结果而产生的任何直接或间接损失（包括设备损坏、经济损失或法律纠纷），作者概不负责。
3. **分发要求**：若您在 GitHub Fork 或分享本项目，请务必保留本免责声明及代码文件顶部的版权信息。

## 开发者寄语与联系方式
本项目由个人独立开发，由于自身精力与能力有限，代码结构与模型算法难免存在不足或疏漏之处。非常欢迎各位老师、同学和同行批评指正！
如果您在使用过程中发现任何 Bug、有好的改进建议，或者对底层计算模型有疑问，欢迎随时与我联系。本项目后续也将持续进行优化和迭代。
**联系邮箱**：[jiangyu@cdu.edu.cn]


The "Renewable Energy Microgrid Operation and Economic Analysis Platform" is an interactive desktop application integrating visual topology modeling, steady-state power flow analysis, and economic evaluation.

Designed specifically for academic research and university-level power systems teaching, Built with Python and PyQt6, the platform features an intuitive drag-and-drop canvas. Users can freely connect components—including Photovoltaic (PV), Wind Turbines (WT), Battery Energy Storage Systems (BESS), Fuel Cells (FC), and various AC/DC buses/converters—to rapidly construct customized hybrid AC/DC microgrid topologies.

The software embeds a steady-state energy flow solver that not only validates topological connections automatically but also accurately computes key metrics over a 24-hour cycle. Core analyses cover: line and converter power losses, renewable energy utilization (and curtailment) rates, carbon emission reductions, daily operating costs, and the Levelized Cost of Energy (LCOE).

The project is a Teaching Version: Focuses on pedagogical interaction. It includes built-in formula derivations, component principles, and typical error case studies, helping students grasp the underlying logic and scheduling assumptions of microgrids.

## Copyright and Disclaimer

This project (including all source code, documentation, and UI design) is intended solely for **academic research** and **classroom teaching**.

**Restrictions and Disclaimers:**
1. **Commercial Use Strictly Prohibited:** Without the author's explicit written authorization, this project may not be used for any commercial purpose (including but not limited to packaging it as commercial software for sale, using it for internal profit-making projects, providing business consulting services, etc.).
2. **Disclaimer:** This project is provided "as is". The author makes no guarantee as to the absolute accuracy of the model calculations. The author is not liable for any direct or indirect losses (including equipment damage, economic losses, or legal disputes) arising from the use of this software or its calculation results.
3. **Distribution Requirements:** If you fork or share this project on GitHub, please be sure to retain this disclaimer and the copyright information at the top of the code files.

## Developer's Message and Contact Information
This project is independently developed. Due to limited time and personal capability, there may inevitably be shortcomings, bugs, or oversights in the code structure and model algorithms. Feedback, corrections, and suggestions from teachers, students, and peers are highly welcomed!
If you find any bugs, have suggestions for improvement, or have questions about the underlying principles, please feel free to contact me. This project will be continuously updated and improved in the future.
**Contact Email**: [jiangyu@cdu.edu.cn]
