import numpy as np
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ===============================
# ① 類似度
# ===============================
def calculate_similarity(df, project_desc):

    vectorizer = TfidfVectorizer()
    texts = df["経歴詳細テキスト"].fillna("").tolist() + [project_desc]
    tfidf = vectorizer.fit_transform(texts)

    return cosine_similarity(tfidf[-1], tfidf[:-1])[0]


# ===============================
# ② フィルタ→マストスキルで人を制限しないため今回は削除
# ===============================
#def apply_filters(df, must_skills):

    #if must_skills:
        #pattern = "|".join(must_skills)
        #df = df[df["スキル"].str.contains(pattern, na=False)]

    #return df


# ===============================
# ③ 個人スコア
# ===============================
def add_individual_scores(df, similarity_scores):

    df = df.copy()

    df["適合スコア"] = similarity_scores * 100
    df["評価寄与"] = df["評価スコア"] * 0.5
    df["稼働寄与"] = df["稼働率"] * 20
    df["耐性寄与"] = df["ストレス耐性"] * 5
    df["リーダー加点"] = df["リーダー経験フラグ"] * 10

    df["個人スコア"] = (
        df["適合スコア"]
        + df["評価寄与"]
        + df["稼働寄与"]
        + df["耐性寄与"]
        + df["リーダー加点"]
    )

    return df


# ===============================
# ④ スキルカバー
# ===============================
def skill_coverage_score(team_df, must_skills):

    # 必須スキル未指定なら評価しない
    if not must_skills:
        return 0

    team_skills = []
    for s in team_df["スキル"].dropna():
        team_skills += s.split(",")

    team_skills = set(team_skills)
    must_skills = set(must_skills)

    missing = must_skills - team_skills

    base_score = 100
    penalty = len(missing) * 30

    return base_score - penalty

# ===============================
# ⑤ スキルレベル
# ===============================
def skill_level_score(team_df, skills_df):

    score = 0

    for _, member in team_df.iterrows():
        emp_skills = skills_df[skills_df["employee_id"] == member["id"]]
        score += emp_skills["level"].sum()

    return score


# ===============================
# ⑥ 強みバランス
# ===============================
def strength_balance_score(team_df):

    strengths = []

    for s in team_df["強みタグ"].dropna():
        strengths += s.split("|")

    return len(set(strengths)) * 5


# ===============================
# ⑦ チームスコア
# ===============================
def calculate_team_score_detail(team_df, skills_df, must_skills, weight, difficulty):

    detail = {}

    # スキルカバー
    detail["スキルカバー"] = skill_coverage_score(team_df, must_skills)

    # スキルレベル
    detail["スキルレベル"] = skill_level_score(team_df, skills_df)

    # 強みバランス
    detail["強みバランス"] = strength_balance_score(team_df)

    # 若手バランス
    young_ratio = (team_df["経験年数"] <= 10).mean()
    detail["若手バランス"] = young_ratio * 20

    # リーダー
    detail["リーダー"] = 20 if team_df["リーダー経験フラグ"].sum() > 0 else 0

    # ストレス耐性
    detail["ストレス耐性"] = team_df["ストレス耐性"].mean() * difficulty * 5

    # 個人スコア
    detail["個人スコア"] = team_df["個人スコア"].mean() * weight

    # 合計
    total = sum(detail.values())

    return total, detail


# ===============================
# ⑧ チーム探索
    #ランダムでチームを500組成しスコア計算、その中から一番いいチームを記載
# ===============================
def find_best_team(df, skills_df, must_skills, team_size, weight, difficulty, trials=500):

    best_team = None
    best_score = -1

    for _ in range(trials):

        team = df.sample(team_size)

        score, detail = calculate_team_score_detail(
        team, skills_df, must_skills, weight, difficulty
        )

        if score > best_score:
            best_score = score
            best_team = team.copy()
            best_detail = detail

    # スコア付与（安全版）
    best_team = best_team.copy()
    best_team.loc[:, "チームスコア"] = best_score
    best_team.loc[:, "総合スコア"] = best_team["個人スコア"]
    best_team.attrs["score_detail"] = best_detail  # ← チームスコア内訳

    return best_team


# ===============================
# ⑨ メイン
# ===============================
def recommend(df, skills_df, project_desc, must_skills, weight, difficulty, team_size=3):


    if len(df) == 0:
        return pd.DataFrame()

    similarity_scores = calculate_similarity(df, project_desc)
    df = add_individual_scores(df, similarity_scores)

    return find_best_team(df, skills_df, must_skills, team_size, weight, difficulty)