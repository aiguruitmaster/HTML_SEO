import os
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# =====================
# Страница (без сайдбара)
# =====================
st.set_page_config(
    page_title="HTML Transformer (GPT-5)",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
      [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display: none !important; }
      .block-container { padding-top: 2rem; }
      .stButton>button { height: 48px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================
# Секреты и жёсткие настройки
# =====================
OPENAI_KEY  = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")

MODEL             = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4o-mini")  # ← поставь доступную модель
MAX_OUTPUT_TOKENS = int(os.getenv("HTML_MAX_OUTPUT_TOKENS", "2048"))
PREVIEW_HEIGHT    = int(os.getenv("HTML_PREVIEW_HEIGHT", "1400"))
MAX_RAW_CHARS     = int(os.getenv("HTML_MAX_RAW_CHARS", "200000"))
PLACEHOLDER       = "Тут должен быть текст который вставил юзер"

# =====================
# Хелперы
# =====================
def build_prompt(raw_text: str) -> str:
    if PLACEHOLDER in BASE_PROMPT:
        return BASE_PROMPT.replace(PLACEHOLDER, raw_text)
    return f"{BASE_PROMPT}\n\n[RAW CONTENT]\n{raw_text}\n"

def call_openai(final_prompt: str) -> str:
    """Сначала пробуем Responses API; если не поддерживается — фолбэк на chat.completions."""
    client = OpenAI(api_key=OPENAI_KEY)
    # 1) Responses API
    try:
        resp = client.responses.create(
            model=MODEL,
            input=final_prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        # в новых SDK есть удобное свойство:
        if hasattr(resp, "output_text") and resp.output_text:
            return resp.output_text
        # универсальная распаковка
        if getattr(resp, "output", None):
            parts = []
            for item in resp.output:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") == "output_text":
                        parts.append(getattr(c, "text", ""))
                    elif getattr(c, "type", "") == "text":
                        parts.append(getattr(c, "text", ""))
            if parts:
                return "".join(parts)
        # если дошли сюда — принудительно упадём в except и попробуем фолбэк
        raise RuntimeError("Responses API returned empty content")
    except Exception:
        # 2) Chat Completions (совместимо со старыми версиями)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": final_prompt}],
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        return resp.choices[0].message.content

def extract_markup(text: str) -> str:
    t = text.strip()
    if t.startswith("<") and t.endswith(">") and 'class="markup-seo-page"' in t:
        return t
    m = re.search(r'<div\s+class="markup-seo-page"[\s\S]*?</div>', t, re.I)
    return m.group(0) if m else t

def validate_markup(html_text: str) -> dict:
    issues, t = [], html_text.strip()
    if not (t.startswith("<") and t.endswith(">")):
        issues.append("Ответ не начинается с '<' или/и не заканчивается '>'")
    if 'class="markup-seo-page"' not in t:
        issues.append('Не найден <div class="markup-seo-page">')
    a = len(re.findall(r"<a\b", t, re.I))
    if a != 7: issues.append(f"Количество <a>: {a} (ожидалось 7)")
    e = len(re.findall(r"<em\b", t, re.I))
    if e != 1: issues.append(f"Количество <em>: {e} (ожидалось 1)")
    tables = re.findall(r"<table[\s\S]*?</table>", t, re.I)
    if len(tables) != 3:
        issues.append(f"Количество <table>: {len(tables)} (ожидалось 3)")
    else:
        for i, need in enumerate([6, 3, 10]):
            rows = len(re.findall(r"<tr\b", tables[i], re.I)) if i < len(tables) else 0
            if rows != need:
                issues.append(f"Таблица #{i+1}: {rows} (ожидалось {need})")
    faq = len(re.findall(r"<label\b[^>]*faq-accordion__item", t, re.I))
    if faq != 5: issues.append(f"FAQ блоки: {faq} (ожидалось 5)")
    return {"ok": not issues, "issues": issues, "length": len(t)}

# =====================
# UI
# =====================
st.title("🧩 HTML Transformer — Streamlit + OpenAI")
st.caption("Вставьте исходный текст → модель вернёт один HTML-блок по вашему шаблону. Настройки захардкожены.")

# !!! ДАЁМ КЛЮЧ, ЧТОБЫ МОЖНО БЫЛО ОЧИЩАТЬ ПОЛЕ
raw = st.text_area(
    "Исходный текст (будет подставлен в [RAW CONTENT])",
    key="raw_text",
    height=280,
    placeholder="Вставьте ваш контент здесь…",
)

col1, col2 = st.columns([1, 1])
with col1:
    generate = st.button("🚀 Сгенерировать HTML", type="primary", use_container_width=True)
with col2:
    clear_btn = st.button("🧹 Очистить", use_container_width=True)

# Очистка: и поле, и результат
if clear_btn:
    st.session_state["raw_text"] = ""
    st.session_state.pop("generated_html", None)
    st.rerun()

# Проверки секретов — и ЖЁСТКИЙ STOP, если ключа нет
if not OPENAI_KEY:
    st.error("Не найден OPENAI_API_KEY в secrets.")
    st.stop()
if not BASE_PROMPT:
    st.warning("Не найден HTML_PROMPT в secrets (вставьте ваш промпт целиком).")

# Генерация
if generate:
    if not raw or not raw.strip():
        st.error("Введите текст для генерации.")
    else:
        text = raw.strip()
        if len(text) > MAX_RAW_CHARS:
            text = text[:MAX_RAW_CHARS] + "\n… [обрезано для лимита запроса]"
        prompt = build_prompt(text)
        with st.spinner("Генерация…"):
            try:
                html_block = call_openai(prompt)
                html_block = extract_markup(html_block)
            except Exception as e:
                st.exception(e)
                st.stop()
            st.session_state["generated_html"] = html_block

# Вывод
html = st.session_state.get("generated_html")
if html:
    st.subheader("Результат")
    report = validate_markup(html)
    if report["ok"]:
        st.success("Проверки пройдены ✓")
    else:
        st.warning("Есть несоответствия:")
        for item in report["issues"]:
            st.write("• ", item)

    fname = f"markup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    st.download_button("💾 Скачать HTML", html, fname, "text/html", use_container_width=True)

    st.divider()
    st.subheader("Предпросмотр")
    # Универсально: components.html работает в любой версии Streamlit
    components.html(html, height=PREVIEW_HEIGHT, scrolling=True)

    with st.expander("Показать чистый HTML"):
        st.code(html, language="html")

st.caption("ℹ️ После «Сгенерировать HTML» ниже появится «Результат», предпросмотр и кнопка «Скачать HTML».")
