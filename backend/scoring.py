import numpy as np

def add_scores(df, similarity_scores, weight):
    df['適合スコア'] = similarity_scores * 100

    # 多様性（仮）
    diversity_bonus = np.random.rand(len(df)) * 10

    df['総合スコア'] = df['適合スコア'] * weight + diversity_bonus

    return df