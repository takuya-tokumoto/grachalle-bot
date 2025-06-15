# prompt_chaining.py
import asyncio
import random
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from common import OpenAIService, logger

# -----------------------------------------------------#
# Pydanticモデル - Parallelizationパターン用           #
# -----------------------------------------------------#


class EvaluationScore(BaseModel):
    """評価結果を格納するモデル"""

    score: int = Field(description="会話の評価スコア (0-100)")


class EvaluationFeedback(BaseModel):
    """評価フィードバックを格納するモデル"""

    feedback: str = Field(description="会話に対する具体的なフィードバック")


class EvaluationResult(BaseModel):
    """会話の評価結果を格納するモデル"""

    result: str = Field(default="評価データを生成できませんでした。", description="会話に対する具体的なフィードバック")


# -----------------------------------------------------#
# 評価結果　　　　　　　　　　　　　　　　                #
# -----------------------------------------------------#


class ConversationEvaluator:
    """会話の評価を行うための専用クラス"""

    def __init__(self):
        self.openai_service = OpenAIService()
        self.conversation_full = ""

    def set_conversation_history(self, conversation_history: list):
        """
        会話履歴を設定します
        """
        self.conversation_full = "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history])

    async def examination_score(self, language: str, level: str) -> EvaluationResult:
        """
        会話履歴を評価し、スコアとフィードバックを生成します
        """
        # システムプロンプト
        system_prompt = (
            f"{language}の会話能力を評価してください。"
            f"評価対象は{level}レベルの学習者です。"
            "以下の観点からuserの入力文について1-10点で評価し、具体的なフィードバックを提供してください：\n"
            "- 適切な表現の使用\n"
            "- 文法的な正確さ\n"
            "- 応答の適切さと流暢さ\n"
            "- 語彙の豊富さと適切な使用\n"
            "回答はJSON形式で、スコア(score)とフィードバック(feedback)を含めてください。"
        )

        try:

            # JSONで評価結果を取得
            result = await self.openai_service.call_llm_with_json_output_async(
                system_prompt, self.conversation_full, EvaluationScore
            )

            return result

        except Exception as e:
            logger.error(f"会話評価中にエラーが発生しました: {str(e)}")
            return "評価処理中にエラーが発生しました。一般的なフィードバック：会話の継続性を保ち、質問に直接回答するよう心がけてください。"

    async def examination_feedback(self, language: str, level: str) -> str:
        """
        ユーザーの回答に対するフィードバックコメントを生成します
        """

        # システムプロンプト
        system_prompt = (
            f"{language}の会話におけるユーザーの回答に対するフィードバックを生成してください。"
            f"レベルは{level}です。以下の点について具体的にコメントしてください：\n"
            "1. 語彙の使用\n"
            "2. 文法\n"
            "3. 発話の一貫性\n"
            "4. コミュニケーション能力\n"
            "5. 強みと改善点\n"
            "フィードバックは日本語で、具体的な例を挙げてください。"
        )

        try:
            # フィードバックを取得
            result = await self.openai_service.call_llm_with_json_output_async(
                system_prompt, self.conversation_full, EvaluationFeedback
            )

            return result

        except Exception as e:
            logger.error(f"フィードバック生成中にエラーが発生しました: {str(e)}")
            return "フィードバックを生成できませんでした。会話の内容を見直してください。"

    async def result_report(self, score, feedback) -> str:
        """
        スコアとフィードバック内容を統合し詳細な評価レポートを生成します
        """

        system_prompt = (
            "以下の評価情報を確認してレポートとしてユーザーに返答してください。"
            "レポートには、スコア、フィードバック、強みと改善点を含めてください。"
            "出力は日本語で、具体的な例を挙げてください。"
            "■評価情報\n"
            f"スコア(100点満点): {score}\n"
            f"フィードバック: {feedback}\n"
        )

        user_content = f"公平公正な評価結果を提供してください。"

        try:
            # 詳細分析を取得
            result = await self.openai_service.call_llm_with_json_output_async(
                system_prompt, user_content, EvaluationResult
            )

            return result.result

        except Exception as e:
            logger.error(f"詳細レポート生成中にエラーが発生しました: {str(e)}")
            return "詳細な言語分析を生成できませんでした。"


if __name__ == "__main__":
    # 非同期関数を定義
    async def main():
        conversation_full = [
            {"role": "user", "content": "こんにちは、今日はどんな天気ですか？"},
            {"role": "assistant", "content": "こんにちは！今日は晴れています。あなたはどうですか？"},
            {"role": "user", "content": "私は元気です。最近何か面白いことありましたか？"},
            {"role": "assistant", "content": "最近、友達と映画を見に行きました。とても楽しかったです。"},
        ]

        # 評価の実行
        evaluator = ConversationEvaluator()
        evaluator.set_conversation_history(conversation_full)
        print("\n会話の評価を開始します")
        language = "日本語"
        level = "初級"

        score = await evaluator.examination_score(language, level)
        feedback = await evaluator.examination_feedback(language, level)
        result = await evaluator.result_report(score, feedback)

        print(score)
        print(feedback)
        print(f"{result}")

    # 非同期関数を実行するためのイベントループを使用
    import asyncio

    asyncio.run(main())
