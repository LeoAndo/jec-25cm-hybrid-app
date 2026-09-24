# 通常版Monacaの最小限テンプレート

単元の出発点として取り込んだ、公式 `monaca-templates/blank` の固定版です。学生へそのまま配布する単元ではありません。

- 出所：[monaca-templates/blank 4.0.0](https://github.com/monaca-templates/blank/tree/63b1dd8483612f23b2be35a3e77d7401a6e5b16f)
- コミット：`63b1dd8483612f23b2be35a3e77d7401a6e5b16f`
- リリース名：Support Cordova 12
- ライセンス：MIT。原文を `LICENSE` に保持しています。複製先の単元にも必ず残します。
- 取り込み許可：2026-09-23 オーナー確認済み

このREADME以外は、取得した4.0.0の原本をそのまま保持しています。原本と単元の差分を追えるよう、教材用の編集は `M0NXxx/` に複製してから行います。

## 比較結果

| 確認点 | 既存のMonacaTemplate | この固定版 | オーナー提供の通常版画面 |
| --- | --- | --- | --- |
| Cordova | 11.0 | 12.0 | 12.0.0 |
| classic.js | あり（index.htmlから未使用） | なし | なし |
| .gitignore / .monacaignore / LICENSE | なし | あり | あり |
| .nvmrc | なし | なし | あり |
| 基本構成 | .monaca / res / www / config.xml / package.json | 同左 | 同左 |

Cordovaの版と主要な構成は一致しますが、画面にある `.nvmrc` は4.0.0にはありません。この差分も含めて比較対象として残します。**クラウドで生成される各ファイルの内容との完全一致と、ZIPインポート・プレビューは未確認です。** このフォルダを、クラウド生成物そのものをエクスポートしたものとは記載しません。既存の `MonacaTemplate/` は比較用に変更せず保持します。

調査時のmaster（4.1.6）はCordova13でした。今回の画面資料に合わせ、移動するmasterではなくCordova12の4.0.0を選んでいます。

2026-09-24、オーナーから共有された [master](https://github.com/monaca-templates/blank/tree/master) を再確認しました。確認時のコミットは `78f4430830a95cf3e54833e1c472b451018a6e2a`（4.1.6）です。Cordova 13、Androidプラットフォーム14.0.1、iOSプラットフォーム8.0.1、Nodeの要件・loader・iOSアイコン構成が変わっています。`index.html` には `cordova.js` の直接読み込みも追加されています。**オーナーが現在のFreeプランで新規作成した最小限テンプレートもCordova 12であると確認し、blank 4.0.0／Cordova 12の維持を決定しました。** 本原本とM01・M02のテンプレート構成は更新しません。

## 単元へ複製するとき

`.monaca/project_info.json`、`.gitignore`、`.monacaignore`、`LICENSE`、`config.xml`、`package.json`、`www/`、`res/` を複製します。`.monaca` のほかのローカル情報は含めません。単元のREADMEはその単元用に作ります。

`www/` の教材コードをLFにそろえ、`config.xml` のアプリIDと名前を単元に合わせます。テンプレート由来の既存依存は保持しますが、授業の動作はCordovaプラグインを呼ばず、静的サーバとChromeで検証できる範囲にします。`npm install` やクラウドビルドを授業の開始条件にはしません。
