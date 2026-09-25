---
name: add-teaching-unit
description: Add a new teaching unit to this hybrid app course repository - a Monaca unit (M01-, kind "monaca", plain HTML/CSS/JS written in the repository and imported into the Monaca cloud IDE) or a Flutter unit (F01-, kind "flutter", created with flutter create --empty and edited in Visual Studio Code). Covers the completed project, the student textbook under docs/, the teacher guide under teacher/, the config registration, the README entries, and the sidebar links in every existing textbook. Also covers the short path for adding the next class session's STEPs to a unit that spans several sessions, which does not add a unit. Use when asked to add, create, or register a new unit, a new textbook page, a new teacher guide, or the next session of an existing unit.
---

# Add teaching unit

作業を始める前に、`AGENTS.md` の §0-A（通常版Monaca Freeの制約）、§0-B（Flutterの前提）、§9（新しい単元を追加するとき）、§11（完成コードの書き方）と、`README.md` の「基本方針」「授業用教科書の基本方針」「単元の範囲の決め方」を読む。このskillは、その手順を作業の順に並べ直したもの。食い違ったら `AGENTS.md` を正とする。

**最初に、どちらの系統の単元かを決める。** 系統で、完成プロジェクトの作り方・configの書き方・確かめ方が分かれる。

| 系統 | `kind` | 単元名 | 開発環境 | 確かめ方 |
| --- | --- | --- | --- | --- |
| Monaca（コマ1〜7） | `"monaca"` | `M01HelloMonaca` など | Google Chrome 上の Monaca クラウド IDE | ローカルの静的サーバ＋Chrome、最後にオーナーがMonacaへインポートしてプレビュー |
| Flutter（コマ8〜15） | `"flutter"` | `F01HelloFlutter` など | Visual Studio Code | `flutter analyze`、iOSシミュレータ／Androidエミュレータ |

単元名は「接頭辞（`M` か `F`）＋2桁の番号＋PascalCase」。`config/teaching-materials.json` の `projects` は M→F の順に並べ、一度Fに変わったらMに戻さない。同じ接頭辞の中は番号の昇順。

## はじめに：単元の次のコマを足すだけなら、この手順は要らない

**1つの単元は、複数のコマにまたがってよい**（configの `sessions` に2以上を書く）。とくにMonaca系は、Freeプランでプロジェクトを3個までしか持てない（AGENTS.md §0-A）ので、1つのプロジェクトを何コマもかけて育てる。そのときも**教科書は1冊**（`docs/<スラッグ>/index.html`）で、コマごとにSTEPを足していく。

すでにある単元に次のコマのSTEPを足す作業は、**単元の追加ではない**。直すのは次の8か所だけで、この下の「1.」以降は読まなくてよい。

1. **完成プロジェクト**（同じ `M0NXxx/` か `F0NXxx/`）のコードを、そのコマの終わりの形まで進める。ファイルを足したら、configの `sources` にも足す。
2. **前のコマのコードを凍結する。** 完成プロジェクトのファイルを書き換える前に、前のコマの終わりの形を `teacher/<スラッグ>/code/NN-ファイル名.拡張子`（NNはそのコードを見せたSTEPの番号）に残す。前のコマで `snippets` の `source` や `mirrors` がそのファイルを指していたら、ファイルを書き換えた時点で一致しなくなるので、次のように付け替える。
   - `snippets`：前のコマのSTEPの `<pre id>` の `source` を、凍結した `teacher/<スラッグ>/code/NN-…` に替える。検査は `<pre>` と `source` のファイルを突き合わせるだけなので、`source` に `teacher/` の下のファイルを書いてよい。
   - `mirrors`：完成プロジェクトと同じ中身であることを求める複製なので、前のコマの形になったものは `mirrors` から外す（ファイルは照合コードとして残す）。新しいコマの終わりの形を、新しい番号で `mirrors` に足す。
3. **`config/teaching-materials.json`**：その単元の `sessions` を1増やす。**全単元の `sessions` の合計が15を超えるとエラー**になる。`sources`・`snippets`・`mirrors` も1と2に合わせる。
4. **教科書** `docs/<スラッグ>/index.html`：いまあるSTEPのうしろにSTEPを足す。
   - サイドバーの目次に、コマの切れ目が分かる見出しを足す（`<p class="eyebrow">2コマ目 · STEP 07〜12</p>` のあとに、そのコマのSTEPの `<ol>`）。
   - `.progress` の `max` と `data-progress-label` の総数を、STEPの数に合わせる。
   - **`<body data-progress-key>` の値と、いまある `data-check` の値は変えない。** 変えると、学生が前のコマで付けたチェックが消える。
   - 新しいコマの最後にも「アレンジできる場所」を置く（README「授業用教科書の基本方針」11）。
5. **教員用ガイド** `teacher/<スラッグ>/index.html`：進め方にそのコマ（どのSTEPを扱うか）を足す。そのコマで意図的に外したものがあれば「この単元の教材方針」に足す。
6. **`README.md`**：15コマ計画表に、そのコマの行を足す。
7. **完成プロジェクトのZIPを作り直す。**

   ```sh
   python3 scripts/package-project.py --project M01HelloMonaca --output docs/hello-monaca/downloads/M01HelloMonaca.zip
   ```

8. **Monaca単元で `import_url` を書いてある場合**：URLの先にあるのは、オーナーのMonacaにある前のコマの形のプロジェクトである。オーナーに、新しいZIPを取り込んで公開し直してもらい、configの `import_url` と教科書の「完成プロジェクトを開く」のURLを新しいものに替える。エージェントはこれをPR本文に「未確認（オーナー作業）」として書く。

**`projects` に新しい項目を足さない。** 単元が増えないので、サイドバーの単元一覧・topbar・GitHubのラベルは変わらない。`docs/` に新しいスラッグのフォルダも作らない。最後に、この下の「検証」を同じように通す。

## この先：新しい単元を足す手順

`docs/<スラッグ>/` を作るだけでは足りない。ここに挙げたすべてに登録する。1つでも抜けると `python3 scripts/check-teaching-materials.py` が落ちる。

**完成プロジェクト（下の1）と、教材一式と登録（下の2〜9）は、別のissue・別のPRにする**（AGENTS.md §1。1つにまとめると `size:XL` になる）。登録のPRでは、既存の教科書のサイドバーも、issueの「触る範囲」に挙がっていなくても直す（登録に必要な変更のため）。

## 1. 完成プロジェクト

### Monaca系（`kind: "monaca"`）

**リポジトリで書き、ローカルのChromeで確かめ、最後にオーナーがMonacaへインポートして確かめる。** Freeプランはエクスポートできないので、Monacaで書いて書き出す経路はない（AGENTS.md §0-A）。

1. **出発点は `MonacaMinimumTemplate/` の固定原本にする。`MonacaTemplate/` は複製しない。** オーナー許可で取り込んだ公式 `monaca-templates/blank` 4.0.0（Cordova12）の出所と比較結果は `MonacaMinimumTemplate/README.md` にある。クラウド生成物との完全一致・インポートは未確認なので、原本をクラウドから書き出したものとは説明しない（AGENTS.md §4）。
   - 単元のフォルダ `M0NXxx/` に `config.xml`・`package.json`・`www/`・`res/` と、`.monaca/project_info.json`・`.gitignore`・`.monacaignore`・`LICENSE` を複製する（AGENTS.md §9）。原本のREADMEは複製せず、単元のREADMEを作る。MITの著作権表示と許諾文を消さない。
2. **改行はLFにそろえる。** `snippets` はバイト単位で照合するので、CRLFのファイルを複製すると、教科書のHTML側にもCRが要ることになる。

   ```sh
   grep -rlI $'\r' M0NXxx/                      # CRを含むファイルを挙げる（何も出なければよい）
   perl -pi -e 's/\r\n/\n/g' M0NXxx/www/index.html   # 出たファイルをLFにする
   ```

3. **`config.xml` を単元に合わせる。**
   - `<widget id="…">` は `jp.ac.jec.<単元名の小文字>`（`M01HelloMonaca` なら `jp.ac.jec.m01hellomonaca`）。configの `app_id` と同じ値にする。
   - `<name>` はアプリ名（日本語でよい）。
   - `<content src="index.html"/>` の先が、configの `entry`（`M01HelloMonaca/www/index.html`）と同じファイルになるようにする。
4. **完成コードで守ること**（AGENTS.md §11 の Monaca系）。
   - 素のHTML / CSS / JavaScript。フレームワークもビルドツールも入れない。
   - 要素の取得は `document.getElementById`、イベントは `addEventListener`、クラスの付け外しは `classList.add` / `classList.remove`。`querySelector` にしない。
   - **Web基礎で習っていないもの**（`querySelector` / `fetch` / `Promise` / `async`・`await` / `JSON` / `localStorage` / アロー関数 / `@keyframes` / CSS Grid / ES Modules / クラス構文）は、黙って使わない。Java / Android または Swift / iOS で既習の対応物があるなら、教員用ガイドに対応物を書き、比較STEPで違いと理由を教える。この場合は新概念に数えない。対応物がないものは新概念として宣言して教え、**1単元で導入する新概念は1つまで**にする。`getElementById` など、完成コードの書き方をそろえる方針はこの判定と別に守る。
   - Cordovaプラグインに依存しない。ブラウザだけで動く範囲で書く。
   - 結果は画面に出す。`console.log` で済ませない。`alert` に頼らない。
   - 命名は `txtXxx` / `btnXxx` / `imgXxx` / `listXxx`。idは `btn_start` のようなスネークケース、JavaScriptの変数は `btnStart` のようなキャメルケース。
   - Onsen UI を使うかは単元ごとに決め、使うならCDN（`unpkg.com`）で版を固定して読み込む。
   - コメントは、学生が読んで分かる日本語で、「なぜそう書いたか」を書く。
5. **ローカルのChromeで確かめる**（AGENTS.md §7 の1段目。エージェントが自分で行う）。

   ```sh
   cd M0NXxx/www && python3 -m http.server 8000   # http://localhost:8000 をChromeで開く
   ```

   `file://` で直接開かない。`cordova.js` はローカルでは404になるが、プラグインを呼んでいなければ動作に影響しない。Chromeのデベロッパーツールでスマホの幅にして、画面と操作が教科書のとおりかを見る。
6. **Monacaで確かめる**（AGENTS.md §7 の2段目。オーナーのMonacaアカウントが要る）。オーナーが、ダッシュボードの「インポート」から完成プロジェクトのZIP（下の2で作る `docs/<スラッグ>/downloads/<単元名>.zip`）を取り込み、プレビューで動かす。登録のPRより前に確かめてもらうときは、ファイルを `git add` してから、ZIPをリポジトリの外（AGENTS.md §2 のPoCの置き場）に作って渡す。

   ```sh
   python3 scripts/package-project.py --project M0NXxx --output ~/Documents/jec-25cm-hybrid-app-verification-deliverables/M0NXxx.zip
   ```

   このZIPの形（単元のフォルダで1階層包んだもの）をMonacaのインポートが受け付けるかは、最初のMonaca単元で確かめる。教科書のスクリーンショットはこのプレビューで撮る。教員のFreeプランの3枠は、完成プロジェクトの公開用に2枠、採点・一時確認用に1枠を使う。公開用の2件は残し、一時確認用のプロジェクトは確認後にオーナーが削除して枠を空ける。**エージェントが確かめられない段は「未確認」としてPR本文に書く。** 1段目を飛ばして「Monacaで動くはず」と書かない。
7. **取り込み用URL（`import_url`）を配るとき。** オーナーが完成プロジェクトを **プロジェクト → 公開…** で公開すると、`https://monaca.mobi/ja/directimport?pid=…` の形のURLが発行される。**実際に発行されたURLをそのまま**configの `import_url` に書き、教科書の「完成プロジェクトを開く」にも同じURLを載せる。`pid` の桁数を固定して書かず、IDやURLを推測で作らない。公開用の2枠にあるプロジェクトは配布中も保持する。

### Flutter系（`kind: "flutter"`）

1. **SDKは、READMEの「開発環境」に書いた版を使う**（AGENTS.md §0-B）。版が決まっていなければ、単元を作り始めずにオーナーに確認する。`flutter` がPATHにないときは、オーナーのSDKの置き場を確かめてから前置きする。
2. **`flutter create` は次の形で作る。** フォルダ名は単元名、Dartのパッケージ名は `--project-name` で別に与える（パッケージ名は小文字とアンダースコアしか使えないため）。

   ```sh
   flutter create --empty --platforms=ios,android --org jp.ac.jec --project-name f01_hello_flutter F01HelloFlutter
   ```

   - `--empty` を付ける。既定テンプレートはTRY THISコメント約60行・`StatefulWidget`・`setState`・dot shorthand が一度に出て、初回から比較して説明する項目が増える。最小の画面から始め、状態の更新は扱う単元で導入する。
   - `--platforms=ios,android` を付ける。`web/`・`macos/`・`linux/`・`windows/` は作らない（AGENTS.md §10）。
   - `pubspec.yaml` の `name`（`f01_hello_flutter`）をconfigの `package_name` に、`android/app/build.gradle.kts` の `namespace` と `applicationId`（`jp.ac.jec.f01_hello_flutter`）をconfigの `application_id` に書く。iOSの `PRODUCT_BUNDLE_IDENTIFIER` はキャメルケース（`jp.ac.jec.f01HelloFlutter`）になり、configには書かない。
3. **生成物を整える。**
   - `test/` が生成されていたら消す。カウンターアプリ用のひな形で、Unit Testは書かない（AGENTS.md §10）。`--empty` なら生成されない版もある。
   - `README.md` は生成されたものを消して、完成プロジェクトの説明に書き直す。節の順は、画面の構成の表 → 使用しているAPI（または画像・素材）→ ソースコードの構成の表 → 処理の流れ → 実装のポイント → 主なパッケージ → ビルドと実行（AGENTS.md §11 の Flutter系8）。
   - `.gitignore` は `flutter create` が生成したものをそのまま残す。**最初のFlutter単元のときだけ**、下の4で `project_layout.gitignore_reference.flutter` に、その `.gitignore` のパスを書く。
   - `*.iml`、`.dart_tool/`、`build/`、`android/local.properties` はcommitしない（`.gitignore` で無視される）。
4. **`lib/` 以外は触らない。** 触ってよいのは `pubspec.yaml`（パッケージの追加とアセットの登録）まで。全単元に共通する例外は2つ：通信を扱う単元の `android/app/src/main/AndroidManifest.xml` への `INTERNET` 追記（`src/main` に無いので、releaseのAPKだけ通信に失敗するため）と、初回ビルドを軽くするための `android/gradle/wrapper/gradle-wrapper.properties` の `-all.zip` → `-bin.zip` の書き換え（AGENTS.md §0-B）。 **これに加えて、F01・F02の配布見本では、生成時に入った作成者個人の `ios/Runner.xcodeproj/project.pbxproj` の `DEVELOPMENT_TEAM` 指定3行も除く（2026-09-24のオーナーへの確認と続行指示による例外）。** ほかの署名設定は変更せず、学生に署名作業は求めない。
5. **完成コードで守ること**（AGENTS.md §11 の Flutter系）。
   - `import 'package:flutter/material.dart'` で通す。`package:material_ui` / `package:cupertino_ui` は使わない。混ぜない。
   - 画面遷移は `Navigator.push` ＋ `MaterialPageRoute`。名前付きルート（`routes: {...}`）と `go_router` は使わない。
   - `StatelessWidget` で足りる画面を `StatefulWidget` にしない。
   - dot shorthand（`.center` など）を黙って使わない。使うなら、Swiftの implicit member expression との比較を置いて教科書で説明する。
   - 結果は画面に出す。`print` / `debugPrint` で済ませない。
   - `// ignore:` / `// ignore_for_file:` で警告を隠さない。原因そのものを消す。
   - パッケージは必要なときだけ足し、バージョンは `pubspec.yaml` で管理する。`shared_preferences` は3系統のAPIのうち1つだけを使う。
   - **1単元で導入する新概念は1つまで。** API名や構文が初出という理由だけでは数えない。Web基礎・Java / Android・Swift / iOS で既習の対応物があるものは、教員用ガイドに対応物を書き、比較STEPで違いと理由を教える。dot shorthandはSwiftのimplicit member expressionと比較し、新概念には数えない。Dartの `async` / `await` なども対応物の既習範囲を確かめ、対応物がないものだけを数える（README「単元の範囲の決め方」）。
   - コメントは日本語で書く。
6. **確かめる。**

   ```sh
   cd F01HelloFlutter && flutter pub get && flutter analyze
   ```

   `flutter analyze` が何も出さない（`No issues found!`）ことを確かめてから、Flutterプロジェクトを開いた Visual Studio Code の `Flutter: Launch Emulator` でiOSシミュレータかAndroidエミュレータを起動する。`flutter devices` で起動した端末のIDを一覧から確認し、`flutter run -d <端末ID>` で実行する。初回はiOSシミュレータのほうが軽い。Androidでビルドするときは、worktreeに `android/local.properties` が無いので環境変数で通す。

   ```sh
   cd F01HelloFlutter && ANDROID_HOME="$HOME/Library/Android/sdk" flutter build apk --debug
   ```

   教科書のスクリーンショットは、シミュレータ／エミュレータで撮る。動かせなかったときは、PR本文に「未確認」と書く。

## 2. 学生用の教科書 `docs/<スラッグ>/`

- **スラッグは、単元名から番号を取った残りを、PascalCaseの語の切れ目でハイフン区切りにした小文字**（`M01HelloMonaca` → `hello-monaca`、`F01HelloFlutter` → `hello-flutter`）。
- `docs/<スラッグ>/index.html`。HTMLの型は、`.skip` → `.topbar` → `.shell` → `.sidebar` → `main#main`、STEPは `<section id="step-N">`。CSSとJavaScriptは `../assets/textbook.css` と `../assets/textbook.js` を読む。このリポジトリに最初の教科書がまだ無いときは、同じ型で書いてある [jec-25cm-kotlin の docs/hello-kotlin/index.html](https://github.com/LeoAndo/jec-25cm-kotlin/blob/main/docs/hello-kotlin/index.html) を手本にしてよい（型だけを借りる。Kotlin・IntelliJ IDEA・Android Studio の記述は持ち込まない）。
- `<body data-progress-key="jec-hybrid-<スラッグ>-v1">` を書く（`jec-hybrid-hello-monaca-v1`）。ページごとに別の値にする。
- サイドバーの `.progress` の `max` と `data-progress-label` の総数を、STEP数に合わせる。複数コマにまたがる単元は、目次をコマごとの見出し（`<p class="eyebrow">1コマ目 · STEP 00〜06</p>`）で区切る。
- **どちらの道具を開くかを、先に書く**（README）。冒頭（`.hero` の `.tags` など）に、Monaca系は「Monaca クラウド IDE / Google Chrome」、Flutter系は「Flutter / Visual Studio Code」のように書く。Visual Studio Code は英語UIを使い、画面の項目名は `Open Folder…` などの実際の英語表記で書く。
- **本文に単元名（`M01HelloMonaca` のような `projects[].name`）の表記を必ず入れる。** `scripts/check-teaching-materials.py` がこれを探す。
- **各STEPに、既知の技術との比較を置く。** 相手は Web基礎（HTML / CSS / JavaScript）、Java / Android、Swift / iOS のどれか（複数でもよい）。比較のないSTEPは未完成とみなす。比較ブロックは次の形で、この単元で書く言語を先頭（左端）に置く。

  ```html
  <div class="compare">
  <div class="compare-item"><p class="compare-lang" translate="no">Dart</p><pre><code>…</code></pre></div>
  <div class="compare-item"><p class="compare-lang" translate="no">Java</p><pre><code>…</code></pre></div>
  <div class="compare-item"><p class="compare-lang" translate="no">Swift</p><pre><code>…</code></pre></div>
  </div>
  ```

  ラベルは言語名（`HTML`・`CSS`・`JavaScript`・`Java`・`Swift`・`Dart`）にして、`translate="no"` を付ける。「Web基礎の書き方」のように日本語を含むラベルにするときは、`translate="no"` を付けない（付けると、どの言語版でも日本語のまま出る）。
- **Web基礎で習っていないもの**（上の「Monaca系」4の一覧）は、教科書の本文と `<pre>` にも黙って出さない。既習の対応物があるなら比較STEPで違いと理由を教え、対応物がないならその単元の新概念として正面から教える。
- `docs/<スラッグ>/downloads/<単元名>.zip` を作る。単元ごとに別プロジェクトなので、ZIPも単元ごとに1つ。

  ```sh
  python3 scripts/package-project.py --project M01HelloMonaca --output docs/hello-monaca/downloads/M01HelloMonaca.zip
  python3 scripts/package-project.py --project F01HelloFlutter --output docs/hello-flutter/downloads/F01HelloFlutter.zip
  ```

  ZIPはGitで管理しているファイルから作るので、新しいファイルは先に `git add` する。
- **「完成プロジェクトを開く」（`#sample-project`）は、どちらの系統も配布フォルダ `~/Documents/hybrid-app-student-materials-日付/samples/<単元名>` をFinderで開くところから書く**（2026-09-25 先生レビュー、#135）。Monaca系は、そのフォルダでコードを読み比べ、Monaca クラウド IDEで動かすときは教員がZIPにして公開した取り込み用URL（`import_url`。実際に発行して開けることを確かめたURLだけを載せる。まだ無ければ、教員が案内すると書く）から取り込む、と書く。Flutter系は、そのフォルダを Visual Studio Code の `File > Open Folder…` で開く手順にし、ZIPのダウンロードリンクは置かない。
- `docs/<スラッグ>/images/` は、**その教科書で実際に使うスクリーンショットがあるときだけ**作る。Monaca系はMonaca クラウド IDEのプレビュー、Flutter系はシミュレータ／エミュレータで撮る。「ここに画像を入れる」のようなプレースホルダは置かない。`<img>` には実寸の `width` と `height` を書く。
- コードのスニペットは、`<pre id="code-…"><code>` に置き、**ソースからHTMLエスケープして差し込む**。configの `snippets` がバイト単位で照合するので、手で写して直さない。

  ```sh
  python3 -c 'import html, pathlib, sys; print(html.escape(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").rstrip()), end="")' M01HelloMonaca/www/js/app.js
  ```

- 教科書の中から**ほかの単元へ本文で送らない**。**Monaca系で作ったものを、Flutter系の前提にしない。** 共通資料へのリンクはサイドバーと明示の導線だけ。
- **単元の最後は「アレンジできる場所」で終える。** どこを変えると画面や動きの何が変わるかを、その単元のコードの中で示す（文字・色・数値・件数など）。新しい概念やAPIはここで足さない。
- **多言語展開の制約を守る**（`python3 scripts/localize-student-materials.py check` が行番号つきで落とす）。
  - 開始タグと終了タグを必ず対応させる。`<span/>` のような自己終了タグを書かない。
  - 属性値は必ず引用符で囲む（`<html lang="ja">`）。
  - 文の途中にHTMLコメントを書かない。段落の外に書く。
  - `/` で始まるルート相対リンクを使わない（`href="../assets/textbook.css"` と書く）。
  - 文の途中の要素に `translate="no"` を付けない。訳してほしくない文字（Monaca クラウド IDEやVisual Studio Codeのメニュー名、Flutterのウィジェット名、パッケージ名）は `<code>` で囲む。
- 1,000行を超える教科書HTMLは、章ごとに分けて書いてから結合する（1回で書こうとするとツール呼び出しが長くなりすぎて止まる）。

## 3. 教員用ガイド `teacher/<スラッグ>/`

- `teacher/<スラッグ>/index.html`。最初の単元のときは、[jec-25cm-kotlin の teacher/hello-kotlin/index.html](https://github.com/LeoAndo/jec-25cm-kotlin/blob/main/teacher/hello-kotlin/index.html) の型を借りてよい。
- **「この単元の教材方針」の節を必ず置く。** 何を意図的に外したかを、理由つきで書く。
  - その単元で導入する新概念（1つまで）を、ここで宣言する。Web基礎で習っていないもの（`querySelector`、`fetch`、`@keyframes` など）を使うときは、既習の対応物と比較STEP、または対応物がないため新概念に数える理由を書く。レビューの「未習事項ゲート」は、この対応付けと本文の説明を見て判断する。
  - Flutter系は、`package:material_ui` を使わない理由、`go_router` と名前付きルートを使わない理由を書く（AGENTS.md §0-B・§11）。`shared_preferences` を使う単元は、APIが3系統あることと、どれを選んだかを書く。
- 進め方には、コマごとにどのSTEPを扱うかを書く。
- `teacher/<スラッグ>/code/` に、STEPごとの照合コードを `NN-ファイル名.拡張子` の形式で置く（`01-index.html`、`03-app.js`、`02-main.dart` など）。完成プロジェクトと同じ中身のものは `mirrors` に登録する。
- 本文に単元名の表記を入れる（`check-teaching-materials.py` は `docs` に挙げた両方のHTMLを見る）。

## 4. `config/teaching-materials.json`

`projects` に足す項目は、Monaca単元なら次の形になる（`M01HelloMonaca` を足す場合）。

```json
{
  "name": "M01HelloMonaca",
  "kind": "monaca",
  "root": "M01HelloMonaca",
  "app_id": "jp.ac.jec.m01hellomonaca",
  "entry": "M01HelloMonaca/www/index.html",
  "sessions": 2,
  "docs": ["docs/hello-monaca/index.html", "teacher/hello-monaca/index.html"],
  "sources": ["M01HelloMonaca/www/index.html", "M01HelloMonaca/www/js/app.js"],
  "snippets": [
    { "html": "docs/hello-monaca/index.html", "id": "code-app-js", "source": "M01HelloMonaca/www/js/app.js" }
  ],
  "mirrors": [
    { "source": "M01HelloMonaca/www/index.html", "copy": "teacher/hello-monaca/code/01-index.html" }
  ],
  "archive": "docs/hello-monaca/downloads/M01HelloMonaca.zip"
}
```

- `app_id` は `config.xml` の `<widget id>` と同じ値（検査が照合する）。`entry` は `<content src>` が指すファイルのリポジトリ上のパスで、`www/` の下に実在する必要がある。
- `sources` は1つ以上。Monaca系は `www/` の下、Flutter系の `.dart` は `lib/` の下に置く。CRを含むと検査が落ちる。
- `import_url` は任意。オーナーがMonacaで公開したら書き、まだなら**キーごと省く**（上の「Monaca系」7）。書いたら、教科書（`docs` の1つ目）に同じURLが無いと検査が落ちる。**URLを推測で書かない。**
- `mirrors` は任意。

Flutter単元なら次の形になる（`F01HelloFlutter` を足す場合）。

```json
{
  "name": "F01HelloFlutter",
  "kind": "flutter",
  "root": "F01HelloFlutter",
  "package_name": "f01_hello_flutter",
  "application_id": "jp.ac.jec.f01_hello_flutter",
  "entry": "F01HelloFlutter/lib/main.dart",
  "sessions": 2,
  "docs": ["docs/hello-flutter/index.html", "teacher/hello-flutter/index.html"],
  "sources": ["F01HelloFlutter/lib/main.dart"],
  "snippets": [
    { "html": "docs/hello-flutter/index.html", "id": "code-main-dart", "source": "F01HelloFlutter/lib/main.dart" }
  ],
  "archive": "docs/hello-flutter/downloads/F01HelloFlutter.zip"
}
```

- `package_name` は `pubspec.yaml` の `name`、`application_id` は `android/app/build.gradle.kts` の `namespace` と `applicationId`。
- **Monaca系は `app_id`、Flutter系は `package_name` と `application_id`。** 取り違えると設定エラーになる。

直すのは次の5か所。

1. `scan_roots`：既存の `scan_roots` の下に入らないディレクトリを足す。単元のプロジェクトのディレクトリ（`M01HelloMonaca`、`F01HelloFlutter`）は必ず足す。`teacher` がまだ挙がっていなければ、最初の教員用ガイドを置くときに足す。
2. `terms[].required_in`：その単元の教科書・教員用ガイドで正式表記を使うなら足す。用語に `applies_to` が書いてあると、その系統の単元にだけ表記が求められるので、該当する系統の単元を足したときは、その教科書と教員用ガイドを `required_in` に足す。
3. `project_layout.gitignore_reference`：値が `null` の系統は、プロジェクト直下の `.gitignore` を照合しない。**最初のFlutter単元を足したときに**、`"flutter"` を `flutter create` が生成した `.gitignore` のパス（`"F01HelloFlutter/.gitignore"`）に替える。Monaca系は `null` のまま。
4. `projects`：**単元番号順の位置に足す。** 並び順は「最初に現れた接頭辞の順（M → F）」で、同じ接頭辞の中は番号の昇順。**一度Fに変わったあとでMに戻すとエラー**になる。Monaca単元はFlutter単元より前に、番号順に足す。サイドバーの検査がこの並びを基準にする。
5. `sessions`：正の整数。**`projects` の `sessions` の合計が `course.total_sessions`（15）を超えるとエラー**になる。15コマ計画表の割り当てと合わせる。

## 5. `README.md`

次のすべてに足す。`config/teaching-materials.json` の `registration` が、READMEに `docs[0]`（教科書）・`docs[1]`（教員用ガイド）・`archive` の3つのパスが出てくることを確かめる。

- 教科書一覧のリンク（`docs/<スラッグ>/index.html`）
- 完成プロジェクトのリンク（`archive` のパス）
- 教員用ガイドのリンク（`teacher/<スラッグ>/index.html`）
- 15コマ計画表の行（コマ・単元・内容・プロジェクト）
- フォルダ表（プロジェクトを新しく作ったとき）

## 6. サイドバーとtopbar（**既存の全教科書を直す**）

サイドバーの `<div class="resources">` に並ぶ単元は、**configの `projects` の順・リンク先・表示名まで**照合される。1冊でも直し忘れると検査が落ちる。

- 表示名は `<番号>：<ラベル>`。単元名から先頭の番号を切り離し、全角コロンでつなぐ（`M01HelloMonaca` → **`M01：HelloMonaca`**、`F01HelloFlutter` → **`F01：HelloFlutter`**。`M01：M01HelloMonaca` にしない）。
- ほかの単元は `<a href="../<スラッグ>/index.html">`、**自単元は `<span aria-current="page">`**。
- 単元の項目は、**文字だけの `<a>` か `<span>`**。中に `<strong>` などの別タグを入れない。
- 位置は「完成プロジェクトを開く」のあと、共通資料の前。「困ったとき」「完成プロジェクトを開く」と共通資料へのリンクは、単元として数えない。共通資料へのリンクには `?from=<自分のスラッグ>` を付ける。
- 複数コマにまたがる単元にコマを足しても、単元の項目は増えない。

**既存の M01 の教科書（`docs/hello-monaca/index.html`）に F01 を足す**

```html
<div class="resources"><a href="#help">困ったとき</a><a href="#sample-project">完成プロジェクトを開く</a><span aria-current="page">M01：HelloMonaca</span><a href="../hello-flutter/index.html">F01：HelloFlutter</a><a href="../common/setup.html?from=hello-monaca">共通：はじめの準備</a></div>
```

**新しい F01 の教科書（`docs/hello-flutter/index.html`）には、全単元を並べる**

```html
<div class="resources"><a href="#help">困ったとき</a><a href="#sample-project">完成プロジェクトを開く</a><a href="../hello-monaca/index.html">M01：HelloMonaca</a><span aria-current="page">F01：HelloFlutter</span><a href="../common/setup.html?from=hello-flutter">共通：はじめの準備</a></div>
```

共通資料は、`docs/common/` にあるページだけを並べる（上の例は `setup.html` だけの場合）。

**topbar は、直前の単元へのリンク1つ**（最初の単元はリンクなし）。ブランドは `JEC / ハイブリッドアプリ開発技法` にそろえる。F01の直前がM01なら、次のようになる。

```html
<header class="topbar"><span class="brand">JEC / ハイブリッドアプリ開発技法</span><a href="../hello-monaca/index.html"><span class="back-arrow" aria-hidden="true">←</span> M01：HelloMonaca</a></header>
```

**矢印の `←` は `<span class="back-arrow" aria-hidden="true">` で囲む。** `←` は右から左の文の中でも向きが変わらないので、アラビア語のページ（`<html dir="rtl">`）では「進む」向きに見える。`docs/assets/textbook.css` が、右から左のページでだけこの `span` を左右反転する。日本語のページの見た目は変わらない。`aria-hidden` は、読み上げで「左向き矢印」と読ませないため。

topbarは導線であって、本文で前の単元へ送ることではない。**Flutter系の最初の単元のtopbarがMonaca系の単元を指していても、本文でMonacaの作品を前提にしてはいけない。** 単元を途中に挿入したときは、**次の単元のtopbar**も新しい単元へ付け替える。topbarは検査されないので、目で確かめる。

## 7. GitHubのラベル

`area:M<NN>` / `area:F<NN>`（`area:M01`、`area:F01`）をラベルに追加し、issueとPRに付ける。複数コマにまたがる単元のコマを足すissueは、単元が増えないので、その単元のラベルをそのまま使う。

## 8. 翻訳

**日常のPRでは翻訳しない。** 新単元のPRでは日本語だけを足し、文を取り出せることを確かめる。

```sh
python3 scripts/localize-student-materials.py check
```

翻訳は、配布準備の翻訳PRでまとめて行う（`skills/translate-teaching-materials/SKILL.md`）。各言語のHTMLはコミットしない。

## 9. 提出課題の共通資料

提出課題は「学生自身が作ったアプリを選んでアレンジして出す」形で、Monaca系は公開URL、Flutter系はビルド成果物を出す（README「提出課題」）。単元が増えると、学生が選べるアプリの本数と顔ぶれが変わる。`docs/common/` に単元名や本数を挙げている箇所があれば、この登録のPRで一緒に直す（`docs/common/` は共有ファイル。AGENTS.md §4）。

## 配布スクリプトへの追記は不要

**`scripts/package-student-materials.py` と `scripts/release-student-materials.py` は直さない。**
どちらも `config/teaching-materials.json` の `projects` から単元一覧を読むので、上の「4」でconfigに足した時点（コマを足したときは `sessions`・`sources` を直した時点）で、次のすべてが自動で追従する。

- 完成プロジェクトZIPの再生成
- 「完成プロジェクトが見つかりません」の検査
- `はじめに.txt` の単元一覧
- リリースノートの単元一覧

**配布スクリプトに単元名や単元番号を直書きしない。** もし直書きを足したくなったら、それはconfigの読み込み漏れなので、スクリプト側の不具合として扱う。

## 検証

最後に、次の4つをすべて通す。**コマを足しただけのときも、この4つは同じように通す。** Python 3.11以上が要る（`python3 -V`）。4つ目は `git ls-files` で配布物を選ぶので、新しいファイルは先に `git add` しておく。

```sh
python3 scripts/check-teaching-materials.py
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/localize-student-materials.py check
python3 scripts/package-student-materials.py
```

系統ごとの確かめ方は、上の「1. 完成プロジェクト」のとおり。

- **Monaca単元**：`python3 -m http.server` とChromeで画面と操作を確かめる（エージェントが行う）。Monacaへのインポートとプレビューは、PR本文に「未確認（オーナー作業）」と書く。
- **Flutter単元**：`flutter analyze` が何も出さないことと、iOSシミュレータかAndroidエミュレータで動くことを確かめる。

`package-student-materials.py` が作った配布ZIPを展開し、入口から教科書・完成プロジェクト・共通資料へのリンクがたどれることも確かめる。commitする前に `git diff --cached --name-only` を見て、系統ごとの所定の位置にある生成物やローカル設定が紛れ込んでいないことを確かめる（AGENTS.md §5）。除外は `scripts/project_files.py` の系統（`kind`）とプロジェクトからの相対パスに従う。Monacaなら直下の `node_modules/`・`platforms/`・`plugins/`、Flutterなら直下の `.dart_tool/`・`build/` や `android/local.properties` などが対象で、`lib/build/`・`lib/plugins/`・`www/plugins/` のような同名のソース用フォルダまで除外しない。`.DS_Store` など両系統のローカルファイルも含めない。
