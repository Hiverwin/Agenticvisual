"""
热力图专用工具（简化版 - 使用 vega_spec）
"""

from typing import Dict, Any, List
import copy


def adjust_color_scale(vega_spec: Dict, scheme: str = "viridis") -> Dict[str, Any]:
    """调整颜色比例"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    if 'color' not in new_spec['encoding']:
        new_spec['encoding']['color'] = {}
    
    new_spec['encoding']['color']['scale'] = {'scheme': scheme}
    
    return {
        'success': True,
        'operation': 'adjust_color_scale',
        'vega_spec': new_spec,
        'message': f'Changed color scheme to {scheme}'
    }


def filter_cells(vega_spec: Dict, min_value: float, max_value: float) -> Dict[str, Any]:
    """筛选单元格"""
    new_spec = copy.deepcopy(vega_spec)
    
    color_field = new_spec.get('encoding', {}).get('color', {}).get('field')
    
    if not color_field:
        return {'success': False, 'error': 'Cannot find color field'}
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    new_spec['transform'].append({
        'filter': f'datum.{color_field} >= {min_value} && datum.{color_field} <= {max_value}'
    })
    
    return {
        'success': True,
        'operation': 'filter_cells',
        'vega_spec': new_spec,
        'message': f'Filtered cells to [{min_value}, {max_value}]'
    }


def highlight_region(vega_spec: Dict, x_values: List, y_values: List) -> Dict[str, Any]:
    """高亮区域"""
    new_spec = copy.deepcopy(vega_spec)
    
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {'success': False, 'error': 'Cannot find x/y fields'}
    
    x_str = ','.join([f'"{v}"' for v in x_values])
    y_str = ','.join([f'"{v}"' for v in y_values])
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': f'indexof([{x_str}], datum.{x_field}) >= 0 && indexof([{y_str}], datum.{y_field}) >= 0',
            'value': 1.0
        },
        'value': 0.3
    }
    
    return {
        'success': True,
        'operation': 'highlight_region',
        'vega_spec': new_spec,
        'message': 'Highlighted specified region'
    }


def cluster_rows_cols(vega_spec: Dict, cluster_rows: bool = True, 
                     cluster_cols: bool = True, method: str = "sum") -> Dict[str, Any]:
    """对行列进行聚类排序（基于数值的排序）"""
    new_spec = copy.deepcopy(vega_spec)
    
    if 'encoding' not in new_spec:
        return {'success': False, 'error': 'No encoding found'}
    
    encoding = new_spec['encoding']
    color_field = encoding.get('color', {}).get('field')
    
    if not color_field:
        return {'success': False, 'error': 'Cannot find color field for sorting'}
    
    # 设置排序方式
    if method == "sum":
        sort_op = "sum"
    elif method == "mean":
        sort_op = "mean"
    elif method == "max":
        sort_op = "max"
    else:
        sort_op = "sum"
    
    # 对行进行排序（Y轴）
    if cluster_rows and 'y' in encoding:
        encoding['y']['sort'] = {
            'op': sort_op,
            'field': color_field,
            'order': 'descending'
        }
    
    # 对列进行排序（X轴）
    if cluster_cols and 'x' in encoding:
        encoding['x']['sort'] = {
            'op': sort_op,
            'field': color_field,
            'order': 'descending'
        }
    
    return {
        'success': True,
        'operation': 'cluster_rows_cols',
        'vega_spec': new_spec,
        'message': f'Sorted rows={cluster_rows}, cols={cluster_cols} by {method}'
    }


def select_submatrix(vega_spec: Dict, x_values: List = None, 
                    y_values: List = None) -> Dict[str, Any]:
    """选择子矩阵"""
    if not x_values and not y_values:
        return {'success': False, 'error': 'Must specify x_values or y_values'}
    
    new_spec = copy.deepcopy(vega_spec)
    
    # 月份名称到数字的映射 (Vega month 从 0 开始: 0=Jan, 11=Dec)
    MONTH_MAP = {
        "Jan": 0, "Feb": 1, "Mar": 2, "Apr": 3,
        "May": 4, "Jun": 5, "Jul": 6, "Aug": 7,
        "Sep": 8, "Oct": 9, "Nov": 10, "Dec": 11,
        "January": 0, "February": 1, "March": 2, "April": 3,
        "May": 4, "June": 5, "July": 6, "August": 7,
        "September": 8, "October": 9, "November": 10, "December": 11
    }
    
    encoding = new_spec.get('encoding', {})
    x_encoding = encoding.get('x', {})
    y_encoding = encoding.get('y', {})
    
    x_field = x_encoding.get('field')
    y_field = y_encoding.get('field')
    x_timeunit = x_encoding.get('timeUnit')
    y_timeunit = y_encoding.get('timeUnit')
    
    if 'transform' not in new_spec:
        new_spec['transform'] = []
    
    filters = []
    
    # 处理 X 轴过滤
    if x_values and x_field:
        if x_timeunit:
            # 有 timeUnit，使用 Vega 表达式函数
            if x_timeunit == 'date':
                # 提取日期（1-31）
                x_nums = ','.join([str(int(v)) for v in x_values])
                filters.append(f'indexof([{x_nums}], date(datum.{x_field})) >= 0')
            elif x_timeunit == 'month':
                # 提取月份，尝试转换月份名称为数字
                x_months = []
                for v in x_values:
                    if v in MONTH_MAP:
                        x_months.append(str(MONTH_MAP[v]))
                    else:
                        try:
                            x_months.append(str(int(v)))
                        except:
                            x_months.append(f'"{v}"')
                x_str = ','.join(x_months)
                filters.append(f'indexof([{x_str}], month(datum.{x_field})) >= 0')
            elif x_timeunit == 'year':
                x_nums = ','.join([str(int(v)) for v in x_values])
                filters.append(f'indexof([{x_nums}], year(datum.{x_field})) >= 0')
            else:
                # 其他 timeUnit，直接使用函数名
                x_str = ','.join([f'"{v}"' for v in x_values])
                filters.append(f'indexof([{x_str}], {x_timeunit}(datum.{x_field})) >= 0')
        else:
            # 没有 timeUnit，直接匹配字段值
            x_str = ','.join([f'"{v}"' for v in x_values])
            filters.append(f'indexof([{x_str}], datum.{x_field}) >= 0')
    
    # 处理 Y 轴过滤
    if y_values and y_field:
        if y_timeunit:
            # 有 timeUnit，使用 Vega 表达式函数
            if y_timeunit == 'date':
                y_nums = ','.join([str(int(v)) for v in y_values])
                filters.append(f'indexof([{y_nums}], date(datum.{y_field})) >= 0')
            elif y_timeunit == 'month':
                # 提取月份，尝试转换月份名称为数字
                y_months = []
                for v in y_values:
                    if v in MONTH_MAP:
                        y_months.append(str(MONTH_MAP[v]))
                    else:
                        try:
                            y_months.append(str(int(v)))
                        except:
                            y_months.append(f'"{v}"')
                y_str = ','.join(y_months)
                filters.append(f'indexof([{y_str}], month(datum.{y_field})) >= 0')
            elif y_timeunit == 'year':
                y_nums = ','.join([str(int(v)) for v in y_values])
                filters.append(f'indexof([{y_nums}], year(datum.{y_field})) >= 0')
            else:
                # 其他 timeUnit，直接使用函数名
                y_str = ','.join([f'"{v}"' for v in y_values])
                filters.append(f'indexof([{y_str}], {y_timeunit}(datum.{y_field})) >= 0')
        else:
            # 没有 timeUnit，直接匹配字段值
            y_str = ','.join([f'"{v}"' for v in y_values])
            filters.append(f'indexof([{y_str}], datum.{y_field}) >= 0')
    
    if filters:
        new_spec['transform'].append({
            'filter': ' && '.join(filters)
        })
    
    return {
        'success': True,
        'operation': 'select_submatrix',
        'vega_spec': new_spec,
        'message': f'Selected submatrix with {len(x_values) if x_values else "all"} cols, {len(y_values) if y_values else "all"} rows'
    }


__all__ = [
    'adjust_color_scale',
    'filter_cells',
    'highlight_region',
    'cluster_rows_cols',
    'select_submatrix'
]
