#!/bin/bash

# 卡密授权管理系统启动脚本

echo "======================================"
echo "  卡密授权管理系统启动脚本"
echo "======================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查端口是否被占用
check_port() {
    local port=$1
    if ss -tuln | grep ":$port " > /dev/null; then
        echo "警告: 端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 创建必要的目录
mkdir -p web/exports
mkdir -p mysql/data

# 检查关键端口
echo "检查端口占用情况..."
check_port 3306 || echo "MySQL 端口 3306 被占用，请检查配置"
check_port 5000 || echo "Web 端口 5000 被占用，请检查配置"

# 提示用户配置
echo ""
echo "请确认以下配置："
echo "- MySQL 端口: 3306"
echo "- Web 端口: 5000"
echo "- 数据库密码: rootpwd"
echo ""

read -p "是否继续启动服务? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消启动"
    exit 0
fi

# 启动服务
echo "正在启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 等待数据库就绪
echo "等待数据库初始化..."
sleep 5

# 检查服务健康状态
echo "检查服务健康状态..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ Web 服务运行正常"
else
    echo "✗ Web 服务可能还在启动中，请稍后再试"
fi

echo ""
echo "======================================"
echo "  启动完成！"
echo "======================================"
echo ""
echo "访问地址："
echo "  Web 管理界面: http://localhost:5000"
echo "  API 接口: http://localhost:5000/api/"
echo "  健康检查: http://localhost:5000/health"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "默认有以下示例卡密："
echo "  VIP-DEMO123456"
echo "  PREMIUM-TEST789012"
echo "  BASIC-SAMPLE345678"
echo ""
echo "如需帮助，请查看 README.md 文件"
echo "======================================"
