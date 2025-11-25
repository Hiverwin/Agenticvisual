"""目标导向模式"""
from typing import Dict, List
from core.vlm_service import get_vlm_service
from core.vega_service import get_vega_service
from tools import get_tool_executor
from prompts import get_prompt_manager
from config.settings import Settings
from core.utils import app_logger
import time


class GoalOrientedMode:
    """目标导向模式"""
    
    def __init__(self):
        self.vlm = get_vlm_service()
        self.vega = get_vega_service()
        self.tool_executor = get_tool_executor()
        self.prompt_mgr = get_prompt_manager()
    
    def execute(self, user_query: str, vega_spec: Dict, 
                image_base64: str, chart_type, context: Dict = None) -> Dict:
        """执行目标导向分析（按DashScope标准多轮对话格式）"""
        system_prompt = self.prompt_mgr.assemble_system_prompt(
            chart_type=chart_type,
            mode="goal_oriented",
            include_tools=True
        )
        
        # 从context读取messages历史（如果有）
        messages = context.get('goal_oriented_messages', []) if context else []
        iterations = context.get('goal_oriented_iterations', []) if context else []
        
        # 如果是新会话，初始化第一条user消息
        if len(messages) == 0:
            messages.append({
                "role": "user",
                "content": [
                    {"text": f"请分析这个视图，用户的分析目标是：{user_query}"},
                    {"image": f"data:image/png;base64,{image_base64}"}
                ]
            })
        
        current_spec = vega_spec
        current_image = image_base64
        
        for iteration in range(Settings.MAX_GOAL_ORIENTED_ITERATIONS):
            # 📊 日志：打印messages结构
            app_logger.info(f"📨 第{iteration+1}轮 - messages数量: {len(messages)}")
            for idx, msg in enumerate(messages):
                role = msg['role']
                content_items = len(msg.get('content', []))
                has_image = any('image' in c for c in msg.get('content', []))
                app_logger.info(f"  消息{idx}: role={role}, items={content_items}, 含图片={has_image}")
            
            # VLM调用
            response = self.vlm.call(messages, system_prompt, expect_json=True)
            
            if not response.get("success"):
                app_logger.error(f"❌ 第{iteration+1}轮VLM失败: {response.get('error', 'Unknown')}")
                
                # 记录失败的迭代
                iterations.append({
                    "iteration": iteration + 1,
                    "success": False,
                    "error": response.get('error', 'Unknown'),
                    "timestamp": time.time()
                })
                break
            
            # 关键：直接追加VLM返回的assistant消息（按DashScope标准）
            decision = response.get("parsed_json", {})
            assistant_message = {
                "role": "assistant",
                "content": [{"text": response.get("content", "")}]  # VLM原始输出文本
            }
            messages.append(assistant_message)
            
            # 📊 日志
            tool_info = decision.get('tool_call', {}).get('tool', 'None') if decision.get('tool_call') else 'None'
            achieved = decision.get('goal_achieved', False)
            app_logger.info(f"✅ 第{iteration+1}轮VLM决策: tool={tool_info}, goal_achieved={achieved}")
            
            # 记录迭代
            iteration_record = {
                "iteration": iteration + 1,
                "success": True,
                "timestamp": time.time(),
                "decision": decision,
                "vlm_raw_output": response.get("content", ""),  # 保存VLM原始输出
                "images": [current_image],
                "analysis_summary": {
                    "goal_understanding": decision.get("goal_understanding"),
                    "current_gap": decision.get("current_gap"),
                    "action_plan": decision.get("action_plan"),
                    "reasoning": decision.get("reasoning")
                }
            }
            
            # 检查是否达成目标
            if decision.get("goal_achieved", False):
                iterations.append(iteration_record)
                app_logger.info(f"Goal achieved at iteration {iteration + 1}")
                break
            
            # 执行工具
            if decision.get("tool_call"):
                tool_call = decision["tool_call"]
                tool_name = tool_call["tool"]
                tool_params = tool_call.get("params", {})
                tool_params['vega_spec'] = current_spec
                
                tool_result = self.tool_executor.execute(tool_name, tool_params)
                
                # 保存工具执行记录（包含完整结果）
                iteration_record["tool_execution"] = {
                    "tool_name": tool_name,
                    "tool_params": {k: v for k, v in tool_params.items() if k != 'vega_spec'},
                    "tool_result": tool_result  # 保存完整的tool_result
                }
                
                if tool_result.get("success") and "vega_spec" in tool_result:
                    # 情况1：工具成功且返回新的vega_spec（修改型工具）
                    current_spec = tool_result["vega_spec"]
                    render_result = self.vega.render(current_spec)
                    
                    if render_result.get("success"):
                        current_image = render_result["image_base64"]
                        iteration_record["images"].append(current_image)
                        
                        # 追加user消息：工具成功反馈
                        success_msg = tool_result.get("message", "操作完成")
                        messages.append({
                            "role": "user",
                            "content": [
                                {"text": f"✅ 工具 {tool_name} 执行成功。\n\n结果：{success_msg}\n\n这是更新后的视图："},
                                {"image": f"data:image/png;base64,{current_image}"}
                            ]
                        })
                        
                        app_logger.info(f"Re-rendered chart after {tool_name}: {success_msg}")
                    else:
                        # 渲染失败
                        render_error = render_result.get('error', 'Render failed')
                        app_logger.error(f"Failed to render after {tool_name}: {render_error}")
                        iteration_record["success"] = False
                        
                        messages.append({
                            "role": "user",
                            "content": [
                                {"text": f"❌ 工具 {tool_name} 执行后渲染失败：{render_error}\n\n当前视图（未变化）："},
                                {"image": f"data:image/png;base64,{current_image}"}
                            ]
                        })
                
                elif tool_result.get("success"):
                    # 情况2：工具成功但没有返回vega_spec（分析型工具，如calculate_correlation）
                    analysis_msg = tool_result.get("message", str(tool_result))
                    messages.append({
                        "role": "user",
                        "content": [
                            {"text": f"✅ 工具 {tool_name} 执行成功。\n\n分析结果：{analysis_msg}\n\n视图未变化，当前视图："},
                            {"image": f"data:image/png;base64,{current_image}"}
                        ]
                    })
                    
                    app_logger.info(f"Tool {tool_name} completed (analysis only): {analysis_msg}")
                
                else:
                    # 情况3：工具执行失败
                    error_msg = tool_result.get("error", "Unknown error")
                    messages.append({
                        "role": "user",
                        "content": [
                            {"text": f"❌ 工具 {tool_name} 执行失败。\n\n错误原因：{error_msg}\n\n请选择其他可用工具，或如果目标已达成，设置 goal_achieved: true。\n\n当前视图（未变化）："},
                            {"image": f"data:image/png;base64,{current_image}"}
                        ]
                    })
                    
                    iteration_record["success"] = False
                    app_logger.warning(f"Tool {tool_name} failed: {error_msg}")
            
            iterations.append(iteration_record)
        
        # 保存messages和iterations到context（用于下次调用）
        if context is not None:
            context['goal_oriented_messages'] = messages
            context['goal_oriented_iterations'] = iterations
        
        return {
            "success": True,
            "mode": "goal_oriented",
            "iterations": iterations,
            "final_spec": current_spec,
            "final_image": current_image
        }
