import asyncio
import json
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

# 環境変数を.envファイルから読み込む
load_dotenv()

# -----------------------------------------------------#
# ロガー設定                                           #
# -----------------------------------------------------#
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------#
# Azure OpenAI設定                                     #
# -----------------------------------------------------#
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")  # デフォルトモデルの設定
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")  # APIバージョンのデフォルト値


# -----------------------------------------------------#
# OpenAI サービス                                      #
# -----------------------------------------------------#
class OpenAIService:
    """
    Azure OpenAI APIを利用するためのサービスクラス。
    同期・非同期両方のAPI呼び出しに対応しています。
    """

    def __init__(self, endpoint=ENDPOINT, api_key=API_KEY, model_name=MODEL_NAME, api_version=API_VERSION):
        """
        OpenAIServiceの初期化。

        Parameters:
            endpoint (str): Azure OpenAIのエンドポイント
            api_key (str): Azure OpenAIのAPIキー
            model_name (str): 使用するモデル名
            api_version (str): APIバージョン
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.model_name = model_name
        self.client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
        # 非同期クライアントは必要時に初期化する
        self._async_client = None

    def _get_async_client(self):
        """
        非同期APIクライアントを取得（遅延初期化）
        """
        if self._async_client is None:
            self._async_client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint, api_key=self.api_key, api_version=self.api_version
            )
        return self._async_client

    def call_llm_with_json_output(self, system_prompt, user_input, output_schema, temperature=0):
        """
        構造化JSONレスポンスを得るためのLLM呼び出しを行います。

        Parameters:
            system_prompt (str): システムプロンプト
            user_input (str): ユーザー入力
            output_schema (pydantic.BaseModel): Pydanticモデルクラス
            temperature (float): 生成の多様性（0～1）

        Returns:
            object: 指定されたPydanticモデルのインスタンス
        """
        try:
            response = self.client.beta.chat.completions.parse(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                model=self.model_name,
                temperature=temperature,
                response_format=output_schema,
            )

            # JSONレスポンスを取得
            json_content = response.choices[0].message.parsed
            logger.debug(f"LLM応答: {json_content}")

            return json_content

        except Exception as e:
            logger.error(f"LLM API呼び出しに失敗: {str(e)}")
            # 空のJSONオブジェクトを返す
            return "{}"

    def _create_example_from_schema(self, json_schema):
        """スキーマから具体的な例を生成する"""
        example = {}
        if "properties" in json_schema:
            for prop, details in json_schema["properties"].items():
                if details.get("type") == "string":
                    example[prop] = f"サンプル{prop}"
                elif details.get("type") == "number" or details.get("type") == "integer":
                    example[prop] = 42
                elif details.get("type") == "boolean":
                    example[prop] = True
                elif details.get("type") == "array":
                    example[prop] = ["サンプル項目1", "サンプル項目2"]
                elif details.get("type") == "object":
                    example[prop] = {"key": "value"}
        return example

    async def call_llm_with_json_output_async(self, system_prompt, user_input, output_schema, temperature=0):
        """
        構造化JSONレスポンスを得るためのLLM呼び出しを非同期で行います。

        Parameters:
            system_prompt (str): システムプロンプト
            user_input (str): ユーザー入力
            output_schema (pydantic.BaseModel): Pydanticモデルクラス
            temperature (float): 生成の多様性（0～1）

        Returns:
            object: 指定されたPydanticモデルのインスタンス
        """
        try:
            async_client = self._get_async_client()

            response = await async_client.beta.chat.completions.parse(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                model=self.model_name,
                temperature=temperature,
                response_format=output_schema,
            )

            # JSONレスポンスを取得
            json_content = response.choices[0].message.parsed
            logger.debug(f"LLM応答(非同期): {json_content}")

            return json_content

        except Exception as e:
            logger.error(f"非同期LLM API呼び出しに失敗: {str(e)}")
            # 空のJSONオブジェクトを返す
            return "{}"

    def _create_default_response(self, json_schema):
        """
        JSONスキーマに基づいたデフォルトのレスポンスを生成します。

        Parameters:
            json_schema (dict): JSONスキーマ

        Returns:
            dict: デフォルトのレスポンスオブジェクト
        """
        default_response = {}
        if "properties" in json_schema:
            for prop, details in json_schema["properties"].items():
                if "default" in details:
                    default_response[prop] = details["default"]
                elif details.get("type") == "boolean":
                    default_response[prop] = False
                elif details.get("type") == "string":
                    default_response[prop] = ""
                elif details.get("type") == "number" or details.get("type") == "integer":
                    default_response[prop] = 0
                elif details.get("type") == "array":
                    default_response[prop] = []
                elif details.get("type") == "object":
                    default_response[prop] = {}
        return default_response
