#!/usr/bin/env bash
# batch_run.sh
# 功能: 轮询(交叉)运行 run_mrq.sh 的多种参数组合，每种跑 N 次
# 用法:
#   ./batch_run.sh [REPEAT] [SLEEP_BETWEEN]
# 例子:
#   ./batch_run.sh                 # 每种3次，间隔0秒
#   ./batch_run.sh 5 2             # 每种5次，每次间隔2秒

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 每种 case 执行次数（可用第1个参数覆盖）
REPEAT="${1:-30}"
# 每次运行之间的间隔秒数（可用第2个参数覆盖）
SLEEP_BETWEEN="${2:-0}"

# 在这里维护/扩展你的用例（每行一个用例；用空格分隔参数）
#   "fcfs" "fcfs lmcache_enabled" "sjf_prompt_tokens" "sjf_prompt_tokens lmcache_enabled"
CASES=(
  # "fcfs"
  # "fcfs lmcache_enabled"
  
  # "sjf_prompt_tokens"
  "sjf_prompt_tokens lmcache_enabled"
  
  # "sjf_uncomputed_tokens_local"
  "sjf_uncomputed_tokens_local lmcache_enabled"

  # "sjf_uncomputed_tokens_global lmcache_enabled"

  # "sjf_cost_aware lmcache_enabled"
)

run_one_case() {
  local case_str="$1"
  # 按空白拆成数组，安全传参（避免用 eval）
  IFS=' ' read -r -a argv <<< "$case_str"
  echo ">>> $(date '+%F %T') Running: ./run_mrq.sh ${case_str}"
  "${SCRIPT_DIR}/run_mrq.sh" "${argv[@]}"
}

for round in $(seq 1 "${REPEAT}"); do
  echo "==================== Round ${round}/${REPEAT} ===================="
  for case_str in "${CASES[@]}"; do
    run_one_case "${case_str}"
    if (( SLEEP_BETWEEN > 0 )); then
      sleep "${SLEEP_BETWEEN}"
    fi
    echo
  done
done

echo "✅ All done."
