# 教科書に同梱するフォント

本文は Noto Sans JP、コードなどの等幅表記は Roboto Mono を使います。Roboto Mono にない日本語は Noto Sans JP で表示します。中国語・韓国語・ミャンマー語・アラビア語・モンゴル語の既存の言語別指定は `../textbook.css` に残しています。

Google Fonts の公式配布から取得した可変 TTF を、内容を変更せずに同梱しています。ファイル名の `[wght]` だけを `-wght` に置き換えました。日本語を含むグリフを削減せず、ウェイトも固定していません。ブラウザは相対パスの `@font-face` で読み込み、CDNや端末にインストールされた同名フォントには依存しません。

## 取得元（2026-11-15）

| 同梱ファイル | ウェイト | 公式配布元の固定コミット |
| --- | --- | --- |
| `noto-sans-jp/NotoSansJP-wght.ttf` | 100–900 | [google/fonts / notosansjp](https://github.com/google/fonts/tree/66a36c8c94b1a5d992ee4e7f392fccfe4945767c/ofl/notosansjp) |
| `roboto-mono/RobotoMono-wght.ttf` | 100–700 | [google/fonts / robotomono](https://github.com/google/fonts/tree/aa24661a5ba24c8f8a550a16fb13198719fc2c23/ofl/robotomono) |

各ディレクトリの `OFL.txt` は、その固定コミットにある著作権表示と SIL Open Font License 1.1 の原文です。教材への同梱・再配布時には、このライセンスと著作権表示も保持します。フォント単体では販売しません。Noto の Reserved Font Name は `Source` です。変更したフォントを再配布する場合は、各ライセンスの条件を改めて確認してください。

## SHA-256

```text
c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f  noto-sans-jp/NotoSansJP-wght.ttf
1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9  noto-sans-jp/OFL.txt
66a80e79d17e4c7cabd162e2916578a4cc08fd19eef6e2a643305eae9c567b2b  roboto-mono/RobotoMono-wght.ttf
50ab8dd54680d3473f649c9db86fece88434d097c7834475c1c72d2f8c429215  roboto-mono/OFL.txt
```

更新時は取得元・ウェイト・ライセンス・ハッシュを一緒に更新し、Figmaとブラウザの書体・太さ・折り返しを再確認します。フォントとライセンスをGit管理に追加してから学生用ZIPを作成し、展開したHTMLをオフラインで確認します。デザインの反映手順はリポジトリ直下のREADMEにあります。
