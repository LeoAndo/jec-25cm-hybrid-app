"""文の取り出し、訳文の検査、各言語のHTMLの生成、対訳カタログの同期と取り込みを検証する。"""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("localize", SCRIPTS / "localize-student-materials.py")
localize = importlib.util.module_from_spec(spec)
sys.modules["localize"] = localize  # dataclass が、モジュールを名前で引けるようにする
spec.loader.exec_module(localize)

TERMS = [{"name": "Flutterのエディタ", "canonical": "Visual Studio Code", "forbidden": ["VSCode"]}]


def page_of(text, name="docs/unit/index.html"):
    tree = localize.parse(text, name)
    extractor = localize._Extractor(text, name)
    return localize.Page(name, text, tree, extractor.run(tree), extractor.in_segment)


def sources_of(text):
    return [segment.source for segment in page_of(text).segments]


class ExtractTest(unittest.TestCase):
    def test_text_with_inline_tags_is_one_segment(self):
        self.assertEqual(
            sources_of("<p>アプリは、<strong>画面</strong>と<code>Dart</code>で作ります。</p>"),
            ["アプリは、<strong>画面</strong>と<code>Dart</code>で作ります。"],
        )

    def test_inline_elements_without_direct_text_are_separate_segments(self):
        # サイドバーのリンクの並び。1つの文にすると、単元を足すたびに全体が訳し直しになる。
        html = '<div class="resources"><a href="#help">困ったとき</a> <a href="../b/index.html">F02：CalcGame</a><span>自分用です。</span></div>'
        self.assertEqual(sources_of(html), ["困ったとき", "自分用です。"])

    def test_tags_with_attributes_become_numbered_placeholders(self):
        page = page_of('<p><a href="#s">見本</a>は<span class="x">参考</span>です。<img src="a.png" alt="図">と<br>改行</p>')
        text = page.segments[0]
        self.assertEqual(text.source, "<a1>見本</a1>は<span2>参考</span2>です。<img3/>と<br>改行")
        self.assertEqual([element.tag for element in text.placeholders], ["a", "span", "img"])

    def test_code_blocks_scripts_and_translate_no_are_not_extracted(self):
        html = (
            "<pre><code>// 日本語のコメント</code></pre><script>const a = 'あ';</script><style>/* あ */</style>"
            '<p translate="no">訳さない</p><p>訳す</p>'
        )
        self.assertEqual(sources_of(html), ["訳す"])

    def test_segment_needs_japanese_outside_protected_elements(self):
        # 3つ目のセルは、日本語が <code> の中にしかない。保護を外すと、訳しようのない断片が混ざる。
        html = ("<table><tr><td><code>テキストを変更</code></td><td>HTML / JavaScript</td>"
                "<td><code>テキストを変更</code> / HTML</td><td><code>x</code>（すべて小文字）</td></tr></table>")
        self.assertEqual(sources_of(html), ["<code>x</code>（すべて小文字）"])

    def test_translate_no_inside_a_sentence_is_rejected(self):
        # 文の途中だけを外すと、その文が断片に割れて訳せなくなる。<code> を使ってもらう。
        with self.assertRaisesRegex(localize.LocalizeError, 'には translate="no" を付けられません'):
            page_of('<p>エディタは <span translate="no">Visual Studio Code</span> です。</p>')

    def test_comment_inside_a_sentence_is_rejected(self):
        # コメントは木に残らないので、訳文で置き換えると消え、前後の文字が連結される。
        with self.assertRaisesRegex(localize.LocalizeError, "文の途中にHTMLコメントは書けません"):
            page_of("<p>あいう<!-- メモ -->えお</p>")
        # 文の外のコメントは、そのまま残るので受け付ける。
        self.assertEqual(sources_of("<p><!--前-->あいう</p><!--後-->"), ["あいう"])

    def test_attribute_value_containing_another_attribute_is_not_confused(self):
        page = page_of("""<p><img alt="かき方は src='sample.png' です" src="real.png"></p>""")
        self.assertEqual(localize._raw_attribute(page.text, page.segments[0].element, "src"), "real.png")

    def test_root_relative_link_is_rejected_while_reading_the_page(self):
        # 生成のときではなく check で捕まえる。行番号が出ないと直す場所が分からない。
        with self.assertRaisesRegex(localize.LocalizeError, "ルート相対のリンクは使えません"):
            page_of('<p>\n<a href="/docs/assets/textbook.css">あ</a></p>')
        # 外部のURLはパスが / で始まるので、混同しない。
        self.assertEqual(sources_of('<p><a href="https://developer.android.com/x#y(a,%20b)">公式</a></p>'), ["公式"])
        # 訳の対象でない要素でも、生成のときに src を書き換える。どのページにも <script src> がある。
        for html in ('<head><script src="/assets/textbook.js"></script></head>',
                     '<head><link rel="stylesheet" href="/assets/textbook.css"></head>',
                     '<div translate="no"><p>訳さない<img src="/a.png" alt="図"></p></div>'):
            with self.subTest(html=html), \
                    self.assertRaisesRegex(localize.LocalizeError, "ルート相対のリンクは使えません"):
                page_of(html)

    def test_unquoted_link_and_lang_attributes_are_rejected(self):
        for html, attribute in (
            ('<html lang=ja><body><p>あ</p></body></html>', "lang"),
            ("<p>あ<img src=images/a.png alt=\"図\"></p>", "src"),
            ('<p><a href=x.html>あ</a></p>', "href"),
        ):
            with self.subTest(attribute=attribute), \
                    self.assertRaisesRegex(localize.LocalizeError, f"{attribute} 属性は引用符で囲んでください"):
                page_of(html)

    def test_attributes_are_extracted_in_document_order(self):
        html = (
            '<html lang="ja"><head><meta name="description" content="説明文"><meta name="viewport" content="幅">'
            "<title>題名</title></head>"
            '<body><nav aria-label="学習ステップ"><a href="#a">一</a></nav><img src="a.png" alt="画面の図"></body></html>'
        )
        page = page_of(html)
        self.assertEqual([(segment.where, segment.source) for segment in page.segments], [
            ("meta content", "説明文"), ("title", "題名"), ("nav aria-label", "学習ステップ"),
            ("a", "一"), ("img alt", "画面の図"),
        ])

    def test_whitespace_is_normalized_and_same_source_is_listed_once(self):
        page = page_of("<p>一行目\n   二行目</p><p>一行目 二行目</p>")
        self.assertEqual(len(page.segments), 2)
        self.assertEqual(page.sources(), ["一行目 二行目"])

    def test_only_ascii_whitespace_is_normalized(self):
        # 全角スペースとノーブレークスペースは、書き方の一部なので残す。
        self.assertEqual(sources_of("<p>00\u3000今日の\n  ゴール</p>"), ["00\u3000今日の ゴール"])
        self.assertEqual(localize.validate("質問はありますか。", "Avez-vous des questions\u00a0?", TERMS), [])

    def test_inline_element_with_block_child_is_a_boundary(self):
        self.assertEqual(sources_of('<a href="x.html">前<div>中</div></a>'), ["前", "中"])

    def test_nested_list_text_is_split_around_the_list(self):
        self.assertEqual(sources_of("<ol><li>外側<ul><li>内側</li></ul>続き</li></ol>"), ["外側", "内側", "続き"])

    def test_html_must_have_matching_tags(self):
        for html, message in (
            ("<div><p>あ</div>", "docs/unit/index.html:1: 開始タグと終了タグが対応していません"),
            ("<div>\n<p>あ</p>", "docs/unit/index.html:1: <div> が閉じていません"),
            ("<p>あ<span/>い</p>", "自己終了タグは使えません"),
            ("<p>あ</br></p>", "</br> は書けません"),
        ):
            with self.subTest(html=html), self.assertRaisesRegex(localize.LocalizeError, re.escape(message)):
                page_of(html)

    def test_unquoted_translated_attribute_is_rejected(self):
        with self.assertRaisesRegex(localize.LocalizeError, "alt 属性は引用符で囲んでください"):
            page_of("<img src=a.png alt=図>")


class ValidateTest(unittest.TestCase):
    def problems(self, source, translation, han=False):
        return localize.validate(source, translation, TERMS, han)

    def test_accepts_reordered_placeholders_and_entities(self):
        self.assertEqual(self.problems(
            "<a1>見本</a1>は<strong>参考</strong>です。<code>a &lt; b</code>",
            "Use <code>a &lt; b</code> &amp; the <strong>reference</strong> <a1>sample</a1>.",
        ), [])

    def test_direction_marks_must_be_written_as_visible_entities(self):
        """&lrm; は目に見える書き方なので通す。見えない文字そのものは、レビューで見落とすので落とす。"""
        self.assertEqual(self.problems("「保存しました。」を確かめます。",
                                       "تحقق من 「保存しました。&lrm;」."), [])
        for character in ("\u200e", "\u200f", "\u061c", "\u202b", "\u2067", "\u2069"):
            with self.subTest(character=f"U+{ord(character):04X}"):
                found = self.problems("「保存しました。」を確かめます。", f"تحقق من 「保存しました。{character}」.")
                self.assertTrue(any("見えない文字" in problem for problem in found), found)

    def test_kanji_only_text_may_stay_the_same_only_in_han_languages(self):
        # 中国語では、日本語と同じ字になる言葉がある。英語などでは、訳し忘れである。
        self.assertEqual(self.problems("操作", "操作", han=True), [])
        self.assertIn("訳されていません", "".join(self.problems("操作", "操作")))
        self.assertIn("訳されていません", "".join(self.problems("共通：DevTools", "共通：DevTools")))

    def test_raw_markup_characters_inside_protected_elements_are_allowed(self):
        # <code> の中身は原文のまま残すので、そこに書かれた & や < は訳文の誤りではない。
        # 見ないようにしないと、この原文はどう訳しても通らなくなる。
        self.assertEqual(self.problems("<code>R&D</code> を開く。", "Open <code>R&D</code>."), [])

    def test_reports_each_kind_of_problem(self):
        cases = (
            ("訳文が空です", "確認", "  "),
            ("余分な空白や改行", "確認", "Check \n it"),
            ("足りません: </a1> <a1>", "<a1>見本</a1>です", "A sample"),
            ("余分にあります: </strong> <strong>", "見本です", "A <strong>sample</strong>"),
            ("入れ子が正しくありません", "<a1><strong>見本</strong></a1>", "<a1><strong>sample</a1></strong>"),
            ("&lt; と書く", "小さい", "a < b"),
            ("&amp; と書く", "質問と答え", "Q&A"),
            ("中身が、原文と違います", "<code>テキストを変更</code>を押す", "Press <code>Change text</code>"),
            ("中身が、原文と違います", "<kbd>実行</kbd>を押す", "Press <kbd>Run</kbd>"),
            ("中身が、原文と違います", "<samp>成功</samp>と出る", "See <samp>OK</samp>"),
            ("中身が、原文と違います", "<var>名前</var>を書く", "Write <var>name</var>"),
            ("正式表記がありません", "Visual Studio Code を開く", "Open the editor"),
            ("禁止表記", "開く", "Open VSCode"),
            ("訳されていません", "できたらチェックします。", "できたらチェックします。"),
        )
        for message, source, translation in cases:
            with self.subTest(source=source):
                found = self.problems(source, translation)
                self.assertTrue(any(message in problem for problem in found), found)


class LocalizeTest(unittest.TestCase):
    PAGES = {"docs/unit/index.html", "docs/other/index.html", "docs/common/setup.html"}

    def test_android_documentation_links_replace_only_japanese_language_parameter(self):
        cases = [
            ("https://developer.android.com/studio?hl=ja", "https://developer.android.com/studio?hl=fr"),
            ("https://developer.android.com/?x=a%20b&hl=ja&empty=&x=%2F#top",
             "https://developer.android.com/?x=a%20b&hl=fr&empty=&x=%2F#top"),
            ("//developer.android.com/studio?hl=ja&hl=ja", "//developer.android.com/studio?hl=fr&hl=fr"),
            ("https://developer.android.com/studio#hl=ja", "https://developer.android.com/studio#hl=ja"),
            ("https://developer.android.com/studio?hl=en", "https://developer.android.com/studio?hl=en"),
            ("https://developer.android.com/studio?otherhl=ja&hl=ja-jp",
             "https://developer.android.com/studio?otherhl=ja&hl=ja-jp"),
            ("https://example.com/?hl=ja", "https://example.com/?hl=ja"),
            ("https://developer.android.com.example.com/?hl=ja",
             "https://developer.android.com.example.com/?hl=ja"),
        ]
        for source, expected in cases:
            with self.subTest(url=source):
                self.assertEqual(localize._rewrite_link(source, "docs/unit/index.html", "fr", "docs",
                                                        self.PAGES, "fr"), expected)
        source = "https://developer.android.com/studio?hl=ja"
        self.assertEqual(localize._rewrite_link(source, "docs/unit/index.html", "ja", "docs",
                                                self.PAGES, "fr"), source)

    def test_android_link_is_escaped_once_inside_translated_and_untranslated_text(self):
        source = '<p><a href="https://developer.android.com/studio?hl=ja&amp;x=a%20b#top">公式資料</a>を開く。</p>'
        for translations in ({}, {"<a1>公式資料</a1>を開く。": "Open the <a1>official guide</a1>."}):
            with self.subTest(translated=bool(translations)):
                rendered = localize.localize(page_of(source), translations, "en", "docs", self.PAGES, "en")
                self.assertIn('href="https://developer.android.com/studio?hl=en&amp;x=a%20b#top"', rendered)
                self.assertNotIn("&amp;amp;", rendered)

    def render(self, html, translations, name="docs/unit/index.html"):
        return localize.localize(page_of(html, name), translations, "en", "docs", self.PAGES)

    def test_untranslated_attributes_mark_the_element_language(self):
        for tag, attribute in (("img", "alt"), ("button", "aria-label"),
                               ("div", "title"), ("input", "placeholder")):
            with self.subTest(attribute=attribute):
                end = "" if tag in localize.VOID else f"</{tag}>"
                source = f'<{tag} {attribute}="日本語の説明">{end}'
                rendered = localize.localize(page_of(source), {}, "en", "docs", self.PAGES,
                                             mark_untranslated=True)
                self.assertIn(f'{attribute}="日本語の説明" lang="ja"', rendered)
                translated = localize.localize(page_of(source), {"日本語の説明": "Description"},
                                               "en", "docs", self.PAGES, mark_untranslated=True)
                self.assertIn(f'{attribute}="Description"', translated)
                self.assertNotIn('lang="ja"', translated)

    def test_translated_attribute_keeps_language_inside_japanese_fallback(self):
        source = '<p>説明：<img src="images/a.png" alt="図の説明" /></p>'
        translated = localize.localize(page_of(source), {"図の説明": "Figure"},
                                       "en", "docs", self.PAGES, mark_untranslated=True)
        self.assertIn('alt="Figure"  lang="en"/>', translated)
        fallback = localize.localize(page_of(source), {}, "en", "docs", self.PAGES,
                                     mark_untranslated=True)
        self.assertIn('alt="図の説明"  lang="ja"/>', fallback)
        self.assertNotIn('/ lang=', fallback)
        page_of(translated)

    def test_untranslated_attributes_do_not_change_translated_descendant_language(self):
        source = ('<section aria-label="操作の説明"><p>押します。</p>'
                  '<p><a href="#next" title="次の説明">次へ</a>進みます。</p></section>')
        translations = {"押します。": "Press it.",
                        '<a1>次へ</a1>進みます。': '<a1>Next</a1>.'}
        rendered = localize.localize(page_of(source), translations, "en", "docs", self.PAGES,
                                     mark_untranslated=True)
        self.assertIn('<section aria-label="操作の説明" lang="ja">', rendered)
        self.assertIn('<p><span lang="en">Press it.</span></p>', rendered)
        self.assertIn('<a href="#next" title="次の説明" lang="ja"><span lang="en">Next</span></a>', rendered)

    def test_right_to_left_page_marks_direction_wherever_it_marks_language(self):
        """右から左のページでは、ページ全体に dir="rtl"、日本語のまま残す部分に dir="ltr" を付ける。

        dir がないと、右から左の段落に置いた日本語の文末の「。」が、文の反対側（左端）へ回り込む。
        """
        source = ('<html lang="ja"><body><p>未翻訳の文です。</p><p>訳した文です。</p>'
                  '<p><a href="#next" title="次の説明">次へ</a>進みます。</p>'
                  '<img src="images/a.png" alt="図の説明"><pre><code>// コード</code></pre></body></html>')
        translations = {"訳した文です。": "جملة مترجمة.", "<a1>次へ</a1>進みます。": "<a1>التالي</a1>."}
        rendered = localize.localize(page_of(source), translations, "ar", "docs", self.PAGES,
                                     mark_untranslated=True, direction="rtl")
        self.assertIn('<html lang="ar" dir="rtl">', rendered)
        self.assertIn('<p><span lang="ja" dir="ltr">未翻訳の文です。</span></p>', rendered)
        self.assertIn('<p>جملة مترجمة.</p>', rendered)
        # 属性だけが日本語の要素には lang だけを付ける。dir まで付けると、中の訳した本文や
        # 入れ物のリスト（aria-label だけが未翻訳の目次など）が左から右に並んでしまう。
        self.assertIn('<a href="#next" title="次の説明" lang="ja"><span lang="ar">التالي</span></a>', rendered)
        # 中身のない img は、dir が効くのが alt の表示だけなので、向きも日本語にする。
        self.assertIn('alt="図の説明" lang="ja" dir="ltr">', rendered)
        # コードは日本語版のバイト列のまま。左から右で読む指定はCSSが受け持つ。
        self.assertIn('<pre><code>// コード</code></pre>', rendered)
        page_of(rendered)
        # 左から右の言語のページには、dir を足さない（今までと同じHTMLになる）。
        english = localize.localize(page_of(source), {}, "en", "docs", self.PAGES, mark_untranslated=True)
        self.assertNotIn(" dir=", english)
        self.assertIn('<span lang="ja">未翻訳の文です。</span>', english)

    def test_container_with_only_a_japanese_label_keeps_the_page_direction(self):
        source = '<nav class="sidebar" aria-label="目次"><ol><li><a href="#a">はじめに</a></li></ol></nav>'
        rendered = localize.localize(page_of(source), {"はじめに": "مقدمة"}, "ar", "docs", self.PAGES,
                                     mark_untranslated=True, direction="rtl")
        self.assertIn('<nav class="sidebar" aria-label="目次" lang="ja"><ol><li><a href="#a">'
                      '<span lang="ar">مقدمة</span></a></li></ol></nav>', rendered)
        self.assertNotIn("dir=", rendered)

    def test_existing_dir_on_html_is_replaced_not_duplicated(self):
        source = '<html lang="ja" dir="ltr"><body><p>文です。</p></body></html>'
        rendered = localize.localize(page_of(source), {}, "ar", "docs", self.PAGES, direction="rtl")
        self.assertIn('<html lang="ar" dir="rtl">', rendered)
        self.assertEqual(rendered.count("dir="), 1)
        english = localize.localize(page_of(source), {}, "en", "docs", self.PAGES)
        self.assertIn('<html lang="en" dir="ltr">', english)

    def test_unquoted_dir_on_html_is_rejected(self):
        with self.assertRaisesRegex(localize.LocalizeError, "dir 属性は引用符で囲んでください"):
            page_of('<html lang="ja" dir=ltr><body><p>あ</p></body></html>')

    def test_without_translations_only_language_and_resource_links_change(self):
        html = (
            '<!doctype html>\n<html lang="ja">\n<head><link rel="stylesheet" href="../assets/textbook.css"></head>\n'
            '<body>\n  <p>一行目\n     二行目 <a href="images/a.png">大きく開く</a></p>\n'
            '<pre id="code"><code>// コメント &lt;b&gt;\n<span class="k">var</span> a;</code></pre>\n</body>\n</html>\n'
        )
        expected = (html.replace('lang="ja"', 'lang="en"')
                    .replace("../assets/textbook.css", "../../assets/textbook.css")
                    .replace("images/a.png", "../../unit/images/a.png"))
        self.assertEqual(self.render(html, {}), expected)

    def test_translation_restores_original_tags_and_keeps_surroundings(self):
        html = '<ul>\n  <li>\n    <a class="x" href="../other/index.html#s">見本</a>は<strong>参考</strong>です。\n  </li>\n</ul>'
        translated = self.render(html, {"<a1>見本</a1>は<strong>参考</strong>です。": "A <strong>reference</strong>: <a1>sample</a1>."})
        self.assertEqual(
            translated,
            '<ul>\n  <li>\n    A <strong>reference</strong>: <a class="x" href="../other/index.html#s">sample</a>.\n  </li>\n</ul>',
        )

    def test_links_are_rewritten_inside_translated_and_untranslated_segments(self):
        html = '<p>図は<a href="images/a.png?v=1#top">こちら</a>。</p><p>別の図は<a href="images/b.png">こちら</a>。</p>'
        translated = self.render(html, {"図は<a1>こちら</a1>。": "See <a1>this figure</a1>."})
        self.assertIn('See <a href="../../unit/images/a.png?v=1#top">this figure</a>.', translated)
        self.assertIn('別の図は<a href="../../unit/images/b.png">こちら</a>。', translated)

    def test_page_links_external_links_and_fragments_are_kept(self):
        html = (
            '<p>先に<a href="../common/setup.html?from=unit">準備</a>、<a href="#step-1">次へ</a>、'
            '<a href="https://developer.android.com/">公式</a>、<a href="downloads/A.zip">ZIP</a>を見ます。</p>'
        )
        translated = self.render(html, {})
        for kept in ('href="../common/setup.html?from=unit"', 'href="#step-1"', 'href="https://developer.android.com/"'):
            self.assertIn(kept, translated)
        self.assertIn('href="../../unit/downloads/A.zip"', translated)

    def test_attributes_are_translated_and_quotes_are_escaped(self):
        html = '<figure><a href="images/a.png"><img src="images/a.png" alt="「確認」の画面"></a></figure>'
        translated = self.render(html, {"「確認」の画面": 'The "Check" screen'})
        self.assertEqual(
            translated,
            '<figure><a href="../../unit/images/a.png"><img src="../../unit/images/a.png" alt="The &quot;Check&quot; screen"></a></figure>',
        )

    def test_attribute_inside_translated_segment_is_translated(self):
        html = '<p>図<img src="a.png" alt="画面">を見ます。</p>'
        translated = self.render(html, {"図<img1/>を見ます。": "See <img1/> here.", "画面": "Screen"})
        self.assertEqual(translated, '<p>See <img src="../../unit/a.png" alt="Screen"> here.</p>')

    def test_root_relative_link_is_rejected(self):
        # relpath に絶対パスを渡すと、実行したフォルダ次第で結果が変わる。
        with self.assertRaisesRegex(localize.LocalizeError, "ルート相対のリンクは使えません"):
            self.render('<p><a href="/docs/assets/textbook.css">あ</a></p>', {})

    def test_page_link_written_as_a_folder_stays_in_the_same_language(self):
        # ../other/ を資材とみなすと ../../ が付き、英語のページから日本語版へ戻ってしまう。
        translated = self.render('<p>次は<a href="../other/">こちら</a>。</p>', {})
        self.assertIn('href="../other/"', translated)

    def test_translated_attribute_cannot_break_a_later_link_attribute(self):
        # 置き換えた訳文をもう一度走査しないので、訳文の中の文字列は属性と取り違えられない。
        translated = self.render('<p><img alt="画像の説明" src="images/a.png"></p>',
                                 {"画像の説明": "screenshot src='other.png' end"})
        self.assertEqual(
            translated,
            '<p><img alt="screenshot src=&#39;other.png&#39; end" src="../../unit/images/a.png"></p>',
        )

    def test_common_page_moves_one_level_deeper_too(self):
        html = '<img src="images/a.png" alt="図"><a data-back href="../unit/index.html">もとの教科書へ戻る</a>'
        translated = self.render(html, {}, "docs/common/setup.html")
        self.assertIn('src="../../common/images/a.png"', translated)
        self.assertIn('href="../unit/index.html"', translated)

    def test_role_override_changes_headers_but_keeps_terminology(self):
        html = ('<section id="step-1"><table><tr><th>コード</th><td>コード</td></tr></table></section>'
                '<section id="step-2"><table><tr><th>コード</th></tr></table></section>')
        catalog = localize.Catalog({"コード": "コード — code"}, {("コード", "th"): "Code"})
        translated = self.render(html, catalog)
        self.assertEqual(translated.count("<th>Code</th>"), 2)
        self.assertIn("<td>コード — code</td>", translated)
        # STEPを移すだけでは、番号やidを使っていない訳し分けは外れない。
        moved = self.render(html.replace("step-1", "step-8").replace("step-2", "step-9"), catalog)
        self.assertEqual(moved.count("<th>Code</th>"), 2)

    def test_attribute_override_does_not_change_the_same_text_in_the_body(self):
        html = '<p>画面<img src="a.png" alt="画面" title="画面">を見ます。</p><p>画面</p>'
        catalog = localize.Catalog({"画面": "Screen"}, {("画面", "img alt"): "App screen"})
        translated = self.render(html, catalog)
        self.assertIn('alt="App screen" title="Screen"', translated)
        self.assertIn("<p>Screen</p>", translated)


def ui(copy):
    """確認用の最小のUI文言。localize.UI_KEYS の全項目を埋める。"""
    return {key: (copy if key == "copy" else f"{copy}:{key}") for key in localize.UI_KEYS}


class TextbookScriptTest(unittest.TestCase):
    def test_script_element_keeps_json_out_of_html_parsing(self):
        element = localize.textbook_i18n_script({"copy": "</script><b>Copy"})
        self.assertNotIn("</script><b>", element)
        payload = element.split(">", 1)[1].rsplit("<", 1)[0]
        self.assertEqual(json.loads(payload)["copy"], "</script><b>Copy")

    def test_body_is_required_for_the_insertion(self):
        self.assertEqual(localize.insert_into_body("<body class='x'>あ</body>", "!", "p.html"),
                         "<body class='x'>!あ</body>")
        with self.assertRaisesRegex(localize.LocalizeError, "p.html"):
            localize.insert_into_body("<p>あ</p>", "!", "p.html")


class CommandTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.write("config/i18n.json", json.dumps({
            "source_language": "ja", "source_root": "docs", "catalog_root": "i18n",
            "languages": [{"code": "en", "name": "English", "distribute": True, "ui": ui("Copy")},
                          {"code": "fr", "name": "Français", "distribute": False, "ui": ui("Copier")}],
            "source_ui": ui("コピー"),
        }, ensure_ascii=False))
        self.write("config/teaching-materials.json", json.dumps({"terms": TERMS}))
        self.write("docs/assets/textbook.css", "body {}")
        self.write("docs/unit/index.html", (
            '<html lang="ja"><head><link rel="stylesheet" href="../assets/textbook.css"><title>単元</title></head>'
            "<body><h1>はじめての単元</h1><p>ここで止まって、確認</p><p><code>Run</code>を押します。</p></body></html>"
        ))
        self.write("docs/common/setup.html", '<html lang="ja"><body><p>ここで止まって、確認</p><p>準備をします。</p></body></html>')
        self.work = self.root / "dist/i18n-work"

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def settings(self):
        return localize.load_settings(self.root)

    def quiet(self, function, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()) as errors:
            result = function(*args)
        return result, output.getvalue(), errors.getvalue()

    def sync(self, *languages):
        self.quiet(localize.sync, self.settings(), list(languages) or ["en"], [], self.work, 40, 3000)

    def todo(self, language="en"):
        """作業ファイルの中身。原文→項目。"""
        items = {}
        for path in sorted((self.work / language).rglob("todo-*.json")):
            for item in json.loads(path.read_text(encoding="utf-8"))["segments"]:
                items[item["source"]] = item
        return items

    def merge(self, translations, overwrite=False, language="en"):
        """原文→訳文を、idで書いた done ファイルにして取り込む。"""
        done = self.work / language / "done-001.json"
        done.parent.mkdir(parents=True, exist_ok=True)
        done.write_text(json.dumps({localize.segment_id(source): translation
                                    for source, translation in translations.items()}, ensure_ascii=False), encoding="utf-8")
        return self.quiet(localize.merge, self.settings(), language, [done], self.work, overwrite)

    def catalog(self, name, language="en"):
        return localize.read_catalog(self.settings().catalog_path(language, name)).entries

    def write_overrides(self, overrides, name="docs/unit/index.html"):
        path = self.settings().catalog_path("en", name)
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {
            "source": name, "language": "en", "entries": [],
        }
        data["overrides"] = overrides
        self.write(path.relative_to(self.root), json.dumps(data, ensure_ascii=False))
        return path

    def test_sync_and_merge_preserve_overrides_without_sharing_them(self):
        self.sync()
        self.merge({"ここで止まって、確認": "Stop here and check"})
        path = self.write_overrides([{"source": "ここで止まって、確認", "where": "p", "translation": "Check your work"}])
        self.sync()
        result, _, errors = self.merge({"ここで止まって、確認": "Stop and check"}, overwrite=True)
        self.assertEqual(result, 0, errors)
        self.assertEqual(localize.read_catalog(path).overrides, {("ここで止まって、確認", "p"): "Check your work"})
        output = localize.localized_pages(self.settings(), "en")
        self.assertIn("<p>Check your work</p>", output["docs/en/unit/index.html"])
        self.assertIn("<p>Stop and check</p>", output["docs/en/common/setup.html"])
        self.assertEqual(self.catalog("docs/unit/index.html")["ここで止まって、確認"], "Stop and check")
        self.assertEqual(localize.check(self.settings()), [])

    def test_overrides_do_not_become_translation_memory_for_new_pages(self):
        self.write_overrides([{"source": "ここで止まって、確認", "where": "p", "translation": "Check your work"}])
        self.write("docs/other/index.html", "<p>ここで止まって、確認</p>")
        self.sync()
        self.assertEqual(self.catalog("docs/other/index.html"), {})
        self.assertIn("ここで止まって、確認", self.todo())
        output = localize.localized_pages(self.settings(), "en")
        self.assertEqual(output["docs/en/other/index.html"], "<p>ここで止まって、確認</p>")

    def test_changed_source_does_not_use_old_override_and_sync_removes_it(self):
        self.write("docs/unit/index.html", "<table><tr><th>コード</th></tr></table>")
        path = self.write_overrides([{"source": "コード", "where": "th", "translation": "Code"}])
        self.write("docs/unit/index.html", "<table><tr><th>完成コード</th></tr></table>")
        self.assertEqual(localize.check(self.settings()), [])
        row = next(row for row in localize.progress(self.settings(), ["en"])[0]["rows"] if row["page"] == "docs/unit/index.html")
        self.assertEqual((row["translated"], row["unused"]), (0, 1))
        output = localize.localized_pages(self.settings(), "en")["docs/en/unit/index.html"]
        self.assertIn("<th>完成コード</th>", output)
        self.sync()
        self.assertFalse(path.exists())
        self.assertIn("完成コード", self.todo())

    def test_invalid_location_is_reported_and_not_silently_removed_by_sync(self):
        self.merge({"単元": "Unit"})
        path = self.write_overrides([{"source": "単元", "where": "th", "translation": "Lesson"}])
        self.assertIn("この原文が指定された場所にありません", "\n".join(localize.check(self.settings())))
        self.sync()
        self.assertEqual(localize.read_catalog(path).overrides, {("単元", "th"): "Lesson"})
        self.assertIn("この原文が指定された場所にありません", "\n".join(localize.check(self.settings())))

    def test_invalid_or_duplicate_override_is_rejected(self):
        override = {"source": "単元", "where": "title", "translation": "Unit"}
        for value in ({}, [{"source": "単元", "translation": "Unit"}],
                      [{**override, "where": None}], [override, override]):
            with self.subTest(overrides=value):
                path = self.write_overrides(value)
                self.assertTrue(localize.check(self.settings()))
                with self.assertRaises(localize.LocalizeError):
                    localize.read_catalog(path)

    def test_override_translation_uses_the_same_validation_as_defaults(self):
        self.write_overrides([{"source": "<code>Run</code>を押します。", "where": "p", "translation": "Press Start."}])
        self.assertIn("訳文にタグが足りません", "\n".join(localize.check(self.settings())))

    def test_sync_and_merge_repair_an_invalid_override(self):
        source = "<code>Run</code>を押します。"
        self.write_overrides([{"source": source, "where": "p", "translation": "Press Start."}])
        self.assertIn("訳文にタグが足りません", "\n".join(localize.check(self.settings())))
        self.sync()
        self.assertIn(source, self.todo())
        result, _, errors = self.merge({source: "Press <code>Run</code>."})
        self.assertEqual(result, 0, errors)
        self.assertEqual(localize.check(self.settings()), [])
        output = localize.localized_pages(self.settings(), "en")["docs/en/unit/index.html"]
        self.assertIn("Press <code>Run</code>.", output)
        self.assertNotIn("Press Start.", output)

    def test_progress_counts_only_sources_translated_in_every_location(self):
        self.write("docs/unit/index.html", "<table><tr><th>コード</th><td>コード</td></tr></table>")
        self.write_overrides([{"source": "コード", "where": "th", "translation": "Code"}])
        rows = {row["page"]: row for row in localize.progress(self.settings(), ["en"])[0]["rows"]}
        self.assertEqual((rows["docs/unit/index.html"]["total"], rows["docs/unit/index.html"]["translated"]), (1, 0))
        self.sync()
        self.assertIn("コード", self.todo())
        self.write("docs/unit/index.html", "<section id=\"step-8\"><table><tr><th>コード</th></tr></table></section>")
        self.sync()
        self.assertNotIn("コード", self.todo())
        self.assertEqual(localize.check(self.settings()), [])
        rows = {row["page"]: row for row in localize.progress(self.settings(), ["en"])[0]["rows"]}
        self.assertEqual((rows["docs/unit/index.html"]["translated"], rows["docs/unit/index.html"]["unused"]), (1, 0))

    def test_legacy_catalog_round_trip_does_not_add_overrides(self):
        self.merge({"単元": "Unit"})
        path = self.settings().catalog_path("en", "docs/unit/index.html")
        before = path.read_bytes()
        catalog = localize.read_catalog(path)
        self.assertEqual(catalog.overrides, {})
        localize.write_catalog(path, "docs/unit/index.html", "en", catalog, ["単元"])
        self.assertEqual(path.read_bytes(), before)

    def test_sync_writes_work_files_and_merge_fills_every_page_with_the_same_source(self):
        self.sync()
        todo = self.todo()
        self.assertEqual(list(todo), ["ここで止まって、確認", "準備をします。", "単元", "はじめての単元", "<code>Run</code>を押します。"])
        self.assertEqual(todo["単元"]["where"], "title")
        # 2つのページにある文は、作業ファイルには1回だけ出す。1回訳せば、両方のページに入る。
        listed = [item["source"] for path in sorted(self.work.rglob("todo-*.json"))
                  for item in json.loads(path.read_text(encoding="utf-8"))["segments"]]
        self.assertEqual(listed.count("ここで止まって、確認"), 1)
        self.assertFalse((self.root / "i18n").exists())  # 訳が1つもないカタログは置かない

        result, _, _ = self.merge({"ここで止まって、確認": "Stop here and check", "はじめての単元": "Your first unit"})
        self.assertEqual(result, 0)
        self.assertEqual(self.catalog("docs/common/setup.html"), {"ここで止まって、確認": "Stop here and check"})
        # 文書に出てくる順で書く。
        self.assertEqual(list(self.catalog("docs/unit/index.html")), ["はじめての単元", "ここで止まって、確認"])
        data = json.loads((self.root / "i18n/en/unit/index.json").read_text(encoding="utf-8"))
        self.assertEqual((data["source"], data["language"]), ("docs/unit/index.html", "en"))

    def test_sync_reuses_translation_from_another_page(self):
        self.sync()
        self.merge({"ここで止まって、確認": "Stop here and check"})
        self.write("docs/other/index.html", '<html lang="ja"><body><p>ここで止まって、確認</p><p>新しい文</p></body></html>')
        self.sync()
        self.assertEqual(self.catalog("docs/other/index.html"), {"ここで止まって、確認": "Stop here and check"})
        self.assertIn("新しい文", self.todo())
        self.assertNotIn("ここで止まって、確認", self.todo())

    def test_changed_source_becomes_untranslated_and_old_translation_is_offered_as_hint(self):
        self.sync()
        self.merge({"準備をします。": "Get ready."})
        self.write("docs/common/setup.html", '<html lang="ja"><body><p>ここで止まって、確認</p><p>先に準備をします。</p></body></html>')
        self.sync()
        self.assertEqual(self.catalog("docs/common/setup.html"), {})  # 古い訳は外れる。学生には届かない
        item = self.todo()["先に準備をします。"]
        self.assertEqual((item["previous_source"], item["previous_translation"]), ("準備をします。", "Get ready."))
        settings = self.settings()
        html = localize.localized_pages(settings, "en")["docs/en/common/setup.html"]
        self.assertIn("<p>先に準備をします。</p>", html)

    def test_merge_rejects_invalid_translations_but_keeps_valid_ones(self):
        self.sync()
        result, _, errors = self.merge({"<code>Run</code>を押します。": "Press <code>Start</code>.", "単元": "Unit"})
        self.assertEqual(result, 1)
        self.assertIn("中身が、原文と違います", errors)
        self.assertEqual(self.catalog("docs/unit/index.html"), {"単元": "Unit"})

    def test_merge_dry_run_checks_without_writing(self):
        self.sync()
        done = self.work / "en/done-001.json"
        done.write_text(json.dumps({localize.segment_id("単元"): "Unit", localize.segment_id("準備をします。"): ""}), encoding="utf-8")
        result, output, errors = self.quiet(localize.merge, self.settings(), "en", [done], self.work, False, True)
        self.assertEqual(result, 1)
        self.assertIn("検査に通った訳 1、カタログに入る数 1（--dry-run なので、入れていません）", output)
        self.assertIn("訳文が空です", errors)
        self.assertFalse((self.root / "i18n").exists())

    def translate_work(self, language="en", prefix="EN: "):
        """作業ファイルの隣に、訳した結果を書く（訳す担当がやることと同じ形）。"""
        written = []
        for todo in sorted((self.work / language).rglob("todo-*.json")):
            data = json.loads(todo.read_text(encoding="utf-8"))
            done = todo.with_name(todo.name.replace("todo-", "done-", 1))
            done.write_text(json.dumps({item["id"]: prefix + item["source"] for item in data["segments"]},
                                       ensure_ascii=False), encoding="utf-8")
            written.append(done)
        return written

    def test_merge_ignores_finished_files_left_over_from_an_earlier_sync(self):
        # 前の回の done-*.json が残っていても、相手の todo がないので取り込まない。
        # これがないと、カタログを手で直した訳が古い訳に巻き戻る。
        self.sync()
        self.translate_work()
        self.quiet(localize.merge, self.settings(), "en", [], self.work, False)
        catalog = self.settings().catalog_path("en", "docs/unit/index.html")
        entries = localize.read_catalog(catalog).entries
        self.assertEqual(entries["はじめての単元"], "EN: はじめての単元")

        # 1文だけ手で直し、別の1文の日本語を直して、もう一度 sync する。
        entries["はじめての単元"] = "EN hand-fixed"
        localize.write_catalog(catalog, "docs/unit/index.html", "en", localize.Catalog(entries), list(entries))
        self.write("docs/unit/index.html", (
            '<html lang="ja"><head><link rel="stylesheet" href="../assets/textbook.css"><title>単元</title></head>'
            "<body><h1>はじめての単元</h1><p>ここで止まって、確認</p><p>直した文です。</p></body></html>"
        ))
        self.sync()
        # 取り込み前の訳を失わないよう、古い done は残す。
        self.assertTrue(sorted(self.work.rglob("done-*.json")))
        self.translate_work()
        result, output, _ = self.quiet(localize.merge, self.settings(), "en", [], self.work, True)

        self.assertEqual(result, 0)
        self.assertEqual(localize.read_catalog(catalog).entries["はじめての単元"], "EN hand-fixed")
        self.assertEqual(localize.read_catalog(catalog).entries["直した文です。"], "EN: 直した文です。")
        self.assertIn("読み飛ばした", output)

    def test_merge_accepts_a_translation_that_moved_to_another_work_file(self):
        # sync のたびに文の分け方は変わる。done-001 の訳が todo-002 に移っても取り込む。
        self.sync()
        self.translate_work()
        moved = sorted(self.work.rglob("todo-*.json"))[0]
        moved.rename(moved.with_name("todo-009.json"))
        result, output, errors = self.quiet(localize.merge, self.settings(), "en", [], self.work, False)
        self.assertEqual(result, 0, errors)
        self.assertNotIn("読み飛ばした", output)
        self.assertEqual(localize.read_catalog(self.settings().catalog_path("en", "docs/unit/index.html")).entries["単元"],
                         "EN: 単元")

    def test_merge_skips_work_files_left_by_a_removed_page(self):
        # 単元を消しても作業ファイルは残る。その訳で merge 全体を失敗させない。
        self.write("docs/gone/index.html", '<html lang="ja"><body><p>消える単元の文。</p></body></html>')
        self.sync()
        self.translate_work()
        (self.root / "docs/gone/index.html").unlink()
        result, output, errors = self.quiet(localize.merge, self.settings(), "en", [], self.work, False)
        self.assertEqual(result, 0, errors)
        self.assertIn("読み飛ばした", output)
        self.assertEqual(localize.read_catalog(self.settings().catalog_path("en", "docs/unit/index.html")).entries["単元"],
                         "EN: 単元")

    def test_sync_drops_translations_that_no_longer_pass_the_check(self):
        # 用語集を足して検査に落ちるようになった訳は、訳し直しに回す。
        # 残すと、CIは赤いのに作業ファイルが1つも作られない。
        self.write("config/teaching-materials.json", json.dumps({"terms": []}))
        self.sync()
        self.merge({"<code>Run</code>を押します。": "Press <code>Run</code> in VSCode."})
        self.write("config/teaching-materials.json", json.dumps({"terms": TERMS}, ensure_ascii=False))
        self.assertNotEqual(localize.check(self.settings()), [])
        self.sync()
        self.assertEqual(self.catalog("docs/unit/index.html"), {})
        item = self.todo()["<code>Run</code>を押します。"]
        self.assertIn("VSCode", item["previous_translation"])
        self.assertEqual(localize.check(self.settings()), [])

    def test_check_finds_the_same_source_translated_two_ways(self):
        # 同じ原文はどのページでも同じ訳、というのがこのしくみの約束。
        # カタログを手で直すと、1ページずつの検査では食い違いに気付けない。
        self.sync()
        self.merge({"ここで止まって、確認": "Stop here and check"})
        path = self.settings().catalog_path("en", "docs/common/setup.html")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entries"][0]["translation"] = "When you need help"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.assertIn("同じ原文に、別の訳が付いています", "\n".join(localize.check(self.settings())))

    def test_build_replaces_pages_left_over_from_an_earlier_run(self):
        self.sync()
        self.merge({"はじめての単元": "Your first unit"})
        output = self.root / "dist/i18n-preview"
        self.quiet(localize.build, self.settings(), ["en"], output)
        stale = output / "docs/en/gone/index.html"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("<p>消した単元</p>", encoding="utf-8")
        self.quiet(localize.build, self.settings(), ["en"], output)
        self.assertFalse(stale.exists())
        self.assertTrue((output / "docs/en/unit/index.html").is_file())

    def test_catalog_with_the_same_source_twice_is_rejected(self):
        # 後の訳で上書きすると、前の訳が黙って消える。
        self.write("i18n/en/unit/index.json", json.dumps({"source": "docs/unit/index.html", "language": "en", "entries": [
            {"source": "単元", "translation": "Unit"}, {"source": "単元", "translation": "Lesson"},
        ]}, ensure_ascii=False))
        with self.assertRaisesRegex(localize.LocalizeError, "同じ原文が2回あります"):
            localize.progress(self.settings(), ["en"])

    def test_merge_reports_unknown_id(self):
        done = self.work / "en/done-001.json"
        done.parent.mkdir(parents=True)
        done.write_text('{"000000000000": "x"}', encoding="utf-8")
        result, _, errors = self.quiet(localize.merge, self.settings(), "en", [done], self.work, False)
        self.assertEqual(result, 1)
        self.assertIn("このidの原文がありません", errors)

    def test_merge_does_not_replace_existing_translation_without_overwrite(self):
        self.sync()
        self.merge({"単元": "Unit"})
        _, output, _ = self.merge({"単元": "Lesson"})
        self.assertIn("入れなかった数 1", output)
        self.assertEqual(self.catalog("docs/unit/index.html")["単元"], "Unit")
        self.merge({"単元": "Lesson"}, overwrite=True)
        self.assertEqual(self.catalog("docs/unit/index.html")["単元"], "Lesson")

    def test_check_ignores_untranslated_and_unused_entries_but_finds_broken_catalogs(self):
        self.sync()
        self.merge({"単元": "Unit", "準備をします。": "Get ready."})
        # 日常のPRで日本語が変わっても、検査は落ちない。
        self.write("docs/common/setup.html", '<html lang="ja"><body><p>書き直した文</p></body></html>')
        self.assertEqual(localize.check(self.settings()), [])

        self.write("i18n/en/unit/index.json", json.dumps({"source": "docs/unit/other.html", "language": "fr", "entries": [
            {"source": "単元", "translation": "Unit"}, {"source": "単元", "translation": "Unit"},
            {"source": "<code>Run</code>を押します。", "translation": "Press Run."}, {"source": "確認"},
        ]}, ensure_ascii=False))
        self.write("i18n/de/unit/index.json", "{}")
        self.write("i18n/en/common/setup.json", "{")
        errors = "\n".join(localize.check(self.settings()))
        self.write("i18n/fr/unit/index.json", json.dumps({"source": "docs/unit/index.html", "language": "fr", "entries": [
            {"source": " 単元 ", "translation": "Unite"},
        ]}, ensure_ascii=False))
        self.write("i18n/fr/common/setup.json", json.dumps({"source": "docs/common/setup.html", "language": "fr", "entries": []}))
        errors = "\n".join(localize.check(self.settings()))
        for message in ("language がフォルダの名前と違います", "source がファイルの場所と違います", "同じ原文が2回あります",
                        "訳文にタグが足りません", "source と translation の組になっていません",
                        "config/i18n.jsonにない言語のフォルダです: de", "JSONとして読み込めません",
                        "原文に余分な空白や改行があります", "entries がありません"):
            self.assertIn(message, errors)

    def test_check_reports_html_that_cannot_be_extracted(self):
        self.write("docs/unit/index.html", "<div><p>閉じていない</div>")
        self.assertIn("docs/unit/index.html:1: 開始タグと終了タグが対応していません", "\n".join(localize.check(self.settings())))

    def test_status_counts_and_require_complete_only_looks_at_distributed_languages(self):
        self.sync("en", "fr")
        self.merge({"単元": "Unit"})
        report = localize.progress(self.settings(), ["en"])[0]
        self.assertEqual({row["page"]: (row["translated"], row["total"]) for row in report["rows"]},
                         {"docs/common/setup.html": (0, 2), "docs/unit/index.html": (1, 4)})
        summary = self.root / "summary.md"
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
            result, _, errors = self.quiet(localize.status, self.settings(), ["en", "fr"], True)
            self.assertEqual(result, 1)
            self.assertIn("en: 未翻訳 5", errors)
            self.assertNotIn("fr", errors)
            self.assertEqual(self.quiet(localize.status, self.settings(), ["en", "fr"], False)[0], 0)
            self.assertEqual(self.quiet(localize.status, self.settings(), ["fr"], True)[0], 0)
        self.assertIn("| en（English） | 対象 | 1 / 6 | 5 | 0 |", summary.read_text(encoding="utf-8"))

    def test_status_counts_translations_left_over_after_the_japanese_changed(self):
        # 日本語を直すと、その訳は「使っていない訳」になる。check は見逃す設計なので、
        # 古い訳に気付く道は、status のこの数字だけ。
        self.sync()
        self.merge({"単元": "Unit"})
        self.write("docs/unit/index.html",
                   '<html lang="ja"><head><title>直した題名</title></head><body><h1>直した見出し</h1></body></html>')
        rows = {row["page"]: row for row in localize.progress(self.settings(), ["en"])[0]["rows"]}
        self.assertEqual(rows["docs/unit/index.html"]["unused"], 1)
        self.assertEqual(rows["docs/unit/index.html"]["translated"], 0)
        self.assertEqual(localize.check(self.settings()), [])  # check は落とさない

    def test_status_lists_catalog_without_page(self):
        self.write("i18n/en/gone/index.json", json.dumps({"source": "docs/gone/index.html", "language": "en",
                                                          "entries": [{"source": "古い文", "translation": "Old"}]}, ensure_ascii=False))
        self.assertEqual(localize.progress(self.settings(), ["en"])[0]["orphans"], ["i18n/en/gone/index.json"])

    def test_build_writes_language_folder_next_to_copied_docs(self):
        self.sync()
        self.merge({"はじめての単元": "Your first unit"})
        output = self.root / "dist/i18n-preview"
        self.quiet(localize.build, self.settings(), ["en"], output)
        html = (output / "docs/en/unit/index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)
        self.assertIn("<h1>Your first unit</h1>", html)
        self.assertIn('href="../../assets/textbook.css"', html)
        self.assertTrue((output / "docs/assets/textbook.css").is_file())
        # 確認用ページでも、コピーボタンなどがその言語の文言で出る（配布物と同じ渡し方）。
        payload = html.split('id="textbook-i18n">')[1].split("</script>")[0]
        self.assertEqual(json.loads(payload)["copy"], "Copy")
        # 言語の切り替えと翻訳の注記は配布物だけのもの。確認用ページには入れない。
        self.assertNotIn("language-nav", html)
        self.assertNotIn("translation-note", html)
        with self.assertRaisesRegex(localize.LocalizeError, "リポジトリの直下には作れません"):
            localize.build(self.settings(), ["en"], self.root)

    def test_generated_language_folder_is_not_a_source_page(self):
        self.write("docs/en/unit/index.html", "<p>generated</p>")
        self.assertEqual(self.settings().page_names(), ["docs/common/setup.html", "docs/unit/index.html"])

    def test_unknown_language_is_rejected(self):
        with self.assertRaisesRegex(localize.LocalizeError, "config/i18n.jsonにない言語です: de"):
            localize.localized_pages(self.settings(), "de")

    def test_localized_pages_uses_configured_official_documentation_language(self):
        source = '<p><a href="https://developer.android.com/studio?hl=ja">公式資料</a>を開く。</p>'
        self.write("docs/unit/index.html", source)
        config_path = self.root / "config/i18n.json"
        config = json.loads(config_path.read_text())
        config["languages"][1]["android_docs_hl"] = "fr"
        config_path.write_text(json.dumps(config))
        rendered = localize.localized_pages(self.settings(), "fr")["docs/fr/unit/index.html"]
        self.assertIn("?hl=fr", rendered)
        self.assertEqual((self.root / "docs/unit/index.html").read_text(), source)
        # 明示の対応がない言語は、存在が確認できる英語に戻す。
        config["languages"][1].pop("android_docs_hl")
        config_path.write_text(json.dumps(config))
        self.assertIn("?hl=en", localize.localized_pages(self.settings(), "fr")["docs/fr/unit/index.html"])

    def add_right_to_left_language(self):
        path = self.root / "config/i18n.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["languages"].append({"code": "ar", "name": "العربية", "distribute": False, "dir": "rtl",
                                    "ui": ui("نسخ")})
        path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    def test_direction_comes_from_the_configuration(self):
        self.add_right_to_left_language()
        settings = self.settings()
        self.assertEqual(settings.direction("ar"), "rtl")
        # 書かなかった言語と、原文の日本語は左から右。
        self.assertEqual(settings.direction("en"), "ltr")
        self.assertEqual(settings.direction("ja"), "ltr")

    def test_invalid_direction_is_rejected(self):
        config_path = self.root / "config/i18n.json"
        config = json.loads(config_path.read_text())
        for value in ("RTL", "auto", "", 1, None):
            with self.subTest(value=value):
                config["languages"][0]["dir"] = value
                config_path.write_text(json.dumps(config))
                with self.assertRaisesRegex(localize.LocalizeError, "en の dir は ltr か rtl"):
                    self.settings()

    def test_build_writes_right_to_left_pages_and_marks_untranslated_text(self):
        """確認用ページも、配布物と同じく、未翻訳の文を日本語と示し、向きを付けて出す。"""
        self.add_right_to_left_language()
        self.sync("ar")
        self.merge({"はじめての単元": "الوحدة الأولى"}, language="ar")
        output = self.root / "dist/i18n-preview"
        self.quiet(localize.build, self.settings(), ["ar", "en"], output)
        arabic = (output / "docs/ar/unit/index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="ar" dir="rtl">', arabic)
        self.assertIn("<h1>الوحدة الأولى</h1>", arabic)
        self.assertIn('<p><span lang="ja" dir="ltr">ここで止まって、確認</span></p>', arabic)
        self.assertIn('<title lang="ja" dir="ltr">単元</title>', arabic)
        english = (output / "docs/en/unit/index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', english)
        self.assertIn('<p><span lang="ja">ここで止まって、確認</span></p>', english)

    def test_invalid_official_documentation_language_is_rejected(self):
        config_path = self.root / "config/i18n.json"
        config = json.loads(config_path.read_text())
        for value in ("", "en&other=1", 123):
            with self.subTest(value=value):
                config["languages"][0]["android_docs_hl"] = value
                config_path.write_text(json.dumps(config))
                with self.assertRaisesRegex(localize.LocalizeError, "android_docs_hl"):
                    self.settings()


# 右から左のページ（<html dir="rtl">）だけに当てるセレクタ。このブロックの中は、左右を決め打ちしてよい（AGENTS.md §12）。
RTL_ONLY_SELECTOR = re.compile(r"\[dir=[\"']?rtl[\"']?\]")
# 4つの値を「上 右 下 左」の順に書くまとめ書き。2つ目（右）と4つ目（左）が違えば、左右の決め打ちになる。
FOUR_SIDES_SHORTHANDS = {"margin", "padding", "inset", "border-width", "border-style", "border-color",
                         "scroll-margin", "scroll-padding"}
# 値に left・right の語が入るもの（text-align: left、background-position: left center、linear-gradient(to right, …) など）と、
# 横に動かす translateX()。--left-gap のような名前の一部は、語ではないので数えない。
SIDE_IN_VALUE = re.compile(r"(?<![\w-])(?:left|right)(?![\w-])|translatex\(")


def fixed_direction_declarations(css):
    """CSSから、左右を決め打ちした宣言を「プロパティ: 値」の形で集める。大文字と小文字は区別しない。

    落とすのは次の書き方。
    - プロパティ名に left・right が入るもの（left、margin-left、border-left-width、border-top-left-radius など）
    - 4つの値を書いた margin・padding・inset・border-width・border-style・border-color・scroll-margin・scroll-padding で、
      2つ目（右）と4つ目（左）の値が違うもの。1〜3つの値の書き方は、左右が必ず同じ値になる
    - border-radius で、左の角と右の角の値が違うもの。2つの値でも、左上と右上が違えば落とす
    - 値に left・right の語が入るもの（text-align・float・clear のほか、background-position・transform-origin・
      justify-content など）と、transform の translateX()
    [dir="rtl"] で絞ったブロックは、右から左のページだけに当てるものなので調べない。
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL).lower()
    found = []
    # 宣言があるのは、いちばん内側のブロックだけ。@media { .a { … } } の .a も、この形で見つかる。
    for block in re.finditer(r"([^{}]*)\{([^{}]*)\}", css):
        selector, body = block.groups()
        # 「[dir="rtl"] code, [dir="rtl"] kbd」のように、並べたセレクタの全部が絞られているときだけ飛ばす。
        if all(RTL_ONLY_SELECTOR.search(part) for part in selector.split(",")):
            continue
        for declaration in body.split(";"):
            if ":" not in declaration:
                continue
            name, value = declaration.split(":", 1)
            name = name.strip()
            value = re.sub(r"\s*!\s*important$", "", " ".join(value.split()))
            if fixes_a_side(name, value):
                found.append(f"{name}: {value}")
    return found


def fixes_a_side(name, value):
    """宣言1つが、左右を決め打ちしているかを返す。name と value は小文字にそろえてある。"""
    if "left" in name.split("-") or "right" in name.split("-"):
        return True
    if SIDE_IN_VALUE.search(value):
        return True
    if name in FOUR_SIDES_SHORTHANDS:
        top, right, bottom, left = four_values(values_of(value))
        return right != left
    if name == "border-radius":
        # 「横の半径 / 縦の半径」の形は、それぞれの側で左右の角をそろえる。
        for radii in radius_groups(value):
            top_left, top_right, bottom_right, bottom_left = four_values(values_of(radii))
            if top_left != top_right or bottom_left != bottom_right:
                return True
    return False


def values_of(value):
    """値を空白で区切る。calc(1rem + 2px) や var(--x, 0) のように、かっこの中の空白では区切らない。"""
    return [each for each in split_outside_parentheses(value, str.isspace) if each]


def radius_groups(value):
    """border-radius の値を「横の半径 / 縦の半径」に分ける。calc(10px / 2) のような、かっこの中の / では分けない。"""
    return split_outside_parentheses(value, "/".__eq__)


def split_outside_parentheses(value, is_separator):
    """value を、かっこの外にある区切り文字（is_separator が真になる文字）で分ける。"""
    parts, depth = [""], 0
    for character in value:
        depth += (character == "(") - (character == ")")
        if depth == 0 and is_separator(character):
            parts.append("")
        else:
            parts[-1] += character
    return parts


def four_values(values):
    """1〜4つの値を、CSSのまとめ書きの決まりどおりに4つへ広げる。

    1つなら4辺とも同じ、2つなら「上下 左右」（border-radius では「左上と右下 右上と左下」）、
    3つなら2つ目を4つ目にも使う。0個や5個以上（CSSとしては誤り）でも、呼び出し側が数を気にしなくてよいよう、
    長さは4つにそろえる。
    """
    if not values:
        return [""] * 4
    if len(values) == 2:
        values = values * 2
    elif len(values) == 3:
        values = values + values[1:2]
    return (values + values[:1] * 4)[:4]


class TextbookCssTest(unittest.TestCase):
    """教科書のCSSの左右の検査（fixed_direction_declarations）を、見本のCSSで確かめる。"""

    def test_declarations_that_fix_a_side_are_found(self):
        # issue #77 の表の12行（古い正規表現は、最初の1行しか捕まえなかった）と、同じ種類の書き方。
        cases = {
            ".a{border-left:4px solid}": "border-left: 4px solid",
            ".a{padding:0 0 0 1.5rem}": "padding: 0 0 0 1.5rem",
            ".a{margin:0 2rem 0 0}": "margin: 0 2rem 0 0",
            ".a{border-width:0 0 0 4px}": "border-width: 0 0 0 4px",
            ".a{border-radius:9px 0 0 9px}": "border-radius: 9px 0 0 9px",
            ".a{border-top-left-radius:4px}": "border-top-left-radius: 4px",
            ".a{inset:0 auto auto 0}": "inset: 0 auto auto 0",
            ".a{background-position:left center}": "background-position: left center",
            ".a{transform-origin:left}": "transform-origin: left",
            ".a{transform:translateX(-100%)}": "transform: translatex(-100%)",
            ".a{justify-content:left}": "justify-content: left",
            ".a{Text-Align:Left}": "text-align: left",
            ".a{left:0}": "left: 0",
            ".a{right:0}": "right: 0",
            ".a{margin-right:auto}": "margin-right: auto",
            ".a{scroll-padding-left:1rem}": "scroll-padding-left: 1rem",
            ".a{-webkit-border-top-left-radius:4px}": "-webkit-border-top-left-radius: 4px",
            ".a{float:right}": "float: right",
            ".a{clear:left}": "clear: left",
            ".a{border-style:none solid none none}": "border-style: none solid none none",
            ".a{border-color:red blue red green}": "border-color: red blue red green",
            ".a{scroll-margin:0 1rem 0 0}": "scroll-margin: 0 1rem 0 0",
            ".a{border-radius:9px 0}": "border-radius: 9px 0",
            ".a{border-radius:9px 0 0}": "border-radius: 9px 0 0",
            ".a{border-radius:9px 9px 0 0 / 5px 0 0 5px}": "border-radius: 9px 9px 0 0 / 5px 0 0 5px",
            ".a{border-radius:calc(10px / 2) 0 0 0}": "border-radius: calc(10px / 2) 0 0 0",
            ".a{border-radius:calc(8px / 2) 0 / 4px}": "border-radius: calc(8px / 2) 0 / 4px",
            ".a{background:url(x.png) left top no-repeat}": "background: url(x.png) left top no-repeat",
            ".a{background:linear-gradient(to right, red, blue)}": "background: linear-gradient(to right, red, blue)",
            ".a{margin:0 1rem 0 0 !important}": "margin: 0 1rem 0 0",
            ".a{padding:0 var(--x, 0) 0 calc(1rem + 2px)}": "padding: 0 var(--x, 0) 0 calc(1rem + 2px)",
            ".a{margin:0\n  2rem\n  0\n  0}": "margin: 0 2rem 0 0",
            "@media (max-width: 720px) { .a { padding: 0 0 0 1rem; } }": "padding: 0 0 0 1rem",
            "@media print { @page { margin: 0 1cm 0 0; } }": "margin: 0 1cm 0 0",
            ".a{color:red;border-left:1px solid;margin:0}": "border-left: 1px solid",
            ".a{border-left:1px solid;padding:0 0 0 1rem}": "border-left: 1px solid",
        }
        for css, declaration in cases.items():
            with self.subTest(css=css):
                self.assertEqual(fixed_direction_declarations(css)[:1], [declaration])
        self.assertEqual(fixed_direction_declarations(".a{border-left:1px solid;padding:0 0 0 1rem}"),
                         ["border-left: 1px solid", "padding: 0 0 0 1rem"])

    def test_symmetric_declarations_pass(self):
        # 今の textbook.css にある書き方と、左右が同じ値になるまとめ書き。
        declarations = [
            "padding: .4rem .55rem", "margin: .2rem 0 1rem", "margin: -1px", "margin: 0 auto", "margin: 16mm",
            "padding: 0 1rem 0 1rem", "margin: 0 calc(1rem + 2px) 0 calc(1rem + 2px)", "padding: 0 var(--x, 0) 0 var(--x, 0)",
            "border-radius: 0 0 9px 9px", "border-radius: 9px 9px 0 0", "border-radius: 9px", "border-radius: 9px 9px",
            "border-radius: 9px 9px 9px", "border-radius: 9px 9px 0 0 / 5px 5px 0 0", "border-radius: 9px/5px",
            "border-radius: calc(10px / 2)", "border-radius: calc(10px / 2) calc(10px / 2) 0 0",
            "border-radius: calc(8px / 2) / calc(4px / 2)", "border-radius: 9px 9px 0 0 / calc(10px / 2) calc(10px / 2) 0 0",
            "border-width: 0 1px 2px 1px", "border-style: solid", "inset: 0", "clip-path: inset(50%)",
            "scroll-padding-top: calc(var(--language-nav-height, 0px) + 1.5rem)",
            "justify-content: flex-end", "justify-content: space-between", "text-align: start", "text-align: center",
            "inset-inline-start: 1rem", "border-inline-start: 4px solid var(--blue)", "border-inline-end: 0",
            "padding-inline-start: 1.5rem", "border-bottom-width: 2px", "margin-top: .4rem", "margin-bottom: 1.25rem",
            "border-start-start-radius: 9px", "display: none !important", "margin: 0 1rem 0 1rem !important",
            "transform: scaleX(-1)", "transform: translateY(-50%)", "letter-spacing: -.04em",
            "font-family: \"Hiragino Kaku Gothic ProN\", sans-serif", "gap: .3rem .6rem",
        ]
        for declaration in declarations:
            with self.subTest(declaration=declaration):
                self.assertEqual(fixed_direction_declarations(f".a {{ {declaration}; }}"), [])
        self.assertEqual(fixed_direction_declarations("@media print { @page { margin: 16mm; } .a { padding: 0; } }"), [])
        self.assertEqual(fixed_direction_declarations("/* border-left: 4px solid */ .a { text-align: start; }"), [])
        self.assertEqual(fixed_direction_declarations(".a { color: red } /* text-align: left */"), [])

    def test_rules_for_right_to_left_pages_only_are_skipped(self):
        for css in ['[dir="rtl"] .back-arrow { display: inline-block; transform: scaleX(-1); }',
                    '[dir="rtl"] .a { transform: translateX(-100%); }',
                    "[dir=rtl] .a { border-left: 4px solid; }",
                    "[dir='rtl'] .a { text-align: left; }",
                    '[dir="rtl"] code, [dir="rtl"] kbd { direction: ltr; padding: 0 0 0 1rem; }',
                    '@media print { [dir="rtl"] .a { float: left; } }']:
            with self.subTest(css=css):
                self.assertEqual(fixed_direction_declarations(css), [])
        # 絞られていないブロックは落とす。並べたセレクタの1つでも絞られていなければ、全ページに当たる。
        self.assertEqual(fixed_direction_declarations(".a { transform: translateX(-100%); }"),
                         ["transform: translatex(-100%)"])
        self.assertEqual(fixed_direction_declarations('[dir="rtl"] .a, .b { border-left: 4px solid; }'),
                         ["border-left: 4px solid"])
        self.assertEqual(fixed_direction_declarations('[dir="rtl"] .a { padding: 0; } .b { float: right; }'),
                         ["float: right"])


class RepositoryTest(unittest.TestCase):
    """実際の教材と対訳カタログで確かめる。"""

    @classmethod
    def setUpClass(cls):
        cls.settings = localize.load_settings(SCRIPTS.parent)

    def test_every_page_can_be_extracted_and_catalogs_are_valid(self):
        self.assertEqual(localize.check(self.settings), [])

    # 参照リポジトリにあった「英語の見出しと版の表が、用語集と混ざらない」テストは移植していない。
    # このリポジトリは翻訳が1文もない状態から始まる（config/i18n.json の distribute は全言語 false）ため、
    # 英語の訳文が入っていることを前提にした検査は、翻訳を始めるまで成り立たない。
    # 最初の言語の翻訳を入れるissueで、そのときの単元名に合わせて書き直す。

    def test_textbook_css_does_not_fix_left_or_right(self):
        """右から左の言語のページで左右が入れ替わるよう、教科書のCSSは論理プロパティで書く。

        border-left などで書くと、アラビア語のページでも枠線や字下げが左に残る。
        落とす書き方は fixed_direction_declarations にあり、TextbookCssTest が見本のCSSで確かめている。
        """
        css = (self.settings.root / self.settings.source_root / "assets/textbook.css").read_text(encoding="utf-8")
        self.assertEqual(fixed_direction_declarations(css), [])

    def test_code_blocks_are_identical_in_every_language(self):
        # <pre> とソースのバイト一致（check-teaching-materials.py）が、どの言語でも保たれる。
        blocks = re.compile(r"<pre.*?</pre>", re.DOTALL)
        for code in self.settings.codes():
            for name, text in localize.localized_pages(self.settings, code).items():
                source = posixpath_source(name, code)
                original = (self.settings.root / source).read_text(encoding="utf-8")
                direction = ' dir="rtl"' if self.settings.direction(code) == "rtl" else ""
                with self.subTest(page=name):
                    self.assertEqual(blocks.findall(text), blocks.findall(original))
                    self.assertIn(f'<html lang="{code}"{direction}>', text)


def posixpath_source(name, code):
    return name.replace(f"docs/{code}/", "docs/", 1)


if __name__ == "__main__":
    unittest.main()
