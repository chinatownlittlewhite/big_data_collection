import os

import streamlit as st
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt

from utils import auth_utils, data_utils
import google.generativeai as genai
from streamlit_tags import st_tags
from utils import similarity_utils

genai.configure(api_key="GOOGLE_API_KEY", transport="rest")

def generate_response(chat, prompt):
    """使用 Gemini API 生成回复."""
    response = chat.send_message(prompt)
    return response.text

# 主程序
def main():
    st.set_page_config(page_title="ArXiv 论文管理平台", layout="wide", page_icon=":books:")

    # --- Sidebar ---
    with st.sidebar:
        st.title("ArXiv 论文管理平台")

        # 页面刷新时保持登录状态
        if 'user_authenticated' not in st.session_state:
            st.session_state.user_authenticated = False

        # 用户认证
        if not st.session_state.user_authenticated:
            if auth_utils.authenticate_user():
                st.session_state.user_authenticated = True
                st.rerun()
            else:
                st.stop()

        if st.button('退出登录'):
            auth_utils.logout()
            st.session_state.user_authenticated = False
            st.rerun()

        # 获取当前用户名
        user = st.session_state.get("username")

        # 侧边栏菜单
        menu = ["首页", "论文订阅与爬取", "相关性分析","论文问答", "个人资料"]
        choice = st.radio("请选择功能", menu)

    # --- Pages ---

    # 首页
    if choice == "首页":
        st.write(f"# 欢迎, {user}! :wave:")
        st.write("这是一个基于 ArXiv 论文数据库的管理平台，您可以方便地搜索、阅读、订阅和分析最新的学术论文。")
        query = "SELECT * FROM paper_subscription_summary"
        data = data_utils.load_data(query)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("论文总数", data['total_papers'][0])
        with col2:
            st.metric("用户总数", data['total_user'][0])
        with col3:
            st.metric("当前用户订阅数", data['total_subscriptions'][0])
        st.metric("热门类别", data['most_frequent_category'][0])

        # st.subheader("论文类别分布")
        # # 改进配色和交互
        # category_counts = json.loads(data['category_counts'][0])
        # df = pd.DataFrame(list(category_counts.items()), columns=['类别', '数量'])
        # df = df.sort_values('数量', ascending=False)  # 添加此行进行降序排序
        #
        # # 创建柱状图
        # fig_category = px.bar(df, x='类别', y='数量', title='论文数量按类别分布', color='类别',
        #                       color_discrete_sequence=px.colors.qualitative.Pastel)
        # fig_category.update_layout(xaxis_title="类别", yaxis_title="论文数量", showlegend=False)
        # st.plotly_chart(fig_category, use_container_width=True)

        st.subheader("平台功能亮点")
        st.markdown("""
        - **智能问答：** 使用 Google 最新的 Gemini 模型，与论文进行智能对话，快速获取关键信息。
        - **统计分析：** 提供丰富的统计图表，帮助您深入了解论文数据，发现研究趋势。
        - **个性化订阅：** 根据您的兴趣订阅论文，不错过任何一篇重要文献。
        - **用户友好：** 简洁直观的界面设计，让您轻松上手。
        """)

        st.subheader("开始使用")
        st.write("请使用左侧导航栏选择您想要使用的功能。")

    # 论文问答页面
    elif choice == "论文问答":
        st.header("论文问答 :speech_balloon:")
        st.markdown("""
            选择一篇您感兴趣的论文，然后使用 Gemini 模型进行问答。请尽情探索奥秘吧！
        """)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "chat" not in st.session_state:
            # model = genai.GenerativeModel('gemini-pro')
            model = genai.GenerativeModel('gemini-1.5-flash')
            st.session_state.chat = model.start_chat(history=[])

        filtered_df = data_utils.load_data("SELECT * FROM user_paper_info WHERE user_id = " + str(st.session_state.usr_id))
        if filtered_df.empty:
            st.write("您还没有订阅任何论文。")
            st.stop()
        selected_paper = st.selectbox("选择论文", filtered_df['标题'], key="select_paper", help="请选择您要进行问答的论文")

        if selected_paper:
            # 获取选定论文的摘要
            selected_paper_info = filtered_df[filtered_df['标题'] == selected_paper].iloc[0]
            paper_summary = selected_paper_info['摘要']
            paper_url = selected_paper_info['链接']

            with st.expander("查看论文摘要", expanded=False):
                st.write(paper_summary)
            st.write(f"论文链接: {paper_url}")
            st.write("---")

            # 显示聊天记录
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            user_prompt = st.text_input("给Gemini发送消息:", key="user_prompt", help="您可以在这里输入您的问题")
            if st.button("发送"):
                if user_prompt:
                    with st.spinner("正在调用 Gemini API..."):
                        full_prompt = f"请结合以下论文摘要回答我的问题：\n{paper_summary}\n\n问题：{user_prompt}"
                        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
                        with st.chat_message("user"):
                            st.markdown(user_prompt)

                    # 生成 Gemini 回复
                    with st.spinner("思考中..."):
                        gemini_response = generate_response(st.session_state.chat, full_prompt)

                    # 将 Gemini 回复添加到聊天记录
                    st.session_state.chat_history.append({"role": "Gemini", "content": gemini_response})
                    with st.chat_message("Gemini"):
                        st.markdown(gemini_response)

    # 数据展示与订阅页面
    elif choice == "论文订阅与爬取":
        st.header("论文订阅与爬取 :bookmark_tabs:")
        st.markdown("""
            在这里浏览论文数据，并根据关键词搜索您感兴趣的论文。您还可以订阅您感兴趣的论文，以便及时获取更新。
        """)

        keywords = st_tags(
            label='## 输入关键词进行搜索:',
            text='按回车键添加关键词',
            value=[],
            suggestions=['machine learning', 'deep learning', 'computer vision', 'natural language processing'],
            maxtags=5,
            key='1'
        )

        # 分页参数
        page_size = 10  # 每页显示的论文数量
        page_num = st.session_state.get("page_num", 1)  # 当前页码，默认为第一页

        # 获取数据总数（根据关键词过滤）
        total_count = data_utils.get_paper_count(keywords)
        # 总页数
        total_pages = (total_count + page_size - 1) // page_size

        # 从数据库中获取当前页的数据
        search_df = data_utils.get_papers(keywords, page_num, page_size)

        users = data_utils.load_users_subscriptions()
        subscribed_paper_ids = [subscription['id'] for subscription in users.get(user, [])]

        st.subheader("论文列表")
        with st.expander("查看论文列表", expanded=True):
            for index, row in search_df.iterrows():
                paper_id = row['id']
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.write(f"**{row['标题']}**")
                    st.write(f"作者: {row['作者']}")
                    st.write(f"类别: {row['类别']}")
                    st.write(f"链接: {row['链接']}")
                with col2:
                    if paper_id in subscribed_paper_ids:
                        if st.button("取消订阅", key=f"unsubscribe_{page_num}_{index}"):
                            if data_utils.unsubscribe_paper(user, paper_id):
                                st.success(f"取消订阅成功！")
                                st.rerun()
                            else:
                                st.error("取消订阅失败，请重试")
                    else:
                        if st.button("订阅", key=f"subscribe_{page_num}_{index}"):
                            if data_utils.subscribe_paper(user, paper_id):
                                st.success(f"订阅成功！")
                                st.rerun()
                            else:
                                st.error("订阅失败，请重试")
                st.write("---")

            # 分页导航
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                if page_num > 1:
                    with col1:
                        st.write(" ")
                        st.write(" ")
                        if st.button("上一页"):
                            st.session_state.page_num = page_num - 1
                            st.rerun()
                with col2:
                    st.write(" ")
                    st.write(" ")
                    st.write(f"第 {page_num} / {total_pages} 页")
                if page_num < total_pages:
                    with col3:
                        st.write(" ")
                        st.write(" ")
                        if st.button("下一页"):
                            st.session_state.page_num = page_num + 1
                            st.rerun()
                with col4:
                    num = st.number_input("跳转到页码", min_value=1, max_value=total_pages, value=page_num, key="page_num")
                with col5:
                    st.write(" ")
                    st.write(" ")
                    if st.button("跳转"):
                        st.session_state.page_num = num
                        st.rerun()
            else:
                st.write("未找到相关论文。")
        st.subheader("没有找到想要的论文？")
        query = st.text_input("输入您感兴趣的论文主题:")
        query = query.replace(" ", "+")
        st.write("输入需要爬取的论文数量")
        col1, col2 = st.columns(2)
        num = col1.number_input("输入需要爬取的论文数量", min_value=1, max_value=200, value=50)
        start = col2.number_input("输入需要爬取的论文起始顺序", min_value=0, max_value=2000, value=0)
        url = "https://arxiv.org/search/?query=" + query + "&searchtype=all&source=header&order=-announced_date_first&size=" + str(num) + "&abstracts=show&start=" + str(start)
        # 爬取数据
        if st.button("爬取数据"):
            papers = data_utils.get_data(url)
            # 保存数据到 MySQL
            if papers:
                count = data_utils.save_to_mysql(papers)
                st.success(f"成功爬取并保存了 {count} 篇论文。")

    elif choice == "相关性分析":
        st.subheader("我的订阅")
        users = data_utils.load_users_subscriptions()
        user_paper_info = data_utils.load_data("SELECT * FROM user_paper_info")

        if user in users and users[user]:
            subscribed_papers = users[user]
            subscribed_df = pd.DataFrame(subscribed_papers)

            # Display subscribed papers in a table
            st.dataframe(subscribed_df, use_container_width=True)


            # 计算订阅论文的相关性
            st.subheader("订阅论文相关性分析")
            correlation_matrix = similarity_utils.calculate_subscription_correlation(user, users, user_paper_info)

            if correlation_matrix:
                df = pd.DataFrame(correlation_matrix)
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(df, annot=True, cmap='coolwarm', linewidths=0.5)

                # 显示热力图
                st.pyplot(fig)

                # # 简单地列出相关性大于阈值的论文对
                # st.subheader("高度相关的论文对 (Jaccard 相似度 > 0.2)")
                # threshold = 0.2
                # for paper_id_1, related_papers in correlation_matrix.items():
                #     for paper_id_2, similarity in related_papers.items():
                #         if similarity > threshold:
                #             paper_title_1 = subscribed_df[subscribed_df['id'] == paper_id_1]['标题'].iloc[0]
                #             paper_title_2 = subscribed_df[subscribed_df['id'] == paper_id_2]['标题'].iloc[0]
                #             st.write(f"**{paper_title_1}** 与 **{paper_title_2}** 相关性: {similarity:.2f}")

            else:
                st.write("未发现相关性")
        else:
            st.write("您还没有订阅任何论文。")
    # 个人资料页面
    elif choice == "个人资料":
        st.header("个人资料 :bust_in_silhouette:")

        # --- User Information ---
        st.subheader("用户信息")
        st.write(f"**用户名:** {user}")

        # --- Subscriptions ---
        st.subheader("我的订阅")
        users = data_utils.load_users_subscriptions()

        if user in users and users[user]:
            subscribed_papers = users[user]
            subscribed_df = pd.DataFrame(subscribed_papers)

            # Display subscribed papers in a table
            st.dataframe(subscribed_df, use_container_width=True)

        else:
            st.write("您还没有订阅任何论文。")

        # --- Password Change ---
        with st.expander("修改密码"):
            current_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_new_password = st.text_input("确认新密码", type="password")

            if st.button("确认修改"):
                if new_password == confirm_new_password:
                    if auth_utils.change_password(user, current_password, new_password):
                        st.success("密码修改成功！")
                    else:
                        st.error("密码修改失败，请检查当前密码是否正确。")
                else:
                    st.error("两次输入的新密码不一致。")

        # --- Other Settings ---
        with st.expander("其他设置"):
            st.write("敬请期待...")

# 程序入口
if __name__ == "__main__":
    main()
