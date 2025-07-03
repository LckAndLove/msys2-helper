@echo off
chcp 65001 > nul
title 卡密授权管理系统启动脚本

echo ======================================
echo   卡密授权管理系统启动脚本
echo ======================================

REM 检查Docker是否安装
docker --version > nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose是否安装
docker-compose --version > nul 2>&1
if errorlevel 1 (
    echo 错误: Docker Compose 未安装，请先安装 Docker Compose
    pause
    exit /b 1
)

REM 创建必要的目录
if not exist "web\exports" mkdir "web\exports"
if not exist "mysql\data" mkdir "mysql\data"

echo.
echo 请确认以下配置：
echo - MySQL 端口: 3306
echo - Web 端口: 5000
echo - 数据库密码: rootpwd
echo.

set /p "confirm=是否继续启动服务? (y/n): "
if /i not "%confirm%"=="y" (
    echo 取消启动
    pause
    exit /b 0
)

REM 启动服务
echo 正在启动服务...
docker-compose up -d

REM 等待服务启动
echo 等待服务启动...
timeout /t 10 /nobreak > nul

REM 检查服务状态
echo 检查服务状态...
docker-compose ps

REM 等待数据库就绪
echo 等待数据库初始化...
timeout /t 5 /nobreak > nul

REM 检查服务健康状态
echo 检查服务健康状态...
curl -f http://localhost:5000/health > nul 2>&1
if errorlevel 1 (
    echo ✗ Web 服务可能还在启动中，请稍后再试
) else (
    echo ✓ Web 服务运行正常
)

echo.
echo ======================================
echo   启动完成！
echo ======================================
echo.
echo 访问地址：
echo   Web 管理界面: http://localhost:5000
echo   API 接口: http://localhost:5000/api/
echo   健康检查: http://localhost:5000/health
echo.
echo 常用命令：
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
echo 默认有以下示例卡密：
echo   VIP-DEMO123456
echo   PREMIUM-TEST789012
echo   BASIC-SAMPLE345678
echo.
echo 如需帮助，请查看 README.md 文件
echo ======================================

pause
