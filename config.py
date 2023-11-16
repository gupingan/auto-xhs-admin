"""File: config.py    Author: 顾平安"""
# 配置数据库
DATABASE_PARAMS = {
    "host": "<your_host>",
    "port": 3306,
    "user": "<your_user>",
    "password": "<your_password>",
    "database": "auto_xhs_db",
    "charset": "utf8mb4",
}
# 你的服务器地址/api
BASE_API = "http://127.0.0.1:5000/api"

try:
    from config_prod import *
except ImportError:
    pass

try:
    from config_dev import *
except ImportError:
    pass
