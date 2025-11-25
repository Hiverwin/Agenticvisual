"""
工具注册器（简化版 - 使用 vega_spec 而非 view_id）
"""

from typing import Dict, List, Callable, Any
from config.chart_types import ChartType

from . import common
from . import bar_chart_tools
from . import line_chart_tools
from . import scatter_plot_tools
from . import parallel_coordinates_tools
from . import heatmap_tools
from . import sankey_tools


class ToolRegistry:
    """工具注册表类"""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._chart_tools: Dict[ChartType, List[str]] = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """注册所有工具"""
        
        # 通用工具
        common_tools = {
            'get_data_summary': {
                'function': common.get_data_summary,
                'category': 'perception',
                'description': '获取数据统计摘要',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'scope': {'type': 'str', 'required': False, 'default': 'all'}
                }
            },
            'get_tooltip_data': {
                'function': common.get_tooltip_data,
                'category': 'perception',
                'description': '获取工具提示数据',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'position': {'type': 'list', 'required': True}
                }
            },
            'zoom': {
                'function': common.zoom,
                'category': 'action',
                'description': '缩放到指定区域',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'area': {'type': 'list', 'required': True}
                }
            },
            'filter': {
                'function': common.filter,
                'category': 'action',
                'description': '按维度筛选数据',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'dimension': {'type': 'str', 'required': True},
                    'range': {'type': 'list', 'required': True}
                }
            },
            'brush': {
                'function': common.brush,
                'category': 'action',
                'description': '刷选区域',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'area': {'type': 'list', 'required': True}
                }
            },
            'change_encoding': {
                'function': common.change_encoding,
                'category': 'action',
                'description': '更改编码映射',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'channel': {'type': 'str', 'required': True},
                    'field_name': {'type': 'str', 'required': True}
                }
            },
            'highlight': {
                'function': common.highlight,
                'category': 'action',
                'description': '高亮类别',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'category': {'type': 'any', 'required': True}
                }
            },
            'render_chart': {
                'function': common.render_chart,
                'category': 'action',
                'description': '渲染图表',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True}
                }
            }
        }
        
        # 柱状图工具
        bar_chart_tools_dict = {
            'sort_bars': {
                'function': bar_chart_tools.sort_bars,
                'category': 'action',
                'description': '按值排序条形',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'order': {'type': 'str', 'required': False, 'default': 'descending'}
                }
            },
            'filter_categories': {
                'function': bar_chart_tools.filter_categories,
                'category': 'action',
                'description': '筛选特定类别',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'categories': {'type': 'list', 'required': True}
                }
            },
            'highlight_top_n': {
                'function': bar_chart_tools.highlight_top_n,
                'category': 'action',
                'description': '高亮前N个条形',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'n': {'type': 'int', 'required': False, 'default': 2},
                    'order': {'type': 'str', 'required': False, 'default': 'descending'}
                }
            },
            'compare_groups': {
                'function': bar_chart_tools.compare_groups,
                'category': 'analysis',
                'description': '组间对比',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'group_field': {'type': 'str', 'required': True}
                }
            }
        }
        
        # 折线图工具
        line_chart_tools_dict = {
            'zoom_time_range': {
                'function': line_chart_tools.zoom_time_range,
                'category': 'action',
                'description': '缩放时间范围',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'start': {'type': 'str', 'required': True},
                    'end': {'type': 'str', 'required': True}
                }
            },
            'highlight_trend': {
                'function': line_chart_tools.highlight_trend,
                'category': 'action',
                'description': '高亮趋势',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'trend_type': {'type': 'str', 'required': False, 'default': 'increasing'}
                }
            },
            'compare_series': {
                'function': line_chart_tools.compare_series,
                'category': 'analysis',
                'description': '对比多条线',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'series_field': {'type': 'str', 'required': True}
                }
            },
            'detect_anomalies': {
                'function': line_chart_tools.detect_anomalies,
                'category': 'analysis',
                'description': '检测异常点',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'threshold': {'type': 'float', 'required': False, 'default': 2.0}
                }
            }
        }
        
        # 散点图工具
        scatter_tools = {
            'select_region': {
                'function': scatter_plot_tools.select_region,
                'category': 'action',
                'description': '选择区域',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'x_range': {'type': 'tuple', 'required': True},
                    'y_range': {'type': 'tuple', 'required': True}
                }
            },
            'identify_clusters': {
                'function': scatter_plot_tools.identify_clusters,
                'category': 'analysis',
                'description': '识别聚类',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'n_clusters': {'type': 'int', 'required': False, 'default': 3},
                    'method': {'type': 'str', 'required': False, 'default': 'kmeans'}
                }
            },
            'calculate_correlation': {
                'function': scatter_plot_tools.calculate_correlation,
                'category': 'analysis',
                'description': '计算相关性',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'method': {'type': 'str', 'required': False, 'default': 'pearson'}
                }
            },
            'zoom_dense_area': {
                'function': scatter_plot_tools.zoom_dense_area,
                'category': 'action',
                'description': '放大密集区域',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'x_range': {'type': 'tuple', 'required': True},
                    'y_range': {'type': 'tuple', 'required': True}
                }
            }
        }
        
        # 热力图工具
        heatmap_tools_dict = {
            'adjust_color_scale': {
                'function': heatmap_tools.adjust_color_scale,
                'category': 'action',
                'description': '调整颜色比例',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'scheme': {'type': 'str', 'required': False, 'default': 'viridis'}
                }
            },
            'filter_cells': {
                'function': heatmap_tools.filter_cells,
                'category': 'action',
                'description': '筛选单元格',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'min_value': {'type': 'float', 'required': True},
                    'max_value': {'type': 'float', 'required': True}
                }
            },
            'highlight_region': {
                'function': heatmap_tools.highlight_region,
                'category': 'action',
                'description': '高亮区域',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'x_values': {'type': 'list', 'required': True},
                    'y_values': {'type': 'list', 'required': True}
                }
            },
            'cluster_rows_cols': {
                'function': heatmap_tools.cluster_rows_cols,
                'category': 'action',
                'description': '对行列进行聚类排序',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'cluster_rows': {'type': 'bool', 'required': False, 'default': True},
                    'cluster_cols': {'type': 'bool', 'required': False, 'default': True},
                    'method': {'type': 'str', 'required': False, 'default': 'sum'}
                }
            },
            'select_submatrix': {
                'function': heatmap_tools.select_submatrix,
                'category': 'action',
                'description': '选择子矩阵',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'x_values': {'type': 'list', 'required': False},
                    'y_values': {'type': 'list', 'required': False}
                }
            }
        }
        
        # 平行坐标图工具
        parallel_coords_tools_dict = {
            'filter_dimension': {
                'function': parallel_coordinates_tools.filter_dimension,
                'category': 'action',
                'description': '按维度筛选',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'dimension': {'type': 'str', 'required': True},
                    'range': {'type': 'list', 'required': True}
                }
            },
            'highlight_cluster': {
                'function': parallel_coordinates_tools.highlight_cluster,
                'category': 'action',
                'description': '高亮聚类',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'cluster_id': {'type': 'int', 'required': True}
                }
            },
            'reorder_dimensions': {
                'function': parallel_coordinates_tools.reorder_dimensions,
                'category': 'action',
                'description': '重新排序维度',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'dimension_order': {'type': 'list', 'required': True}
                }
            }
        }
        
        # 桑基图工具
        sankey_tools_dict = {
            'filter_flow': {
                'function': sankey_tools.filter_flow,
                'category': 'action',
                'description': '筛选流量',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'min_value': {'type': 'float', 'required': True}
                }
            },
            'highlight_path': {
                'function': sankey_tools.highlight_path,
                'category': 'action',
                'description': '高亮路径',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'source': {'type': 'str', 'required': True},
                    'target': {'type': 'str', 'required': True}
                }
            },
            'trace_node': {
                'function': sankey_tools.trace_node,
                'category': 'action',
                'description': '追踪节点',
                'params': {
                    'vega_spec': {'type': 'dict', 'required': True},
                    'node_name': {'type': 'str', 'required': True}
                }
            }
        }
        
        # 注册所有工具
        for name, info in common_tools.items():
            self._tools[name] = info
        
        for name, info in bar_chart_tools_dict.items():
            self._tools[name] = info
        
        for name, info in line_chart_tools_dict.items():
            self._tools[name] = info
        
        for name, info in scatter_tools.items():
            self._tools[name] = info
        
        for name, info in heatmap_tools_dict.items():
            self._tools[name] = info
        
        for name, info in parallel_coords_tools_dict.items():
            self._tools[name] = info
        
        for name, info in sankey_tools_dict.items():
            self._tools[name] = info
        
        # 映射图表类型到工具
        self._chart_tools[ChartType.BAR_CHART] = list(bar_chart_tools_dict.keys()) + list(common_tools.keys())
        self._chart_tools[ChartType.LINE_CHART] = list(line_chart_tools_dict.keys()) + list(common_tools.keys())
        self._chart_tools[ChartType.SCATTER_PLOT] = list(scatter_tools.keys()) + list(common_tools.keys())
        self._chart_tools[ChartType.HEATMAP] = list(heatmap_tools_dict.keys()) + list(common_tools.keys())
        self._chart_tools[ChartType.PARALLEL_COORDINATES] = list(parallel_coords_tools_dict.keys()) + list(common_tools.keys())
        self._chart_tools[ChartType.SANKEY_DIAGRAM] = list(sankey_tools_dict.keys()) + list(common_tools.keys())
    
    def get_tool(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        return self._tools.get(tool_name)
    
    def list_tools_for_chart(self, chart_type: ChartType) -> List[str]:
        """列出指定图表类型可用的工具"""
        return self._chart_tools.get(chart_type, list(self._tools.keys()))
    
    def list_all_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())


tool_registry = ToolRegistry()
