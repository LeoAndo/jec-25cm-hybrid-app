---
name: teaching-materials-review
description: Review teaching materials of this hybrid app course (Monaca units in plain HTML/CSS/JS and Flutter units in Dart) against the completed project sources, code snippets, canonical terminology, the gate for features the students have not learned in their Web basics course, and the student distribution archives; when explicitly requested, summarize the result in a PR comment. Use for PRs that change docs, teacher guides, completed projects, packaging, or release workflows in this repository.
---

# Teaching materials review

このリポジトリ（ハイブリッドアプリ開発技法・1コマ90分 × 全15コマ）の教材変更をレビューするときは、文章だけでなく、教材・完成プロジェクト・配布ZIPの整合性を確認する。判断の前提は `AGENTS.md`（とくに「受講生像と、教材の書き方」・§0-A・§0-B・§10・§11）と `README.md` の方針にある。

単元には**2系統**ある。どちらの系統かで、確かめることが変わる。

| 系統 | `config/teaching-materials.json` の `kind` | 完成プロジェクト | 動かし方 |
| --- | --- | --- | --- |
| Monaca（`M01`〜） | `monaca` | `M01HelloMonaca/`（`config.xml`・`package.json`・`www/`・`res/`） | `www/` を静的サーバで開いてChromeで確かめ、Monaca クラウド IDEへインポートしてプレビュー |
| Flutter（`F01`〜） | `flutter` | `F01HelloFlutter/`（`flutter create --empty --platforms=ios,android` で作ったもの） | `flutter analyze`、iOSシミュレータ／Androidエミュレータ |

## 必須確認

1. 次の4つを実行する（Python 3.11以上）。

   ```sh
   python3 scripts/check-teaching-materials.py
   python3 -m unittest discover -s scripts -p 'test_*.py'
   python3 scripts/localize-student-materials.py check
   python3 scripts/package-student-materials.py
   ```

2. 検査が失敗した場合は、PRを承認可能と判断しない。
3. `config/teaching-materials.json` の `terms` の正式表記を基準にし、禁止表記を個別に修正する。
4. 教材の完成コードとプロジェクトの実ファイルが一致することを確認する。`snippets` はバイト単位で照合されるので、教科書のコードを手で写して直していないかを見る。
5. ZIPの内容が現行ソースと一致し、IDE設定・SDK設定・ビルド生成物を含まないことを確認する。除外は `scripts/project_files.py` の系統（`kind`）とプロジェクトからの相対パスに従う。Monacaは直下の `node_modules/`・`platforms/`・`plugins/`、Flutterは直下の `.dart_tool/`・`build/`、`android/.gradle/`・`android/app/build/`・`android/local.properties`・`ios/Pods/` など、所定の位置にあるものを除外する。名前だけで `lib/build/`・`lib/plugins/`・`www/plugins/` のようなソース用フォルダを落としていたら「対応が必要」とする。`.idea`・`.DS_Store` など両系統のローカル設定も含めない。`project_layout` の `untracked_parts` と `untracked_names` は共通のローカル設定の検査用である。
6. 下の「未習事項ゲート」を行う。
7. PRレビュー指摘には、妥当性・再現性・デグレの可能性・修正コスト・既存仕様への影響を確認したうえで、対応が必要、任意対応、対応不要のいずれかを明記する。

## 未習事項ゲート

**受講生は Web基礎（HTML / CSS / JavaScript、全14章）を履修しているが、次のものはその授業では習っていない**（AGENTS.md「受講生像と、教材の書き方」）。ただし、Java / Android または Swift / iOS で既習の対応物があるものは、比較STEPで違いと理由を教えれば新概念には数えない。このゲートは、対応物の有無と必要な説明の抜けを確認するもので、一覧にあるAPIを自動的に新概念へ数えるものではない。

`querySelector` / `fetch` / `Promise` / `async`・`await` / `JSON` / `localStorage` / アロー関数 / `@keyframes` / CSS Grid / ES Modules / クラス構文

**対象**は、学生が読んで書き写すHTML / CSS / JavaScript のコード。

- Monaca単元の完成プロジェクトの `www/` の下（`M0NXxx/www/**/*.html`・`*.css`・`*.js`）
- 教員用ガイドの照合コード（`teacher/<スラッグ>/code/` の `.html`・`.css`・`.js`）
- 教科書（`docs/**/*.html`）の `<pre>`。ただし、比較ブロックで言語名が Java・Swift・Dart のもの（`<p class="compare-lang">` のラベル）と、Flutter単元の教科書の比較ブロック以外の `<pre>`（Dartのコード）は除く。Dartの `class` や `=>`、Swift の `async` はそれぞれの言語の書き方で、このゲートの対象ではない。Dart側の新概念は、下の「完成コードの判断基準」15で見る。

**対象外**は、Monacaテンプレート由来のファイル（`www/components/` の `loader.js`・`loader.css`、`monaca-cordova-loader`、`monaca-core-utils` など）、CDNから読み込むライブラリ（Onsen UI など）、教科書自身のUI（`docs/assets/textbook.css`・`textbook.js`。これは学生が書くコードではない）、`MonacaTemplate/`。

リポジトリの直下で次を実行し、出てきた行を1つずつ見る。

```sh
python3 - <<'PY'
import glob, json, re
from html.parser import HTMLParser
from pathlib import Path

RULES = {
    "querySelector": r"\bquerySelector(All)?\b",
    "fetch": r"\bfetch\s*\(",
    "Promise": r"\bPromise\b|\.then\s*\(",
    "async / await": r"\basync\s+(function\b|\(|[A-Za-z_$][\w$]*\s*=>)|\bawait\s",
    "JSON": r"\bJSON\s*\.",
    "localStorage": r"\b(localStorage|sessionStorage)\b",
    "アロー関数": r"=>",
    "@keyframes": r"@keyframes|\banimation(-name)?\s*:",
    "CSS Grid": r"display\s*:\s*(inline-)?grid\b|\bgrid-(template|area|column|row)",
    "ES Modules": r"type\s*=\s*[\"']module|^\s*(import|export)\b",
    "クラス構文": r"(^|[\s;{}(=])class\s+[A-Za-z_$][\w$]*\s*(extends\b|\{)",
}
NOT_WEB = {"Java", "Swift", "Dart", "Kotlin"}

def report(path, first_line, text):
    for offset, line in enumerate(text.splitlines()):
        for name, pattern in RULES.items():
            if re.search(pattern, line):
                print(f"{path}:{first_line + offset}: {name}: {line.strip()}")

class Pres(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found, self.label, self.in_label, self.pre = [], None, False, None
    def handle_starttag(self, tag, attrs):
        if tag == "p" and "compare-lang" in (dict(attrs).get("class") or "").split():
            self.in_label, self.label = True, ""
        elif tag == "pre":
            self.pre = [self.getpos()[0], ""]
    def handle_data(self, data):
        if self.in_label:
            self.label += data
        if self.pre is not None:
            self.pre[1] += data
    def handle_endtag(self, tag):
        if tag == "p":
            self.in_label = False
        elif tag == "pre" and self.pre is not None:
            self.found.append((self.pre[0], (self.label or "").strip(), self.pre[1]))
            self.pre, self.label = None, None

config = json.loads(Path("config/teaching-materials.json").read_text(encoding="utf-8"))
flutter_docs = {doc for p in config["projects"] if p.get("kind") == "flutter" for doc in p["docs"]}
for path in sorted(glob.glob("M[0-9][0-9]*/www/**/*.*", recursive=True) + glob.glob("teacher/*/code/*.*")):
    if "/components/" not in path and path.endswith((".html", ".css", ".js")):
        report(path, 1, Path(path).read_text(encoding="utf-8"))
for path in sorted(glob.glob("docs/**/*.html", recursive=True)):
    parser = Pres()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    for line, label, text in parser.found:
        if label not in NOT_WEB and (label or path not in flutter_docs):
            report(path, line, text)
PY
```

これは候補を挙げるだけで、判定はしない（`<script async>` の属性や、コメントの中の語も拾う）。出てきた1つ1つについて、次の順に判断する。

1. **その単元の教員用ガイド**（`teacher/<スラッグ>/index.html`）の「この単元の教材方針」に、Web基礎・Java / Android・Swift / iOS で既習の対応物が書いてあり、教科書の比較STEPで違いと理由を教えているか。両方あれば新概念には数えない。API名や構文が初出という理由だけで新概念と判定しない。
2. 対応物がないものは、その単元の新概念として宣言され、教科書のSTEPで正面から教えているかを見る。**1単元で導入する新概念は1つまで**にする。`projects` の並びで前にある**同じ系統の単元**で既に教えた概念は重ねて数えない。ただし、本文をほかの単元へ送らず、今回必要な手順とコードは今回の教科書にも置く。Monacaの作品や手順をFlutterの前提にはしない。
3. 上の1または2を満たす説明がなければ「**対応が必要**」とする。Web基礎で習った書き方に戻すか、既習の対応物との比較STEPを足すか、対応物のない新概念として教える。2つ目の新概念になる場合は、単元を分けるか片方を外す。`getElementById` など完成コードの書き方をそろえる方針は、概念の数え方と別に守る。
4. `fetch`・`Promise`（または `async`・`await`）・`JSON` を使うときは、それぞれについて既習の対応物と比較STEPを確かめる。対応物のない独立した概念が複数残る場合は、まとめて「通信」という1つの名前にして数を減らさず、扱う範囲を分ける。

## 系統ごとに確かめること

**Monaca単元（`kind: "monaca"`）**

- 出発点が通常版の「最小限のテンプレート」であること。`www/classic.js` があったり、`.monaca/project_info.json` が `cordova_version: 11.0` だったりするのは、旧 Monaca Education の「クラシック」テンプレート（`MonacaTemplate/`）を複製した形で、「対応が必要」とする（AGENTS.md §4）。
- `config.xml` の `<widget id>` が configの `app_id`（`jp.ac.jec.<単元名の小文字>`）と一致し、`<content src>` の先が `entry` のファイルであること。
- 完成コードの改行がLFだけであること（`grep -rlI $'\r' M0NXxx/` が何も出さない）。
- Cordovaプラグインに依存していないこと。テンプレートにない `<plugin>` が `config.xml` に、プラグインが `package.json` に足されていたら指摘する。
- ローカルの静的サーバとChromeで、画面と操作が教科書のとおりであること。

  ```sh
  cd M01HelloMonaca/www && python3 -m http.server 8000   # http://localhost:8000 をChromeで開く
  ```

  `cordova.js` の404は、プラグインを呼んでいなければ問題ない。
- Monacaへのインポートとプレビューでの確認は、オーナーのアカウントが要る。レビュワーが確かめられない場合は「未確認項目」として総括コメントに残す。推測で「Monacaで動いた」と書かない。
- `import_url` があれば、Monacaで実際に発行された `https://monaca.mobi/ja/directimport?pid=…` のURLと一致し、教科書の「完成プロジェクトを開く」にも同じURLがあること。`pid` の桁数を固定して判定せず、推測のIDやプレースホルダを使わない。URLの先が生きているかは、開いて確かめられなければ「未確認項目」にする。
- 学生向けの教材に、Monaca Education 前提の手順（「Web公開」での提出、「クラシック」テンプレート、App Store の `Monaca for Study`、`edu.monaca.io`）が入っていたら「対応が必要」とする（AGENTS.md §0-A）。教員用ガイドで前年度との違いとして挙げるのは問題ない。

**Flutter単元（`kind: "flutter"`）**

- `flutter analyze` が何も出さないこと。

  ```sh
  cd F01HelloFlutter && flutter pub get && flutter analyze
  ```

- `pubspec.yaml` の `name` が `package_name` と、`android/app/build.gradle.kts` の `namespace` と `applicationId` が `application_id` と一致すること。
- プラットフォームのディレクトリが `ios/` と `android/` だけで、`web/`・`macos/`・`linux/`・`windows/` が無いこと。`test/` が無いこと。
- `lib/` と `pubspec.yaml` の外を変えていないこと。例外は、通信を扱う単元の `android/app/src/main/AndroidManifest.xml` への `INTERNET` 追記と、`gradle-wrapper.properties` の `-bin.zip` 書き換えの2つだけ（AGENTS.md §11）。通信を扱う単元で `INTERNET` の追記STEPが教科書に無ければ、releaseのAPKで通信が失敗するので「対応が必要」とする。
- 画面の確認は、iOSシミュレータかAndroidエミュレータで行う。READMEの「開発環境」に書いた基準のFlutter SDKと違う版で撮ったスクリーンショットは指摘する。レビュワーが動かせない場合は「未確認項目」として残す。
- 教科書にXcodeのアプリ名（`Simulator`・`DeviceHub`）での起動手順が書かれていたら指摘する。シミュレータは Visual Studio Code のデバイス選択（または `flutter devices`）から起動させる（AGENTS.md §0-B）。Visual Studio Code は英語UIを使い、操作名が `Open Folder…` など実際の表示に合っていることを確認する。
- 完成プロジェクトの `README.md` が、画面の構成の表 → 使用しているAPI（または画像・素材）→ ソースコードの構成の表 → 処理の流れ → 実装のポイント → 主なパッケージ → ビルドと実行、の順になっていること。

## 完成コードの判断基準

完成プロジェクトのコードは、AGENTS.md §11 を基準に読む。ここから外れていれば指摘し、ここに沿っていれば「読みやすく書き直すべき」という指摘は採用しない。

**Monaca系**

1. **素のHTML / CSS / JavaScript。** フレームワーク（Vue・React など）もビルドツールも入れない。入っていたら「対応が必要」とする。
2. **要素の取得は `document.getElementById`、イベントは `addEventListener`、クラスの付け外しは `classList.add` / `classList.remove`。** `querySelector` への書き換えを求める指摘は採用しない。
3. **Cordovaプラグインに依存しない。** `www/` を静的サーバで開くだけで全部確かめられる状態を保つ。
4. **結果は画面に出す。** `console.log` だけで済ませていたら「対応が必要」とする。`alert` に頼っていても同じ。
5. **命名は `txtXxx` / `btnXxx` / `imgXxx` / `listXxx`。** idは `btn_start` のようなスネークケース、JavaScriptの変数は `btnStart` のようなキャメルケース。
6. **`config.xml` の `<widget id>` は `jp.ac.jec.<単元名の小文字>`。**

**Flutter系**

7. **`import 'package:flutter/material.dart'` で通す。** `package:material_ui` / `package:cupertino_ui` が混ざっていたら「対応が必要」とする（学生のimportが壊れる）。移行を勧める指摘は「対応不要」とする。
8. **画面遷移は `Navigator.push` ＋ `MaterialPageRoute`。** 名前付きルート（`routes: {...}`）と `go_router` は採らない。
9. **`StatelessWidget` で足りる画面を `StatefulWidget` にしない。**
10. **結果は画面に出す。** `print` / `debugPrint` だけで済ませていたら「対応が必要」とする。
11. **`// ignore:` / `// ignore_for_file:` で警告を隠さない。** 足されていたら「対応が必要」とする。
12. **パッケージは必要なときだけ足し、バージョンは `pubspec.yaml` で管理する。** `shared_preferences` のAPIが教材の中で混在していたら指摘する。
13. **dot shorthand（`.center` など）を黙って使わない。** 使うなら、教科書にSwiftの implicit member expression との比較があるかを見る。

**両系統に共通**

14. **コメントは、学生が読んで意味が分かる日本語で書く。** 英語のコメントは指摘する。
15. **1単元で導入する新概念は1つまで。** 「新概念」は、Web基礎にもJava / AndroidにもSwift / iOSにも既習の対応物がないもの（README「単元の範囲の決め方」）。対応物があるものは比較STEPで教え、新概念には数えない。Monaca系は上の「未習事項ゲート」で、Flutter系もDartの `async` / `await` やWidgetツリーによる宣言的UIなどについて対応物と説明を確認する。dot shorthandはSwiftのimplicit member expressionと比較し、新概念には数えない。画面（Monacaはプレビュー、Flutterはシミュレータ／エミュレータ）で効果が見える形になっているかも見る。2つ目の新概念が混ざっていたら、別issueへ分ける指摘にする。
16. **完成プロジェクトにUnit Testは書かない。** テストの追加や、そのための構造変更を求める指摘は「対応不要」とする。`scripts/test_*.py` はCIで動くので、通る状態を保つ。
17. **オーナーの書き方を保つ。** 「初学者向けに書き直すべき」という指摘の既定の対応は「教科書で説明する」。採用するのは、動作を変えない小さな明確化だけにする。

## 教科書の判断基準

- **各STEPに、既知の技術（Web基礎・Java/Android・Swift/iOS）との比較があること。** 比較のないSTEPは未完成として指摘する。概念そのもの（変数・DOM・画面遷移とは何か）の説明を足す指摘は採用しない。
- **本文でほかの単元へ手順やコードを送っていないこと。** とくに、Monaca系で作ったものをFlutter系の前提にしていたら「対応が必要」とする。サイドバーとtopbarのリンクは導線なので対象外。
- **どちらの道具（Monaca クラウド IDE／Visual Studio Code）を開くかが、先に書いてあること。**
- **単元（コマ）の最後に「アレンジできる場所」があること。** そこで新しい概念やAPIを足していたら指摘する。
- 多言語展開の制約（開始タグと終了タグの対応、引用符のない属性、文の途中のコメント・`translate="no"`、ルート相対リンク）は `localize-student-materials.py check` が落とす。比較ブロックの言語名ラベルに `translate="no"` が付いているかも見る。

## PRコメントの扱い

- PR番号またはURLがレビュー対象として明示され、ユーザーがPRへの投稿を依頼した場合に限り、レビュー結果をGitHubへ投稿する。単に「レビューして」と依頼された場合は、結果をこの会話で報告し、外部へ投稿しない。
- 投稿する場合は、個別コメントを大量に作らず、原則として1件の総括コメントにまとめる。行固有の修正が必要な指摘だけは、総括コメントから該当ファイル・行へリンクする。
- 総括コメントには、対象PR、レビュー対象コミット、必須検査と関連テストの結果、未習事項ゲートの結果、指摘一覧、未確認項目、マージ可否を含める。各指摘には「対応が必要」「任意対応」「対応不要」のいずれかを付ける。
- 対応が必要な指摘がある場合は「マージ不可」、任意対応だけまたは指摘がない場合は「マージ可」、検査を完了できない場合は「判断保留」と明記する。検査不能の理由と未確認項目も記載する。
- 同じPRへ再レビュー結果を投稿する場合は、`<!-- teaching-materials-review-summary -->` マーカー付きの既存総括コメントを更新し、重複投稿しない。既存コメントがなければこのマーカーを付けて新規投稿する。
- 総括コメントの投稿は、承認・変更要求・マージ・ラベル変更を意味しない。これらは別途明示的に依頼された場合のみ行う。
- コメントは日本語で書く。実在しないissue番号・PR番号・URLを書かない。

## 判断基準

- 正式表記や配布物の不一致は、学生配布前に直す必要がある指摘として扱う。
- 初学者向けのコード構成を変えるだけの改善は、教材の学習目標と変更範囲を比較して判断する（上の「完成コードの判断基準」17）。
- 自動レビューの指摘はそのまま実行せず、必ず現在のソースと検査結果で再確認する。チェックが `SUCCESS` でも、そのbotがレビューしたとは限らない（AGENTS.md §8）。
- マージ可否は、次の優先順位で判定する。①必須検査を実行して失敗した場合は「マージ不可」とし、必須検査の失敗を「マージ可」と判定しない。②必須検査を実行できない、または完了できない場合は「判断保留」とする。③必須検査が成功していても対応が必要なレビュー指摘（未習事項ゲートで「対応が必要」としたものを含む）があれば「マージ不可」とする。④必須検査が成功し、対応が必要な指摘がなく、任意対応のみまたは指摘がない場合に限り「マージ可」とする。関連テストの結果も総括コメントに記載する。
- 「承認可能」と「マージ可」は別の概念として扱う。必須確認2により、必須検査に失敗したPRを承認可能と判断してはならず、レビュー上も「マージ可」としてはならない。マージ操作自体はユーザーの依頼がない限り実行しない。

## 対象外（指摘しない）

次の項目は指摘しない。botに指摘されたら「対応不要」と返信する。検証もしない（AGENTS.md §10）。

- 完成プロジェクトのUnit Test。テストしやすくするためのリファクタリングも含む。Flutterの `test/` のひな形を残す提案も含む。
- Windows。教員も学生もmacOSで、CIはubuntu。
- ダークテーマ。確認は既定のライトテーマだけで行う。直書きの色もそのままにする。
- タブレット・フォルダブル対応、画面回転と横画面。
- Flutterの iOS・Android 以外のプラットフォーム（Web・macOS・Linux・Windows）。
- 提出物の署名とストア公開。Monaca FreeプランではリリースビルドができずFlutterはデバッグ鍵で署名されるので、「署名されていない」「ストアに出せない」は仕様どおり。
- Monaca Education の機能（Web公開、共同編集、データベース、コース機能）を前提にした指摘。
- 教科書自身のUI（`docs/assets/textbook.css`・`textbook.js`）が `querySelector`・アロー関数・CSS Grid を使っていること。学生が書くコードではないので、未習事項ゲートの対象ではない。
