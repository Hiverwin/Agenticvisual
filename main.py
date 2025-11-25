"""
主程序入口
提供简单的命令行交互接口
"""

import base64
import json
import sys
from pathlib import Path
from datetime import datetime

from config import validate_config
from core import get_session_manager, get_vega_service
from core.utils import app_logger


def save_exploration_result(result: dict, session_id: str):
    """保存探索结果到文件"""
    try:
        # 创建results目录
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exploration_{session_id[:8]}_{timestamp}.json"
        filepath = results_dir / filename
        mode = result.get("mode", "autonomous_exploration")
        records = result.get("explorations") if mode == "autonomous_exploration" else result.get("iterations", [])
        image_dir = results_dir / f"exploration_{session_id[:8]}_{timestamp}_{mode}_images"
        image_dir.mkdir(exist_ok=True)
        
        # 处理每轮图像
        for exp in records:
            view_files = []
            for idx, image_b64 in enumerate(exp.get("images", []), start=1):
                try:
                    image_bytes = base64.b64decode(image_b64.split(",")[-1])
                    iter_num = exp.get("iteration", 0)
                    view_filename = image_dir / f"exploration_{session_id[:8]}_iter{iter_num}_view{idx}.png"
                    with open(view_filename, "wb") as img_f:
                        img_f.write(image_bytes)
                    view_files.append(str(view_filename))
                except Exception as exc:
                    app_logger.error(f"保存视图失败：{exc}", exc_info=True)
            if view_files:
                exp["view_files"] = view_files
        
        # 准备保存的数据
        save_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "mode": result.get("mode"),
            "total_iterations": result.get("total_iterations"),
            "explorations": records,
            "final_report": result.get("final_report")
        }
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"系统> ✅ 探索结果已保存到: {filepath}\n")
        
        # 同时生成一个人类可读的文本报告
        txt_filename = f"exploration_{session_id[:8]}_{timestamp}.txt"
        txt_filepath = results_dir / txt_filename
        
        title = "自主探索模式" if mode == "autonomous_exploration" else "目标导向模式"
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"{title} - 详细报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"会话ID: {session_id}\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总轮次: {result.get('total_iterations', 0)}\n\n")
            
            # 写入每轮探索
            for exp in records:
                f.write("-" * 60 + "\n")
                f.write(f"第 {exp.get('iteration', 0)} 轮探索\n")
                f.write("-" * 60 + "\n\n")
                
                if not exp.get("success"):
                    f.write(f"状态: 失败\n")
                    f.write(f"错误: {exp.get('error', 'Unknown')}\n\n")
                    continue
                
                f.write(f"状态: 成功\n")
                f.write(f"耗时: {exp.get('duration', 0):.2f}秒\n\n")
                
                # 如果有VLM原始输出，优先展示
                vlm_raw = exp.get("vlm_raw_output")
                if vlm_raw:
                    f.write("=" * 50 + "\n")
                    f.write("VLM完整思考过程:\n")
                    f.write("=" * 50 + "\n")
                    f.write(vlm_raw)
                    f.write("\n" + "=" * 50 + "\n\n")
                
                # 写入工具调用
                tool_exec = exp.get("tool_execution")
                if tool_exec:
                    f.write("工具调用:\n")
                    f.write(f"  工具: {tool_exec.get('tool_name', 'Unknown')}\n")
                    f.write(f"  参数: {json.dumps(tool_exec.get('tool_params', {}), ensure_ascii=False)}\n")
                    
                    tool_result = tool_exec.get('tool_result', {})
                    f.write(f"  结果: {'成功' if tool_result.get('success') else '失败'}\n")
                    
                    # 展示工具返回的完整信息
                    if tool_result.get('message'):
                        f.write(f"  消息: {tool_result['message']}\n")
                    if tool_result.get('error'):
                        f.write(f"  错误: {tool_result['error']}\n")
                    
                    # 如果有其他有用的结果字段，也展示出来
                    for key in ['correlation_coefficient', 'cluster_statistics', 'operation']:
                        if key in tool_result:
                            f.write(f"  {key}: {tool_result[key]}\n")
                    f.write("\n")
                
                analysis = exp.get("analysis_summary", {})
                
                # 写入VLM决策解析（从analysis_summary）
                analysis = exp.get("analysis_summary", {})
                if analysis:
                    f.write("VLM决策解析:\n")
                    
                    goal = analysis.get("goal_understanding")
                    if goal:
                        f.write(f"  目标理解: {goal}\n")
                    
                    gap = analysis.get("current_gap")
                    if gap:
                        f.write(f"  当前差距: {gap}\n")
                    
                    plan = analysis.get("action_plan")
                    if plan:
                        f.write(f"  行动计划: {plan}\n")
                    
                    reasoning = analysis.get("reasoning")
                    if reasoning:
                        f.write(f"  推理过程: {reasoning}\n")
                    
                    f.write("\n")
                
                # 写入洞察
                insights = analysis.get("key_insights", [])
                if insights:
                    f.write("关键洞察:\n")
                    for idx, insight in enumerate(insights, 1):
                        f.write(f"  {idx}. {insight}\n")
                    f.write("\n")
                
                # 写入模式
                patterns = analysis.get("patterns_found", [])
                if patterns:
                    f.write("数据模式:\n")
                    for idx, pattern in enumerate(patterns, 1):
                        f.write(f"  {idx}. {pattern}\n")
                    f.write("\n")
                
                # 写入异常
                anomalies = analysis.get("anomalies", [])
                if anomalies:
                    f.write("异常发现:\n")
                    for idx, anomaly in enumerate(anomalies, 1):
                        f.write(f"  {idx}. {anomaly}\n")
                    f.write("\n")
                
                # 写入建议
                recommendations = analysis.get("recommendations", [])
                if recommendations:
                    f.write("分析建议:\n")
                    for idx, rec in enumerate(recommendations, 1):
                        f.write(f"  {idx}. {rec}\n")
                    f.write("\n")

                achievement_analysis = analysis.get("achievement_analysis")
                if achievement_analysis:
                    f.write(f"达成分析: {achievement_analysis}\n\n")

                remaining_gaps = analysis.get("remaining_gaps", [])
                if remaining_gaps:
                    f.write("剩余差距:\n")
                    for gap in remaining_gaps:
                        f.write(f"  - {gap}\n")
                    f.write("\n")

                next_action = analysis.get("next_action")
                if next_action:
                    f.write(f"下一步建议: {next_action}\n\n")
                
                view_files = exp.get("view_files", [])
                if view_files:
                    f.write("视图文件:\n")
                    for path in view_files:
                        f.write(f"  - {path}\n")
                    f.write("\n")
                
                decision = exp.get("decision")
                if decision:
                    f.write("VLM反馈:\n")
                    goal_understanding = decision.get("goal_understanding")
                    if goal_understanding:
                        f.write(f"  目标理解: {goal_understanding}\n")
                    current_gap = decision.get("current_gap")
                    if current_gap:
                        f.write(f"  当前差距: {current_gap}\n")
                    action_plan = decision.get("action_plan") or decision.get("decision", {}).get("action_plan")
                    if action_plan:
                        f.write(f"  行动计划: {action_plan}\n")
                    if decision.get("analysis_insights"):
                        f.write("  关联洞察:\n")
                        for insight in decision.get("analysis_insights", []):
                            f.write(f"    - {insight}\n")
                    f.write("\n")
            
            # 写入总结
            f.write("=" * 60 + "\n")
            f.write("探索总结\n")
            f.write("=" * 60 + "\n\n")
            
            report = result.get("final_report", {})
            f.write(f"总轮次: {report.get('total_iterations', len(records))}\n")
            f.write(f"成功轮次: {report.get('successful_iterations', len(records))}\n")
            f.write(f"摘要: {report.get('summary', '')}\n\n")
            
            all_insights = report.get('all_insights', [])
            if all_insights:
                f.write(f"全部洞察 ({len(all_insights)}条):\n")
                for idx, insight in enumerate(all_insights, 1):
                    f.write(f"  {idx}. {insight}\n")
                f.write("\n")
            
            tools_used = report.get('tools_used', [])
            if tools_used:
                f.write("工具使用统计:\n")
                for tool_info in tools_used:
                    status = "成功" if tool_info.get("success") else "失败"
                    f.write(f"  第{tool_info['iteration']}轮: {tool_info['tool']} ({status})\n")
        
        print(f"系统> ✅ 文本报告已保存到: {txt_filepath}\n")
        
    except Exception as e:
        print(f"系统> ❌ 保存失败: {e}\n")
        app_logger.error(f"Save exploration result failed: {e}", exc_info=True)


def main():
    """主函数"""
    print("=" * 60)
    print("可视化分析系统 - Visual Analysis System")
    print("=" * 60)
    
    # 验证配置
    errors = validate_config()
    if errors:
        print("\n⚠️  配置错误：")
        for error in errors:
            print(f"  - {error}")
        print("\n请在环境变量或.env文件中设置DASHSCOPE_API_KEY")
        return
    
    print("\n✅ 配置验证通过")
    
    # 初始化会话管理器
    session_mgr = get_session_manager()
    print("✅ 系统初始化完成\n")
    
    
    # 示例：加载Vega-Lite规范
    print("请提供Vega-Lite规范文件路径（或输入'demo'使用示例）：")
    spec_path = input("> ").strip()
    
    if spec_path.lower() == 'demo':
        # 使用示例规范
        vega_spec = {
            "mark": "bar",
            "encoding": {
                "x": {"field": "category", "type": "nominal"},
                "y": {"field": "value", "type": "quantitative"}
            },
            "data": {
                "values": [
                    {"category": "A", "value": 28},
                    {"category": "B", "value": 55},
                    {"category": "C", "value": 43}
                ]
            }
        }
    else:
        try:
            with open(spec_path, 'r') as f:
                vega_spec = json.load(f)
        except Exception as e:
            print(f"❌ 加载文件失败: {e}")
            return
    
    # 创建会话
    print("\n创建会话...")
    session_id = session_mgr.create_session(vega_spec)
    
    if not session_id:
        print("❌ 会话创建失败")
        return
    
    print(f"✅ 会话创建成功: {session_id}\n")
    
    
    # 交互循环
    print("开始对话（输入'exit'退出，'reset'重置视图，'save'保存结果）：\n")
    
    last_result = None  # 保存最后一次结果
    
    while True:
        user_query = input("用户> ").strip()
        
        if not user_query:
            continue
        
        if user_query.lower() == 'exit':
            print("\n再见！")
            break
        
        if user_query.lower() == 'reset':
            result = session_mgr.reset_view(session_id)
            print(f"系统> {result.get('message', '重置完成')}\n")
            continue
        
        if user_query.lower() == 'save':
            if last_result and last_result.get("mode") in ("autonomous_exploration", "goal_oriented"):
                save_exploration_result(last_result, session_id)
            else:
                print("系统> 没有可保存的探索结果\n")
            continue
        
        # 处理查询
        print("\n处理中...")
        result = session_mgr.process_query(session_id, user_query)
        last_result = result  # 保存结果
        
        if result.get("success"):
            mode = result.get("mode", "unknown")
            print(f"\n[{mode.upper()}模式]")
            
            if mode == "chitchat":
                print(f"系统> {result.get('response', '')}\n")
            elif mode == "goal_oriented":
                iterations = result.get("iterations", [])
                print(f"执行了{len(iterations)}次迭代")
                for it in iterations:
                    print(f"  - 迭代{it['iteration']}:")
                    decision = it.get("decision", {})
                    goal_understanding = decision.get("goal_understanding")
                    if goal_understanding:
                        print(f"     目标理解: {goal_understanding}")
                    current_gap = decision.get("current_gap")
                    if current_gap:
                        print(f"     当前差距: {current_gap}")
                    reasoning = decision.get("reasoning")
                    if reasoning:
                        print(f"     思考: {reasoning}")
                    action_plan = decision.get("action_plan") or decision.get("decision", {}).get("action_plan", "")
                    if action_plan:
                        print(f"     行动计划: {action_plan}")
                    insights = decision.get("analysis_insights", [])
                    if insights:
                        print(f"     分析洞察:")
                        for insight in insights:
                            print(f"       - {insight}")
                    remaining_gaps = decision.get("remaining_gaps", [])
                    if remaining_gaps:
                        print(f"     剩余差距:")
                        for gap in remaining_gaps:
                            print(f"       • {gap}")
                    next_action = decision.get("next_action")
                    if next_action:
                        print(f"     下一步建议: {next_action}")
                    view_files = it.get("view_files", [])
                    if view_files:
                        print(f"     视图文件 ({len(view_files)}):")
                        for path in view_files:
                            print(f"       • {path}")
                print()
            elif mode == "autonomous_exploration":
                explorations = result.get("explorations", [])
                report = result.get("final_report", {})
                
                print(f"进行了{len(explorations)}轮探索\n")
                
                # 显示每轮探索的详细信息
                for exp in explorations:
                    iter_num = exp.get("iteration", 0)
                    success = exp.get("success", False)
                    
                    print(f"【第 {iter_num} 轮探索】")
                    
                    if not success:
                        print(f"  ❌ 失败: {exp.get('error', 'Unknown error')}")
                        print()
                        continue
                    
                    # 显示分析摘要
                    analysis = exp.get("analysis_summary", {})
                    
                    # 关键洞察
                    insights = analysis.get("key_insights", [])
                    if insights:
                        print(f"  💡 关键洞察:")
                        for idx, insight in enumerate(insights[:3], 1):  # 最多显示3个
                            print(f"     {idx}. {insight}")
                    
                    # 发现的模式
                    patterns = analysis.get("patterns_found", [])
                    if patterns:
                        print(f"  📊 数据模式:")
                        for idx, pattern in enumerate(patterns[:2], 1):  # 最多显示2个
                            print(f"     {idx}. {pattern}")
                    
                    # 异常点
                    anomalies = analysis.get("anomalies", [])
                    if anomalies:
                        print(f"  ⚠️  异常发现:")
                        for idx, anomaly in enumerate(anomalies[:2], 1):
                            print(f"     {idx}. {anomaly}")
                    
                    # 建议
                    recommendations = analysis.get("recommendations", [])
                    if recommendations:
                        print(f"  💭 分析建议:")
                        for idx, rec in enumerate(recommendations[:2], 1):
                            print(f"     {idx}. {rec}")
                    
                    # 工具使用
                    tool_exec = exp.get("tool_execution")
                    if tool_exec:
                        tool_name = tool_exec.get("tool_name", "未知工具")
                        tool_success = tool_exec.get("tool_result", {}).get("success", False)
                        status = "✅" if tool_success else "❌"
                        print(f"  🔧 工具调用: {status} {tool_name}")
                        
                        tool_result = tool_exec.get("tool_result", {})
                        if tool_result.get("message"):
                            print(f"     {tool_result['message']}")
                        if tool_result.get("error"):
                            print(f"     错误: {tool_result['error']}")
                        details = tool_result.get("details")
                        if details:
                            print("     详情:")
                            for detail in details:
                                print(f"       • {detail}")
                    
                    # 耗时
                    duration = exp.get("duration", 0)
                    print(f"  ⏱️  耗时: {duration:.2f}秒")
                    print()
                
                # 显示最终报告
                print("【探索总结】")
                print(f"  总轮次: {report.get('total_iterations', 0)}")
                print(f"  成功轮次: {report.get('successful_iterations', 0)}")
                print(f"  {report.get('summary', '探索完成')}")
                
                
                # 汇总所有洞察
                all_insights = report.get('all_insights', [])
                if all_insights:
                    print(f"\n  📝 全部洞察 ({len(all_insights)}条):")
                    for idx, insight in enumerate(all_insights[:5], 1):  # 最多显示5条
                        print(f"     {idx}. {insight}")
                    if len(all_insights) > 5:
                        print(f"     ... 还有 {len(all_insights) - 5} 条")
                
                # 工具使用统计
                tools_used = report.get('tools_used', [])
                if tools_used:
                    print(f"\n  🔧 工具使用统计:")
                    for tool_info in tools_used:
                        status = "✅" if tool_info.get("success") else "❌"
                        print(f"     {status} 第{tool_info['iteration']}轮: {tool_info['tool']}")
                
                print()
        else:
            print(f"\n❌ 错误: {result.get('error', 'Unknown error')}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断退出")
        sys.exit(0)
    except Exception as e:
        app_logger.error(f"程序异常: {e}", exc_info=True)
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
