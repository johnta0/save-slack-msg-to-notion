# save-slack-msg-to-notion

## Prerequisite

### Slack のアーカイブダウンロード

https://slack.com/help/articles/201658943-Export-your-workspace-data に従ってアーカイブをダウンロードし、
適当な場所で zip を解凍する。そのパスを .env に記載すること。

### Notion の設定

* https://developers.notion.com/docs/create-a-notion-integration などのに従って Integration を作成する
* Notion Web 版で、右上にある「・・・」マークから Connect to をクリックし、上で作成した Integration を接続する

### .env の設定

上記で作成した情報を .env に登録する。

```
cp .env.example .env
```

とし、内容を書き換える。

### rye の設定

rye を使用しています。セットアップしてください。


## 実行

```bash
rye sync
```

を実行したあと、以下のコマンドでスクリプトを実行する。

```
rye run save_msg_to_notion
```

### CSV を作成してそれを Notion に Import する方法

量が多いならこちらの方がだいぶ速く済む。以下のコマンドを実行し CSV を作成し、それを Import する方法だ。
しかし、既に存在する DB に追加はできず、全く新しい DB を作成することになるので注意。

```
rye run gen_import_csv
```

## 最後に

このコードはほとんど Claude が書いてくれました。便利だね

