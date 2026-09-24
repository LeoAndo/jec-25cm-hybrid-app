# F02StampRelease — スタンプ帳：追加・保存・APK提出

Flutter 3.47.5 / Dart 3.13.4で、習慣の入力と端末内保存を加えるコマ12〜15の完成見本です。Visual Studio Codeを使います。

## 画面の構成

| 画面 | 表示・操作 |
| --- | --- |
| 一覧 | 習慣・合計・スタンプ、追加、1つ戻す、詳細、読込状況、初期化 |
| 追加 | 名前40文字・続けたい理由200文字、空欄検証、追加して保存 |
| 詳細 | 選んだ習慣の名前・回数・理由、戻る |

## 使用しているAPI・素材

- Flutter SDKのMaterialウィジェットと標準アイコン。外部画像・通信は使いません。
- `TextField` / `TextEditingController`、`Navigator.push` / `MaterialPageRoute`、`showDialog`。
- `SharedPreferencesAsync`の`getStringList` / `setStringList` / `remove`、`Future` / `async` / `await`。
- 習慣と理由は架空の記入例です。私生活の開示を求めず、自分が扱いやすい題材へ変えられます。

## ソースコードの構成

| ファイル・型 | 役割 |
| --- | --- |
| `lib/main.dart` / `StampApp` | 起動・配色 |
| `Habit` | 名前・理由・回数 |
| `StampBoardPage` | 保存の読込・検証・書込、一覧の状態、画面遷移、初期化 |
| `StampMarks` / `HabitDetailPage` | 値を受け取る表示専用の部品・画面 |
| `AddHabitPage` | 入力、検証、保存完了を待って戻る |
| `pubspec.yaml` / `pubspec.lock` | 依存の指定と解決済みの版 |

## 処理の流れ

1. 起動時に保存キー`jec-25cm-stamp-release-v1`を読みます。未保存なら初期の3件、有効な保存値ならその内容を表示します。
2. スタンプ操作は元のHabitを変更せず次の配列を作り、保存成功後に画面へ反映します。回数は0〜5です。
3. 入力画面は空欄・空白だけを止め、保存成功を待って一覧へ戻ります。失敗時は入力内容を残します。
4. 初期化は確認画面で同意したときだけ、このアプリのキー1個を削除します。取消しでは変えません。

## 実装のポイント

新概念は非同期処理の`Future` / `async` / `await`です。同期処理と完了を待つ処理の順序、成功・失敗、画面が破棄された後の`mounted`確認を教材で説明します。入力欄・コントローラ・保存キー・例外処理・ライフサイクル・コールバックはJava／Swiftの対応物と比較します。

保存形式は文字列リストで、1件を「名前・理由・回数」の3要素にします。JSONをFlutter側の前提にしません。読込時は要素数、空文字、数値と範囲を検証し、空リストは有効な0件として扱います。不正な保存値や読込失敗を初期データで上書きせず、追加・スタンプを止めて再読込または本人が選ぶ初期化へ案内します。

保存・読込中は操作を止めます。入力画面は`PopScope`と戻るボタンで保存中の移動を抑え、成功後に戻ります。表示と保存が食い違うのを避けるため、保存する前に元の状態を変更しません。保存領域全体の`clear`は使いません。

端末内の少量の記録を扱う教材です。`shared_preferences`は重要データの永続性を保証する用途に使いません。同期APIやキャッシュ付きAPIと混ぜず、`SharedPreferencesAsync`だけを使います。日付・通知・ログイン・通信・データ移行は扱いません。入力済みの記録は提出APKに含まれないため、採点先でも見せるアレンジは初期データ・文字・配色などのソースへ残します。

`package:flutter/material.dart`を授業の固定SDKで使い、`material_ui`を混ぜません。画面遷移は小規模な3画面なので`Navigator.push`と`MaterialPageRoute`に統一し、名前付きルートと`go_router`は使いません。

## 主なパッケージ

| パッケージ | 用途 |
| --- | --- |
| Flutter SDK | Material UIと画面遷移 |
| shared_preferences 2.5.5 | `SharedPreferencesAsync`による端末内保存 |
| flutter_lints 6系 | 静的解析 |

依存する各プラットフォーム実装の解決済みの版は`pubspec.lock`へ記録しています。

## ビルドと実行

Visual Studio Codeの`File > Open Folder…`でこのフォルダを開き、`Terminal > New Terminal`で実行します。授業期間中は`flutter upgrade`しません。

```sh
flutter pub get
flutter analyze
flutter devices
flutter run -d <起動済み端末のID>
```

`Flutter: Launch Emulator`で既存のiOSシミュレータ、またはAndroidエミュレータを起動・選択します。既存のiOSランタイムを使える場合、追加取得は不要です。配布見本では生成時に入った個人のiOS署名チーム指定3行だけを除き、学生に署名作業は求めません。AndroidのGradleは公式9.3.1の`bin.zip`です。

提出用の通常APKは次のコマンドで作ります。既定はreleaseで、生成された設定のdebug鍵を使います。ストア配布は扱いません。

```sh
flutter build apk
flutter run --release --no-resident -d <AndroidエミュレータのID> --use-application-binary=build/app/outputs/flutter-apk/app-release.apk
```

生成物は`build/app/outputs/flutter-apk/app-release.apk`です。入力済みのデータを配るファイルではありません。2026-09-24に通常APK（48,666,844 bytes、約48.7MB）を生成しました。Flutter 3.47.5の`flutter analyze`は指摘なしです。Android 17の専用arm64エミュレータで、最終APKの初期表示・追加・保存・5回上限・取消し・詳細・再起動時の名前／理由／回数の復元・初期化の取消しと確定を確認しました。Androidの空欄検証も実施し、リポジトリ外の検証コピーでは保存失敗時の回数維持と入力保持、不正データでの上書き防止、空リストの0件表示を確認しました。

iOS 26.5（iPhone 17 Pro）で起動・スタンプ保存・空欄検証を確認しました。学生全員のSDK・端末の組み合わせと教室の同時取得時間は未確認です。完成アプリのUnit Testはリポジトリ方針により作成していません。
