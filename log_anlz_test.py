import re

# 日志文件路径
log_file = (
    "/home/yshan/Programs/vllm-scheduling-optimized/benchmarks/multi-round-qa/benchmark_log/sjf_prompt_tokens/lmcache_enabled/2025_09_08_16-04/run_vllm_server.log"
)

# 定义计数器
positive_count = 0
zero_count = 0
negative_count = 0

# 定义正则
pattern = re.compile(r"need to load:\s*(-?\d+)")

with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        match = pattern.search(line)
        if match:
            num = int(match.group(1))
            if num > 0:
                positive_count += 1
            elif num == 0:
                zero_count += 1
            else:
                negative_count += 1

print(f"正数条数: {positive_count}")
print(f"0 的条数: {zero_count}")
print(f"负数条数: {negative_count}")