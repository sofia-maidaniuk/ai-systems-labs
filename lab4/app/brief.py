import html
import json

import streamlit as st


PRODUCT_TYPES = [
    "Онлайн-клуб / підписка",
    "Онлайн-курс",
    "Мінікурс",
    "Вебінар / майстер-клас",
    "Інтенсив / марафон",
    "Фізичний товар",
    "Послуга / консультація",
    "Програмний сервіс",
    "Подія / захід",
    "Інше",
]

GOALS = [
    "Продажі / підписки",
    "Залучення заявок",
    "Реєстрації",
    "Переходи на сайт",
    "Підвищення впізнаваності",
]


def render_brief():
    saved = st.session_state.get("brief", {})

    st.html(
        """
        <div class="ams-section-kicker">
            01 / Початок роботи
        </div>
        <div class="ams-section-title">
            Розкажіть про продукт.
        </div>
        <div class="ams-section-lead">
            Заповніть маркетинговий бриф — він стане основою
            для всіх наступних етапів.
            Поля зі зірочкою обов’язкові.
            Що точніші вихідні дані, то кориснішим буде аналіз.
        </div>
        """
    )

    selected_type = saved.get("product_type", PRODUCT_TYPES[0])
    selected_goal = saved.get("goal", GOALS[0])

    with st.form("product_brief", clear_on_submit=False):
        st.html(
            """
            <div class="ams-form-heading">
                <span class="n">01</span> Основна інформація
            </div>
            """
        )

        col_type, col_name = st.columns(2, gap="medium")

        with col_type:
            product_type = st.selectbox(
                "Тип продукту *",
                PRODUCT_TYPES,
                index=(
                    PRODUCT_TYPES.index(selected_type)
                    if selected_type in PRODUCT_TYPES
                    else 0
                ),
            )

        with col_name:
            product_name = st.text_input(
                "Назва продукту *",
                value=saved.get("product_name", ""),
                placeholder="Наприклад, LADY DRIVE CLUB",
            )

        st.html('<div class="ams-form-gap"></div>')

        st.html(
            """
            <div class="ams-form-heading">
                <span class="n">02</span> Офер і цінність
            </div>
            """
        )

        offer_title = st.text_input(
            "Заголовок оферу",
            value=saved.get("offer_title", ""),
            placeholder=(
                "Основна обіцянка або ідея продукту "
                "(якщо сформульована)"
            ),
        )

        offer_subtitle = st.text_area(
            "Підзаголовок оферу",
            value=saved.get("offer_subtitle", ""),
            placeholder=(
                "Коротко: що це, для кого і чому "
                "варто звернути увагу"
            ),
            height=77,
        )

        product_description = st.text_area(
            "Опис продукту *",
            value=saved.get("description", ""),
            placeholder=(
                "Що це за продукт? Яку проблему вирішує? "
                "Як саме він працює?"
            ),
            height=120,
        )

        col_content, col_adv = st.columns(2, gap="medium")

        with col_content:
            product_content = st.text_area(
                "Що отримує клієнт",
                value=saved.get("content", ""),
                placeholder=(
                    "Уроки, матеріали, функції, "
                    "зустрічі, доступ…"
                ),
                height=105,
            )

        with col_adv:
            advantages = st.text_area(
                "Ключові переваги",
                value=saved.get("advantages", ""),
                placeholder=(
                    "Чим продукт корисний або "
                    "відрізняється від інших?"
                ),
                height=105,
            )

        st.html('<div class="ams-form-gap"></div>')

        st.html(
            """
            <div class="ams-form-heading">
                <span class="n">03</span> Умови та мета реклами
            </div>
            """
        )

        col_price, col_goal = st.columns(2, gap="medium")

        with col_price:
            price = st.text_input(
                "Ціна",
                value=saved.get("price", ""),
                placeholder="Наприклад, 390 грн/міс або «за запитом»",
            )

        with col_goal:
            goal = st.selectbox(
                "Мета реклами *",
                GOALS,
                index=(
                    GOALS.index(selected_goal)
                    if selected_goal in GOALS
                    else 0
                ),
            )

        offer_terms = st.text_area(
            "Умови пропозиції",
            value=saved.get("offer_terms", ""),
            placeholder=(
                "Пробний доступ, бонуси, акції, обмеження — "
                "лише якщо вони справді є"
            ),
            height=80,
        )

        with st.expander(
            "＋ Додаткові деталі (необов’язково)",
            expanded=False,
        ):
            known_audience = st.text_area(
                "Що вже відомо про цільову аудиторію?",
                value=saved.get("known_audience", ""),
                placeholder=(
                    "Відомі сегменти, особливості клієнтів, "
                    "результати досліджень"
                ),
                height=85,
            )

            additional_info = st.text_area(
                "Додаткові уточнення",
                value=saved.get("additional_info", ""),
                placeholder=(
                    "Географія, важливі обмеження, "
                    "деталі комунікації"
                ),
                height=85,
            )

        st.html(
            """
            <div class="ams-note">
                ✦ Бриф зберігається в поточній сесії.
                За потреби його можна завантажити у форматі JSON.
            </div>
            """
        )

        submitted = st.form_submit_button(
            "Зберегти маркетинговий бриф →",
            use_container_width=True,
        )

    if submitted:
        if not product_name.strip():
            st.error("Укажіть назву продукту.")

        elif len(product_description.strip()) < 20:
            st.error(
                "Додайте змістовний опис продукту — "
                "щонайменше 20 символів."
            )

        else:
            st.session_state["brief"] = {
                "product_type": product_type,
                "product_name": product_name.strip(),
                "offer_title": offer_title.strip(),
                "offer_subtitle": offer_subtitle.strip(),
                "description": product_description.strip(),
                "content": product_content.strip(),
                "advantages": advantages.strip(),
                "price": price.strip(),
                "goal": goal,
                "offer_terms": offer_terms.strip(),
                "known_audience": known_audience.strip(),
                "additional_info": additional_info.strip(),
            }

    if "brief" in st.session_state:
        render_brief_confirmation()


def render_brief_confirmation():
    brief = st.session_state["brief"]

    name = html.escape(brief["product_name"])
    product_type = html.escape(brief["product_type"])

    st.html(
        f"""
        <div class="ams-confirm">
            <div class="ams-confirm-icon">✓</div>
            <div class="ams-confirm-content">
                <h3>Бриф збережено</h3>
                <div class="ams-confirm-meta">
                    {name} · {product_type}
                </div>
                <p>
                    Інформація готова для аналізу
                    цільової аудиторії.
                </p>
            </div>
        </div>
        """
    )

    col_next, col_export = st.columns(
        [1.4, 1],
        gap="small",
    )

    with col_next:
        if st.button(
            "Перейти до аналізу ЦА →",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["stage"] = "audience"
            st.rerun()

    with col_export:
        st.download_button(
            "↓ Завантажити JSON",
            data=json.dumps(
                brief,
                ensure_ascii=False,
                indent=2,
            ),
            file_name="marketing_brief.json",
            mime="application/json",
            use_container_width=True,
        )