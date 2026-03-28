from database import DBManager


def init_db():
    try:
        DBManager.initialize_pool()
        print("数据库连接池初始化成功！")
    except Exception as e:
        print(f"数据库连接初始化失败: {e}")


# --- 辅助查询函数 ---

def get_db_options(table_name, column_name):
    """通用：获取某列的所有选项"""
    sql = f"SELECT {column_name} FROM public.{table_name}"
    results = DBManager.fetch_all(sql)
    return [row[0] for row in results]


def get_stations_by_line(line_id):
    sql = """
    SELECT s.station_id, s.station_name 
    FROM public.station s, public.map m 
    WHERE s.station_id = m.station_id 
      AND m.line_id = %s 
    ORDER BY m.station_sequence
    """
    results = DBManager.fetch_all(sql, (line_id,))
    # 返回字典列表，方便前端取用 value 和 text
    return [{"id": row[0], "name": row[1]} for row in results]

def check_leader_authority(user_id):
    # 修改点：不再查询 line_leader 表
    sql = "SELECT line_id FROM public.driver WHERE driver_id = %s AND is_lineleader = TRUE"
    res = DBManager.fetch_all(sql, (user_id,))

    if res:
        return {"is_leader": True, "managed_line": res[0][0]}
    return {"is_leader": False, "managed_line": None}


# --- 数据录入函数 ---

def add_driver(data):
    # 前端传来的 'true'/'false' 字符串或布尔值需要处理
    is_leader = data.get('is_lineleader')
    # 如果是字符串 'true' 则转为 True，否则为 False
    if isinstance(is_leader, str):
        is_leader = (is_leader.lower() == 'true')

    sql = "INSERT INTO public.driver (driver_id, name, gender, line_id, is_lineleader) VALUES (%s, %s, %s, %s, %s)"
    DBManager.execute_query(sql, (data['driver_id'], data['name'], data['gender'], data['line_id'], bool(is_leader)))


def add_bus(data):
    """录入车辆"""
    sql = "INSERT INTO public.bus (plate_num, seats, line_id) VALUES (%s, %s, %s)"
    DBManager.execute_query(sql, (data['plate_num'], data['seats'], data['line_id']))


def add_violation(data):
    sql = "INSERT INTO public.violation (driver_id, plate_num, v_type, location, v_time) VALUES (%s, %s, %s, %s, %s)"
    DBManager.execute_query(sql, (data['driver_id'], data['plate_num'], data['v_type'], data['location'], data['v_time']))


# --- 数据查询函数 ---

def query_team_drivers(team_id):
    sql = """
    SELECT d.driver_id, d.name, d.gender, l.line_id, d.is_lineleader
    FROM public.driver d, public.line l
    WHERE d.line_id = l.line_id AND l.team_id = %s
    """
    results = DBManager.fetch_all(sql, (team_id,))

    data = []
    for r in results:
        # r[4] 是布尔值 is_lineleader
        role = "路队长" if r[4] else "司机"
        data.append({
            "driver_id": r[0],
            "name": r[1],
            "gender": r[2],
            "line_id": r[3],
            "role": role
        })
    return data


def query_driver_violations(driver_id, start_date, end_date):
    """查询司机违章详情"""
    sql = """
    SELECT v_id, v_type, v_time, location, plate_num 
    FROM public.violation 
    WHERE driver_id = %s AND v_time BETWEEN %s AND %s
    ORDER BY v_time DESC
    """
    results = DBManager.fetch_all(sql, (driver_id, start_date, end_date))
    return [{"v_id": r[0], "v_type": r[1], "v_time": r[2].strftime('%Y-%m-%d %H:%M:%S'), "location": r[3],
             "plate_num": r[4]} for r in results]


def query_team_stats(team_id, start_date, end_date):
    """查询车队统计"""
    sql = """
    SELECT v.v_type, COUNT(*) 
    FROM public.violation v, public.driver d, public.line l 
    WHERE v.driver_id=d.driver_id AND d.line_id=l.line_id 
    AND l.team_id=%s AND v.v_time BETWEEN %s AND %s 
    GROUP BY v.v_type
    """
    results = DBManager.fetch_all(sql, (team_id, start_date, end_date))
    return [{"v_type": r[0], "count": r[1]} for r in results]