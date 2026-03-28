/* =============================================
   1. 补充约束 (处理循环依赖)
   ============================================= */
--线路表的路队长必须是司机，这个约束只能等司机表建好后才能加
ALTER TABLE public.line ADD CONSTRAINT fk_line_leader
FOREIGN KEY (line_leader_id) REFERENCES public.driver(driver_id);

/* =============================================
   2. 创建索引 (加快查询速度)
   ============================================= */
-- 加快按姓名查询司机的速度
CREATE INDEX idx_driver_name ON public.driver(name);
-- 加快按时间段统计违章的速度
CREATE INDEX idx_violation_time ON public.violation(v_time);

/* =============================================
   3. 创建视图 (简化查询)
   ============================================= */
-- 创建一个视图，直接展示“违章详情+司机姓名+车队名”，方便前台查询
CREATE OR REPLACE VIEW public.v_violation_details AS
SELECT
    v.v_id,
    v.v_type,
    v.v_time,
    d.name AS driver_name,
    l.team_id
FROM public.violation v
JOIN public.driver d ON v.driver_id = d.driver_id
JOIN public.line l ON d.line_id = l.line_id;