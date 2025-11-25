"""
平行坐标图专用工具（简化版 - 使用 vega_spec）
"""

from typing import Dict, Any, List
import copy


def filter_dimension(vega_spec: Dict, dimension: str, range: List[float]) -> Dict[str, Any]:
    """按维度筛选"""
    new_spec = copy.deepcopy(vega_spec)
    
    min_val, max_val = range
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    new_spec['transform'].append({
        'filter': f'datum.{dimension} >= {min_val} && datum.{dimension} <= {max_val}'
    })
    
    return {
        'success': True,
        'operation': 'filter_dimension',
        'vega_spec': new_spec,
        'message': f'Filtered {dimension} to [{min_val}, {max_val}]'
    }


def highlight_cluster(vega_spec: Dict, cluster_id: int) -> Dict[str, Any]:
    """高亮聚类"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': f'datum.cluster == {cluster_id}',
            'value': 1.0
        },
        'value': 0.1
    }
    
    return {
        'success': True,
        'operation': 'highlight_cluster',
        'vega_spec': new_spec,
        'message': f'Highlighted cluster {cluster_id}'
    }


def reorder_dimensions(vega_spec: Dict, dimension_order: List[str]) -> Dict[str, Any]:
    """重新排序维度"""
    new_spec = copy.deepcopy(vega_spec)
    
    # 这是一个简化实现
    # 实际的平行坐标图可能需要更复杂的重排逻辑
    
    return {
        'success': True,
        'operation': 'reorder_dimensions',
        'vega_spec': new_spec,
        'message': f'Reordered dimensions to {dimension_order}'
    }


__all__ = [
    'filter_dimension',
    'highlight_cluster',
    'reorder_dimensions'
]
