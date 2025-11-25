"""
通用VLM工具适配器
支持将工具转换为标准的function calling格式，使任何支持function calling的VLM都能使用
"""

from typing import Dict, List, Any, Optional
from .tool_registry import tool_registry
from config.chart_types import ChartType


class VLMToolAdapter:
    """VLM工具适配器，支持多种格式"""
    
    def __init__(self):
        self.registry = tool_registry
    
    def to_openai_format(self, chart_type: Optional[ChartType] = None) -> List[Dict[str, Any]]:
        """
        转换为OpenAI function calling格式
        
        Args:
            chart_type: 图表类型，如果指定则只返回该类型的工具
            
        Returns:
            OpenAI格式的工具列表
        """
        tools = []
        
        # 获取工具列表
        if chart_type:
            tool_names = self.registry.list_tools_for_chart(chart_type)
        else:
            tool_names = self.registry.list_all_tools()
        
        for tool_name in tool_names:
            tool_info = self.registry.get_tool(tool_name)
            if not tool_info:
                continue
            
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info['description'],
                    "parameters": self._convert_params_to_json_schema(tool_info['params'])
                }
            }
            tools.append(openai_tool)
        
        return tools
    
    def to_anthropic_format(self, chart_type: Optional[ChartType] = None) -> List[Dict[str, Any]]:
        """
        转换为Anthropic (Claude) tool use格式
        
        Args:
            chart_type: 图表类型
            
        Returns:
            Anthropic格式的工具列表
        """
        tools = []
        
        # 获取工具列表
        if chart_type:
            tool_names = self.registry.list_tools_for_chart(chart_type)
        else:
            tool_names = self.registry.list_all_tools()
        
        for tool_name in tool_names:
            tool_info = self.registry.get_tool(tool_name)
            if not tool_info:
                continue
            
            anthropic_tool = {
                "name": tool_name,
                "description": tool_info['description'],
                "input_schema": self._convert_params_to_json_schema(tool_info['params'])
            }
            tools.append(anthropic_tool)
        
        return tools
    
    def to_generic_format(self, chart_type: Optional[ChartType] = None) -> List[Dict[str, Any]]:
        """
        转换为通用格式（可用于提示词描述）
        
        Args:
            chart_type: 图表类型
            
        Returns:
            通用格式的工具列表
        """
        tools = []
        
        # 获取工具列表
        if chart_type:
            tool_names = self.registry.list_tools_for_chart(chart_type)
        else:
            tool_names = self.registry.list_all_tools()
        
        for tool_name in tool_names:
            tool_info = self.registry.get_tool(tool_name)
            if not tool_info:
                continue
            
            # 构建参数描述
            params_desc = []
            for param_name, param_spec in tool_info['params'].items():
                param_type = param_spec.get('type', 'any')
                required = param_spec.get('required', False)
                default = param_spec.get('default', 'N/A')
                
                param_str = f"  - {param_name} ({param_type})"
                if required:
                    param_str += " [REQUIRED]"
                elif default != 'N/A':
                    param_str += f" [default={default}]"
                
                params_desc.append(param_str)
            
            tool_desc = {
                "name": tool_name,
                "category": tool_info.get('category', 'unknown'),
                "description": tool_info['description'],
                "parameters": "\n".join(params_desc) if params_desc else "No parameters"
            }
            tools.append(tool_desc)
        
        return tools
    
    def to_prompt_string(self, chart_type: Optional[ChartType] = None) -> str:
        """
        转换为提示词字符串格式（用于不支持function calling的VLM）
        
        Args:
            chart_type: 图表类型
            
        Returns:
            格式化的工具描述字符串
        """
        tools = self.to_generic_format(chart_type)
        
        prompt_parts = ["# Available Tools\n"]
        
        # 按类别分组
        categories = {}
        for tool in tools:
            cat = tool['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        # 生成提示词
        for category, cat_tools in categories.items():
            prompt_parts.append(f"\n## {category.upper()} Tools\n")
            
            for tool in cat_tools:
                prompt_parts.append(f"\n### {tool['name']}")
                prompt_parts.append(f"\n{tool['description']}")
                prompt_parts.append(f"\n**Parameters:**\n{tool['parameters']}\n")
        
        prompt_parts.append("\n## Tool Usage Format\n")
        prompt_parts.append("To use a tool, respond with JSON in this format:\n")
        prompt_parts.append("```json\n")
        prompt_parts.append('{\n')
        prompt_parts.append('  "tool": "tool_name",\n')
        prompt_parts.append('  "params": {\n')
        prompt_parts.append('    "vega_spec": {...},\n')
        prompt_parts.append('    "param1": "value1",\n')
        prompt_parts.append('    "param2": "value2"\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "reason": "Why you are calling this tool"\n')
        prompt_parts.append('}\n')
        prompt_parts.append("```\n")
        
        return "".join(prompt_parts)
    
    def _convert_params_to_json_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """将参数规范转换为JSON Schema格式"""
        properties = {}
        required = []
        
        for param_name, param_spec in params.items():
            param_type = param_spec.get('type', 'string')
            
            # 类型映射
            type_mapping = {
                'str': 'string',
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean',
                'list': 'array',
                'dict': 'object',
                'tuple': 'array',
                'any': 'string'  # 默认为string
            }
            
            json_type = type_mapping.get(param_type, 'string')
            
            properties[param_name] = {
                "type": json_type,
                "description": f"Parameter {param_name} of type {param_type}"
            }
            
            # 添加默认值
            if 'default' in param_spec:
                properties[param_name]['default'] = param_spec['default']
            
            # 收集必需参数
            if param_spec.get('required', False):
                required.append(param_name)
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
        
        return schema
    
    def generate_tool_execution_guide(self) -> str:
        """生成工具执行指南"""
        guide = """
# Tool Execution Guide

## Overview
This system provides interactive tools for visual analysis. All tools operate on Vega-Lite specifications.

## Core Principles

1. **All tools require vega_spec**: Every tool call must include the current vega_spec as a parameter
2. **Tools return updated state**: Action tools return an updated vega_spec and rendered image
3. **Tools are composable**: You can chain multiple tool calls in sequence

## Tool Categories

### Perception Tools
These tools READ the current state:
- `get_data_summary`: Get statistical summary of data
- `get_tooltip_data`: Get data at specific position

### Action Tools  
These tools MODIFY the visualization:
- `zoom`: Zoom to a specific area
- `filter`: Filter data by dimension
- `brush`: Select/brush an area
- `change_encoding`: Change visual encoding
- `highlight`: Highlight specific categories
- `render_chart`: Render the visualization

### Analysis Tools
These tools ANALYZE patterns:
- `identify_clusters`: Find clusters in scatter plots
- `calculate_correlation`: Calculate correlation
- `detect_anomalies`: Detect anomalies in time series

## Usage Pattern

1. **Understand the task**: Parse user query
2. **Plan tool usage**: Decide which tools to use
3. **Execute tools**: Call tools with proper parameters
4. **Interpret results**: Analyze tool outputs
5. **Respond to user**: Provide insights based on results

## Example Workflow

```python
# 1. Get data summary to understand the data
result = get_data_summary(vega_spec=current_spec, scope='all')

# 2. Identify interesting patterns
clusters = identify_clusters(vega_spec=current_spec, n_clusters=3)

# 3. Highlight findings
updated = highlight(vega_spec=current_spec, category=clusters['labels'][0])

# 4. Return insights to user
```

## Error Handling

- Always check tool result['success']
- If a tool fails, try alternative approaches
- Validate parameters before calling tools
"""
        return guide


# 创建全局实例
vlm_adapter = VLMToolAdapter()
