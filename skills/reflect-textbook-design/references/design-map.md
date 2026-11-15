# Figmaと共有CSSの対応付け

この対応表は初回の移植時点の調査用情報。現在の参照先はREADME「教科書のデザインをFigmaから反映する（教員用）」を読む。毎回最新のFigmaの対象ノード・変数・モード・テキストスタイルと、実際のCSSを取得する。値の正本はFigmaとし、この表にhex値を複製し続けない。

## 参照先

- [M01 好きなものノート 教科書｜PC版](https://www.figma.com/design/Gfot9q0DSrfaZI3PmMQ50X?node-id=2-2)
- fileKey: `Gfot9q0DSrfaZI3PmMQ50X`
- ページID: `0:1`、基準フレーム: `2:2`、PC幅1440px
- [F01 差分コード・比較表示の部品見本](https://www.figma.com/design/Gfot9q0DSrfaZI3PmMQ50X?node-id=9-2)：フレーム `9:2`。原文は `docs/stamp-board/index.html` の `section#step-2 / pre#diff-02-main-dart`（追加・削除行）と、`section#step-0` 内の最初の `.compare`。

名前やIDが変わった場合は現在のファイルを調べる。存在未確認の変数やノードを推測して対応付けない。

## 変数とスタイルの参照先

初回整備時点のコレクションは次の3つ。反映時はIDだけで判断せず、現在のコレクション名・モード・用途とCSS構文名を再取得する。

| コレクション | ID | 役割 |
| --- | --- | --- |
| 教科書｜パレット | `VariableCollectionId:15:2` | 基本色。用途別色からaliasで参照する |
| 教科書｜色 | `VariableCollectionId:15:3` | 本文・コード・確認・差分などの用途別色 |
| 教科書｜書体 | `VariableCollectionId:15:4` | 本文・コードのファミリーと400/600/700/750/800の太さ |

初回は用途別色40個・基本色33個・書体変数7個・テキストスタイル41個を設定した。用途別色のうち37個と基本色のうち32個はCSSに対応し、残りは後述のブラウザ標準表示の参考値である。代表デザインの全500テキストノード・1237区間にスタイルと書体・太さの継承を確認し、塗り・線・影の単色色設定2089箇所はすべて変数へ関連付けた。これらは初回確認時点の件数で、今後のデザイン追加時に維持する固定件数ではない。

M01の取り込みで分割されていた本文135箇所は、Figma内でリッチテキストへ整理して文字の重なりを解消した。コード枠は内容に合わせて高さが伸びる設定にし、末尾の欠けを解消した。最終画像でM01のコード末尾とF01の差分・比較表示を確認している。Figmaの高さや改行をHTMLへ機械的に写さず、HTMLの通常の折り返し・コード枠内の横スクロールを維持する。

## CSSのスコープ

`docs/assets/textbook.css` の基本規則は学生用・共通資料・教員用ガイドが共有する。後半の `.textbook` は学生用単元に適用する。書体は `:root` の `--font-body`・`--font-code`、日本語以外は言語別規則も見る。後続の上書き・画面幅・印刷規則まで確認し、冒頭の値だけで実効値を判断しない。

M01をPCの代表画面とする。単元一覧は `config/teaching-materials.json` から取得し、M01にない差分コード・比較ブロックはF01/F02等の実在する箇所を確認する。教材の文章・学習順序・掲載コードはGitを正とする。Figmaの取り込み時の改行やレイヤー分割を本文へ戻さない。

## 色の用途とCSS変数

`.textbook` の基本色は `--palette-243247` のような小文字hex名で定義し、用途別変数から参照する。3桁hexは6桁、半透明のRGBAは8桁（例：`--palette-24324718`）で表す。用途だけを変える場合は用途別変数の参照先を選び、基本色を変える場合は同じ基本色を使う全用途への影響を確認する。ブラウザ標準のチェックボックスなど、CSSに存在しない取り込み色を推測で追加しない。

| 用途 | CSS変数 | 主な適用先 |
| --- | --- | --- |
| 本文・補助文字 | `--ink` / `--muted` | 本文、見出し、補助説明 |
| ページ・区切り | `--paper` / `--line` | ページ、目次、表、画像 |
| 強調 | `--blue` | リンク、STEP番号、ボタン |
| 目標 | `--surface-goal` | `.goal` |
| 注意 | `--surface-note` / `--note-border` / `--note-title` | `.note`、枠、見出し |
| 確認 | `--mint` / `--check-border` / `--check-accent` | `.check`、進捗、チェック、目次の確認記号 |
| コード | `--surface-code` / `--surface-code-heading` / `--border-code` | `pre`、`.code-head` |
| インラインコード | `--code-inline-background` | `code` |
| 構文色 | `--syntax-keyword` / `--syntax-string` / `--syntax-type` / `--syntax-comment` | `.syntax-*`。差分markupのないコードだけ色分けする |
| ナビ | `--nav-border` / `--nav-selected-background` / `--nav-selected-text` / `--nav-menu-background` | 目次ボタン・選択・メニュー |
| メニューの影 | `--menu-shadow` | 影の色・透明度。位置やぼかしは別の設計値 |
| 参照コード | `--reference-heading-background` / `--reference-code-background` | `[data-code-kind="reference"]` と直後のコード |
| ファイルの装飾 | `--file-icon-border` | `.file-icon`。今回のノードが実在・使用されているか調べる |
| 練習・操作 | `--task-border` / `--action-background` | `.task`、`.next a`、`.button-link` |
| 差分の既存行 | `--diff-context` | `pre.diff`、`.diff-keep` |
| 差分の追加行 | `--diff-add-background` / `--diff-add-border` / `--diff-add-text` | `ins`、`.diff-add` |
| 差分の削除行 | `--diff-delete-background` / `--diff-delete-border` / `--diff-delete-text` | `del`、`.diff-del` |

Figma変数の表示名だけで対応を断定しない。用途、解決後の値、関連付いたノードを照合し、参照先の基本色・モードも確認する。同じ色でも構文の文字列と確認欄、型名と強調色は別用途である。パレット変更時は参照している用途を列挙する。CSS変数を宣言しただけで反映済みとせず、対象規則から使われていることを確かめる。

ネイティブチェックボックスはブラウザが描く。次の変数はFigma取り込み時のブラウザ標準表示を編集・参照するためのもので、CSSには定義していない。

| Figmaの参考変数に付けたCSS構文名 | 用途 |
| --- | --- |
| `--browser-checkbox-border` | ブラウザ標準のチェックボックス境界線 |
| `--browser-checkbox-background` | ブラウザ標準のチェックボックス背景 |
| `--browser-checkbox-mark` | ブラウザ標準のチェック記号 |
| `--palette-767676` | 標準境界線の参考基本色 |

これらの名前がFigmaにあるという理由だけで、CSS変数や独自チェックボックスを追加しない。HTMLはネイティブinputと `accent-color` を使うため、ブラウザが描いた図形の枠・記号に対応する個別CSS規則があるとは限らない。チェックボックス自体の見た目の変更を依頼された場合に、状態・キーボード操作・読み上げへの影響を調べ、必要な実装範囲を決める。

## 書体と文字設定

- `--font-body` はNoto Sans JP、`--font-code` はRoboto Monoと日本語用Noto Sans JP。`font-family` と `font` shorthandの両方を検索する。
- `:root` の `--font-weight-400`・`--font-weight-600`・`--font-weight-700`・`--font-weight-750`・`--font-weight-800` は既存の太さの共通参照先。値を変更する場合は共有する本文・見出し・教員用ガイドへの影響も調べる。
- テキストスタイル名のMedium/Boldだけで判断せず、Figmaノードの解決後の太さを取得する。600・750・800などを一律に500や700へ丸めない。fontFamily変数の関連付けによって太さの解決値が変わっていないか確認する。
- 中国語（簡体・香港繁体・台湾繁体）、韓国語、ミャンマー語、アラビア語、モンゴル語の言語別指定と、翻訳内の日本語指定を保持する。全言語をNoto Sans JP一つへ置換しない。
- 教科書本文18px・行高1.85、コード16pxなどの初期値を反映時の正本にしない。相対単位・計算式・意図した小数を保持する。

## 構造と操作

RTLには論理プロパティを使う。コードのLTRと本文のRTLを区別する。`pre.diff` の `ins`・`del`・省略行を平坦なテキストへ置換しない。比較コードは狭い幅でも折り返して読める状態を保つ。

`docs/assets/textbook.js` は既存の訳文・要素からPC目次とSTEP見出しを組み立てる。翻訳済みの目次ラベル、進捗キー、`data-check`、章ID、`data-back`、`data-keep-from`、言語切替を保つ。見た目だけの更新でカタログを再翻訳しない。
