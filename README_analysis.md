# requests.jsonl数据分析工具

这个工具用于分析multi-round-qa.py生成的requests.jsonl文件，计算kv_cache_tokens和new_tokens的统计指标，以评估多轮对话中token使用的分布情况和差异性。

## 功能特点

- 按组分析请求数据，支持自定义组大小
- 计算标准统计指标：均值、中位数、标准差、方差、最大值、最小值、范围
- 计算特殊分布指标：Gini系数、变异系数(CV)
- 生成可视化图表：直方图、散点图、条形图
- 提供数据解释和建议

## 使用方法

1. 运行multi-round-qa.py生成requests.jsonl文件
2. 运行analyze_requests.py分析数据

基本用法:
```bash
python analyze_requests.py
```

自定义参数:
```bash
python analyze_requests.py --file path/to/requests.jsonl --group-size 20 --output-dir results
```

## 参数说明

- `--file`: 指定要分析的JSON文件路径，默认为当前目录下的requests.jsonl
- `--group-size`: 指定每组包含的请求数量，默认为10
- `--output-dir`: 指定结果输出目录，默认为analysis_results

## 输出结果

1. **CSV文件** (request_stats.csv): 包含所有统计指标的详细数据表格
2. **可视化图表**:
   - kv_cache_tokens_histogram.png: KV缓存Tokens分布直方图
   - new_tokens_histogram.png: 新Tokens分布直方图
   - tokens_scatter.png: KV缓存Tokens vs 新Tokens散点图
   - gini_by_group.png: 各组Gini系数对比条形图
   - cv_by_group.png: 各组变异系数对比条形图
3. **控制台输出**: 全局统计信息和结果解释

## 统计指标说明

### 基础统计指标
- **均值**: 平均值，代表中心趋势
- **中位数**: 位于中间的数值，不受极端值影响
- **标准差**: 数据分散程度的度量
- **方差**: 标准差的平方，衡量数据波动性
- **范围**: 最大值与最小值之差，表示数据跨度

### 特殊分布指标
- **Gini系数**: 衡量分布不平等程度，0表示完全平等，1表示完全不平等
- **变异系数(CV)**: 标准差与均值之比，用于比较不同量纲的分散程度

## 数据解释示例

Gini系数解释:
- < 0.3: 分布相对均匀
- 0.3-0.5: 分布中等不均匀
- > 0.5: 分布很不均匀

变异系数解释:
- < 0.5: 数据相对稳定
- 0.5-1.0: 数据波动较大
- > 1.0: 数据波动非常大

## 依赖项

- Python 3.7+
- numpy
- pandas
- matplotlib
- scipy

## 安装依赖

```bash
pip install numpy pandas matplotlib scipy
``` 