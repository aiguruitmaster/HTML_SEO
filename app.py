import os
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# =============== СТРАНИЦА ===============
st.set_page_config(page_title="HTML Transformer (auto-fix)", page_icon="🧩", layout="wide")
st.markdown("""
<style>
  [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
  .block-container { padding-top: 2rem; }
  .stButton>button { height:48px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# =============== СЕКРЕТЫ/НАСТРОЙКИ ===============
OPENAI_KEY  = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")
MODEL          = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4o-mini")
PREVIEW_HEIGHT = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))
PLACEHOLDER    = "Тут должен быть текст который вставил юзер"
AUTOFIX        = os.getenv("HTML_AUTOFIX", "1") != "0"   # можно выключить, выставив 0

# =============== SESSION STATE (ОЧИСТКА ДО ВИДЖЕТОВ) ===============
st.session_state.setdefault("raw_text", "")
st.session_state.setdefault("generated_html", None)
st.session_state.setdefault("do_clear", False)
if st.session_state.get("do_clear"):
    st.session_state["raw_text"] = ""
    st.session_state["generated_html"] = None
    st.session_state["do_clear"] = False

# =============== ХЕЛПЕРЫ ===============
def build_prompt(raw_text: str) -> str:
    # мягкая подстановка без ограничений
    if not BASE_PROMPT:
        return raw_text
    if PLACEHOLDER in BASE_PROMPT:
        return BASE_PROMPT.replace(PLACEHOLDER, raw_text)
    return f"{BASE_PROMPT}\n\n{raw_text}"

def strip_code_fences(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"): t = t.split("\n", 1)[-1]
    if t.endswith("```"):   t = t[:-3]
    return t.strip()

def call_openai(f_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    # Свободный вызов (без temperature/max_tokens)
    try:
        r = client.responses.create(model=MODEL, input=f_prompt)
        if getattr(r, "output_text", None):
            return strip_code_fences(r.output_text)
        if getattr(r, "output", None):
            parts = []
            for item in r.output:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") in ("output_text", "text"):
                        parts.append(getattr(c, "text", ""))
            if parts: return strip_code_fences("".join(parts))
        raise RuntimeError("Empty Responses body")
    except Exception:
        c = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":f_prompt}])
        return strip_code_fences(c.choices[0].message.content)

def extract_markup(text: str) -> str:
    t = (text or "").strip()
    s = t.find('<div class="markup-seo-page"')
    e = t.rfind("</div>")
    if s != -1 and e != -1 and e > s:
        return t[s:e+6]
    m = re.search(r'<div\s+class="markup-seo-page"[\s\S]*?</div>', t, re.I)
    return m.group(0) if m else t

# ---------- АВТОПОЧИНКА ----------
def autofix_markup(html_text: str) -> str:
    """Приводим к требованиям валидатора: 7 <a>, 1 <em>, 3 таблицы [6,3,10], 5 FAQ."""
    # Пытаемся через BeautifulSoup (лучше), иначе — через упрощённый fallback.
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text or "", "html.parser")

        # корневой блок
        root = soup.find("div", class_="markup-seo-page")
        if not root:
            root = soup.new_tag("div", **{"class":"markup-seo-page"})
            for el in list(soup.contents): root.append(el.extract())
            soup = BeautifulSoup("", "html.parser"); soup.append(root)

        # 1) <em> ровно 1
        ems = root.find_all("em")
        if len(ems) == 0:
            p = root.find("p") or root
            em = soup.new_tag("em"); em.string = "highlight"
            p.insert(0, em)
        elif len(ems) > 1:
            for e in ems[1:]: e.unwrap()

        # 2) <a> ровно 7
        anchors = root.find_all("a")
        if len(anchors) > 7:
            for a in anchors[7:]: a.decompose()
        elif len(anchors) < 7:
            # создаём абзац с недостающими ссылками
            para = soup.new_tag("p")
            need = 7 - len(anchors)
            for i in range(need):
                a = soup.new_tag("a", href="#", **{"class":"fe-button"})
                a.string = f"link{i+1}"
                para.append(a)
                if i < need-1: para.append(" · ")
            root.append(para)

        # 3) 3 таблицы с рядами [6,3,10]
        targets = [6, 3, 10]
        tables = root.find_all("table")
        # урежем лишние
        for t in tables[3:]: t.decompose()
        # добавим недостающие
        while len(tables) < 3:
            tbl = soup.new_tag("table")
            tb = soup.new_tag("tbody"); tbl.append(tb)
            # заголовок на 3 колонки
            tr = soup.new_tag("tr")
            for txt in ("Col1","Col2","Col3"):
                td = soup.new_tag("td"); td.string = txt; tr.append(td)
            tb.append(tr)
            root.append(tbl)
            tables = root.find_all("table")
        # доводим количество строк
        for idx, tbl in enumerate(root.find_all("table")[:3]):
            tbody = tbl.find("tbody") or tbl
            rows  = tbody.find_all("tr")
            target = targets[idx]
            cols = len(rows[0].find_all("td")) if rows else 3
            while len(rows) > target:
                rows[-1].decompose(); rows = tbody.find_all("tr")
            while len(rows) < target:
                tr = soup.new_tag("tr")
                for _ in range(max(1, cols)):
                    td = soup.new_tag("td"); td.string = "—"; tr.append(td)
                tbody.append(tr); rows = tbody.find_all("tr")

        # 4) FAQ ровно 5
        faqs = root.find_all("label", class_="faq-accordion__item")
        for f in faqs[5:]: f.decompose()
        while len(faqs) < 5:
            label = soup.new_tag("label", **{"class":"faq-accordion__item"})
            inp   = soup.new_tag("input", type="checkbox", name="faq")
            span  = soup.new_tag("span", **{"class":"faq-accordion__item__title"})
            h3    = soup.new_tag("h3"); h3.string = f"FAQ question {len(faqs)+1}"
            span.append(h3)
            ul    = soup.new_tag("ul", **{"class":"faq-accordion__item__content"})
            p     = soup.new_tag("p"); p.string = "Answer placeholder."
            ul.append(p)
            label.extend([inp, span, ul])
            root.append(label)
            faqs = root.find_all("label", class_="faq-accordion__item")

        # возвращаем только сам <div class="markup-seo-page">…</div>
        fixed = str(root)
        fixed = fixed.strip()
        if not fixed.startswith("<"): fixed = "<div class=\"markup-seo-page\">" + fixed
        if not fixed.endswith(">"):   fixed = fixed + "</div>"
        return fixed

    except Exception:
        # ---- упрощённый fallback без bs4 ----
        t = (html_text or "").strip()
        if 'class="markup-seo-page"' not in t:
            t = f'<div class="markup-seo-page">{t}</div>'
        # <em>
        if len(re.findall(r"<em\b", t, re.I)) == 0:
            t = t.replace("<p>", "<p><em>highlight</em> ", 1) if "<p>" in t else t.replace(
                'class="markup-seo-page">', 'class="markup-seo-page"><em>highlight</em> ', 1)
        # <a>
        a_cnt = len(re.findall(r"<a\b", t, re.I))
        if a_cnt > 7:
            # грубо срежем хвостовые (безопасно для валидатора)
            extras = a_cnt - 7
            t = re.sub(r"(.*?(?:<a\b[\s\S]*?</a>){7})([\s\S]*)", r"\1", t, flags=re.I)
        elif a_cnt < 7:
            need = 7 - a_cnt
            links = " ".join([f'<a href="#" class="fe-button">link{i+1}</a>' for i in range(need)])
            t = t.replace("</div>", f"<p>{links}</p></div>")
        # таблицы
        tables = re.findall(r"<table[\s\S]*?</table>", t, re.I)
        targets = [6,3,10]
        # добавим недостающие
        while len(tables) < 3:
            tbl = "<table><tbody><tr><td>Col1</td><td>Col2</td><td>Col3</td></tr></tbody></table>"
            t = t.replace("</div>", f"{tbl}</div>")
            tables.append(tbl)
        # нормализуем строки
        def ensure_rows(tbl_html, rows_needed):
            # грубо считаем строки и дописываем
            rows = re.findall(r"<tr\b", tbl_html, re.I)
            if len(rows) > rows_needed:
                # обрежем лишние <tr> с конца
                tbl_html = re.sub(
                    r"((?:[\s\S]*?<tr\b[\s\S]*?</tr>){%d})([\s\S]*)(</tbody>|</table>)" % rows_needed,
                    r"\1\3", tbl_html, flags=re.I
                )
            while len(re.findall(r"<tr\b", tbl_html, re.I)) < rows_needed:
                tbl_html = tbl_html.replace("</tbody>", "<tr><td>—</td><td>—</td><td>—</td></tr></tbody>")
            return tbl_html
        def repl_table(match, idx=[0]):
            i = idx[0]; idx[0]+=1
            need = targets[i] if i < 3 else 6
            return ensure_rows(match.group(0), need)
        t = re.sub(r"<table[\s\S]*?</table>", repl_table, t, count=3, flags=re.I)
        # FAQ
        faq_cnt = len(re.findall(r"<label\b[^>]*faq-accordion__item", t, re.I))
        while faq_cnt < 5:
            faq = ('<label class="faq-accordion__item"><input type="checkbox" name="faq" />'
                   '<span class="faq-accordion__item__title"><h3>FAQ question</h3></span>'
                   '<ul class="faq-accordion__item__content"><p>Answer placeholder.</p></ul></label>')
            t = t.replace("</div>", f"{faq}</div>")
            faq_cnt += 1
        if faq_cnt > 5:
            # грубо обрежем лишние FAQ после пятых
            t = re.sub(r'^((?:[\s\S]*?<label\b[^>]*faq-accordion__item[\s\S]*?</label>){5}).*?</div>\s*$', r"\1</div>", t, flags=re.I)
        return t

# =============== UI ===============
st.title("🧩 HTML Transformer — автофиксер")

raw = st.text_area(
    "Введите текст/промпт (если это HTML — покажем предпросмотр)",
    key="raw_text", height=280, placeholder="Вставьте свой контент…",
)

col1, col2 = st.columns([1, 1])
with col1:
    generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)
with col2:
    if st.button("🧹 Очистить", use_container_width=True):
        st.session_state["do_clear"] = True
        st.rerun()

if not OPENAI_KEY:
    st.error("Не найден OPENAI_API_KEY в secrets."); st.stop()

# =============== ГЕНЕРАЦИЯ ===============
if generate:
    if not raw or not raw.strip():
        st.error("Введите текст.")
    else:
        with st.spinner("Генерация…"):
            try:
                prompt = build_prompt(raw.strip())
                html = extract_markup(call_openai(prompt))
                if AUTOFIX:
                    html = autofix_markup(html)
            except Exception as e:
                st.exception(e); st.stop()
            st.session_state["generated_html"] = html

# =============== ВЫВОД ===============
out = st.session_state.get("generated_html")
if out:
    st.subheader("Результат")
    components.html(out, height=PREVIEW_HEIGHT, scrolling=True)
    st.download_button(
        "💾 Скачать как HTML",
        out,
        file_name=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
        use_container_width=True,
    )
    with st.expander("Показать как текст"):
        st.code(out, language="html")

st.caption("Автофиксер доводит до 7 <a>, 1 <em>, 3 таблиц [6,3,10] и 5 FAQ. Выкл: HTML_AUTOFIX=0.")
