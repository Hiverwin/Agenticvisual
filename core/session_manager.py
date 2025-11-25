"""
会话管理器
负责会话状态维护、意图识别、模式分发
"""

from typing import Dict, Optional
import uuid
import time

from config.chart_types import ChartType, get_candidate_chart_types
from config.intent_types import IntentType
from core.vlm_service import get_vlm_service
from core.vega_service import get_vega_service
from core.modes import ChitchatMode, GoalOrientedMode, AutonomousExplorationMode
from prompts import get_prompt_manager
from core.utils import app_logger


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> session_data
        self.vlm = get_vlm_service()
        self.vega = get_vega_service()
        self.prompt_mgr = get_prompt_manager()
        
        # 初始化各模式
        self.chitchat_mode = ChitchatMode()
        self.goal_mode = GoalOrientedMode()
        self.explore_mode = AutonomousExplorationMode()
        
        app_logger.info("Session Manager initialized")
    
    def create_session(self, vega_spec: Dict) -> str:
        """
        创建新会话
        
        Args:
            vega_spec: Vega-Lite JSON规范
        
        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())
        
        # 渲染初始视图
        render_result = self.vega.render(vega_spec)
        
        if not render_result.get("success"):
            app_logger.error("Failed to render initial view")
            return None
        
        # 识别图表类型
        chart_type = self._identify_chart_type(
            vega_spec,
            render_result["image_base64"]
        )
        
        # 创建会话数据
        self.sessions[session_id] = {
            "session_id": session_id,
            "vega_spec": vega_spec,
            "original_spec": vega_spec,  # 保存原始规范
            "current_image": render_result["image_base64"],
            "chart_type": chart_type,
            "conversation_history": [],
            "created_at": time.time(),
            "last_activity": time.time()
        }
        
        app_logger.info(f"Session created: {session_id}, chart_type: {chart_type}")
        return session_id
    
    def _identify_chart_type(self, vega_spec: Dict, image_base64: str) -> ChartType:
        """识别图表类型"""
        # 首先从Vega规范推测
        candidates = get_candidate_chart_types(vega_spec)
        
        if len(candidates) == 1 and candidates[0] != ChartType.UNKNOWN:
            return candidates[0]
        
        # 如果无法确定，使用VLM视觉识别
        prompt = """请识别这个图表的类型。返回JSON格式：
{
    "chart_type": "bar_chart|line_chart|scatter_plot|parallel_coordinates|heatmap|sankey_diagram",
    "confidence": 0.0-1.0,
    "reasoning": "判断理由"
}"""
        
        response = self.vlm.call_with_image(prompt, image_base64, expect_json=True)
        
        if response.get("success"):
            parsed = response.get("parsed_json", {})
            chart_type_str = parsed.get("chart_type", "unknown")
            
            # 转换为ChartType枚举
            for ct in ChartType:
                if ct.value == chart_type_str:
                    return ct
        
        return ChartType.UNKNOWN
    
    def process_query(self, session_id: str, user_query: str) -> Dict:
        """
        处理用户查询
        
        Args:
            session_id: 会话ID
            user_query: 用户查询文本
        
        Returns:
            处理结果
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        session["last_activity"] = time.time()
        
        # 1. 意图识别
        intent = self._recognize_intent(
            user_query,
            session["current_image"],
            session["chart_type"]
        )
        
        # 2. 根据意图分发到不同模式
        if intent == IntentType.CHITCHAT:
            result = self.chitchat_mode.execute(user_query, session["current_image"], session)
        elif intent == IntentType.EXPLICIT_ANALYSIS:
            result = self.goal_mode.execute(
                user_query,
                session["vega_spec"],
                session["current_image"],
                session["chart_type"],
                session
            )
            # 更新会话状态
            if result.get("success"):
                session["vega_spec"] = result.get("final_spec", session["vega_spec"])
                session["current_image"] = result.get("final_image", session["current_image"])
        else:  # VAGUE_EXPLORATION
            result = self.explore_mode.execute(
                user_query,
                session["vega_spec"],
                session["current_image"],
                session["chart_type"],
                session
            )
        
        # 3. 更新对话历史
        session["conversation_history"].append({
            "query": user_query,
            "intent": intent.value if isinstance(intent, IntentType) else str(intent),
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def _recognize_intent(self, user_query: str, image_base64: str, 
                         chart_type: ChartType) -> IntentType:
        """识别用户意图"""
        # 快速判断：基于关键词识别明显的意图
        query_lower = user_query.lower().strip()
        
        # 问候语关键词
        greetings = [
            '你好', '您好', 'hi', 'hello', 'hey', '嗨', 'hola',
            '早上好', '中午好', '下午好', '晚上好', '早安', '晚安'
        ]
        
        # 礼貌用语关键词
        polite_words = [
            '谢谢', '多谢', 'thanks', 'thank you', 'thx',
            '再见', '拜拜', 'bye', 'goodbye', 'see you'
        ]
        
        # 系统询问关键词
        system_queries = [
            '你是谁', '你叫什么', '你能做什么', '你会什么',
            '怎么用', '怎么使用', '如何使用', '使用方法',
            'what can you do', 'how to use', 'who are you'
        ]
        
        # 明确操作关键词（表示 EXPLICIT_ANALYSIS）
        explicit_actions = [
            '筛选', '过滤', 'filter', 'select',
            '放大', '缩小', 'zoom', 'scale',
            '高亮', '突出', 'highlight', 'emphasize',
            '排序', 'sort', 'order',
            '显示', '隐藏', 'show', 'hide',
            '对比', '比较', 'compare', 'contrast',
            '选择', '选中', 'choose', 'pick',
            '调整', '修改', 'adjust', 'modify',
            '聚焦', 'focus',
            '只看', '只显示', 'only show',
            '去掉', '删除', 'remove', 'delete',
            '添加', '增加', 'add',
            '改成', '换成', 'change to',
            '设置为', 'set to'
        ]
        
        # 检查是否为纯粹的问候或礼貌用语（长度小于10个字符）
        if len(query_lower) < 10:
            for greeting in greetings:
                if greeting in query_lower:
                    app_logger.info(f"Quick intent recognition: CHITCHAT (greeting: {greeting})")
                    return IntentType.CHITCHAT
            
            for polite in polite_words:
                if polite in query_lower:
                    app_logger.info(f"Quick intent recognition: CHITCHAT (polite: {polite})")
                    return IntentType.CHITCHAT
        
        # 检查系统询问（即使较长的句子）
        for sys_query in system_queries:
            if sys_query in query_lower:
                app_logger.info(f"Quick intent recognition: CHITCHAT (system query: {sys_query})")
                return IntentType.CHITCHAT
        
        # 检查明确操作关键词
        for action in explicit_actions:
            if action in query_lower:
                app_logger.info(f"Quick intent recognition: EXPLICIT_ANALYSIS (action: {action})")
                return IntentType.EXPLICIT_ANALYSIS
        
        # 使用VLM进行意图识别
        intent_prompt = self.prompt_mgr.get_intent_recognition_prompt(
            user_query=user_query,
            chart_type=chart_type
        )
        
        response = self.vlm.call_with_image(
            intent_prompt, image_base64,
            expect_json=True
        )
        
        if response.get("success"):
            parsed = response.get("parsed_json", {})
            intent_str = parsed.get("intent_type", "unknown")
            
            app_logger.info(f"VLM intent recognition: {intent_str}")
            
            for it in IntentType:
                if it.value == intent_str:
                    return it
        
        return IntentType.UNKNOWN
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话数据"""
        return self.sessions.get(session_id)
    
    def reset_view(self, session_id: str) -> Dict:
        """重置视图到原始状态"""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        session["vega_spec"] = session["original_spec"]
        
        render_result = self.vega.render(session["vega_spec"])
        if render_result.get("success"):
            session["current_image"] = render_result["image_base64"]
        
        return {"success": True, "message": "View reset to original state"}


_session_manager = None

def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
