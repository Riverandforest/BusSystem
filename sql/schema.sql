/* =============================================
   2. 创建实体表
   ============================================= */

-- (1) 车队表
CREATE TABLE team (
    team_id VARCHAR(20) PRIMARY KEY,
    leader_name VARCHAR(50) NOT NULL
);

-- (2) 线路表
CREATE TABLE line (
    line_id VARCHAR(20) PRIMARY KEY,
    team_id VARCHAR(20) NOT NULL,
    line_leader_id VARCHAR(20),
    CONSTRAINT fk_line_team FOREIGN KEY (team_id) REFERENCES team(team_id)
);

-- (3) 司机表
CREATE TABLE driver (
    driver_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('男', '女')),
    line_id VARCHAR(20),
    CONSTRAINT fk_driver_line FOREIGN KEY (line_id) REFERENCES line(line_id)
);

-- (4) 车辆表
CREATE TABLE bus (
    plate_num VARCHAR(20) PRIMARY KEY,
    seats INT,
    line_id VARCHAR(20),
    CONSTRAINT fk_bus_line FOREIGN KEY (line_id) REFERENCES line(line_id)
);

-- (5) 违章记录表
CREATE TABLE violation (
    driver_id VARCHAR(20),
    plate_num VARCHAR(20),
    location VARCHAR(100),
    v_time TIMESTAMP DEFAULT NOW(),
    v_type VARCHAR(50),
    CONSTRAINT fk_vio_driver FOREIGN KEY (driver_id) REFERENCES driver(driver_id),
    CONSTRAINT fk_vio_bus FOREIGN KEY (plate_num) REFERENCES bus(plate_num)
);