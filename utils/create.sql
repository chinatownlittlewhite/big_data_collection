CREATE TABLE papers(
    id INT AUTO_INCREMENT PRIMARY KEY,
    编号 VARCHAR(255) UNIQUE,
    链接 TEXT,
    类别 VARCHAR(255),
    标题 TEXT,
    作者 TEXT,
    摘要 TEXT,
    提交日期 VARCHAR(255)
);
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- 自动增长的用户ID
    usrname VARCHAR(255) NOT NULL UNIQUE,  -- 用户名，确保唯一
    password VARCHAR(255) NOT NULL,        -- 用户的明文密码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 记录创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- 记录更新时间
);
CREATE TABLE subscriptions (
    user_id INT,                        -- 外键，指向 `users` 表的 `id`
    paper_id INT,                        -- 外键，指向 `papers` 表的 `id`
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 订阅时间
    PRIMARY KEY (user_id, paper_id),     -- 用户和论文的组合唯一
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);


CREATE OR REPLACE VIEW paper_subscription_summary AS
SELECT
    (SELECT COUNT(*) FROM users) AS total_user,  -- 用户总数
    (SELECT COUNT(*) FROM papers) AS total_papers,  -- 论文总数
    (SELECT COUNT(*) FROM subscriptions) AS total_subscriptions, -- 用户订阅数
    (
        SELECT 类别
        FROM papers
        GROUP BY 类别
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) AS most_frequent_category, -- 数量最多的类别
    (
        SELECT JSON_OBJECTAGG(category_count.类别, category_count.count)
        FROM (
            SELECT 类别, COUNT(*) AS count
            FROM papers
            GROUP BY 类别
        ) AS category_count
    ) AS category_counts -- 不同类别论文的数量 (以 JSON 格式返回)
;

CREATE OR REPLACE VIEW user_paper_info AS
SELECT
    s.user_id,
    s.paper_id,
    p.标题,
    p.摘要,
    p.链接
FROM
    subscriptions s
JOIN
    papers p ON s.paper_id = p.id;