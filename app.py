import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# =====================
# Страница
# =====================
st.set_page_config(page_title="HTML Transformer — no fixes", page_icon="🧩", layout="wide")
st.markdown("""
<style>
  [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
  .block-container { padding-top: 2rem; }
  .stButton>button { height:48px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# =====================
# Секреты/настройки
# =====================
OPENAI_KEY  = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")  # ← здесь ДОЛЖЕН быть ваш строгий промпт c TARGET HTML TEMPLATE

MODEL          = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-5")  # можно переопределить переменной окружения
PREVIEW_HEIGHT = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))
PLACEHOLDER    = "Тут должен быть текст который вставил юзер"

# =====================
# Session State (очистка до виджетов)
# =====================
st.session_state.setdefault("raw_text", "")
st.session_state.setdefault("result_text", None)
st.session_state.setdefault("do_clear", False)

if st.session_state.get("do_clear"):
    st.session_state["raw_text"] = ""
    st.session_state["result_text"] = None
    st.session_state["do_clear"] = False

# =====================
# Хелперы
# =====================
def build_prompt(raw_text: str) -> str:
    """Только подстановка. НИКАКИХ локальных исправлений."""
    if not BASE_PROMPT:
        return raw_text
    if PLACEHOLDER in BASE_PROMPT:
        return BASE_PROMPT.replace(PLACEHOLDER, raw_text)
    return f"{BASE_PROMPT}\n\n{raw_text}"

def strip_code_fences(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()

def call_openai(f_prompt: str) -> str:
    """Свободный вызов: без temperature, без max_tokens. Никаких автопочинок."""
    client = OpenAI(api_key=OPENAI_KEY)
    # Responses API
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
            if parts:
                return strip_code_fences("".join(parts))
        raise RuntimeError("Empty response")
    except Exception:
        # Chat Completions fallback (совместимость)
        c = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f_prompt}],
        )
        return strip_code_fences(c.choices[0].message.content)

def looks_like_html(s: str) -> bool:
    t = (s or "").strip().lower()
    return t.startswith("<!doctype") or (t.startswith("<") and "</" in t)

# =====================
# UI
# =====================
st.title("🧩 HTML Transformer — промпт возвращает готовый HTML")

raw = st.text_area(
    "Исходный текст (подставится в ваш HTML_PROMPT)",
    key="raw_text", height=280, placeholder="Вставьте контент…",
)

c1, c2 = st.columns([1, 1])
with c1:
    generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 Очистить", use_container_width=True):
        st.session_state["do_clear"] = True
        st.rerun()

# Обязательные секреты
if not OPENAI_KEY:
    st.error("Не найден OPENAI_API_KEY в secrets."); st.stop()
if not BASE_PROMPT:
    st.error("Не найден HTML_PROMPT в secrets. Поместите ваш строгий промпт c TARGET HTML TEMPLATE в secrets.toml."); st.stop()

# Генерация (без повторов/правок)
if generate:
    if not raw or not raw.strip():
        st.error("Введите текст.")
    else:
        with st.spinner("Генерация…"):
            try:
                prompt = build_prompt(raw.strip())
                out = call_openai(prompt)
            except Exception as e:
                st.exception(e); st.stop()
            st.session_state["result_text"] = out

# Вывод (ровно то, что прислала модель)
out = st.session_state.get("result_text")
if out:
    st.subheader("Результат (без изменений)")
    if looks_like_html(out):
        components.html(out, height=PREVIEW_HEIGHT, scrolling=True)
        st.download_button(
            "💾 Скачать как HTML",
            out,
            file_name=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.write(out)

    with st.expander("Показать как текст"):
        st.code(out, language="html")

st.caption("Здесь НЕТ автоправок и валидаций. Если результат не соответствует — корректируйте ваш HTML_PROMPT.")
