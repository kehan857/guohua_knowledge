#!/bin/bash

# 熵变智元AI销售助手 - 数据备份脚本
# 支持数据库、文件和配置的全量备份

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# 配置变量
BACKUP_DIR="/backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# 数据库配置
DB_HOST=${DB_HOST:-postgres-service}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-ai_sales_db}
DB_USER=${DB_USER:-ai_sales_user}
DB_PASSWORD=${DB_PASSWORD}

# Redis配置
REDIS_HOST=${REDIS_HOST:-redis-service}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD}

# 显示帮助信息
show_help() {
    cat << EOF
熵变智元AI销售助手备份脚本

用法: $0 [选项] [备份类型]

备份类型:
  all            全量备份 (默认)
  database       仅备份数据库
  redis          仅备份Redis数据
  files          仅备份文件
  config         仅备份配置

选项:
  -h, --help     显示此帮助信息
  -d, --dir      指定备份目录 (默认: /backups)
  -r, --retention 指定保留天数 (默认: 30天)
  --compress     压缩备份文件
  --encrypt      加密备份文件
  --upload       上传到云存储 (需要配置)

示例:
  $0                           # 全量备份
  $0 database                  # 仅备份数据库
  $0 --compress --encrypt all  # 压缩加密的全量备份
EOF
}

# 创建备份目录
create_backup_dir() {
    local backup_path="$BACKUP_DIR/$TIMESTAMP"
    
    if [[ ! -d "$backup_path" ]]; then
        mkdir -p "$backup_path"
        log_info "创建备份目录: $backup_path"
    fi
    
    echo "$backup_path"
}

# 备份PostgreSQL数据库
backup_database() {
    local backup_path=$1
    local compress=$2
    
    log_info "开始备份PostgreSQL数据库..."
    
    local db_backup_file="$backup_path/database_${TIMESTAMP}.sql"
    
    # 检查数据库连接
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
        log_error "无法连接到数据库"
        return 1
    fi
    
    # 执行数据库备份
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        > "$db_backup_file"
    
    if [[ $? -eq 0 ]]; then
        local file_size=$(du -h "$db_backup_file" | cut -f1)
        log_success "数据库备份完成: $db_backup_file ($file_size)"
        
        # 压缩备份文件
        if [[ "$compress" == "true" ]]; then
            gzip "$db_backup_file"
            log_success "数据库备份已压缩: ${db_backup_file}.gz"
        fi
    else
        log_error "数据库备份失败"
        return 1
    fi
}

# 备份Redis数据
backup_redis() {
    local backup_path=$1
    local compress=$2
    
    log_info "开始备份Redis数据..."
    
    local redis_backup_file="$backup_path/redis_${TIMESTAMP}.rdb"
    
    # 检查Redis连接
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping &> /dev/null; then
        log_error "无法连接到Redis"
        return 1
    fi
    
    # 执行Redis备份
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" \
        --rdb "$redis_backup_file"
    
    if [[ $? -eq 0 ]]; then
        local file_size=$(du -h "$redis_backup_file" | cut -f1)
        log_success "Redis备份完成: $redis_backup_file ($file_size)"
        
        # 压缩备份文件
        if [[ "$compress" == "true" ]]; then
            gzip "$redis_backup_file"
            log_success "Redis备份已压缩: ${redis_backup_file}.gz"
        fi
    else
        log_error "Redis备份失败"
        return 1
    fi
}

# 备份应用文件
backup_files() {
    local backup_path=$1
    local compress=$2
    
    log_info "开始备份应用文件..."
    
    local files_backup_file="$backup_path/files_${TIMESTAMP}.tar"
    
    # 定义需要备份的目录
    local backup_dirs=(
        "/app/uploads"
        "/app/logs"
        "/app/static"
    )
    
    # 创建tar备份
    local tar_options=""
    if [[ "$compress" == "true" ]]; then
        tar_options="-czf"
        files_backup_file="${files_backup_file}.gz"
    else
        tar_options="-cf"
    fi
    
    # 检查目录是否存在并备份
    local existing_dirs=()
    for dir in "${backup_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            existing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#existing_dirs[@]} -gt 0 ]]; then
        tar $tar_options "$files_backup_file" "${existing_dirs[@]}"
        
        if [[ $? -eq 0 ]]; then
            local file_size=$(du -h "$files_backup_file" | cut -f1)
            log_success "文件备份完成: $files_backup_file ($file_size)"
        else
            log_error "文件备份失败"
            return 1
        fi
    else
        log_warning "没有找到需要备份的文件目录"
    fi
}

# 备份配置文件
backup_config() {
    local backup_path=$1
    local compress=$2
    
    log_info "开始备份配置文件..."
    
    local config_backup_file="$backup_path/config_${TIMESTAMP}.tar"
    
    # 定义需要备份的配置文件
    local config_files=(
        "/app/.env"
        "/etc/nginx/nginx.conf"
        "/etc/nginx/conf.d"
        "/etc/prometheus/prometheus.yml"
        "/etc/grafana/provisioning"
    )
    
    # 创建tar备份
    local tar_options=""
    if [[ "$compress" == "true" ]]; then
        tar_options="-czf"
        config_backup_file="${config_backup_file}.gz"
    else
        tar_options="-cf"
    fi
    
    # 检查文件是否存在并备份
    local existing_files=()
    for file in "${config_files[@]}"; do
        if [[ -e "$file" ]]; then
            existing_files+=("$file")
        fi
    done
    
    if [[ ${#existing_files[@]} -gt 0 ]]; then
        tar $tar_options "$config_backup_file" "${existing_files[@]}"
        
        if [[ $? -eq 0 ]]; then
            local file_size=$(du -h "$config_backup_file" | cut -f1)
            log_success "配置备份完成: $config_backup_file ($file_size)"
        else
            log_error "配置备份失败"
            return 1
        fi
    else
        log_warning "没有找到需要备份的配置文件"
    fi
}

# 加密备份文件
encrypt_backup() {
    local backup_path=$1
    local encryption_key=${BACKUP_ENCRYPTION_KEY:-""}
    
    if [[ -z "$encryption_key" ]]; then
        log_warning "未设置加密密钥，跳过加密"
        return 0
    fi
    
    log_info "开始加密备份文件..."
    
    # 查找所有备份文件
    local backup_files=($(find "$backup_path" -type f -name "*.sql" -o -name "*.rdb" -o -name "*.tar*"))
    
    for file in "${backup_files[@]}"; do
        if [[ -f "$file" ]]; then
            # 使用GPG加密
            echo "$encryption_key" | gpg --batch --yes --passphrase-fd 0 --cipher-algo AES256 --compress-algo 2 --symmetric --output "${file}.gpg" "$file"
            
            if [[ $? -eq 0 ]]; then
                rm "$file"  # 删除原文件
                log_success "文件已加密: ${file}.gpg"
            else
                log_error "文件加密失败: $file"
            fi
        fi
    done
}

# 上传到云存储
upload_to_cloud() {
    local backup_path=$1
    local cloud_provider=${CLOUD_PROVIDER:-""}
    
    if [[ -z "$cloud_provider" ]]; then
        log_info "未配置云存储，跳过上传"
        return 0
    fi
    
    log_info "开始上传备份到云存储..."
    
    case "$cloud_provider" in
        "aws")
            upload_to_aws "$backup_path"
            ;;
        "aliyun")
            upload_to_aliyun "$backup_path"
            ;;
        "tencent")
            upload_to_tencent "$backup_path"
            ;;
        *)
            log_warning "不支持的云存储提供商: $cloud_provider"
            ;;
    esac
}

# 上传到AWS S3
upload_to_aws() {
    local backup_path=$1
    local s3_bucket=${AWS_S3_BUCKET:-""}
    
    if [[ -z "$s3_bucket" ]]; then
        log_error "AWS S3 bucket未配置"
        return 1
    fi
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI未安装"
        return 1
    fi
    
    aws s3 sync "$backup_path" "s3://$s3_bucket/ai-sales-assistant/backups/$(basename $backup_path)/"
    
    if [[ $? -eq 0 ]]; then
        log_success "备份已上传到AWS S3"
    else
        log_error "上传到AWS S3失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    local retention_days=$1
    
    log_info "清理 $retention_days 天前的备份..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warning "备份目录不存在，跳过清理"
        return 0
    fi
    
    # 查找并删除旧备份
    local old_backups=$(find "$BACKUP_DIR" -type d -name "????????_??????" -mtime +$retention_days)
    
    if [[ -n "$old_backups" ]]; then
        echo "$old_backups" | while read -r backup_dir; do
            if [[ -d "$backup_dir" ]]; then
                rm -rf "$backup_dir"
                log_info "删除旧备份: $backup_dir"
            fi
        done
        log_success "旧备份清理完成"
    else
        log_info "没有需要清理的旧备份"
    fi
}

# 创建备份清单
create_manifest() {
    local backup_path=$1
    local manifest_file="$backup_path/backup_manifest.json"
    
    log_info "创建备份清单..."
    
    # 收集备份信息
    local backup_info=$(cat << EOF
{
    "backup_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "backup_version": "1.0",
    "application": "ai-sales-assistant",
    "environment": "${ENVIRONMENT:-production}",
    "files": [
EOF
)
    
    # 添加文件信息
    local first_file=true
    while read -r file; do
        if [[ -f "$file" ]]; then
            local file_name=$(basename "$file")
            local file_size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "0")
            local file_hash=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
            
            if [[ "$first_file" == "false" ]]; then
                backup_info+=","
            fi
            backup_info+=$(cat << EOF

        {
            "name": "$file_name",
            "size": $file_size,
            "sha256": "$file_hash",
            "type": "$(echo $file_name | sed 's/.*_[0-9]*_[0-9]*\.\(.*\)/\1/')"
        }
EOF
)
            first_file=false
        fi
    done < <(find "$backup_path" -type f ! -name "backup_manifest.json")
    
    backup_info+=$(cat << EOF

    ]
}
EOF
)
    
    echo "$backup_info" > "$manifest_file"
    log_success "备份清单已创建: $manifest_file"
}

# 验证备份完整性
verify_backup() {
    local backup_path=$1
    
    log_info "验证备份完整性..."
    
    local manifest_file="$backup_path/backup_manifest.json"
    
    if [[ ! -f "$manifest_file" ]]; then
        log_warning "备份清单不存在，跳过验证"
        return 0
    fi
    
    # 验证每个文件的哈希值
    local verification_failed=false
    
    while read -r file_info; do
        local file_name=$(echo "$file_info" | jq -r '.name')
        local expected_hash=$(echo "$file_info" | jq -r '.sha256')
        local file_path="$backup_path/$file_name"
        
        if [[ -f "$file_path" ]]; then
            local actual_hash=$(sha256sum "$file_path" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$file_path" 2>/dev/null | cut -d' ' -f1)
            
            if [[ "$actual_hash" == "$expected_hash" ]]; then
                log_info "文件验证通过: $file_name"
            else
                log_error "文件验证失败: $file_name (期望: $expected_hash, 实际: $actual_hash)"
                verification_failed=true
            fi
        else
            log_error "文件不存在: $file_path"
            verification_failed=true
        fi
    done < <(jq -c '.files[]' "$manifest_file" 2>/dev/null || echo '{}')
    
    if [[ "$verification_failed" == "true" ]]; then
        log_error "备份验证失败"
        return 1
    else
        log_success "备份验证完成"
        return 0
    fi
}

# 主备份函数
perform_backup() {
    local backup_type=$1
    local compress=$2
    local encrypt=$3
    local upload=$4
    
    local backup_path=$(create_backup_dir)
    local backup_success=true
    
    log_info "开始 $backup_type 备份..."
    
    case "$backup_type" in
        "all")
            backup_database "$backup_path" "$compress" || backup_success=false
            backup_redis "$backup_path" "$compress" || backup_success=false
            backup_files "$backup_path" "$compress" || backup_success=false
            backup_config "$backup_path" "$compress" || backup_success=false
            ;;
        "database")
            backup_database "$backup_path" "$compress" || backup_success=false
            ;;
        "redis")
            backup_redis "$backup_path" "$compress" || backup_success=false
            ;;
        "files")
            backup_files "$backup_path" "$compress" || backup_success=false
            ;;
        "config")
            backup_config "$backup_path" "$compress" || backup_success=false
            ;;
        *)
            log_error "不支持的备份类型: $backup_type"
            return 1
            ;;
    esac
    
    if [[ "$backup_success" == "true" ]]; then
        # 创建备份清单
        create_manifest "$backup_path"
        
        # 验证备份
        verify_backup "$backup_path"
        
        # 加密备份
        if [[ "$encrypt" == "true" ]]; then
            encrypt_backup "$backup_path"
        fi
        
        # 上传到云存储
        if [[ "$upload" == "true" ]]; then
            upload_to_cloud "$backup_path"
        fi
        
        # 显示备份信息
        local backup_size=$(du -sh "$backup_path" | cut -f1)
        log_success "备份完成: $backup_path (大小: $backup_size)"
        
        return 0
    else
        log_error "备份过程中出现错误"
        return 1
    fi
}

# 主函数
main() {
    local backup_type="all"
    local compress="false"
    local encrypt="false"
    local upload="false"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --compress)
                compress="true"
                shift
                ;;
            --encrypt)
                encrypt="true"
                shift
                ;;
            --upload)
                upload="true"
                shift
                ;;
            all|database|redis|files|config)
                backup_type="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "AI销售助手备份开始"
    log_info "备份类型: $backup_type"
    log_info "备份目录: $BACKUP_DIR"
    log_info "保留天数: $RETENTION_DAYS"
    
    # 检查必要工具
    local required_tools=("pg_dump" "redis-cli" "tar" "gzip")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "缺少必要工具: $tool"
            exit 1
        fi
    done
    
    # 执行备份
    if perform_backup "$backup_type" "$compress" "$encrypt" "$upload"; then
        # 清理旧备份
        cleanup_old_backups "$RETENTION_DAYS"
        
        log_success "备份任务完成"
        exit 0
    else
        log_error "备份任务失败"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

