from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(df, project_desc):
    vectorizer = TfidfVectorizer()

    texts = df['経歴詳細'].tolist() + [project_desc]
    tfidf = vectorizer.fit_transform(texts)

    scores = cosine_similarity(tfidf[-1], tfidf[:-1])[0]

    return scores