# gpt.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# 絶対パスで読む（最強）
base_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(base_dir, ".env")

load_dotenv(env_path)

print("API KEY:", os.getenv("OPENAI_API_KEY"))  # デバッグ

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_comment(row, project_desc):
    """
    個人ごとの選定理由を200文字程度で生成する関数
    """
    # エラーを防ぐため、データがない場合は '不明' とする
    name = row.get('名前', '不明')
    skills = row.get('スキル', '不明')
    strengths = row.get('強みタグ', '不明')
    mbti = row.get('MBTI', '不明')
    experience = row.get('経験年数', '不明')
    
    system_prompt = """
    あなたはプロのHRコンサルタントです。
    提供されたプロジェクト概要と候補者のスキル・特性を踏まえ、
    「なぜこの人物をこのプロジェクトに選出したのか（どのように貢献できるか）」という推薦理由を、
    200文字程度の自然な日本語で簡潔に説明してください。
    """
    
    user_prompt = f"""
    【プロジェクト概要】
    {project_desc}
    
    【候補者情報】
    名前: {name}
    経験年数: {experience}年
    スキル: {skills}
    強み: {strengths}
    MBTI: {mbti}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"選定理由の取得に失敗しました: {e}"

# -------------------------------------------------------------------
# ↓ ここから下の「関数の定義（def ...）」が抜けていたため修正しました！
# -------------------------------------------------------------------
def generate_mbti_team_advice(pj_outline, recommended_members):
    member_info_str = ""
    for member in recommended_members:
        name = member.get('名前', '不明')
        mbti = member.get('MBTI', '不明')
        skills = member.get('スキル', '不明')
        # ★追加：AIに渡すために総合スコアも取得する（小数点第1位に丸める）
        score = round(member.get('総合スコア', 0), 1)
        
        # ★追加：文字列にスコアの情報を組み込む
        member_info_str += f"- {name} (スコア: {score}, MBTI: {mbti}, スキル: {skills})\n"

    system_prompt = """
    あなたは組織心理学とMBTI（16タイプ診断）に精通したHRコンサルタントです。
    提供されたプロジェクト要件と選出されたメンバーのMBTI特性や総合スコアを元に、以下の3点を軸にアドバイスを要約して500文字程度で出力してください。
    個人名も記載することでチーム形成のイメージが沸くように。
    
    1. 【チームの強み】: このMBTIの組み合わせが生み出すシナジー
    2. 【注意点】: 意思決定やコミュニケーションにおける潜在的な摩擦（E/I, S/N, T/F, J/Pの違いなどを考慮）
    3. 【進め方のアドバイス】: プロジェクトを成功に導くための具体的な役割分担や声かけ
    """

    user_prompt = f"""
    【プロジェクト概要】
    {pj_outline}

    【選出メンバー】
    {member_info_str}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AIアドバイスの取得に失敗しました: {e}"