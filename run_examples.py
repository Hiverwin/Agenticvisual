#!/usr/bin/env python3
"""
运行示例脚本的便捷工具
确保正确的Python路径设置
"""

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行VLM工具示例')
    parser.add_argument(
        'example',
        choices=['usage', 'benchmark', 'all'],
        help='要运行的示例: usage, benchmark, 或 all'
    )
    
    args = parser.parse_args()
    
    if args.example == 'usage' or args.example == 'all':
        print("=" * 60)
        print("运行: generic_vlm_usage.py")
        print("=" * 60)
        from examples import generic_vlm_usage
        generic_vlm_usage.main()
    
    if args.example == 'benchmark' or args.example == 'all':
        print("\n" + "=" * 60)
        print("运行: generic_vlm_benchmark.py")
        print("=" * 60)
        from examples import generic_vlm_benchmark
        generic_vlm_benchmark.main()

if __name__ == "__main__":
    main()
