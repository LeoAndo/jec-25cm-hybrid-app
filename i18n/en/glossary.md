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

| ハイブリッドアプリ開発技法 | Hybrid App Development | 授業名。学生用ZIPの入口ページ（`package-student-materials.py`）と同じつづり。Techniques は付けない |
| Web基礎 | Web Basics | 学生が履修済みの科目名 |
| 通常版Monaca | standard Monaca | Monaca Education ではない通常版 |
| Freeプラン | Free plan | |
| 枠（プロジェクトの枠） | slot | Freeプランの3枠。空き＝free slot |
| 教材 | materials | |
| 教科書 | textbook | |
| 学生用ZIP | student ZIP | |
| 共通資料 | shared guide | `docs/common/setup.html`。見出し「授業を始めるまでの準備」は Getting ready for class、サイドバーの「共通：はじめの準備」は Shared: Getting ready for class（jec-25cm-kotlin と同じ） |
| 完成見本 | completed sample | finished sample とは書かない |
| 完成プロジェクト | completed project | |
| 開始コード | starting code | 各コマの最初にある合流用のコード |
| 合流（する） | join partway through | 途中のSTEPから加わること |
| 全文（コード見出しの `· 全文`） | full file | `www/index.html · full file` |
| 単元 | unit | |
| コマ（見出し） | Session N | `STEP 00 · Session 5`、`Sessions 5–7 · 90 minutes each`。本文の「第Nコマ」は session N |
| アレンジ | customize / customization | jec-25cm-kotlin と同じ |
| 題材 | topic | 学生が自分で決める好きなもの・習慣などの内容。Flutter の theme と区別する |
| 先生／教員 | your teacher / the teacher | |
| 提出 | submit / submission | 提出先＝submission site、提出物＝deliverable |
| 好きなものノート | favorites notebook | M01・M02の題材。画面の題名 「好きなものノート」 は日本語のまま残し (Favorites Notebook) を添える |
| 好きなもの | favorite | |
| 名前・種類・好きな理由 | name / type / reason | 画面の項目名。コードのプロパティ `name`・`genre`・`comment` は原文のまま |
| ひとこと | short comment | M01の第1コマのカードの文 |
| 一覧／詳細 | list / detail screen | |
| 行 | row | 一覧の1行 |
| 右端の目印（＞） | marker (＞) at the right edge | Onsen UI の chevron |
| 端末選択 | device selector | プレビューの iPhone 15／Pixel 8 |
| OSの強制指定 | forced OS setting | `ons.platform.select` |
| 押す／クリック | tap / click | 端末の操作は tap、マウスは click |
| 初期化 | reset | 画面の「初期の内容に戻す」は日本語のまま残し (Restore initial contents) を添える |
| 確認欄（初期化の確認欄） | confirmation panel | M02の初期化のパネル |
| 確認欄（STEPの確認欄） | check box | 各STEPの末尾のチェック |
| 保存キー | storage key | `localStorage` のキー |
| 読込／読み込み | load | 読込失敗＝load failure |
| 復元 | restore | |
| 保存領域 | storage area | |
| スタンプ帳 | stamp board | F01・F02の題材。stamp book とは書かない |
| 習慣 | habit | |
| 目標回数 | goal count | `stampGoal` |
| 回数 | count | |
| 合計 | total | |
| スタンプを押す／1つ戻す | add a stamp / undo one | 画面のボタンは日本語のまま残し (Add a stamp)／(Undo one) を添える |
| 詳しく見る | (See details) | 画面のボタン。日本語のまま残す |
| 達成メッセージ | achievement message | |
| ホットリスタート | hot restart | |
| 非同期処理 | asynchronous processing | |
| 待機中 | waiting | 保存中の表示 |
| 空欄 | empty field | |
| 通常APK | normal APK | `flutter build apk` の既定（release）のAPK |
| 端末ID | device ID | `flutter devices` で見る値。`端末ID` が `<code>` の中にあるときは (端末ID = device ID) と添える |
| Gradleキャッシュ | Gradle cache | |
| 空テンプレート | empty template | `flutter create --empty` |
| 制作フォルダ | work folder | |
| 条件演算子 | conditional operator | `? :` |
| 名前付き引数 | named argument | jec-25cm-kotlin と同じ |

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

## 書き方の決まり

- 見出しは文頭だけ大文字（sentence case）。`〜` の範囲は en dash（`STEP 00–04`、`Sessions 5–7`）。
- かぎかっこ「」は `"…"` にする。ただし画面やアプリに出る日本語は 「」 のまま残し、うしろに (gloss) を添える（`「まだ選択していません」 (Nothing selected yet)`）。`<code>` の中の日本語の置き換え語は、閉じタグのうしろに `(端末ID = device ID)` の形で添える。
- 各STEPの確認欄の文は、一人称の過去形（I checked …）ではなく、確かめ終えた状態で書く：`… has been checked.`、`… is displayed.`、`You can explain …`（jec-25cm-kotlin と同じ）。
- Monaca クラウド IDE の画面の言葉は日本語のまま残し、上の表のかっこ書きを添える。Visual Studio Code・Xcode・Flutter の画面の言葉は英語のまま。
- 授業名は Hybrid App Development、前の科目は Web Basics。単元名（`M01：OshiList`）は訳さない。
