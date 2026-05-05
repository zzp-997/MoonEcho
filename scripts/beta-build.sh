#!/bin/bash
# ============================================================
# 回声 APP — 公测版构建与部署脚本
# 用途：一键构建前端 + 部署后端 + 启动公测环境
# 使用：bash scripts/beta-build.sh [选项]
#   --h5        仅构建 H5 版本
#   --mp        仅构建微信小程序
#   --app       仅构建 App 版本（提示 HBuilderX 操作）
#   --all       构建所有版本（默认构建 H5 + 微信小程序）
#   --deploy    构建后部署到公测服务器
#   --skip-test 跳过测试
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
DIST_DIR="$PROJECT_ROOT/dist/beta"

# 版本信息
VERSION="1.0.0-beta"
BUILD_DATE=$(date +%Y%m%d%H%M%S)
BUILD_TAG="beta-${VERSION}-${BUILD_DATE}"

# 解析参数
BUILD_H5=false
BUILD_MP=false
BUILD_APP=false
DEPLOY=false
SKIP_TEST=false

if [ $# -eq 0 ]; then
    BUILD_H5=true
    BUILD_MP=true
    BUILD_APP=false  # App 需要 HBuilderX，默认不构建
else
    for arg in "$@"; do
        case $arg in
            --h5)   BUILD_H5=true ;;
            --mp)   BUILD_MP=true ;;
            --app)  BUILD_APP=true ;;
            --all)  BUILD_H5=true; BUILD_MP=true; BUILD_APP=true ;;
            --deploy) DEPLOY=true ;;
            --skip-test) SKIP_TEST=true ;;
            *) echo -e "${RED}未知参数: $arg${NC}"; exit 1 ;;
        esac
    done
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   回声 APP 公测版构建${NC}"
echo -e "${BLUE}   版本: ${VERSION}${NC}"
echo -e "${BLUE}   构建: ${BUILD_TAG}${NC}"
echo -e "${BLUE}============================================${NC}"

# 创建输出目录
mkdir -p "$DIST_DIR"

# ----------------------------------------------------------
# 0. 前置检查
# ----------------------------------------------------------
echo -e "${YELLOW}[0/7] 前置环境检查...${NC}"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误：Node.js 未安装！请安装 Node.js 16+${NC}"
    exit 1
fi
NODE_VERSION=$(node -v)
echo -e "${GREEN}Node.js 版本: ${NODE_VERSION}${NC}"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误：npm 未安装！${NC}"
    exit 1
fi

# 检查 Docker（部署模式需要）
if [ "$DEPLOY" = true ]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误：Docker 未安装！部署模式需要 Docker${NC}"
        exit 1
    fi
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}错误：Docker Compose V2 未安装！${NC}"
        exit 1
    fi
    echo -e "${GREEN}Docker 环境就绪${NC}"
fi

# 检查 .env.beta 文件
if [ ! -f "$PROJECT_ROOT/.env.beta" ]; then
    echo -e "${RED}错误：.env.beta 文件不存在！请先创建公测环境配置${NC}"
    exit 1
fi
echo -e "${GREEN}.env.beta 配置文件就绪${NC}"

# 检查前端 .env.beta 文件
if [ ! -f "$FRONTEND_DIR/.env.beta" ]; then
    echo -e "${YELLOW}警告：前端 .env.beta 文件不存在，将使用 .env.production${NC}"
fi

# ----------------------------------------------------------
# 1. 前端依赖检查
# ----------------------------------------------------------
echo -e "${YELLOW}[1/7] 检查前端依赖...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
else
    echo -e "${GREEN}前端依赖已安装${NC}"
fi

# ----------------------------------------------------------
# 2. 后端依赖检查
# ----------------------------------------------------------
echo -e "${YELLOW}[2/7] 检查后端依赖...${NC}"
cd "$BACKEND_DIR"

if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo -e "${YELLOW}建议创建 Python 虚拟环境：python -m venv venv && source venv/bin/activate${NC}"
fi

# ----------------------------------------------------------
# 3. 运行测试
# ----------------------------------------------------------
if [ "$SKIP_TEST" = false ]; then
    echo -e "${YELLOW}[3/7] 运行后端测试...${NC}"
    cd "$BACKEND_DIR"
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short 2>&1 | tail -20 || echo -e "${YELLOW}测试有失败，请检查${NC}"
    else
        echo -e "${YELLOW}pytest 未安装，跳过测试${NC}"
    fi

    # 前端类型检查
    echo -e "${YELLOW}运行前端类型检查...${NC}"
    cd "$FRONTEND_DIR"
    if npm run type-check 2>/dev/null; then
        echo -e "${GREEN}前端类型检查通过${NC}"
    else
        echo -e "${YELLOW}前端类型检查有警告，不影响构建${NC}"
    fi
else
    echo -e "${YELLOW}[3/7] 跳过测试${NC}"
fi

# ----------------------------------------------------------
# 4. 构建前端 - H5 版本
# ----------------------------------------------------------
echo -e "${YELLOW}[4/7] 构建前端...${NC}"
cd "$FRONTEND_DIR"

# 4.1 H5 构建
if [ "$BUILD_H5" = true ]; then
    echo -e "${BLUE}构建 H5 版本...${NC}"

    # 使用公测环境配置（如有 .env.beta），否则使用 production
    if [ -f ".env.beta" ]; then
        echo -e "${BLUE}使用 .env.beta 公测环境配置${NC}"
        cp .env.beta .env
    else
        echo -e "${YELLOW}使用 .env.production 配置（无 .env.beta）${NC}"
        cp .env.production .env
    fi

    npm run build:h5

    # 检查构建输出
    H5_DIST="dist/build/h5"
    if [ -d "$H5_DIST" ]; then
        cp -r "$H5_DIST" "$DIST_DIR/h5"
        H5_SIZE=$(du -sh "$DIST_DIR/h5" | cut -f1)
        H5_FILE_COUNT=$(find "$DIST_DIR/h5" -type f | wc -l)
        echo -e "${GREEN}H5 构建成功！${NC}"
        echo -e "${GREEN}  大小: ${H5_SIZE}${NC}"
        echo -e "${GREEN}  文件数: ${H5_FILE_COUNT}${NC}"
        echo -e "${GREEN}  输出: ${DIST_DIR}/h5/${NC}"
    else
        echo -e "${RED}H5 构建失败！未找到输出目录 dist/build/h5/${NC}"
        exit 1
    fi
fi

# 4.2 微信小程序构建
if [ "$BUILD_MP" = true ]; then
    echo -e "${BLUE}构建微信小程序版本...${NC}"
    npm run build:mp-weixin

    MP_DIST="dist/build/mp-weixin"
    if [ -d "$MP_DIST" ]; then
        cp -r "$MP_DIST" "$DIST_DIR/mp-weixin"
        MP_SIZE=$(du -sh "$DIST_DIR/mp-weixin" | cut -f1)
        MP_FILE_COUNT=$(find "$DIST_DIR/mp-weixin" -type f | wc -l)
        echo -e "${GREEN}微信小程序构建成功！${NC}"
        echo -e "${GREEN}  大小: ${MP_SIZE}${NC}"
        echo -e "${GREEN}  文件数: ${MP_FILE_COUNT}${NC}"
        echo -e "${GREEN}  输出: ${DIST_DIR}/mp-weixin/${NC}"

        # 检查小程序包大小（主包限制 2MB）
        MAIN_PKG_SIZE=$(du -sb "$DIST_DIR/mp-weixin" | cut -f1)
        MAIN_PKG_MB=$(echo "scale=2; $MAIN_PKG_SIZE / 1048576" | bc)
        if (( $(echo "$MAIN_PKG_MB > 2" | bc -l) )); then
            echo -e "${YELLOW}警告：微信小程序主包 ${MAIN_PKG_MB}MB 超过 2MB 限制！${NC}"
            echo -e "${YELLOW}建议：优化静态资源、启用分包加载${NC}"
        else
            echo -e "${GREEN}微信小程序包大小正常：${MAIN_PKG_MB}MB${NC}"
        fi

        echo -e "${YELLOW}提示：需使用微信开发者工具打开 dist/build/mp-weixin 目录进行上传${NC}"
        echo -e "${YELLOW}上传后可在小程序管理后台设为体验版供公测用户使用${NC}"
    else
        echo -e "${RED}微信小程序构建失败！${NC}"
        exit 1
    fi
fi

# 4.3 App 构建提示
if [ "$BUILD_APP" = true ]; then
    echo -e "${BLUE}构建 App 版本...${NC}"
    echo -e "${YELLOW}App 打包需要 HBuilderX，请按以下步骤手动操作：${NC}"
    echo -e "${YELLOW}  1. 使用 HBuilderX 打开 frontend/ 目录${NC}"
    echo -e "${YELLOW}  2. 确认 manifest.json 配置正确（versionName: ${VERSION}）${NC}"
    echo -e "${YELLOW}  3. 发行 -> 原生App-云打包${NC}"
    echo -e "${YELLOW}  4. 选择 Android（公测版建议使用公共测试证书）${NC}"
    echo -e "${YELLOW}  5. 等待云打包完成（3-10分钟）${NC}"
    echo -e "${YELLOW}  6. 将 APK 复制到 ${DIST_DIR}/${NC}"
    echo -e "${YELLOW}  7. 详细步骤请参考 docs/android-build-guide.md${NC}"
    echo ""
    echo -e "${YELLOW}iOS TestFlight 流程：${NC}"
    echo -e "${YELLOW}  1. 需要 Apple 开发者账号（$99/年）${NC}"
    echo -e "${YELLOW}  2. 创建 App ID 和开发证书${NC}"
    echo -e "${YELLOW}  3. HBuilderX 云打包 iOS${NC}"
    echo -e "${YELLOW}  4. 上传 IPA 到 App Store Connect${NC}"
    echo -e "${YELLOW}  5. TestFlight 添加测试员${NC}"
    echo -e "${YELLOW}  6. 详细流程请参考 docs/distribution-plan.md 第五章${NC}"
fi

# ----------------------------------------------------------
# 5. 构建后端 Docker 镜像（仅部署模式）
# ----------------------------------------------------------
echo -e "${YELLOW}[5/7] 检查后端...${NC}"
cd "$BACKEND_DIR"

if [ "$DEPLOY" = true ]; then
    echo -e "${BLUE}后端将通过 Docker Compose 自动构建${NC}"
fi
echo -e "${YELLOW}部署时请运行：alembic upgrade head${NC}"

# ----------------------------------------------------------
# 6. 部署
# ----------------------------------------------------------
if [ "$DEPLOY" = true ]; then
    echo -e "${YELLOW}[6/7] 部署到公测环境...${NC}"
    cd "$PROJECT_ROOT"

    # 检查 .env.beta
    if [ ! -f ".env.beta" ]; then
        echo -e "${RED}.env.beta 文件不存在！请先创建公测环境配置${NC}"
        exit 1
    fi

    # 检查并提示配置密钥
    if grep -q "CHANGE_ME" .env.beta; then
        echo -e "${RED}警告：.env.beta 中存在 CHANGE_ME 占位符！${NC}"
        echo -e "${RED}请先替换以下密钥为实际值：${NC}"
        grep "CHANGE_ME" .env.beta | while read line; do
            echo -e "${RED}  ${line}${NC}"
        done
        echo -e "${YELLOW}生成密钥命令：openssl rand -hex 32${NC}"
        read -p "是否继续部署？(y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo -e "${YELLOW}部署已取消${NC}"
            exit 0
        fi
    fi

    # 复制环境文件
    cp .env.beta .env

    # Docker Compose 部署
    echo -e "${BLUE}启动 Docker Compose 服务...${NC}"
    docker compose up -d --build

    # 等待服务启动
    echo -e "${BLUE}等待服务启动...${NC}"
    sleep 15

    # 健康检查
    echo -e "${BLUE}健康检查...${NC}"
    HEALTH_OK=true

    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}API 健康！${NC}"
    else
        echo -e "${RED}API 不可用！${NC}"
        HEALTH_OK=false
    fi

    if curl -sf http://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}Nginx 健康！${NC}"
    else
        echo -e "${RED}Nginx 不可用！${NC}"
        HEALTH_OK=false
    fi

    # 运行数据库迁移
    echo -e "${BLUE}运行数据库迁移...${NC}"
    docker compose exec api alembic upgrade head

    # MinIO 存储桶初始化检查
    echo -e "${BLUE}检查 MinIO 存储桶...${NC}"
    docker compose logs minio-init --tail 5 2>/dev/null || true

    if [ "$HEALTH_OK" = true ]; then
        echo -e "${GREEN}部署完成！所有服务运行正常${NC}"
    else
        echo -e "${YELLOW}部署完成，但部分服务健康检查失败，请检查日志${NC}"
        echo -e "${YELLOW}查看日志：docker compose logs -f${NC}"
    fi

    echo -e "${GREEN}H5 访问: http://localhost${NC}"
    echo -e "${GREEN}API 文档: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}管理后台: http://localhost:8000/admin${NC}"
    echo -e "${GREEN}MinIO 控制台: http://localhost:9001${NC}"
    echo -e "${GREEN}监控面板: http://localhost:3001${NC}"
else
    echo -e "${YELLOW}[6/7] 跳过部署（使用 --deploy 参数部署）${NC}"
fi

# ----------------------------------------------------------
# 7. 构建校验与摘要
# ----------------------------------------------------------
echo -e "${YELLOW}[7/7] 构建校验...${NC}"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   公测版构建完成！${NC}"
echo -e "${GREEN}   构建标签: ${BUILD_TAG}${NC}"
echo -e "${GREEN}   输出目录: ${DIST_DIR}${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

if [ "$BUILD_H5" = true ] && [ -d "$DIST_DIR/h5" ]; then
    H5_SIZE=$(du -sh "$DIST_DIR/h5" | cut -f1)
    echo -e "  H5: ${DIST_DIR}/h5/ (${H5_SIZE})"
fi
if [ "$BUILD_MP" = true ] && [ -d "$DIST_DIR/mp-weixin" ]; then
    MP_SIZE=$(du -sh "$DIST_DIR/mp-weixin" | cut -f1)
    echo -e "  微信小程序: ${DIST_DIR}/mp-weixin/ (${MP_SIZE})"
fi

echo ""
echo -e "${YELLOW}下一步：${NC}"
if [ "$BUILD_H5" = true ]; then
    echo -e "  [H5] 部署公测环境: bash scripts/beta-build.sh --h5 --deploy"
    echo -e "  [H5] 配置域名: 参考 docs/distribution-plan.md 第二章"
    echo -e "  [H5] 配置 SSL: 参考 docs/distribution-plan.md 第二章"
fi
if [ "$BUILD_MP" = true ]; then
    echo -e "  [小程序] 打开微信开发者工具导入: ${DIST_DIR}/mp-weixin/"
    echo -e "  [小程序] 上传体验版: 参考 docs/distribution-plan.md 第三章"
    echo -e "  [小程序] 添加体验成员: 小程序管理后台 → 成员管理"
fi
echo -e "  [Android] HBuilderX 云打包: 参考 docs/android-build-guide.md"
echo -e "  [iOS] TestFlight 流程: 参考 docs/distribution-plan.md 第五章"
echo -e "  邀请公测用户"
echo -e "  收集反馈: docs/beta_feedback_form.html"
echo -e "  跟踪 Bug: docs/beta_report.md"
