#!/bin/bash
# run_mrq.sh
# 用法:
#   ./run_mrq.sh <MODE> [lmcache_enabled]
# 例子:
#   ./run_mrq.sh fcfs
#   ./run_mrq.sh sjf_prompt_tokens lmcache_enabled

set -o errexit
set -o nounset
set -o pipefail

MODE="${1:-}"
LMFLAG="${2:-}"

VALID_MODES=("fcfs" "sjf_prompt_tokens" "sjf_uncomputed_tokens_local" "sjf_uncomputed_tokens_global")
if [[ -z "$MODE" ]]; then
  echo "❌ Missing MODE argument."
  echo "Usage: $0 <MODE> [lmcache_enabled]"
  echo "Available SchedulerPolicy options:"
  printf '  - %s\n' "${VALID_MODES[@]}"
  exit 1
fi

# 基础路径与时间戳run目录
BASE_LOG_DIR="/home/yshan/Programs/vllm-scheduling-optimized/benchmarks/multi-round-qa/benchmark_log"
DATE_TIME="$(date +%Y_%m_%d_%H-%M)"
LMFLAG_DIR=${LMFLAG:-lmcache_disabled}
RUN_DIR="$BASE_LOG_DIR/$MODE/$LMFLAG_DIR/$DATE_TIME"
mkdir -p "$RUN_DIR"

VLLM_LOG="$RUN_DIR/run_vllm_server.log"
MRQ_LOG="$RUN_DIR/run_mrq.log"

# 压测参数
MODEL_DIR="/home/yshan/Downloads/models/Qwen-1_5b"

NUM_USERS=50
QPS=100

# --------- 工具函数 ----------
wait_for_vllm_ready() {
  local url="http://localhost:8000/v1/models"
  local timeout_sec=300        # 最长等 5 分钟
  local interval_sec=2
  local elapsed=0

  echo "⏳ 等待 vLLM 就绪（最多 ${timeout_sec}s）..." | tee -a "$MRQ_LOG"
  while (( elapsed < timeout_sec )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "✅ vLLM 已就绪。" | tee -a "$MRQ_LOG"
      return 0
    fi
    sleep "$interval_sec"
    elapsed=$((elapsed + interval_sec))
  done

  echo "❌ 等待 vLLM 超时（${timeout_sec}s）。" | tee -a "$MRQ_LOG"
  return 1
}

stop_vllm() {
  echo "🛑 正在关闭 vLLM 服务器..." | tee -a "$MRQ_LOG"
  # 尝试优雅关闭（杀掉 uvicorn/vllm api_server 进程）
  pkill -f "vllm.entrypoints.openai.api_server.*--port 8000" || true
  # 再等几秒确认退出
  sleep 3
  # 若还有遗留，再补一次
  if pgrep -f "vllm.entrypoints.openai.api_server.*--port 8000" >/dev/null 2>&1; then
    echo "⚠️ 发现残留进程，二次终止..." | tee -a "$MRQ_LOG"
    pkill -9 -f "vllm.entrypoints.openai.api_server.*--port 8000" || true
  fi
  echo "✅ vLLM 已关闭。" | tee -a "$MRQ_LOG"
}

cleanup() {
  # 确保脚本异常中断时也能收尾
  stop_vllm
}
trap cleanup EXIT INT TERM

# --------- 启动 vLLM ----------
{
  echo "==================== START ===================="
  echo "Date Time: $DATE_TIME"
  echo "Run Dir: $RUN_DIR"
  echo 
  echo "SchedulerPolicy (MODE): $MODE"
  echo "LMCache Flag: ${LMFLAG:-<none>}"
  echo 
  echo "NUM Of USERS: $NUM_USERS"
  echo "QPS: $QPS"
  echo "==================== OUTPUT ===================="
} > "$MRQ_LOG"

echo "▶️ 启动 vLLM 服务器..." | tee -a "$MRQ_LOG"

# 将 vLLM 服务放到后台运行，日志写到 $RUN_DIR/run_vllm_server.log
# 第三个参数传递 LOG_DIR，保持两份日志在同一目录
VLLM_SERVER_SCRIPT="/home/yshan/Programs/vllm-scheduling-optimized/run_vllm_server.sh"
"$VLLM_SERVER_SCRIPT" "$MODE" "${LMFLAG:-}" "$RUN_DIR" >/dev/null 2>&1 &

VLLM_WRAPPER_PID=$!
echo "vLLM wrapper pid: $VLLM_WRAPPER_PID" >> "$MRQ_LOG"


# 等待服务就绪
wait_for_vllm_ready

# --------- 运行压测 ----------
echo "🚀 开始运行 multi-round-qa 压测..." | tee -a "$MRQ_LOG"

CMD=(
  python multi-round-qa_orig.py
  --num-users $NUM_USERS
  --shared-system-prompt 1
  --user-history-prompt 1
  --answer-len 5000000
  --num-rounds 10
  --qps $QPS
  --model "$MODEL_DIR"
  --seed 12345
  --base-url http://localhost:8000/v1
  --sharegpt
  --time 200
)

{
  echo "==================== COMMAND ===================="
  printf '%s \\\n' "${CMD[@]}"
  echo
  echo "==================== OUTPUT ===================="
} >> "$MRQ_LOG"

# 执行压测，输出同时写文件与控制台
# （这里 tee -a $MRQ_LOG 方便你实时查看；若不需要可直接重定向到 >> "$MRQ_LOG"）
"${CMD[@]}" 2>&1 | tee -a "$MRQ_LOG"


{
  echo "==================== PARAMS ===================="
  echo "Date Time: $DATE_TIME"
  echo "Run Dir: $RUN_DIR"
  echo 
  echo "SchedulerPolicy (MODE): $MODE"
  echo "LMCache Flag: ${LMFLAG:-<none>}"
  echo 
  echo "NUM Of USERS: $NUM_USERS"
  echo "QPS: $QPS"
  echo "==================== OUTPUT ===================="
} >> "$MRQ_LOG"

# --------- 关闭 vLLM ----------
stop_vllm

echo "🏁 本次测试完成。日志目录：$RUN_DIR" | tee -a "$MRQ_LOG"
