# -*- coding: utf-8 -*-
"""
HTML Transformer — промпт возвращает готовый HTML (без автопочинок).
Стримлит-приложение с аккуратной структурой и минимальными зависимостями.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Dict, Iterable, Tuple

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# =====================
# Константы/настройки
# =====================

APP_TITLE = "🧩 HTML Transformer — промпт возвращает готовый HTML"

# Ключ в secrets для API
OPENAI_KEY: str = st.secrets.get("OPENAI_API_KEY", "")

# ❶ Ключи секретов для разных брендов (в порядке приоритета)
SECRET_KEYS: Dict[str, Iterable[str]] = {
    "RocketPlay": ["HTML_PROMPT_RP", "HTML_PROMPT"],  # совместимость со старым ключом
    "WinSpirit / LuckyHills": ["HTML_PROMPT_WS_LH"],
    "Zoome": ["HTML_PROMPT_ZOOME"],  # новый бренд
}

# Можно переопределить переменными окружения
MODEL: str = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4.1-mini")
PREVIEW_HEIGHT: int = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))

# Плейсхолдер (не обязателен к использованию в новой схеме, оставлен для совместимости)
PLACEHOLDER = "Тут должен быть текст который вставил юзер"


# =====================
# Инициализация страницы
# =====================

def setup_page() -> None:
    """Единая точка для конфигурации страницы и CSS."""
    st.set_page_config(page_title="HTML Transformer — no fixes", page_icon="🧩", layout="wide")
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
          .block-container { padding-top: 2rem; }
          .stButton>button { height:48px; font-weight:600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================
# Session State helpers
# =====================

def init_session_state() -> None:
    """Гарантирует наличие ключей и обрабатывает флаг очистки."""
    st.session_state.setdefault("raw_text", "")
    st.session_state.setdefault("result_text", None)
    st.session_state.setdefault("do_clear", False)
    st.session_state.setdefault("brand", "RocketPlay")

    if st.session_state.get("do_clear"):
        st.session_state["raw_text"] = ""
        st.session_state["result_text"] = None
        st.session_state["do_clear"] = False


# =====================
# Бизнес-логика
# =====================

def resolve_base_prompt(brand: str) -> Tuple[str, str]:
    """
    Возвращает кортеж (prompt, used_secret_key) для выбранного бренда.
    Бросает ValueError, если подходящего секрета нет.
    """
    keys = SECRET_KEYS.get(brand, [])
    for key in keys:
        val = st.secrets.get(key, "")
        if val:
            return val, key
    raise ValueError(f"Не найден промпт для «{brand}». Добавьте секрет(ы): {', '.join(keys)}.")


# ---- Новый блок: готовим system-prompt с «СТРОГИМ ПРИМЕРОМ», не вырезая его

EXAMPLE_TITLE_RE = re.compile(r"(?:^|\n)\s*СТРОГИЙ\s+ПРИМЕР\b", flags=re.IGNORECASE)

def prepare_system_prompt_with_example(base_prompt: str) -> str:
    """
    Не удаляем «СТРОГИЙ ПРИМЕР», а помечаем его как иллюстрацию и добавляем пролог,
    который запрещает переносить данные из примера. Пользовательский SOURCE_TEXT
    придёт отдельным user-сообщением.
    """
    # Помечаем заголовок примера (если он есть)
    marked = EXAMPLE_TITLE_RE.sub(
        "\nСТРОГИЙ ПРИМЕР (ДАННЫЕ ИСПОЛЬЗОВАТЬ НЕЛЬЗЯ — ТОЛЬКО ИЛЛЮСТРАЦИЯ)\n",
        base_prompt,
    )

    preface = (
        "ВАЖНО:\n"
        "1) Секция «СТРОГИЙ ПРИМЕР» приведена ТОЛЬКО для иллюстрации формата.\n"
        "   ЧИСЛА/БРЕНДЫ/ДАТЫ из примера ИСПОЛЬЗОВАТЬ НЕЛЬЗЯ.\n"
        "2) Заполняй шаблон ТОЛЬКО по фактическому SOURCE_TEXT из следующего сообщения пользователя.\n"
        "3) Верни строго один HTML-документ без комментариев и Markdown.\n"
    )
    return f"{preface}\n{marked}".strip()


def strip_code_fences(text: str) -> str:
    """
    Убирает обрамление ```...``` если модель вернула кодом.
    """
    t = (text or "").strip()
    if t.startswith("```"):
        # Отрезаем первую строку с ```<lang>? и оставшееся содержимое
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def call_openai_with_messages(system_prompt: str, user_text: str) -> str:
    """
    Жёсткая схема: system = инструкции/шаблон/пример, user = реальный SOURCE_TEXT.
    Никаких автопочинок, только постобрезка тройных бэктиков.
    """
    client = OpenAI(api_key=OPENAI_KEY)

    # Responses API
    try:
        r = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"SOURCE_TEXT:\n{user_text}"},
            ],
        )

        # Прямое поле текстового вывода (новые SDK)
        if getattr(r, "output_text", None):
            return strip_code_fences(r.output_text)

        # Универсальный сбор кусочков
        if getattr(r, "output", None):
            parts: list[str] = []
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
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"SOURCE_TEXT:\n{user_text}"},
            ],
        )
        return strip_code_fences(c.choices[0].message.content)


def looks_like_html(s: str) -> bool:
    """Очень грубая эвристика для определения HTML."""
    t = (s or "").strip().lower()
    return t.startswith("<!doctype") or (t.startswith("<") and "</" in t)


# =====================
# UI
# =====================

def render_header() -> None:
    st.title(APP_TITLE)


def render_controls() -> Tuple[str, str, bool]:
    """
    Рендерит элементы управления и возвращает кортеж:
    (brand, raw_text, generate_clicked)
    """
    # ❷ Выбор шаблона/бренда
    brands = list(SECRET_KEYS.keys())
    st.session_state["brand"] = st.selectbox(
        "Шаблон / бренд",
        options=brands,
        index=brands.index(st.session_state.get("brand", "RocketPlay")),
    )

    raw = st.text_area(
        "Исходный текст (подставится в промпт выбранного бренда)",
        key="raw_text",
        height=280,
        placeholder="Вставьте контент…",
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)

    with col_right:
        if st.button("🧹 Очистить", use_container_width=True):
            st.session_state["do_clear"] = True
            st.rerun()

    return st.session_state["brand"], raw, generate


def guard_secrets() -> None:
    """Проверяет наличие обязательных секретов."""
    if not OPENAI_KEY:
        st.error("Не найден OPENAI_API_KEY в secrets.")
        st.stop()


def render_result(out: str) -> None:
    """Показывает результат ровно в том виде, как вернула модель."""
    if not out:
        return

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

    st.caption(
        "Здесь НЕТ автоправок и валидаций. Если результат не соответствует — "
        "корректируйте ваш HTML_PROMPT_* в secrets."
    )


# =====================
# Точка входа
# =====================

def main() -> None:
    setup_page()
    init_session_state()
    render_header()

    brand, raw, generate = render_controls()
    guard_secrets()

    # Разрешим пользователю увидеть, из какого секрета берём промпт
    try:
        base_prompt, used_secret_key = resolve_base_prompt(brand)
        st.caption(f"Используется секрет: **{used_secret_key}**")
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Генерация (без повторов/правок)
    if generate:
        if not raw or not raw.strip():
            st.error("Введите текст.")
        else:
            with st.spinner("Генерация…"):
                try:
                    system_prompt = prepare_system_prompt_with_example(base_prompt)
                    out = call_openai_with_messages(system_prompt, raw.strip())
                    st.session_state["result_text"] = out
                except Exception as e:  # показываем стек в dev-режиме
                    st.exception(e)
                    st.stop()

    # Вывод результата (ровно то, что прислала модель)
    render_result(st.session_state.get("result_text"))


if __name__ == "__main__":
    main()
