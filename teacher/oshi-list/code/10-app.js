// 見た目の比較では、次の行を有効にして再読み込みする。
// OSの指定は、Onsen UIが画面を作る前に行う。
// ons.platform.select("android");

// ページの要素が使えるようになってから処理する。
document.addEventListener("init", function(event) {
  const page = event.target;

  if (page.id === "page_list") {
    document.getElementById("txt_selected").textContent = "一覧を準備しました";
  }
});
