document.addEventListener('DOMContentLoaded', function() {
    // 1. 工具函数

    // 显示全局提示框
    function showAlert(message, type = 'success') {
        const alertBox = document.getElementById('global-alert');
        const alertMsg = document.getElementById('alert-message');

        // 设置样式 (success/danger/warning)
        alertBox.className = `alert alert-${type} alert-dismissible fade show`;
        alertMsg.textContent = message;
        alertBox.style.display = 'block';

        // 成功提示 3秒后自动消失，错误提示需手动关闭
        if (type === 'success') {
            setTimeout(() => { alertBox.style.display = 'none'; }, 3000);
        }
    }

    // 切换功能面板 (SPA效果)
    function switchSection(targetId) {
        // 隐藏所有区域
        document.querySelectorAll('.feature-section').forEach(el => el.classList.remove('active'));
        // 移除导航栏激活状态
        document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));

        // 显示目标区域
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // 激活对应的导航菜单
        const navItem = document.querySelector(`[data-target="${targetId}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }

        // 切换时隐藏旧的提示框
        document.getElementById('global-alert').style.display = 'none';
    }

    // 绑定导航栏点击事件
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            switchSection(targetId);
        });
    });

    // 2. 通用表单提交处理

    function bindFormSubmit(formId, apiEndpoint) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault(); // 阻止默认提交刷新页面

            // 提取表单数据为 JSON
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => data[key] = value);

            // 发送 AJAX 请求
            fetch(apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json().then(resData => ({ status: response.status, body: resData })))
            .then(({ status, body }) => {
                if (status === 200) {
                    showAlert(body.message, 'success');
                    form.reset(); // 成功后清空表单
                } else {
                    showAlert(body.error, 'danger');
                }
            })
            .catch(error => showAlert('请求失败: ' + error, 'danger'));
        });
    }

    // 绑定三个录入表单
    bindFormSubmit('form-add-driver', '/api/add/driver');
    bindFormSubmit('form-add-bus', '/api/add/bus');
    bindFormSubmit('form-add-violation', '/api/add/violation');

    // 3. 特殊功能交互

    // [功能 3] 权限验证与级联数据加载
    const btnCheckAuth = document.getElementById('btn-check-auth');
    if (btnCheckAuth) {
        btnCheckAuth.addEventListener('click', function() {
            const userId = document.getElementById('auth-user-id').value;
            if (!userId) { showAlert('请输入工号', 'warning'); return; }

            fetch('/api/check_authority', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.is_leader) {
                    showAlert('验证成功！', 'success');

                    // 1. 切换界面
                    switchSection('section-add-violation');

                    // 2. 显示管理线路信息
                    document.getElementById('auth-line-info').textContent = `当前管理线路: ${data.managed_line}`;
                    document.getElementById('managed-line-id').value = data.managed_line;

                    // 3. 并行加载：违章类型 + 线路专属站点
                    Promise.all([
                        fetch('/api/options/violation_type/type_name').then(r => r.json()),
                        fetch(`/api/stations/${data.managed_line}`).then(r => r.json())
                    ]).then(([vTypes, stations]) => {
                        // 填充违章类型
                        const typeSelect = document.getElementById('violation-type-select');
                        typeSelect.innerHTML = vTypes.map(t => `<option value="${t}">${t}</option>`).join('');

                        // 填充站点：Value=ID, Text=Name
                        // 后端 logic.py 必须返回 [{'id': '...', 'name': '...'}, ...] 格式
                        const stationSelect = document.getElementById('violation-location-select');
                        stationSelect.innerHTML = stations.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

                        if (stations.length === 0) {
                             showAlert('警告：该线路下暂无站点数据，无法录入。', 'warning');
                        }
                    });
                } else {
                    showAlert('验证失败：您不是路队长，无权操作。', 'danger');
                }
            });
        });
    }

    // [功能 4] 查询车队司机
    const btnQueryDrivers = document.getElementById('btn-query-team-drivers');
    if (btnQueryDrivers) {
        btnQueryDrivers.addEventListener('click', function() {
            const teamId = document.getElementById('query-team-id').value;
            if (!teamId) { showAlert('请输入车队编号', 'warning'); return; }

            fetch(`/api/query/team_drivers?team_id=${teamId}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('tbody-team-drivers');
                tbody.innerHTML = ''; // 清空旧数据

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">无数据</td></tr>';
                    return;
                }

                data.forEach(row => {
                    // 处理职位显示
                    const roleText = row.role ? row.role : '司机';
                    // 给路队长加高亮徽章
                    const roleDisplay = roleText === '路队长'
                        ? `<span class="badge bg-warning text-dark">路队长</span>`
                        : roleText;

                    tbody.innerHTML += `<tr>
                        <td>${row.driver_id}</td>
                        <td>${row.name}</td>
                        <td>${row.gender}</td>
                        <td>${row.line_id}</td>
                        <td>${roleDisplay}</td>
                    </tr>`;
                });
            });
        });
    }

    // [功能 5] 查询司机违章详情
    const btnQueryViolations = document.getElementById('btn-query-driver-violations');
    if (btnQueryViolations) {
        btnQueryViolations.addEventListener('click', function() {
            const dId = document.getElementById('q-driver-id').value;
            const start = document.getElementById('q-dv-start').value;
            const end = document.getElementById('q-dv-end').value;
            if (!dId || !start || !end) { showAlert('请补全查询条件', 'warning'); return; }

            fetch(`/api/query/driver_violations?driver_id=${dId}&start_date=${start}&end_date=${end}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('tbody-driver-violations');
                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">无数据</td></tr>';
                    return;
                }
                data.forEach(row => {
                    tbody.innerHTML += `<tr>
                        <td>${row.v_time}</td>
                        <td>${row.v_type}</td>
                        <td>${row.location}</td>
                        <td>${row.plate_num}</td>
                    </tr>`;
                });
            });
        });
    }

    // [功能 6] 查询车队统计
    const btnQueryStats = document.getElementById('btn-query-team-stats');
    if (btnQueryStats) {
        btnQueryStats.addEventListener('click', function() {
            const tId = document.getElementById('q-stat-team-id').value;
            const start = document.getElementById('q-stat-start').value;
            const end = document.getElementById('q-stat-end').value;
            if (!tId || !start || !end) { showAlert('请补全查询条件', 'warning'); return; }

            fetch(`/api/query/team_stats?team_id=${tId}&start_date=${start}&end_date=${end}`)
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('list-team-stats');
                list.innerHTML = '';
                if (data.length === 0) {
                    list.innerHTML = '<li class="list-group-item text-center">无违章记录</li>';
                    return;
                }
                data.forEach(row => {
                    list.innerHTML += `<li class="list-group-item d-flex justify-content-between align-items-center">
                                            ${row.v_type}
                                            <span class="badge bg-primary rounded-pill">${row.count} 次</span>
                                        </li>`;
                });
            });
        });
    }

    // 4. 初始化工作
    // 自动填充日期选择器为“本月”
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const startOfMonth = `${yyyy}-${mm}-01`;
    // 获取当月最后一天
    const endOfMonth = new Date(yyyy, mm, 0).toISOString().split('T')[0];

    const dateInputs = ['q-dv-start', 'q-stat-start', 'q-dv-end', 'q-stat-end'];
    dateInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (id.includes('start')) el.value = startOfMonth;
            if (id.includes('end')) el.value = endOfMonth;
        }
    });
});