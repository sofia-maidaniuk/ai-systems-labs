import json

import streamlit as st

from config import DEFAULT_MODEL, GENERATION_PARAMS, MODELS
from creatives_service import (
    find_price_facts,
    generate_creative,
    revise_creative,
)
from llm import LLMError


def get_creatives_signature(
    brief,
    segments,
    selected_hooks,
    model,
    notes,
):
    return json.dumps(
        {
            "brief": brief,
            "segments": segments,
            "selected_hooks": selected_hooks,
            "model": model,
            "notes": notes,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def render_creative_content(creative):
    st.markdown(f"### {creative['hook']}")

    if creative["body_style"] == "bullets":
        for item in creative["body"]:
            st.write(f"• {item}")
    else:
        st.write(creative["body"][0])

    if creative["price"]:
        st.markdown(f"**{creative['price']}**")

    st.caption(f"CTA: {creative['cta']}")


def render_creative_revision(
    index,
    creative,
    brief,
    segments,
    model,
    notes,
):
    proposals = st.session_state.setdefault(
        "creative_proposals", {}
    )

    proposal = proposals.get(str(index))
    epoch = st.session_state.get("creatives_epoch", 0)

    with st.expander(
        "Правка з AI",
        expanded=(proposal is not None),
    ):
        with st.form(f"creative_revision_{epoch}_{index}"):
            feedback = st.text_area(
                "Що потрібно змінити?",
                placeholder=(
                    "Наприклад: заміни ціну на пробний "
                    "доступ за 19,90 грн на 5 днів. "
                    "Інші частини креативу не змінюй."
                ),
                height=110,
            )

            submitted = st.form_submit_button(
                "Переробити креатив з AI",
                use_container_width=True,
            )

        if submitted:
            if len(feedback.strip()) < 10:
                st.warning(
                    "Опишіть правку детальніше — "
                    "щонайменше 10 символів."
                )
            else:
                with st.spinner("AI доопрацьовує креатив..."):
                    try:
                        revised = revise_creative(
                            brief=brief,
                            segments=segments,
                            creative=creative,
                            feedback=feedback,
                            model=model,
                            notes=notes,
                        )

                    except LLMError as exc:
                        st.error(str(exc))

                    else:
                        proposals[str(index)] = revised
                        st.rerun()

        if proposal is not None:
            st.markdown("#### Запропонована AI версія")

            render_creative_content(proposal)

            accept_col, reject_col = st.columns(2)

            with accept_col:
                if st.button(
                    "Прийняти правку",
                    key=f"accept_creative_revision_{epoch}_{index}",
                    type="primary",
                    use_container_width=True,
                ):
                    updated = st.session_state["creatives"].copy()
                    updated[index] = proposal.copy()

                    st.session_state["creatives"] = updated

                    proposals.pop(str(index), None)

                    st.session_state["creatives_epoch"] = (
                        epoch + 1
                    )

                    st.rerun()

            with reject_col:
                if st.button(
                    "Відхилити правку",
                    key=f"reject_creative_revision_{epoch}_{index}",
                    use_container_width=True,
                ):
                    proposals.pop(str(index), None)

                    st.session_state["creatives_epoch"] = (
                        epoch + 1
                    )

                    st.rerun()


def render_creative_card(
    index,
    creative,
    brief,
    segments,
    model,
    notes,
):
    with st.container(border=True):
        st.caption(
            f"КРЕАТИВ {index + 1:02d} · "
            f"{creative['approach']}"
        )

        render_creative_content(creative)

        render_creative_revision(
            index=index,
            creative=creative,
            brief=brief,
            segments=segments,
            model=model,
            notes=notes,
        )


def render_creatives():
    brief = st.session_state.get("brief")
    segments = st.session_state.get("audience_segments")
    selected_hooks = st.session_state.get(
        "selected_hooks", []
    )

    if not brief or not segments or not selected_hooks:
        st.warning(
            "Спочатку виберіть рекламні хуки "
            "на третьому етапі."
        )

        if st.button("← Повернутися до хуків"):
            st.session_state["stage"] = "hooks"
            st.rerun()

        return

    st.html(
        """
        <div class="ams-section-kicker">
            04 / Рекламні креативи
        </div>

        <div class="ams-section-title">
            Перетворимо хуки на креативи.
        </div>

        <div class="ams-section-lead">
            Для кожного вибраного хука створимо
            підсилювальний текст, цінову пропозицію
            та CTA. Результати можна доопрацювати через AI.
        </div>
        """
    )

    st.caption(f"Вибрано хуків: {len(selected_hooks)}")

    if "creatives_model" not in st.session_state:
        st.session_state["creatives_model"] = (
            st.session_state.get(
                "hooks_model",
                DEFAULT_MODEL,
            )
        )

    if st.session_state["creatives_model"] not in MODELS:
        st.session_state["creatives_model"] = DEFAULT_MODEL

    model = st.selectbox(
        "AI-модель",
        options=list(MODELS.keys()),
        format_func=lambda name: MODELS[name],
        key="creatives_model",
    )

    notes = st.text_area(
        "Додаткові побажання до креативів (необов'язково)",
        placeholder=(
            "Наприклад: короткі буліти, акцент "
            "на практичності, CTA — «Приєднатися»."
        ),
        height=100,
        key="creatives_notes",
    )

    price_facts = find_price_facts(brief)

    if price_facts:
        st.caption(
            "У брифі знайдено ціну. "
            "Вона обов'язково відображатиметься "
            "в кожному креативі."
        )
    else:
        st.caption(
            "Підтвердженої ціни в брифі не знайдено."
        )

    with st.expander("Параметри генерації"):
        params = GENERATION_PARAMS.get(
            "creatives",
            {
                "temperature": 0.4,
                "max_tokens": 700,
            },
        )

        st.write(
            f"Temperature: **{params['temperature']}**"
        )

        st.write(
            f"Максимум токенів на креатив: "
            f"**{params['max_tokens']}**"
        )

    signature = get_creatives_signature(
        brief,
        segments,
        selected_hooks,
        model,
        notes,
    )

    if st.button(
        f"Згенерувати {len(selected_hooks)} креативів →",
        type="primary",
        use_container_width=True,
    ):
        results = []

        progress = st.progress(
            0,
            text="Створюємо рекламні тексти...",
        )

        error = None

        for index, hook in enumerate(selected_hooks):
            try:
                creative = generate_creative(
                    brief=brief,
                    segments=segments,
                    hook=hook,
                    model=model,
                    notes=notes,
                )

            except LLMError as exc:
                error = f"Креатив {index + 1}: {exc}"
                break

            else:
                results.append(creative)

                progress.progress(
                    len(results) / len(selected_hooks),
                    text=(
                        f"Створено {len(results)} "
                        f"із {len(selected_hooks)} креативів"
                    ),
                )

        progress.empty()

        st.session_state["creatives"] = results
        st.session_state["creatives_signature"] = signature
        st.session_state["creative_proposals"] = {}

        st.session_state["creatives_epoch"] = (
            st.session_state.get("creatives_epoch", 0) + 1
        )

        if error:
            st.error(error)

            if results:
                st.info(
                    f"Успішно створено й збережено "
                    f"{len(results)} креативів."
                )

        else:
            st.rerun()

    creatives = st.session_state.get("creatives", [])

    if creatives:
        st.divider()
        st.subheader("Готові тексти креативів")

        if (
            st.session_state.get("creatives_signature")
            != signature
        ):
            st.warning(
                "Вхідні дані змінилися. "
                "Згенеруйте креативи повторно, "
                "щоб врахувати нові налаштування."
            )

        for index, creative in enumerate(creatives):
            render_creative_card(
                index=index,
                creative=creative,
                brief=brief,
                segments=segments,
                model=model,
                notes=notes,
            )

        st.download_button(
            "↓ Завантажити креативи в JSON",
            data=json.dumps(
                {"creatives": creatives},
                ensure_ascii=False,
                indent=2,
            ),
            file_name="advertising_creatives.json",
            mime="application/json",
        )

    st.write("")

    if st.button("← Повернутися до хуків"):
        st.session_state["stage"] = "hooks"
        st.rerun()