# Interactive VA Benchmark - 轻量版

这是一个轻量化的benchmark实现，用于评估VLM在交互式可视化分析中的表现。

## 📂 文件结构

```
benchmark/
├── data/
│   └── scatter_user_behavior.json    # 散点图数据（用户行为分析）
├── tasks/
│   └── scatter_clustering_001.json   # 任务定义+Ground Truth
├── results/                           # 评估结果输出目录
├── evaluator.py                       # 评估器（4个维度）
└── README.md                          # 本文件

test_benchmark.py                      # 测试脚本
```

## 🎯 任务说明

**任务ID**: `scatter_clustering_001`  
**类型**: 散点图 - 用户行为分群  
**难度**: Medium  
**交互必要性**: Critical（不交互无法发现两个隐藏子群）

**场景**: App用户使用时长 vs 活跃度分析  
**查询**: "请探索这个用户数据，分析使用时长和活跃度之间的关系，并发现是否存在不同的用户群体特征。"

**数据特点**:
- 30个用户数据点
- 包含2个明显分离的子群：
  - 新手用户：低时长(15-25h)、低活跃度(25-35分)，15个用户
  - 高价值用户：高时长(47-58h)、高活跃度(67-78分)，15个用户

## 📊 评估维度

### 1. 洞察质量 (40%权重)
- **Recall**: 发现了多少ground truth洞察
- **Precision**: 发现的洞察有多少是真实的
- **Depth**: 洞察的层次深度

**Critical洞察**（必须发现）:
1. 用户明显分为两个群体
2. 第一组为新手用户（低时长低活跃）
3. 第二组为高价值用户（高时长高活跃）

### 2. 探索路径 (25%权重)
- **里程碑完成度**: 是否达成关键探索目标
- **步数效率**: 实际步数vs最优步数

**必达里程碑**:
1. 识别数据中存在两个分离的群体
2. 观察并描述两个群体的特征

**最优步数**: 3步  
**可接受范围**: 2-6步

### 3. 工具调用 (20%权重)
- **工具选择**: 是否使用必需工具
- **参数正确性**: 参数是否有效

**必需工具**:
- `identify_clusters` (识别聚类)

**推荐工具**:
- `zoom_dense_area` (放大密集区域)

**不适用工具**:
- `sort_bars`, `filter_categories`, `highlight_trend`

### 4. 效率 (15%权重)
- **步数效率**: 是否在合理步数内完成
- **冗余检测**: 是否有重复操作

## 🚀 使用方法

### 方法1: 手动运行（推荐）

由于环境限制，建议手动运行：

1. **启动系统**:
```bash
python3 main.py
```

2. **在交互界面中**:
   - 选择图表类型: `5` (scatter_plot)
   - 输入spec路径: `benchmark/data/scatter_user_behavior.json`
   - 选择分析模式: `2` (自主探索模式)
   - 输入查询: `请探索这个用户数据，分析使用时长和活跃度之间的关系，并发现是否存在不同的用户群体特征。`
   - 等待系统完成探索（约3-5轮）

3. **记录结果文件路径**:
   - 在 `results/` 目录下
   - 文件名类似: `exploration_xxx_20251124_xxxxxx.json`

4. **运行评估**:
```bash
python3 test_benchmark.py results/exploration_xxx_20251124_xxxxxx.json
```

### 方法2: 自动化运行（需要依赖）

如果环境完整，可以使用：

```bash
python3 run_benchmark.py
```

这会自动：
1. 加载任务
2. 执行系统
3. 评估打分
4. 保存结果

## 📋 评估示例

```
============================================================
Benchmark评估报告 - scatter_clustering_001
============================================================

📊 总分: 78.5/100

📈 各维度得分:
  1. 洞察质量 (40%权重): 85.0/100
  2. 探索路径 (25%权重): 80.0/100
  3. 工具调用 (20%权重): 70.0/100
  4. 效率评估 (15%权重): 75.0/100

📋 探索详情:
  - 探索轮次: 4
  - 发现洞察: 8个
  - 使用工具: identify_clusters, zoom_dense_area, calculate_correlation

总体评价: ✅ 良好 (Good)
============================================================
```

## 🎯 评分标准

- **85+**: 🌟 优秀 (Excellent)
- **70-84**: ✅ 良好 (Good)
- **60-69**: ⚠️ 及格 (Pass)
- **<60**: ❌ 不及格 (Fail)

## 🔧 Ground Truth说明

Ground Truth包含：
- **洞察质量**: 3个critical insights，必须通过交互发现
- **探索路径**: 2个必达里程碑，最优3步
- **工具调用**: 必须使用identify_clusters
- **效率**: 最优3步，最多8步

详见: `benchmark/tasks/scatter_clustering_001.json`

## 💡 预期表现

一个表现良好的VLM agent应该：
1. ✅ 使用 `identify_clusters(n=2)` 识别两个子群
2. ✅ 使用 `zoom_dense_area` 分别观察两个子群的特征
3. ✅ 发现并描述两个群体的差异（时长、活跃度范围）
4. ✅ 在3-4步内完成探索

## 📝 注意事项

1. 这是**轻量化**实现，评估方法简化：
   - 洞察匹配使用关键词（非语义相似度）
   - 参数验证只做基本检查
   - 冗余检测只检查连续重复

2. 任务是**Critical交互必要性**：
   - 静态分析无法识别两个子群的边界
   - 必须通过zoom+cluster才能发现详细特征

3. 数据是**合成数据**：
   - 两个子群分离明显，便于评估
   - 真实场景可能更复杂

## 🔍 调试

查看详细的评估结果：
```bash
cat benchmark/results/scatter_clustering_001_evaluation.json
```

查看agent的完整输出：
```bash
cat results/exploration_xxx_20251124_xxxxxx.txt
```

---

**Created**: 2025-11-24  
**Version**: 1.0  
**Status**: ✅ Ready to use

