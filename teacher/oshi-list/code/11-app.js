// 見た目の比較では、次の行を有効にして再読み込みする。
// OSの指定は、Onsen UIが画面を作る前に行う。
// ons.platform.select("android");

let oshiItems = [
  {
    name: "NotebookLM",
    genre: "学習ツール",
    comment: "授業のノートをもとに、自分の言葉で説明できるまで質問しています。\n分からなかったことがつながる瞬間が好きです。"
  },
  {
    name: "Android Studio / Xcode",
    genre: "開発ツール",
    comment: "Android StudioやXcodeで、思いついた画面を形にするのが好きです。\n次は自分が毎日使えるアプリを作ってみたいです。"
  },
  {
    name: "AIエージェントを使ったアプリ開発",
    genre: "気になる技術",
    comment: "AIエージェントと相談しながら、アプリを作る方法に興味があります。\n提案されたコードの理由を確かめ、自分でも直せるようになりたいです。"
  }
];

// ページの要素が使えるようになってから処理する。
document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    document.getElementById("txt_selected").textContent = "登録件数：" + oshiItems.length;
  }
});
