"""
折线图专用工具（简化版 - 使用 vega_spec）
"""

from typing import List, Dict, Any, Tuple, Optional
import copy


def _get_time_field(vega_spec: Dict) -> Optional[str]:
    """获取时间字段（支持 layer 结构）"""
    # 检查是否有 layer 结构
    if 'layer' in vega_spec and len(vega_spec['layer']) > 0:
        encoding = vega_spec['layer'][0].get('encoding', {})
    else:
        encoding = vega_spec.get('encoding', {})
    
    # 时间字段通常在 x 轴，但也可能在 y 轴
    x_encoding = encoding.get('x', {})
    y_encoding = encoding.get('y', {})
    
    if x_encoding.get('type') == 'temporal':
        return x_encoding.get('field')
    elif y_encoding.get('type') == 'temporal':
        return y_encoding.get('field')
    
    # 如果类型未指定，尝试从字段推断（通常时间在 x 轴）
    return x_encoding.get('field') or y_encoding.get('field')


def zoom_time_range(vega_spec: Dict, start: str, end: str) -> Dict[str, Any]:
    """缩放时间范围 - 放大视图到特定时间段（不删除数据）"""
    new_spec = copy.deepcopy(vega_spec)
    
    # 获取时间字段名（支持 layer 结构）
    time_field = _get_time_field(new_spec)
    
    if not time_field:
        return {
            'success': False,
            'error': 'Cannot find time field'
        }
    
    # 确定时间字段在哪个轴上
    if 'layer' in new_spec and len(new_spec['layer']) > 0:
        encoding = new_spec['layer'][0].get('encoding', {})
    else:
        encoding = new_spec.get('encoding', {})
    
    x_field = encoding.get('x', {}).get('field')
    time_axis = 'x' if x_field == time_field else 'y'
    
    # 直接使用VLM提供的日期格式，不做任何转换
    # VLM应该根据提示词观察原始数据格式并返回一致的格式
    if 'layer' in new_spec and len(new_spec['layer']) > 0:
        layer_encoding = new_spec['layer'][0].get('encoding', {})
        if time_axis not in layer_encoding:
            layer_encoding[time_axis] = {}
        if 'scale' not in layer_encoding[time_axis]:
            layer_encoding[time_axis]['scale'] = {}
        layer_encoding[time_axis]['scale']['domain'] = [start, end]
    else:
        if 'encoding' not in new_spec:
            new_spec['encoding'] = {}
        if time_axis not in new_spec['encoding']:
            new_spec['encoding'][time_axis] = {}
        if 'scale' not in new_spec['encoding'][time_axis]:
            new_spec['encoding'][time_axis]['scale'] = {}
        new_spec['encoding'][time_axis]['scale']['domain'] = [start, end]
    
    # 确保 mark 有 clip: true，裁剪超出范围的点
    if 'layer' in new_spec:
        for layer in new_spec['layer']:
            if 'mark' in layer:
                if isinstance(layer['mark'], dict):
                    layer['mark']['clip'] = True
                else:
                    layer['mark'] = {'type': layer['mark'], 'clip': True}
    else:
        if 'mark' in new_spec:
            if isinstance(new_spec['mark'], dict):
                new_spec['mark']['clip'] = True
            else:
                new_spec['mark'] = {'type': new_spec['mark'], 'clip': True}
    
    return {
        'success': True,
        'operation': 'zoom_time_range',
        'vega_spec': new_spec,
        'message': f'Zoomed to time range: {start} to {end}',
        'details': [f'View zoomed to show time range between {start} and {end}']
    }


def highlight_trend(vega_spec: Dict, trend_type: str = "increasing") -> Dict[str, Any]:
    """高亮趋势 - 添加回归趋势线"""
    new_spec = copy.deepcopy(vega_spec)
    
    # 获取 x 和 y 字段（支持 layer 结构）
    if 'layer' in new_spec and len(new_spec['layer']) > 0:
        encoding = new_spec['layer'][0].get('encoding', {})
    else:
        encoding = new_spec.get('encoding', {})
    
    y_field = encoding.get('y', {}).get('field')
    x_field = encoding.get('x', {}).get('field')
    
    if not y_field or not x_field:
        return {
            'success': False,
            'error': 'Cannot find x or y field for trend line'
        }
    
    # 如果原规范没有 layer，转换为 layer 结构
    if 'layer' not in new_spec:
        original_layer = copy.deepcopy(new_spec)
        # 移除顶层的 mark 和 encoding，因为它们现在在 layer 中
        for key in ['mark', 'encoding']:
            if key in original_layer:
                del original_layer[key]
        
        new_spec = original_layer
        new_spec['layer'] = [{
            'mark': vega_spec.get('mark', 'line'),
            'encoding': vega_spec.get('encoding', {})
        }]
    
    # 添加趋势线图层
    new_spec['layer'].append({
        'mark': {
            'type': 'line',
            'color': 'red',
            'strokeDash': [5, 5],
            'strokeWidth': 2
        },
        'transform': [{
            'regression': y_field,
            'on': x_field
        }],
        'encoding': {
            'x': {'field': x_field, 'type': encoding['x'].get('type', 'temporal')},
            'y': {'field': y_field, 'type': encoding['y'].get('type', 'quantitative')}
        }
    })
    
    return {
        'success': True,
        'operation': 'highlight_trend',
        'vega_spec': new_spec,
        'message': f'Added {trend_type} regression trend line',
        'details': [f'Trend line shows overall {trend_type} pattern']
    }


def compare_series(vega_spec: Dict, series_field: str) -> Dict[str, Any]:
    """对比多条线 - 按指定字段区分不同系列并用颜色编码"""
    new_spec = copy.deepcopy(vega_spec)
    
    # 检查数据中是否存在该字段
    data = new_spec.get('data', {}).get('values', [])
    if data and series_field not in data[0]:
        return {
            'success': False,
            'error': f'Field "{series_field}" not found in data'
        }
    
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    # 如果已经有 color encoding，覆盖它
    new_spec['encoding']['color'] = {
        'field': series_field,
        'type': 'nominal',
        'legend': {'title': series_field}
    }
    
    # 确保有多条线的 detail encoding（如果没有的话）
    if 'detail' not in new_spec['encoding']:
        new_spec['encoding']['detail'] = {
        'field': series_field,
        'type': 'nominal'
    }
    
    return {
        'success': True,
        'operation': 'compare_series',
        'vega_spec': new_spec,
        'message': f'Comparing series by {series_field}',
        'details': [f'Each unique value in {series_field} is shown as a separate colored line']
    }


def detect_anomalies(vega_spec: Dict, threshold: float = 2.0) -> Dict[str, Any]:
    """检测异常点 - 检测并在视图中高亮标记异常数据点"""
    import numpy as np
    
    data = vega_spec.get('data', {}).get('values', [])
    
    # 获取字段（支持 layer 结构）
    if 'layer' in vega_spec and len(vega_spec['layer']) > 0:
        encoding = vega_spec['layer'][0].get('encoding', {})
    else:
        encoding = vega_spec.get('encoding', {})
    
    y_field = encoding.get('y', {}).get('field')
    x_field = encoding.get('x', {}).get('field')
    
    if not data or not y_field:
        return {'success': False, 'error': 'Missing data or y field'}
    
    values = [row.get(y_field) for row in data if row.get(y_field) is not None]
    
    if len(values) < 3:
        return {'success': False, 'error': 'Not enough data for anomaly detection'}
    
    # 计算统计特征
    mean = np.mean(values)
    std = np.std(values)
    
    # 识别异常点
    anomaly_data = []
    for row in data:
        val = row.get(y_field)
        if val is not None and abs(val - mean) > threshold * std:
            anomaly_data.append(row)
    
    new_spec = copy.deepcopy(vega_spec)
    
    # 如果检测到异常点，在视图中标记
    if anomaly_data:
        # 转换为 layer 结构
        if 'layer' not in new_spec:
            original_layer = copy.deepcopy(new_spec)
            for key in ['mark', 'encoding']:
                if key in original_layer:
                    del original_layer[key]
            
            new_spec = original_layer
            new_spec['layer'] = [{
                'mark': vega_spec.get('mark', 'line'),
                'encoding': vega_spec.get('encoding', {})
            }]
        
        # 添加异常点标记图层
        new_spec['layer'].append({
            'data': {'values': anomaly_data},
            'mark': {
                'type': 'point',
                'color': 'red',
                'size': 100,
                'filled': True
            },
            'encoding': {
                'x': {'field': x_field, 'type': encoding['x'].get('type', 'temporal')} if x_field else {},
                'y': {'field': y_field, 'type': encoding['y'].get('type', 'quantitative')},
                'tooltip': [
                    {'field': x_field, 'type': encoding['x'].get('type', 'temporal'), 'title': 'Time'} if x_field else {},
                    {'field': y_field, 'type': 'quantitative', 'title': 'Value (Anomaly)'}
                ]
            }
        })
    
    return {
        'success': True,
        'operation': 'detect_anomalies',
        'vega_spec': new_spec,
        'anomaly_count': len(anomaly_data),
        'anomalies': anomaly_data[:10],
        'message': f'Detected and highlighted {len(anomaly_data)} anomalies (threshold={threshold} std)',
        'details': [
            f'Mean: {mean:.2f}, Std: {std:.2f}',
            f'Anomalies are values beyond {threshold} standard deviations from mean',
            f'Anomalies marked with red points on the chart'
        ]
    }


__all__ = [
    'zoom_time_range',
    'highlight_trend',
    'compare_series',
    'detect_anomalies'
]
