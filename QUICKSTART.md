# 快速开始指南

本指南帮助你快速复现和使用VLM可视化分析系统。

## 5分钟快速体验

### 步骤1: 安装依赖 (1分钟)

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如遇到权限问题
pip install -r requirements.txt --break-system-packages
```

### 步骤2: 配置API密钥 (1分钟)

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
# DASHSCOPE_API_KEY=sk-your-api-key-here
```

获取API密钥: https://dashscope.console.aliyun.com/

### 步骤3: 运行示例 (3分钟)

**推荐方式（从项目根目录）**：
```bash
# 确保在项目根目录
cd /path/to/visual-analysis-system-modified\ 3

# 方式1: 使用便捷脚本（最简单）
python run_examples.py usage

# 方式2: 使用 -m 选项（推荐）
python -m examples.generic_vlm_usage

# 方式3: 直接运行（已修复路径）
python examples/generic_vlm_usage.py
```

**注意**：如果遇到 `ModuleNotFoundError: No module named 'tools'` 错误，请查看 `IMPORT_FIX.md` 文档了解详细解决方案。

## 核心使用场景

### 场景1: 使用本系统（VLM + 工具 + 优化提示词）

```python
from main import VisualAnalysisSystem

# 初始化
system = VisualAnalysisSystem()

# 加载图表
vega_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"url": "data.json"},
    "mark": "point",
    "encoding": {
        "x": {"field": "x", "type": "quantitative"},
        "y": {"field": "y", "type": "quantitative"}
    }
}

# 分析
session_id = system.initialize_session(vega_spec)
result = system.query(session_id, "这个图表有什么聚类模式？")
print(result['response'])
```

### 场景2: 让其他VLM使用工具

#### OpenAI GPT-4V

```python
from openai import OpenAI
from tools.vlm_adapter import vlm_adapter
from tools.tool_executor import get_tool_executor

# 初始化
client = OpenAI(api_key="your-openai-key")
executor = get_tool_executor()

# 获取工具定义
tools = vlm_adapter.to_openai_format()

# 准备消息（图表+查询）
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "分析这个散点图的聚类"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
        ]
    }
]

# 调用GPT-4V
response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# 执行工具调用
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = executor.execute(
            tool_call.function.name,
            json.loads(tool_call.function.arguments)
        )
        print(result)
```

#### Anthropic Claude

```python
import anthropic
from tools.vlm_adapter import vlm_adapter

client = anthropic.Anthropic(api_key="your-claude-key")
tools = vlm_adapter.to_anthropic_format()

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64
                    }
                },
                {"type": "text", "text": "分析聚类模式"}
            ]
        }
    ]
)

# 处理工具使用
for content in message.content:
    if content.type == "tool_use":
        result = executor.execute(content.name, content.input)
        print(result)
```

#### 通用VLM（不支持function calling）

```python
from tools.vlm_adapter import vlm_adapter

# 生成工具提示词
tools_prompt = vlm_adapter.to_prompt_string()

# 添加到system prompt
system_prompt = f"""你是可视化分析助手。

{tools_prompt}

请根据用户查询选择合适的工具。
"""

# 调用任意VLM
response = your_vlm.generate(
    system=system_prompt,
    user="分析这个散点图",
    image=image_data
)

# VLM会返回JSON格式的工具调用
# {"tool": "identify_clusters", "params": {...}}
```

### 场景3: 对比评估

```bash
# 1. 本系统（VLM + 工具 + 优化提示词）
python run_benchmark.py

# 2. 纯VLM baseline（无工具）
python run_static_baseline.py

# 3. 其他VLM + 通用工具（无优化提示词）
# 修改 examples/generic_vlm_usage.py 中的VLM配置
python examples/generic_vlm_usage.py

# 对比结果
python benchmark/compare_results.py
```

## 目录结构说明

```
visual-analysis-system/
│
├── 📁 tools/              # 工具系统（核心）
│   ├── common.py          # 通用感知/操作工具
│   ├── scatter_plot_tools.py  # 散点图专用工具
│   ├── tool_registry.py   # 工具注册表
│   ├── tool_executor.py   # 工具执行器
│   └── vlm_adapter.py     # VLM适配器（新增）
│
├── 📁 core/               # VLM调用
│   ├── vlm_service.py     # VLM API封装
│   └── vega_service.py    # 图表渲染
│
├── 📁 prompts/            # 提示词库
│   ├── base/              # 基础系统提示词
│   ├── chart_specific/    # 图表专用提示词
│   └── modes/             # 分析模式提示词
│
├── 📁 benchmark/          # 评估系统
│   ├── tasks/             # 测试任务集
│   ├── evaluator.py       # 自动评估
│   └── results/           # 评估结果
│
├── 📁 examples/           # 使用示例（新增）
│   └── generic_vlm_usage.py  # 通用VLM接入示例
│
└── 📄 main.py            # 主程序入口
```

## 工具调用流程

```
用户查询 
  ↓
VLM理解意图
  ↓
选择工具（从tool_registry）
  ↓
执行工具（通过tool_executor）
  ↓
更新图表状态
  ↓
VLM分析结果
  ↓
返回洞察给用户
```

## 关键文件说明

### 1. tools/vlm_adapter.py (新增)
将工具转换为不同VLM的格式：
- `to_openai_format()` - OpenAI function calling
- `to_anthropic_format()` - Claude tool use
- `to_prompt_string()` - 提示词描述（通用）

### 2. tools/tool_registry.py
工具注册表，定义所有可用工具：
- 感知工具：get_data_summary, get_tooltip_data
- 操作工具：zoom, filter, brush, highlight
- 分析工具：identify_clusters, calculate_correlation

### 3. tools/tool_executor.py
工具执行器，负责：
- 参数验证
- 工具调用
- 结果返回
- 执行历史记录

### 4. prompts/
优化的提示词，包含：
- 工具使用指导
- 分析策略
- 输出格式规范

## 数据格式

### 输入：Vega-Lite规范

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"values": [...]},
  "mark": "point",
  "encoding": {
    "x": {"field": "x", "type": "quantitative"},
    "y": {"field": "y", "type": "quantitative"}
  }
}
```

### 输出：工具调用结果

```json
{
  "success": true,
  "vega_spec": {...},        // 更新后的规范
  "image_base64": "...",     // 渲染的图像
  "analysis": {...},         // 分析结果
  "metadata": {...}          // 元数据
}
```

## 常见问题

### Q1: 如何添加新的VLM支持？

在 `tools/vlm_adapter.py` 添加格式转换方法：

```python
def to_your_vlm_format(self, chart_type=None):
    """转换为你的VLM格式"""
    tools = []
    # 实现格式转换逻辑
    return tools
```

### Q2: 工具调用失败怎么办？

1. 检查vega_spec格式
2. 验证参数类型
3. 查看logs/error.log

### Q3: 如何自定义工具？

1. 在 `tools/*_tools.py` 实现函数
2. 在 `tool_registry.py` 注册
3. 更新提示词文档

示例：

```python
# tools/scatter_plot_tools.py
def my_custom_tool(vega_spec: dict, param1: str) -> dict:
    """自定义工具"""
    # 实现逻辑
    return {
        'success': True,
        'vega_spec': updated_spec
    }

# tools/tool_registry.py
scatter_tools = {
    'my_custom_tool': {
        'function': scatter_plot_tools.my_custom_tool,
        'category': 'analysis',
        'description': '自定义分析',
        'params': {...}
    }
}
```

### Q4: 如何运行评估？

```bash
# 准备测试数据
cd benchmark/tasks
# 确保有测试任务JSON文件

# 运行评估
python run_benchmark.py

# 查看结果
cat benchmark/results/evaluation_results.json
```

## 下一步

1. ✅ 阅读完整README: `README.md`
2. ✅ 查看工具文档: `tools/README.md`
3. ✅ 运行示例代码: `examples/`
4. ✅ 尝试自己的数据和查询
5. ✅ 参与开发和改进

## 获取帮助

- 📖 完整文档: `README.md`
- 💬 Issues: [GitHub Issues]
- 📧 Email: your-email@example.com
