#!/bin/bash
#================================================================
# 提案系统回滚脚本
# 支持：全部回滚、项目回滚、提案回滚
# 用法:
#   bash scripts/rollback_proposals.sh full [N]           # 回滚到第N个备份（默认1=最新）
#   bash scripts/rollback_proposals.sh project <project_id> [N]  # 回滚指定项目
#   bash scripts/rollback_proposals.sh proposal <proposal_id> [N] # 回滚指定提案
#   bash scripts/rollback_proposals.sh list               # 列出可用备份
#   bash scripts/rollback_proposals.sh verify <backup.tar.gz>     # 验证备份完整性
#================================================================

set -e

PROPOSALS_ROOT="/home/hermes/.hermes/proposals"
BACKUP_DIR="$PROPOSALS_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 备份文件清单
CSV_FILES="projects.csv proposals.csv"
INDEX_FILES="proposal-index.md proposal-docs-index.md project-index.md"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[rollback]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[rollback]${NC} $1"; }
log_error() { echo -e "${RED}[rollback]${NC} $1"; }

# 检查备份目录
check_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "备份目录不存在: $BACKUP_DIR"
        log_info "请先运行 backup_proposals.sh 创建备份"
        exit 1
    fi
}

# 列出可用备份
list_backups() {
    check_backup_dir
    echo ""
    echo "=== 可用备份 ==="
    echo ""
    
    local idx=0
    for backup in $(ls -1t "$BACKUP_DIR"/proposals_backup_*.tar.gz 2>/dev/null); do
        idx=$((idx + 1))
        local size=$(du -h "$backup" | cut -f1)
        local date=$(basename "$backup" | sed 's/proposals_backup_//' | sed 's/.tar.gz//')
        echo "  [$idx] $date (${size})"
    done
    
    if [ $idx -eq 0 ]; then
        log_warn "没有找到任何备份"
    fi
    echo ""
}

# 验证备份完整性
verify_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_info "验证备份: $(basename "$backup_file")"
    
# 验证tarball完整性
if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
    log_error "备份文件损坏: tarball不完整"
    exit 1
fi
    
    # 检查必要的CSV文件
    local missing=""
    for csv in $CSV_FILES; do
        if ! tar -tzf "$backup_file" | grep -q "$csv"; then
            missing="$missing $csv"
        fi
    done
    
    if [ -n "$missing" ]; then
        log_error "备份文件缺少必要文件:$missing"
        exit 1
    fi
    
    log_info "备份验证通过"
    
    # 显示备份内容
    echo ""
    echo "备份内容:"
    tar -tzf "$backup_file" | while read f; do
        echo "  - $f"
    done
}

# 提取备份文件到临时目录
extract_backup() {
    local backup_file="$1"
    local extract_dir="/tmp/proposals_rollback_$$"
    
    mkdir -p "$extract_dir"
    tar -xzf "$backup_file" -C "$extract_dir"
    echo "$extract_dir"
}

# 全量回滚
rollback_full() {
    local backup_index="${1:-1}"
    
    check_backup_dir
    
    # 获取指定序号的备份
    local backup_file=""
    local idx=0
    for backup in $(ls -1t "$BACKUP_DIR"/proposals_backup_*.tar.gz 2>/dev/null); do
        idx=$((idx + 1))
        if [ $idx -eq $backup_index ]; then
            backup_file="$backup"
            break
        fi
    done
    
    if [ -z "$backup_file" ]; then
        log_error "未找到第 $backup_index 个备份"
        list_backups
        exit 1
    fi
    
    log_warn "即将全量回滚到: $(basename "$backup_file")"
    log_warn "这将覆盖当前所有数据！"
    echo ""
    read -p "确认继续? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消回滚"
        exit 0
    fi
    
    # 验证备份
    verify_backup "$backup_file"
    
    # 创建当前数据的紧急备份
    local emergency_backup="$BACKUP_DIR/emergency_before_rollback_$(date +%Y%m%d_%H%M%S).tar.gz"
    log_info "创建紧急备份: $emergency_backup"
    tar -czf "$emergency_backup" -C "$PROPOSALS_ROOT" \
        $CSV_FILES $INDEX_FILES 2>/dev/null || true
    
    # 提取并应用备份
    local extract_dir=$(extract_backup "$backup_file")
    
    log_info "应用备份数据..."
    for csv in $CSV_FILES; do
        if [ -f "$extract_dir/$csv" ]; then
            cp "$extract_dir/$csv" "$PROPOSALS_ROOT/$csv"
            log_info "  恢复: $csv"
        fi
    done
    
    for md in $INDEX_FILES; do
        if [ -f "$extract_dir/$md" ]; then
            cp "$extract_dir/$md" "$PROPOSALS_ROOT/$md"
            log_info "  恢复: $md"
        fi
    done
    
    # 清理
    rm -rf "$extract_dir"
    
    log_info "全量回滚完成"
}

# 项目回滚
rollback_project() {
    local project_id="$1"
    local backup_index="${2:-1}"
    
    if [ -z "$project_id" ]; then
        log_error "请指定项目ID"
        echo "用法: rollback_proposals.sh project <project_id> [N]"
        exit 1
    fi
    
    check_backup_dir
    
    # 获取指定序号的备份
    local backup_file=""
    local idx=0
    for backup in $(ls -1t "$BACKUP_DIR"/proposals_backup_*.tar.gz 2>/dev/null); do
        idx=$((idx + 1))
        if [ $idx -eq $backup_index ]; then
            backup_file="$backup"
            break
        fi
    done
    
    if [ -z "$backup_file" ]; then
        log_error "未找到第 $backup_index 个备份"
        exit 1
    fi
    
    log_warn "即将回滚项目 $project_id 到: $(basename "$backup_file")"
    echo ""
    read -p "确认继续? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消回滚"
        exit 0
    fi
    
    # 提取备份
    local extract_dir=$(extract_backup "$backup_file")
    
    # 读取备份中的项目数据
    local backup_projects="$extract_dir/projects.csv"
    
    if [ ! -f "$backup_projects" ]; then
        log_error "备份中无projects.csv"
        rm -rf "$extract_dir"
        exit 1
    fi
    
    # 检查项目是否存在
    local project_line=$(grep "^$project_id," "$backup_projects" 2>/dev/null || true)
    if [ -z "$project_name" ]; then
        log_warn "备份中未找到项目: $project_id"
    fi
    
    # 读取当前CSV
    local temp_dir="/tmp/proposals_project_rollback_$$"
    mkdir -p "$temp_dir"
    
    # 备份当前数据
    cp "$PROPOSALS_ROOT/projects.csv" "$temp_dir/projects.csv"
    cp "$PROPOSALS_ROOT/proposals.csv" "$temp_dir/proposals.csv"
    
    # 从备份恢复项目数据
    # 1. 移除当前项目
    grep -v "^$project_id," "$PROPOSALS_ROOT/projects.csv" > "$temp_dir/projects_new.csv" || true
    
    # 2. 添加备份中的项目
    grep "^$project_id," "$backup_projects" >> "$temp_dir/projects_new.csv" || true
    
    # 3. 恢复项目的提案状态（从备份的proposals.csv）
    # 找出备份中该项目所有提案
    local backup_proposals="$extract_dir/proposals.csv"
    local project_proposals=$(grep ",$project_id," "$backup_proposals" 2>/dev/null | cut -d',' -f1 || true)
    
    # 移除当前该项目的所有提案
    grep -v ",$project_id," "$PROPOSALS_ROOT/proposals.csv" > "$temp_dir/proposals_new.csv" || true
    
    # 添加备份中该项目的提案
    if [ -n "$project_proposals" ]; then
        for pid in $project_proposals; do
            grep "^$pid," "$backup_proposals" >> "$temp_dir/proposals_new.csv" || true
        done
    fi
    
    # 应用更改
    mv "$temp_dir/projects_new.csv" "$PROPOSALS_ROOT/projects.csv"
    mv "$temp_dir/proposals_new.csv" "$PROPOSALS_ROOT/proposals.csv"
    
    rm -rf "$temp_dir"
    rm -rf "$extract_dir"
    
    log_info "项目回滚完成: $project_id"
}

# 提案回滚
rollback_proposal() {
    local proposal_id="$1"
    local backup_index="${2:-1}"
    
    if [ -z "$proposal_id" ]; then
        log_error "请指定提案ID"
        echo "用法: rollback_proposals.sh proposal <proposal_id> [N]"
        exit 1
    fi
    
    check_backup_dir
    
    # 获取指定序号的备份
    local backup_file=""
    local idx=0
    for backup in $(ls -1t "$BACKUP_DIR"/proposals_backup_*.tar.gz 2>/dev/null); do
        idx=$((idx + 1))
        if [ $idx -eq $backup_index ]; then
            backup_file="$backup"
            break
        fi
    done
    
    if [ -z "$backup_file" ]; then
        log_error "未找到第 $backup_index 个备份"
        exit 1
    fi
    
    log_warn "即将回滚提案 $proposal_id 到: $(basename "$backup_file")"
    echo ""
    read -p "确认继续? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消回滚"
        exit 0
    fi
    
    # 提取备份
    local extract_dir=$(extract_backup "$backup_file")
    local backup_proposals="$extract_dir/proposals.csv"
    
    # 检查提案是否存在
    local proposal_line=$(grep "^$proposal_id," "$backup_proposals" 2>/dev/null || true)
    if [ -z "$proposal_line" ]; then
        log_error "备份中未找到提案: $proposal_id"
        rm -rf "$extract_dir"
        exit 1
    fi
    
    # 备份当前数据
    local emergency_backup="$BACKUP_DIR/emergency_proposal_rollback_$(date +%Y%m%d_%H%M%S).tar.gz"
    mkdir -p "$(dirname "$emergency_backup")"
    tar -czf "$emergency_backup" \
        "$PROPOSALS_ROOT/proposals.csv" 2>/dev/null || true
    log_info "当前数据已备份到: $emergency_backup"
    
    # 移除当前提案，添加备份中的提案
    grep -v "^$proposal_id," "$PROPOSALS_ROOT/proposals.csv" > "$extract_dir/proposals_fixed.csv"
    grep "^$proposal_id," "$backup_proposals" >> "$extract_dir/proposals_fixed.csv"
    mv "$extract_dir/proposals_fixed.csv" "$PROPOSALS_ROOT/proposals.csv"
    
    rm -rf "$extract_dir"
    
    log_info "提案回滚完成: $proposal_id"
}

# 主程序
main() {
    local command="${1:-}"
    
    case "$command" in
        list)
            list_backups
            ;;
        verify)
            verify_backup "$2"
            ;;
        full)
            rollback_full "$2"
            ;;
        project)
            rollback_project "$2" "$3"
            ;;
        proposal)
            rollback_proposal "$2" "$3"
            ;;
        help|--help|-h)
            echo "提案系统回滚脚本"
            echo ""
            echo "用法:"
            echo "  bash scripts/rollback_proposals.sh list                      # 列出可用备份"
            echo "  bash scripts/rollback_proposals.sh verify <backup.tar.gz>  # 验证备份完整性"
            echo "  bash scripts/rollback_proposals.sh full [N]                 # 全量回滚到第N个备份（默认1=最新）"
            echo "  bash scripts/rollback_proposals.sh project <id> [N]         # 回滚指定项目"
            echo "  bash scripts/rollback_proposals.sh proposal <id> [N]       # 回滚指定提案"
            echo ""
            echo "示例:"
            echo "  bash scripts/rollback_proposals.sh list"
            echo "  bash scripts/rollback_proposals.sh full                     # 回滚到最新备份"
            echo "  bash scripts/rollback_proposals.sh full 3                  # 回滚到第3个备份"
            echo "  bash scripts/rollback_proposals.sh project PRJ-20260419-007"
            echo "  bash scripts/rollback_proposals.sh proposal P-20260419-001"
            ;;
        *)
            if [ -z "$command" ]; then
                log_error "请指定命令"
            else
                log_error "未知命令: $command"
            fi
            echo "运行 'bash scripts/rollback_proposals.sh help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"