import html
import json

import streamlit as st
from pydantic import ValidationError

from audience_service import (
    analyze_audience,
    revise_audience_segment,
)
from config import (
    DEFAULT_MODEL,
    GENERATION_PARAMS,
    MODELS,
    OLLAMA_BASE_URL,
)
from llm import LLMError, check_connection
from schemas import AudienceSegment


FIELD_LABELS = {
    "requests": "Запити",
    "pains": "Болі",
    "needs": "Потреби",
    "fears": "Страхи",
    "objections": "Заперечення",
}


def update_segment(index, segment):
    segments = st.session_state["audience_segments"].copy()
    segments[index] = segment

    st.session_state["audience_segments"] = segments
    st.session_state["audience_epoch"] = (
        st.session_state.get("audience_epoch", 0) + 1
    )

    st.session_state.setdefault(
        "audience_proposals", {}
    ).pop(str(index), None)


def render_segment_details(segment):
    st.write(segment["description"])

    col_left, col_right = st.columns(2, gap="large")
    fields = list(FIELD_LABELS.items())

    for position, (field, label) in enumerate(fields):
        column = col_left if position % 2 == 0 else col_right

        with column:
            st.markdown(f"**{label}**")

            for item in segment[field]:
                st.write(f"• {item}")


def render_segment_editor(index, segment):
    epoch = st.session_state.get("audience_epoch", 0)

    with st.form(f"segment_editor_{index}_{epoch}"):
        name = st.text_input(
            "Назва сегмента",
            value=segment["name"],
        )

        description = st.text_area(
            "Короткий опис",
            value=segment["description"],
            height=90,
        )

        edited_fields = {}

        for field, label in FIELD_LABELS.items():
            edited_fields[field] = st.text_area(
                label,
                value="\n".join(segment[field]),
                height=85,
                help="Кожен пункт записуйте з нового рядка.",
            )

        saved = st.form_submit_button(
            "Зберегти зміни",
            use_container_width=True,
        )

    if saved:
        data = {
            "name": name.strip(),
            "description": description.strip(),
        }

        for field, value in edited_fields.items():
            data[field] = [
                line.strip().lstrip("•- ").strip()
                for line in value.splitlines()
                if line.strip().lstrip("•- ").strip()
            ]

        try:
            updated = AudienceSegment.model_validate(data)

        except ValidationError:
            st.error(
                "Перевірте поля: назва й опис мають бути "
                "заповнені, а кожен список повинен "
                "містити хоча б один пункт."
            )

        else:
            update_segment(index, updated.model_dump())
            st.rerun()


def render_segment_revision(index, segment, brief, model):
    with st.form(f"segment_revision_{index}"):
        feedback = st.text_area(
            "Що потрібно змінити?",
            placeholder=(
                "Наприклад: сегмент надто вузький. "
                "Зосередься на водійках, які мають права, "
                "але відчувають нестачу практичних знань."
            ),
            height=110,
        )

        submitted = st.form_submit_button(
            "Переробити сегмент з AI",
            use_container_width=True,
        )

    if submitted:
        if len(feedback.strip()) < 10:
            st.warning(
                "Опишіть правку детальніше — "
                "щонайменше 10 символів."
            )

        else:
            with st.spinner("AI доопрацьовує сегмент..."):
                try:
                    proposal = revise_audience_segment(
                        brief=brief,
                        segment=segment,
                        feedback=feedback,
                        model=model,
                    )

                except LLMError as exc:
                    st.error(str(exc))

                else:
                    st.session_state.setdefault(
                        "audience_proposals", {}
                    )[str(index)] = proposal.model_dump()
                    st.rerun()

    proposal = st.session_state.get(
        "audience_proposals", {}
    ).get(str(index))

    if proposal is not None:
        st.markdown("#### Запропонована AI версія")
        render_segment_details(proposal)

        accept_col, reject_col = st.columns(2)

        with accept_col:
            if st.button(
                "Прийняти правку",
                key=f"accept_revision_{index}",
                type="primary",
                use_container_width=True,
            ):
                update_segment(index, proposal)
                st.rerun()

        with reject_col:
            if st.button(
                "Відхилити правку",
                key=f"reject_revision_{index}",
                use_container_width=True,
            ):
                st.session_state["audience_proposals"].pop(
                    str(index), None
                )
                st.rerun()


def render_segments(brief, model):
    segments = st.session_state.get("audience_segments")

    if not segments:
        return

    st.divider()
    st.subheader("Результати аналізу")

    generated_model = st.session_state.get("audience_model", model)

    st.caption(
        "3 маркетингові гіпотези · "
        f"Модель генерації: {MODELS.get(generated_model, generated_model)}"
    )

    brief_signature = json.dumps(
        brief,
        ensure_ascii=False,
        sort_keys=True,
    )

    brief_is_current = (
        st.session_state.get("audience_brief_signature")
        == brief_signature
    )

    if not brief_is_current:
        st.warning(
            "Бриф було змінено після аналізу. "
            "Перегенеруйте сегменти перед створенням хуків."
        )

    for index, segment in enumerate(segments):
        title = f"{index + 1:02d} · {segment['name']}"

        with st.expander(title, expanded=(index == 0)):
            view_tab, edit_tab, ai_tab = st.tabs(
                [
                    "Перегляд",
                    "Редагувати",
                    "Правка з AI",
                ]
            )

            with view_tab:
                render_segment_details(segment)

            with edit_tab:
                render_segment_editor(index, segment)

            with ai_tab:
                render_segment_revision(
                    index,
                    segment,
                    brief,
                    model,
                )

    st.divider()

    st.caption(
        "Усі три сегменти збережено для наступного етапу. "
        "Генератор хуків використовуватиме спільні та різні "
        "запити, болі й потреби всієї аудиторії."
    )

    st.download_button(
        "↓ Завантажити сегменти в JSON",
        data=json.dumps(
            {"segments": segments},
            ensure_ascii=False,
            indent=2,
        ),
        file_name="audience_segments.json",
        mime="application/json",
    )


def render_audience():
    brief = st.session_state.get("brief")

    if not brief:
        st.warning("Спочатку заповніть маркетинговий бриф.")

        if st.button("← Повернутися до брифу"):
            st.session_state["stage"] = "brief"
            st.rerun()

        return

    product_name = html.escape(brief["product_name"])

    st.html(
        f"""
        <div class="ams-section-kicker">
            02 / Цільова аудиторія
        </div>

        <div class="ams-section-title">
            Знайдемо вашу аудиторію.
        </div>

        <div class="ams-section-lead">
            На основі брифу створимо три гіпотези сегментів.
            Результати можна редагувати та доопрацьовувати.
        </div>

        <div class="ams-result">
            <h3>{product_name}</h3>
            <div class="ams-result-sub">
                Маркетинговий бриф підключено до аналізу.
            </div>
        </div>
        """
    )

    st.write("")
    st.subheader("AI-модель")

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = DEFAULT_MODEL

    model = st.selectbox(
        "Модель для аналізу",
        options=list(MODELS.keys()),
        format_func=lambda name: MODELS[name],
        key="selected_model",
    )

    st.caption(f"API: {OLLAMA_BASE_URL}")

    with st.expander("Параметри генерації"):
        params = GENERATION_PARAMS["audience"]

        st.write(f"Temperature: **{params['temperature']}**")
        st.write(
            f"Ліміт відповіді: **{params['max_tokens']} токенів**"
        )
        st.caption(
            "Розмір контексту Ollama налаштовується "
            "окремо через Modelfile."
        )

    col_check, col_generate = st.columns(
        [1, 1.5],
        gap="small",
    )

    with col_check:
        if st.button(
            "Перевірити підключення",
            use_container_width=True,
        ):
            with st.spinner("Перевіряємо Ollama..."):
                try:
                    answer = check_connection(model)
                    st.success(f"Модель відповідає: {answer}")

                except LLMError as exc:
                    st.error(str(exc))

    with col_generate:
        generate_clicked = st.button(
            "Проаналізувати ЦА →",
            type="primary",
            use_container_width=True,
        )

    if generate_clicked:
        with st.spinner("Генеруємо три сегменти ЦА..."):
            try:
                analysis = analyze_audience(brief, model)

            except LLMError as exc:
                st.error(str(exc))

            else:
                st.session_state["audience_segments"] = [
                    segment.model_dump()
                    for segment in analysis.segments
                ]

                st.session_state["audience_model"] = model

                st.session_state["audience_brief_signature"] = (
                    json.dumps(
                        brief,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )

                st.session_state["audience_proposals"] = {}
                st.session_state["audience_epoch"] = (
                    st.session_state.get("audience_epoch", 0) + 1
                )

                st.rerun()

    render_segments(brief, model)

    st.write("")

    if st.button("← Повернутися до брифу"):
        st.session_state["stage"] = "brief"
        st.rerun()