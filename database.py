import psycopg2
from psycopg2 import pool, OperationalError

# 数据库配置信息
"""DB_CONFIG = {
    "host": "192.168.10.8",      # 板子的 IP，连不上请换 192.168.23.206
    "port": "5432",              # 端口
    "user": "gaussdb",           # 用户名
    "password": "Bus_2025@Safe", # 密码
    "database": "postgres"       # 初始连接默认库
}"""
DB_CONFIG = {
    "host": "192.168.254.129",      # 您的新 IP
    "port": "5432",
    "user": "dev",                  # 您的新用户名
    "password": "Dbtest@123456",    # 您的新密码
    "database": "postgres",
    # 建议加上这个选项，确保查询默认指向 public 模式
    "options": "-c search_path=public"
}

class DBManager:
    """数据库连接管理器"""
    _connection_pool = None

    @staticmethod
    def initialize_pool():
        """初始化连接池"""
        if DBManager._connection_pool is None:
            try:
                DBManager._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    **DB_CONFIG
                )
                print("数据库连接池初始化成功")
            except OperationalError as e:
                print(f"数据库连接失败: {e}")
                raise e

    @staticmethod
    def get_connection():
        """从池中获取一个连接"""
        if DBManager._connection_pool is None:
            DBManager.initialize_pool()
        return DBManager._connection_pool.getconn()

    @staticmethod
    def return_connection(conn):
        """将连接归还给池"""
        if DBManager._connection_pool and conn:
            DBManager._connection_pool.putconn(conn)

    @staticmethod
    def execute_query(query, params=None):
        """执行查询（INSERT/UPDATE/DELETE）并自动提交"""
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            print(f"执行成功: {query[:30]}...")
        except Exception as e:
            conn.rollback()
            print(f"执行出错: {e}")
        finally:
            cursor.close()
            DBManager.return_connection(conn)

    @staticmethod
    def fetch_all(query, params=None):
        """执行查询（SELECT）并返回所有结果"""
        conn = DBManager.get_connection()
        cursor = conn.cursor()
        result = []
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
        except Exception as e:
            print(f"查询出错: {e}")
        finally:
            cursor.close()
            DBManager.return_connection(conn)
        return result

# 测试代码：如果直接运行这个文件，会尝试连接
if __name__ == "__main__":
    try:
        DBManager.initialize_pool()
        # 测试查询版本
        version = DBManager.fetch_all("SELECT version();")
        print(f"数据库版本: {version[0][0]}")
    except Exception:
        print("请检查 IP 地址是否正确，或防火墙是否放行。")