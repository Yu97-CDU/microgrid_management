from __future__ import annotations

import html


SIMPLIFIED_MODEL_NOTE = (
    "教学版说明：本软件用于帮助学生理解新能源微电网的拓扑关系、能量流向、"
    "环境参数影响和经济性指标。当前分析采用简化潮流与简化经济模型，"
    "不等同于严格 AC 潮流、暂态电磁仿真或设备级控制仿真。"
)


SIMPLIFIED_FLOW_ASSUMPTIONS_HTML = """
<h3>简化潮流模型假设</h3>
<p><b>教学定位：</b>当前模型用于本科阶段理解微电网拓扑、功率方向、损耗趋势和经济性指标，不能作为工程设计、保护整定或并网审查依据。</p>
<h4>1. 功率流计算假设</h4>
<ul>
<li>节点功率由元件当前功率或额定功率近似给出，新能源功率由环境参数修正得到。</li>
<li>线路功率方向用于教学显示，重点表达“能量从哪里来、到哪里去”，不求解完整三相 AC 潮流。</li>
<li>未严格求解节点电压相角、无功功率、电压跌落、频率动态和短路电流。</li>
<li>当网络结构复杂时，潮流结果用于趋势观察，不应解释为精确电气计算结果。</li>
</ul>
<h4>2. 线路与变换器假设</h4>
<ul>
<li>线路损耗采用 I²R 等效估算，电流由功率和电压等级近似换算。</li>
<li>变换器按固定效率估算损耗，不展开控制环节、谐波、开关损耗和热约束。</li>
<li>母线只表达 AC/DC 公共连接点，不进行母线电压稳定性和保护选择性分析。</li>
</ul>
<h4>3. 储能与经济性假设</h4>
<ul>
<li>储能 SOC 采用简化能量平衡，不考虑温度、寿命衰减、倍率限制和 BMS 保护细节。</li>
<li>经济性结果采用典型日运行成本和年化投资近似，适合比较方案，不替代全寿命周期财务评价。</li>
</ul>
<p><b>课堂建议：</b>让学生先用该模型判断拓扑是否合理，再讨论哪些假设在真实工程中必须被更严格的模型替代。</p>
"""


PARAMETER_SOURCE_HTML = """
<h3>参数来源说明</h3>
<p>教学版参数分为四类。学生修改参数时，应先判断该参数属于哪一类，再解释其对结果的影响。</p>
<table border="1" cellspacing="0" cellpadding="6">
<tr><th>参数类别</th><th>典型参数</th><th>建议来源</th><th>教学解释</th></tr>
<tr><td>铭牌参数</td><td>额定功率、额定容量、额定电压、最大载流量</td><td>设备样本、课程设定、厂家手册</td><td>决定设备规模和是否越限。</td></tr>
<tr><td>环境参数</td><td>辐照度、环境温度、风速、空气密度</td><td>气象数据、典型日曲线、课堂给定值</td><td>决定 PV 和 WT 的出力波动。</td></tr>
<tr><td>电气参数</td><td>线路长度、单位电阻、单位电抗、变换器效率</td><td>电缆手册、经验默认值、教学简化值</td><td>用于估算线路损耗、变换器损耗和设备负载率。</td></tr>
<tr><td>经济参数</td><td>电价、售电价、单位投资、运行维护成本</td><td>地方电价表、文献案例、教师设定情景</td><td>用于比较不同配置方案的成本趋势。</td></tr>
<tr><td>教学默认值</td><td>负荷曲线形状、储能初始 SOC、年化系数</td><td>软件内置默认值</td><td>用于降低入门难度，正式研究时应替换为真实数据。</td></tr>
</table>
<p><b>课堂要求：</b>报告中建议把“使用默认值”和“自行设定值”分开列出，避免把教学假设误写成工程实测数据。</p>
"""


GREEN_LOW_CARBON_HTML = """
<h3>绿色低碳指标模块</h3>
<p><b>教学目的：</b>把微电网经济性从“少花多少钱”扩展到“多消纳多少新能源、少排放多少二氧化碳”。该模块适合本科阶段理解经济-低碳协同分析。</p>
<h4>1. 新能源消纳能力</h4>
<p>新能源可发电量 = 光伏发电量 + 风电发电量。</p>
<p>本地新能源消纳电量表示被本地负荷、线路损耗、变换器损耗和储能充电等环节吸收的新能源电量。</p>
<p>本地新能源消纳率 = 本地新能源消纳电量 / 新能源可发电量。</p>
<p>新能源外送电量表示富余新能源通过并网送出的部分；弃新能源电量表示在教学模型中未被本地使用且未外送的部分。</p>
<h4>2. 外购电减少量</h4>
<p>基准外购电量 = 日负荷电量。该基准表示“没有本地新能源微电网时，负荷全部由大电网供电”。</p>
<p>外购电减少量 = 基准外购电量 - 当前外购电量。</p>
<h4>3. 碳减排量</h4>
<p>碳减排量 = 外购电减少量 * 电网排放因子。</p>
<p>教学版默认电网排放因子为 0.570 kgCO2/kWh。真实研究应根据所在区域或论文数据替换该参数。</p>
<h4>4. 碳减排收益与低碳修正成本</h4>
<p>碳减排收益 = 碳减排量(tCO2) * 碳价。教学版默认碳价为 80 元/tCO2。</p>
<p>低碳修正运行成本 = 日运行成本 - 碳减排收益。</p>
<p><b>注意：</b>绿证收益、碳配额、碳交易价格波动和生命周期碳排放暂未纳入，建议放在科研版或拓展讨论中。</p>
"""


TEACHING_TASKS_HTML = """
<h3>任务式教学案例</h3>
<p>以下案例适合本科课程实验、毕业设计入门或课堂演示。每个任务都建议学生记录“拓扑修改、参数修改、结果变化、原因解释”。</p>
<h4>任务 1：PV 为什么不能直连 AC 母线</h4>
<ol>
<li>点击“典型错误案例”，观察 PV -> AC Bus 的红色/黄色提示。</li>
<li>将路径改为 PV -> DC/DC -> DC Bus -> DC/AC -> AC Bus。</li>
<li>比较修改前后的拓扑提示，说明 MPPT、升降压和逆变环节的作用。</li>
</ol>
<h4>任务 2：风机为什么需要全功率变流链路</h4>
<ol>
<li>在示例系统中找到 WT、AC/DC、DC Bus、DC/AC 与 AC Bus。</li>
<li>修改风速参数，观察风电出力和购电量变化。</li>
<li>解释“波动交流”和“工频交流”之间为什么需要电力电子转换。</li>
</ol>
<h4>任务 3：储能接 DC 侧和 AC 侧的区别</h4>
<ol>
<li>比较 Battery -> 双向 DC/DC -> DC Bus 与 Battery -> PCS -> AC Bus 两种思路。</li>
<li>观察储能功率、SOC、变换器容量和损耗的变化。</li>
<li>说明双向 DC/DC 与 PCS 的功能边界。</li>
</ol>
<h4>任务 4：线路长度与损耗敏感性</h4>
<ol>
<li>双击线路，逐步增大线路长度或单位电阻。</li>
<li>运行分析，观察线路中点信息框中的损耗和负载率。</li>
<li>解释为什么远距离输电会提高损耗成本。</li>
</ol>
<h4>任务 5：环境参数对新能源出力的影响</h4>
<ol>
<li>分别修改 PV 的辐照度、环境温度，修改 WT 的风速。</li>
<li>运行分析并对比新能源电量、购电量、日运行成本。</li>
<li>说明新能源“装机容量”和“实际可发电量”的区别。</li>
</ol>
<h4>任务 6：经济性指标与拓扑方案比较</h4>
<ol>
<li>加载示例系统和综合示例，分别运行分析。</li>
<li>切换到经济结果层，比较投资、损耗成本、运行成本和 LCOE。</li>
<li>讨论“设备更多”是否一定意味着“经济性更好”。</li>
</ol>
"""


LAYER_NOTES = {
    "physical": (
        "物理拓扑层",
        "重点观察元件、母线和电力电子接口的连接关系。此层弱化功率箭头和线路标签，"
        "适合检查 PV、风机、储能、直流母线和交流母线之间的物理接入路径是否合理。",
    ),
    "energy": (
        "能量流层",
        "重点观察功率方向、线路损耗和负载率。此层显示功率箭头和线路中点信息框，"
        "适合讲解源-网-荷-储之间的能量平衡关系。",
    ),
    "economic": (
        "经济结果层",
        "重点观察日运行成本、购售电、电能损耗成本、估算投资和 LCOE。此层弱化拓扑线条，"
        "鼓励学生把拓扑结构与经济指标联系起来。",
    ),
}


COMPONENT_PRINCIPLES = {
    "PV": {
        "title": "光伏 PV",
        "body": (
            "光伏阵列本质上输出直流电，输出功率主要受太阳辐照度、组件温度、额定功率和 MPPT/DC-DC 环节影响。"
            "教学建模中可先用辐照度比例和温度修正估算直流侧功率，再通过 DC/DC 和 DC/AC 接入交流母线。"
        ),
        "path": "推荐路径：PV -> DC/DC(MPPT/升降压) -> DC Bus -> DC/AC -> AC Bus。",
    },
    "WT": {
        "title": "风机 WT",
        "body": (
            "风机输出随风速三次方近似变化，且发电机端电压、频率和功率会随转速、控制策略和风况波动。"
            "教学建模中采用切入、额定、切出风速的分段功率曲线，并用 AC/DC + DC/AC 表示全功率变流并网链路。"
        ),
        "path": "推荐路径：WT -> AC/DC -> DC Bus -> DC/AC -> AC Bus。",
    },
    "Battery": {
        "title": "电池储能 Battery",
        "body": (
            "电池单体/电池簇属于直流储能，本体不应直接挂到交流母线。"
            "在直流微电网或直流母线侧，常通过双向 DC/DC 管理充放电、电压匹配和 SOC；"
            "在交流侧储能系统中，通常由 PCS 完成直流电池与交流母线之间的双向功率交换。"
        ),
        "path": "直流侧：Battery -> 双向 DC/DC -> DC Bus；交流侧：Battery -> PCS -> AC Bus。",
    },
    "SC": {
        "title": "超级电容 SC",
        "body": "超级电容适合快速功率支撑和短时能量缓冲，通常通过双向 DC/DC 接入直流母线，也可经 PCS 接入交流侧。",
        "path": "推荐路径：SC -> 双向 DC/DC -> DC Bus，或 SC -> PCS -> AC Bus。",
    },
    "FES": {
        "title": "飞轮储能 FES",
        "body": "飞轮储能通过电机/发电机和变流器实现机械能与电能互换，直接接母线时应明确其电力电子接口。",
        "path": "推荐路径：FES -> PCS -> AC Bus，或经整流/逆变链路接入 DC/AC 系统。",
    },
    "SMES": {
        "title": "超导储能 SMES",
        "body": "超导储能以直流电磁能形式储能，工程上需要功率变换装置实现快速充放电和并网控制。",
        "path": "推荐路径：SMES -> 双向 DC/DC -> DC Bus，或 SMES -> PCS -> AC Bus。",
    },
    "EL": {
        "title": "电解槽 EL",
        "body": "电解槽通常需要可控直流供电，适合吸收新能源富余电量制氢。若来自交流侧，需经 AC/DC 整流。",
        "path": "推荐路径：DC Bus -> EL，或 AC Bus -> AC/DC -> EL。",
    },
    "FC": {
        "title": "燃料电池 FC",
        "body": "燃料电池输出通常为直流，动态响应慢于电力电子装置，教学模型中可作为可控直流电源或氢能回发电单元。",
        "path": "推荐路径：FC -> DC/DC -> DC Bus -> DC/AC -> AC Bus。",
    },
    "DC_DC": {
        "title": "普通 DC/DC",
        "body": "普通 DC/DC 主要用于直流电压匹配、升降压和光伏 MPPT，适合表示单向或不强调储能控制的直流变换环节。",
        "path": "典型用途：PV/FC -> DC/DC -> DC Bus。",
    },
    "BIDIR_DC_DC": {
        "title": "双向 DC/DC",
        "body": "双向 DC/DC 是储能侧常用接口，可同时表达充电和放电方向，适合讲解 SOC、功率限值和直流母线支撑。",
        "path": "典型用途：Battery/SC/SMES -> 双向 DC/DC -> DC Bus。",
    },
    "PCS": {
        "title": "PCS 储能变流器",
        "body": "PCS 是储能系统接入交流侧的核心接口，完成 DC/AC 双向变换、并网控制、功率因数和保护协调等功能。",
        "path": "典型用途：Battery/FES/SC -> PCS -> AC Bus。",
    },
    "DC_AC": {
        "title": "DC/AC 逆变器",
        "body": "DC/AC 将直流侧能量变换为工频交流，是光伏、直流母线、燃料电池和部分储能并入交流侧的关键接口。",
        "path": "典型用途：DC Bus -> DC/AC -> AC Bus。",
    },
    "AC_DC": {
        "title": "AC/DC 整流器",
        "body": "AC/DC 将交流变为直流，可用于风电全功率变流的前级，也可用于交流侧供电给电解槽或直流负荷。",
        "path": "典型用途：WT -> AC/DC -> DC Bus，或 AC Bus -> AC/DC -> EL。",
    },
    "AC_Bus": {
        "title": "交流母线 AC Bus",
        "body": "交流母线表示工频交流公共连接点，适合连接电网、交流负荷、逆变器、PCS 和微燃机等交流侧设备。",
        "path": "检查重点：直流设备接入 AC Bus 前是否经过 DC/AC 或 PCS。",
    },
    "DC_Bus": {
        "title": "直流母线 DC Bus",
        "body": "直流母线表示直流公共连接点，适合连接光伏、储能、燃料电池、电解槽和 DC/DC 变换器。",
        "path": "检查重点：与 AC Bus 之间是否经过 DC/AC 或 AC/DC。",
    },
    "Grid": {
        "title": "外部电网 Grid",
        "body": "外部电网在教学模型中作为能量缺口补偿和富余电量吸收端，用于计算购电、售电和并网交换。",
        "path": "典型用途：Grid -> AC Bus。",
    },
    "Load": {
        "title": "负荷 Load",
        "body": "负荷表示用电需求。教学模型中可用典型日负荷曲线放大当前功率，帮助观察源荷不匹配和储能调节作用。",
        "path": "典型用途：AC Bus -> Load；直流负荷可用 DC Bus 侧设备表示。",
    },
    "MT": {
        "title": "微燃机 MT",
        "body": "微燃机属于可控交流电源，通常用于补充新能源波动和负荷缺口，经济分析中会体现燃料成本或运行成本。",
        "path": "典型用途：MT -> AC Bus。",
    },
}


ERROR_CASES = [
    {
        "title": "错误案例 1：PV 直连 AC Bus",
        "wrong": "PV -> AC Bus",
        "why": "光伏阵列输出为直流，直接接入交流母线缺少 MPPT、电压匹配和逆变并网环节。",
        "fix": "PV -> DC/DC -> DC Bus -> DC/AC -> AC Bus。",
    },
    {
        "title": "错误案例 2：Battery 直连 AC Bus",
        "wrong": "Battery -> AC Bus",
        "why": "电池本体为直流储能，直接接交流母线既不符合电气接口，也无法表达充放电控制和并网控制。",
        "fix": "Battery -> 双向 DC/DC -> DC Bus，或 Battery -> PCS -> AC Bus。",
    },
    {
        "title": "扩展案例：WT 直连 AC Bus",
        "wrong": "WT -> AC Bus",
        "why": "风机端电压和频率会随风况与转速波动，不能简单等同于稳定工频交流电源。",
        "fix": "WT -> AC/DC -> DC Bus -> DC/AC -> AC Bus。",
    },
]


FORMULA_REFERENCE_HTML = """
<h3>简化模型与公式来源说明</h3>
<p><b>定位：</b>本教学版用于概念理解和方案比较，参数来自课堂常用近似、设备铭牌参数和文献中常见的典型曲线形式，不作为工程验算结论。</p>
<h4>1. 光伏功率</h4>
<p>P_pv = P_stc * G / 1000 * [1 + alpha * (T_cell - 25)] * eta_dc</p>
<p>T_cell = T_amb + (NOCT - 20) / 800 * G。G 为辐照度，T_amb 为环境温度，alpha 为温度系数。</p>
<h4>2. 风机功率</h4>
<p>v &lt; v_ci 或 v &gt; v_co 时 P_wt = 0；v_ci 到 v_r 之间按 v^3 分段上升；v_r 到 v_co 之间取额定功率。</p>
<p>该模型适合教学讲解风速敏感性，不替代厂家功率曲线或风电机组控制模型。</p>
<h4>3. 储能 SOC</h4>
<p>SOC(t+1) = SOC(t) + eta_ch * P_ch * dt / E_cap - P_dis * dt / (eta_dis * E_cap)。</p>
<p>教学版主要反映充放电方向、效率和容量约束，不展开电池退化、温度、C-rate 和 BMS 保护细节。</p>
<h4>4. 线路损耗</h4>
<p>P_loss = I^2 * R_total，R_total = r_per_km * L。电流由线路功率和电压等级近似估算。</p>
<p>这是等效有功损耗估算，不等同于完整三相潮流、电压分布和无功优化。</p>
<h4>5. 变换器损耗</h4>
<p>P_conv_loss = P_throughput * (1 - eta)。PCS、DC/AC、AC/DC、DC/DC 和双向 DC/DC 均按效率近似。</p>
<h4>6. 经济指标</h4>
<p>日运行成本 = 购电成本 - 售电收益 + 损耗电量成本 + 可控电源运行成本。</p>
<p>LCOE = (年化投资 + 年运行成本) / 年供电量。教学版用于比较方案，不替代全寿命周期财务模型。</p>
"""


def component_principle_html(symbol: str, name: str = "") -> str:
    item = COMPONENT_PRINCIPLES.get(symbol)
    if item is None:
        title = html.escape(name or symbol)
        return f"<h3>{title}</h3><p>该元件暂无专门教学说明，可查看参数表和拓扑连接建议。</p>"
    display_title = html.escape(item["title"])
    prefix = f"<p><b>当前元件：</b>{html.escape(name)}</p>" if name else ""
    return (
        f"<h3>{display_title}</h3>"
        f"{prefix}"
        f"<p>{html.escape(item['body'])}</p>"
        f"<p><b>接入建议：</b>{html.escape(item['path'])}</p>"
    )


def error_cases_html() -> str:
    blocks = ["<h3>典型错误案例</h3>"]
    for case in ERROR_CASES:
        blocks.append(
            "<div style='margin-bottom:10px;'>"
            f"<b>{html.escape(case['title'])}</b>"
            f"<p><span style='color:#dc2626;'>错误连接：</span>{html.escape(case['wrong'])}</p>"
            f"<p><span style='color:#b7791f;'>原因：</span>{html.escape(case['why'])}</p>"
            f"<p><span style='color:#111827;'>推荐改法：</span>{html.escape(case['fix'])}</p>"
            "</div>"
        )
    return "".join(blocks)


def layer_note_html(mode: str) -> str:
    title, body = LAYER_NOTES.get(mode, LAYER_NOTES["energy"])
    return f"<h3>{html.escape(title)}</h3><p>{html.escape(body)}</p>"
