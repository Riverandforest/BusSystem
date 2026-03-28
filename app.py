from flask import Flask, render_template, request, jsonify
import logic

app = Flask(__name__)

# 在应用启动时初始化数据库连接
with app.app_context():
    logic.init_db()

# --- 页面路由 ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API 接口 ---

# 获取选项列表 (如违章类型)
@app.route('/api/options/<table_name>/<column_name>', methods=['GET'])
def get_options(table_name, column_name):
    try:
        options = logic.get_db_options(table_name, column_name)
        return jsonify(options)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 检查路队长权限
@app.route('/api/check_authority', methods=['POST'])
def check_authority():
    data = request.get_json()
    user_id = data.get('user_id')
    result = logic.check_leader_authority(user_id)
    return jsonify(result)

# 获取特定线路的站点
@app.route('/api/stations/<line_id>', methods=['GET'])
def get_stations(line_id):
    try:
        stations = logic.get_stations_by_line(line_id)
        return jsonify(stations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 录入数据接口 (通用)
@app.route('/api/add/<type>', methods=['POST'])
def add_data(type):
    data = request.get_json()
    try:
        if type == 'driver':
            logic.add_driver(data)
        elif type == 'bus':
            logic.add_bus(data)
        elif type == 'violation':
            logic.add_violation(data)
        else:
            return jsonify({"error": "无效的数据类型"}), 400
        return jsonify({"message": "录入成功！"}), 200
    except Exception as e:
        # 捕获数据库错误，如外键约束违反等
        return jsonify({"error": f"录入失败: {str(e)}"}), 500

# 查询接口
@app.route('/api/query/team_drivers', methods=['GET'])
def query_team_drivers_api():
    team_id = request.args.get('team_id')
    try:
        results = logic.query_team_drivers(team_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query/driver_violations', methods=['GET'])
def query_driver_violations_api():
    driver_id = request.args.get('driver_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    try:
        results = logic.query_driver_violations(driver_id, start_date, end_date)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query/team_stats', methods=['GET'])
def query_team_stats_api():
    team_id = request.args.get('team_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    try:
        results = logic.query_team_stats(team_id, start_date, end_date)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 设置 debug=True 方便开发调试，host='0.0.0.0' 使局域网可访问
    app.run(debug=True, host='0.0.0.0', port=5000)