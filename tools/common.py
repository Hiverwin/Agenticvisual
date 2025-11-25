"""
通用工具库（简化版 - 直接使用 vega_spec，无需 view_id）
包含感知类API和行动类API，适用于所有图表类型
"""

import json
import copy
from typing import Dict, List, Any, Tuple, Optional
import numpy as np


# ==================== 感知类 API (Perception APIs) ====================

def get_data_summary(vega_spec: Dict, scope: str = 'all') -> Dict[str, Any]:
    """
    返回数据的统计摘要
    
    Args:
        vega_spec: Vega-Lite规范
        scope: 'visible' 或 'all' - 返回可见数据或全部数据的统计
        
    Returns:
        统计摘要字典
    """
    # 从 vega_spec 中提取数据
    data = vega_spec.get('data', {}).get('values', [])
    
    if not data:
        return {'success': False, 'error': 'No data available'}
    
    # 计算统计信息
    summary = {
        'count': len(data),
        'numeric_fields': {},
        'categorical_fields': {}
    }
    
    if data:
        sample = data[0]
        for field_name in sample.keys():
            values = [row.get(field_name) for row in data if row.get(field_name) is not None]
            
            if not values:
                continue
            
            if isinstance(values[0], (int, float)):
                summary['numeric_fields'][field_name] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'median': float(np.median(values))
                }
            else:
                unique_values = list(set(values))
                value_counts = {v: values.count(v) for v in unique_values}
                
                summary['categorical_fields'][field_name] = {
                    'unique_count': len(unique_values),
                    'categories': unique_values[:20],
                    'distribution': value_counts
                }
    
    return {
        'success': True,
        'summary': summary
    }


def get_tooltip_data(vega_spec: Dict, position: Tuple[float, float]) -> Dict[str, Any]:
    """获取指定位置的工具提示数据"""
    data = vega_spec.get('data', {}).get('values', [])
    
    x_pos, y_pos = position
    x_field = _get_encoding_field(vega_spec, 'x')
    y_field = _get_encoding_field(vega_spec, 'y')
    
    if not x_field or not y_field:
        return {'success': False, 'message': 'Cannot find x/y fields'}
    
    closest_point = None
    min_distance = float('inf')
    
    for row in data:
        x_val = row.get(x_field)
        y_val = row.get(y_field)
        
        if x_val is not None and y_val is not None:
            distance = np.sqrt((x_val - x_pos)**2 + (y_val - y_pos)**2)
            if distance < min_distance:
                min_distance = distance
                closest_point = row
    
    if closest_point:
        return {'success': True, 'data': closest_point, 'distance': min_distance}
    
    return {'success': False, 'message': 'No data point found'}


# ==================== 行动类 API (Action APIs) ====================

def zoom(vega_spec: Dict, area: List[float]) -> Dict[str, Any]:
    """缩放指定区域，过滤掉区域外的数据点
    
    Args:
        vega_spec: Vega-Lite规范
        area: [x1, y1, x2, y2] 缩放区域（4个元素的列表）
    
    Returns:
        包含过滤后的vega_spec和统计信息的字典
    """
    new_spec = copy.deepcopy(vega_spec)
    x1, y1, x2, y2 = area
    
    # 提取x和y范围
    x_range = [min(x1, x2), max(x1, x2)]
    y_range = [min(y1, y2), max(y1, y2)]
    
    # 获取字段名
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {
            'success': False,
            'error': 'Cannot find required x or y fields in encoding',
            'operation': 'zoom'
        }
    
    # 获取原始数据
    data = new_spec.get('data', {}).get('values', [])
    if not data:
        return {
            'success': False,
            'error': 'No data found in specification',
            'operation': 'zoom'
        }
    
    original_count = len(data)
    
    # 过滤数据：只保留范围内的点
    filtered_data = [
        point for point in data
        if (point.get(x_field) is not None and 
            point.get(y_field) is not None and
            x_range[0] <= point[x_field] <= x_range[1] and
            y_range[0] <= point[y_field] <= y_range[1])
    ]
    
    filtered_count = len(filtered_data)
    
    if filtered_count == 0:
        return {
            'success': False,
            'error': f'No data points found in range x:[{x_range[0]}, {x_range[1]}], y:[{y_range[0]}, {y_range[1]}]',
            'original_count': original_count,
            'filtered_count': 0,
            'operation': 'zoom'
        }
    
    # 更新数据
    new_spec['data']['values'] = filtered_data
    
    # 调整axis scales
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    for axis, vals in [('x', x_range), ('y', y_range)]:
        if axis not in new_spec['encoding']:
            new_spec['encoding'][axis] = {}
        if 'scale' not in new_spec['encoding'][axis]:
            new_spec['encoding'][axis]['scale'] = {}
        new_spec['encoding'][axis]['scale']['domain'] = vals
    
    return {
        'success': True,
        'operation': 'zoom',
        'vega_spec': new_spec,
        'original_count': original_count,
        'filtered_count': filtered_count,
        'zoom_range': {
            'x': x_range,
            'y': y_range
        },
        'message': f'Zoomed to area [{x1},{y1},{x2},{y2}]: showing {filtered_count} out of {original_count} points ({filtered_count/original_count*100:.1f}%)'
    }


def filter(vega_spec: Dict, dimension: str, range: List[float]) -> Dict[str, Any]:
    """按维度筛选数据"""
    new_spec = copy.deepcopy(vega_spec)
    min_val, max_val = range
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    new_spec['transform'].append({
        'filter': f'datum.{dimension} >= {min_val} && datum.{dimension} <= {max_val}'
    })
    
    return {
        'success': True,
        'operation': 'filter',
        'vega_spec': new_spec,
        'message': f'Filtered {dimension} to [{min_val},{max_val}]'
    }


def brush(vega_spec: Dict, area: List[float]) -> Dict[str, Any]:
    """刷选区域"""
    new_spec = copy.deepcopy(vega_spec)
    return {
        'success': True,
        'operation': 'brush',
        'vega_spec': new_spec,
        'message': f'Brushed area {area}'
    }


def change_encoding(vega_spec: Dict, channel: str, field_name: str) -> Dict[str, Any]:
    """更改编码映射"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding'][channel] = {
        'field': field_name,
        'type': _infer_field_type(vega_spec, field_name)
    }
    
    return {
        'success': True,
        'operation': 'change_encoding',
        'vega_spec': new_spec,
        'message': f'Changed {channel} to {field_name}'
    }


def highlight(vega_spec: Dict, category: Any) -> Dict[str, Any]:
    """高亮类别"""
    new_spec = copy.deepcopy(vega_spec)
    
    if not isinstance(category, list):
        category = [category]
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    primary_field = _get_primary_category_field(new_spec)
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': f'indexof({json.dumps(category)}, datum.{primary_field}) >= 0',
            'value': 1.0
        },
        'value': 0.2
    }
    
    return {
        'success': True,
        'operation': 'highlight',
        'vega_spec': new_spec,
        'message': f'Highlighted {len(category)} categories'
    }


def render_chart(vega_spec: Dict) -> Dict[str, Any]:
    """渲染图表"""
    from core.vega_service import get_vega_service
    from core.utils import app_logger
    
    try:
        vega_service = get_vega_service()
        render_result = vega_service.render(vega_spec)
        
        if render_result.get("success"):
            return {
                'success': True,
                'operation': 'render',
                'image_base64': render_result["image_base64"],
                'renderer': render_result.get("renderer"),
                'message': f'Rendered using {render_result.get("renderer")}'
            }
        else:
            return {
                'success': False,
                'operation': 'render',
                'error': render_result.get("error")
            }
    except Exception as e:
        return {'success': False, 'operation': 'render', 'error': str(e)}


# ==================== 辅助函数 ====================

def _get_encoding_field(vega_spec: Dict, channel: str) -> Optional[str]:
    """获取编码字段"""
    return vega_spec.get('encoding', {}).get(channel, {}).get('field')


def _get_primary_category_field(vega_spec: Dict) -> str:
    """获取主分类字段"""
    encoding = vega_spec.get('encoding', {})
    for channel in ['color', 'x', 'y']:
        if channel in encoding:
            field = encoding[channel].get('field')
            field_type = encoding[channel].get('type')
            if field and field_type in ['nominal', 'ordinal']:
                return field
    return 'category'


def _infer_field_type(vega_spec: Dict, field_name: str) -> str:
    """推断字段类型"""
    data = vega_spec.get('data', {}).get('values', [])
    if not data:
        return 'nominal'
    
    for row in data:
        value = row.get(field_name)
        if value is not None:
            if isinstance(value, (int, float)):
                return 'quantitative'
            elif isinstance(value, str):
                if any(sep in value for sep in ['-', '/', ':']):
                    return 'temporal'
                return 'nominal'
    return 'nominal'


__all__ = [
    'get_data_summary',
    'get_tooltip_data',
    'zoom',
    'filter',
    'brush',
    'change_encoding',
    'highlight',
    'render_chart',
]
