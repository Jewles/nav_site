# IT 导航站 (IT Nav Site)

轻量级团队书签导航工具，用于集中管理常用运维、监控、CI/CD、云服务等链接。

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-2.3+-green)
![MySQL](https://img.shields.io/badge/mysql-5.7+-orange)

## 功能

- **分类管理** — 按分类组织链接，支持拖拽排序并自动保存
- **链接 CRUD** — 添加、编辑、删除书签，自动补全 `https://` 前缀
- **实时搜索** — 首页按名称、URL、描述模糊过滤
- **壁纸系统** — 上传/替换/移除背景壁纸，支持 PNG/JPG/WebP/GIF
- **管理后台** — `/admin` 独立管理面板，所有操作表单化
- **响应式设计** — 自适应桌面/移动端，毛玻璃导航栏 + 卡片动画


## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+ / MariaDB 10.3+
- pip

### 2. 安装依赖

```bash
cd nav_site
pip install -r requirements.txt
```

### 3. 数据库配置

项目通过环境变量配置 MySQL 连接，默认值见下表：

| 变量名 | 默认值      | 说明 |
|--------|----------|------|
| `NAV_DB_HOST` | `你的IP`   | 数据库主机 |
| `NAV_DB_PORT` | `3306`   | 数据库端口 |
| `NAV_DB_USER` | `你的SQL用户` | 数据库用户 |
| `NAV_DB_PASS` | `用户密码`   | 数据库密码 |
| `NAV_DB_NAME` | `自定义库名`  | 数据库名 |

示例启动，覆盖默认配置：

```bash
export NAV_DB_HOST=127.0.0.1
export NAV_DB_USER=root
export NAV_DB_PASS=yourpassword
export NAV_DB_NAME=nav_site
```

首次启动会自动创建库和表，并预置以下分类：

- 监控平台
- CI/CD
- 云服务
- 运维工具
- 文档/Wiki

### 4. 启动

```bash
python app.py
```

默认监听 `0.0.0.0:5800`，浏览器访问 `http://localhost:5800`。

生产环境建议用 Gunicorn 或 uWSGI 部署。

## 项目结构

```
nav_site/
├── app.py                  # Flask 应用入口 & 所有路由
├── requirements.txt        # Python 依赖
├── static/
│   └── wallpapers/         # 上传的壁纸文件
├── templates/
│   ├── index.html          # 首页（分类 + 链接展示）
│   └── admin.html          # 管理后台
├── nav.db                  # SQLite (未使用，实际使用 MySQL)
└── README.md
```

> 项目中残留的 `nav.db-wal` / `nav.db-shm` 是 SQLite 遗留文件，可安全删除。

## 技术栈

- **后端** — Flask + PyMySQL
- **前端** — 原生 HTML/CSS/JS（无框架），Inter 字体
- **存储** — MySQL（InnoDB），表 `categories`（分类）和 `links`（链接）

## API 路由

| 方法 | 路由 | 说明 |
|------|------|------|
| `GET` | `/` | 首页 |
| `GET` | `/admin` | 管理后台 |
| `POST` | `/cat/reorder` | 重排分类顺序 |
| `POST` | `/cat/add` | 添加分类 |
| `POST` | `/cat/<id>/delete` | 删除分类（级联删除链接） |
| `POST` | `/link/add` | 添加链接 |
| `POST` | `/link/<id>/edit` | 编辑链接 |
| `POST` | `/link/<id>/delete` | 删除链接 |
| `POST` | `/wallpaper/upload` | 上传壁纸 |
| `POST` | `/wallpaper/remove` | 移除所有壁纸 |
| `GET` | `/wallpapers/<filename>` | 壁纸静态文件 |

## 授权

MIT
