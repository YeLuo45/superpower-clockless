#!/bin/bash
#================================================================
# 提案系统备份脚本
# 数据来源：ai-superpower API（禁止直接读 CSV）
#================================================================

set -e

SKILL_NAME="prj-proposals-manager"
SKILL_DIR="/home/hermes/.hermes/skills/${SKILL_NAME}"
PROPOSALS_ROOT="${SUPERPOWER_ROOT:-/home/hermes/proposals}"
BACKUP_ROOT="${PROPOSALS_ROOT}/backups"
API_BASE="${AI_SUPERPOWER_BASE:-http://0.0.0.0:8000}"

# 环境变量检查
if [ -z "$SUPERPOWER_API_KEY" ]; then
    echo "❌ 错误: SUPERPOWER_API_KEY 未设置"
    echo "   请先: export SUPERPOWER_API_KEY=\"your-key\""
    exit 1
fi

# 创建备份目录（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/backup_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

echo "📦 提案系统备份"
echo "=================="
echo "备份目录: ${BACKUP_DIR}"
echo "API: ${API_BASE}"
echo ""

total=0
success=0
failed=0

# ========== 通过 API 备份 CSV 数据 ==========
echo "📄 备份提案数据（通过 API）..."

python3 "${SKILL_DIR}/scripts/backup_api.py" "$BACKUP_DIR"
if [ -f "${BACKUP_DIR}/projects.csv" ]; then
    success=$((success + 1)); echo "  ✅ projects.csv"
else
    failed=$((failed + 1)); echo "  ⚠️  projects.csv 失败"
fi
total=$((total + 1))

if [ -f "${BACKUP_DIR}/proposals.csv" ]; then
    success=$((success + 1)); echo "  ✅ proposals.csv"
else
    failed=$((failed + 1)); echo "  ⚠️  proposals.csv 失败"
fi
total=$((total + 1))

# ========== 直接复制 Markdown 文件 ==========
MARKDOWN_FILES=(
    "${PROPOSALS_ROOT}/project-index.md"
    "${PROPOSALS_ROOT}/proposal-docs-index.md"
    "${PROPOSALS_ROOT}/proposal-index.md"
)
for file in "${MARKDOWN_FILES[@]}"; do
    name=$(basename "$file")
    if [ -f "$file" ]; then
        cp "$file" "${BACKUP_DIR}/"; echo "  ✅ $name"; success=$((success + 1))
    else
        echo "  ⚠️  不存在: $name"; failed=$((failed + 1))
    fi
    total=$((total + 1))
done

# 备份模板目录
TEMPLATES_DIR="${PROPOSALS_ROOT}/templates"
if [ -d "$TEMPLATES_DIR" ]; then
    cp -r "$TEMPLATES_DIR" "${BACKUP_DIR}/"; echo "  ✅ templates/"; success=$((success + 1))
else
    echo "  ⚠️  不存在: templates/"; failed=$((failed + 1))
fi
total=$((total + 1))

# ========== 备份技能文件 ==========
echo ""
echo "📦 备份技能文件..."

for subdir in references; do
    if [ -d "${SKILL_DIR}/${subdir}" ]; then
        cp -r "${SKILL_DIR}/${subdir}" "${BACKUP_DIR}/skill_${subdir}/"
        echo "  ✅ skill_${subdir}/"; success=$((success + 1)); total=$((total + 1))
    fi
done

for file in SKILL.md SKILL-zh.md scripts/backup_proposals.sh scripts/rollback_proposals.sh; do
    name=$(basename "$file")
    src="${SKILL_DIR}/${file}"
    if [ -f "$src" ]; then
        cp "$src" "${BACKUP_DIR}/"; echo "  ✅ $name"; success=$((success + 1))
    else
        echo "  ⚠️  不存在: $name"; failed=$((failed + 1))
    fi
    total=$((total + 1))
done

# ========== 生成备份清单 ==========
{
    echo "# 备份清单 - ${TIMESTAMP}"
    echo ""
    echo "## 备份内容"
    echo ""
    echo "| 类型 | 名称 | 状态 |"
    echo "|------|------|------|"
    for item in $(ls -A "${BACKUP_DIR}" 2>/dev/null); do
        if [ -d "${BACKUP_DIR}/$item" ]; then
            count=$(find "${BACKUP_DIR}/$item" \( -name "*.md" -o -name "*.csv" -o -name "*.sh" -o -name "*.py" \) 2>/dev/null | wc -l)
            echo "| 目录 | $item | ✅ ($count 文件) |"
        else
            echo "| 文件 | $item | ✅ |"
        fi
    done
    echo ""
    echo "## 备份信息"
    echo "- 备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "- 备份路径: ${BACKUP_DIR}"
    echo "- API 来源: ${API_BASE}"
    echo "- 成功: ${success}/${total}"
    [ $failed -gt 0 ] && echo "- 失败/跳过: ${failed}"
} > "${BACKUP_DIR}/MANIFEST.md"

# 更新最新备份软链接
rm -f "${BACKUP_ROOT}/latest"
ln -s "${BACKUP_DIR}" "${BACKUP_ROOT}/latest"

echo ""
echo "📋 备份清单已生成: ${BACKUP_DIR}/MANIFEST.md"
echo ""
echo "✅ 备份完成！"
echo "   最新备份: ${BACKUP_ROOT}/latest"
echo "   本次备份: ${BACKUP_DIR}"

# 清理旧备份（保留最近 10 个）
echo ""
echo "🧹 清理旧备份（保留最近 10 个）..."
backup_count=$(ls -d "${BACKUP_ROOT}"/backup_* 2>/dev/null | wc -l)
if [ $backup_count -gt 10 ]; then
    old=$(ls -d "${BACKUP_ROOT}"/backup_* 2>/dev/null | sort | head -n -10)
    for d in $old; do rm -rf "$d"; echo "  🗑️  已删除: $(basename $d)"; done
    echo "   已清理 $((backup_count - 10)) 个旧备份"
else
    echo "   无需清理，当前共 ${backup_count} 个备份"
fi