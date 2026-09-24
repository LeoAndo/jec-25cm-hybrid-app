# 用語集：简体中文（zh-Hans）

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

同じ学生が Kotlin演習（jec-25cm-kotlin）も受けている。この表の訳語は、jec-25cm-kotlin の `i18n/zh-Hans/glossary.md` と同じにしてある。変えるときは、あちらも同じように直す。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| プロジェクト | 项目 | |
| パッケージ | 包 | `f01_hello_flutter`・`package:flutter/material.dart` などのパッケージ名は訳さない |
| 関数 | 函数 | `function`（JavaScript）・`void main()`（Dart）の表記は原文のまま |
| 変数 | 变量 | `let` / `const`（JavaScript）・`var` / `final`（Dart）の表記は原文のまま |
| 実行 | 运行 | Monacaのメニュー名 **実行** は日本語のまま残し（运行）を添える。Visual Studio Code のボタンの表示は Run を保持 |
| コンソール | 控制台 | Chromeのデベロッパーツールの Console、Visual Studio Code の Debug Console は保持 |
| エミュレータ | 模拟器 | Androidエミュレータ。Flutter系の単元で使う。シミュレータと同じ語になるので、区別が要るときは Android 模拟器 と書く |

## この授業の用語

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| ハイブリッドアプリ | 混合应用 | |
| ネイティブアプリ | 原生应用 | |
| アプリ | 应用 | |
| クロスプラットフォーム | 跨平台 | |
| WebView | WebView | Android の `WebView`、iOS の `WKWebView` に当たる。訳さない |
| クラウドIDE | 云端 IDE | ブラウザで使う開発環境。Monacaの画面名として出るときは日本語のまま残す |
| テンプレート | 模板 | |
| 公開 | 公开 | Monacaの **プロジェクト → 公開…**。発行されるのはプロジェクトを取り込ませるURLで、アプリを動かすURLではない。「Web公开（托管）」の意味にしない |
| 公開URL・取り込み用のURL | 导入链接 | `https://monaca.mobi/ja/directimport?pid=…` の形のURL。開くと、そのプロジェクトが自分のMonacaに取り込まれる |
| インポート・取り込む | 导入 | ダッシュボードの **インポート** は日本語のまま残す。Dart の `import` 文は `<code>` の中なので関係ない |
| エクスポート | 导出 | Freeプランでは使えない |
| プレビュー | 预览 | クラウドIDEの画面名 **プレビュー** は日本語のまま残す |
| ビルド | 构建 | jec-25cm-kotlin の用語集と同じ訳語。変えるときは、あちらも同じように直す |
| クラウドビルド | 云构建 | |
| デバッグ | 调试 | jec-25cm-kotlin の用語集にはまだ無い |
| 実機 | 真机 | |
| シミュレータ | 模拟器 | iOSシミュレータ。エミュレータと同じ語になるので、区別が要るときは iOS 模拟器 と書く。jec-25cm-kotlin の用語集にはまだ無い |
| デバイス | 设备 | Visual Studio Code のデバイス選択の画面名は英語のまま |
| ウィジェット | Widget | Flutter中文文档（docs.flutter.cn）に合わせて英字のまま。组件 と訳す資料もある。要確認 |
| 宣言的UI | 声明式 UI | |
| 状態 | 状态 | `setState` は `<code>` のまま |
| ホットリロード | 热重载 | |
| 画面遷移 | 页面跳转 | `Navigator` は `<code>` のまま |
| 非同期 | 异步 | `async` / `await` は `<code>` のまま |
| コマ | 节课 | 1コマ＝90分の授業1回。「2コマ目」は 第2节课 |

## Web基礎で習った用語

学生が履修済みの用語。定訳を使い、説明を足さない。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| 要素 | 元素 | HTMLの要素 |
| 属性 | 属性 | HTMLの属性 |
| イベント | 事件 | |

## Monacaの画面に出る言葉（日本語のまま残し、訳をかっこで添える）

Monacaは日本語表示で使う。画面の言葉は訳さずに残し、うしろにこの表の訳をかっこで添える（例：**プロジェクト → 公開…**（项目 → 公开…））。かっこの訳は意味を伝えるためのもので、Monacaの中国語表示の文字と同じとは限らない。

| 画面の言葉 | かっこに添える訳 | 場所 |
| --- | --- | --- |
| ファイル | 文件 | クラウドIDEのメニュー |
| 編集 | 编辑 | クラウドIDEのメニュー |
| 表示 | 查看 | クラウドIDEのメニュー |
| 実行 | 运行 | クラウドIDEのメニュー |
| ビルド | 构建 | クラウドIDEのメニュー |
| プロジェクト | 项目 | クラウドIDEのメニュー |
| 設定 | 设置 | クラウドIDEのメニュー |
| ヘルプ | 帮助 | クラウドIDEのメニュー |
| 公開… | 公开… | プロジェクトメニュー |
| インポート | 导入 | ダッシュボード |
| 新しいプロジェクトを作る | 新建项目 | ダッシュボード |
| クラウドIDEで開く | 在云端 IDE 中打开 | ダッシュボード |
| 最小限のテンプレート | 最小模板 | 新規作成のテンプレートの選択肢 |
| プレビュー | 预览 | クラウドIDEの画面 |
