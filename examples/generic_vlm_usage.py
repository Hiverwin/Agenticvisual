"""
通用VLM使用示例
演示如何让任意VLM（OpenAI GPT-4V, Claude, Gemini等）使用可视化分析工具
"""

import json
import sys
import os
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.vlm_adapter import vlm_adapter
from tools.tool_executor import get_tool_executor
from config.chart_types import ChartType


class GenericVLMVisualAnalyzer:
    """
    通用VLM可视化分析器
    可以接入任何支持function calling或提示词的VLM
    """
    
    def __init__(self, chart_type: ChartType = None):
        """
        初始化分析器
        
        Args:
            chart_type: 图表类型（可选，用于限定工具范围）
        """
        self.adapter = vlm_adapter
        self.executor = get_tool_executor()
        self.chart_type = chart_type
        self.conversation_history = []
    
    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """
        获取OpenAI格式的工具定义
        适用于: GPT-4, GPT-4V, GPT-4-turbo等
        """
        return self.adapter.to_openai_format(self.chart_type)
    
    def get_tools_for_anthropic(self) -> List[Dict[str, Any]]:
        """
        获取Anthropic格式的工具定义
        适用于: Claude 3 Opus, Sonnet, Haiku等
        """
        return self.adapter.to_anthropic_format(self.chart_type)
    
    def get_tools_as_prompt(self) -> str:
        """
        获取提示词格式的工具说明
        适用于: 不支持function calling的VLM
        """
        return self.adapter.to_prompt_string(self.chart_type)
    
    def execute_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            params: 工具参数（必须包含vega_spec）
            
        Returns:
            工具执行结果
        """
        result = self.executor.execute(tool_name, params)
        return result
    
    def parse_tool_calls_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        从VLM响应中解析工具调用
        支持JSON和代码块格式
        
        Args:
            response_text: VLM的文本响应
            
        Returns:
            解析出的工具调用列表
        """
        tool_calls = []
        
        # 尝试提取JSON代码块
        import re
        json_blocks = re.findall(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict) and 'tool' in data:
                    tool_calls.append(data)
                elif isinstance(data, list):
                    tool_calls.extend([item for item in data if isinstance(item, dict) and 'tool' in item])
            except json.JSONDecodeError:
                continue
        
        return tool_calls


# ============================================================================
# 使用示例 1: OpenAI GPT-4V
# ============================================================================

def example_openai_gpt4v():
    """
    示例: 使用OpenAI GPT-4V进行可视化分析
    """
    print("=" * 60)
    print("示例 1: OpenAI GPT-4V")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = GenericVLMVisualAnalyzer(chart_type=ChartType.SCATTER_PLOT)
    
    # 获取工具定义（OpenAI格式）
    tools = analyzer.get_tools_for_openai()
    
    print("\n✓ 已生成 OpenAI 格式的工具定义")
    print(f"✓ 可用工具数量: {len(tools)}")
    print(f"✓ 示例工具: {tools[0]['function']['name']}")
    
    # 模拟调用（实际使用时需要OpenAI API）
    """
    from openai import OpenAI
    client = OpenAI(api_key="your-api-key")
    
    # 准备消息
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "分析这个散点图的聚类情况"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
            ]
        }
    ]
    
    # 调用GPT-4V with tools
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    # 处理工具调用
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # 执行工具
            result = analyzer.execute_tool_call(tool_name, tool_args)
            print(f"工具 {tool_name} 执行结果:", result)
    """
    
    print("\n📝 OpenAI 集成代码已在注释中提供")


# ============================================================================
# 使用示例 2: Anthropic Claude
# ============================================================================

def example_anthropic_claude():
    """
    示例: 使用Anthropic Claude进行可视化分析
    """
    print("\n" + "=" * 60)
    print("示例 2: Anthropic Claude")
    print("=" * 60)
    
    analyzer = GenericVLMVisualAnalyzer(chart_type=ChartType.SCATTER_PLOT)
    
    # 获取工具定义（Anthropic格式）
    tools = analyzer.get_tools_for_anthropic()
    
    print("\n✓ 已生成 Anthropic 格式的工具定义")
    print(f"✓ 可用工具数量: {len(tools)}")
    print(f"✓ 示例工具: {tools[0]['name']}")
    
    # 模拟调用（实际使用时需要Anthropic API）
    """
    import anthropic
    client = anthropic.Anthropic(api_key="your-api-key")
    
    # 准备消息
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
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "分析这个散点图，找出聚类模式"
                    }
                ]
            }
        ]
    )
    
    # 处理工具使用
    if message.stop_reason == "tool_use":
        for content in message.content:
            if content.type == "tool_use":
                tool_name = content.name
                tool_input = content.input
                
                # 执行工具
                result = analyzer.execute_tool_call(tool_name, tool_input)
                print(f"工具 {tool_name} 执行结果:", result)
    """
    
    print("\n📝 Anthropic 集成代码已在注释中提供")


# ============================================================================
# 使用示例 3: 通用VLM（使用提示词）
# ============================================================================

def example_generic_vlm_with_prompt():
    """
    示例: 使用不支持function calling的VLM（通过提示词）
    """
    print("\n" + "=" * 60)
    print("示例 3: 通用VLM（提示词方式）")
    print("=" * 60)
    
    analyzer = GenericVLMVisualAnalyzer(chart_type=ChartType.SCATTER_PLOT)
    
    # 获取工具提示词
    tools_prompt = analyzer.get_tools_as_prompt()
    
    print("\n✓ 已生成工具提示词")
    print(f"✓ 提示词长度: {len(tools_prompt)} 字符")
    print("\n前300字符预览:")
    print("-" * 60)
    print(tools_prompt[:300] + "...")
    print("-" * 60)
    
    # 模拟对话
    system_prompt = f"""你是一个可视化分析助手。

{tools_prompt}

当需要使用工具时，请按照上述格式返回JSON。
"""
    
    print("\n📝 将此提示词添加到VLM的system prompt中")
    print("📝 VLM会返回JSON格式的工具调用，然后解析并执行")
    
    # 模拟解析工具调用
    example_response = """
我需要先识别散点图中的聚类。

```json
{
  "tool": "identify_clusters",
  "params": {
    "vega_spec": {...},
    "n_clusters": 3,
    "method": "kmeans"
  },
  "reason": "识别数据中的3个主要聚类模式"
}
```
"""
    
    tool_calls = analyzer.parse_tool_calls_from_response(example_response)
    print(f"\n✓ 成功解析 {len(tool_calls)} 个工具调用")
    if tool_calls:
        print(f"✓ 工具名称: {tool_calls[0]['tool']}")


# ============================================================================
# 完整工作流示例
# ============================================================================

def example_complete_workflow():
    """
    完整的分析工作流示例
    """
    print("\n" + "=" * 60)
    print("示例 4: 完整分析工作流")
    print("=" * 60)
    
    # 1. 加载图表数据
    print("\n步骤 1: 加载Vega-Lite图表")
    vega_spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {
            "values": [
                {"x": 1, "y": 2}, {"x": 2, "y": 4},
                {"x": 3, "y": 6}, {"x": 4, "y": 8}
            ]
        },
        "mark": "point",
        "encoding": {
            "x": {"field": "x", "type": "quantitative"},
            "y": {"field": "y", "type": "quantitative"}
        }
    }
    print("✓ 图表已加载")
    
    # 2. 初始化分析器
    print("\n步骤 2: 初始化分析器")
    analyzer = GenericVLMVisualAnalyzer(chart_type=ChartType.SCATTER_PLOT)
    print("✓ 分析器已初始化")
    
    # 3. 获取工具列表
    print("\n步骤 3: 获取可用工具")
    tools_openai = analyzer.get_tools_for_openai()
    print(f"✓ OpenAI格式工具: {len(tools_openai)} 个")
    
    # 4. 执行分析工具
    print("\n步骤 4: 执行数据摘要工具")
    result = analyzer.execute_tool_call(
        "get_data_summary",
        {"vega_spec": vega_spec, "scope": "all"}
    )
    
    if result['success']:
        print("✓ 工具执行成功")
        print(f"  数据点数量: {result.get('count', 'N/A')}")
        print(f"  统计信息: {list(result.get('summary', {}).keys())}")
    else:
        print(f"✗ 工具执行失败: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("✓ 完整工作流演示完成")
    print("=" * 60)


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("通用VLM可视化分析工具 - 使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_openai_gpt4v()
    example_anthropic_claude()
    example_generic_vlm_with_prompt()
    example_complete_workflow()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)
    print("\n提示:")
    print("1. 查看上述示例代码，了解如何集成不同的VLM")
    print("2. 取消注释相应的API调用代码")
    print("3. 填入你的API密钥")
    print("4. 运行实际的分析任务")
    print("\n详细文档: 请查看 README.md")


if __name__ == "__main__":
    main()
