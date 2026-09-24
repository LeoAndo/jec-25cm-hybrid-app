// 見た目の比較では、次の行を有効にして再読み込みする。
// ons.platform.select("android");

// 初期化のたびに新しい配列を返し、追加した内容と混ぜない。
function createInitialItems() {
  return [
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
}

let oshiItems = createInitialItems();
let isOpeningPage = false;

document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    document.getElementById("txt_storage").textContent = "この段階では、追加した内容は保存されません。";
    renderOshiList();
    document.getElementById("btn_open_add").addEventListener("click", openAddPage);

  }

  if (page.id === "page_add") {
    document.getElementById("btn_save_oshi").addEventListener("click", addOshi);
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

  // 続けて押しても、詳細画面を重ねて開かない。
  if (isOpeningPage || navApp.topPage.id !== "page_list") {
    return;
  }

  isOpeningPage = true;
  document.getElementById("txt_selected").textContent = "選択中：" + oshi.name;

  navApp.pushPage("detail.html", {
    data: {
      oshi: oshi
    },
    callback: function() {
      isOpeningPage = false;
    }
  });
}

function openAddPage() {
  const navApp = document.getElementById("nav_app");
  if (isOpeningPage || navApp.topPage.id !== "page_list") {
    return;
  }
  isOpeningPage = true;
  navApp.pushPage("add.html", {
    callback: function() {
      isOpeningPage = false;
    }
  });
}

function addOshi() {
  const btnSave = document.getElementById("btn_save_oshi");
  const txtMessage = document.getElementById("txt_add_message");
  if (btnSave.disabled) {
    return;
  }
  const name = document.getElementById("txt_input_name").value.trim();
  const genre = document.getElementById("txt_input_genre").value.trim();
  const comment = document.getElementById("txt_input_comment").value.trim();
  if (name === "" || genre === "" || comment === "") {
    txtMessage.textContent = "名前・ジャンル・推しポイントをすべて入力してください。";
    return;
  }
  btnSave.disabled = true;
  oshiItems.push({ name: name, genre: genre, comment: comment });
  renderOshiList();
  document.getElementById("txt_selected").textContent = "追加した推し：" + name;
  document.getElementById("nav_app").popPage();
}
