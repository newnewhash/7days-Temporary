#!/bin/bash
# Twitter财经资讯日报 - 每日自动生成并推送到GitHub
# 执行时间：每天早上 6:00

# 配置
# 注意: GITHUB_TOKEN通过环境变量GITHUB_TOKEN传入，不要硬编码
GITHUB_TOKEN="${GITHUB_TOKEN}"
REPO_URL="https://github.com/newnewhash/7days-Temporary"
REPO_DIR="/workspace/7days-Temporary"
REPORTS_DIR="/workspace/reports"
TWITTER_ACCOUNTS=(
    "zerohedge" "wublockchain12" "AndreasSteno" "JeffLia12309881" "biancoresearch"
    "josephwang" "Murphychen888" "LynAldenContact" "profplum99" "_FORAB"
    "NickTimiraos" "Maxandzero" "qinbafrank" "Amy6Tina" "rickawsb"
    "wepoets1107" "KobeissiLetter" "Cointelegraph" "EmberCN" "GracyBitget"
    "fxtrader" "soberoption" "financialjuice" "HODL15Capital" "myanTokenGeek"
    "saylor" "SantiagoAuFund" "TCNetwork" "TheBlockCo" "gary_yangge"
)

# 获取当前日期
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="${REPORTS_DIR}/daily_twitter_summary_${TODAY}.md"

echo "=== Twitter财经资讯日报生成任务 ==="
echo "执行时间: $(date)"
echo ""

# 步骤1: 确保报告目录存在
mkdir -p ${REPORTS_DIR}

# 步骤2: 生成日报（这里调用Python脚本生成报告）
# 由于cron环境中无法直接调用MCP工具，这里预留接口
# 实际执行时会由Agent自动完成

# 步骤3: 克隆仓库
echo "[1/4] 同步GitHub仓库..."
rm -rf ${REPO_DIR}
git clone "https://${GITHUB_TOKEN}@github.com/newnewhash/7days-Temporary.git" ${REPO_DIR}

# 步骤4: 复制日报到仓库
echo "[2/4] 复制日报到仓库..."
mkdir -p ${REPO_DIR}/Twitter-daily-summary
if [ -f "${REPORT_FILE}" ]; then
    cp ${REPORT_FILE} ${REPO_DIR}/Twitter-daily-summary/
    echo "日报已复制: ${REPORT_FILE}"
else
    echo "警告: 今日日报文件不存在，跳过复制"
    exit 1
fi

# 步骤5: 提交并推送
echo "[3/4] 提交更改..."
cd ${REPO_DIR}
git config user.email "daily-report@bot.com"
git config user.name "Daily Report Bot"
git add Twitter-daily-summary/
git commit -m "Add Twitter财经资讯日报 ${TODAY}"

echo "[4/4] 推送到GitHub..."
git push origin main

echo ""
echo "=== 任务完成 ==="
echo "日报已推送到: https://github.com/newnewhash/7days-Temporary"
