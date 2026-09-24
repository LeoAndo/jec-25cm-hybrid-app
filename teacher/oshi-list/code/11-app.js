// 見た目の比較では、次の行を有効にして再読み込みする。
// OSの指定は、Onsen UIが画面を作る前に行う。
// ons.platform.select("android");

let oshiItems = [
  {
    name: "好きな音楽",
    genre: "音楽",
    comment: "通学中に聴くと、元気になります。"
  },
  {
    name: "カレー",
    genre: "食べ物",
    comment: "自分の好きな辛さを選べるところが好きです。"
  },
  {
    name: "公園",
    genre: "場所",
    comment: "ゆっくり歩いて、気分を変えられます。"
  }
];

// ページの要素が使えるようになってから処理する。
document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    document.getElementById("txt_selected").textContent = "登録件数：" + oshiItems.length;
  }
});
