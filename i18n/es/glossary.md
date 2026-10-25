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
| ビルド | compilación | 動詞は compilar。build と英字のまま書く資料もある |
| クラウドビルド | compilación en la nube | ビルドの訳語にそろえる |
| デバッグ | depuración | 動詞は depurar |
| 実機 | dispositivo físico | |
| シミュレータ | simulador | iOSシミュレータ（simulador de iOS） |
| デバイス | dispositivo | Visual Studio Code のデバイス選択の画面名は英語のまま |
| ウィジェット | widget | 男性名詞（el widget）。個々のクラス名（`Text`、`Scaffold`）は `<code>` の中なので訳さない |
| 宣言的UI | UI declarativa | 女性名詞（la UI） |
| 状態 | estado | `setState` は `<code>` のまま |
| ホットリロード | hot reload | 英字のまま。男性名詞（el hot reload）。recarga en caliente と訳す資料もある |
| 画面遷移 | navegación entre pantallas | `Navigator` は `<code>` のまま |
| 非同期 | asíncrono | `async` / `await` は `<code>` のまま |
| コマ | clase | 1コマ＝90分の授業1回。「2コマ目」は clase 2 |
| 追加（コード欄の見出しの変え方） | agregar | 見出しは `<パス> · <変え方> · <範囲>` の形。パスと ` · ` と範囲の中のコードの断片は訳さない。見出しの変え方を説明する文（「コード欄の見出しには…」）のかぎかっこの中も、この3語にそろえる（#182） |
| 置き換え（同上） | reemplazar | |
| 全体を置き換える（同上） | reemplazar todo el archivo | 以前の見出しの `· 全文`（archivo completo）に代わる語。`全文` は見出しから消えた |
| コード欄 | bloque de código | |
| コードは変えません。（STEPの冒頭の決まり文句） | Este STEP no tiene cambios de código. | 教科書がそのSTEPで新しいコードを出さない、という意味。直後に学生が自分で値を変える文が続くことがあるので、「コードを変えるな」という禁止の言い方にしない（#182） |
| ハイブリッドアプリ開発技法 | Técnicas de desarrollo de aplicaciones híbridas | 授業名。教科書の題名・上部の帯・末尾の行。学生用ZIPの入口ページ（`package-student-materials.py`）は日本語と英語だけなので、es の訳文はそこに出ない（en は入口ページに合わせて Hybrid App Development） |
| Web基礎 | Fundamentos web | 学生が履修済みの科目名。web は小文字で書く（Fundamentos de la Web・Fundamentos Web とは書かない） |
| 通常版Monaca | versión estándar de Monaca | Monaca Education ではない通常版 |
| Freeプラン | plan Free | |
| 枠（プロジェクトの枠） | espacio | Freeプランの3枠。空き＝espacio libre／espacio disponible。CSS の「枠」（border）は borde で別の語 |
| 教材 | materiales | jec-25cm-kotlin と同じ（los materiales）。material educativo・materiales de enseñanza とは書かない |
| 教科書 | libro de texto | jec-25cm-kotlin と同じ |
| 共通資料 | material común | jec-25cm-kotlin と同じ。単数で書く（「共通資料のSTEP 4〜7」は el STEP 4〜7 del material común）。リンクの「共通資料：困ったとき」は Material común: Solución de problemas。サイドバーの「共通：はじめの準備」「共通：困ったとき」は Común: Preparación inicial／Común: Solución de problemas |
| 開始コード | código inicial | 各コマの最初にある合流用のコード |
| 単元 | unidad | jec-25cm-kotlin と同じ |
| 完成版 | versión terminada | jec-25cm-kotlin と同じ。「STEP NNまで書いたコードが、…の完成版です。」も versión terminada（versión final とは書かない） |
| アレンジ | personalizar／personalización | jec-25cm-kotlin と同じ |
| 題材 | tema | 学生が自分で決める好きなもの・習慣などの内容。temática とは書かない |
| 先生／教員 | docente | 男女で形が変わらない語（下の「書き方の決まり」）。profesor とは書かない（#185）。冠詞は文による（el docente／tu docente。どちらの形も既訳にある） |
| 提出 | entregar／entrega | jec-25cm-kotlin と同じ（Google Classroom の語） |
| 好きなものノート | Cuaderno de favoritos | M01・M02の題材。画面の題名「好きなものノート」は日本語のまま残し (Cuaderno de favoritos) を添える。文中は cuaderno de favoritos（「自分の好きなものノート」は tu propio cuaderno de favoritos） |
| 好きなもの | favorito／cosa favorita | M02 の画面のボタン「好きなものを追加」は (Agregar un favorito)。文中では cosas que te gustan とも書く |
| 名前・種類・好きな理由 | nombre／tipo／razón | 画面の項目名。コードのプロパティ `name`・`genre`・`comment` は原文のまま。F01・F02 の「続けたい理由」も razón（「続けたい理由」 (Razón para continuar)）。データの項目としての「理由」は motivo とは書かない（項目でない一般の「理由」は motivo でもよい） |
| 項目（オブジェクトの） | campo | M02の保存データの「文字列の3項目」、F01・F02 の `Habit` の項目。選んでいる一覧の項目（elemento）と区別する |
| 一覧／詳細 | lista／detalle | 詳細画面＝pantalla de detalle。Monaca系（M01・M02）は単数の el detalle、Flutter系（F01・F02）の既訳は複数の los detalles（pantalla de detalles、「詳しく見る」 (Ver detalles)）で、系統の中ではそろっている |
| 端末選択 | selección de dispositivos | Monacaのプレビューの iPhone 15／Pixel 8 |
| 初期化（記録を初期の内容に戻す操作） | restablecer／restablecimiento | M02・F02 の初期化ボタンと処理。reiniciar／reinicio は「再起動」に使うので、初期化には使わない。F02 の画面のボタン「初期化する」は (Restablecer)、M02 の「初期の内容に戻す」は (Restablecer contenido inicial)。プログラムの初期化（Onsen UI のページの `init`、Swift の初期化）は inicializar／inicialización |
| 保存キー | clave de guardado | `localStorage` のキー（M02）、`SharedPreferencesAsync` のキー（F02） |
| 復元 | restaurar | |
| 空欄 | campo vacío | 空白だけの入力（solo espacios en blanco）と区別する。campo en blanco とは書かない |
| スタンプ帳 | tablero de sellos | F01・F02の題材。題名では Tablero de sellos。estampa とは書かない |
| スタンプ／スタンプを押す | sello／poner un sello | 画面のボタン「スタンプを押す」は日本語のまま残し (Poner sello) を添える。押した分＝los sellados |
| 1つ戻す | deshacer uno | 画面のボタン「1つ戻す」は日本語のまま残し (Deshacer uno) を添える（sello に合わせて男性形） |
| 習慣 | hábito | |
| 回数 | conteo | recuento・cantidad de veces とは書かない。画面の「回」は veces（「3 / 2 回 · あと-1回」 (3 / 2 veces · faltan -1 veces)） |
| 目標回数 | cantidad objetivo | `stampGoal`。「目標」は objetivo |
| 残り回数 | cantidad restante | |
| 合計 | total | |
| 詳しく見る | (Ver detalles) | 画面のボタン。日本語のまま残す |
| 達成メッセージ | mensaje de logro | |
| ホットリスタート | hot restart | 英字のまま。男性名詞（el hot restart） |
| 非同期処理 | procesamiento asíncrono | F02 で定義する文は procesamiento asíncrono (非同期処理) と日本語を添える。`async` / `await` は `<code>` のまま |
| 通常APK | APK normal | `flutter build apk` の既定（release）のAPK |
| 端末ID | ID del dispositivo | `flutter devices` で見る値。`端末ID` が `<code>` の中にあるときは (端末ID = ID del dispositivo) と添える |
| 空テンプレート | plantilla vacía | `flutter create --empty` |
| 制作フォルダ | carpeta de trabajo | |
| 条件演算子 | operador condicional | `? :` |
| 名前付き引数 | argumento con nombre | jec-25cm-kotlin と同じ。「必須の名前付き引数」は argumento con nombre obligatorio |
| 件（データの数） | elemento | 3件＝3 elementos |

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
