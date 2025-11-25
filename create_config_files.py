#!/usr/bin/env python3
"""
项目文件批量生成脚本
自动创建visual-analysis-system的所有必要文件
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path("/home/claude/visual-analysis-system")

# 文件内容定义
FILES_CONTENT = {
    # ==================== 配置文件 ====================
    "config/settings.py": '''"""
全局配置文件
包含系统参数、DashScope API配置等
"""

import os
from pathlib import Path

# ==================== 项目路径配置 ====================
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"

# 确保日志目录存在
LOGS_DIR.mkdir(exist_ok=True)

# ==================== DashScope API 配置 ====================
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# VLM 模型配置 - 使用 qwen-vl-plus
VLM_MODEL = "qwen-vl-plus"
VLM_MAX_TOKENS = 2000
VLM_TEMPERATURE = 0
VLM_TOP_P = 0.9
VLM_REQUEST_TIMEOUT = 60

# ==================== 系统参数配置 ====================
SESSION_TIMEOUT = 3600
MAX_CONVERSATION_HISTORY = 20
CHART_IDENTIFICATION_CONFIDENCE_THRESHOLD = 0.7
INTENT_CONFIDENCE_THRESHOLD = 0.6
MAX_EXPLORATION_ITERATIONS = 10
EXPLORATION_STOP_CONFIDENCE = 0.85
MAX_GOAL_ORIENTED_ITERATIONS = 15
GOAL_ACHIEVEMENT_THRESHOLD = 0.7

# ==================== Vega 渲染配置 ====================
VEGA_RENDERER = "canvas"
VEGA_IMAGE_FORMAT = "png"
VEGA_IMAGE_SCALE = 2
VEGA_DEFAULT_WIDTH = 800
VEGA_DEFAULT_HEIGHT = 600

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
APP_LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
VLM_LOG_FILE = LOGS_DIR / "vlm_calls.log"

# ==================== 其他配置 ====================
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
TOOL_EXECUTION_TIMEOUT = 30
ENABLE_TOOL_VALIDATION = True
ENABLE_PROMPT_CACHE = True
PROMPT_CACHE_TTL = 3600

def validate_config():
    """验证配置的有效性"""
    errors = []
    if not DASHSCOPE_API_KEY:
        errors.append("DASHSCOPE_API_KEY 未设置")
    if VLM_MAX_TOKENS < 100:
        errors.append("VLM_MAX_TOKENS 过小")
    if not (0 <= VLM_TEMPERATURE <= 2):
        errors.append("VLM_TEMPERATURE 应在 0-2 之间")
    if not (0 <= VLM_TOP_P <= 1):
        errors.append("VLM_TOP_P 应在 0-1 之间")
    return errors
''',

    "config/chart_types.py": '''"""
图表类型枚举和配置
定义支持的所有图表类型及其特征
"""

from enum import Enum
from typing import Dict, List

class ChartType(Enum):
    """图表类型枚举"""
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    SCATTER_PLOT = "scatter_plot"
    PARALLEL_COORDINATES = "parallel_coordinates"
    HEATMAP = "heatmap"
    SANKEY_DIAGRAM = "sankey_diagram"
    UNKNOWN = "unknown"

# 图表类型元数据配置
CHART_TYPE_METADATA = {
    ChartType.BAR_CHART: {
        "name": "条形图",
        "description": "用于比较不同类别的数值",
        "vega_marks": ["bar"],
        "typical_encodings": ["x", "y", "color"],
        "tools_prefix": "bar_chart",
        "visual_features": ["矩形条形", "类别轴", "数值轴"]
    },
    ChartType.LINE_CHART: {
        "name": "折线图",
        "description": "用于展示数据随时间或连续变量的变化趋势",
        "vega_marks": ["line", "point", "area"],
        "typical_encodings": ["x", "y", "color"],
        "tools_prefix": "line_chart",
        "visual_features": ["连续的线条", "时间或连续轴", "趋势变化"]
    },
    ChartType.SCATTER_PLOT: {
        "name": "散点图",
        "description": "用于展示两个变量之间的关系和分布",
        "vega_marks": ["point", "circle"],
        "typical_encodings": ["x", "y", "size", "color"],
        "tools_prefix": "scatter_plot",
        "visual_features": ["离散的点", "两个数值轴", "点的分布模式"]
    },
    ChartType.PARALLEL_COORDINATES: {
        "name": "平行坐标图",
        "description": "用于展示多维数据和变量之间的关系",
        "vega_marks": ["line", "rule"],
        "typical_encodings": ["x", "y", "color", "detail"],
        "tools_prefix": "parallel_coordinates",
        "visual_features": ["多条平行的垂直轴", "连接各轴的折线"]
    },
    ChartType.HEATMAP: {
        "name": "热力图",
        "description": "用于展示矩阵数据和两个分类变量的关系强度",
        "vega_marks": ["rect", "square"],
        "typical_encodings": ["x", "y", "color"],
        "tools_prefix": "heatmap",
        "visual_features": ["网格状矩形", "颜色编码数值"]
    },
    ChartType.SANKEY_DIAGRAM: {
        "name": "Sankey图",
        "description": "用于展示流量、转化或网络关系",
        "vega_marks": ["path", "rect", "link"],
        "typical_encodings": ["source", "target", "value"],
        "tools_prefix": "sankey",
        "visual_features": ["流动的带状路径", "节点和连接"]
    }
}

def get_chart_type_by_name(name: str):
    """根据名称获取图表类型"""
    for chart_type in ChartType:
        if chart_type.value == name.lower():
            return chart_type
    return ChartType.UNKNOWN

def get_candidate_chart_types(vega_spec: dict) -> List:
    """根据 Vega-Lite 规范推测可能的图表类型"""
    candidates = []
    mark = vega_spec.get("mark", {})
    if isinstance(mark, str):
        mark_type = mark
    elif isinstance(mark, dict):
        mark_type = mark.get("type", "")
    else:
        return [ChartType.UNKNOWN]
    
    # 简单的mark类型映射
    mark_mapping = {
        "bar": [ChartType.BAR_CHART],
        "line": [ChartType.LINE_CHART],
        "point": [ChartType.SCATTER_PLOT],
        "rect": [ChartType.HEATMAP],
    }
    return mark_mapping.get(mark_type, [ChartType.UNKNOWN])

def get_chart_metadata(chart_type):
    """获取图表类型的元数据"""
    return CHART_TYPE_METADATA.get(chart_type, {})
''',

    "config/intent_types.py": '''"""
意图类型枚举
定义用户查询的意图分类
"""

from enum import Enum
from typing import Dict

class IntentType(Enum):
    """用户意图类型枚举"""
    CHITCHAT = "chitchat"
    EXPLICIT_ANALYTICAL = "explicit_analytical"
    VAGUE_ANALYTICAL = "vague_analytical"
    UNKNOWN = "unknown"

# 意图类型元数据
INTENT_TYPE_METADATA = {
    IntentType.CHITCHAT: {
        "name": "闲聊",
        "description": "用户进行社交对话，不涉及数据分析",
        "indicators": ["问候语", "感谢", "系统功能询问"],
        "response_mode": "direct_conversation"
    },
    IntentType.EXPLICIT_ANALYTICAL: {
        "name": "明确分析意图",
        "description": "用户有明确的操作目标或分析需求",
        "indicators": ["具体的操作动词", "明确的数据范围或条件"],
        "response_mode": "goal_oriented"
    },
    IntentType.VAGUE_ANALYTICAL: {
        "name": "模糊分析意图",
        "description": "用户想要了解数据，但没有明确的操作目标",
        "indicators": ["开放式问题", "探索性语言"],
        "response_mode": "autonomous_exploration"
    }
}

def get_intent_metadata(intent_type):
    """获取意图类型的元数据"""
    return INTENT_TYPE_METADATA.get(intent_type, {})

def get_intent_by_name(name: str):
    """根据名称获取意图类型"""
    for intent_type in IntentType:
        if intent_type.value == name.lower():
            return intent_type
    return IntentType.UNKNOWN
''',

    "config/__init__.py": '''"""配置模块"""
from .settings import *
from .chart_types import *
from .intent_types import *
''',
}

def create_files():
    """创建所有文件"""
    for file_path, content in FILES_CONTENT.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created: {file_path}")

if __name__ == "__main__":
    create_files()
    print(f"\n✅ 配置文件创建完成！")
