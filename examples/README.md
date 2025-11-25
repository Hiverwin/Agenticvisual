# 使用示例

本目录包含如何让其他VLM使用可视化分析工具的示例代码。

## 文件说明

### generic_vlm_usage.py
展示如何接入不同的VLM使用工具库：
- OpenAI GPT-4V
- Anthropic Claude
- 通用VLM（提示词方式）

**运行方式:**
```bash
python examples/generic_vlm_usage.py
```

### generic_vlm_benchmark.py
展示如何使用通用VLM进行基准测试和评估对比：
- 加载测试任务
- 调用VLM执行分析
- 执行工具调用
- 评估和保存结果

**运行方式:**
```bash
python examples/generic_vlm_benchmark.py
```

## 快速开始

### 1. OpenAI GPT-4V 示例

```python
from openai import OpenAI
from tools.vlm_adapter import vlm_adapter
from tools.tool_executor import get_tool_executor

# 初始化
client = OpenAI(api_key="your-key")
executor = get_tool_executor()

# 获取工具定义
tools = vlm_adapter.to_openai_format()

# 调用GPT-4V
response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "分析这个散点图"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
            ]
        }
    ],
    tools=tools
)

# 执行工具调用
for tool_call in response.choices[0].message.tool_calls:
    result = executor.execute(
        tool_call.function.name,
        json.loads(tool_call.function.arguments)
    )
```

### 2. Anthropic Claude 示例

```python
import anthropic
from tools.vlm_adapter import vlm_adapter

client = anthropic.Anthropic(api_key="your-key")
tools = vlm_adapter.to_anthropic_format()

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    tools=tools,
    messages=[...]
)
```

### 3. 通用VLM（提示词）示例

```python
from tools.vlm_adapter import vlm_adapter

# 生成工具描述
tools_prompt = vlm_adapter.to_prompt_string()

# 添加到system prompt
system_prompt = f"""你是可视化分析助手。

{tools_prompt}
"""

# VLM会返回JSON格式的工具调用
response = your_vlm.generate(system_prompt + user_query)
```

## 评估对比流程

### 对比三种方案

1. **本系统（VLM + 工具 + 优化提示词）**
   ```bash
   python run_benchmark.py
   ```

2. **其他VLM + 通用工具（无优化提示词）**
   ```python
   from examples.generic_vlm_benchmark import GenericVLMBenchmark
   
   benchmark = GenericVLMBenchmark(vlm_name="gpt-4v")
   result = benchmark.run_task_with_generic_vlm(
       task=task,
       vlm_call_function=your_vlm_call,
       vlm_type='openai'
   )
   ```

3. **纯VLM baseline（无工具）**
   ```bash
   python run_static_baseline.py
   ```

### 对比指标

- **准确性**: 答案正确率
- **效率**: 工具调用次数
- **完整性**: 分析深度和覆盖面

## 常见VLM API配置

### OpenAI
```python
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

### Anthropic
```python
import anthropic
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
```

### Google Gemini
```python
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
```

## 工具格式转换

```python
from tools.vlm_adapter import vlm_adapter

# OpenAI格式
openai_tools = vlm_adapter.to_openai_format(chart_type)

# Anthropic格式
claude_tools = vlm_adapter.to_anthropic_format(chart_type)

# 通用提示词
prompt_tools = vlm_adapter.to_prompt_string(chart_type)
```

## 注意事项

1. **API密钥**: 确保配置正确的API密钥
2. **工具格式**: 不同VLM的工具格式略有差异
3. **图像格式**: 注意base64编码和URL格式
4. **速率限制**: 注意API调用频率限制
5. **成本控制**: 大规模测试时注意API调用成本

## 故障排查

### 工具调用失败
- 检查工具参数格式
- 验证vega_spec有效性
- 查看错误日志

### VLM响应异常
- 检查API密钥
- 验证消息格式
- 查看API文档

### 评估结果不准确
- 检查ground truth定义
- 验证评估指标
- 对比多个样本

## 更多资源

- 完整文档: `../README.md`
- 工具文档: `../tools/README.md`
- 快速开始: `../QUICKSTART.md`
