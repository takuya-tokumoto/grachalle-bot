# prompt_chaining.py
import asyncio
import random
from datetime import datetime
from typing import Optional

from common_v2 import OpenAIService, logger
from pydantic import BaseModel, Field


# -----------------------------------------------------#
# Pydanticモデル                                       #
# -----------------------------------------------------#
class ExaminationStartIntent(BaseModel):
    """
    ユーザー入力が試験開始のリクエストであるかを判断するモデル。
    """

    description: str = Field(description="ユーザー入力の生テキスト")
    is_request_for_examination: bool = Field(description="入力テキストが試験開始のリクエストであるかどうか")


class ExaminationInformation(BaseModel):
    """
    試験の出題傾向・レベルに関する詳細情報を格納するモデル。
    """

    language: Optional[str] = Field(
        default=None, description="出題言語（解析できない場合はNone）"
    )
    level: Optional[str] = Field(default=None, description="出題難易度（解析できない場合はNone）")

class ConfirmationMessage(BaseModel):
    """
    試験情報の確認メッセージを表すモデル。
    """

    confirmation_message: str = Field(description="試験の出題言語と難易度を含む確認メッセージ")


# -----------------------------------------------------#
# 意図抽出　　　　　　　　　　　　　　　　                #
# -----------------------------------------------------#
class IntentExtract:
    def __init__(self):
        self.openai_service = OpenAIService()

    def detect_intent(self, user_input):
        """
        ステップ1: ユーザー入力が試験のリクエストであるかを検出します。
        """

        logger.info("入力が試験開始のリクエストであるかを確認中")
        system_prompt = (
            "以下のユーザーのテキストが試験開始のリクエストであるかを判断し、"
            "その結果をJSON形式で返してください。"
            "出題言語と難易度は後続のステップで抽出します。"
        )

        try:
            result = self.openai_service.call_llm_with_json_output(
                system_prompt, user_input, ExaminationStartIntent
            )
            logger.info(f"試験受験意図の検出結果: {result.is_request_for_examination}")
            return result

        except Exception as e:
            logger.error(f"意図検出に失敗しました: {str(e)}")
            return ExaminationStartIntent(description=user_input, is_request_for_examination=False)


    def extract_examination_info(self, user_input):
        """
        ステップ2: ユーザー入力から受けたい試験情報を抽出します。
        """
        logger.info("試験情報を抽出中")
        system_prompt = (
            "以下のユーザーのテキストから試験の出題言語と難易度を抽出し、"
            "その結果をJSON形式で返してください。"
            "出題言語は英語、フランス語など、出題難易度は初級、中級、上級などです。"
        )
        try:
            result = self.openai_service.call_llm_with_json_output(
                system_prompt, user_input, ExaminationInformation
            )

            logger.info(
                f"情報抽出結果: "
                f"出題言語={result.language}, 出題難易度={result.level}"
            )
            return result
        except Exception as e:
            logger.error(f"予約情報の抽出に失敗しました: {str(e)}")
            return ExaminationInformation()

    def generate_confirmation(self, language, level):
        """
        ステップ3: 試験情報をユーザーに共有するメッセージを提供します。
        """
        logger.info("試験情報の確認メッセージを生成中")
        system_prompt = (
            "以下の出題言語と難易度に基づいて、試験開始の確認メッセージを生成してください。"
            "出題言語は英語、フランス語など、出題難易度は初級、中級、上級などです。"
            "確認メッセージは、出題言語と難易度を含む文である必要があります。"
        )

        try:
            result = self.openai_service.call_llm_with_json_output(
                system_prompt,
                f"出題言語: {language}, 出題難易度: {level}",
                ConfirmationMessage
            )
            logger.info(f"確認メッセージ生成結果: {result.confirmation_message}")
            return  result
        except Exception as e:
            logger.error(f"確認メッセージの生成に失敗しました: {str(e)}")
            return ConfirmationMessage(confirmation_message="試験情報の確認に失敗しました。再度お試しください。")
    

# -----------------------------------------------------#
# ユーザーインターフェース                              #
# -----------------------------------------------------#
class GraChalleInterface:
    def __init__(self):
        self.intent_extract = IntentExtract()

    def run(self, user_input):
        """
        試験開始のための情報抽出を実施。
        """
        logger.info(f"ユーザー入力を処理しています: {user_input}")

        # ステップ1: 意図検出
        intent_result = self.intent_extract.detect_intent(user_input)

        # 試験リクエストでない場合は終了
        if not intent_result.is_request_for_examination:
            logger.info("入力は試験リクエストではありません")
            return "申し訳ありませんが、関係のない入力のため試験開始できませんでした。"

        # ステップ2: 情報抽出
        examination_info = self.intent_extract.extract_examination_info(user_input)

        # ステップ3: 不足情報の入力促進
        if examination_info.language is None:
            language_input = input("試験で出題される言語を指定してください: ")
            enhanced_input = f"{user_input} {language_input}"
            logger.info(f"言語入力: {enhanced_input}")

            examination_info = self.intent_extract.extract_examination_info(enhanced_input)
            logger.info(f"{examination_info.language} が抽出されました")

        if examination_info.level is None:
            level_input = input("出題難易度を指定してください: ")
            enhanced_input = f"{user_input} {level_input}"
            examination_info = self.intent_extract.extract_examination_info(enhanced_input)
            logger.info(f"{examination_info.level} が抽出されました")

        # ステップ4: 確認メッセージ生成
        if examination_info.language and examination_info.level:
            confirmation = self.intent_extract.generate_confirmation(
                examination_info.language,
                examination_info.level,
            )
            return confirmation.confirmation_message
        else:
            return "必要な情報が不足しているため、試験を開始できませんでした。"


# 単独実行の場合のサンプルコード
if __name__ == "__main__":
    interface = GraChalleInterface()
    user_input = input("試験のリクエストを入力してください: ")
    result = interface.run(user_input)
    print(result)
