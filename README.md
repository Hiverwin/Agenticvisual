# VLM可视化分析系统

基于VLM和交互工具的智能图表分析系统，支持多种图表类型和分析模式。

## 核心功能链路

```
用户查询 → VLM理解意图 → 选择工具 → 执行工具 → 更新图表 → VLM分析结果 → 返回洞察
```

### 工作流程

1. **图表输入**: 系统接收Vega-Lite格式的图表规范
2. **意图识别**: VLM分析用户查询，理解分析意图
3. **工具调用**: VLM选择合适的工具进行感知或操作
4. **状态更新**: 工具修改图表状态或提取数据
5. **迭代分析**: VLM基于结果继续分析或调用更多工具
6. **结果输出**: 生成分析洞察和可视化

## 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repo-url>
cd visual-analysis-system-modified

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env文件，填入API_KEY
```

### 2. 基础使用

```python
from main import VisualAnalysisSystem

# 初始化系统
system = VisualAnalysisSystem()

# 加载图表
vega_spec = {...}  # Vega-Lite JSON
session_id = system.initialize_session(vega_spec)

# 分析查询
result = system.query(session_id, "这个图表有什么异常点？")
print(result['response'])
```

### 3. 支持的VLM

本系统支持任何VLM接入工具使用：

#### OpenAI GPT-4V
```python
from examples.generic_vlm_usage import GenericVLMVisualAnalyzer

analyzer = GenericVLMVisualAnalyzer()
tools = analyzer.get_tools_for_openai()
# 使用tools调用OpenAI API
```

#### Anthropic Claude
```python
tools = analyzer.get_tools_for_anthropic()
# 使用tools调用Claude API
```

#### 通用VLM（提示词方式）
```python
tools_prompt = analyzer.get_tools_as_prompt()
# 将tools_prompt添加到system prompt
```

详见 `examples/generic_vlm_usage.py`

**运行示例**：
```bash
# 从项目根目录运行
python run_examples.py usage
# 或
python -m examples.generic_vlm_usage
```

## 支持的图表类型

- 散点图 (Scatter Plot) - 聚类、相关性分析
- 折线图 (Line Chart) - 趋势、异常检测
- 柱状图 (Bar Chart) - 排序、对比
- 热力图 (Heatmap) - 模式识别
- 平行坐标图 (Parallel Coordinates) - 多维分析
- 桑基图 (Sankey Diagram) - 流量追踪

## 工具系统

### 感知工具 (Perception)
- `get_data_summary` - 获取数据统计
- `get_tooltip_data` - 查询特定位置

### 操作工具 (Action)
- `zoom` - 缩放区域
- `filter` - 数据筛选
- `brush` - 区域选择
- `highlight` - 高亮显示
- `change_encoding` - 修改编码

### 分析工具 (Analysis)
- `identify_clusters` - 聚类识别
- `calculate_correlation` - 相关性计算
- `detect_anomalies` - 异常检测

完整工具列表见 `tools/` 目录

## 评估与对比

### 运行基准测试

```bash
# 使用本系统（带工具+提示词）
python run_benchmark.py

# 对比：纯VLM baseline（无工具）
python run_static_baseline.py

# 对比：其他VLM + 工具（无定制提示词）
python examples/generic_vlm_usage.py
```

### 评估指标

- 准确性：答案正确率
- 效率：工具调用次数
- 完整性：分析深度

结果保存在 `benchmark/results/`

## 项目结构

```
visual-analysis-system/
├── tools/                  # 工具库
│   ├── common.py          # 通用工具
│   ├── *_tools.py         # 专用工具
│   ├── tool_registry.py   # 工具注册
│   ├── tool_executor.py   # 工具执行
│   └── vlm_adapter.py     # VLM适配器 [NEW]
│
├── core/                   # 核心逻辑
│   ├── vlm_service.py     # VLM调用
│   ├── vega_service.py    # 图表渲染
│   └── modes/             # 分析模式
│
├── prompts/               # 提示词库
│   ├── base/             # 基础提示词
│   ├── chart_specific/   # 图表专用
│   └── modes/            # 模式提示词
│
├── benchmark/             # 基准测试
│   ├── tasks/            # 测试任务
│   └── evaluator.py      # 评估器
│
├── examples/              # 使用示例 [NEW]
│   └── generic_vlm_usage.py  # 通用VLM示例
│
└── main.py               # 主入口
```

## 关键代码示例

### 工具调用流程

```python
from tools.tool_executor import get_tool_executor

executor = get_tool_executor()

# 执行工具
result = executor.execute(
    tool_name="identify_clusters",
    params={
        "vega_spec": vega_spec,
        "n_clusters": 3
    }
)

# 检查结果
if result['success']:
    updated_spec = result['vega_spec']
    cluster_info = result['cluster_labels']
```

### VLM调用流程

```python
from core.vlm_service import get_vlm_service

vlm = get_vlm_service()

# 调用VLM
response = vlm.call_with_image(
    text="分析这个散点图",
    image_base64=chart_image,
    system_prompt=system_prompt,
    expect_json=True
)

# 解析工具调用
if response['success']:
    tool_calls = response['parsed_json']
```

## 让其他VLM使用工具

### 方法1: Function Calling (推荐)

适用于支持function calling的VLM（GPT-4, Claude等）

```python
from tools.vlm_adapter import vlm_adapter

# 获取OpenAI格式
tools = vlm_adapter.to_openai_format(chart_type)

# 或Anthropic格式
tools = vlm_adapter.to_anthropic_format(chart_type)

# 传递给VLM API
response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=messages,
    tools=tools
)
```

### 方法2: 提示词描述

适用于不支持function calling的VLM

```python
# 生成工具描述提示词
tools_prompt = vlm_adapter.to_prompt_string(chart_type)

# 添加到system prompt
system_prompt = f"{base_prompt}\n\n{tools_prompt}"

# VLM会以JSON格式返回工具调用
response = vlm.generate(system_prompt + user_query)

# 解析并执行
tool_calls = parse_tool_calls(response)
for call in tool_calls:
    result = executor.execute(call['tool'], call['params'])
```

### 方法3: 作为评估对比

```python
# 1. 本系统: VLM + 工具 + 优化提示词
system_result = system.query(session_id, query)

# 2. 对比1: 纯VLM（无工具）
baseline_result = vlm.call_with_image(query, image)

# 3. 对比2: 其他VLM + 工具（无优化提示词）
generic_analyzer = GenericVLMVisualAnalyzer()
other_vlm_result = other_vlm.call(
    query, 
    tools=generic_analyzer.get_tools_for_openai()
)

# 比较三者的准确性和效率
```

详细示例见 `examples/generic_vlm_usage.py`

## 配置说明

### 环境变量 (.env)

```bash
# VLM API配置
DASHSCOPE_API_KEY=your_api_key
VLM_MODEL=qwen-vl-plus

# 系统参数
MAX_ITERATIONS=10
LOG_LEVEL=INFO
```

### 图表渲染

支持两种方式：

1. **vl-convert-python** (推荐，无需Node.js)
```bash
pip install vl-convert-python
```

2. **vega-cli** (需要Node.js)
```bash
npm install -g vega vega-lite vega-cli canvas
```

## 开发指南

### 添加新工具

1. 在 `tools/*_tools.py` 实现工具函数
2. 在 `tools/tool_registry.py` 注册
3. 更新提示词文档

```python
def new_tool(vega_spec: dict, param1: str) -> dict:
    """工具描述"""
    # 实现逻辑
    return {
        'success': True,
        'vega_spec': updated_spec,
        'result': analysis_result
    }
```

### 添加新VLM支持

1. 在 `tools/vlm_adapter.py` 添加格式转换方法
2. 在 `examples/` 添加使用示例
3. 更新文档

## 故障排查

### 常见问题

1. **工具调用失败**
   - 检查 `vega_spec` 格式是否正确
   - 确认参数类型匹配

2. **VLM无响应**
   - 验证API密钥
   - 检查网络连接
   - 查看日志 `logs/error.log`

3. **图表渲染失败**
   - 安装 `vl-convert-python` 或 `vega-cli`
   - 检查Vega规范有效性

## 引用

如果使用本系统，请引用：

```bibtex
@software{vlm_visual_analysis,
  title={VLM Visual Analysis System},
  author={Your Team},
  year={2024}
}
```

## 许可证

MIT License

## 联系方式

- Issues: [GitHub Issues]
- Email: your-email@example.com
