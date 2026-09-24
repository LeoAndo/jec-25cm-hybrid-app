# F01StampBoard — スタンプ帳

Flutter 3.47.5 / Dart 3.13.4で、習慣のカードとスタンプを作るコマ8〜11の完成見本です。作業にはVisual Studio Codeを使います。

## 画面の構成

| 画面 | 表示・操作 |
| --- | --- |
| 一覧 | 習慣3件、合計、各習慣のスタンプと回数。押す・1つ戻す・詳しく見る |
| 詳細 | 選んだ習慣の名前、スタンプ、回数、続けたい理由。戻る操作 |

## 使用しているAPI・素材

- Flutter SDKのMaterialウィジェットと標準アイコン。外部画像・通信は使いません。
- `StatefulWidget` / `setState`、`StatelessWidget`、`Navigator.push` / `MaterialPageRoute`。
- 習慣と理由は架空の記入例です。コード中の文字・色・目標回数を自分の題材へ変えられます。

## ソースコードの構成

| ファイル・型 | 役割 |
| --- | --- |
| `lib/main.dart` の `StampApp` | 起動、配色、最初の画面 |
| `Habit` | 名前・理由・回数 |
| `StampBoardPage` | 一覧と回数の更新、詳細への移動 |
| `StampMarks` | 回数に応じたマークの表示 |
| `HabitDetailPage` | 表示専用の詳細 |
| `pubspec.yaml` | SDKと依存の指定 |

## 処理の流れ

1. 初期データ3件を0回で表示します。
2. 「スタンプを押す」で回数を1増やし、`setState` でカード・合計・マークを描き直します。
3. 目標の5回に達したら追加ボタンを無効にし、達成メッセージを表示します。「1つ戻す」は0回で無効になります。
4. 「詳しく見る」で選んだ `Habit` を表示専用画面へ渡します。戻ると、一覧の回数は維持されます。

## 実装のポイント

この単元の新概念は宣言的UIです。DOMやネイティブViewを個別に書き換える方法と、現在の値から `build` が画面を返す方法を比較します。

一覧だけが状態を管理し、マークと詳細は `StatelessWidget` にしています。Dartのクラス・名前付き引数・`final`・クロージャ・null・文字列補間・リスト内のforは、Java／SwiftやWeb基礎の対応する書き方と比較して説明します。dot shorthandは使わず、`CrossAxisAlignment.start` のように型名を省略しません。

保存・入力追加・日付によるリセット・通知はこの単元では扱いません。バックグラウンドへ移しただけでは回数が残ることがありますが、アプリを終了して起動し直すと0へ戻ります。ホットリロードは状態を維持し、ホットリスタートは初期化するため、初期データを変更した際はホットリスタートします。

画面遷移は `Navigator.push` と `MaterialPageRoute` に統一します。小規模な2画面で深いリンクは扱わないため、名前付きルートや追加のルーティングパッケージは使いません。授業で固定した3.47.5では `package:flutter/material.dart` が利用できるため、移行先の `material_ui` は混ぜません。

## 主なパッケージ

| パッケージ | 用途 |
| --- | --- |
| Flutter SDK | Material UIと画面遷移 |
| flutter_lints 6系 | 静的解析。解決済みの版は `pubspec.lock` に記録 |

## ビルドと実行

Flutter 3.47.5を使い、授業期間中は `flutter upgrade` しません。

```sh
flutter pub get
flutter analyze
flutter devices
flutter run -d <起動済みシミュレータのID>
```

Visual Studio Codeの `File > Open Folder…` でこのフォルダを開き、`Flutter: Launch Emulator` から既存のiOSシミュレータを起動・選択できます。別科目のランタイムを再利用できる場合、追加ダウンロードは不要です。

配布用のため、生成時に入った個人のiOS署名チーム指定3行は除いています。iOSシミュレータの実行に署名チームの設定は不要です。

AndroidのGradle配布物は公式9.3.1の `bin.zip` にしています。Androidで実行する場合も起動済みエミュレータのIDを指定します。APKの作成・提出は後続単元の教材内で扱います。

```sh
flutter run -d <起動済みAndroidエミュレータのID>
```

2026-09-24にFlutter 3.47.5で `flutter analyze` の指摘なしと、iOS 26.5シミュレータ（iPhone 17 Pro）で起動・加算・5回の上限・取り消し・詳細表示を確認しました。アプリのUnit Testはリポジトリ方針により作成していません。
