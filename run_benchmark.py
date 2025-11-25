"""
Benchmark运行脚本
加载任务 → 执行系统 → 评估打分
"""

import json
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from benchmark.evaluator import BenchmarkEvaluator, format_evaluation_report
from core.session_manager import SessionManager
from core.vega_service import get_vega_service
from core.modes.autonomous_exploration_mode import AutonomousExplorationMode


def load_benchmark_task(task_path: str) -> dict:
    """加载benchmark任务"""
    with open(task_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_vega_spec(spec_path: str) -> dict:
    """加载Vega-Lite spec"""
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_benchmark_task(task_data: dict) -> dict:
    """执行benchmark任务"""
    print(f"\n🚀 开始执行任务: {task_data['task_id']}")
    print(f"   查询: {task_data['task']['query']}")
    print()
    
    # 加载Vega spec
    spec_path = task_data['task']['initial_visualization']['vega_spec_path']
    vega_spec = load_vega_spec(spec_path)
    
    # 初始化服务
    vega_service = get_vega_service()
    session_mgr = SessionManager()
    
    # 渲染初始视图
    render_result = vega_service.render(vega_spec)
    if not render_result.get('success'):
        print(f"❌ 渲染失败: {render_result.get('error')}")
        return None
    
    image_base64 = render_result['image_base64']
    
    # 创建session
    chart_type = task_data['metadata']['chart_type']
    session_id = session_mgr.create_session(vega_spec, chart_type)
    session = session_mgr.get_session(session_id)
    
    # 执行autonomous exploration
    mode = AutonomousExplorationMode()
    user_query = task_data['task']['query']
    
    context = session.get('context', {})
    
    result = mode.execute(
        user_query=user_query,
        vega_spec=vega_spec,
        image_base64=image_base64,
        chart_type=chart_type,
        context=context
    )
    
    print(f"✅ 任务执行完成")
    print(f"   - 探索轮次: {result.get('total_iterations', 0)}")
    print(f"   - 模式: {result.get('mode', 'unknown')}")
    print()
    
    return result


def evaluate_result(task_data: dict, agent_result: dict) -> dict:
    """评估结果"""
    print("📊 开始评估...")
    
    ground_truth = task_data['ground_truth']
    evaluator = BenchmarkEvaluator(ground_truth)
    
    eval_result = evaluator.evaluate(agent_result)
    
    return eval_result


def save_results(task_id: str, agent_result: dict, eval_result: dict):
    """保存结果"""
    output_dir = Path("benchmark/results")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 保存agent结果
    agent_file = output_dir / f"{task_id}_agent_result.json"
    with open(agent_file, 'w', encoding='utf-8') as f:
        json.dump(agent_result, f, ensure_ascii=False, indent=2)
    
    # 保存评估结果
    eval_file = output_dir / f"{task_id}_evaluation.json"
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(eval_result, f, ensure_ascii=False, indent=2)
    
    print(f"💾 结果已保存到: {output_dir}/")


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 Interactive VA Benchmark - 轻量版")
    print("=" * 60)
    
    # 加载任务
    task_path = "benchmark/tasks/scatter_clustering_001.json"
    print(f"\n📂 加载任务: {task_path}")
    
    try:
        task_data = load_benchmark_task(task_path)
        print(f"✅ 任务加载成功")
        print(f"   - 任务ID: {task_data['task_id']}")
        print(f"   - 难度: {task_data['metadata']['difficulty']}")
        print(f"   - 交互必要性: {task_data['metadata']['interaction_necessity']}")
    except Exception as e:
        print(f"❌ 任务加载失败: {e}")
        return
    
    # 执行任务
    try:
        agent_result = run_benchmark_task(task_data)
        if not agent_result:
            print("❌ 任务执行失败")
            return
    except Exception as e:
        print(f"❌ 任务执行出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 评估结果
    try:
        eval_result = evaluate_result(task_data, agent_result)
        
        # 打印评估报告
        report = format_evaluation_report(eval_result, task_data['task_id'])
        print("\n" + report)
        
        # 保存结果
        save_results(task_data['task_id'], agent_result, eval_result)
        
    except Exception as e:
        print(f"❌ 评估出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✨ Benchmark运行完成！")


if __name__ == "__main__":
    main()

