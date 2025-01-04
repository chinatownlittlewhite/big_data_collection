from sklearn.feature_extraction.text import TfidfVectorizer
def calculate_jaccard_similarity(set1, set2):
    """计算 Jaccard 相似度."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0
    return intersection / union


def calculate_subscription_correlation(user, users, user_paper_info):
    """计算用户订阅论文之间的相关性."""
    if user not in users or not users[user]:
        return None

    subscribed_papers = users[user]
    paper_ids = [paper['id'] for paper in subscribed_papers]

    # 获取订阅论文的标题和摘要，用于提取关键词
    subscribed_df = user_paper_info[user_paper_info['paper_id'].isin(paper_ids)]
    subscribed_df['combined_text'] = subscribed_df['标题'] + " " + subscribed_df['摘要']

    # 使用 TF-IDF 提取关键词
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
    tfidf_matrix = tfidf_vectorizer.fit_transform(subscribed_df['combined_text'])

    # 提取每篇论文的关键词集合
    feature_names = tfidf_vectorizer.get_feature_names_out()
    paper_keywords = []
    for i in range(tfidf_matrix.shape[0]):
        feature_index = tfidf_matrix[i, :].nonzero()[1]
        tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
        keywords = {feature_names[i]: s for (i, s) in tfidf_scores}
        # 基于 TF-IDF 权重排序并取前 N 个关键词
        top_keywords = set(sorted(keywords, key=keywords.get, reverse=True)[:10])
        paper_keywords.append(top_keywords)

    correlations = {}
    for i in range(len(paper_ids)):
        for j in range(i + 1, len(paper_ids)):
            paper_id_1 = paper_ids[i]
            paper_id_2 = paper_ids[j]
            similarity = calculate_jaccard_similarity(paper_keywords[i], paper_keywords[j])

            if paper_id_1 not in correlations:
                correlations[paper_id_1] = {}
            if paper_id_2 not in correlations:
                correlations[paper_id_2] = {}
            correlations[paper_id_1][paper_id_2] = similarity
            correlations[paper_id_2][paper_id_1] = similarity

    return correlations