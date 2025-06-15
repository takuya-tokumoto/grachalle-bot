# main.py
import asyncio
import logging

from evaluator import ConversationEvaluator
from examination import ConversationalChat
from intent import IntentExtract

# ロガーの参照
logger = logging.getLogger(__name__)


# -----------------------------------------------------#
# メインアプリケーションエントリーポイント               #
# -----------------------------------------------------#
class GraChalleInterface:
    def __init__(self):
        self.intent_extract = IntentExtract()
        self.examination = ConversationalChat()
        self.evaluator = ConversationEvaluator()

        self.IS_REQUEST_EXAMINATION = False
        self.LANGAGE = None
        self.LEVEL = None

        self.exam_status = "hearing"  # "hearing", "before", "started", "finished"
        self.conversation_turns = 0
        self.MAX_TURNS = 3  # 最大会話ターン数

    async def _evaluator(self, conversation_full):
        evaluator = ConversationEvaluator()
        evaluator.set_conversation_history(conversation_full)
        logger.info("\n会話の評価を開始します")
        score = await evaluator.examination_score(self.LANGAGE, self.LEVEL)
        feedback = await evaluator.examination_feedback(self.LANGAGE, self.LEVEL)
        result = await evaluator.result_report(score, feedback)
        return result

    async def run_async(self, user_input):
        logger.info("会話式外国語試験を開始します")
        if self.exam_status == "hearing":
            # ステップ1: 意図検出
            if not self.IS_REQUEST_EXAMINATION:
                content = self.intent_extract.detect_intent(user_input)
                self.IS_REQUEST_EXAMINATION = content.is_request_for_examination
            # 試験リクエストでない場合は終了
            if not self.IS_REQUEST_EXAMINATION:
                logger.info("入力は試験リクエストではありません")
                return "申し訳ありませんが、関係のない入力のため終了します。"
            # ステップ2: 情報抽出
            if self.LANGAGE is None or self.LEVEL is None:
                examination_info = self.intent_extract.extract_examination_info(user_input)
                if self.LANGAGE is None:
                    logger.info(f"抽出された言語: {examination_info.language}")
                    self.LANGAGE = examination_info.language
                if self.LEVEL is None:
                    logger.info(f"抽出されたレベル: {examination_info.level}")
                    self.LEVEL = examination_info.level
            # ステップ3: 不足情報の入力促進
            if self.LANGAGE is None:
                return "試験で出題される言語を指定してください。"
            if self.LEVEL is None:
                return "出題難易度を指定してください。"
            confirmation = self.intent_extract.generate_confirmation(
                self.LANGAGE,
                self.LEVEL,
            )
            self.exam_status = "before"
            return confirmation.confirmation_message
        if self.exam_status == "before":
            # 試験開始
            first_conv = await self.examination.initialize_conversation(self.LANGAGE, self.LEVEL)
            self.exam_status = "started"
            return first_conv
        if self.conversation_turns >= self.MAX_TURNS:
            # 試験を終了して評価を実行
            conversation_history = self.examination.get_conversation_history()
            response = await self._evaluator(conversation_history)
            return response
        response = await self.examination.continue_conversation(user_input)
        self.conversation_turns += 1
        return response

    def run(self, user_input):
        """
        同期版インターフェース（非同期関数をラップ）
        """
        return asyncio.run(self.run_async(user_input))


# 単独実行の場合のサンプルコード
if __name__ == "__main__":
    # ログの設定
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    interface = GraChalleInterface()
    user_input = input("試験のリクエストを入力してください: ")
    result = interface.run(user_input)
    print("\n===== 評価結果 =====")
    print(result)
