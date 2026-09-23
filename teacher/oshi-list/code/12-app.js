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
    renderOshiList();
  }
});

function createOshiRowHtml(index) {
  return '<ons-list-item id="item_oshi_' + index +
    '" class="oshi-card" tappable modifier="chevron">' +
    '<div class="center">' +
    '<span class="list-item__title oshi-name" id="txt_name_' +
    index + '"></span>' +
    '<span class="list-item__subtitle oshi-genre" id="txt_genre_' +
    index + '"></span>' +
    '</div>' +
    '</ons-list-item>';
}

function renderOshiList() {
  const listOshi = document.getElementById("list_oshi");
  let html = "";

  for (let i = 0; i < oshiItems.length; i++) {
    html += createOshiRowHtml(i);
  }

  // HTMLを作り直すとイベントも消えるため、全行を置いてから登録する。
  listOshi.innerHTML = html;

  for (let i = 0; i < oshiItems.length; i++) {
    // データに含まれる「<」などを、HTMLではなく文字として表示する。
    document.getElementById("txt_name_" + i).textContent = oshiItems[i].name;
    document.getElementById("txt_genre_" + i).textContent = oshiItems[i].genre;

  }
}
