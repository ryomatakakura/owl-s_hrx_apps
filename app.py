import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from backend.recommend import recommend
from backend.gpt import generate_mbti_team_advice, generate_comment

# ===============================
# ① ページ設定
# ===============================
st.set_page_config(page_title="HRX - チーム編成ツール", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# ② データ読み込み（DBから）
# ===============================
@st.cache_data
def load_data():
    employees = pd.read_csv("data/employees.csv")
    skills = pd.read_csv("data/employee_skills.csv")

    # --- スキルをまとめる（表示用） ---
    skills_grouped = skills.groupby("employee_id")["skill_name"].apply(lambda x: ",".join(x)).reset_index()

    # --- employeesと結合 ---
    df = employees.merge(skills_grouped, left_on="id", right_on="employee_id", how="left")

    df.rename(columns={"skill_name": "スキル"}, inplace=True)

    return df, skills  # ←ここ重要！！

# 呼び出し側
df, skills_df = load_data()

#スキルバランス計算
def calculate_skill_balance(team_df):
    categories = ["技術", "営業", "戦略", "デザイン", "管理"]
    scores = {c: 0 for c in categories}

    for skills in team_df["スキル"].dropna():
        for s in skills.split(","):
            s = s.strip().lower()

            if any(k in s for k in ["python", "aws", "sql", "java"]):
                scores["技術"] += 1
            elif any(k in s for k in ["営業", "交渉", "新規"]):
                scores["営業"] += 1
            elif any(k in s for k in ["戦略", "分析", "リサーチ"]):
                scores["戦略"] += 1
            elif any(k in s for k in ["デザイン", "sns", "ui"]):
                scores["デザイン"] += 1
            elif any(k in s for k in ["マネジメント", "採用", "労務"]):
                scores["管理"] += 1

    return [scores[c] for c in categories]

# ===============================
# ③ サイドバー（入力）
# ===============================
with st.sidebar:
    st.header("プロジェクト要件入力")

    project_desc = st.text_area(
        "プロジェクト概要",
        "AIを活用した新規SaaSの立ち上げ"
    )

    # スキル一覧をDBから生成
    all_skills = set()
    for s in df["スキル"].dropna():
        all_skills.update(s.split(","))

    must_skills = st.multiselect(
        "スキル要件",
        sorted(list(all_skills))
    )

    weight = st.slider(
        "スキル重視 ← → 多様性重視",
        0.0, 5.0, 2.5
    )

    team_size = st.slider("チーム人数", 2, 15, 5)

    difficulty = st.slider("プロジェクト難易度（ハードさ）",1, 5, 3)

    search_btn = st.button("チームをレコメンド", type="primary")

# ===============================
# ④ メイン処理
# ===============================
if search_btn:

    # ---- レコメンド実行 ----
    result_df = recommend(
    df,
    skills_df,
    project_desc,
    must_skills,
    weight,
    difficulty,
    team_size=team_size
    )

   # ---- チームスコア表示 ----
    if not result_df.empty:
        st.header("🏆 おすすめチーム")
        st.subheader(f"チームスコア：{round(result_df['チームスコア'].iloc[0],1)}")
   
    # ---- メンバー表示 ----
    for i, row in result_df.iterrows():
        with st.expander(
            f"【個人スコア {round(row['総合スコア'],1)}】 {row['名前']}（{row['所属']}）",
            expanded=(i == 0)
        ):
            col1, col2, col3 = st.columns([1, 2, 2])

        # スコア表示
            col1.metric("個人スコア", round(row["総合スコア"], 1))

        # 基本情報
            col2.write(f"**経験年数:** {row['経験年数']}")
            col2.write(f"**スキル:** {row['スキル']}")
            col2.write(f"**強み:** {row['強みタグ']}")
            col2.write(f"**MBTI:** {row['MBTI']}")

        # AIコメント（そのまま活かす）
        with col3:
            st.write("**🤖 AI選定理由**")
            # 少しロードに時間がかかるため、くるくる（spinner）を表示
            with st.spinner("選定理由を生成中..."):
            # gpt.py の generate_comment に row と project_desc を渡す
                comment = generate_comment(row, project_desc)
                st.caption(comment)

    #チームスコア内訳表示
    #st.subheader("📊 チームスコア内訳(棒グラフ) ")

    #detail = result_df.attrs.get("score_detail", {})

    #total = sum(detail.values())

    #normalized = {k: v / total * 100 for k, v in detail.items()}

    #detail_df = pd.DataFrame(
    #    list(normalized.items()),
    #    columns=["要素", "割合(%)"]
    #)

    #st.bar_chart(detail_df.set_index("要素"))

    st.subheader("📊 チームスコア内訳")

    detail = result_df.attrs.get("score_detail", {})

    # 合計
    total = sum(detail.values())

    # 割合に変換
    labels = []
    values = []

    for k, v in detail.items():
        if v > 0:  # マイナスは除外（見やすくする）
            labels.append(k)
            values.append(v / total * 100)

    # 円グラフ（Plotly）
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3  # ドーナツ型にすると見やすい
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)
    # ===============================
    # ⑤ チーム分析
    # ===============================
    #st.divider()
    #st.header("チーム分析")

    col_g1, col_g2 = st.columns(2)

    # --- レーダーチャート（簡易） ---
    #with col_g1:
    #    st.subheader("スキルバランス")

    #    categories = ["技術", "営業", "戦略", "デザイン", "管理"]
    #    team_scores = calculate_skill_balance(result_df)

        # 正規化
    #    max_score = max(team_scores) if max(team_scores) > 0 else 1
    #    team_scores = [s / max_score * 100 for s in team_scores]

        # グラフを閉じる
    #    team_scores += [team_scores[0]]
    #    categories += [categories[0]]

        # グラフ描画
    #    fig = go.Figure()
    #    fig.add_trace(go.Scatterpolar(
    #        r=team_scores,
    #        theta=categories,
    #        fill='toself',
    #        name='チーム構成'
    #    ))
    #    # 軸固定
    #    fig.update_layout(
    #        polar=dict(
    #            radialaxis=dict(
    #                visible=True,
    #                range=[0, 100]  # ←これが軸固定
     #           )
      #      ),
       #     showlegend=False
        #)

     #   st.plotly_chart(fig, use_container_width=True)

    # --- MBTI分布 ---
    #with col_g2:
    #    st.subheader("MBTI分布")
    #    st.bar_chart(result_df['MBTI'].value_counts())

    # ===============================
    # チーム分析 ＆ 全体AIアドバイス
    # ===============================
    st.divider()
    st.header("チーム分析")

    # ここでチーム全体に対するMBTIアドバイスを生成・表示
    with st.spinner("MBTIに基づくチームの相性を分析中..."):
        # PandasのDataFrameを、関数で扱いやすい辞書のリストに変換
        team_members_dict = result_df.to_dict('records')
        
        # GPTにプロジェクト概要とメンバー情報を渡してアドバイスを取得
        team_advice = generate_mbti_team_advice(project_desc, team_members_dict)
        
        # 取得したアドバイスを目立たせる形で表示
        st.subheader("🤖 AIによるチーム編成アドバイス（MBTI特性）")
        st.info(team_advice)

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)


    # ===============================
    # ⑥ フィードバック
    # ===============================
    st.divider()
    st.subheader("フィードバック")

    col1, col2 = st.columns([1, 2])

    col1.selectbox("評価", ["5", "4", "3", "2", "1"])
    col2.text_area("コメント")

    st.button("送信")

# ===============================
# 初期画面
# ===============================
else:
    st.info("左の条件を入力してレコメンドを実行してください")