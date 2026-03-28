import sys
from datetime import datetime
from database import DBManager

VALID_TYPES = ['闯红灯', '压线行驶', '违章停车', '未礼让斑马线', '超速']


def print_menu():
    print("\n" + "=" * 40)
    print(" 公交安全管理系统 ")
    print("=" * 40)
    print("1. 录入司机基本信息")
    print("2. 录入汽车基本信息")
    print("3. 录入司机的违章信息(需路队长权限)")
    print("4. 查询某车队下的司机信息")
    print("5. 查询某司机某时段的违章详情")
    print("6. 查询某车队某时段的违章统计")
    print("0. 退出系统")
    print("=" * 40)


def get_line_by_leader(user_id):
    sql = "SELECT line_id FROM public.driver WHERE driver_id = %s AND is_lineleader = TRUE"
    res = DBManager.fetch_all(sql, (user_id,))
    if res: return res[0][0]
    return None


def get_stations_by_line(line_id):
    sql = """
        SELECT s.station_name 
        FROM public.station s, public.map m 
        WHERE s.station_id = m.station_id 
          AND m.line_id = %s 
        ORDER BY m.station_sequence
        """
    results = DBManager.fetch_all(sql, (line_id,))
    return [row[0] for row in results]


def get_db_options(table_name, column_name):
    sql = f"SELECT {column_name} FROM public.{table_name}"
    results = DBManager.fetch_all(sql)
    return [row[0] for row in results]


def select_from_list(prompt, options):
    print(f"\n{prompt}")
    for i, opt in enumerate(options):
        print(f"{i + 1}. {opt}")
    while True:
        try:
            choice = int(input("请选择序号: "))
            if 1 <= choice <= len(options): return options[choice - 1]
        except:
            pass
        print("输入无效")


def add_driver():
    """功能1：录入司机信息"""
    print("\n[录入司机信息]")
    d_id = input("请输入工号 (如 D051): ")
    name = input("请输入姓名: ")
    gender = input("请输入性别 (男/女): ")
    line_id = input("请输入所属线路号 (请确保该线路已存在): ")

    is_leader_input = input("是否任命为路队长? (y/n, 默认n): ")
    is_leader = True if is_leader_input.lower() == 'y' else False

    try:
        # SQL 只有4个字段，对应4个占位符
        sql = "INSERT INTO public.driver (driver_id, name, gender, line_id, is_lineleader) VALUES (%s, %s, %s, %s, %s)"
        DBManager.execute_query(sql, (d_id, name, gender, line_id, is_leader))
    except Exception as e:
        print(f" 录入失败！错误详情: {e}")


def add_bus():
    """功能2：录入汽车信息"""
    print("\n[录入汽车信息]")
    plate = input("请输入车牌号: ")
    seats = input("请输入座位数: ")
    # 【修改】通用提示
    line_id = input("请输入所属线路号: ")

    try:
        sql = "INSERT INTO public.bus (plate_num, seats, line_id) VALUES (%s, %s, %s)"
        DBManager.execute_query(sql, (plate, seats, line_id))
    except Exception as e:
        print(f" 录入失败！请检查线路号是否存在。错误详情: {e}")


def add_violation():
    print("\n[录入违章]")
    # 1. 权限验证
    op_id = input("请输入您的工号验证身份: ")
    managed_line = get_line_by_leader(op_id)

    if not managed_line:
        print(" 验证失败：您不是路队长，或未被任命！")
        return
    print(f" 身份验证通过。您管理线路: {managed_line}")

    d_id = input("违章司机工号: ")
    plate = input("违章车牌: ")

    # 2. 动态读取数据库里的违章类型
    v_types = get_db_options("violation_type", "type_name")

    stations = get_stations_by_line(managed_line)
    if not stations:
        print(" 该线路暂无站点数据。")
        return

    v_type = select_from_list("违章类型:", v_types)
    location = select_from_list(f"违章地点 (仅显示 {managed_line} 站点):", stations)

    while True:
        v_time = input("时间 (YYYY-MM-DD HH:MM:SS): ")
        try:
            datetime.strptime(v_time, "%Y-%m-%d %H:%M:%S")
            break
        except:
            print(" 格式错误，请重新输入")

    sql = "INSERT INTO public.violation (driver_id, plate_num, v_type, location, v_time) VALUES (%s, %s, %s, %s, %s)"
    DBManager.execute_query(sql, (d_id, plate, v_type, location, v_time))


def query_team_drivers():
    print("\n[查询车队司机]")
    t_id = input("请输入车队编号 (如 T01): ")
    sql = "SELECT d.driver_id, d.name, d.gender, l.line_id, d.is_lineleader FROM public.driver d, public.line l WHERE d.line_id = l.line_id AND l.team_id = %s"
    results = DBManager.fetch_all(sql, (t_id,))
    print(f"\n查询结果 (共 {len(results)} 人):")
    print(f"{'工号':<10}{'姓名':<10}{'性别':<6}{'线路':<8}{'职位'}")
    print("-" * 50)
    for row in results:
        role = "路队长" if row[4] else "司机"  # row[4] 是布尔值
        print(f"{row[0]:<10}{row[1]:<10}{row[2]:<6}{row[3]:<8}{role}")


def query_driver_violations():
    d_id = input("请输入司机工号: ")
    s = input("开始日期 (YYYY-MM-DD): ")
    e = input("结束日期 (YYYY-MM-DD): ")
    sql = "SELECT v_id, v_type, v_time, location, plate_num FROM public.violation WHERE driver_id = %s AND v_time BETWEEN %s AND %s"
    res = DBManager.fetch_all(sql, (d_id, s, e))
    print(f"\n查询结果 (共 {len(res)} 条):")
    for row in res: print(f"[{row[2]}] {row[1]} @ {row[3]} (车牌: {row[4]})")


def query_team_stats():
    tid = input("请输入车队编号 (如 T01): ")
    s = input("开始日期: ")
    e = input("结束日期: ")
    sql = "SELECT v.v_type, COUNT(*) FROM public.violation v, public.driver d, public.line l WHERE v.driver_id=d.driver_id AND d.line_id=l.line_id AND l.team_id=%s AND v.v_time BETWEEN %s AND %s GROUP BY v.v_type"
    res = DBManager.fetch_all(sql, (tid, s, e))
    print(f"\n车队 {tid} 违章统计:")
    if not res:
        print("无记录。")
    else:
        for row in res: print(f"- {row[0]}: {row[1]} 次")


def main():
    try:
        DBManager.initialize_pool()
    except Exception:
        print("无法连接数据库，程序退出。")
        return

    while True:
        print_menu()
        choice = input("请选择功能 (0-6): ")
        if choice == '1':
            add_driver()
        elif choice == '2':
            add_bus()
        elif choice == '3':
            add_violation()
        elif choice == '4':
            query_team_drivers()
        elif choice == '5':
            query_driver_violations()
        elif choice == '6':
            query_team_stats()
        elif choice == '0':
            sys.exit()
        else:
            print("无效输入")
        input("\n按回车键继续...")


if __name__ == "__main__":
    main()