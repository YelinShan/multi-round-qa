import re
import sys

if len(sys.argv) < 2:
    print("用法: python script.py <log_file>")
    sys.exit(1)

log_file = sys.argv[1]

positive_count = 0
zero_count = 0
negative_count = 0

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
