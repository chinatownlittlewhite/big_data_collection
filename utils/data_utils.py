import pandas as pd
import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
import pymysql
import warnings
warnings.filterwarnings("ignore")


# db_params = {
#     'host': os.getenv("DB_HOST"),  # MySQL 主机地址
#     'user': os.getenv("DB_USER"),  # MySQL 用户名
#     'password': os.getenv("DB_PASSWORD"),  # MySQL 密码
#     'database': os.getenv("DB_NAME"),  # 数据库名称
#     'charset': "utf8mb4"
# }

db_params = {
    'host': '',  # MySQL 主机地址
    'user': '',  # MySQL 用户名
    'password': '',  # MySQL 密码
    'database': '',  # 数据库名称
    'charset': "utf8mb4"
}

# 定义爬虫函数
def get_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }

    # 请求网页内容
    response = requests.get(url, headers=headers)

    # 检查请求状态
    if response.status_code == 200:
        print("请求成功，开始解析内容")

        # 使用BeautifulSoup解析网页内容
        soup = BeautifulSoup(response.content, 'html.parser')

        # 使用 CSS 选择器提取信息
        results = soup.select("li.arxiv-result")

        # 存储论文信息
        papers = []

        for result in results:
            # 提取论文ID和链接
            id_tag = result.select_one("p.list-title a")
            paper_id = id_tag.text.strip() if id_tag else "N/A"
            paper_link = id_tag['href'] if id_tag else "N/A"

            # 提取类别
            category_tag = result.select_one("span.tag")
            category = category_tag['data-tooltip'] if category_tag else "N/A"

            # 提取标题
            title_tag = result.select_one("p.title")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            # 提取作者
            authors_tag = result.select_one("p.authors")
            authors = ", ".join(a.get_text(strip=True) for a in authors_tag.select("a")) if authors_tag else "N/A"

            # 提取摘要
            abstract_tag = result.select_one("span.abstract-full")
            abstract = abstract_tag.get_text(strip=True) if abstract_tag else "N/A"

            # 提取提交时间
            submitted_tag = result.select_one("p.is-size-7")
            submitted = submitted_tag.get_text(strip=True).split("Submitted")[-1] if submitted_tag else "N/A"

            # 存储信息到字典
            paper_info = {
                "编号": paper_id,
                "链接": paper_link,
                "类别": category,
                "标题": title,
                "作者": authors,
                "摘要": abstract,
                "提交日期": submitted
            }

            papers.append(paper_info)

        return papers
    else:
        print("请求失败，状态码：", response.status_code)
        return []

# 将数据存入 MySQL 数据库
def save_to_mysql(data):
    try:
        # 连接到 MySQL 数据库
        connection = pymysql.connect(**db_params)
        cursor = connection.cursor()
        print("成功连接到 MySQL 数据库")
        # 插入数据
        insert_query = """
        INSERT IGNORE INTO papers(编号, 链接, 类别, 标题, 作者, 摘要, 提交日期)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for paper in data:
            cursor.execute(insert_query, (
                paper["编号"], paper["链接"], paper["类别"],
                paper["标题"], paper["作者"], paper["摘要"], paper["提交日期"]
            ))

        # 提交事务
        connection.commit()
        print("数据已成功存入 MySQL 数据库")
        return len(data)

    except pymysql.MySQLError as err:
        print("MySQL 错误：", err)

    finally:
        # 关闭连接
        if connection.open:
            cursor.close()
            connection.close()
            print("MySQL 连接已关闭")

def load_data(query):
    """从 MySQL 数据库读取数据（使用 pymysql）"""
    try:
        # 连接到 MySQL 数据库
        conn = pymysql.connect(**db_params)
        # 执行查询并将结果加载到 DataFrame
        df = pd.read_sql(query, conn)

        # 关闭数据库连接
        conn.close()

        return df
    except pymysql.MySQLError as e:
        st.error(f"数据库错误: {e}")
        return None
    except Exception as e:
        st.error(f"加载数据时出错: {e}")
        return None


def load_users_subscriptions():
    """从 MySQL 数据库加载用户和订阅信息"""
    try:
        # 连接到 MySQL 数据库
        conn = pymysql.connect(**db_params)

        # 获取所有用户
        get_users_query = 'SELECT id, usrname FROM users'
        users_df = pd.read_sql(get_users_query, conn)

        # 获取所有用户的订阅信息
        get_subscriptions_query = '''
        SELECT s.user_id, p.id, p.编号, p.标题
        FROM subscriptions s
        JOIN papers p ON s.paper_id = p.id
        '''
        subscriptions_df = pd.read_sql(get_subscriptions_query, conn)

        # 关闭数据库连接
        conn.close()

        # 组织用户和订阅信息
        users = {}
        for _, row in users_df.iterrows():
            username = row['usrname']
            user_id = row['id']
            # 获取该用户的订阅信息
            user_subscriptions = subscriptions_df[subscriptions_df['user_id'] == user_id]
            subscribed_papers = user_subscriptions[['id', '编号', '标题']].to_dict(orient='records')
            users[username] = subscribed_papers

        return users
    except pymysql.MySQLError as e:
        print(f"数据库错误: {e}")
        return {}
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return {}


def filter_data_by_user(df, user):
    """根据用户订阅过滤数据"""
    users = load_users_subscriptions()
    if user not in users:
        return pd.DataFrame()  # 用户不存在，返回空 DataFrame

    subscribed_paper_ids = [subscription['id'] for subscription in users[user]]
    filtered_df = df[df['id'].isin(subscribed_paper_ids)]

    return filtered_df


def subscribe_paper(user, paper_id):
    """订阅论文"""
    users = load_users_subscriptions()
    if user in users:
        # 获取用户的 ID
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE usrname = %s", (user,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]

        # 检查论文是否存在
        cursor.execute("SELECT id FROM papers WHERE id = %s", (paper_id,))
        paper_result = cursor.fetchone()
        if paper_result:
            paper_id = paper_result[0]
            # 插入订阅记录
            cursor.execute("INSERT INTO subscriptions (user_id, paper_id) VALUES (%s, %s)", (user_id, paper_id))
            conn.commit()
            cursor.close()
            return True
    return False


def unsubscribe_paper(user, paper_id):
    """取消订阅论文"""
    users = load_users_subscriptions()
    if user in users:
        # 获取用户的 ID
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE usrname = %s", (user,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]

        # 检查论文是否存在
        cursor.execute("SELECT id FROM papers WHERE id = %s", (paper_id,))
        paper_result = cursor.fetchone()
        if paper_result:
            paper_id = paper_result[0]
            # 删除订阅记录
            cursor.execute("DELETE FROM subscriptions WHERE user_id = %s AND paper_id = %s", (user_id, paper_id))
            conn.commit()
            cursor.close()
            return True
    return False


def get_paper_count(keywords):
    """获取符合条件的论文总数"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM papers WHERE 1=1"
        params = []

        for keyword in keywords:
            query += " AND (标题 LIKE %s OR 类别 LIKE %s OR 摘要 LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        cursor.execute(query, tuple(params))
        count = cursor.fetchone()[0]
        return count

    except pymysql.Error as err:
        print(f"Error: {err}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()

def get_papers(keywords, page_num, page_size):
    """获取指定页的论文数据"""
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**db_params)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = "SELECT * FROM papers WHERE 1=1"
        params = []

        for keyword in keywords:
            query += " AND (标题 LIKE %s OR 类别 LIKE %s OR 摘要 LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        query += " ORDER BY id LIMIT %s OFFSET %s"
        params.extend([page_size, (page_num - 1) * page_size])

        cursor.execute(query, tuple(params))
        papers = cursor.fetchall()
        return pd.DataFrame(papers)

    except pymysql.Error as err:
        print(f"Error: {err}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()