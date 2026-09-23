# 用語集：English（en）

ハイブリッドアプリ開発技法の対訳表。訳すときは、この表の訳語を使う。新しく訳語を決めた用語は、行を足す。全言語に共通の翻訳ルールは `skills/translate-teaching-materials/SKILL.md` にある。メモに「要確認」とある行は、訳語に自信がないもの。翻訳PRで確かめたら「要確認」を消す。

## 製品名（訳さない）

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| Monaca | Monaca | 通常版Monaca（Freeプラン）。Monaca Education とは別のサービス |
| Monaca クラウド IDE | Monaca クラウド IDE | 正式表記をそのまま保持する |
| Flutter | Flutter | |
| Dart | Dart | |
| Visual Studio Code | Visual Studio Code | 正式表記をそのまま保持する |
| Google Chrome | Google Chrome | |
| Xcode | Xcode | |
| Android Studio | Android Studio | Androidエミュレータと Android SDK のために使う |
| Cordova | Cordova | Apache Cordova |
| Onsen UI | Onsen UI | |

## 両科目に共通の用語（jec-25cm-kotlin とそろえる）

同じ学生が Kotlin演習（jec-25cm-kotlin）も受けている。この表の訳語は、jec-25cm-kotlin の `i18n/en/glossary.md` と同じにしてある。変えるときは、あちらも同じように直す。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| プロジェクト | project | |
| パッケージ | package | `f01_hello_flutter`・`package:flutter/material.dart` などのパッケージ名は訳さない |
| 関数 | function | `function`（JavaScript）・`void main()`（Dart）の表記は原文のまま |
| 変数 | variable | `let` / `const`（JavaScript）・`var` / `final`（Dart）の表記は原文のまま |
| 実行 | run | Monacaのメニュー名 **実行** は日本語のまま残し (Run) を添える。Visual Studio Code のボタン名は **Run** のまま |
| コンソール | console | Chromeのデベロッパーツールの Console、Visual Studio Code の **Debug Console** は原文のまま |
| エミュレータ | emulator | Androidエミュレータ。Flutter系の単元で使う |

## この授業の用語

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| ハイブリッドアプリ | hybrid app | |
| ネイティブアプリ | native app | |
| アプリ | app | |
| クロスプラットフォーム | cross-platform | |
| WebView | WebView | Android の `WebView`、iOS の `WKWebView` に当たる。訳さない |
| クラウドIDE | cloud IDE | ブラウザで使う開発環境。Monacaの画面名として出るときは日本語のまま残す |
| テンプレート | template | |
| 公開 | publish | Monacaの **プロジェクト → 公開…**。発行されるのはプロジェクトを取り込ませるURLで、アプリを動かすURLではない。前年度の「Web公開」（web hosting）とは別物なので、host とは訳さない |
| 公開URL・取り込み用のURL | import URL | `https://monaca.mobi/ja/directimport?pid=…` の形のURL。開くと、そのプロジェクトが自分のMonacaに取り込まれる |
| インポート・取り込む | import | ダッシュボードの **インポート** は日本語のまま残す。Dart の `import` 文は `<code>` の中なので関係ない |
| エクスポート | export | Freeプランでは使えない |
| プレビュー | preview | クラウドIDEの画面名 **プレビュー** は日本語のまま残す |
| ビルド | build | jec-25cm-kotlin の用語集にはまだ無い。あちらに足すときは同じ訳語にする |
| クラウドビルド | cloud build | |
| デバッグ | debug | jec-25cm-kotlin の用語集にはまだ無い |
| 実機 | real device | |
| シミュレータ | simulator | iOSシミュレータ。jec-25cm-kotlin の用語集にはまだ無い |
| デバイス | device | Visual Studio Code のデバイス選択の画面名は英語のまま |
| ウィジェット | widget | 個々のクラス名（`Text`、`Scaffold`）は `<code>` の中なので訳さない |
| 宣言的UI | declarative UI | |
| 状態 | state | `setState` は `<code>` のまま |
| ホットリロード | hot reload | |
| 画面遷移 | screen navigation | 文脈により navigating between screens。`Navigator` は `<code>` のまま |
| 非同期 | asynchronous | `async` / `await` は `<code>` のまま |
| コマ | class session | 1コマ＝90分の授業1回。「2コマ目」は session 2 |

## Web基礎で習った用語

学生が履修済みの用語。定訳を使い、説明を足さない。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| 要素 | element | HTMLの要素 |
| 属性 | attribute | HTMLの属性 |
| イベント | event | |

## Monacaの画面に出る言葉（日本語のまま残し、訳をかっこで添える）

Monacaは日本語表示で使う。画面の言葉は訳さずに残し、うしろにこの表の訳をかっこで添える（例：**プロジェクト → 公開…** (Project → Publish…)）。かっこの訳は意味を伝えるためのもので、Monacaを英語表示にしたときの文字と同じとは限らない。

| 画面の言葉 | かっこに添える訳 | 場所 |
| --- | --- | --- |
| ファイル | File | クラウドIDEのメニュー |
| 編集 | Edit | クラウドIDEのメニュー |
| 表示 | View | クラウドIDEのメニュー |
| 実行 | Run | クラウドIDEのメニュー |
| ビルド | Build | クラウドIDEのメニュー |
| プロジェクト | Project | クラウドIDEのメニュー |
| 設定 | Settings | クラウドIDEのメニュー |
| ヘルプ | Help | クラウドIDEのメニュー |
| 公開… | Publish… | プロジェクトメニュー |
| インポート | Import | ダッシュボード |
| 新しいプロジェクトを作る | Create a new project | ダッシュボード |
| クラウドIDEで開く | Open in the cloud IDE | ダッシュボード |
| 最小限のテンプレート | Minimal template | 新規作成のテンプレートの選択肢 |
| プレビュー | Preview | クラウドIDEの画面 |
