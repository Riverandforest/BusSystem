import random
from faker import Faker
from database import DBManager

fake = Faker("zh_CN")

LINES = ['L01', 'L02', 'L03']
STATION_SUFFIXES = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
V_TYPES = ['闯红灯', '压线行驶', '违章停车', '未礼让斑马线', '超速']


def generate_fake_data():
    print(" 开始生成仿真数据 ...")
    DBManager.initialize_pool()
    conn = DBManager.get_connection()
    cursor = conn.cursor()

    try:
        # 1. 初始化违章类型
        print("1. 初始化违章类型...", end="")
        for vt in V_TYPES:
            cursor.execute("SELECT 1 FROM public.violation_type WHERE type_name=%s", (vt,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO public.violation_type (type_name) VALUES (%s)", (vt,))
        print("成功")

        # 2. 生成车队及队长
        print("2. 生成车队及队长...", end="")
        team_ids = []
        for i in range(1, 4):
            t_id = f"T{i:02d}"
            tl_id = f"TL{i:02d}"
            cursor.execute("SELECT 1 FROM public.team_leader WHERE leader_id=%s", (tl_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO public.team_leader (leader_id, name) VALUES (%s, %s)", (tl_id, fake.name()))
            cursor.execute("SELECT 1 FROM public.team WHERE team_id=%s", (t_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO public.team (team_id, leader_id) VALUES (%s, %s)", (t_id, tl_id))
            team_ids.append(t_id)
        print("成功")

        # 3. 生成线路 & 站点 & 线路图
        print("3. 生成线路、站点及Map...", end="")
        line_stations_ids = {}

        for i, l_id in enumerate(LINES):
            t_id = random.choice(team_ids)
            # 插入线路
            cursor.execute("SELECT 1 FROM public.line WHERE line_id=%s", (l_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO public.line (line_id, team_id) VALUES (%s, %s)", (l_id, t_id))

            current_ids = []
            for seq, suffix in enumerate(STATION_SUFFIXES, 1):  # seq 从 1 开始
                # 站点ID (建议用 S_L01_01 这种格式，防止重复)
                s_id = f"S_{l_id}_{suffix}"
                s_name = f"{suffix}站"

                # 插入站点 (Station表)
                cursor.execute("SELECT 1 FROM public.station WHERE station_id=%s", (s_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO public.station (station_id, station_name, line_id) VALUES (%s, %s, %s)",
                                   (s_id, s_name, l_id))

                # 插入线路图 (Map表)
                cursor.execute("SELECT 1 FROM public.map WHERE station_id=%s AND line_id=%s", (s_id, l_id))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO public.map (station_id, line_id, station_sequence) VALUES (%s, %s, %s)",
                                   (s_id, l_id, seq))

                current_ids.append(s_id)  # 这里存名字用于生成违章，但要注意违章表存的是什么

            line_stations_ids[l_id] = current_ids
        print("成功")

        # 4. 生成车辆
        print("4. 生成车辆...", end="")
        bus_plates = []
        for _ in range(20):
            plate = fake.license_plate()
            l_id = random.choice(LINES)
            cursor.execute("SELECT 1 FROM public.bus WHERE plate_num=%s", (plate,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO public.bus (plate_num, seats, line_id) VALUES (%s, %s, %s)",
                               (plate, 45, l_id))
                bus_plates.append(plate)
            else:
                bus_plates.append(plate)
        print("成功")

        # 5. 生成司机并任命路队长
        print("5. 生成司机并任命路队长...", end="")
        driver_ids = []
        driver_line_map = {}
        line_drivers_list = {lid: [] for lid in LINES}  # 记录每条线有哪些司机

        # 5.1 先把所有人都生成为“普通司机” (False)
        for i in range(1, 51):
            d_id = f"D{i:03d}"
            l_id = random.choice(LINES)

            cursor.execute("SELECT 1 FROM public.driver WHERE driver_id=%s", (d_id,))
            if not cursor.fetchone():
                # 默认 is_lineleader = False
                cursor.execute(
                    "INSERT INTO public.driver (driver_id, name, gender, line_id, is_lineleader) VALUES (%s, %s, %s, %s, %s)",
                    (d_id, fake.name(), random.choice(['男', '女']), l_id, False))

            driver_ids.append(d_id)
            driver_line_map[d_id] = l_id
            line_drivers_list[l_id].append(d_id)

        # 5.2 遍历每条线路，随机选一个人为队长 (True)
        for l_id in LINES:
            drivers_in_this_line = line_drivers_list[l_id]
            if drivers_in_this_line:
                lucky_guy = random.choice(drivers_in_this_line)
                # 更新 update
                cursor.execute("UPDATE public.driver SET is_lineleader = TRUE WHERE driver_id = %s", (lucky_guy,))

        print("成功")

        # 6. 生成违章记录
        print("6. 生成违章记录...", end="")
        for _ in range(30):
            if driver_ids and bus_plates:
                d_id = random.choice(driver_ids)
                plate = random.choice(bus_plates)
                v_type = random.choice(V_TYPES)
                my_line = driver_line_map[d_id]
                # 从该线路的站点名列表中选一个
                if my_line in line_stations_ids and line_stations_ids[my_line]:
                    loc_id = random.choice(line_stations_ids[my_line])
                    v_time = fake.date_time_this_year()
                    sql = "INSERT INTO public.violation (driver_id, plate_num, v_type, location, v_time) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (d_id, plate, v_type, loc_id, v_time))
        print("成功")

        conn.commit()
        print("\n 仿真数据填充成功！")

    except Exception as e:
        conn.rollback()
        print(f"\n 生成失败，已回滚: {e}")
    finally:
        cursor.close()
        DBManager.return_connection(conn)


if __name__ == "__main__":
    generate_fake_data()