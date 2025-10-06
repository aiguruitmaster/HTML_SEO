import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# =============== БАЗА СТРАНИЦЫ ===============
st.set_page_config(page_title="HTML Free Transformer", page_icon="🧩", layout="wide")
st.markdown("""
<style>
  [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
  .block-container { padding-top: 2rem; }
  .stButton>button { height:48px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# =============== СЕКРЕТЫ/НАСТРОЙКИ ===============
OPENAI_KEY  = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")  # если есть — используем как мягкое вступление, БЕЗ жёстких правил

MODEL          = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4o-mini")
PREVIEW_HEIGHT = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))
PLACEHOLDER    = "Тут должен быть текст который вставил юзер"

# =============== SESSION STATE (ОЧИСТКА ДО ВИДЖЕТОВ) ===============
st.session_state.setdefault("raw_text", "")
st.session_state.setdefault("generated_text", None)
st.session_state.setdefault("do_clear", False)

if st.session_state.get("do_clear"):
    st.session_state["raw_text"] = ""
    st.session_state["generated_text"] = None
    st.session_state["do_clear"] = False

# =============== ХЕЛПЕРЫ ===============
def build_prompt(raw_text: str) -> str:
    """Никаких ограничений: просто подставляем текст в мягкий промпт (если он есть)."""
    if not BASE_PROMPT:
        return raw_text
    if PLACEHOLDER in BASE_PROMPT:
        return BASE_PROMPT.replace(PLACEHOLDER, raw_text)
    return f"{BASE_PROMPT}\n\n{raw_text}"

def strip_code_fences(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"):
        # убираем возможные тройные бэктики
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()

def call_openai(f_prompt: str) -> str:
    """Минималистичный вызов: без temperature, без max_tokens — даём модели свободу.
       Фолбэк на chat.completions, если Responses API недоступен."""
    client = OpenAI(api_key=OPENAI_KEY)

    # Responses API
    try:
        resp = client.responses.create(model=MODEL, input=f_prompt)
        if hasattr(resp, "output_text") and resp.output_text:
            return strip_code_fences(resp.output_text)
        # универсальная распаковка на всякий случай
        if getattr(resp, "output", None):
            parts = []
            for item in resp.output:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") in ("output_text", "text"):
                        parts.append(getattr(c, "text", ""))
            if parts:
                return strip_code_fences("".join(parts))
        raise RuntimeError("Empty response body")
    except Exception:
        # Chat Completions (совместимость)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f_prompt}],
        )
        return strip_code_fences(resp.choices[0].message.content)

def looks_like_html(s: str) -> bool:
    t = (s or "").strip().lower()
    return t.startswith("<!doctype") or (t.startswith("<") and "</" in t)

# =============== UI ===============
st.title("🧩 HTML Free Transformer — без ограничений")

raw = st.text_area(
    "Введите текст/промпт (если это HTML, покажем предпросмотр)",
    key="raw_text",
    height=280,
    placeholder="Вставьте свой контент или промпт…",
)

col1, col2 = st.columns([1, 1])
with col1:
    generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)
with col2:
    if st.button("🧹 Очистить", use_container_width=True):
        st.session_state["do_clear"] = True
        st.rerun()

# Ключ обязателен
if not OPENAI_KEY:
    st.error("Не найден OPENAI_API_KEY в secrets.")
    st.stop()

# Генерация
if generate:
    if not raw or not raw.strip():
        st.error("Введите текст.")
    else:
        with st.spinner("Генерация…"):
            try:
                prompt = build_prompt(raw.strip())
                result = call_openai(prompt)
            except Exception as e:
                st.exception(e)
                st.stop()
            st.session_state["generated_text"] = result

# Вывод
out = st.session_state.get("generated_text")
if out:
    st.subheader("Результат")
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

st.caption("Свободный режим: без температур, без лимитов токенов и без валидаций. Что пришло — то и показываем.")
