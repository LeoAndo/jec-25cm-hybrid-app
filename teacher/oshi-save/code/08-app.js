// 見た目の比較では、次の行を有効にして再読み込みする。
// ons.platform.select("android");

const STORAGE_KEY = "jec-25cm-oshi-save-v1";

// 初期化のたびに新しい配列を返し、追加した内容と混ぜない。
function createInitialItems() {
  return [
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
}

let oshiItems = createInitialItems();
let isOpeningPage = false;
let canSave = true;

document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    loadOshiItems();
    renderOshiList();
    document.getElementById("btn_open_add").disabled = !canSave;
    document.getElementById("btn_open_add").addEventListener("click", openAddPage);
    document.getElementById("btn_request_reset").addEventListener("click", function() {
      document.getElementById("panel_reset").classList.remove("is-hidden");
    });
    document.getElementById("btn_cancel_reset").addEventListener("click", function() {
      document.getElementById("panel_reset").classList.add("is-hidden");
    });
    document.getElementById("btn_confirm_reset").addEventListener("click", resetOshiItems);
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
  if (!canSave || isOpeningPage || navApp.topPage.id !== "page_list") {
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
  if (btnSave.disabled || !canSave) {
    return;
  }

  const name = document.getElementById("txt_input_name").value.trim();
  const genre = document.getElementById("txt_input_genre").value.trim();
  const comment = document.getElementById("txt_input_comment").value.trim();
  if (name === "" || genre === "" || comment === "") {
    txtMessage.textContent = "名前・種類・好きな理由をすべて入力してください。";
    return;
  }

  // 保存に成功するまでは、表示中の配列を変えない。
  const nextItems = oshiItems.slice();
  nextItems.push({ name: name, genre: genre, comment: comment });
  btnSave.disabled = true;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextItems));
  } catch (error) {
    btnSave.disabled = false;
    txtMessage.textContent = "保存できませんでした。入力内容は残しています。ブラウザの保存設定や空き容量を確認してください。";
    return;
  }

  oshiItems = nextItems;
  renderOshiList();
  document.getElementById("txt_storage").textContent = oshiItems.length + "件をこのブラウザに保存しました。";
  document.getElementById("txt_selected").textContent = "追加したもの：" + name;
  document.getElementById("nav_app").popPage();
}

function loadOshiItems() {
  const txtStorage = document.getElementById("txt_storage");
  txtStorage.textContent = "ソースに書いた初期の内容を表示しています。";
  try {
    const text = localStorage.getItem(STORAGE_KEY);
    if (text === null) {
      return;
    }
    const savedItems = JSON.parse(text);
    // JSONとして読めても、画面に必要な配列・文字列とは限らない。
    if (!isValidItems(savedItems)) {
      canSave = false;
    } else {
      oshiItems = savedItems;
      txtStorage.textContent = oshiItems.length + "件の保存内容を読み込みました。";
    }
  } catch (error) {
    canSave = false;
  }
  if (!canSave) {
    txtStorage.textContent = "保存内容を読み込めません。保存データは変更していません。初期の内容に戻すか、ブラウザの保存設定を先生と確認してください。";
  }
}

function isValidItems(items) {
  if (!Array.isArray(items)) {
    return false;
  }
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item === null || typeof item !== "object" ||
        typeof item.name !== "string" || typeof item.genre !== "string" ||
        typeof item.comment !== "string") {
      return false;
    }
    if (item.name.trim() === "" || item.genre.trim() === "" || item.comment.trim() === "") {
      return false;
    }
  }
  return true;
}

function resetOshiItems() {
  const txtStorage = document.getElementById("txt_storage");
  try {
    // clearではなく、このアプリの保存キーだけを削除する。
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    txtStorage.textContent = "保存内容を削除できませんでした。表示と保存データは変更していません。";
    return;
  }
  oshiItems = createInitialItems();
  canSave = true;
  document.getElementById("btn_open_add").disabled = false;
  document.getElementById("panel_reset").classList.add("is-hidden");
  renderOshiList();
  document.getElementById("txt_selected").textContent = "まだ選択していません";
  txtStorage.textContent = "保存内容を削除し、ソースに書いた初期の内容へ戻しました。";
}
