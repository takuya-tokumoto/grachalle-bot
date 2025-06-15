# GraChalleBot - 言語試験対話ボット

## 概要

GraChalleBot（グラチャレボット）は、ユーザーとの対話を通じて言語試験を提供するAIボットです。様々な言語に対応しており、初級・中級・上級の難易度から選択して試験を受けることができます。

## 主な機能

- 自然言語による試験リクエストの意図検出
- 複数言語対応（英語、日本語など）
- 難易度選択（初級・中級・上級）
- 会話形式での言語試験の提供
- 試験結果の評価とフィードバック

## システム構成

- **Streamlitウェブアプリ**: ユーザーインターフェース（app.py）
- **バックエンドロジック**: 試験実施エンジン（main.py）
- **言語モデル連携**: Azure OpenAIを利用した自然言語処理

## インストールと実行方法

### 前提条件

- Python 3.10以上
- Anacondaまたはpipがインストールされていること

### 環境構築

1. リポジトリをクローンします

```bash
git clone https://github.com/takuya-tokumoto/grachalle-bot.git
cd grachalle-bot
```

2. 仮想環境を作成し、依存パッケージをインストールします

```bash
# Anacondaを使用する場合
conda create -n grachalle-bot python=3.10
conda activate grachalle-bot

# 依存パッケージのインストール
pip install -r requirements.txt
```

3. 環境変数を設定します

- `.env.template`をもとにAPIキーなどを入力し`.env`として配置してください

### 実行方法

#### コマンドラインモード

```bash
python main.py
```

#### ウェブアプリモード

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセスするとウェブインターフェースが表示されます。

## 使用方法

1. 「英語の試験を受けたい」のようにリクエストを入力します
2. 言語が指定されていない場合は、どの言語の試験を受けたいか質問されます
3. 難易度（初級/中級/上級）を選択します
4. 確認後、試験が開始されます
5. 質問に回答していき、最後に結果とフィードバックが表示されます

## 開発情報

### ファイル構成

```
grachalle-bot/
├── .vscode   
├── .env   
├── app.py               # Streamlitウェブアプリ
├── common.py            # 共通用のスクリプト
├── evaluator.py         # 回答評価モジュール
├── examination.py       # 試験問題生成モジュール
├── intent.py            # 意図抽出モジュール
├── main.py              # メインロジック
├── README.md            # 本ドキュメント
└── requirements.txt     # 依存パッケージ
```
