"""
条形图专用工具（简化版 - 使用 vega_spec）
"""

from typing import List, Dict, Any
import copy


def sort_bars(vega_spec: Dict, order: str = "descending") -> Dict[str, Any]:
    """按值排序条形"""
    new_spec = copy.deepcopy(vega_spec)
    
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not y_field:
        return {'success': False, 'error': 'Cannot find value field'}
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    if 'x' not in new_spec['encoding']:
        new_spec['encoding']['x'] = {}
    
    new_spec['encoding']['x']['sort'] = {
        'field': y_field,
        'order': order
    }
    
    return {
        'success': True,
        'operation': 'sort_bars',
        'vega_spec': new_spec,
        'message': f'Sorted bars in {order} order'
    }


def filter_categories(vega_spec: Dict, categories: List[str]) -> Dict[str, Any]:
    """筛选特定类别"""
    new_spec = copy.deepcopy(vega_spec)
    
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    
    if not x_field:
        return {'success': False, 'error': 'Cannot find category field'}
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    category_str = ','.join([f'"{c}"' for c in categories])
    new_spec['transform'].append({
        'filter': f'indexof([{category_str}], datum.{x_field}) >= 0'
    })
    
    return {
        'success': True,
        'operation': 'filter_categories',
        'vega_spec': new_spec,
        'message': f'Filtered to {len(categories)} categories'
    }


def highlight_top_n(vega_spec: Dict, n: int = 5, order: str = "descending") -> Dict[str, Any]:
    """高亮前N个条形"""
    new_spec = copy.deepcopy(vega_spec)
    
    data = new_spec.get('data', {}).get('values', [])
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not y_field or not data:
        return {'success': False, 'error': 'Missing data or field'}
    
    # 排序数据获取top N
    order_value = str(order).lower()
    descending_aliases = {"descending", "desc", "top", "high", "max", "maximum"}
    descending = order_value in descending_aliases
    reverse = descending
    sorted_data = sorted(data, key=lambda x: x.get(y_field, 0), reverse=reverse)
    top_values = [row.get(y_field) for row in sorted_data[:n]]
    
    # 添加高亮
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': ' || '.join([f'datum.{y_field} == {v}' for v in top_values]),
            'value': 1.0
        },
        'value': 0.3
    }
    
    return {
        'success': True,
        'operation': 'highlight_top_n',
        'vega_spec': new_spec,
        'message': f'Highlighted top {n} bars'
    }


def compare_groups(vega_spec: Dict, group_field: str) -> Dict[str, Any]:
    """组间对比"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['color'] = {
        'field': group_field,
        'type': 'nominal'
    }
    
    return {
        'success': True,
        'operation': 'compare_groups',
        'vega_spec': new_spec,
        'message': f'Grouped by {group_field}'
    }


__all__ = [
    'sort_bars',
    'filter_categories',
    'highlight_top_n',
    'compare_groups'
]
