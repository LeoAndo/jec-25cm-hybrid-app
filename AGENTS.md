# AGENTS.md — このリポジトリで作業するAIエージェントへの指示

このファイルは、全エージェント（Claude Code・Codex・Cursor・Antigravity・Devin など）に共通の、ただ1つの指示書です。`CLAUDE.md` はこのファイルを読み込むだけにしてあります。

- **ルールはここに書く。** オーナー（LeoAndo）から新しいルールや方針を受け取ったら、エージェント固有の記憶（Claude Codeのmemory、Cursorのrules、DevinのKnowledgeなど）ではなく、このファイルか `README.md` を直すPRにする。固有の記憶は、ほかのエージェントから読めない。
- **教材の方針は `README.md` にある。** 「基本方針」「授業用教科書の基本方針」「単元の範囲の決め方」「完成コードの書き方」は、教材を触る前に読む。ここには重複して書かない。例外は§11で、READMEの「完成コードの書き方」を、このリポジトリの実物のコードを引いて具体化してある。
- **受講生像と、Monacaのプランの制約だけは、ここにも書く。** 下の「受講生像と、教材の書き方」と「§0-A Monacaの制約」は教材の全判断の前提になるので、READMEを開く前にここで読めるようにしてある。
- **単元ごとの判断は教員用ガイドにある。** `teacher/<スラッグ>/index.html` の「この単元の教材方針」に、何を意図的に外したか、なぜその書き方にしたかが理由つきで書いてある。その単元を触る前に読む。
- issue・PR・コミットメッセージは日本語で書く。

この授業は **ハイブリッドアプリ開発技法（JEC / 25CM）、1コマ90分 × 全15コマ**。単元は2系統ある。

| 系統 | コマ | 開発環境 | プロジェクト | 実行と確認のしかた |
| --- | --- | --- | --- | --- |
| Monaca | 1〜7 | **ブラウザ（Google Chrome）上の Monaca クラウド IDE**。ローカルにビルドコマンドはない | `M0NXxx`（`www/` と `config.xml`・`package.json`・`res/`） | クラウド IDEのプレビュー画面。ローカルでは `www/index.html` を静的サーバで開いて確認する |
| Flutter | 8〜15 | **Visual Studio Code**。ローカルに `flutter` コマンドがある | `F0NXxx`（Flutterプロジェクト一式） | iOSシミュレータ／Androidエミュレータ。静的な確認は `flutter analyze` |

2系統あることが、この運用のほとんどの分岐の理由になっている。**どちらの系統の作業かを先に決めてから読み進める。**

## §0-A Monacaの制約（通常版Monaca Freeプラン）

**この授業のMonacaは「通常版Monaca（`console.monaca.mobi`）のFreeプラン」を使う（オーナー決定）。** Monaca Education は使わない。教育版と通常版はシステムが完全に分離していて、プロジェクトの相互共有もデバッガーアプリの共用もできないので、**教育版向けに書かれた記事・FAQ・前年度資料の手順を、そのまま持ち込まない。** 出典は [Freeプラン](https://ja.docs.monaca.io/faq/free-plan.md)。

Freeプランの利用規約は「法人による商用でのアプリ開発」を禁じているが、**「学習、教育、研修利用を目的としたアプリ開発」は商用に含まないと明記されている**ので、授業での利用は規約上問題ない。アシアル自身も、教育版デバッガーをメンテナンスモードへ移すアナウンス（2023-12-26）で「Cordovaアプリ開発は通常版Monacaをご利用ください」と案内している。

| 項目 | Freeプラン | 教材づくりへの影響 |
| --- | --- | --- |
| **プロジェクト数** | **3個** | **1人が同時に持てるMonacaプロジェクトは3個まで。7コマで7本は作れない。** しかもサインアップ直後に「はじめてのMonacaアプリ」が自動で1つ作られるので、実質の空きは2個 |
| **プロジェクトエクスポート** | **×**（ファイル・フォルダ単位も不可） | **学生は自分の作品をZIPで書き出せない。** 課題のZIP提出は成立しない。持ち出す手段は「公開URL」だけ |
| クラウドビルド | ○（**3回/日**） | 全員が授業中にビルドする回は作らない。ビルドを扱うなら1回で済む設計にする |
| リリースビルド | × | 署名・ストア配布は授業の対象外（§10） |
| カスタムプラグイン | ×（**コアプラグインのみ**） | 教材で使えるCordovaプラグインは、Monacaのコアプラグインに限られる |
| Monaca CLI / Localkit | × | ローカルからMonacaへコマンドで流し込むことはできない。取り込みはダッシュボードの「インポート」だけ |
| ストレージ | 250MB | 画像素材を大量に置かない |
| プロジェクト自動退避 | 180日未ログインでアーカイブ送り | 学期をまたいで残ることを当てにしない |

**配布と提出は、どちらも「プロジェクトの公開URL」で行う。**

- クラウド IDEの **プロジェクト → 公開…** で、`https://monaca.mobi/ja/directimport?pid=<発行されたpid>` の形のURLが発行される。
- このURLは **アプリを動かすURLではなく、プロジェクトを相手のMonacaへ取り込ませるURL**。前年度まで使っていた Monaca Education の「Web公開」（作品をWebで見せる機能）は、通常版Freeには無い。**前年度資料の課題提出手順をそのまま写さない。**
- **学生の課題提出は、学生が自分のプロジェクトを公開し、そのURLを教員に共有する形**（オーナー決定）。教員はURLからインポートして実際に動かして採点する。

**教員アカウントもFreeプランの3枠で運用する（2026-09-23 オーナー決定）。** 完成見本2本は公開を維持し、残り1枠を検証・採点に使う。学生作品は1件ずつ取り込み、確認・採点が済んだコピーだけを削除する。公開用の2本は消さない。

**リポジトリが正で、Monacaは実行環境。** 完成プロジェクトのソースはこのリポジトリで書き、確認のときだけMonacaへ「インポート」で流し込む。Monaca側で書いてエクスポートする経路はFreeプランでは使えない。

**新規プロジェクトのテンプレートは「最小限のテンプレート」**（フレームワークを利用しない空白のプロジェクト）。前年度資料の「クラシック」の代わりにこれを選ぶ。**名前が変わっただけではなく、中身も違う**（§4の `MonacaTemplate/` の項）。ウィザードの選択肢は「サンプル アプリケーション／フレームワーク テンプレート／Capacitor（BETA）／最小限のテンプレート」の4つ。新規作成したプロジェクトのフレームワークは **Cordova 12.0.0**（通常版は2026-05-19に Cordova 13 のサポートも開始している）。

**iOS実機でのデバッグは、通常版のストア版Monacaデバッガーが2023-01-06にApp Storeでの配信停止になっている。** 代替はクイックビューア（モバイルからMonacaにアクセスする。**iPhoneのみ対応**）とシミュレータービルド（生成ZIPをMacのiOSシミュレータへドラッグ＆ドロップ）。Android版デバッガーはGoogle Playから引き続き入る。**「App Storeから Monaca for Study を入れる」とは書かない**（`Monaca for Study` は教育版のアプリで、通常版では使わない。しかも2023-12-26からメンテナンスモードに入っている）。

**承認済み15コマ計画のM01・M02ではOnsen UI 2.12.9を採用する（2026-09-23 オーナー決定）。** 素のJavaScriptから使うUIライブラリとして扱い、Vue・React・AngularJSやビルドツールは足さない。 2026-09時点で Onsen UI は生きている（最新安定版 2.12.9、2026-06-16 公開、Apache-2.0）が、その前の安定版は2022-12-27で、約3年半空いたあとのパッチ1本である。**前年度資料の「AngularJSをベースに」という説明は Onsen UI 1 の話で、v2以降はフレームワーク非依存。そのまま写さない。** 導入はCDN（`unpkg.com`）でよい。

## §0-B Flutterの前提（2026-09-23 時点で実測・確認した事実）

- **学生のMacは全員Apple Silicon（arm64）で、Intel（x64）の学生はいない（2026-09-23 オーナー確認）。** Flutter SDKのダウンロード手順はmacOS arm64に統一する。

- **基準のFlutter SDKは 3.47.5 / Dart 3.13.4（2026-09-18リリース）に固定する。** 学生のAndroid StudioとXcodeの組み合わせ（READMEの「開発環境：学生」）の全部を満たす版として選んだ。選んだ根拠と比較表は README の「Flutter SDKの基準バージョン」にある。**その版で実際に動くかは、授業の中で確かめる（オーナー方針）。**
  - **3.41系では、Android Studio 2026.1 の学生がAndroidのビルドをできない。** Flutterは既定で Android Studio に同梱のJDKを使う。同梱JDKは Panda 2（2025.3）が 21.0.9、2026.1 が 25.0.3（教員Macの実物で確認）。Flutter自身の互換表（`flutter_tools/lib/src/android/gradle_utils.dart`）は「Java 25 には Gradle 9.1.0 以上」としていて、3.41 のテンプレートは Gradle 8.14。**実測でも、3.41 で作ったプロジェクトの `./gradlew help` は JDK 21 で成功し、JDK 25 で `What went wrong: 25.0.3` と失敗した**（ログは `~/Documents/jec-25cm-hybrid-app-verification-deliverables/flutter-sdk-compat-2026-09-23/`）。3.44 のテンプレートは Gradle 9.1.0、3.47 は 9.3.1。
  - **Xcode 27 の学生のために、3.47.4 以上が要る。** 3.47.4 で「Xcode 27 でデバッグすると白い画面のまま数分止まる」（flutter/189284）、3.47.5 で「iOS 27 の実機でデバッグ中にときどき落ちる」（flutter/190307）が直っている。3.44系の変更履歴には Xcode 27 の修正が無い。Xcode 26.4以上の実機デバッグで落ちる不具合（flutter/184254）は 3.41.7 で直っているので、3.47.5 には入っている。
  - 下限は問題にならない。Flutter が要求する Xcode は 3.44 以降で 15 以上（推奨16以上）で、学生の 26.4〜27 はすべて満たす。
  - **授業期間中は `flutter upgrade` しない。** 次の安定版（ブログでは11月）で SDK 内の Material / Cupertino が正式に非推奨になる予定で、上げると教材のコードに非推奨の警告が出始める。学生にもそう案内する。
  - **教員マシンは 3.47.5 / Dart 3.13.4 にそろえた（`~/Downloads/flutter`、2026-09-24 確認）。** 3.41→3.47 の間に AGP 8→9、Gradle 8.14→9.3.1、iOS最低バージョン 13→15、`flutter_lints` 5→6 が動いているので、3.41 の画面や出力で教科書を書くと学生の手元と合わない。
- **`flutter create` は `--empty` と `--platforms=ios,android` を付ける。**
  - 既定テンプレートは、英語のTRY THISコメント約60行＋`StatefulWidget`＋`setState`＋dot shorthand＋`ColorScheme.fromSeed` が最初から全部入っていて、**初回から比較して説明する項目が増え、授業時間を圧迫する**。`--empty` なら `MainApp` と `MaterialApp(home: Scaffold(body: Center(child: Text(...))))` の21行で始まる。カウンターと `setState` は、あとの単元で意図して導入する。
  - `--platforms` を省くと `web/`・`macos/`・`linux/`・`windows/` まで生成され、プロジェクトパネルが読みにくくなる。授業の対象は iOS と Android だけ（§10）。
  - **完成プロジェクトは、フォルダ名を単元名（`F01HelloFlutter`）、Dartのパッケージ名を `--project-name` で別に与える。** `flutter create` はフォルダ名をそのままパッケージ名にするが、パッケージ名は小文字とアンダースコアしか使えないので、`F01HelloFlutter` のままでは作れない。

    ```sh
    flutter create --empty --platforms=ios,android --org jp.ac.jec --project-name f01_hello_flutter F01HelloFlutter
    ```

    `android/app/build.gradle.kts` の `namespace` と `applicationId` は `--org の値 + . + パッケージ名`（この例では `jp.ac.jec.f01_hello_flutter`）になる。`config/teaching-materials.json` の `package_name` と `application_id` に同じ値を書き、`scripts/check-teaching-materials.py` が照合する。学生が授業で作るプロジェクトの `--org` や名前は、教科書の側で決める。
- **dot shorthand（`.fromSeed(...)`、`.center`）は、未説明で使わない。** Dart 3.10（Flutter 3.38）で入った書き方で、既定テンプレートの `main.dart` に最初から出てくる。Web基礎に対応物はないが、**Swiftの implicit member expression（`.center` など）とまったく同じ発想**なので、Swiftとの比較でそのまま説明できる。**新概念の上限には数えないが、比較STEPを省かない。**
- **Material / Cupertino が SDK 本体から独立パッケージ（`package:material_ui` / `package:cupertino_ui`）へ移行中。** SDK内ライブラリは「11月の安定版で正式に非推奨化」予定とブログにあり、授業期間の真ん中に当たる。**この教材は `import 'package:flutter/material.dart'` で通す**（3.47時点で完全に有効で、`flutter create` が生成するのもこれ）。移行は任意なので追わない。教員用ガイドに「なぜ `material_ui` を使わないか」を書く。**混ぜない。** 学生のimportが壊れる。
- **初回のAndroidビルドでは、Gradle本体と依存関係の取得に時間がかかる。** 過去の実測はFlutter 3.41.0での値で、初回debugビルド97.4秒、キャッシュ取得後のreleaseビルド30.1秒だった。3.47.5の授業時間を保証する数値にはしない。
  - `android/gradle/wrapper/gradle-wrapper.properties` の `distributionUrl` を `https\://services.gradle.org/distributions/gradle-9.3.1-bin.zip` にそろえる。公式配布物は `-bin.zip` が約137MB、`-all.zip` が約235MBで、約42%小さい（2026-09-23確認）。
  - 教員が同じURLで取得した `~/.gradle/wrapper/dists/gradle-9.3.1-bin/` を共有またはUSBで配り、学生は**授業時間内に**配置する。ハッシュ階層・展開済みディレクトリ・`.zip.ok` を保持し、別版のキャッシュを上書きしない。`-all.zip` のキャッシュとは共有できない。
  - **`flutter precache` にはAndroid用のフラグがある。** 通常ヘルプでは隠れているだけで、Gradle・Android SDK・NDK・AGPのすべてを用意する保証にはならない。3.47.5のMaven予取得は別のWrapperを使うため、授業の準備完了条件にしない（[3.47.5の定義](https://github.com/flutter/flutter/blob/3.47.5/packages/flutter_tools/lib/src/commands/precache.dart)、[取得処理](https://github.com/flutter/flutter/blob/3.47.5/packages/flutter_tools/lib/src/flutter_cache.dart)）。
  - 配布後もAndroid SDK・NDK・AGP等の取得が残り得る。初回Android実行はコマ14に置き、回線・キャッシュのない環境での所要時間は別途確認する。
- **学生のダウンロードもすべて授業時間内に行う（2026-09-23 オーナー決定）。** コマ7の冒頭にFlutter SDKのダウンロードを開始し、既存のiOSシミュレータ環境を確認する。学生は別科目でXcodeを使っているため、利用できるランタイムがあれば再取得しない。不足分の取得だけをMonacaの仕上げと並行する。コマ8にも準備確認の時間を設ける。授業前の自宅作業を完了条件にしない。
- **初回の実行はiOSシミュレータのほうが軽い。** Swift Package Manager が Flutter 3.44 からデフォルトで有効になり、3.47のiOSテンプレートには Podfile が含まれていない。**プラグインを使わないアプリならCocoaPodsは要らず、Gradleを一切踏まない。** 前年度は初回の回でAndroidとiOSの両方を実行させてAndroidで詰まったので、**「初回はiOSシミュレータ、AndroidはAPKを作る単元で初めて触る」**という順序にする。`xcodebuild -downloadPlatform iOS` は最新のiOSプラットフォームとシミュレータランタイムを取得するため、全員必須にはしない。別科目で利用中のシミュレータで進められる学生は省略する。必要なランタイムがない場合だけ、コマ7で教員と確認して授業中に取得する。
- **Flutter系の課題提出物はAPKファイルとする（2026-09-23 オーナー決定）。** 提出先の上限は100MB以上または上限なしのため、`flutter build apk` の通常APK `app-release.apk` を採用する。生成したAPK自体をAndroidの検証先へインストールして確認する。
- **releaseのAPKは、署名設定なしで作れる。** テンプレートの `android/app/build.gradle.kts` に `signingConfig = signingConfigs.getByName("debug")` が入っているため。**`flutter build apk` は既定でreleaseビルド**（デバッグAPKが欲しいときだけ `--debug`）。旧Flutter 3.41.0での実測サイズは通常APK（全ABI）42.6MB、arm64-v8aのみ15.0MB、debugは138MBだった。今回の完成アプリは3.47.5で通常APKを生成し、容量を確かめる。
- **`INTERNET` パーミッションは `android/app/src/debug/AndroidManifest.xml` と `src/profile/…` にしか入っていない。** `src/main/AndroidManifest.xml` には無い。つまり **`flutter run` では通信できるのに、releaseのAPKでは通信が失敗する**。「授業では動いたのに提出物が動かない」の典型。通信を扱う単元では、その単元の本文の中に `main/AndroidManifest.xml` への追記STEPを置く（他の単元へ送らない）。
- **学生のXcodeは 26.4 / 26.5 / 27 が混在している。** シミュレータの起動方法が Xcode 27以降は `open -a DeviceHub`、26以前は `open -a Simulator` と分かれるので、**教材では Xcode のアプリ名に触れず、Flutterプロジェクトを開いてからVisual Studio Codeの `Flutter: Launch Emulator` で起動し、デバイスを選択する。** `flutter devices` は接続済み端末の一覧表示であり、起動コマンドではない。 本文でOSバージョン分岐を作らない。
- **CocoaPodsのレジストリは2026年12月2日に恒久的にread-onlyになる**と公式が告知している。授業期間中に到来する。プラグインを使う単元を置くなら、この日付の前後で手順が変わらないかを確かめる。

## 受講生像と、教材の書き方

**受講生は Web基礎（HTML / CSS / JavaScript）を履修済みで、Android（Java）と iOS（Swift）のネイティブアプリを作れる。Monaca と Flutter を初めて触る。** 「初学者」とは「このフレームワークが初めて」という意味で、プログラミングの入門者ではない。教材を1文でも書く前に、この前提を思い出すこと。

- **概念そのものの説明はしない。** 変数・条件分岐・繰り返し・関数・DOM・画面遷移・リスト表示が何かは書かない。書くのは、**MonacaやFlutterでの書き方と、知っている書き方との違いと、違う理由**。
- **各STEPには、既知の技術との比較を必ず置く。** 比較の相手は次の3つのどれか（複数でもよい）。比較がないSTEPは未完成とみなす。
  - **Web基礎（HTML / CSS / JavaScript）** — Monaca系ではこれが主軸になる。
  - **Android（Java）** — 画面部品・イベント・画面遷移・保存の対比に使う。
  - **iOS（Swift）** — 同上。
- **Web基礎で習っていないものは、黙って使わない。** 受講生が履修した Web基礎（全14章）には、次のものが**入っていない**。使うなら、必ずその単元のSTEPで書き方・違い・理由を教える。**Java/AndroidまたはSwift/iOSに対応物があるAPIは比較で説明し、新概念の上限には数えない**（2026-09-23 オーナー決定）。対応物がないものだけを、その単元の新概念として宣言する。
  - `querySelector` / `fetch` / `Promise` / `async`・`await` / `JSON` / `localStorage` / アロー関数 / `@keyframes` / CSS Grid / ES Modules / クラス構文
  - 逆に、次は**履修済み**なので説明しない：`getElementById`、`addEventListener`、`classList` の追加削除、フォームの入力値取得、`let` / `const`、配列、関数、条件分岐、繰り返し、flexboxの段組み、メディアクエリ、`transition` によるアニメーション、絶対配置。
- **「1単元で導入する新概念は1つまで」の「新概念」は、Web基礎にもJava/Androidにも Swift/iOS にもないものを指す。** 書き方だけが違うものは数えない（READMEの「単元の範囲の決め方」）。
- **予習も復習もしない前提で、前から順に読めば進める**という構成の原則と、**本文からほかの単元へ送らない**という原則は守る（READMEの「授業用教科書の基本方針」）。**Monaca系の単元で作ったものを、Flutter系の単元の前提にしない。** 系統をまたぐ参照は特に危険で、使う道具も画面も違う。
- **単元の教科書は、「アレンジできる場所」が分かる形で終わらせる。** 最後まで進めた学生が、**どこを変えると、画面や動きの何が変わるか**を、その単元のコードの中で見つけられるようにする。挙げるのは、その単元で扱った範囲で変えられるもの（文字・色・数値・件数など）だけで、新しい概念やAPIをここで足さない。提出課題が「自分で作ったアプリをアレンジして出す」形なので、単元の終わりが、そのときの手がかりになる。例は挙げるが、正解は決めない。
- 前年度（2025年度・24CM01）の配布資料は、参照元としてだけ使う。**PDF・docx自体はリポジトリにcommitしない**（置き場は `~/Documents/jec-25cm-hybrid-app-verification-deliverables/前年度の参考資料/`。§2のPoC置き場と同じ）。

## 1. 作業の単位

**1 issue = 1 ブランチ = 1 worktree = 1 セッション = 1 PR。**

- 1つのセッションで、2つ目のissueや別の単元の作業を始めない。頼まれたら、別のセッション（別のworktree）で行うことを提案する。
- 例外：同じ種類の `size:XS` のissueは、1つのPRでまとめて閉じてよい（`Closes #<番号1>, closes #<番号2>`）。
- 新しい単元は「完成プロジェクト」と「教材一式（教科書＋教員用ガイド＋登録）」の2つのissueに分ける。1つにまとめると `size:XL` になり、1セッションに収まらない（§6）。
- **オーナーが「このセッションで全部進めてよい」と明示したときだけ、この単位を外してよい。** そのときも、やったことはPR本文か報告に残す。

## 2. 作業場所

- ローカルのcloneは1つだけにする。cloneした場所そのもの（mainチェックアウト）は、オーナーとVisual Studio Code／Android Studioが使う。常に `main` のままにして、そこではブランチを切り替えず、コミットもしない。
- エージェントは必ずworktreeで作業する。ツールが自動で作るworktree（Claude Codeの `.claude/worktrees/` など）はそのまま使ってよい。手動で作るときは、mainチェックアウトの外に作る（次のコマンドはmainチェックアウトで実行する）。

  ```sh
  git fetch origin --prune
  git worktree add ../jec-25cm-hybrid-app.worktrees/issue-<番号>-<slug> -b issue-<番号>-<slug> origin/main
  ```

- `git stash` は使わない。stashは全worktreeで共有されるので、ほかのセッションの変更を取り出してしまう。退避したいときはWIPコミットにする。
- **Monaca単元**：ローカルにビルドコマンドはない。`www/` は素のHTML / CSS / JavaScript なので、**静的サーバで開けば、ブラウザだけで動作を確かめられる**（§7）。

  ```sh
  cd M02Xxx/www && python3 -m http.server 8000   # http://localhost:8000 をChromeで開く
  ```

  `file://` で直接開かない。相対パスと `fetch` 系の挙動がブラウザによって変わる。
- **Flutter単元**：worktreeには `android/local.properties` がない（Git管理外のため）。ビルドは環境変数で通す。`local.properties` は作ってもコミットしない。

  ```sh
  cd F01Xxx && flutter pub get && flutter analyze
  cd F01Xxx && ANDROID_HOME="$HOME/Library/Android/sdk" flutter build apk --debug
  ```

  `flutter` がPATHにないときは、オーナーのSDKの置き場を確かめてから前置きする（前年度は `~/Downloads/flutter/bin`）。**SDKの置き場を教材に書くときは、必ず実在を確かめてから書く。**
- **commitしないPoC成果物は、リポジトリの外に置く。** 置き場は `~/Documents/jec-25cm-hybrid-app-verification-deliverables`。なければ作る。

  ```sh
  mkdir -p ~/Documents/jec-25cm-hybrid-app-verification-deliverables
  ```

  ここに置くのは、検証のために撮った大量のスクリーンショット、検証結果をまとめただけのHTML、配布予定のないPoCプロジェクト、前年度の配布資料（PDF・docx）など、commitするとリポジトリが重くなるもの。リポジトリの外なので `.gitignore` は要らない。worktreeの中に作ると、`git clean` やworktreeの削除で消える。
- この置き場のバックアップは取らない。消えて困るものは置かない。教材として配布するスクリーンショットは、ここではなく `docs/<スラッグ>/images/` にcommitする。

## 3. 着手から後片付けまで

1. `git fetch origin --prune` してから、issueを読む（`gh issue view <番号>`）。
2. 重複着手がないことを確認する。`gh pr list --state open` と `git branch -r` に `issue-<番号>-` があれば、誰かが作業中。マージ済みのブランチはGitHubが自動で消すので、リモートにブランチがあること自体が作業中の目印になる。issue本文に「#NN とは同時に進めない」と相手の番号が挙がっていたら、その番号についても同じ確認をする。
   - **リモートだけでは足りない。ローカルのブランチとworktreeも見る。** 手順4のとおりすぐpushしても、ブランチを作ってからpushするまでの数十秒は、リモートに何も出ない。まとめて起動された並行セッションは、全員が同時にこの窓に入る。

     ```sh
     git branch -vv | grep "issue-<番号>-"
     git worktree list
     ```

     ローカルのcloneは1つだけなので（§2）、worktreeとローカルブランチは全セッションで共有される。まだpushされていない別セッションのブランチも、この2つには出る。
   - **見つけたら、先に着手した側を優先し、あとから来た側が降りる。** どちらが先かは `git reflog show --date=iso <ブランチ名>` で分かる。reflogは新しい順に出るので、作成時刻は末尾の `Created from` の行を見る。降りるときは、自分が出してしまった目印を全部片付ける。worktreeを消し（`git worktree remove <パス>`）、その外からローカルブランチを消し（コミット済みなら `git branch -D`）、pushしていればリモートも消す（`git push -d origin issue-<番号>-<slug>`）。手順9がworktreeとローカルブランチの削除を書いているのは「マージ後」なので、降りるときは自分で3つとも消す。
3. 共有ファイル（§4）を触るissueなら、共有ファイルを触るPRがほかに開いていないことを確認する（`gh pr list --state open --label area:shared`）。
4. `origin/main` からブランチ `issue-<番号>-<slug>` を作り、**コミットがなくてもすぐ `git push -u origin issue-<番号>-<slug>` する。** 調査の長いissueでは最初のコミットまで時間がかかることがあり、その間、手順2で見える「作業中」の目印が何も出ない。エージェント名（`claude/`、`codex/`）は付けない。ツールが別の名前でブランチを作っていたら、pushする前に `git branch -m issue-<番号>-<slug>` で直す。
5. 最初のコミットをpushしたら、すぐDraft PRを開く（本文に `Closes #<番号>`）。このときの本文はひな形でよく、完成版に仕上げるのはDraftのうちにする（§8）。Draft PRは「作業中」の目印で、利用制限などで別のエージェントに交代するときの引き継ぎ先にもなる。進み具合はセッションの中ではなく、pushしたコミットとPR本文のチェックリストに残す。
6. **編集を始める直前と、pushの直前に、もう一度 `git fetch origin --prune` する。** 調査やsubagentの待ち時間が長いと、その間に `origin/main` が進み、同じファイルを触るPRが先にマージされていることがある。あわせて手順2・3の確認もやり直す。このとき、手順4で出した自分のブランチ・worktree・PRは数えない。
   - まだコミットがなければ、`git merge --ff-only origin/main` で追従してから編集する。
   - コミット済みで、`origin/main` が自分と同じファイルを変えていたら、試しにマージして（作業ツリーは変わらない）、衝突の有無とマージ後のファイルの形を確かめる。

     ```sh
     if T=$(git merge-tree --write-tree HEAD origin/main); then
       git show "${T}:docs/<スラッグ>/index.html"   # 衝突なし。マージ後の形を確認する
     else
       echo "$T"                                    # 衝突あり。競合したファイルが出る
     fi
     ```

     衝突があると終了コードが1になり、`$T` はtree IDだけでなく競合情報も含む複数行になる。そのまま `git show "${T}:..."` に渡すと `invalid object name` で失敗するので、終了コードで分ける。zshでは `git show $T:docs/...` と書くと `:d` が修飾子と解釈されて失敗するので、`"${T}:..."` と波かっこで囲む。
   - push前ならrebaseしてよい。push済みなら履歴は書き換えず（§5）、必要なら `git merge origin/main` する。
7. issueの「触る範囲」の外は触らない。範囲外で気付いたことは§6の手順でissueにする。
8. コミットは§5、検証は§7の手順で行う。検証が済んだらDraftを外す。レビュー対応は§8。
9. マージ後はworktreeを消す（`git worktree remove <パス>`）。ローカルブランチは `git branch -d` で消す。マージせずに作業をやめたときは、手順4で出した目印のブランチも消す（`git push -d origin issue-<番号>-<slug>`）。GitHubが自動で消すのはマージ済みのブランチだけなので、残すとほかのセッションが作業中と誤解する。

## 4. 並行してよい範囲

| 触る場所 | 並行 |
| --- | --- |
| 単元ごとの場所だけ（`M0NXxx/` か `F0NXxx/` と、その単元の `docs/<スラッグ>/`・`teacher/<スラッグ>/`） | 別の単元のissueとは並行してよい。同じ単元のissue同士は直列 |
| 共有ファイル：リポジトリ直下のファイル（`README.md`、`AGENTS.md`、`CLAUDE.md`、`.gitignore`）、`config/`、`scripts/`、`docs/common/`、`docs/assets/`、`.github/`、`skills/` | 同時に開くPRは1本まで（ラベル `area:shared`） |
| 対訳カタログ：`i18n/<言語>/`（§12） | 別の言語のissueとは並行してよい。単元や共有ファイルのissueとも並行してよい。同じ言語のissue同士は直列（ラベル `area:i18n`） |

- **1つの単元が複数コマにまたがる場合、そのコマどうしは直列になる。** Monaca系は§0の制約でプロジェクト本数を絞るため、1つの単元が何コマも続く。回ごとに教科書のSTEPと完成コードが同じ場所に伸びるので、並行させると必ず衝突する。
- **配布ZIPはバイナリなので、並行する2本のPRが両方作り直すと必ず衝突する。** 片方がマージされたあと、§3の手順6でもう一度 `python3 scripts/package-project.py --project <単元名> --output docs/<スラッグ>/downloads/<単元名>.zip` を実行し直して、自分のPRのZIPを作り直す。ZIPは決め打ちタイムスタンプで作るので、中身が同じなら同じバイト列になる。
- **`MonacaTemplate/` は単元ではなく、しかも2026年の通常版の「最小限のテンプレート」でもない。** 中身は前年度まで使っていた Monaca Education の「クラシック」テンプレートで、`www/classic.js` の冒頭に `Monaca Education Classic Library`、`.monaca/project_info.json` に `cordova_version: 11.0` とある（`classic.js` は `index.html` から読み込まれていない）。オーナーが2026-09-23に通常版で「最小限のテンプレート」から作ったプロジェクトには `.gitignore`・`.monacaignore`・`LICENSE` があって `classic.js` は無く、フレームワークは Cordova 12.0.0 だった。
  - `config/teaching-materials.json` には登録せず、学生用ZIPにも入れない。**中身に手を入れない**（オーナーがcommitしたものなので、比較の基準として残す）。
  - **単元の完成プロジェクトの出発点にしない。** 2026-09-23のオーナー許可により、公式 [monaca-templates/blank 4.0.0](https://github.com/monaca-templates/blank/tree/63b1dd8483612f23b2be35a3e77d7401a6e5b16f)（MIT、Cordova12）を `MonacaMinimumTemplate/` に原本として取り込んだ。以後の単元はこれを複製する。提供画面とCordovaの版・ファイル構成を比較済みで、masterのCordova13ではなく4.0.0を固定した。**原本とクラウドで生成される各ファイルとの完全一致は未確認**で、比較結果と出所は `MonacaMinimumTemplate/README.md` に残す。取り込んだ原本は直接編集しない。 **2026-09-24に最新版master（4.1.6／Cordova13）との違いを再確認し、現在のFreeプランで新規作成した最小限テンプレートもCordova12であることをオーナーが確認し、4.0.0／Cordova12の継続を決定した。**
  - **派生した `M01OshiList` の検証は原本の比較と分けて記録する。** `config.xml` をZIP直下に置く構成で通常版Monacaへのインポートを確認済み。クラウドのiPhone 15（iOS）・Pixel 8（Android）プレビューで一覧・詳細・戻るを確認し、[取り込み用の公開URL](https://monaca.mobi/ja/directimport?pid=6ab3e25de78885da2c0a0ae6)を発行した。この確認は派生M01についてのもので、原本の各ファイルの完全一致確認は別途残る。
  - `www/index.html` と `www/components/loader.js` は **CRLF** になっている。単元へ複製するときは LF にそろえる。`snippets` のバイト一致検査が、教科書のHTML側にも CR を要求してしまうため。
- 新しい単元の登録（§9）は必ず共有ファイルに当たる。2つの単元を同時に登録しない。登録のPRは、既存の全単元の教科書のサイドバーも触る（§9）。`<div class="resources">` は全体で1行なので、ほかの単元のPRが同じ行を触っていると、先にマージされた側と衝突する。相手のPRが開いているあいだは、手順6では分からない（比べる相手が `origin/main` だけのため）。相手がマージされたあとの§3の手順6で確かめ、両方の変更を残す。
- 教科書 `docs/<スラッグ>/index.html` から他単元へのリンクは、topbarとサイドバーの2か所にある。どちらも本文ではなく導線で、手順やコードを他単元へ送るものではない。サイドバーに先の単元へのリンクがあっても、方針違反ではない。
  - **サイドバー**（`<div class="resources">` の1行）には、どの単元でも全単元を単元番号順に並べる。位置は「完成プロジェクトを開く」のあと、「共通：…」の前。いま開いている単元だけはリンクにせず、現在地として書く（`<span aria-current="page">M01：HelloMonaca</span>`）。表示名は、`projects[].name` を番号と残りに分けて全角コロンでつないだ形にする。項目の中に別のタグは入れない。`scripts/check-teaching-materials.py` が、`config/teaching-materials.json` の `projects` の並びと、リンク先・表示名まで照合する。単元を足して1冊でも直し忘れると、CIが落ちる。位置は検査されない。
  - **2系統の並び順は「M→F」。** 検査は、`projects` に最初に現れた接頭辞の順で並んでいること、同じ接頭辞の中では番号が昇順であることを見る。**一度Fに変わったあとでMに戻るとエラーになる。**
  - **topbar** は、直前の単元へのリンク1つだけにする（最初の単元はなし）。こちらは検査されない。単元を挿入したときや、並行して作った単元をマージしたあとは、次の単元のtopbarが直前の単元を指しているかを目で確かめる。指す先が実在するかぎりリンク切れにはならないので、CIでは検出できない。

## 5. コミットのしかた

- `git add -A` と `git add .` は使わない。パスを明示する。
- **コミットの直前に必ず `git diff --cached --name-only` を見て、意図したファイルだけがstageされていることを確認する。** IDEが新規ファイルを自動でstageすることがあり、パスを明示して `git add` しても無関係なファイルが紛れ込む。このリポジトリで特に紛れやすいのは次の3つ。

  | 混入するもの | 出どころ |
  | --- | --- |
  | `.dart_tool/`、`build/`、`.flutter-plugins*`、`ios/Pods/` | `flutter run` / `flutter build` を実行したとき |
  | `android/local.properties`、`.gradle/` | Android Studio でGradle同期したとき |
  | `node_modules/`、`platforms/`、`plugins/` | Monacaプロジェクトで `npm install` 相当を実行したとき |
  | `.DS_Store` | Finderでフォルダを開いたとき。`.gitignore` で無視しているが、**一度追跡されたものには効かない**（2026-09-23 に `git rm --cached` 済み） |

- 混入に気付いたら、push前なら `git rm --cached` して `--amend` する。push済みなら別コミットで `git rm --cached` する（履歴は書き換えない）。
- PRタイトルは、学生が読んで分かる日本語にする。学生向けリリースノートに載るため（READMEの「リリースノートとフィードバックの扱い」）。

## 6. 気付いた別課題はissueにする

- 今のissueの完了条件に含まれるもの、PRを正しくするために必要なものは、そのPRで直す。
- それ以外は、その場で直さずにissueにする。今のPRには混ぜない。
- 起票の前に既存のissueを検索する（closedも含める）。検索語は1つずつ指定する。`OR` でつなぐと、リポジトリの絞り込みが外れて他人のリポジトリのissueが返る。

  ```sh
  gh issue list --state all --search "<語>"
  ```

- ラベルは `size:*` を1つ、`area:*` を当てはまるだけ付ける。本文は次の書式にする。

  ```markdown
  ## 背景
  ## 目的
  ## 再現条件（不具合でなければ「対象」）
  ## 完了条件
  ## 見積（基準：Claude Code / Opus 5 / effort high、2026-09-23）
  - サイズ：S（同種の既存issueと比べて決めた）
  - 推奨構成：軽い構成で可（判断の要らない機械的な修正）
  - 人間の確認：XS（差分の目視のみ）
  - 触る範囲：M02Xxx/www/、docs/<スラッグ>/、config/teaching-materials.json（共有ファイルあり）
  ```

  サイズの根拠には、**実在する既存のissue・PRの番号だけ**を書く。思い当たる番号がなければ、番号を書かずに「同種の既存issueと比べて決めた」と書く。存在しない番号を書くと、あとから根拠をたどれない。
- issueを分割・統合してクローズしたら、そのissueを「同時に進めない」相手として挙げているほかのissueの本文も直す。

### 見積の基準

サイズは時間ではなく、**基準の構成で1セッション（1コンテキスト）に収まるか**で決める。基準の構成は `Claude Code / Opus 5 / effort high、2026-09-23`。差分の行数では決めない（Flutterプロジェクトのひな形でファイル数が膨らむため）。過去のissue・PRと比べて「あれと同じくらい」と決めると、モデルの世代が変わっても使える。

| サイズ | 定義と、このリポジトリでの例 |
| --- | --- |
| `size:XS` | 1ファイル、判断不要、ビルドも実行確認も要らない。例：教科書の誤記を1か所直す、READMEのリンクを1本直す、`teacher/` のコメントを足す |
| `size:S` | 1単元（1コマぶん）に閉じた数ファイルの変更。検査スクリプトか、1回の実行で確認できる。例：Monaca単元の `www/` の文言を直してブラウザで確認する、Flutter単元の1画面を直して `flutter analyze` を通す |
| `size:M` | 複数の単元や共有ファイルにまたがり、全体の照合が要る。例：`scripts/` のロジックを変える、`config/teaching-materials.json` のスキーマを変える、`docs/common/` にページを足す、全教科書のサイドバーを機械的に直す |
| `size:L` | 単元の完成プロジェクト1つ、または教材一式（教科書＋教員用ガイド＋登録）1単元ぶん。1セッションの上限 |
| `size:XL` | 1セッションに収まらない。見積値ではなく分割の合図。このまま着手しない。例：完成プロジェクトと教材一式を1つのPRにまとめる、2つの単元を同時に登録する |

- **推奨構成**は、その作業に足りる最小のモデルとエフォートを書く。判断の要らない機械的な修正（XS・S）は軽い構成でよい。教材の設計判断が要る作業は、最上位のモデルと高いエフォートにする。
- ClaudeとCodexのエフォート段階は同じ尺度ではないので、換算係数は作らない。基準は見出しの1構成に固定し、ほかのエージェントについては「この作業に使える／使えない」だけを書く。基準の構成を変えるときは、この節の書式例と日付を直す。
- **人間の確認**は、オーナーの確認にかかる手間を書く。XS＝差分の目視のみ、S＝ブラウザかシミュレータでの動作確認、M＝複数の単元やファイルの確認、L＝教科書の通読。
- PR本文の最後に実績を1行で残す。見積と実績がずれたら、上の表の例を直す。

  ```markdown
  実績：Claude Code / Opus 5 / high、1セッション、レビュー往復2回
  ```

## 7. 検証

- **CIにMonacaのJavaScript構文検査とFlutterの静的解析を導入する（2026-09-24 オーナー承認）。** `.github/workflows/student-materials.yml` の `validate-app-sources` が、Git管理下のM系 `www/` のJavaScript（標準の `components/` を除く）とF系のFlutterプロジェクトを検出する。教材登録前の完成プロジェクトも対象とし、単元を足すたびにワークフローへ名前を追加しない。Flutterは3.47.5に固定する。第三者Actionの `subosito/flutter-action` は利用可と承認済みで、確認したコミットSHAに固定する。静的解析は以下の画面確認の代わりにはならない。

- 教材・設定・スクリプトを触ったら、次の4つを通す。**4つ目は配布物に入れるファイルを `git ls-files -- docs` で選ぶので、新しいファイルは先に `git add` しておく。** 未追跡のままだと、エラーにならずに配布物から抜け落ちる。**3つ目は `docs/` 配下のHTMLをファイルシステムから直接読むので、未追跡のHTMLも検査の対象になる。**

  ```sh
  python3 scripts/check-teaching-materials.py
  python3 -m unittest discover -s scripts -p 'test_*.py'
  python3 scripts/localize-student-materials.py check
  python3 scripts/package-student-materials.py
  ```

  **Python 3.11以上が要る。** `scripts/test_*.py` が `unittest.TestCase.enterContext`（3.11で入ったもの）を使っている。3.10以下だと2つ目のコマンドだけが大量に失敗するので、コードの不具合と取り違えないこと。`python3 -V` で確かめる。

  それぞれが見ているもの：1つ目は `config/teaching-materials.json` と教材の照合（コマ数の合計、サイドバーの並び、スニペットのバイト一致、ZIPの内容一致、正式表記）、2つ目はスクリプト自身のテスト、3つ目は教科書HTMLから翻訳用の文を取り出せるか（§12の禁止事項を行番号つきで落とす）、4つ目は配布ZIPが最後まで組み立つか。

- **Monaca単元**を触ったら、次の2段階で確かめる。

  1. **ローカルのブラウザ（Google Chrome）で確かめる。** `www/` を静的サーバで開き、画面と操作が教科書のとおりかを見る（§2）。**教材はCordovaプラグインに依存しない作りにするので（§11）、ここまでで機能は全部確かめられる。** `cordova.js` はローカルでは404になるが、プラグインを呼んでいなければ動作に影響しない。
  2. **Monacaのクラウド IDEに取り込んで、プレビューで確かめる。** ダッシュボードの「インポート」から入れる。教科書に載せるスクリーンショットは、このプレビュー画面で撮る。**Freeプランはプロジェクト3個までなので、確認が済んだ一時コピーだけを消して枠を空ける。配布中の完成見本2本は削除しない。**

  この2段階を分けているのは、**エージェントは1だけ自分でできて、2はオーナーのMonacaアカウントが要る**ため。エージェントは1まで実行し、2は「未確認」としてPR本文に書く（オーナーが確認する）。1を飛ばして「Monacaで動くはず」と書かない。
- **Flutter単元**を触ったら、`flutter analyze` を通したうえで、iOSシミュレータかAndroidエミュレータで動かす。画面に関わる変更は必ず実機相当の画面で確かめる。教科書のスクリーンショットもそこで撮る。
- **完成プロジェクトにUnit Testは書かない。** 動作はブラウザ・シミュレータ・エミュレータで確認する。`scripts/test_*.py` はCIで実行されるので、通る状態を保つ。
- 確認できなかった項目は、PR本文に「未確認」と書く。§10の項目は確認しなくてよく、「未確認」にも挙げない。

## 8. PRとレビュー対応

- PR本文は「概要／変更内容／判断したこと／検証／実績」の順に書き、`Closes #<番号>` を入れる。検証の節に「※ リポジトリの方針により、Unit Test は対象外です。」と書く。
  - PR本文に書くときは、Closes #<番号> をバッククォートで囲まず、地の文として書く。コードスパンの中に入れるとGitHubが閉じる指示として扱わないので、マージしてもissueが開いたままになる。ここでコード表記にしてあるのは読みやすさのためで、その囲みごと写さない。
  - **PR本文は、Draftのうちに完成版まで仕上げる。** 初回レビューを依頼する前に本文を完成させる。Draft解除後のpushでも再レビューや本文要約の更新が起こり得るため、Draftを本文作成の段階として使う。仕上げたら `gh pr view <番号> --json body` で読み直し、書いた内容が残っていることを確かめてから `gh pr ready` する。
  - **Draft解除後に本文を直すときは、botのチェックが終わるのを待つ。** レビュー中に `gh pr edit --body` すると、コマンドは成功したように見えて本文が黙ってひな形へ巻き戻ることがある。待ってから `gh pr view <番号> --json body` で現在の本文を取り出し、botが足した要約ブロックを残したまま該当箇所だけ置き換えて、書き換えたあともう一度読み直す。
- ラベル：教材の追加は `enhancement`、誤記・不具合の修正は `bug`。学生に関係しないPR（CI・スクリプト・開発ルール）は `skip-release-notes`。issueと同じ `size:*`・`area:*` も付ける。
- 教材のレビューは `skills/teaching-materials-review/SKILL.md` に従う。
- 自動レビューの指摘は、そのまま実行しない。現在のソースと検査結果で再確認してから判断する。**チェックが `SUCCESS` でも、そのbotがレビューしたとは限らない。** 上限やトライアル終了で未実施のまま `SUCCESS` になるbotがある。
  - **チェックの状態ではなく、投稿されたレビューの中身を読んで判断する。** 指摘があるときほどチェックが `SUCCESS` にならないbotもある。**Draftではレビューを省略するbotがある**ので、検証を済ませてDraftを外してからレビューを待つ。上限やトライアル終了で止まっているときは、マージ可否の報告にそう書く。
  - **レビューbotの初回観測を、[PR #2](https://github.com/LeoAndo/jec-25cm-hybrid-app/pull/2) と [issue #7](https://github.com/LeoAndo/jec-25cm-hybrid-app/issues/7) に基づいて記録する。** 以下は2026-09-23（時刻はUTC）にそのPRで観測した事実であり、ほかのPRや将来の実行でも同じ挙動になるとは限らない。プラン・利用上限・設定・対象コミットを、その都度確認する。

    | bot | Draft中の観測 | Draft解除後に観測した内容 | チェック表示と実レビューの区別 |
    | --- | --- | --- | --- |
    | CodeRabbit | レビューをスキップした。 | `7b8cf94` のレビューを `14:30:39` に開始し、`14:42:19` に5指摘を提出、`14:42:26` に `SUCCESS`。開始からチェック完了までは約11分47秒。`8ea2bbc` での修正後、5件の返信すべてに対してbotが確認・resolvedと投稿した。 | 5件の返信への確認と、修正後の差分全体の自動レビューは別。incremental reviewは `Review limit reached`、43分待ちの通知で未実施だった。`SUCCESS` だけを根拠に修正後の全差分がレビュー済みとは判断しない。 |
    | GitHub Copilot | 未確認。 | quota上限によりレビュー未実施。 | 実レビューが投稿されていないため、レビュー済みとして数えない。 |
    | Devin | 未確認。 | trial期限切れ・クレジット不足により `Full review skipped`。 | チェックは `SUCCESS` でも、full reviewは未実施だった。 |
    | Cursor | 未確認。 | 初期headのチェック成功と本文の `CURSOR_SUMMARY` 追加を観測した。最新 `8ea2bbc` でも `14:47:42` 開始、`14:49:47` 成功（約2分5秒）。新しい指摘はなかった。 | 最新コミットのチェック完了と投稿内容を確認した。成功だけを根拠に、すべての行のレビューを保証しない。 |

    `8ea2bbc` ではCIとbotの処理が完了し、5指摘の解決・新しい指摘なし・`CLEAN` を確認して、`14:51:34` にマージコミットで統合した。43分という待ち時間は、そのとき表示された値であり、今後の標準待機時間にはしない。

    **PR本文では、CodeRabbitとCursorによる要約ブロックの追加を観測した。** botの完了後に要約を残して `gh pr edit` を行い、`gh pr view --json body` で読み直して、意図した本文との一致を確認した。この操作では本文のロールバックは観測しなかった。レビュー中の編集でも安全であると確かめたわけではないため、本文更新後の読み直しは引き続き行う。
- 指摘には、各スレッドにインラインで返信する。先頭に判断を書く。

  ```markdown
  **判断：対応必要（本PRで修正します）**
  **判断：任意対応（…）**
  **判断：対応不要（本PRでは修正しません）**
  ```

  続けて、妥当性・再現性／不具合やデグレの可能性／コストと効果／既存仕様への影響を箇条書きにする。インラインでない指摘にはPRコメントで返す。
- 対応必要の指摘を直したら、検証してコミットし、「修正しました：<sha> …」と検証結果を返信する。立場が変わらない返信は繰り返さない。
- マージ可否は、理由・CIの状態・未対応や未確認の項目を添えて報告する。マージするのは、オーナーに任されているときだけ。そのときも、CIとレビューbotが落ち着き、全指摘に返信済みで、`mergeStateStatus` が `CLEAN` であることを確かめてから、マージコミットでマージする（squashしない）。auto-mergeは有効にしない。

## 9. 新しい単元を追加するとき

`docs/<スラッグ>/` を作るだけでは足りない。次のすべてに登録する。手順は `skills/add-teaching-unit/SKILL.md` にもある。

1. 完成プロジェクト。
   - **Monaca系**：`M0NXxx/` に `config.xml`・`package.json`・`www/`・`res/` を置く。出発点は `MonacaMinimumTemplate/` の固定原本にする（§4。`MonacaTemplate/` は複製しない）。`.monaca/project_info.json`・`.gitignore`・`.monacaignore`・`LICENSE` も保持し、原本のREADMEは複製せず単元用に書く。改行はLFにそろえる。`config.xml` の `<widget id>` と `<name>` を単元に合わせる。**Monacaのクラウドで作ってエクスポートする経路はFreeプランでは使えないので、リポジトリで書いてインポートで確かめる**（§0-A・§7）。
   - **Flutter系**：`F0NXxx/` を `flutter create --empty --platforms=ios,android --org jp.ac.jec --project-name <パッケージ名> F0NXxx` で作る（§0-B）。`pubspec.yaml` の `name` をconfigの `package_name` に、`android/app/build.gradle.kts` の `applicationId` を `application_id` にそろえる。`test/` はカウンターアプリ用のひな形なので消す（Unit Testは書かない。§10）。
2. `docs/<スラッグ>/index.html`、`images/`（画像を使う単元だけ）、`downloads/<Project>.zip`。ZIPは次で作る。

   ```sh
   python3 scripts/package-project.py --project <単元名> --output docs/<スラッグ>/downloads/<単元名>.zip
   ```

   `--project` と `--output` はどちらも必須で、既定値はない。
   - **`images/` を作るのは、その教科書で実際に使うスクリーンショットがあるときだけ。** Monaca系はクラウド IDEのプレビュー、Flutter系はシミュレータ／エミュレータで撮る。**「ここに画像を入れる」のようなプレースホルダは置かない。**
3. `teacher/<スラッグ>/index.html` と `teacher/<スラッグ>/code/`（STEPごとの照合コード。`NN-ファイル名.拡張子` の形式）。「この単元の教材方針」の節を必ず置き、何を意図的に外したかを理由つきで書く。
   - **教科書（手順2）と教員用ガイドの本文には、単元名（`projects[].name`）の表記を必ず入れる。** `scripts/check-teaching-materials.py` が、`docs` に挙げたHTMLを1つずつ開いて探す。
4. `config/teaching-materials.json`：`scan_roots`、正式表記の `required_in`、`projects`。
   - `projects` は単元番号順の位置に足す（サイドバーの検査がこの並びを基準にする。§4）。**M→Fの順を崩さない。**
   - `kind` は `"monaca"` か `"flutter"` のどちらか。ほかの値はエラーになる。
   - `sessions` は、その単元に割くコマ数。**`projects` の `sessions` の合計が `course.total_sessions`（15）を超えるとエラー。** 未満は、まだ単元化していないだけなので通る。
   - `snippets` は `<pre id="…">` とソースをバイト単位で照合するので、コードは手で写さずソースから生成する。
5. `README.md`：教科書リンク、完成プロジェクトのリンク、教員用リンク、15コマ計画表、フォルダ表。
6. 単元どうしのリンク（§4）。サイドバーは、**既存の全単元の教科書**に新しい単元へのリンクを単元番号順の位置へ足し、新しい単元の教科書には全単元を並べる（自単元は `<span aria-current="page">`）。1冊でも直し忘れると、`scripts/check-teaching-materials.py` が落ちる。topbarは、新しい単元に直前の単元へのリンクを置く。topbarは検査されないので、目で確かめる。既存の教科書のサイドバーは、issueの「触る範囲」に挙がっていなくても、登録に必要な変更なので同じPRで直す（§6）。
7. GitHubのラベル `area:M<NN>` / `area:F<NN>`。
8. 翻訳の対象は `docs/` のHTMLから自動で見つかる。新単元のPRでは日本語だけを追加し、`python3 scripts/localize-student-materials.py check` で文を取り出せることを確かめる（§7）。翻訳そのものは日常のPRでは行わない（§12）。
9. **提出課題の共通資料が古くなっていないかを確かめる。** 提出課題は「学生自身が作ったアプリを選んでアレンジして出す」形で、Monaca系は公開URL、Flutter系はビルド成果物を出す（READMEの「提出課題」）。単元が増えると、学生が選べるアプリの本数と顔ぶれが変わるので、単元名を挙げている箇所と本数に触れている箇所が古くなる。古くなっていたら、この登録のPRで一緒に直す（`docs/common/` は共有ファイル。§4）。

### 単元を足しても、配布スクリプトには何も書かない

**`scripts/package-student-materials.py` と `scripts/release-student-materials.py` は直さない。** どちらも単元の一覧を `config/teaching-materials.json` の `projects` から読む。完成プロジェクトZIPの再生成も、`はじめに.txt` の単元一覧も、リリースノートの単元一覧も、上の手順4でconfigに足した時点で自動的に付いてくる。**スクリプトに単元名や単元番号を直書きしない**（配布ZIPの名前や見出しのような、単元に依存しない固定値は直書きでよい）。

## 10. 対象外

次の項目は、レビューで指摘しない。botに指摘されたら「対応不要」と返信する。検証もしない。

- 完成プロジェクトのUnit Test（§7）。テストしやすくするためのリファクタリングもしない。**Flutterプロジェクトの `test/` にひな形が生成されるが、授業では触らない。**
- Windows。教員も学生もmacOSで、CIはubuntu（READMEの「開発環境」）。
- ダークテーマ。確認は既定のライトテーマだけで行う。直書きの色もそのままにする。
- タブレット・フォルダブル対応、画面回転と横画面。
- **Flutterの対象プラットフォームは iOS と Android だけ。** `flutter create` は `web/`・`macos/`・`linux/`・`windows/` も作るが、授業では扱わない。「Webでも動くはず」「デスクトップ対応を」という指摘は対象外。
- **提出物の署名（リリースビルド）。** Monacaはそもそも**Freeプランでリリースビルドができない**（§0-A）。Flutter側は、テンプレートがデバッグ鍵でreleaseに署名するため、署名設定なしでAPKが作れる（§0-B）。署名鍵の作成・ストアへの公開は授業の範囲外とする。「ストアに出せない」「署名されていない」という指摘は、仕様どおりなので「対応不要」と返信する。教材にも署名の手順は書かない。
- **Monaca Education の機能**（Web公開、共同編集、データベース、コース機能）。この授業は通常版Freeプランで進める（§0-A）ので、Education固有の機能を前提にした指摘は対象外。

## 11. 完成コードの書き方

READMEの「完成コードの書き方（全単元共通）」を、系統ごとに具体化したもの。教材のコードを書くとき・レビューするときは、ここを基準にする。

### Monaca系（HTML / CSS / JavaScript）

1. **素のHTML / CSS / JavaScript で書く。** 承認済みのM01・M02では、Onsen UI 2.12.9を素のJavaScriptから使うUIライブラリとして採用する。Vue / React / AngularJSや、webpackなどのバンドラー・ビルドツールは追加しない。受講生はWeb基礎で素のHTML/CSS/JSを書いているため、追加のフレームワークやビルド工程を挟まず、自分が書いたコードと画面の対応を追える形にする。
2. **Web基礎で習った書き方にそろえる。** 要素の取得は `document.getElementById`（`querySelector` は使わない）、イベントは `addEventListener`、クラスの付け外しは `classList.add` / `classList.remove`。**別の書き方に変えない。**（理由はREADMEの「授業用教科書の基本方針」）
3. **Cordovaプラグインに依存しない。** 使ってよいのは、ブラウザだけで動く範囲。カメラ・GPS・通知などプラグインが要る機能は、**Freeプランでコアプラグインしか使えない**うえ、ローカルのブラウザでもプレビューでも確かめられないので扱わない。結果として、`www/` は静的サーバで開くだけで全部確認できる状態を保つ（§7）。
4. **結果は画面に出す。`console.log` で済ませない。** 学生はアプリを触っているとき開発者ツールを見ていない。押しても何も起きないアプリになると、自分のコードが動いたかを確かめられない。開発者ツールは、学生が中身を確かめるための補助として扱う単元でだけ使う。
5. **`alert` に頼らない。** Web基礎ではダイアログを習っているが、アプリのUIとしては画面の書き換えで見せる。
6. **命名は、その部品の種類が分かる形にする。** `txtXxx` / `btnXxx` / `imgXxx` / `listXxx`。idは `id="btn_start"` のようにスネークケース、JavaScriptの変数は `btnStart` のようにキャメルケースでそろえる。
7. **`config.xml` の `<widget id>` は `jp.ac.jec.<単元名の小文字>` にする。** `<name>` はアプリ名（日本語でよい）。
8. **コメントは、学生が読んで意味が分かる日本語で書く。** 英語のコメントにしない。「何をしているか」ではなく「なぜそう書いたか」を書く。

### Flutter系（Dart）

1. **`lib/` 以外は触らない。** `android/`・`ios/` はウィザードが作ったままにする。触るのは `pubspec.yaml`（パッケージ追加とアセット登録）まで。**全単元に共通する例外は2つ**で、どちらも§0-Bに理由がある：通信を扱う単元の `android/app/src/main/AndroidManifest.xml` への `INTERNET` 追記と、初回ビルドを軽くするための `gradle-wrapper.properties` の `-bin.zip` 書き換え。 **これに加えて、F01・F02の配布見本では、生成時に入った作成者個人の `ios/Runner.xcodeproj/project.pbxproj` の `DEVELOPMENT_TEAM` 指定3行も除く（2026-09-24のオーナーへの確認と続行指示による例外）。** ほかの署名設定は変更せず、学生に署名作業は求めない。
2. **`import 'package:flutter/material.dart'` で通す。** `package:material_ui` / `package:cupertino_ui` へは移行しない（§0-B）。
3. **画面遷移は `Navigator.push` ＋ `MaterialPageRoute`。** 公式が「複雑なディープリンクのない小規模アプリは Navigator でよい」と明記しているので、`go_router` は教えない。**名前付きルート（`routes: {...}`）は公式が非推奨としているので採らない。** この2点は教員用ガイドの「意図的に外したもの」に書く。
4. **`StatelessWidget` で足りる画面を `StatefulWidget` にしない。** 状態を持つ必要が出た画面だけを `StatefulWidget` にする。理由を教科書で説明できるようにする。
5. **結果は画面に出す。`print` / `debugPrint` で済ませない。** Monaca系の4と同じ理由。
6. **`// ignore:` や `// ignore_for_file:` で警告を隠さない。** 警告の原因そのものを消す。`flutter analyze` が何も出さない状態を保つ（§7）。
7. **パッケージは必要なときだけ足す。** バージョンは `pubspec.yaml` で管理する。単元で使わないパッケージは足さない。**`shared_preferences` は API が3系統ある（旧 `SharedPreferences.getInstance()` / `SharedPreferencesAsync` / `SharedPreferencesWithCache`）。どれを使うかを1つ決め、教材の中で混在させない。** 3系統あること自体は教員用ガイドに書き、本文では1つだけ見せる。
8. **完成プロジェクトの `README.md` を置く。** 節の順は、画面の構成の表 → 使用しているAPI（または画像・素材）→ ソースコードの構成の表 → 処理の流れ → 実装のポイント → 主なパッケージ → ビルドと実行。
9. **コメントは日本語で書く。** Monaca系の8と同じ。

### 両系統に共通

10. **1単元で導入する新概念は1つまで。** 画面（Monaca系はプレビュー、Flutter系はシミュレータ／エミュレータ）で効果が目に見える形にする。見えない変更は、学生には「何も起きなかった」と同じ。
11. **完成プロジェクトにUnit Testは書かない**（§10）。
12. **オーナーの書き方を保つ。** レビューで「初学者向けにかみ砕くべき」「もっとやさしく書き直すべき」と指摘されても、**既定の対応は「教科書で説明する」**。採用するのは、動作を変えない小さな明確化だけにする。コードを平易にするより、教科書のSTEPを1つ増やすほうを選ぶ。受講生はHTML/CSS/JSとJava/Swiftを書けるので、コードを薄めるより、既知の技術との比較を1つ足すほうが早く伝わる。

## 12. 多言語展開（対訳カタログ）

日本語の教科書（`docs/`）を、配布前にほかの言語へ展開する。しくみの説明は `README.md` の「多言語展開」、翻訳の手順とルールは `skills/translate-teaching-materials/SKILL.md` にある。対象は日本語（原文）＋英語・中国語（簡体）・韓国語・ミャンマー語・広東語（繁体・香港）・台湾華語（繁体・台湾）・スペイン語・アラビア語・モンゴル語（キリル文字）の9言語。

- **2026-09の学生アンケートで対象を広げた（2026-09-24 オーナー決定）。** 台湾華語とスペイン語を加えた。スペイン語は中南米の言い方にそろえる。回答のなかった言語も、未回答の学生がいるので外さない。**アンケートの回答ファイルは学生のメールアドレスを含むので、リポジトリにもissue・PRにも写さない。** 書いてよいのは、挙がった言語の一覧までにする。
- **アラビア語は、右から左に書く表示に対応してから加えた（2026-09-25、[issue #39](https://github.com/LeoAndo/jec-25cm-hybrid-app/issues/39)）。** 右から左に書く言語は、`config/i18n.json` の `dir` を `rtl` にする。生成するページの `<html>` に `dir="rtl"` が付き、日本語のまま残る未翻訳の文には `dir="ltr"` が付く。
- **`docs/assets/textbook.css` には、左右を決め打ちした指定を書かない。** `border-left`・`padding-left`・`left:`・`text-align: left` などの代わりに、論理プロパティ（`border-inline-start`・`padding-inline-start`・`inset-inline-start`・`text-align: start`）を使う。日本語のページでは同じ見た目になり、アラビア語のページでは左右が入れ替わる。`scripts/test_localize_student_materials.py` が検査する。右から左のページだけに当てる指定は `[dir="rtl"]` で絞る（`code` に `unicode-bidi: isolate` を当てると、日本語のページでも行の折り返す位置が変わるため）。
- **モンゴル語は、モンゴル国のキリル文字（`mn`、横書き）で加えた（2026-09-25 オーナー確認）。** 学生本人に読む文字を確かめた結果（[issue #40](https://github.com/LeoAndo/jec-25cm-hybrid-app/issues/40)）。伝統的モンゴル文字（縦書き、`mn-Mong`）には対応しない。

- **いまは `config/i18n.json` の `en` と `zh-Hans` だけが `distribute: true`（2026-09-25 オーナー決定）。** 2026-09-28 の授業開始に合わせて、日本語・英語・中国語（簡体）の3言語で初版を配布する。ほかの7言語は `false` のままで、後期の授業が始まってから1言語ずつ段階的に進める。`false` の言語を未翻訳が残ったまま `true` にすると、公開ゲート（`localize-student-materials.py status --require-complete`）で止まる。
- **`true` に上げてよいのは、次の2つが両方終わった言語だけ。**
  1. その言語の未翻訳が0件になっている（`python3 scripts/localize-student-materials.py status`）。
  2. 翻訳したのとは別のAIが、その言語の全文を原文と1回照合し終えている（前に照合したページも含める）。**照合は、翻訳と同じセッション・同じPRの中のsubagentが行ってもよい**（オーナーの判断、2026-09-24）。照合の担当は、訳した担当とは別のモデルにする。自分で訳して自分で照合しない。
- **`true` に上げるのは、1PRにつき1言語。** `distribute` を上げるPRは共有ファイル（`config/`）を触るので `area:shared` になる（§4）。初版の `en` と `zh-Hans` だけは、授業開始に間に合わせるため、オーナーの判断で1本のPRにまとめて上げた（2026-09-25）。
- **照合は、学生の手に渡る前に1回だけ行う（2026-09-25 オーナー決定、[issue #87](https://github.com/LeoAndo/jec-25cm-hybrid-app/issues/87)）。** 訳すたびには照合しない。基準は、きれいな訳文ではなく、学生が操作を間違えないことに置く（配布する翻訳ページには日本語版が正という注記と、日本語版へのリンクが付く。コード・キー・正式表記・タグの数は `check` が検査する）。同じ学生が受ける Kotlin演習（jec-25cm-kotlin）と同じ決まりにしてある（[jec-25cm-kotlin #100](https://github.com/LeoAndo/jec-25cm-kotlin/issues/100)）。
  - `distribute: false` の言語の翻訳PRでは、照合しない。`check` と確認用ページの目視までにする。`en`・`zh-Hans` 以外の7言語の翻訳PRは、いまはどれもこれに当たる。
  - `distribute` を `true` に上げるときに、その言語の全文を1回照合する（上の2）。
  - `distribute: true` の言語の差分翻訳は、訳した文が50文以上のときだけ照合する（下の手順4）。
  - 照合し直すのは、照合のあとで意味が変わる修正をした文だけ。記号・大文字と小文字・言い回しのそろえでは照合し直さない。
  - 原文を見ずに日本語へ訳し戻して比べるのは、ミャンマー語だけ。ほかの言語は対訳を並べて読む。
  - 照合の記録は、PR本文と、指摘の全件を残すPRのコメントだけにする。用語集に「照合の記録」の節を作らない。
- **日常のPRでは翻訳しない。** `docs/` の日本語を直しても、`i18n/` は触らない。直した文は自動で未翻訳に戻り、CIは未翻訳の数を表示するだけで落ちない。翻訳は、配布前の翻訳PRでまとめて行う。配布していない言語（`distribute: false`）の文は、配布前の翻訳PRでも訳さず、日本語で表示されるままにする。その言語の翻訳PRか、その言語を配布対象に上げるときに訳す。
- **教科書のHTMLには、次の形を書かない。** どれも `python3 scripts/localize-student-materials.py check` が行番号つきで落とす（§7の `unittest` にも含まれる）。黙って壊れるより、書いた人がその場で気付けるようにしてある。
  - 開始タグと終了タグの不一致（`<p>`・`<li>`・`<td>` の閉じ忘れ）と、`<span/>` のような自己終了タグ。文を取り出せない。
  - 引用符で囲んでいない属性（`<html lang=ja>`、`href=images/x.png`）。値の終わりが決まらず、書き換えた結果が壊れる。
  - 文の途中のHTMLコメント（`<p>あいう<!-- メモ -->えお</p>`）。訳文で置き換えるとコメントが消え、前後の文字が連結される。段落の外に書く。
  - `/` で始まるルート相対のリンク（`href="/docs/assets/textbook.css"`）。GitHub Pagesがリポジトリ名の下にあるので日本語版でも使えない。
  - 文の途中の要素に付けた `translate="no"`（`<span translate="no">`）。その文が断片に割れて訳せなくなる。
- **訳してほしくない文字は、`<code>` で囲む。** `<code>`・`<kbd>`・`<pre>` の中身は、どの言語でも日本語版のまま出る。既知技術との比較ブロックのコードも `<pre>` の中なので、どの言語版でもそのまま出る。言語名のラベルだけは文になるので、`<p class="compare-lang" translate="no">JavaScript</p>` のように**ブロック要素に** `translate="no"` を付けて外す。Monaca クラウド IDEのメニュー名、Visual Studio Codeのメニュー名、Flutterのウィジェット名、パッケージ名はここに入れる。段落や表のセルを丸ごと訳の対象から外したいときは、その要素（`<p>`・`<td>`・`<div>` など、文の区切りになる要素）に `translate="no"` を付ける。
- **各言語のHTMLはコミットしない。** コミットするのは `i18n/<言語>/` の対訳カタログと `glossary.md`（用語集）だけ。確認用のページは `dist/i18n-preview/` に作る（`dist/` はGit管理の対象外）。
- **カタログの `source` は手で書き換えない。** 訳を直すときは `translation` だけを直す。並べ替えと、使わなくなった訳の削除は、`sync` と `merge` が行う。
- 翻訳のPRには `area:i18n` を付ける。学生用ZIPに入るまでは `skip-release-notes` も付ける。

### 配布準備のissueと翻訳PR

1. 配布準備のissueを起票し、対象の版・言語・未翻訳の件数を書く。§6の書式とサイズ見積を使い、`area:i18n` と `size:*` を付ける。翻訳PRにも同じラベルと `enhancement` を付ける。まだ配布対象でない言語だけのPRには `skip-release-notes` も付ける。
2. 最新のmainで `python3 scripts/localize-student-materials.py status` を実行する。翻訳用skillに従い、未翻訳の文だけを訳す。Actionsで翻訳APIを呼ぶ処理やSecretは追加しない。
3. **翻訳PRを開いてから学生向けの公開が終わるまでは、`docs/` を触るPRをマージしない。** 翻訳PRの本文に、この期間と対象の版を書く。日本語の変更が入った場合は最新のmainを取り込み、差分だけを訳し直す。
4. **訳した文が50文以上なら**、翻訳したのとは別のAIが、新しく訳した文を原文と照合する。50文未満なら照合せず、翻訳の担当が訳を見直して、その旨と文の数をPR本文に書く。照合では、ミャンマー語だけ原文を見ずに訳文を日本語へ訳し戻してから比べ、ほかの言語は対訳を並べて読む（翻訳用skillの「別のモデルによる照合」）。意味の違い・訳し落とし・足しすぎ・操作順・用語集との不一致を確かめる。**照合の担当には資料を自分で読ませ、指摘は全件を要約せずにPRのコメントに残し（ミャンマー語の綴りは写さない）、照合のあとで意味が変わる修正をした文だけ照合し直す**（くわしくは翻訳用skillの同じ節）。PR本文には担当と照合範囲、指摘への対応を残す。全体を訳し直す必要はない。
5. §7の4つの検証に加え、`python3 scripts/localize-student-materials.py status --require-complete` を通す。ZIPの入口 `index.html` から配布対象の言語を開き、リンク・コードのコピー・共通資料からの戻り先を確認する。
