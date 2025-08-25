#!/bin/bash

# 熵变智元AI销售助手 - 部署脚本
# 支持Docker Compose和Kubernetes两种部署方式

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
熵变智元AI销售助手部署脚本

用法: $0 [选项] <部署类型>

部署类型:
  docker          使用Docker Compose部署
  k8s            使用Kubernetes部署
  dev            开发环境部署

选项:
  -h, --help     显示此帮助信息
  -e, --env      指定环境文件路径 (默认: .env)
  -n, --namespace 指定Kubernetes命名空间 (默认: ai-sales-assistant)
  -v, --version  指定版本号 (默认: latest)
  --skip-build   跳过构建步骤
  --skip-migrate 跳过数据库迁移
  --dry-run      仅显示要执行的命令，不实际执行

示例:
  $0 docker                    # Docker Compose部署
  $0 k8s -n production         # Kubernetes生产环境部署
  $0 dev --skip-build          # 开发环境部署，跳过构建
EOF
}

# 检查依赖
check_dependencies() {
    local deploy_type=$1
    
    log_info "检查依赖..."
    
    # 通用依赖
    if ! command -v git &> /dev/null; then
        log_error "Git未安装"
        exit 1
    fi
    
    if [[ "$deploy_type" == "docker" || "$deploy_type" == "dev" ]]; then
        # Docker相关依赖
        if ! command -v docker &> /dev/null; then
            log_error "Docker未安装"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose未安装"
            exit 1
        fi
        
        # 检查Docker服务状态
        if ! docker info &> /dev/null; then
            log_error "Docker服务未运行"
            exit 1
        fi
    fi
    
    if [[ "$deploy_type" == "k8s" ]]; then
        # Kubernetes相关依赖
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl未安装"
            exit 1
        fi
        
        if ! command -v helm &> /dev/null; then
            log_warning "Helm未安装，将跳过Helm部署"
        fi
        
        # 检查Kubernetes连接
        if ! kubectl cluster-info &> /dev/null; then
            log_error "无法连接到Kubernetes集群"
            exit 1
        fi
    fi
    
    log_success "依赖检查完成"
}

# 检查环境变量
check_env_vars() {
    local env_file=$1
    
    log_info "检查环境变量..."
    
    if [[ ! -f "$env_file" ]]; then
        log_error "环境变量文件 $env_file 不存在"
        log_info "请复制 env.example 为 $env_file 并填写实际配置"
        exit 1
    fi
    
    # 加载环境变量
    set -a
    source "$env_file"
    set +a
    
    # 检查必要的环境变量
    local required_vars=(
        "SECRET_KEY"
        "DB_PASSWORD"
        "REDIS_PASSWORD"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必要的环境变量: ${missing_vars[*]}"
        exit 1
    fi
    
    # 检查密码强度
    if [[ ${#SECRET_KEY} -lt 32 ]]; then
        log_warning "SECRET_KEY长度不足32位，建议使用更强的密钥"
    fi
    
    if [[ ${#DB_PASSWORD} -lt 12 ]]; then
        log_warning "数据库密码长度不足12位，建议使用更强的密码"
    fi
    
    log_success "环境变量检查完成"
}

# 构建Docker镜像
build_image() {
    local version=$1
    local skip_build=$2
    
    if [[ "$skip_build" == "true" ]]; then
        log_info "跳过镜像构建"
        return
    fi
    
    log_info "构建Docker镜像..."
    
    local dockerfile_path="infrastructure/docker/Dockerfile"
    local context_path="fastapi-backend"
    
    if [[ ! -f "$dockerfile_path" ]]; then
        log_error "Dockerfile不存在: $dockerfile_path"
        exit 1
    fi
    
    # 构建镜像
    docker build \
        -f "$dockerfile_path" \
        -t "ai-sales-assistant:$version" \
        -t "ai-sales-assistant:latest" \
        "$context_path"
    
    log_success "镜像构建完成"
}

# 数据库迁移
run_migrations() {
    local deploy_type=$1
    local skip_migrate=$2
    
    if [[ "$skip_migrate" == "true" ]]; then
        log_info "跳过数据库迁移"
        return
    fi
    
    log_info "执行数据库迁移..."
    
    if [[ "$deploy_type" == "docker" || "$deploy_type" == "dev" ]]; then
        # Docker环境迁移
        docker-compose -f infrastructure/docker/docker-compose.yml \
            exec -T ai-sales-assistant \
            python -m alembic upgrade head
    elif [[ "$deploy_type" == "k8s" ]]; then
        # Kubernetes环境迁移
        kubectl exec -n "$NAMESPACE" \
            deployment/ai-sales-assistant \
            -- python -m alembic upgrade head
    fi
    
    log_success "数据库迁移完成"
}

# Docker Compose部署
deploy_docker() {
    local version=$1
    local env_file=$2
    local skip_build=$3
    local skip_migrate=$4
    local dry_run=$5
    
    log_info "开始Docker Compose部署..."
    
    local compose_file="infrastructure/docker/docker-compose.yml"
    local env_option=""
    
    if [[ -n "$env_file" ]]; then
        env_option="--env-file $env_file"
    fi
    
    # 构建镜像
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: build_image $version $skip_build"
    else
        build_image "$version" "$skip_build"
    fi
    
    # 启动服务
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: docker-compose $env_option -f $compose_file up -d"
    else
        docker-compose $env_option -f "$compose_file" up -d
    fi
    
    # 等待服务启动
    if [[ "$dry_run" != "true" ]]; then
        log_info "等待服务启动..."
        sleep 30
        
        # 检查服务状态
        if docker-compose -f "$compose_file" ps | grep -q "Up"; then
            log_success "服务启动成功"
        else
            log_error "服务启动失败"
            docker-compose -f "$compose_file" logs
            exit 1
        fi
        
        # 数据库迁移
        run_migrations "docker" "$skip_migrate"
    fi
    
    log_success "Docker Compose部署完成"
}

# Kubernetes部署
deploy_k8s() {
    local version=$1
    local namespace=$2
    local env_file=$3
    local skip_build=$4
    local skip_migrate=$5
    local dry_run=$6
    
    log_info "开始Kubernetes部署..."
    
    local k8s_dir="infrastructure/k8s"
    
    # 构建并推送镜像
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: build_image $version $skip_build"
    else
        build_image "$version" "$skip_build"
        
        # 如果有镜像仓库，推送镜像
        if [[ -n "$DOCKER_REGISTRY" ]]; then
            docker tag "ai-sales-assistant:$version" "$DOCKER_REGISTRY/ai-sales-assistant:$version"
            docker push "$DOCKER_REGISTRY/ai-sales-assistant:$version"
        fi
    fi
    
    # 创建命名空间
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: kubectl apply -f $k8s_dir/namespace.yaml"
    else
        kubectl apply -f "$k8s_dir/namespace.yaml"
    fi
    
    # 应用配置
    local manifests=(
        "configmap.yaml"
        "secrets.yaml"
        "pv.yaml"
        "statefulset.yaml"
        "deployment.yaml"
        "service.yaml"
        "ingress.yaml"
    )
    
    for manifest in "${manifests[@]}"; do
        if [[ -f "$k8s_dir/$manifest" ]]; then
            if [[ "$dry_run" == "true" ]]; then
                log_info "[DRY RUN] 将执行: kubectl apply -f $k8s_dir/$manifest"
            else
                kubectl apply -f "$k8s_dir/$manifest"
            fi
        fi
    done
    
    if [[ "$dry_run" != "true" ]]; then
        # 等待部署完成
        log_info "等待部署完成..."
        kubectl rollout status deployment/ai-sales-assistant -n "$namespace" --timeout=300s
        
        # 数据库迁移
        run_migrations "k8s" "$skip_migrate"
    fi
    
    log_success "Kubernetes部署完成"
}

# 开发环境部署
deploy_dev() {
    local version=$1
    local env_file=$2
    local skip_build=$3
    local dry_run=$4
    
    log_info "开始开发环境部署..."
    
    # 创建开发环境配置
    local dev_compose="infrastructure/docker/docker-compose.dev.yml"
    
    if [[ ! -f "$dev_compose" ]]; then
        # 如果没有开发环境配置，使用主配置
        dev_compose="infrastructure/docker/docker-compose.yml"
    fi
    
    local env_option=""
    if [[ -n "$env_file" ]]; then
        env_option="--env-file $env_file"
    fi
    
    # 构建镜像
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: build_image $version $skip_build"
    else
        build_image "$version" "$skip_build"
    fi
    
    # 启动开发环境
    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] 将执行: docker-compose $env_option -f $dev_compose up -d"
    else
        docker-compose $env_option -f "$dev_compose" up -d
        
        # 显示日志
        log_info "启动完成，显示服务日志..."
        docker-compose -f "$dev_compose" logs -f
    fi
    
    log_success "开发环境部署完成"
}

# 验证部署
verify_deployment() {
    local deploy_type=$1
    local namespace=$2
    
    log_info "验证部署状态..."
    
    if [[ "$deploy_type" == "docker" || "$deploy_type" == "dev" ]]; then
        # 检查Docker服务
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "服务健康检查通过"
        else
            log_error "服务健康检查失败"
            return 1
        fi
    elif [[ "$deploy_type" == "k8s" ]]; then
        # 检查Kubernetes部署
        local service_url=$(kubectl get service nginx-service -n "$namespace" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
        
        if curl -f "http://$service_url/health" &> /dev/null; then
            log_success "服务健康检查通过"
        else
            log_warning "无法访问外部服务，请检查LoadBalancer配置"
        fi
        
        # 显示Pod状态
        kubectl get pods -n "$namespace"
    fi
    
    log_success "部署验证完成"
}

# 主函数
main() {
    local deploy_type=""
    local env_file=".env"
    local namespace="ai-sales-assistant"
    local version="latest"
    local skip_build="false"
    local skip_migrate="false"
    local dry_run="false"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -e|--env)
                env_file="$2"
                shift 2
                ;;
            -n|--namespace)
                namespace="$2"
                shift 2
                ;;
            -v|--version)
                version="$2"
                shift 2
                ;;
            --skip-build)
                skip_build="true"
                shift
                ;;
            --skip-migrate)
                skip_migrate="true"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            docker|k8s|dev)
                deploy_type="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查部署类型
    if [[ -z "$deploy_type" ]]; then
        log_error "请指定部署类型: docker, k8s, 或 dev"
        show_help
        exit 1
    fi
    
    log_info "开始部署 AI销售助手 ($deploy_type 模式)"
    log_info "版本: $version"
    log_info "环境文件: $env_file"
    
    if [[ "$deploy_type" == "k8s" ]]; then
        log_info "命名空间: $namespace"
    fi
    
    # 检查依赖
    check_dependencies "$deploy_type"
    
    # 检查环境变量
    if [[ "$dry_run" != "true" ]]; then
        check_env_vars "$env_file"
    fi
    
    # 执行部署
    case $deploy_type in
        docker)
            deploy_docker "$version" "$env_file" "$skip_build" "$skip_migrate" "$dry_run"
            ;;
        k8s)
            deploy_k8s "$version" "$namespace" "$env_file" "$skip_build" "$skip_migrate" "$dry_run"
            ;;
        dev)
            deploy_dev "$version" "$env_file" "$skip_build" "$dry_run"
            ;;
    esac
    
    # 验证部署
    if [[ "$dry_run" != "true" ]]; then
        verify_deployment "$deploy_type" "$namespace"
    fi
    
    log_success "部署完成！"
    
    # 显示访问信息
    if [[ "$dry_run" != "true" ]]; then
        echo
        log_info "访问信息:"
        if [[ "$deploy_type" == "docker" || "$deploy_type" == "dev" ]]; then
            echo "  API: http://localhost:8000"
            echo "  文档: http://localhost:8000/docs"
            echo "  监控: http://localhost:3000 (Grafana)"
        elif [[ "$deploy_type" == "k8s" ]]; then
            echo "  请查看Ingress配置获取访问地址"
            echo "  kubectl get ingress -n $namespace"
        fi
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

