import pandas as pd
import pymysql
import streamlit as st
import json
import os
import warnings
warnings.filterwarnings("ignore")

db_params = {
    'host': '',  # MySQL 主机地址
    'user': '',  # MySQL 用户名
    'password': '',  # MySQL 密码
    'database': '',  # 数据库名称
    'charset': "utf8mb4"
}

def load_users():
    """从 MySQL 数据库读取数据（使用 pymysql）"""
    try:
        # 连接到 MySQL 数据库
        conn = pymysql.connect(**db_params)

        # 执行查询并将结果加载到 DataFrame
        get_usrs = 'SELECT usrname, password, id FROM users'
        users = pd.read_sql(get_usrs, conn)

        # 关闭数据库连接
        conn.close()

        # 将用户名和密码关联返回
        users = {users.iloc[i][0]: [users.iloc[i][1], users.iloc[i][2]] for i in range(len(users))}
        return users
    except pymysql.MySQLError as e:
        st.error(f"数据库错误: {e}")
        return None
    except Exception as e:
        st.error(f"加载数据时出错: {e}")
        return None


def save_users(users):
    """将用户信息保存到数据库"""
    try:
        # 连接到 MySQL 数据库
        conn = pymysql.connect(**db_params)

        # 遍历用户并更新数据库中的密码
        with conn.cursor() as cursor:
            for username, password in users.items():
                # 确保用户名不存在，则插入新记录
                cursor.execute('SELECT 1 FROM users WHERE usrname = %s', (username,))
                if cursor.fetchone() is None:
                    cursor.execute('INSERT INTO users (usrname, password) VALUES (%s, %s)', (username, password))
            conn.commit()

        # 关闭数据库连接
        conn.close()
    except pymysql.MySQLError as e:
        st.error(f"数据库错误: {e}")
    except Exception as e:
        st.error(f"保存用户数据时出错: {e}")


def create_user(username, password):
    """创建新用户"""
    users = load_users()
    if users is None:
        return False  # 如果无法加载用户，则不能创建新用户

    if username in users:
        return False  # 用户已存在

    # 保存明文密码
    users[username] = password
    save_users(users)
    return True  # 用户创建成功


def authenticate_user():
    """用户认证"""
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
        st.session_state.username = None
        st.session_state.role = None

    if not st.session_state.user_authenticated:
        login_tab, register_tab = st.sidebar.tabs(["登录", "注册"])
        with login_tab:
            username = st.text_input("用户名", key="username_login")
            password = st.text_input("密码", key="password_login", type="password")
            if st.button("登录"):
                users = load_users()
                if users is not None and username in users and password == users[username][0]:
                    st.session_state.user_authenticated = True
                    st.session_state.username = username
                    st.session_state.usr_id = users[username][1]
                    # 假设我们没有角色字段，默认将角色设为空
                    st.success(f"欢迎 {username} 登录")
                else:
                    st.error("登录失败，请检查用户名和密码")
        with register_tab:
            new_username = st.text_input("新用户名", key="new_username")
            new_password = st.text_input("新密码", key="new_password", type="password")
            if st.button("注册"):
                if create_user(new_username, new_password):
                    st.success(f"用户 {new_username} 注册成功！")
                else:
                    st.error("用户注册失败，用户名已存在！")
    return st.session_state.user_authenticated


def logout():
    """用户登出"""
    st.session_state.user_authenticated = False
    st.session_state.username = None
    st.session_state.role = None
