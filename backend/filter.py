def apply_filters(df, must_skills, departments=None):
    if must_skills:
        df = df[df['スキル'].str.contains('|'.join(must_skills))]

    if departments:
        df = df[df['所属'].isin(departments)]

    return df