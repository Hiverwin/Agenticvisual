"""
静态VLM Baseline测试
直接使用DashScope API标准形式调用qwen-vl-plus，简单分析图表
"""

import json
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# 导入DashScope
try:
    import dashscope
    from dashscope import MultiModalConversation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("❌ 错误: 未安装dashscope库")
    print("   请运行: pip install dashscope")
    sys.exit(1)

from core.vega_service import get_vega_service


def load_benchmark_task(task_path: str) -> dict:
    """加载benchmark任务"""
    task_file = Path(task_path)
    if not task_file.exists():
        print(f"❌ 错误: 文件不存在: {task_path}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_vega_spec(spec_path: str) -> dict:
    """加载Vega-Lite spec"""
    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"❌ 错误: Vega spec文件不存在: {spec_path}")
        sys.exit(1)
    
    with open(spec_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_static_baseline(task_data: dict) -> dict:
    """运行静态baseline分析（直接调用DashScope API）"""
    print("=" * 60)
    print("🔬 静态VLM Baseline测试")
    print("=" * 60)
    print()
    print(f"任务ID: {task_data['task_id']}")
    print(f"模式: 静态分析（无交互）")
    print()
    
    # 检查API Key
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("❌ 错误: 未设置DASHSCOPE_API_KEY环境变量")
        sys.exit(1)
    
    dashscope.api_key = api_key
    
    # 加载Vega spec并渲染
    spec_path = task_data['task']['initial_visualization']['vega_spec_path']
    vega_spec = load_vega_spec(spec_path)
    
    vega_service = get_vega_service()
    render_result = vega_service.render(vega_spec)
    
    if not render_result.get('success'):
        print(f"❌ 渲染失败: {render_result.get('error')}")
        return None
    
    image_base64 = render_result['image_base64']
    user_query = task_data['task']['query']
    
    print(f"📊 初始视图已渲染")
    print(f"❓ 查询: {user_query}")
    print()
    
    # 直接使用DashScope API标准形式调用
    print("🤖 正在调用DashScope API (qwen-vl-plus)...")
    
    try:
        response = MultiModalConversation.call(
            model='qwen-vl-plus',
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": user_query},
                        {"image": f"data:image/png;base64,{image_base64}"}
                    ]
                }
            ]
        )
        
        if response.status_code == 200:
            vlm_output = response.output.choices[0].message.content[0]["text"]
            print("✅ API调用成功")
            
            print()
            print("=" * 60)
            print("VLM输出:")
            print("=" * 60)
            print(vlm_output[:500] + "..." if len(vlm_output) > 500 else vlm_output)
            print("=" * 60)
            print()
            
            # 构建结果格式（保持兼容性，用于后续评估）
            result = {
                "session_id": f"static_baseline_{task_data['task_id']}",
                "timestamp": datetime.now().isoformat(),
                "mode": "static_vlm_baseline",
                "total_iterations": 1,
                "explorations": [
                    {
                        "iteration": 1,
                        "success": True,
                        "timestamp": 0,
                        "vlm_raw_output": vlm_output,
                        "images": [image_base64],
                        "analysis_summary": {
                            "key_insights": [],  # 简化：不解析，保持空列表
                            "patterns_found": [],
                            "anomalies": [],
                            "recommendations": []
                        },
                        "tool_execution": None,
                        "duration": 0
                    }
                ]
            }
            
            return result
        else:
            print(f"❌ API调用失败: status={response.status_code}, message={response.message}")
            return None
            
    except Exception as e:
        print(f"❌ API调用异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def save_result(task_id: str, result: dict):
    """保存结果"""
    output_dir = Path("benchmark/results")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_file = output_dir / f"{task_id}_static_baseline.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"💾 结果已保存到: {output_file}")
    return output_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='运行静态VLM baseline测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_static_baseline.py benchmark/tasks/scatter_clustering_001.json
  python run_static_baseline.py benchmark/tasks/cars_multivariate_002.json
        """
    )
    parser.add_argument(
        'benchmark_path',
        help='benchmark任务JSON文件路径'
    )
    
    args = parser.parse_args()
    
    print("\n📂 加载任务...")
    task_data = load_benchmark_task(args.benchmark_path)
    
    print("🚀 开始静态VLM分析...\n")
    result = run_static_baseline(task_data)
    
    if result:
        output_file = save_result(task_data['task_id'], result)
        
        print("\n✨ 静态baseline测试完成！")
        print(f"\n下一步: 运行评估器评估结果")
        print(f"   python test_benchmark.py {output_file}")
    else:
        print("\n❌ 静态baseline测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
