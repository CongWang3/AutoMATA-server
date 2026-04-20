#!/usr/bin/env bash
# backend/start_docker.sh - Docker 生产环境启动脚本
# 功能：自动检测并初始化 MySQL 用户（幂等），然后启动 uvicorn
# 特点：即使初始化失败也不阻断服务启动（适配新服务器首次部署 + 日常重启场景）

echo "========================================="
echo "AutoMATA Backend Startup (Docker)"
echo "========================================="

# 尝试初始化 MySQL 用户（幂等操作，用户已存在则跳过）
echo "[1/2] Checking/initializing MySQL user..."
python -c "
import sys, logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger('mysql-init')

try:
    from init_mysql_user import init_mysql_user
    logger.info('Running MySQL user initialization...')
    success = init_mysql_user()
    if success:
        logger.info('MySQL user initialization completed')
    else:
        logger.warning('MySQL user initialization returned False (may be config issue)')
except ImportError as e:
    logger.warning('init_mysql_user.py not found, skipping: %s', e)
except Exception as e:
    logger.warning('MySQL user initialization failed (non-fatal): %s', e)
    logger.info('Continuing with uvicorn startup...')
" || echo "⚠️  MySQL user initialization skipped (continuing anyway)"

# 启动 uvicorn
echo "[2/2] Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8005
