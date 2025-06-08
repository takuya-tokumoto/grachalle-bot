import os
from pydantic import BaseModel, Field
from openai import AsyncAzureOpenAI, AzureOpenAI
from typing import Optional  # この行を追加

from dotenv import load_dotenv
load_dotenv()  # .envファイルを読み込む
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")  # デフォルトモデルの設定
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")  # APIバージョンのデフォルト値

# client = AzureOpenAI(azure_endpoint=ENDPOINT, api_key=API_KEY, api_version=API_VERSION)
client = AsyncAzureOpenAI(azure_endpoint=ENDPOINT, api_key=API_KEY, api_version=API_VERSION)

class ExaminationInformation(BaseModel):
    """
    試験の出題傾向・レベルに関する詳細情報を格納するモデル。
    """

    language: Optional[str] = Field(
        default=None, description="出題言語（解析できない場合はNone）"
    )
    level: Optional[str] = Field(default=None, description="出題難易度（解析できない場合はNone）")

print(type(ExaminationInformation))

# completion = client.beta.chat.completions.parse(
#     model="MODEL_DEPLOYMENT_NAME", # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
#     messages=[
#         {"role": "system", "content": "試験の言語とレベルを抽出するためのシステムメッセージです。"},
#         {"role": "user", "content": "英語の会話試験を受けたいです。レベルは中級でお願いします。"},
#     ],
#     response_format=ExaminationInformation,
# )
completion = await client.beta.chat.completions.parse(
    model="MODEL_DEPLOYMENT_NAME", # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
    messages=[
        {"role": "system", "content": "試験の言語とレベルを抽出するためのシステムメッセージです。"},
        {"role": "user", "content": "英語の会話試験を受けたいです。レベルは中級でお願いします。"},
    ],
    response_format=ExaminationInformation,
)


event = completion.choices[0].message.parsed
# import json

# 一度JSONに変換してから検証
# json_str = json.dumps(completion.model_dump())
# event = ConversationalText.model_validate_json(json_str)
# event = ConversationalText.model_validate_json(completion)

print(event)
print(type(event))
print(event.language)
print(event.level)
print(completion.model_dump_json(indent=2))