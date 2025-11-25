# 导入路径问题修复说明

## 问题原因

当你在 `examples/` 目录下直接运行 Python 脚本时：
```bash
python examples/generic_vlm_usage.py
```

Python 会将 `examples/` 设为当前工作目录，但导入语句 `from tools.vlm_adapter import ...` 需要从项目根目录导入，因此会报错 `ModuleNotFoundError: No module named 'tools'`。

## 解决方案（3种方法）

### 方法1: 从项目根目录运行（推荐） ⭐

```bash
# 在项目根目录下运行
cd /path/to/visual-analysis-system-modified\ 3

# 使用 -m 选项运行模块
python -m examples.generic_vlm_usage
python -m examples.generic_vlm_benchmark
```

或者使用提供的便捷脚本：
```bash
# 运行使用示例
python run_examples.py usage

# 运行评估示例
python run_examples.py benchmark

# 运行所有示例
python run_examples.py all
```

### 方法2: 设置PYTHONPATH环境变量

```bash
# 临时设置
export PYTHONPATH=/path/to/visual-analysis-system-modified\ 3:$PYTHONPATH
python examples/generic_vlm_usage.py

# 或者一行命令
PYTHONPATH=/path/to/visual-analysis-system-modified\ 3 python examples/generic_vlm_usage.py
```

### 方法3: 使用修复后的脚本（已包含在代码中）

脚本中已添加路径修复代码：
```python
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

现在可以直接运行：
```bash
python examples/generic_vlm_usage.py
```

## 详细说明

### Python导入机制

Python导入模块时会在以下路径中查找：
1. 当前脚本所在目录
2. PYTHONPATH环境变量指定的目录
3. Python标准库目录
4. 第三方包目录

当你运行 `python examples/generic_vlm_usage.py` 时：
- 当前目录 = `examples/`
- Python找不到 `tools/` 目录（它在上一级）

### 解决方法对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 方法1: python -m | 官方推荐，最规范 | 需要记住-m选项 | 开发和生产 |
| 方法2: PYTHONPATH | 灵活，可全局设置 | 环境变量管理复杂 | 临时测试 |
| 方法3: sys.path修改 | 方便，自动处理 | 修改了运行时路径 | 独立脚本 |

## 推荐使用方式

### 日常使用
```bash
# 最简单：使用便捷脚本
python run_examples.py usage

# 或者使用 -m 选项
python -m examples.generic_vlm_usage
```

### 集成到其他项目
```python
# 在你的代码中
import sys
sys.path.insert(0, '/path/to/visual-analysis-system')

from tools.vlm_adapter import vlm_adapter
from tools.tool_executor import get_tool_executor
```

### IDE开发（如PyCharm、VSCode）
1. 将项目根目录设为"源代码根目录"
2. IDE会自动处理导入路径
3. 可以直接运行任何脚本

## 验证修复

运行以下命令验证所有功能正常：

```bash
# 测试1: 使用便捷脚本
python run_examples.py usage

# 测试2: 使用-m选项
python -m examples.generic_vlm_usage

# 测试3: 直接运行（已修复）
python examples/generic_vlm_usage.py

# 测试4: 从examples目录运行
cd examples
python generic_vlm_usage.py
cd ..
```

所有命令应该都能正常运行！

## 常见问题

### Q1: 为什么不用相对导入？
相对导入（如 `from ..tools import ...`）只能在包内使用，直接运行脚本时会报错。

### Q2: 可以安装为包吗？
可以！在项目根目录创建 `setup.py`：
```python
from setuptools import setup, find_packages

setup(
    name="visual-analysis-system",
    version="1.0.0",
    packages=find_packages(),
)
```

然后安装：
```bash
pip install -e .
```

之后可以在任何地方导入：
```python
from tools.vlm_adapter import vlm_adapter
```

### Q3: 如何在Jupyter Notebook中使用？
```python
import sys
sys.path.insert(0, '/path/to/visual-analysis-system')

# 然后正常导入
from tools.vlm_adapter import vlm_adapter
```

## 总结

✅ **推荐方式**：使用 `python run_examples.py usage`

✅ **备选方式**：使用 `python -m examples.generic_vlm_usage`

✅ **已修复**：所有脚本都已添加路径处理代码

现在所有运行方式都应该正常工作！
