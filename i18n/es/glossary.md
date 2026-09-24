# 用語集：Español（es）

ハイブリッドアプリ開発技法の対訳表。訳すときは、この表の訳語を使う。新しく訳語を決めた用語は、行を足す。全言語に共通の翻訳ルールは `skills/translate-teaching-materials/SKILL.md` にある。メモに「要確認」とある行は、訳語に自信がないもの。翻訳PRで確かめたら「要確認」を消す。

**中南米のスペイン語にそろえる（2026-09-24 オーナー決定）。** 言語コードは `es` のままにし、言葉選びで中南米に合わせる。スペインの言い方（ordenador、fichero、vosotros など）は使わない（下の「書き方の決まり」）。

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

同じ学生が Kotlin演習（jec-25cm-kotlin）も受けている。この表の訳語と、下の「書き方の決まり」は、jec-25cm-kotlin の `i18n/es/glossary.md` と同じにしてある（2026-09-25、[jec-25cm-kotlin PR #85](https://github.com/LeoAndo/jec-25cm-kotlin/pull/85)。冠詞の例に挙げる語だけは、それぞれの授業に出る語にしてある）。あちらでは、下の「この授業の用語」のうちアプリ・ビルド・デバッグ・実機・デバイス・テンプレート・プレビュー・コマも、両科目に共通の用語として同じ訳語にしてある。これらの訳語を変えるときは、あちらも同じように直す。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| プロジェクト | proyecto | |
| パッケージ | paquete | `f01_hello_flutter`・`package:flutter/material.dart` などのパッケージ名は訳さない |
| 関数 | función | `function`（JavaScript）・`void main()`（Dart）の表記は原文のまま |
| 変数 | variable | `let` / `const`（JavaScript）・`var` / `final`（Dart）の表記は原文のまま |
| 実行 | ejecutar | 名詞は ejecución。Monacaのメニュー名 **実行** は日本語のまま残し (Ejecutar) を添える。Visual Studio Code のボタン名は **Run** のまま |
| コンソール | consola | Chromeのデベロッパーツールの Console、Visual Studio Code の **Debug Console** は原文のまま |
| エミュレータ | emulador | Androidエミュレータ（emulador de Android）。Flutter系の単元で使う |

## この授業の用語

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| ハイブリッドアプリ | aplicación híbrida | |
| ネイティブアプリ | aplicación nativa | |
| アプリ | aplicación | app とも言うが、訳文では aplicación にそろえる |
| クロスプラットフォーム | multiplataforma | |
| WebView | WebView | Android の `WebView`、iOS の `WKWebView` に当たる。訳さない |
| クラウドIDE | IDE en la nube | ブラウザで使う開発環境。男性名詞（el IDE）。Monacaの画面名として出るときは日本語のまま残す |
| テンプレート | plantilla | |
| 公開 | publicar | 名詞は publicación。Monacaの **プロジェクト → 公開…**。発行されるのはプロジェクトを取り込ませるURLで、アプリを動かすURLではない。前年度の「Web公開」（alojamiento web）とは別物なので、alojar とは訳さない |
| 公開URL・取り込み用のURL | URL de importación | `https://monaca.mobi/ja/directimport?pid=…` の形のURL。女性名詞（la URL）。開くと、そのプロジェクトが自分のMonacaに取り込まれる |
| インポート・取り込む | importar | ダッシュボードの **インポート** は日本語のまま残す。Dart の `import` 文は `<code>` の中なので関係ない |
| エクスポート | exportar | Freeプランでは使えない |
| プレビュー | vista previa | クラウドIDEの画面名 **プレビュー** は日本語のまま残す |
| ビルド | compilación | 動詞は compilar。build と英字のまま書く資料もある。要確認 |
| クラウドビルド | compilación en la nube | ビルドの訳語にそろえる |
| デバッグ | depuración | 動詞は depurar |
| 実機 | dispositivo físico | |
| シミュレータ | simulador | iOSシミュレータ（simulador de iOS） |
| デバイス | dispositivo | Visual Studio Code のデバイス選択の画面名は英語のまま |
| ウィジェット | widget | 男性名詞（el widget）。個々のクラス名（`Text`、`Scaffold`）は `<code>` の中なので訳さない |
| 宣言的UI | UI declarativa | 女性名詞（la UI） |
| 状態 | estado | `setState` は `<code>` のまま |
| ホットリロード | hot reload | 英字のまま。男性名詞（el hot reload）。recarga en caliente と訳す資料もある。要確認 |
| 画面遷移 | navegación entre pantallas | `Navigator` は `<code>` のまま |
| 非同期 | asíncrono | `async` / `await` は `<code>` のまま |
| コマ | clase | 1コマ＝90分の授業1回。「2コマ目」は clase 2 |

## Web基礎で習った用語

学生が履修済みの用語。定訳を使い、説明を足さない。

| 日本語 | 訳 | メモ |
| --- | --- | --- |
| 要素 | elemento | HTMLの要素 |
| 属性 | atributo | HTMLの属性 |
| イベント | evento | |

## Monacaの画面に出る言葉（日本語のまま残し、訳をかっこで添える）

Monacaは日本語表示で使う。画面の言葉は訳さずに残し、うしろにこの表の訳をかっこで添える（例：**プロジェクト → 公開…** (Proyecto → Publicar…)）。かっこの訳は意味を伝えるためのもので、Monacaのほかの言語の表示と同じとは限らない。

| 画面の言葉 | かっこに添える訳 | 場所 |
| --- | --- | --- |
| ファイル | Archivo | クラウドIDEのメニュー |
| 編集 | Editar | クラウドIDEのメニュー |
| 表示 | Ver | クラウドIDEのメニュー |
| 実行 | Ejecutar | クラウドIDEのメニュー |
| ビルド | Compilar | クラウドIDEのメニュー |
| プロジェクト | Proyecto | クラウドIDEのメニュー |
| 設定 | Configuración | クラウドIDEのメニュー |
| ヘルプ | Ayuda | クラウドIDEのメニュー |
| 公開… | Publicar… | プロジェクトメニュー |
| インポート | Importar | ダッシュボード |
| 新しいプロジェクトを作る | Crear un proyecto nuevo | ダッシュボード |
| クラウドIDEで開く | Abrir en el IDE en la nube | ダッシュボード |
| 最小限のテンプレート | Plantilla mínima | 新規作成のテンプレートの選択肢 |
| プレビュー | Vista previa | クラウドIDEの画面 |

## 書き方の決まり

- **学生への呼びかけは tú にする。** 手順は tú の命令形で書く（Haz clic en **Run**.、Abre el archivo.）。usted・vos・vosotros は使わない。複数の人に向けるときは ustedes。
- **中南米の言い方にする。** スペインの言い方と分かれる語は、次の表の「中南米」の列の訳を使う。

  | 日本語 | 中南米（この用語集） | 使わない言い方 |
  | --- | --- | --- |
  | パソコン | computadora | ordenador |
  | ノートパソコン | laptop | portátil |
  | ファイル | archivo | fichero |
  | マウス | mouse | ratón |
  | キー・ボタンを押す | presionar | pulsar |
  | 画面をタップする | tocar | pulsar |
  | スマートフォン | celular | móvil |

- **疑問符と感嘆符は、文頭の ¿ ¡ と文末の ? ! を対で書く。**
- **見出しは文頭だけ大文字にする**（Tres objetivos）。英語のように各語の頭を大文字にしない。
- **引用符は “…”、引用の中の引用は ‘…’。** 画面やアプリに出る日本語を囲むときは「」のまま残してよい（翻訳skillのルール）。
- 学生と先生を指すときは、男女で形が変わらない語を選ぶ（estudiante、docente）。`config/i18n.json` の翻訳の注記（pregúntale a tu docente）も、この書き方にそろえてある。
- 英字の用語に冠詞を付けるときは、上の表のメモの性に従う（el widget、el IDE、la URL、la UI）。
