# 卡密授权管理系统

基于 Python + Flask + MySQL 的卡密授权服务系统，支持容器化部署。

## 功能特性

- **卡密验证 API** - 绑定机器码和有效期控制
- **Web 管理后台** - 完整的增删改查功能
- **批量操作** - 批量生成和导出功能
- **状态管理** - 未使用/已激活/已过期状态
- **容器化部署** - Docker + MySQL 一键部署
- **自动过期** - 定时清理过期卡密

## 项目结构

```
kamisystem/
├── docker-compose.yml      # Docker Compose 配置
├── mysql/                  # MySQL 配置
│   └── init.sql           # 数据库初始化脚本
├── web/                   # Web 应用
│   ├── app.py            # 主应用文件
│   ├── models.py         # 数据模型
│   ├── requirements.txt  # Python 依赖
│   ├── Dockerfile        # Docker 镜像配置
│   ├── routes/           # 路由模块
│   │   ├── api.py       # API 路由
│   │   └── admin.py     # 管理后台路由
│   ├── templates/        # HTML 模板
│   │   ├── base.html    # 基础模板
│   │   ├── index.html   # 管理列表页
│   │   ├── generate.html # 批量生成页
│   │   └── ...
│   ├── static/          # 静态文件
│   │   ├── css/         # CSS 样式
│   │   └── js/          # JavaScript
│   ├── utils/           # 工具模块
│   │   └── export_txt.py # 导出功能
│   └── exports/         # 导出文件目录
└── README.md            # 项目说明
```

## 快速开始

### 1. 克隆项目

```bash
git clone <项目地址>
cd kamisystem
```

### 2. 使用 Docker Compose 部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 停止服务
docker-compose down
```

### 3. 访问系统

- **Web 管理界面**: http://localhost:5000
- **健康检查**: http://localhost:5000/health
- **API 文档**: http://localhost:5000/api/

## API 接口

### 1. 卡密验证接口

**POST** `/api/validate`

请求参数：
```json
{
  "code": "VIP-ABCD123456",
  "machine_code": "PC-UUID-123"
}
```

响应示例：
```json
{
  "status": "success",
  "message": "授权成功",
  "expire_at": "2024-01-01T15:00:00",
  "remaining_hours": 2.5
}
```

### 2. 卡密状态查询

**GET** `/api/status/{code}`

响应示例：
```json
{
  "status": "success",
  "data": {
    "full_code": "VIP-ABCD123456",
    "status": "active",
    "remaining_hours": 2.5,
    "expire_at": "2024-01-01T15:00:00"
  }
}
```

### 3. 健康检查

**GET** `/api/health`

响应示例：
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00",
  "service": "kamisystem"
}
```

## 数据库结构

### cards 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键，自增 |
| prefix | VARCHAR(16) | 卡密前缀 |
| code | VARCHAR(64) | 随机生成主体 |
| full_code | VARCHAR(128) | 完整卡密代码 |
| used_at | DATETIME | 第一次使用时间 |
| expire_at | DATETIME | 过期时间 |
| machine_code | VARCHAR(128) | 绑定设备码 |
| status | ENUM | 状态：unused/active/expired |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 使用说明

### 1. 批量生成卡密

1. 访问 "批量生成" 页面
2. 输入前缀、数量和代码长度
3. 点击 "开始生成"
4. 系统自动生成唯一的卡密

### 2. 导出卡密

1. 在管理列表页面点击 "导出卡密"
2. 可选择按前缀筛选
3. 系统生成 TXT 文件供下载

### 3. 编辑卡密

1. 在管理列表中点击 "编辑"
2. 可修改前缀和状态
3. 保存后自动更新完整代码

### 4. 状态管理

- **未使用** (unused): 新生成的卡密
- **已激活** (active): 已绑定机器码，3小时内有效
- **已过期** (expired): 超过有效期的卡密

## 配置说明

### 环境变量

- `DATABASE_URL`: 数据库连接字符串
- `FLASK_ENV`: Flask 环境 (development/production)
- `SECRET_KEY`: Flask 密钥
- `PORT`: 服务端口

### Docker 配置

修改 `docker-compose.yml` 中的配置：

```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: your-password
      MYSQL_DATABASE: kamisystem
      MYSQL_USER: kamisystem
      MYSQL_PASSWORD: your-password
  
  web:
    environment:
      - DATABASE_URL=mysql+pymysql://kamisystem:your-password@mysql:3306/kamisystem
```

## 开发指南

### 本地开发

1. 安装依赖：
```bash
cd web
pip install -r requirements.txt
```

2. 配置数据库：
```bash
# 创建数据库
mysql -u root -p < ../mysql/init.sql
```

3. 启动应用：
```bash
python app.py
```

### 添加新功能

1. 在 `routes/` 目录下创建新的路由模块
2. 在 `templates/` 目录下创建对应的HTML模板
3. 在 `static/` 目录下添加CSS和JS文件
4. 在 `app.py` 中注册新的蓝图

## 部署说明

### 生产环境部署

1. 修改密钥和密码
2. 配置反向代理（如 Nginx）
3. 设置 SSL 证书
4. 配置日志轮转
5. 设置监控和备份

### 安全建议

1. 更改默认密码
2. 使用强密钥
3. 启用 HTTPS
4. 定期备份数据库
5. 监控系统日志

## 常见问题

### Q: 如何修改卡密有效期？

A: 在 `models.py` 中的 `activate` 方法中修改：
```python
self.expire_at = datetime.utcnow() + timedelta(hours=3)  # 修改小时数
```

### Q: 如何增加新的卡密状态？

A: 在 `models.py` 中修改 `CardStatus` 枚举，并更新数据库表结构。

### Q: 如何自定义导出格式？

A: 在 `utils/export_txt.py` 中修改 `export_unused_cards` 函数。

## 许可证

本项目使用 MIT 许可证。

## 贡献指南

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
