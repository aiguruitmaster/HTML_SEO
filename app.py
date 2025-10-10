# streamlit_app.py
import os
import re
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
# Конфиг/секреты
# =====================
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")

SECRET_KEYS = {
    "RocketPlay": ["HTML_PROMPT_RP", "HTML_PROMPT"],      # совместимость
    "WinSpirit / LuckyHills": ["HTML_PROMPT_WS_LH"],
    "Zoome": ["HTML_PROMPT_ZOOME"],
}

MODEL          = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4.1-mini")
PREVIEW_HEIGHT = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))
PLACEHOLDER    = "Тут должен быть текст который вставил юзер"

# =====================
# Session State
# =====================
st.session_state.setdefault("raw_text", "")
st.session_state.setdefault("result_text", None)
st.session_state.setdefault("do_clear", False)
st.session_state.setdefault("brand", "RocketPlay")
st.session_state.setdefault("wl_subbrand", "WinSpirit")  # для WS/LH

if st.session_state.get("do_clear"):
    st.session_state["raw_text"] = ""
    st.session_state["result_text"] = None
    st.session_state["do_clear"] = False

# =====================
# Хелперы
# =====================
def resolve_base_prompt(brand: str) -> tuple[str, str]:
    keys = SECRET_KEYS.get(brand, [])
    for k in keys:
        v = st.secrets.get(k, "")
        if v:
            return v, k
    raise ValueError(f"Не найден промпт для «{brand}». Добавьте секрет(ы): {', '.join(keys)}.")

def _inject_brand_line(text: str, brand_line: str) -> str:
    """Гарантированно добавляет строку BRAND_NAME: ... первой строкой сырого текста,
    если её ещё нет."""
    t = (text or "").lstrip()
    if re.search(r"^\s*BRAND_NAME\s*:", t, flags=re.IGNORECASE):
        return text  # уже есть
    return f"BRAND_NAME: {brand_line}\n{t}"

def build_prompt(base_prompt: str, raw_text: str, brand: str, wl_subbrand: str) -> str:
    """
    Надёжно вставляет сырой текст в разные форматы секретов и,
    при необходимости, подбрасывает BRAND_NAME для точной детекции.
    """
    if not base_prompt:
        return raw_text

    rt = (raw_text or "").strip()
    out = base_prompt

    # --- Поддержка бренд-оверов ---
    # Для WS/LH — явно прокидываем BRAND_NAME в SOURCE_TEXT.
    if brand == "WinSpirit / LuckyHills":
        rt = _inject_brand_line(rt, wl_subbrand)

    # Для Zoome можно подсунуть желаемый бренд аналогично (если хотите фиксировать):
    if brand == "Zoome":
        # Если в тексте нет BRAND_NAME, вставим "Zoome" как дефолт — или замените на нужный бренд.
        rt = _inject_brand_line(rt, "Zoome")

    # --- Универсальные подстановки ---
    # [RAW CONTENT]
    out2 = re.sub(r"(\[RAW CONTENT\])", r"\1\n" + rt, out, count=1)
    if out2 != out:
        return out2

    # RocketPlay PLACEHOLDER
    out2 = out.replace(PLACEHOLDER, rt)
    if out2 != out:
        return out2

    # WS/LH: SOURCE_TEXT: <<...>>
    out2 = re.sub(
        r"(SOURCE_TEXT:\s*<<)(.*?)(>>)",
        lambda m: f"{m.group(1)}{rt}{m.group(3)}",
        out,
        count=1,
        flags=re.DOTALL,
    )
    if out2 != out:
        return out2

    # WS/LH: <<ВСТАВЬ ИСХОДНЫЙ ТЕКСТ>>
    out2 = out.replace("<<ВСТАВЬ ИСХОДНЫЙ ТЕКСТ>>", rt)
    if out2 != out:
        return out2

    # Zoome: вставка сразу после строки "ВХОД"
    pattern_vhod = re.compile(r"(?:^|\n)ВХОД\s*\n\s*$", flags=re.DOTALL)
    if pattern_vhod.search(out):
        return pattern_vhod.sub(lambda m: m.group(0) + rt + "\n", out, count=1)

    # Fallback — дописать в конец
    return out.rstrip() + "\n\n" + rt + "\n"

def strip_code_fences(t: str) -> str:
    t = (t or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()

def call_openai(f_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    try:
        r = client.responses.create(
            model=MODEL,
            input=f_prompt,
            temperature=0,
            max_output_tokens=4096,
        )
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
        c = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f_prompt}],
            temperature=0,
        )
        return strip_code_fences(c.choices[0].message.content)

def looks_like_html(s: str) -> bool:
    t = (s or "").strip().lower()
    return t.startswith("<!doctype") or (t.startswith("<") and "</" in t)

# =====================
# UI
# =====================
st.title("🧩 HTML Transformer — промпт возвращает готовый HTML")

brand_options = list(SECRET_KEYS.keys())
st.session_state["brand"] = st.selectbox(
    "Шаблон / бренд",
    options=brand_options,
    index=brand_options.index(st.session_state.get("brand", "RocketPlay")),
)

# Подбренд для WS/LH
if st.session_state["brand"] == "WinSpirit / LuckyHills":
    st.session_state["wl_subbrand"] = st.radio(
        "Подбренд",
        options=["WinSpirit", "LuckyHills"],
        horizontal=True,
        index=0 if st.session_state.get("wl_subbrand") == "WinSpirit" else 1,
    )

raw = st.text_area(
    "Исходный текст (подставится в промпт выбранного бренда)",
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

try:
    BASE_PROMPT, USED_SECRET_KEY = resolve_base_prompt(st.session_state["brand"])
    st.caption(f"Используется секрет: **{USED_SECRET_KEY}**")
except ValueError as e:
    st.error(str(e)); st.stop()

# Генерация
if generate:
    if not raw or not raw.strip():
        st.error("Введите текст.")
    else:
        with st.spinner("Генерация…"):
            try:
                prompt = build_prompt(
                    BASE_PROMPT,
                    raw.strip(),
                    st.session_state["brand"],
                    st.session_state.get("wl_subbrand", "WinSpirit"),
                )
                out = call_openai(prompt)
            except Exception as e:
                st.exception(e); st.stop()
            st.session_state["result_text"] = out

# Вывод
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

st.caption("Подстановка идёт строго в секрете; для WS/LH добавляется строка BRAND_NAME: WinSpirit/LuckyHills в SOURCE_TEXT, чтобы модель не ошибалась с брендом. Модель — temperature=0.")
