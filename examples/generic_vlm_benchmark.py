"""
通用VLM评估对比脚本
用于对比不同VLM在使用相同工具时的表现
"""

import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.vlm_adapter import vlm_adapter
from tools.tool_executor import get_tool_executor
from benchmark.evaluator import evaluate_result


class GenericVLMBenchmark:
    """通用VLM基准测试"""
    
    def __init__(self, vlm_name: str = "generic"):
        """
        初始化基准测试
        
        Args:
            vlm_name: VLM名称，用于标识结果
        """
        self.vlm_name = vlm_name
        self.executor = get_tool_executor()
        self.results = []
    
    def load_task(self, task_path: str) -> Dict[str, Any]:
        """加载测试任务"""
        with open(task_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def prepare_tools_for_vlm(self, vlm_type: str, chart_type=None) -> Any:
        """
        为指定VLM准备工具定义
        
        Args:
            vlm_type: VLM类型 ('openai', 'anthropic', 'prompt')
            chart_type: 图表类型（可选）
            
        Returns:
            对应格式的工具定义
        """
        if vlm_type == 'openai':
            return vlm_adapter.to_openai_format(chart_type)
        elif vlm_type == 'anthropic':
            return vlm_adapter.to_anthropic_format(chart_type)
        elif vlm_type == 'prompt':
            return vlm_adapter.to_prompt_string(chart_type)
        else:
            raise ValueError(f"Unknown VLM type: {vlm_type}")
    
    def run_task_with_generic_vlm(
        self,
        task: Dict[str, Any],
        vlm_call_function,
        vlm_type: str = 'openai'
    ) -> Dict[str, Any]:
        """
        使用通用VLM运行任务
        
        Args:
            task: 任务定义
            vlm_call_function: VLM调用函数
            vlm_type: VLM类型
            
        Returns:
            任务执行结果
        """
        # 准备工具
        tools = self.prepare_tools_for_vlm(vlm_type, task.get('chart_type'))
        
        # 构建初始消息
        query = task['query']
        vega_spec = task['vega_spec']
        
        # 调用VLM（需要用户实现具体的调用逻辑）
        response = vlm_call_function(
            query=query,
            vega_spec=vega_spec,
            tools=tools
        )
        
        # 解析工具调用
        tool_calls = self._parse_tool_calls(response, vlm_type)
        
        # 执行工具
        execution_results = []
        current_spec = vega_spec
        
        for tool_call in tool_calls:
            tool_name = tool_call['tool']
            params = tool_call['params']
            params['vega_spec'] = current_spec
            
            result = self.executor.execute(tool_name, params)
            execution_results.append({
                'tool': tool_name,
                'success': result.get('success', False),
                'result': result
            })
            
            if result.get('success') and 'vega_spec' in result:
                current_spec = result['vega_spec']
        
        # 组装结果
        return {
            'task_id': task.get('task_id'),
            'vlm_name': self.vlm_name,
            'query': query,
            'tool_calls': tool_calls,
            'execution_results': execution_results,
            'final_response': response.get('final_answer', ''),
            'metadata': {
                'num_tool_calls': len(tool_calls),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _parse_tool_calls(self, response: Dict[str, Any], vlm_type: str) -> List[Dict]:
        """解析VLM响应中的工具调用"""
        tool_calls = []
        
        if vlm_type == 'openai':
            # OpenAI格式
            if 'tool_calls' in response:
                for call in response['tool_calls']:
                    tool_calls.append({
                        'tool': call['function']['name'],
                        'params': json.loads(call['function']['arguments'])
                    })
        
        elif vlm_type == 'anthropic':
            # Anthropic格式
            if 'content' in response:
                for content in response['content']:
                    if content.get('type') == 'tool_use':
                        tool_calls.append({
                            'tool': content['name'],
                            'params': content['input']
                        })
        
        elif vlm_type == 'prompt':
            # 从文本中提取JSON
            text = response.get('text', '')
            import re
            json_blocks = re.findall(r'```json\n(.*?)\n```', text, re.DOTALL)
            
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and 'tool' in data:
                        tool_calls.append(data)
                except json.JSONDecodeError:
                    continue
        
        return tool_calls
    
    def evaluate_result(self, result: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict:
        """评估结果"""
        return evaluate_result(result, ground_truth)
    
    def save_results(self, output_path: str):
        """保存结果"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'vlm_name': self.vlm_name,
                'results': self.results,
                'summary': self._compute_summary()
            }, f, indent=2, ensure_ascii=False)
    
    def _compute_summary(self) -> Dict:
        """计算总结统计"""
        if not self.results:
            return {}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('evaluation', {}).get('passed', False))
        
        total_tools = sum(r['metadata']['num_tool_calls'] for r in self.results)
        avg_tools = total_tools / total if total > 0 else 0
        
        return {
            'total_tasks': total,
            'successful_tasks': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_tool_calls_per_task': avg_tools
        }


# ============================================================================
# 使用示例
# ============================================================================

def example_openai_evaluation():
    """示例：使用OpenAI GPT-4V进行评估"""
    
    print("=" * 60)
    print("示例：OpenAI GPT-4V 评估")
    print("=" * 60)
    
    benchmark = GenericVLMBenchmark(vlm_name="gpt-4v")
    
    # 模拟VLM调用函数（实际使用时需要实现）
    def mock_openai_call(query, vega_spec, tools):
        """模拟OpenAI API调用"""
        # 实际实现：
        # from openai import OpenAI
        # client = OpenAI(api_key="...")
        # response = client.chat.completions.create(
        #     model="gpt-4-vision-preview",
        #     messages=[...],
        #     tools=tools
        # )
        # return response
        
        return {
            'tool_calls': [
                {
                    'function': {
                        'name': 'get_data_summary',
                        'arguments': json.dumps({'vega_spec': vega_spec, 'scope': 'all'})
                    }
                }
            ],
            'final_answer': '模拟回答'
        }
    
    # 加载任务
    task = {
        'task_id': 'test_001',
        'chart_type': 'scatter_plot',
        'vega_spec': {'data': {'values': []}, 'mark': 'point'},
        'query': '分析这个散点图',
        'ground_truth': {'expected_tools': ['get_data_summary']}
    }
    
    # 运行任务
    result = benchmark.run_task_with_generic_vlm(
        task=task,
        vlm_call_function=mock_openai_call,
        vlm_type='openai'
    )
    
    print(f"\n✓ 任务完成")
    print(f"  工具调用次数: {result['metadata']['num_tool_calls']}")
    print(f"  执行结果: {len(result['execution_results'])} 个工具")
    
    benchmark.results.append(result)
    
    # 保存结果
    output_path = 'benchmark/results/gpt4v_generic_evaluation.json'
    benchmark.save_results(output_path)
    print(f"\n✓ 结果已保存到: {output_path}")


def example_comparison_workflow():
    """示例：完整对比工作流"""
    
    print("\n" + "=" * 60)
    print("完整对比工作流")
    print("=" * 60)
    
    # 对比三种方案：
    # 1. 本系统（VLM + 工具 + 优化提示词）
    # 2. 其他VLM + 工具（无优化提示词）
    # 3. 纯VLM baseline（无工具）
    
    print("\n方案1: 本系统")
    print("  - 特定VLM（如qwen-vl-plus）")
    print("  - 完整工具库")
    print("  - 优化的提示词")
    print("  → 运行: python run_benchmark.py")
    
    print("\n方案2: 其他VLM + 通用工具")
    print("  - 任意VLM（GPT-4V/Claude/Gemini）")
    print("  - 相同工具库")
    print("  - 通用工具描述（无优化）")
    print("  → 使用本脚本实现")
    
    print("\n方案3: 纯VLM baseline")
    print("  - 任意VLM")
    print("  - 无工具支持")
    print("  - 仅图像+查询")
    print("  → 运行: python run_static_baseline.py")
    
    print("\n对比维度:")
    print("  ✓ 准确性: 答案正确率")
    print("  ✓ 效率: 工具调用次数")
    print("  ✓ 完整性: 分析深度")
    
    print("\n实现步骤:")
    print("  1. 准备相同的测试任务集")
    print("  2. 分别运行三种方案")
    print("  3. 收集和对比结果")
    print("  4. 生成对比报告")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("通用VLM评估对比系统")
    print("=" * 60)
    
    # 运行示例
    example_openai_evaluation()
    example_comparison_workflow()
    
    print("\n" + "=" * 60)
    print("使用说明")
    print("=" * 60)
    print("\n要让其他VLM使用这些工具进行评估对比:")
    print("\n1. 实现VLM调用函数")
    print("   def your_vlm_call(query, vega_spec, tools):")
    print("       # 调用你的VLM API")
    print("       # 返回包含工具调用的响应")
    print("\n2. 创建基准测试实例")
    print("   benchmark = GenericVLMBenchmark(vlm_name='your-vlm')")
    print("\n3. 运行测试任务")
    print("   result = benchmark.run_task_with_generic_vlm(")
    print("       task=task,")
    print("       vlm_call_function=your_vlm_call,")
    print("       vlm_type='openai'  # or 'anthropic' or 'prompt'")
    print("   )")
    print("\n4. 保存和对比结果")
    print("   benchmark.save_results('results/your-vlm.json')")
    print("\n详细示例见代码注释部分。")


if __name__ == "__main__":
    main()
