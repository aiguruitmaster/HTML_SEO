import os
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# =====================
# Page config + no sidebar
# =====================
st.set_page_config(
    page_title="HTML Transformer (GPT-5)",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# Жёстко прячем сайдбар/бургер/верхнее меню
st.markdown(
    """
    <style>
      [data-testid="stSidebar"],
      [data-testid="collapsedControl"],
      header { display: none !important; }
      .block-container { padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================
# Secrets & constants
# =====================
# В .streamlit/secrets.toml:
# OPENAI_API_KEY = "sk-..."
# HTML_PROMPT   = """
#   ВАШ ПОЛНЫЙ ПРОМПТ (с [RAW CONTENT] и TARGET HTML TEMPLATE)
# """
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")

# Жёсткие настройки (можно переопределить переменными окружения)
MODEL = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-5")
MAX_OUTPUT_TOKENS = int(os.getenv("HTML_MAX_OUTPUT_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("HTML_TEMPERATURE", "0.15"))
PREVIEW_HEIGHT = int(os.getenv("HTML_PREVIEW_HEIGHT", "1400"))
MAX_RAW_CHARS = int(os.getenv("HTML_MAX_RAW_CHARS", "200000"))  # защита от чрезмерно больших вставок

PLACEHOLDER = "Тут должен быть текст который вставил юзер"

# =====================
# Helpers
# =====================
def build_prompt(raw_text: str) -> str:
    """Подставить пользовательский текст в секцию [RAW CONTENT]."""
    if PLACEHOLDER in BASE_PROMPT:
        return BASE_PROMPT.replace(PLACEHOLDER, raw_text)
    return f"{BASE_PROMPT}\n\n[RAW CONTENT]\n{raw_text}\n"

def call_openai(final_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.responses.create(
        model=MODEL,
        input=final_prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        temperature=TEMPERATURE,
    )
    return resp.output_text

def extract_markup(text: str) -> str:
    """Оставляем только <div class="markup-seo-page">…</div> если модель болтнула лишнее."""
    trimmed = text.strip()
    if trimmed.startswith("<") and trimmed.endswith(">") and 'class="markup-seo-page"' in trimmed:
        return trimmed
    m = re.search(r'<div\s+class="markup-seo-page"[\s\S]*?</div>', trimmed, re.I)
    return m.group(0) if m else trimmed

def validate_markup(html_text: str) -> dict:
    issues, t = [], html_text.strip()

    if not (t.startswith("<") and t.endswith(">")):
        issues.append("Ответ не начинается с '<' или/и не заканчивается '>'")

    if 'class="markup-seo-page"' not in t:
        issues.append('Не найден <div class="markup-seo-page">')

    if (a := len(re.findall(r"<a\b", t, re.I))) != 7:
        issues.append(f"Количество <a>: {a} (ожидалось 7)")

    if (e := len(re.findall(r"<em\b", t, re.I))) != 1:
        issues.append(f"Количество <em>: {e} (ожидалось 1)")

    tables = re.findall(r"<table[\s\S]*?</table>", t, re.I)
    if len(tables) != 3:
        issues.append(f"Количество <table>: {len(tables)} (ожидалось 3)")
    else:
        for i, need in enumerate([6, 3, 10]):
            rows = len(re.findall(r"<tr\b", tables[i], re.I)) if i < len(tables) else 0
            if rows != need:
                issues.append(f"Таблица #{i+1}: {rows} (ожидалось {need})")

    if (faq := len(re.findall(r"<label\b[^>]*faq-accordion__item", t, re.I))) != 5:
        issues.append(f"FAQ блоки: {faq} (ожидалось 5)")

    return {"ok": not issues, "issues": issues, "length": len(t)}

# =====================
# UI (без сайдбара)
# =====================
st.title("🧩 HTML Transformer — Streamlit + OpenAI Responses API")
st.caption("Вставьте исходный текст → модель вернёт один HTML-блок по вашему шаблону. Настройки захардкожены.")

raw = st.text_area(
    "Исходный текст (будет подставлен в [RAW CONTENT])",
    height=280,  # <— фикс: используем height вместо min_height
    placeholder="Вставьте ваш контент здесь…",
)

col1, col2 = st.columns([1, 1])
with col1:
    generate = st.button("🚀 Сгенерировать HTML", type="primary", use_container_width=True)
with col2:
    clear_btn = st.button("🧹 Очистить", use_container_width=True)

if clear_btn:
    st.session_state.pop("generated_html", None)
    st.experimental_rerun()

# Предусловия
if not OPENAI_KEY:
    st.error("Не найден OPENAI_API_KEY в secrets.")
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
if html := st.session_state.get("generated_html"):
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
    if hasattr(st, "html"):
        st.html(html)  # Streamlit 1.39+
    else:
        components.html(html, height=PREVIEW_HEIGHT, scrolling=True)

    with st.expander("Показать чистый HTML"):
        st.code(html, language="html")

st.caption("ℹ️ Ответ должен быть РОВНО одним HTML-блоком: начинается с <div class=\"markup-seo-page\"> и заканчивается </div>.")
