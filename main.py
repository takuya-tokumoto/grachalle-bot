# main.py
import asyncio
import logging

from intent import IntentExtract
from examination import ConversationalChat
from evaluator import ConversationEvaluator

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

    def _intent_extract(self, user_input):
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
            # 抽出された言語とレベルを返す
            return confirmation.confirmation_message, examination_info.language, examination_info.level
        else:
            return "必要な情報が不足しているため、試験を開始できませんでした。", None, None
        
    async def _examination(self, language, level):    
        logger.info("会話式外国語試験を開始します")
        
        # 試験開始
        first_conv = await self.examination.initialize_conversation(language, level)
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
            
            response = await self.examination.continue_conversation(user_input)
            print("\n試験官: " + response)
            
            # 3往復したら終了
            if conversation_turns >= 3:
                print("\n3往復の会話が完了しました。会話を終了します。")
                break
            
            # 試験が終了した場合
            if "【会話試験終了】" in response:
                break
        
        logger.info("\n会話式外国語試験を終了します")
        
        # 会話履歴を返す（評価のため）
        return self.examination.get_conversation_history()

    async def _evaluator(self, conversation_full):
        evaluator = ConversationEvaluator()
        evaluator.set_conversation_history(conversation_full)
        logger.info("\n会話の評価を開始します")
        language = "日本語"
        level = "初級"

        score = await evaluator.examination_score(language, level)
        feedback = await evaluator.examination_feedback(language, level)
        result = await evaluator.result_report(score, feedback)

        return result
    
    async def run_async(self, user_input):
        """
        ユーザー入力を元に試験を実行する非同期メソッド
        """
        # 意図検出と情報抽出
        confirmation, language, level = self._intent_extract(user_input)
        print(confirmation)
        
        if language is None or level is None:
            return "試験に必要な情報が揃いませんでした。"
        
        # 試験実行
        conversation_history = await self._examination(language, level)
        
        # 評価
        result = await self._evaluator(conversation_history)
        
        return result

    def run(self, user_input):
        """
        同期版インターフェース（非同期関数をラップ）
        """
        return asyncio.run(self.run_async(user_input))

# 単独実行の場合のサンプルコード
if __name__ == "__main__":
    # ログの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    interface = GraChalleInterface()
    user_input = input("試験のリクエストを入力してください: ")
    result = interface.run(user_input)
    print("\n===== 評価結果 =====")
    print(result)
