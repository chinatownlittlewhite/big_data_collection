# ArXiv 论文智能管理平台

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff69b4.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**一个为你量身打造的、由AI驱动的ArXiv科研助手。**

本项目是一个基于 Streamlit 构建的交互式Web应用，旨在彻底改变您发现、管理和理解 ArXiv 学术论文的方式。平台深度集成了 Google Gemini 模型，让您能与论文直接“对话”，并提供强大的数据分析工具，助您轻松洞察研究趋势，高效管理您的学术资料库。

## ✨ 核心功能

### 论文发现与管理
- **🔍 智能搜索与爬取**: 通过关键词实时搜索 ArXiv 论文，并可按需爬取指定数量的新论文，自动存入您的个人数据库。
- **⭐ 个性化订阅**: 一键订阅您感兴趣的论文，构建专属的学术阅读列表，方便随时回顾。
- **📖 清晰的分页浏览**: 友好的分页功能，让您在海量论文中轻松导航。

### 数据洞察与分析
- **🔗 智能关联分析**: 自动计算您订阅论文之间的文本相似度，通过交互式热力图直观展示论文间的内在联系。
- **🎯 高相关性配对**: 精准列出最相关的论文组合，助您发现潜在的研究方向和跨领域知识。

### AI 赋能的交互体验
- **🤖 与论文对话 (Q&A)**: 选择任意一篇论文，与集成的 Gemini AI 模型进行深入问答。无论是总结核心观点、解释复杂术语，还是探讨实验细节，AI 都能为您解答。
- **💬 对话历史记录**: 自动保存您与 AI 的每一次对话，方便您随时查阅和梳理思路。

### 个人中心
- **👤 用户仪表盘**: 集中管理您的个人信息和已订阅的论文列表。
- **🔒 安全设置**: 提供便捷的密码修改功能，保障账户安全。

## 🛠️ 技术栈

- **Web框架**: Streamlit
- **核心语言**: Python
- **AI模型**: Google Generative AI (Gemini)
- **数据处理**: Pandas, SQLAlchemy
- **数据库**: MySQL (通过 PyMySQL 连接)
- **数据可视化**: Plotly, Seaborn, Matplotlib
- **前端组件**: streamlit-tags

## 🚀 部署与运行指南

请遵循以下步骤在您的本地环境中设置并启动项目。

### 1. 克隆代码仓库

```bash
git clone https://github.com/your-username/arxiv-management-platform.git
cd arxiv-management-platform
```

### 2. 创建并激活虚拟环境 (推荐)

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt
```

### 4. 数据库设置 (MySQL)

1.  确保您已安装并运行 MySQL 数据库服务。
2.  登录您的 MySQL，创建一个新的数据库。
    ```sql
    CREATE DATABASE arxiv_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ```
3.  执行项目中的 `create.sql` 脚本，以在该数据库中创建所需的数据表。
    ```bash
    # 使用您的用户名和刚刚创建的数据库名替换 'your_user' 和 'arxiv_db'
    mysql -u your_user -p arxiv_db < create.sql
    ```

### 5. 配置敏感信息 (重要！)

为了安全起见，**请勿将数据库密码和 API 密钥直接写入代码**。我们使用 Streamlit 的 secrets 管理功能。

1.  在项目根目录下创建一个名为 `.streamlit` 的文件夹。
2.  在该文件夹内创建一个名为 `secrets.toml` 的文件。
3.  将您的数据库连接信息和 Gemini API 密钥按以下格式填入该文件：

    ```toml
    # .streamlit/secrets.toml

    # 数据库连接信息
    [database]
    db_type = "mysql+pymysql"
    username = "YOUR_DB_USERNAME"
    password = "YOUR_DB_PASSWORD"
    host = "localhost"
    port = 3306
    db_name = "arxiv_db"

    # Google Gemini API 密钥
    [api_keys]
    gemini_api_key = "YOUR_GEMINI_API_KEY"
    ```

4.  **请确保您的代码已适配为从 `st.secrets` 读取信息**。例如，在 `app.py` 和 `utils/data_utils.py` 中，使用以下方式获取密钥和数据库配置：
    ```python
    # 获取 Gemini API Key
    api_key = st.secrets["api_keys"]["gemini_api_key"]
    genai.configure(api_key=api_key)

    # 获取数据库连接字符串
    db_config = st.secrets["database"]
    connection_string = f"{db_config['db_type']}://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    engine = create_engine(connection_string)
    ```

### 6. 运行应用

所有配置完成后，启动 Streamlit 应用：

```bash
streamlit run app.py
```

应用将在您的浏览器中自动打开！

## 📂 项目结构

```
arxiv-management-platform/
├── .streamlit/
│   └── secrets.toml        # (需手动创建) 存放数据库密码和API密钥
├── utils/
│   ├── auth_utils.py       # 用户认证与密码管理
│   ├── data_utils.py       # 数据加载、处理、爬取
│   └── similarity_utils.py # 计算论文相似度
├── app.py                  # Streamlit 应用主程序
├── create.sql              # 数据库表结构创建脚本
└── requirements.txt        # Python 依赖包列表
```

## 💡 未来路线图 (Roadmap)

- [ ] **更智能的推荐系统**: 基于用户的订阅和阅读行为，主动推荐可能感兴趣的论文。
- [ ] **增强的统计分析**: 增加对作者、机构、关键词趋势的深度分析。
- [ ] **全文支持**: 支持下载论文 PDF 全文，并能对全文内容进行 AI 问答。
- [ ] **精细化分类**: 引入更细粒度的论文分类标签（如使用模型进行自动打标）。
- [ ] **用户体验优化**: 增加加载动画、优化错误提示、提升界面响应速度。

## 🤝 贡献

欢迎对本项目提出宝贵的改进意见或贡献代码！您可以：
-   提交一个 [Issue](https://github.com/your-username/arxiv-management-platform/issues) 来报告 Bug 或提出功能建议。
-   创建一个 [Pull Request](https://github.com/your-username/arxiv-management-platform/pulls) 来贡献您的代码。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 授权。
