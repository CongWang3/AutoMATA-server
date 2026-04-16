"""
MySQL 用户初始化脚本 - 生产环境部署使用
在 Docker 容器启动时自动创建 automata 用户并授权
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)


def init_mysql_user():
    """
    初始化 MySQL 用户
    
    使用 root 用户连接到 MySQL，创建 automata 用户并授权。
    仅在用户不存在时创建，保证幂等性。
    """
    import pymysql
    
    # 从环境变量获取 MySQL root 配置
    mysql_host = os.environ.get("DB_HOST", "mysql")
    mysql_port = int(os.environ.get("DB_PORT", "3306"))
    root_password = os.environ.get("MYSQL_ROOT_PASSWORD", "")
    
    # 要创建的用户信息
    db_user = os.environ.get("DB_USER", "automata")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "automata")
    
    if not root_password:
        logger.warning("MYSQL_ROOT_PASSWORD 未设置，跳过用户创建")
        return False
    
    if not db_password:
        logger.warning("DB_PASSWORD 未设置，跳过用户创建")
        return False
    
    logger.info("开始初始化 MySQL 用户: %s@%% (host=%s, port=%s)", db_user, mysql_host, mysql_port)
    
    try:
        # 使用 root 用户连接
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user="root",
            password=root_password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        
        with connection.cursor() as cursor:
            # 检查用户是否已存在
            cursor.execute(
                "SELECT COUNT(*) as count FROM mysql.user WHERE User = %s",
                (db_user,),
            )
            result = cursor.fetchone()
            user_exists = result["count"] > 0 if result else False
            
            if user_exists:
                logger.info("用户 %s 已存在，跳过创建", db_user)
            else:
                # 创建用户（允许从任意主机连接，Docker 网络中容器 IP 会变化）
                logger.info("创建用户 %s...", db_user)
                cursor.execute(
                    "CREATE USER %s@'%%' IDENTIFIED BY %s",
                    (db_user, db_password),
                )
                logger.info("用户 %s 创建成功", db_user)
            
            # 检查数据库是否存在
            cursor.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (db_name,),
            )
            db_exists = cursor.fetchone()
            
            if not db_exists:
                # 创建数据库
                logger.info("创建数据库 %s...", db_name)
                cursor.execute(
                    f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.info("数据库 %s 创建成功", db_name)
            
            # 授权（无论用户是否已创建，都确保权限正确）
            logger.info("授予 %s 数据库权限给 %s...", db_name, db_user)
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON {db_name}.* TO %s@'%%'",
                (db_user,),
            )
            
            # 刷新权限
            cursor.execute("FLUSH PRIVILEGES")
            logger.info("权限刷新完成")
            
            # 验证权限
            cursor.execute(
                "SHOW GRANTS FOR %s@'%%'",
                (db_user,),
            )
            grants = cursor.fetchall()
            logger.info("用户 %s 的权限:", db_user)
            for grant in grants:
                logger.info("  - %s", grant.get("Grants for automata@%", ""))
        
        connection.close()
        logger.info("✅ MySQL 用户初始化完成")
        return True
        
    except pymysql.Error as e:
        logger.error("❌ MySQL 错误: %s", e)
        return False
    except Exception as e:
        logger.error("❌ 其他错误: %s", e)
        return False


if __name__ == "__main__":
    import logging as _logging

    # 配置日志
    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    
    logger.info("=" * 60)
    logger.info("MySQL 用户初始化脚本")
    logger.info("=" * 60)
    
    success = init_mysql_user()
    
    if success:
        logger.info("✅ 初始化成功")
        sys.exit(0)
    else:
        logger.error("❌ 初始化失败")
        sys.exit(1)
