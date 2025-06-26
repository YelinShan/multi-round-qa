#!/usr/bin/env python3
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import argparse
import os


def gini_coefficient(x):
    """计算Gini系数，确保结果在0-1之间"""
    # 确保没有负值
    x = np.array(x)
    if len(x) <= 1:
        return 0
    if np.all(x == 0):  # 如果所有值都为0，Gini系数为0
        return 0
    
    # 检测负值并提供警告
    if np.any(x < 0):
        print(f"Warning: Negative values detected in Gini calculation. Values: {x}")
        x = np.abs(x)  # 使用绝对值
    
    # 使用更稳定的Gini系数计算方法
    # 方法1：使用排序后的差异总和 (更稳定)
    x = np.sort(x)
    n = len(x)
    cumx = np.cumsum(x)
    # 通过lorenz曲线与平等线之间的面积计算
    return (n + 1 - 2 * np.sum(cumx) / np.sum(x)) / n
    
    # 如果上面的方法仍然产生负值，可以使用下面的方法2
    # 方法2：使用绝对差异的平均值
    # n = len(x)
    # mean_x = np.mean(x)
    # if mean_x == 0:
    #     return 0
    # abs_diffs = 0
    # for i in range(n):
    #    for j in range(n):
    #        abs_diffs += abs(x[i] - x[j])
    # return abs_diffs / (2 * n * n * mean_x)


def coefficient_of_variation(x):
    """计算变异系数(CV)"""
    x = np.array(x)
    if len(x) == 0 or np.mean(x) == 0:
        return 0
    return np.std(x) / np.mean(x)


def analyze_requests(file_path, group_size=10, output_dir=None):
    """分析requests.jsonl文件，计算每组数据的统计指标"""
    # 读取JSON文件
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"警告: 跳过无法解析的行: {line}")
    
    if not data:
        print("错误: 文件为空或格式不正确")
        return
    
    # 将数据转换为DataFrame
    df = pd.DataFrame(data)
    
    # 确保必要的字段存在
    required_fields = ['kv_cache_tokens', 'new_tokens']
    for field in required_fields:
        if field not in df.columns:
            print(f"错误: 缺少必要字段 '{field}'")
            return
    
    # 计算总组数
    total_groups = len(df) // group_size
    if len(df) % group_size != 0:
        total_groups += 1
    
    # 创建结果数据结构
    results = []
    
    # 按组处理数据
    for i in range(total_groups):
        start_idx = i * group_size
        end_idx = min((i + 1) * group_size, len(df))
        group_df = df.iloc[start_idx:end_idx]
        
        # 提取组内的kv_cache_tokens和new_tokens
        kv_cache_tokens = group_df['kv_cache_tokens'].values
        new_tokens = group_df['new_tokens'].values
        
        # 计算平均绝对差
        kv_cache_tokens_mad = np.mean(np.abs(kv_cache_tokens - np.median(kv_cache_tokens)))
        new_tokens_mad = np.mean(np.abs(new_tokens - np.median(new_tokens)))
        
        # 计算统计指标
        group_stats = {
            'group': i + 1,
            'size': len(group_df),
            'start_row': start_idx + 1,
            'end_row': end_idx,
            
            # KV缓存token统计
            'kv_cache_tokens_mean': np.mean(kv_cache_tokens),
            'kv_cache_tokens_median': np.median(kv_cache_tokens),
            'kv_cache_tokens_std': np.std(kv_cache_tokens),
            'kv_cache_tokens_var': np.var(kv_cache_tokens),
            'kv_cache_tokens_min': np.min(kv_cache_tokens),
            'kv_cache_tokens_max': np.max(kv_cache_tokens),
            'kv_cache_tokens_range': np.max(kv_cache_tokens) - np.min(kv_cache_tokens),
            'kv_cache_tokens_gini': gini_coefficient(kv_cache_tokens),
            'kv_cache_tokens_cv': coefficient_of_variation(kv_cache_tokens),
            'kv_cache_tokens_mad': kv_cache_tokens_mad,
            
            # 新token统计
            'new_tokens_mean': np.mean(new_tokens),
            'new_tokens_median': np.median(new_tokens),
            'new_tokens_std': np.std(new_tokens),
            'new_tokens_var': np.var(new_tokens),
            'new_tokens_min': np.min(new_tokens),
            'new_tokens_max': np.max(new_tokens),
            'new_tokens_range': np.max(new_tokens) - np.min(new_tokens),
            'new_tokens_gini': gini_coefficient(new_tokens),
            'new_tokens_cv': coefficient_of_variation(new_tokens),
            'new_tokens_mad': new_tokens_mad,
        }
        
        results.append(group_stats)
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(results)
    
    # 计算全局统计量
    global_stats = {
        'group': 'Global',
        'size': len(df),
        'start_row': 1,
        'end_row': len(df),
        
        'kv_cache_tokens_mean': df['kv_cache_tokens'].mean(),
        'kv_cache_tokens_median': df['kv_cache_tokens'].median(),
        'kv_cache_tokens_std': df['kv_cache_tokens'].std(),
        'kv_cache_tokens_var': df['kv_cache_tokens'].var(),
        'kv_cache_tokens_min': df['kv_cache_tokens'].min(),
        'kv_cache_tokens_max': df['kv_cache_tokens'].max(),
        'kv_cache_tokens_range': df['kv_cache_tokens'].max() - df['kv_cache_tokens'].min(),
        'kv_cache_tokens_gini': gini_coefficient(df['kv_cache_tokens'].values),
        'kv_cache_tokens_cv': coefficient_of_variation(df['kv_cache_tokens'].values),
        'kv_cache_tokens_mad': np.mean(np.abs(df['kv_cache_tokens'].values - np.median(df['kv_cache_tokens'].values))),
        
        'new_tokens_mean': df['new_tokens'].mean(),
        'new_tokens_median': df['new_tokens'].median(),
        'new_tokens_std': df['new_tokens'].std(),
        'new_tokens_var': df['new_tokens'].var(),
        'new_tokens_min': df['new_tokens'].min(),
        'new_tokens_max': df['new_tokens'].max(),
        'new_tokens_range': df['new_tokens'].max() - df['new_tokens'].min(),
        'new_tokens_gini': gini_coefficient(df['new_tokens'].values),
        'new_tokens_cv': coefficient_of_variation(df['new_tokens'].values),
        'new_tokens_mad': np.mean(np.abs(df['new_tokens'].values - np.median(df['new_tokens'].values))),
    }
    
    # 添加全局统计到结果
    results_df = pd.concat([results_df, pd.DataFrame([global_stats])], ignore_index=True)
    
    # 输出结果
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存统计数据为CSV
        csv_path = os.path.join(output_dir, 'request_stats.csv')
        results_df.to_csv(csv_path, index=False)
        print(f"Statistics saved to: {csv_path}")
        
        # 生成可视化图表
        create_visualizations(df, results_df, output_dir)
    
    return results_df


def create_visualizations(raw_df, stats_df, output_dir):
    """Create data visualizations"""
    # 1. KV cache tokens distribution histogram
    plt.figure(figsize=(10, 6))
    plt.hist(raw_df['kv_cache_tokens'], bins=100, alpha=0.7)
    plt.title('KV Cache Tokens Distribution')
    plt.xlabel('Number of KV Cache Tokens')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'kv_cache_tokens_histogram.png'))
    plt.close()
    
    # 2. New tokens distribution histogram
    plt.figure(figsize=(10, 6))
    plt.hist(raw_df['new_tokens'], bins=100, alpha=0.7)
    plt.title('New Tokens Distribution')
    plt.xlabel('Number of New Tokens')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'new_tokens_histogram.png'))
    plt.close()
    
    # 3. KV cache tokens vs new tokens scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(raw_df['kv_cache_tokens'], raw_df['new_tokens'], alpha=0.5)
    plt.title('KV Cache Tokens vs New Tokens')
    plt.xlabel('Number of KV Cache Tokens')
    plt.ylabel('Number of New Tokens')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'tokens_scatter.png'))
    plt.close()
    
    # 4. Gini coefficient comparison by group
    group_stats = stats_df[stats_df['group'] != 'Global']
    
    # Debug: Print Gini coefficients for inspection
    print("\nDebug - Gini coefficients by group:")
    for i, row in group_stats.iterrows():
        print(f"Group {row['group']}: KV Cache Tokens Gini = {row['kv_cache_tokens_gini']:.4f}, New Tokens Gini = {row['new_tokens_gini']:.4f}")
    
    plt.figure(figsize=(12, 6))
    x = np.arange(len(group_stats))
    width = 0.35
    
    # Ensure all values are positive (should already be handled by gini_coefficient)
    kv_gini_values = group_stats['kv_cache_tokens_gini'].values
    new_gini_values = group_stats['new_tokens_gini'].values
    
    # Debug: Print final values before plotting
    print("\nDebug - Final values for plotting:")
    print(f"KV Cache Tokens Gini values: {kv_gini_values}")
    print(f"New Tokens Gini values: {new_gini_values}")
    
    plt.bar(x - width/2, kv_gini_values, width, label='KV Cache Tokens')
    plt.bar(x + width/2, new_gini_values, width, label='New Tokens')
    plt.xlabel('Group Number')
    plt.ylabel('Gini Coefficient')
    plt.title('Gini Coefficient Comparison by Group')
    plt.xticks(x, group_stats['group'])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 添加参考线，标示不同的均匀性级别
    plt.axhline(y=0.2, color='g', linestyle='-', alpha=0.7, label='Very Uniform (0.2)')
    plt.axhline(y=0.4, color='y', linestyle='-', alpha=0.7, label='Relatively Uniform (0.4)')
    plt.axhline(y=0.6, color='orange', linestyle='-', alpha=0.7, label='Moderately Uneven (0.6)')
    plt.axhline(y=0.8, color='r', linestyle='-', alpha=0.7, label='Highly Uneven (0.8)')
    
    # 添加区域标签
    x_max = len(group_stats) - 0.5
    plt.text(x_max, 0.1, 'Very Uniform', ha='right', va='center', color='g', fontweight='bold')
    plt.text(x_max, 0.3, 'Relatively Uniform', ha='right', va='center', color='y', fontweight='bold')
    plt.text(x_max, 0.5, 'Moderately Uneven', ha='right', va='center', color='orange', fontweight='bold')
    plt.text(x_max, 0.7, 'Highly Uneven', ha='right', va='center', color='orange', fontweight='bold')
    plt.text(x_max, 0.9, 'Extremely Uneven', ha='right', va='center', color='r', fontweight='bold')
    
    # 更新图例
    plt.legend(loc='upper left')
    
    # Set y-axis limits to ensure correct display
    plt.ylim(0, 1)
    
    plt.savefig(os.path.join(output_dir, 'gini_by_group.png'))
    plt.close()
    
    # 5. Coefficient of variation comparison by group
    plt.figure(figsize=(12, 6))
    
    # Debug: Print CV values for inspection
    print("\nDebug - CV values by group:")
    for i, row in group_stats.iterrows():
        print(f"Group {row['group']}: KV Cache Tokens CV = {row['kv_cache_tokens_cv']:.4f}, New Tokens CV = {row['new_tokens_cv']:.4f}")
    
    plt.bar(x - width/2, group_stats['kv_cache_tokens_cv'].values, width, label='KV Cache Tokens')
    plt.bar(x + width/2, group_stats['new_tokens_cv'].values, width, label='New Tokens')
    plt.xlabel('Group Number')
    plt.ylabel('Coefficient of Variation (CV)')
    plt.title('Coefficient of Variation Comparison by Group')
    plt.xticks(x, group_stats['group'])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 添加变异系数参考线
    plt.axhline(y=0.1, color='g', linestyle='-', alpha=0.7, label='Low Variation (0.1)')
    plt.axhline(y=0.5, color='y', linestyle='-', alpha=0.7, label='Medium Variation (0.5)')
    plt.axhline(y=1.0, color='orange', linestyle='-', alpha=0.7, label='High Variation (1.0)')
    plt.axhline(y=1.5, color='r', linestyle='-', alpha=0.7, label='Very High Variation (1.5)')
    
    # 添加区域标签
    x_max = len(group_stats) - 0.5
    plt.text(x_max, 0.05, 'Very Low Variation', ha='right', va='center', color='g', fontweight='bold')
    plt.text(x_max, 0.3, 'Low Variation', ha='right', va='center', color='g', fontweight='bold')
    plt.text(x_max, 0.75, 'Medium Variation', ha='right', va='center', color='y', fontweight='bold')
    plt.text(x_max, 1.25, 'High Variation', ha='right', va='center', color='orange', fontweight='bold')
    plt.text(x_max, 1.75, 'Very High Variation', ha='right', va='center', color='r', fontweight='bold')
    
    # 更新图例
    plt.legend(loc='upper left')
    
    # Set y-axis limits to allow for all values
    max_cv = max(group_stats['kv_cache_tokens_cv'].max(), group_stats['new_tokens_cv'].max())
    plt.ylim(0, max(2.0, max_cv * 1.1))
    
    # 保存图像
    plt.savefig(os.path.join(output_dir, 'cv_by_group.png'))
    plt.close()
    
    # 6. 新增: 平均绝对差(MAD)比较
    plt.figure(figsize=(12, 6))
    
    # 打印MAD值用于调试
    print("\nDebug - MAD values by group:")
    for i, row in group_stats.iterrows():
        print(f"Group {row['group']}: KV Cache Tokens MAD = {row['kv_cache_tokens_mad']:.4f}, New Tokens MAD = {row['new_tokens_mad']:.4f}")
    
    plt.bar(x - width/2, group_stats['kv_cache_tokens_mad'].values, width, label='KV Cache Tokens')
    plt.bar(x + width/2, group_stats['new_tokens_mad'].values, width, label='New Tokens')
    plt.xlabel('Group Number')
    plt.ylabel('Mean Absolute Deviation (MAD)')
    plt.title('Mean Absolute Deviation Comparison by Group')
    plt.xticks(x, group_stats['group'])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 计算合适的Y轴上限
    max_mad = max(group_stats['kv_cache_tokens_mad'].max(), group_stats['new_tokens_mad'].max())
    plt.ylim(0, max_mad * 1.1)
    
    # 保存图像
    plt.savefig(os.path.join(output_dir, 'mad_by_group.png'))
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='分析requests.jsonl数据文件')
    parser.add_argument('--file', type=str, default='requests.jsonl', help='JSON数据文件路径')
    parser.add_argument('--group-size', type=int, default=5, help='每组包含的请求数量')
    parser.add_argument('--output-dir', type=str, default='analysis_results', help='结果输出目录')
    
    args = parser.parse_args()
    
    print(f"Analyzing file: {args.file}")
    print(f"Group size: {args.group_size}")
    
    results = analyze_requests(args.file, args.group_size, args.output_dir)
    
    if results is not None:
        # 打印全局统计信息
        global_stats = results[results['group'] == 'Global']
        print("\nGlobal Statistics:")
        print(f"Sample Count: {global_stats['size'].values[0]}")
        print(f"KV Cache Tokens - Mean: {global_stats['kv_cache_tokens_mean'].values[0]:.2f}, Std: {global_stats['kv_cache_tokens_std'].values[0]:.2f}, Gini: {global_stats['kv_cache_tokens_gini'].values[0]:.4f}, CV: {global_stats['kv_cache_tokens_cv'].values[0]:.4f}")
        print(f"New Tokens - Mean: {global_stats['new_tokens_mean'].values[0]:.2f}, Std: {global_stats['new_tokens_std'].values[0]:.2f}, Gini: {global_stats['new_tokens_gini'].values[0]:.4f}, CV: {global_stats['new_tokens_cv'].values[0]:.4f}")
        
        # 提供简单的分析解释
        interpret_results(global_stats)


def interpret_results(global_stats):
    """Simple interpretation of the results"""
    kv_gini = global_stats['kv_cache_tokens_gini'].values[0]
    new_gini = global_stats['new_tokens_gini'].values[0]
    kv_cv = global_stats['kv_cache_tokens_cv'].values[0]
    new_cv = global_stats['new_tokens_cv'].values[0]
    
    print("\nResults Interpretation:")
    
    # Gini coefficient interpretation
    print("Gini Coefficient Interpretation (0=complete equality, 1=complete inequality):")
    if kv_gini > 0.5:
        print(f"- KV Cache Tokens Gini of {kv_gini:.4f} indicates very uneven cache size distribution, with a few requests using most cache resources.")
    elif kv_gini > 0.3:
        print(f"- KV Cache Tokens Gini of {kv_gini:.4f} indicates moderately uneven cache size distribution.")
    else:
        print(f"- KV Cache Tokens Gini of {kv_gini:.4f} indicates relatively even cache size distribution.")
        
    if new_gini > 0.5:
        print(f"- New Tokens Gini of {new_gini:.4f} indicates very uneven distribution of new token calculations, suggesting large differences in request complexity.")
    elif new_gini > 0.3:
        print(f"- New Tokens Gini of {new_gini:.4f} indicates moderately uneven distribution of new token calculations.")
    else:
        print(f"- New Tokens Gini of {new_gini:.4f} indicates relatively even distribution of new token calculations.")
    
    # Coefficient of variation interpretation
    print("\nCoefficient of Variation Interpretation (higher values indicate greater dispersion):")
    if kv_cv > 1.0:
        print(f"- KV Cache Tokens CV of {kv_cv:.4f} indicates very high variation in cache sizes.")
    elif kv_cv > 0.5:
        print(f"- KV Cache Tokens CV of {kv_cv:.4f} indicates significant variation in cache sizes.")
    else:
        print(f"- KV Cache Tokens CV of {kv_cv:.4f} indicates relatively stable cache sizes.")
        
    if new_cv > 1.0:
        print(f"- New Tokens CV of {new_cv:.4f} indicates very high variation in new token counts.")
    elif new_cv > 0.5:
        print(f"- New Tokens CV of {new_cv:.4f} indicates significant variation in new token counts.")
    else:
        print(f"- New Tokens CV of {new_cv:.4f} indicates relatively stable new token counts.")
    
    # Recommendations
    print("\nRecommendations:")
    if kv_gini > 0.5 or kv_cv > 1.0:
        print("- KV cache resources are unevenly distributed; consider smarter caching strategies or dedicated processing paths for large contexts.")
    
    if new_gini > 0.5 or new_cv > 1.0:
        print("- Request complexity varies significantly; consider more flexible scaling strategies or complexity-based request routing.")
    
    if kv_gini > 0.3 and new_gini > 0.3:
        print("- Overall workload is unbalanced; consider implementing fairer scheduling mechanisms.")
    elif kv_gini <= 0.3 and new_gini <= 0.3:
        print("- Overall workload is relatively balanced; current processing strategies may be adequate.")


if __name__ == "__main__":
    main() 