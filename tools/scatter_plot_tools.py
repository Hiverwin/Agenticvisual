"""
散点图专用工具（简化版 - 直接使用 vega_spec）
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import copy
from sklearn.cluster import KMeans
from scipy.stats import pearsonr, spearmanr


def select_region(vega_spec: Dict, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> Dict[str, Any]:
    """选择特定区域的点"""
    new_spec = copy.deepcopy(vega_spec)
    
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {'success': False, 'error': 'Cannot find required fields'}
    
    data = new_spec.get('data', {}).get('values', [])
    selected_count = sum(1 for row in data if 
                         row.get(x_field) is not None and row.get(y_field) is not None and
                         x_range[0] <= row[x_field] <= x_range[1] and
                         y_range[0] <= row[y_field] <= y_range[1])
    
    # 添加高亮
    new_spec['encoding']['opacity'] = {
        'condition': {
            'test': (f'datum.{x_field} >= {x_range[0]} && datum.{x_field} <= {x_range[1]} && '
                    f'datum.{y_field} >= {y_range[0]} && datum.{y_field} <= {y_range[1]}'),
            'value': 1.0
        },
        'value': 0.2
    }
    
    return {
        'success': True,
        'operation': 'select_region',
        'vega_spec': new_spec,
        'selected_count': selected_count,
        'message': f'Selected {selected_count} points'
    }


def identify_clusters(vega_spec: Dict, n_clusters: int = 3, method: str = "kmeans") -> Dict[str, Any]:
    """识别数据聚类"""
    new_spec = copy.deepcopy(vega_spec)
    
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {'success': False, 'error': 'Cannot find required fields'}
    
    data = new_spec.get('data', {}).get('values', [])
    
    points = []
    valid_indices = []
    for i, row in enumerate(data):
        if row.get(x_field) is not None and row.get(y_field) is not None:
            points.append([row[x_field], row[y_field]])
            valid_indices.append(i)
    
    if len(points) < n_clusters:
        return {'success': False, 'error': f'Not enough points for {n_clusters} clusters'}
    
    points_array = np.array(points)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(points_array)
    centers = kmeans.cluster_centers_
    
    cluster_field = f'cluster_{n_clusters}'
    for i, label in enumerate(labels):
        data[valid_indices[i]][cluster_field] = int(label)
    
    new_spec['data']['values'] = data
    new_spec['encoding']['color'] = {
        'field': cluster_field,
        'type': 'nominal',
        'scale': {'scheme': 'category10'},
        'legend': {'title': 'Cluster'}
    }
    
    cluster_stats = []
    for i in range(n_clusters):
        cluster_points = points_array[labels == i]
        cluster_stats.append({
            'cluster_id': i,
            'size': len(cluster_points),
            'center': centers[i].tolist()
        })
    
    return {
        'success': True,
        'operation': 'identify_clusters',
        'vega_spec': new_spec,
        'n_clusters': n_clusters,
        'cluster_statistics': cluster_stats,
        'message': f'Identified {n_clusters} clusters'
    }


def calculate_correlation(vega_spec: Dict, method: str = "pearson") -> Dict[str, Any]:
    """计算相关系数"""
    x_field = vega_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = vega_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {'success': False, 'error': 'Cannot find required fields'}
    
    data = vega_spec.get('data', {}).get('values', [])
    
    x_values = [row[x_field] for row in data if row.get(x_field) is not None and row.get(y_field) is not None]
    y_values = [row[y_field] for row in data if row.get(x_field) is not None and row.get(y_field) is not None]
    
    if len(x_values) < 2:
        return {'success': False, 'error': 'Not enough data points'}
    
    x_array = np.array(x_values)
    y_array = np.array(y_values)
    
    if method == "pearson":
        correlation, p_value = pearsonr(x_array, y_array)
    elif method == "spearman":
        correlation, p_value = spearmanr(x_array, y_array)
    else:
        return {'success': False, 'error': f'Unsupported method: {method}'}
    
    strength = "strong" if abs(correlation) >= 0.7 else "moderate" if abs(correlation) >= 0.4 else "weak"
    direction = "positive" if correlation > 0 else "negative"
    
    return {
        'success': True,
        'operation': 'calculate_correlation',
        'method': method,
        'correlation_coefficient': float(correlation),
        'p_value': float(p_value),
        'strength': strength,
        'direction': direction,
        'message': f'{method} correlation: {correlation:.3f} ({strength} {direction})'
    }


def zoom_dense_area(vega_spec: Dict, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> Dict[str, Any]:
    """Zooms the specified view to a particular area by filtering data and adjusting axis scales.
    
    This focuses the visualization on a specific rectangular region.
    
    Args:
        vega_spec: The Vega-Lite specification
        x_range: Tuple of (min, max) for x-axis range
        y_range: Tuple of (min, max) for y-axis range
        
    Returns:
        Dict containing success status, filtered vega_spec, and statistics
    """
    new_spec = copy.deepcopy(vega_spec)
    
    # Get field names
    x_field = new_spec.get('encoding', {}).get('x', {}).get('field')
    y_field = new_spec.get('encoding', {}).get('y', {}).get('field')
    
    if not x_field or not y_field:
        return {'success': False, 'error': 'Cannot find required x or y fields'}
    
    # Get original data
    data = new_spec.get('data', {}).get('values', [])
    if not data:
        return {'success': False, 'error': 'No data found in specification'}
    
    original_count = len(data)
    
    # Filter data: only keep points within the specified range
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
            'filtered_count': 0
        }
    
    # Update data in spec
    new_spec['data']['values'] = filtered_data
    
    # Adjust axis scales to the specified range
    if 'encoding' not in new_spec:
        new_spec['encoding'] = {}
    
    for axis, vals in [('x', x_range), ('y', y_range)]:
        if axis not in new_spec['encoding']:
            new_spec['encoding'][axis] = {}
        if 'scale' not in new_spec['encoding'][axis]:
            new_spec['encoding'][axis]['scale'] = {}
        new_spec['encoding'][axis]['scale']['domain'] = [vals[0], vals[1]]
    
    return {
        'success': True,
        'operation': 'zoom_dense_area',
        'vega_spec': new_spec,
        'original_count': original_count,
        'filtered_count': filtered_count,
        'zoom_range': {
            'x': list(x_range),
            'y': list(y_range)
        },
        'message': f'Zoomed to dense area: showing {filtered_count} out of {original_count} points ({filtered_count/original_count*100:.1f}%)'
    }


__all__ = [
    'select_region',
    'identify_clusters',
    'calculate_correlation',
    'zoom_dense_area'
]
