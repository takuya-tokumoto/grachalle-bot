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


class ConversationState(BaseModel):
    conversation_history: list[dict] = Field(default_factory=list, description="会話履歴")
    current_topic: str = Field(default="", description="現在の会話トピック")
    level: str = Field(default="", description="会話の難易度")
    language: str = Field(default="", description="会話言語")
    score: int = Field(default=0, description="現在のスコア")
    mistakes: list[str] = Field(default_factory=list, description="ユーザーの間違いリスト")
    turn_count: int = Field(default=0, description="会話のターン数")
    examination_mode: bool = Field(default=True, description="試験モードかどうか")


class ConversationalText(BaseModel):
    """
    試験開始の確認メッセージを表すモデル。
    """

    message: str = Field(description="試験における会話文")


# -----------------------------------------------------#
# 試験出題　　　　　　　　　　　　　　　　                #
# -----------------------------------------------------#


class ConversationalChat:
    def __init__(self):
        self.state = ConversationState()
        self.openai_service = OpenAIService()

    async def initialize_conversation(self, language: str, level: str) -> str:
        """会話式試験を初期化し、最初の質問を生成します"""

        # 初期状態の設定 - 引数の値を使用
        self.state = ConversationState(
            language=language,
            level=level,
        )

        # 会話のコンテキスト設定と最初の質問を生成
        system_prompt = (
            f"あなたは{language}の会話試験官です。{level}レベルの{language}で会話を行います。"
            "質問は簡潔で、明確で、回答しやすいものにしてください。"
        )

        user_prompt = f"{language}で{level}レベルの会話をしましょう。"

        try:
            # JSON出力ではなく通常のテキスト出力に変更
            first_conv = await self.openai_service.call_llm_with_json_output_async(
                system_prompt, user_prompt, ConversationalText
            )
            print(f"first_conv: {first_conv}")

            # 会話履歴に追加
            self.state.conversation_history.append({"role": "assistant", "content": first_conv.message})
            self.state.turn_count += 1

            return first_conv.message

        except Exception as e:
            logger.error(f"会話初期化中にエラーが発生しました: {str(e)}")
            return f"{language}で会話を始めましょう。あなたの趣味について教えてください。"

    async def continue_conversation(self, user_input: str) -> str:
        """ユーザーの入力に基づいて会話を続け、次の会話文を生成します"""

        # 会話履歴をフォーマット
        formatted_history = "\n".join(
            [f"{item['role']}: {item['content']}" for item in self.state.conversation_history]
        )

        # ユーザーの入力を会話履歴に追加
        self.state.conversation_history.append({"role": "user", "content": user_input})

        # 次の質問を生成
        system_prompt = (
            f"あなたは{self.state.language}の会話試験官です。"
            f"ユーザーの回答に基づいて次の質問を生成してください。"
            f"{self.state.language}で{self.state.level}レベルの会話を続けてください。"
            f"直近の会話:\n{formatted_history}"
        )

        try:
            # JSON出力ではなく通常のテキスト出力に変更
            next_conv = await self.openai_service.call_llm_with_json_output_async(
                system_prompt, user_input, ConversationalText
            )

            # 会話履歴に追加
            self.state.conversation_history.append({"role": "assistant", "content": next_conv.message})
            self.state.turn_count += 1

            return next_conv.message

        except Exception as e:
            logger.error(f"会話継続中にエラーが発生しました: {str(e)}")
            return "会話を続けることができませんでした。もう一度お試しください。"

    async def end_examination(self) -> str:
        """試験を終了して最終評価を取得します"""
        # 会話終了処理を実装
        self.state.examination_mode = False

        return (
            f"【会話試験終了】\n\n"
            f"言語: {self.state.language}\n"
            f"レベル: {self.state.level}\n"
            f"会話ターン数: {self.state.turn_count}\n\n"
            f"お疲れ様でした！"
        )

    def get_conversation_history(self):
        """会話履歴を取得する"""
        return self.state.conversation_history


# -----------------------------------------------------#
# ユーザーインターフェース                              #
# -----------------------------------------------------#


# 単独実行の場合のサンプルコード
if __name__ == "__main__":

    async def main():
        examination = ConversationalChat()

        print("会話式外国語試験を開始します")
        language = "英語"
        level = "初級"

        # 試験開始
        first_conv = await examination.initialize_conversation(language, level)
        print("\n試験官: " + first_conv)

        # 会話カウンター（ユーザーの応答回数）
        conversation_turns = 0

        # 会話ループ
        while True:
            user_input = input("\nあなた: ")

            # 終了コマンド
            if user_input.lower() in ["終了", "exit", "quit", "q"]:
                break

            # ユーザーの応答回数をカウント
            conversation_turns += 1

            response = await examination.continue_conversation(user_input)
            print("\n試験官: " + response)

            # 3往復したら終了
            if conversation_turns >= 3:
                print("\n3往復の会話が完了しました。会話を終了します。")
                break

            # 試験が終了した場合
            if "【会話試験終了】" in response:
                break

        print("\n会話式外国語試験を終了します")

    asyncio.run(main())
