# M01OshiList — 好きなものノートの一覧と詳細

Monacaのコマ1〜4で作る「好きなものノート」の完成プロジェクトです。日常の中で見つけた「好きな音楽」「カレー」「公園」の3件をカードにし、押した項目の好きな理由を読みます。授業では静的なカードから順に作り、この完成版は動作確認とコード比較に使います。

## 画面の構成

| 画面 | 表示するもの | 操作 |
| --- | --- | --- |
| 一覧 | 名前・種類を載せた3枚のカード、選択した項目 | カードを押すと、その詳細を開く |
| 詳細 | 名前、種類、好きな理由 | 左上の戻るボタンで一覧へ戻る（iOS向けは「＜ 戻る」、Android向けは矢印「←」だけ） |

読み直すと初期状態に戻ります。この単元では入力・追加・保存は扱いません。

## 使用するAPIと素材

- Onsen UIの`ons-navigator`、`ons-page`、`ons-toolbar`、`ons-list`、`ons-list-item`、`ons-back-button`、`init`、`pushPage`。
- 標準JavaScriptの`getElementById`、`addEventListener`、`innerHTML`、`textContent`、配列、関数、条件分岐、繰り返し。
- 表示データは`www/js/app.js`にあるサンプルの文字列です。外部APIや画像の取得処理はありません。
- `res/`のアイコン等は最小限テンプレートの原本を保持しています。

## ソースコードの構成

| ファイル | 役割 |
| --- | --- |
| `www/index.html` | ライブラリ読込、一覧と詳細のtemplate、画面部品 |
| `www/css/style.css` | カードの枠と余白、文字の色と大きさ、詳細コメントの改行 |
| `www/js/app.js` | 初期データ、一覧作成、選択、詳細へのデータ受渡し |
| `config.xml` | アプリ名「好きなものノート」、ID `jp.ac.jec.m01oshilist` |
| `package.json` | テンプレート由来の依存とプロジェクト情報 |
| `.monaca/project_info.json` | テンプレート由来のMonaca設定 |
| `www/components/` | テンプレート由来のMonaca読込コード |

## 処理の流れ

1. `index.html`がMonacaの読込コード、Onsen UI、`app.js`を読み込みます。
2. Navigatorが`list.html`のtemplateから一覧ページを作ります。
3. 一覧の`init`で`renderOshiList()`を呼び、配列の件数分の行を作ります。
4. 各行の名前と種類を`textContent`で設定し、クリックイベントを登録します。
5. 行を押すと選択名を更新し、`pushPage`の`data`で項目を詳細ページへ渡します。
6. 詳細の`init`で、`page.data.oshi`から名前・種類・コメントを表示します。
7. 戻る部品が詳細を閉じると、一覧と選択名が再び見えます。

## 実装のポイント

この単元で初めて導入する概念は、同じマークアップをOSに応じて描き分ける**auto-styling**です。一覧・画面遷移・イベントは、Web基礎、Java / Android、Swift / iOSの既知の書き方と比較して扱います。

- `init`はページが作られたときに使います。template内のDOMを、それより前に取得しません。
- HTMLの骨組みをまとめて置いたあとに、文字とイベントを設定します。表示データをHTML文字列に連結せず、`textContent`で文字として表示します。
- `ons-list-item`に`oshi-card`を付け、余白と角丸の枠でカードにします。`width: auto`で左右の余白を含めて画面に収め、一覧と行の既定罫線を外します。行の中央の要素は右の余白を30px空け、長い名前が右端の目印と重ならないようにします。ツールバー・戻る部品・押したときの表現はOnsen UIに任せます。
- `ons-back-button`が戻る処理を持つため、独自の戻るイベントは足しません。
- 遷移中の連打はBooleanで抑え、完了時の`callback`で解除します。`pushPage`の返り値を扱うコードは書きません。
- アプリの処理はCordovaプラグインを呼びません。`www/components/`や`package.json`にあるテンプレート由来の依存は保持していますが、この単元の機能に追加プラグインは不要です。

アレンジできる場所は次のとおりです。

| 変更する場所 | 変わるもの |
| --- | --- |
| `app.js`の`oshiItems`の`name`・`genre`・`comment` | 一覧と詳細の文字 |
| `oshiItems`の項目数・並び順 | 一覧の件数・順序 |
| `style.css`の`.app-caption`・`.app-selection`の`color` | 詳細の種類・一覧上部の説明と、選択名の色 |
| `style.css`の`.app-section`の`padding` | 画面の余白 |
| `style.css`の`.oshi-card`の`border`・`border-radius`・`margin` | カードの枠・角丸・間隔 |
| `style.css`の`.app-heading`の`font-size` | 見出しの大きさ |

## 主な依存と出所

| 依存 | 版・用途 |
| --- | --- |
| Onsen UI | **2.12.9**。`index.html`に固定したCDN URLから読み込む（Apache-2.0） |
| 最小限テンプレート | [monaca-templates/blank 4.0.0](https://github.com/monaca-templates/blank/tree/63b1dd8483612f23b2be35a3e77d7401a6e5b16f)、コミット`63b1dd8483612f23b2be35a3e77d7401a6e5b16f`（MIT） |
| monaca-plugin-monaca-core | 3.3.1。テンプレート由来の依存を保持 |
| Cordova / browser-sync | `package.json`の`^12.0.0` / `~2.27.7`を原本から保持。ローカル確認ではインストールしない |

テンプレートのMITライセンスは`LICENSE`に残しています。クラウドからエクスポートした生成物ではなく、公開原本を複製したものです。`.monaca/project_info.json`の設定も原本を保持しており、現在のクラウドで選べるビルド環境を示す一覧ではありません。

Onsen UIのCSSはアイコン用CSSやフォントも取得します。CDNに接続できる環境で確認します。JSとCSSの3ファイルだけをコピーしてオフライン実行できるとは限りません。

APIの根拠：[初期化とページイベント](https://onsen.io/v2/guide/lifecycle.html)、[画面遷移とデータ受渡し](https://onsen.io/v2/api/js/ons-navigator.html)、[auto-stylingとOS指定](https://onsen.io/v2/guide/theming.html#cross-platform-styling-autostyling)。

## ビルドと実行

### ローカルのGoogle Chrome

ターミナルで、この`README.md`がある`M01OshiList`フォルダに移動して実行します。`npm install`は不要です。

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory www
```

Google Chromeで[ローカルの好きなものノート](http://127.0.0.1:8765/)を開きます。停止するときはターミナルで`Control + C`を押します。`index.html`を`file://`で直接開かず、HTTPで確認します。

auto-stylingは、[iOS指定](http://127.0.0.1:8765/?platform=ios)と[Android指定](http://127.0.0.1:8765/?platform=android)を開いて比較します。これはOnsen UIが用意している検証用の指定です。幅を変えるだけでOSも変わるとは限りません。

コードで指定する場合は、`app.js`冒頭の`ons.platform.select("android");`を有効にして読み直します。`"ios"`へ変えるとiOS風になります。比較が終わったらコメントに戻します。指定はページ生成前に行い、`ons.ready`の中へ移しません。

### 動作確認の項目

- 一覧の3項目をそれぞれ開くと、対応する名前・種類・コメントが表示される。
- 戻ると一覧が見え、選択した名前が残る。繰り返しても行やイベントが増えない。
- 行を素早く続けて押しても、詳細画面が重ならない。
- `oshiItems`の名前を`A < B & C`に変えても、一覧と詳細に文字として表示される。
- 配列に1件追加すると4件目が表示され、その詳細も開ける。
- iOS指定とAndroid指定で、ツールバー・戻る部品・タップ表現の違いが見える。

### 確認状況

2026-09-24、題名を「好きなものノート」、初期の3件を好きな音楽・カレー・公園へ変更しました。好きな理由は2文で、`\n`で改行します。データの3プロパティ、識別子と画面遷移の処理は維持しています。変更後のローカルChromeの390px幅で、一覧・全3件の詳細・理由の改行・戻る・選択名の保持・連打を確認しました。

同日、公開用のMonacaプロジェクトへ同じ`index.html`・`style.css`・`app.js`・`config.xml`・`package.json`を保存し、エディター上の全文がこのフォルダと一致することをSHA-256で照合しました。iPhone 15とPixel 8のプレビューでは、Reload後に全3件の詳細・理由の改行・戻る・選択名の保持を確認しました。行を3回続けて押しても詳細は1画面だけで、戻る1回で一覧へ戻ることも確認しました。公開URLは作り直していません。2026-09-24、オーナーがM01の公開URLから取り込み、内容に問題がないことを確認しました。この記録は公開後に追記しています。

2026-09-25、PR #65（#46）で変えた`www/css/style.css`（一覧の行の右の余白30px）を公開用のMonacaプロジェクトへ保存し直し、`index.html`・`style.css`・`app.js`・`config.xml`・`package.json`のエディター上の全文が`main`（332011a）と一致することをSHA-256で照合しました（issue #94）。公開URLは作り直していません。公開URLからの取り込みは、保存した最新の内容を取り込ませます。

以下の2026-09-23の記録は、学習・開発を題材にしていた変更前の版についてのものです。

2026-09-23にGoogle Chromeの390px幅で、3件の詳細・戻る・選択名の保持・連打、iOS/Androidのauto-stylingを確認しました。検証用コピーでは4件への追加と`A < B & C`・`<b>そのまま表示</b>`の文字表示も確認済みです。

通常版Monacaの「インポート → ZIPファイル」で、`config.xml`をZIPの直下に置いた構成の取り込みが成功しました。ダッシュボードでCordova 12.0.0、Monaca クラウド IDEのiPhone 15／Pixel 8プレビューで一覧・詳細・戻る・選択名の保持を確認しました。端末を切り替えたあとにプレビューのReloadを押し、iOSとAndroidの戻る部品の違いも確認済みです。

[完成見本をMonacaへ取り込む](https://monaca.mobi/ja/directimport?pid=6ab3e25de78885da2c0a0ae6)。このURLはアプリのWeb公開ではなく、プロジェクトの取り込み用です。取り込む前に3枠の空きを確認してください。公開URLからの再取り込みは、題材変更後の版でオーナーが確認しました（上記）。

インポート用ZIPは`config.xml`が直下の構成で検証しました。教材のダウンロードZIPはプロジェクト名のフォルダで包んだコード比較用であり、この包み方でのMonaca取り込みは未確認です。
