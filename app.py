import os
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# ---------- Page config ----------
st.set_page_config(
    page_title="HTML Transformer (GPT‑5)",
    page_icon="🧩",
    layout="wide",
)

st.title("🧩 HTML Transformer — Streamlit + OpenAI Responses API")
st.caption(
    "Вставьте исходный текст → модель вернёт один HTML‑блок по вашему шаблону."
)

# ---------- Secrets & config ----------
# Требуемые секреты в .streamlit/secrets.toml:
# OPENAI_API_KEY = "sk-..."
# HTML_PROMPT = """
#   <ВЕСЬ ВАШ ПРОМПТ ИЗ СООБЩЕНИЯ>
# """

OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "")
BASE_PROMPT = st.secrets.get("HTML_PROMPT", "")

if not OPENAI_KEY:
    st.error(
        "Не найден OPENAI_API_KEY в secrets. Добавьте ключ в .streamlit/secrets.toml и перезапустите приложение.")
if not BASE_PROMPT:
    st.warning(
        "Не найден HTML_PROMPT в secrets. Вставьте туда ваш промпт (включая RAW CONTENT и TARGET HTML TEMPLATE)."
    )

# ---------- Sidebar ----------
st.sidebar.header("Настройки")
model = st.sidebar.selectbox(
    "Модель",
    options=["gpt-5", "gpt-5-mini", "gpt-5-nano"],
    index=0,
    help="Требуется доступ к семейству GPT‑5 в API.",
)
max_output_tokens = st.sidebar.slider(
    "max_output_tokens",
    min_value=512,
    max_value=8192,
    value=4096,
    step=256,
    help="Ограничение на размер ответа модели.",
)

temperature = st.sidebar.slider(
    "temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.2,
    step=0.05,
    help="Ниже = строже следование шаблону.",
)

preview_height = st.sidebar.slider(
    "Высота предпросмотра (px)", 600, 2400, 1200, 50
)

st.sidebar.markdown(
    "**Подсказка:** держите промпт в `HTML_PROMPT` и подставляйте сырой текст сюда — код сам заменит placeholder."
)

# ---------- Helpers ----------

def build_prompt(raw_text: str) -> str:
    """Подставить пользовательский текст в секцию [RAW CONTENT].
    Ожидается, что в исходном промпте есть фраза-плейсхолдер
    "Тут должен быть текст который вставил юзер".
    """
    placeholder = "Тут должен быть текст который вставил юзер"
    if placeholder not in BASE_PROMPT:
        # Мягкая подстраховка: если плейсхолдер не найден — добавим [RAW CONTENT] в конец
        return f"{BASE_PROMPT}\n\n[RAW CONTENT]\n{raw_text}\n"
    return BASE_PROMPT.replace(placeholder, raw_text)


def call_openai(final_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    response = client.responses.create(
        model=model,
        input=final_prompt,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    # В Responses API есть удобное свойство
    return response.output_text


def validate_markup(html_text: str) -> dict:
    """Быстрые проверки на соответствие требованиям шаблона.
    Это простая валидация по паттернам, без тяжёлых зависимостей.
    """
    issues = []

    trimmed = html_text.strip()
    if not (trimmed.startswith("<") and trimmed.endswith(">")):
        issues.append("Ответ не начинается с '<' или/и не заканчивается '>'")

    if 'class="markup-seo-page"' not in trimmed:
        issues.append("Не найден <div class=\"markup-seo-page\">")

    # Счётчики тегов
    anchors = len(re.findall(r"<a\b", trimmed, flags=re.I))
    if anchors != 7:
        issues.append(f"Количество <a>: {anchors} (ожидалось 7)")

    em_count = len(re.findall(r"<em\b", trimmed, flags=re.I))
    if em_count != 1:
        issues.append(f"Количество <em>: {em_count} (ожидалось 1)")

    tables = re.findall(r"<table[\s\S]*?</table>", trimmed, flags=re.I)
    if len(tables) != 3:
        issues.append(f"Количество <table>: {len(tables)} (ожидалось 3)")
    else:
        row_targets = [6, 3, 10]
        for i, tbl in enumerate(tables):
            rows = len(re.findall(r"<tr\b", tbl, flags=re.I))
            if rows != row_targets[i]:
                issues.append(
                    f"Таблица #{i+1}: {rows} строк(и) (ожидалось {row_targets[i]})"
                )

    # FAQ блоки: считаем label.faq-accordion__item
    faq_blocks = len(re.findall(r"<label\b[^>]*faq-accordion__item", trimmed, flags=re.I))
    if faq_blocks != 5:
        issues.append(f"FAQ блоки: {faq_blocks} (ожидалось 5)")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "length": len(trimmed),
    }


# ---------- UI ----------
raw = st.text_area(
    "Исходный текст (будет подставлен в [RAW CONTENT])",
    min_height=240,
    placeholder="Вставьте ваш контент здесь…",
)

col_run, col_save = st.columns([1, 1])

with col_run:
    generate = st.button("🚀 Сгенерировать HTML", type="primary", use_container_width=True)

with col_save:
    clear_btn = st.button("🧹 Очистить", use_container_width=True)

if clear_btn:
    st.session_state.pop("generated_html", None)
    st.experimental_rerun()

if generate:
    if not raw.strip():
        st.error("Введите текст для генерации.")
    elif not OPENAI_KEY or not BASE_PROMPT:
        st.error("Нужно настроить OPENAI_API_KEY и HTML_PROMPT в secrets.")
    else:
        with st.spinner("Генерация…"):
            prompt = build_prompt(raw.strip())
            try:
                html_block = call_openai(prompt)
            except Exception as e:
                st.exception(e)
                st.stop()
            st.session_state["generated_html"] = html_block

# ---------- Output ----------
if html := st.session_state.get("generated_html"):
    st.subheader("Результат")

    # Валидация
    report = validate_markup(html)
    if report["ok"]:
        st.success("Проверки пройдены ✓")
    else:
        st.warning("Есть несоответствия:")
        for item in report["issues"]:
            st.write("• ", item)

    # Кнопки скачивания
    file_name = f"markup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    st.download_button(
        label="💾 Скачать HTML",
        data=html,
        file_name=file_name,
        mime="text/html",
        use_container_width=True,
    )

    # Предпросмотр: по возможности используем новый st.html,
    # иначе — стандартный components.html в iframe.
    st.divider()
    st.subheader("Предпросмотр")
    if hasattr(st, "html"):
        # Streamlit 1.39+ ввёл st.html (без iframe)
        st.html(html)
    else:
        components.html(html, height=preview_height, scrolling=True)

    with st.expander("Показать чистый HTML"):
        st.code(html, language="html")

st.caption(
    "ℹ️ Примечания: модель должна вернуть ровно один HTML‑блок, начинающийся с <div class=\"markup-seo-page\"> и заканчивающийся </div>."
)
