"""
桑基图专用工具（简化版 - 使用 vega_spec）
"""

from typing import Dict, Any, List
import copy


def filter_flow(vega_spec: Dict, min_value: float) -> Dict[str, Any]:
    """筛选流量"""
    new_spec = copy.deepcopy(vega_spec)
    
    value_field = 'value'  # 桑基图通常使用 value 字段
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    new_spec['transform'].append({
        'filter': f'datum.{value_field} >= {min_value}'
    })
    
    return {
        'success': True,
        'operation': 'filter_flow',
        'vega_spec': new_spec,
        'message': f'Filtered flows >= {min_value}'
    }


def highlight_path(vega_spec: Dict, source: str, target: str) -> Dict[str, Any]:
    """高亮路径"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': f'datum.source == "{source}" && datum.target == "{target}"',
            'value': 1.0
        },
        'value': 0.2
    }
    
    return {
        'success': True,
        'operation': 'highlight_path',
        'vega_spec': new_spec,
        'message': f'Highlighted path {source} -> {target}'
    }


def trace_node(vega_spec: Dict, node_name: str) -> Dict[str, Any]:
    """追踪节点"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': f'datum.source == "{node_name}" || datum.target == "{node_name}"',
            'value': 1.0
        },
        'value': 0.2
    }
    
    return {
        'success': True,
        'operation': 'trace_node',
        'vega_spec': new_spec,
        'message': f'Traced connections of {node_name}'
    }


__all__ = [
    'filter_flow',
    'highlight_path',
    'trace_node'
]
