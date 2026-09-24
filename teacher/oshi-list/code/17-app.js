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

// templateの中身は、ページが作られてから取得する。
document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    renderOshiList();
  }

  if (page.id === "page_detail") {
    const oshi = page.data.oshi;

    document.getElementById("txt_detail_name").textContent = oshi.name;
    document.getElementById("txt_detail_genre").textContent = oshi.genre;
    document.getElementById("txt_detail_comment").textContent = oshi.comment;
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

    const itemOshi = document.getElementById("item_oshi_" + i);
    itemOshi.addEventListener("click", function() {
      openOshiDetail(oshiItems[i]);
    });
  }
}

function openOshiDetail(oshi) {
  const navApp = document.getElementById("nav_app");

  document.getElementById("txt_selected").textContent = "選択中：" + oshi.name;

  navApp.pushPage("detail.html", {
    data: {
      oshi: oshi
    }
  });
}
