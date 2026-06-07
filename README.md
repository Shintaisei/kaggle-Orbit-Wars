# Kaggle Orbit Wars

Kaggle [Orbit Wars](https://www.kaggle.com/competitions/orbit-wars/overview) コンペ用の研究ワークスペース兼提出コード置き場です。

主な Kaggle 提出ファイルは `main.py` です。単一ファイルのヒューリスティックエージェントを中心に、候補版、ローカル評価スクリプト、調整メモをまとめています。

## リポジトリ構成

```text
.
|-- main.py                         # 現在の単一ファイル提出エージェント
|-- test_local.py                   # kaggle-environments を使うローカル評価スクリプト
|-- review_action_accuracy.py       # 行動やリプレイ確認用の補助スクリプト
|-- requirements.txt                # 最小限の Python 依存関係
|-- setup_windows.ps1               # Windows 用の環境構築スクリプト
|-- baselines/                      # 以前のベースラインエージェント
|-- candidates/                     # 改善ループごとの候補版、研究用バリアント
|-- docs/research/                  # 研究メモ、ログ、改善計画
|-- eval_clones/                    # 決定的評価用のローカル専用クローン
|-- external/                       # 外部・公開ノートブック由来の参考エージェント
|-- locked_submissions/             # 重要な Kaggle 提出時点の正確なスナップショット
|-- notebooks/                      # 参照した公開ノートブックと変換済みコード
|-- tools/                          # 評価・分析用ユーティリティ
`-- variants/                       # 名前付きの公開版・参考版バリアント
```

`__pycache__`、`data`、`logs`、`replays`、`eval_results` などの生成物は Git 管理から除外しています。

## セットアップ

Windows では仮想環境の場所として `C:\owv` を使います。OneDrive 配下では `kaggle-environments` の依存関係が Windows のパス長制限に当たることがあるためです。

```powershell
.\setup_windows.ps1
```

仮想環境を有効化します。

```powershell
C:\owv\Scripts\Activate.ps1
```

最小限の依存関係を入れます。

```powershell
C:\owv\Scripts\python.exe -m pip install -r requirements.txt
```

`kaggle-environments` は依存関係なしで別途インストールします。

```powershell
C:\owv\Scripts\python.exe -m pip install --no-deps kaggle-environments==1.28.0
```

## ローカル評価

組み込みの `random` エージェント相手に簡単な smoke test を実行します。

```powershell
C:\owv\Scripts\python.exe test_local.py --games 5
```

現在のエージェントを特定の相手と対戦させます。

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents locked_submissions\53418690_vickimar_heuristic_fixed_SCORE_908_0.py --games 20 --seats 2
```

2 人戦と 4 人戦の両方を確認します。

```powershell
C:\owv\Scripts\python.exe test_local.py --agent main.py --opponents random --games 10 --seats 2,4 --rotate-seats --out eval_results\smoke_main.jsonl
```

## Kaggle CLI

Kaggle CLI が使えるか確認します。

```powershell
C:\owv\Scripts\kaggle.exe --version
```

Kaggle にログインします。

```powershell
C:\owv\Scripts\kaggle.exe auth login
```

コンペが見えるか確認します。

```powershell
C:\owv\Scripts\kaggle.exe competitions list -s "orbit wars"
```

コンペファイルをダウンロードします。

```powershell
C:\owv\Scripts\kaggle.exe competitions download orbit-wars -p data
```

現在の単一ファイルエージェントを提出します。

```powershell
C:\owv\Scripts\kaggle.exe competitions submit orbit-wars -f main.py -m "submission message"
```

## メモ

- `main.py` は公開 Kaggle Orbit Wars ノートブックとローカルのヒューリスティック改善をもとにしています。
- `locked_submissions/README.md` には、重要な提出スナップショットと観測した公開スコアを記録しています。
- `eval_clones/` は決定的なローカル研究評価用で、soft deadline を無効化しています。Kaggle には提出しないでください。
- コンペページでは、エントリー締切が 2026 年 6 月 16 日、最終提出締切が 2026 年 6 月 23 日 11:59 PM UTC と案内されていました。
