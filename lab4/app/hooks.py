import json

import streamlit as st

from config import DEFAULT_MODEL, GENERATION_PARAMS, MODELS
from hooks_service import generate_hooks, revise_hook
from llm import LLMError


HOOK_COUNT = 10


def get_input_signature(brief, segments, model, notes):
    return json.dumps(
        {
            "brief": brief,
            "segments": segments,
            "model": model,
            "notes": notes,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def render_hook_revision(index, hook, brief, segments, model, notes):
    proposals = st.session_state.setdefault("hooks_proposals", {})
    proposal = proposals.get(str(index))
    epoch = st.session_state.get("hooks_epoch", 0)

    with st.expander("Правка з AI", expanded=(proposal is not None)):
        with st.form(f"hook_revision_{epoch}_{index}"):
            feedback = st.text_area(
                "Що потрібно змінити?",
                placeholder=(
                    "Наприклад: використай конструкцію «Досить...», "
                    "зроби заголовок конкретнішим і коротшим."
                ),
                height=110,
            )
            submitted = st.form_submit_button(
                "Переробити хук з AI",
                use_container_width=True,
            )

        if submitted:
            if len(feedback.strip()) < 10:
                st.warning("Опишіть побажання детальніше — щонайменше 10 символів.")
            else:
                with st.spinner("AI доопрацьовує хук..."):
                    try:
                        result = revise_hook(
                            brief=brief,
                            segments=segments,
                            hook=hook,
                            feedback=feedback,
                            model=model,
                            notes=notes,
                        )
                    except LLMError as exc:
                        st.error(str(exc))
                    else:
                        proposals[str(index)] = result.model_dump()
                        st.rerun()

        if proposal is not None:
            st.markdown("#### Запропонована AI версія")
            st.markdown(f"**{proposal['text']}**")
            st.caption(f"Підхід: {proposal['approach']}")
            st.caption(f"Рекламний сенс: {proposal['basis']}")

            accept_col, reject_col = st.columns(2)
            with accept_col:
                if st.button(
                    "Прийняти правку",
                    key=f"accept_hook_revision_{index}",
                    type="primary",
                    use_container_width=True,
                ):
                    hooks = st.session_state["hooks"].copy()
                    hooks[index] = proposal.copy()
                    st.session_state["hooks"] = hooks
                    st.session_state["hooks_epoch"] = epoch + 1
                    proposals.pop(str(index), None)
                    st.session_state.pop("selected_hooks", None)
                    st.session_state.pop("creatives", None)
                    st.rerun()

            with reject_col:
                if st.button(
                    "Відхилити правку",
                    key=f"reject_hook_revision_{index}",
                    use_container_width=True,
                ):
                    proposals.pop(str(index), None)
                    st.session_state["hooks_epoch"] = epoch + 1
                    st.rerun()


def render_hook_results(brief, segments, model, notes):
    hooks = st.session_state.get("hooks")
    if not hooks:
        return

    is_current = (
        st.session_state.get("hooks_input_signature")
        == get_input_signature(brief, segments, model, notes)
    )

    st.divider()
    st.subheader("Згенеровані рекламні хуки")
    generated_model = st.session_state.get("hooks_model_used", model)
    st.caption(
        f"{len(hooks)} варіантів · "
        f"Модель: {MODELS.get(generated_model, generated_model)}"
    )

    if len(hooks) != HOOK_COUNT:
        st.info("Це результат попередньої генерації. Нова версія створює 10 хуків.")
    if not is_current:
        st.warning(
            "Вхідні дані або модель змінилися. "
            "Для актуальних результатів згенеруйте хуки повторно."
        )

    for index, hook in enumerate(hooks):
        with st.container(border=True):
            col_content, col_select = st.columns([5, 1], gap="medium")
            with col_content:
                st.caption(f"ХУК {index + 1:02d} · {hook['approach']}")
                st.markdown(f"**{hook['text']}**")
                st.caption(f"Рекламний сенс: {hook['basis']}")
            with col_select:
                st.checkbox("Обрати", key=f"hook_select_{index}")

            render_hook_revision(
                index=index,
                hook=hook,
                brief=brief,
                segments=segments,
                model=model,
                notes=notes,
            )

    selected_indexes = [
        index
        for index in range(len(hooks))
        if st.session_state.get(f"hook_select_{index}", False)
    ]

    st.divider()
    st.subheader("Вибрані хуки")
    st.write(f"Обрано **{len(selected_indexes)} із {len(hooks)}** варіантів.")

    if st.button(
        "Перейти до рекламних креативів →",
        type="primary",
        use_container_width=True,
        disabled=(not selected_indexes or not is_current),
    ):
        st.session_state["selected_hooks"] = [
            hooks[index].copy() for index in selected_indexes
        ]
        st.session_state["stage"] = "creatives"
        st.rerun()

    st.download_button(
        "↓ Завантажити всі хуки у JSON",
        data=json.dumps({"hooks": hooks}, ensure_ascii=False, indent=2),
        file_name="advertising_hooks.json",
        mime="application/json",
    )


def render_hooks():
    brief = st.session_state.get("brief")
    segments = st.session_state.get("audience_segments")

    if not brief or not segments:
        st.warning(
            "Для генерації хуків потрібні маркетинговий бриф "
            "і результати аналізу цільової аудиторії."
        )
        if st.button("← Повернутися до аналізу ЦА"):
            st.session_state["stage"] = "audience"
            st.rerun()
        return

    st.html(
        """
        <div class="ams-section-kicker">03 / Рекламні хуки</div>
        <div class="ams-section-title">Знайдемо сильні рекламні сенси.</div>
        <div class="ams-section-lead">
            Створимо 10 заголовків для рекламних банерів
            на основі брифу та всіх трьох сегментів ЦА.
            Результати можна доопрацьовувати через AI.
        </div>
        """
    )

    st.subheader("Налаштування генерації")

    if "hooks_model" not in st.session_state:
        st.session_state["hooks_model"] = st.session_state.get(
            "selected_model", DEFAULT_MODEL
        )
    if st.session_state["hooks_model"] not in MODELS:
        st.session_state["hooks_model"] = DEFAULT_MODEL

    model = st.selectbox(
        "AI-модель",
        options=list(MODELS.keys()),
        format_func=lambda name: MODELS[name],
        key="hooks_model",
    )

    notes = st.text_area(
        "Що важливо донести в рекламі? (необов'язково)",
        placeholder=(
            "Наприклад: акцент на самостійних поїздках і паркуванні. "
            "Хочу сильні заголовки без перебільшення страхів."
        ),
        height=110,
        key="hooks_notes",
    )

    with st.expander("Параметри генерації"):
        params = GENERATION_PARAMS["hooks"]
        st.write(f"Temperature: **{params['temperature']}**")
        st.write(f"Максимум токенів: **{params['max_tokens']}**")
        st.caption("Використовуються маркетинговий бриф і всі три сегменти ЦА.")

    if st.button(
        "Згенерувати 10 хуків →",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Генеруємо рекламні хуки..."):
            try:
                result = generate_hooks(
                    brief=brief,
                    segments=segments,
                    model=model,
                    notes=notes,
                )
            except LLMError as exc:
                st.error(str(exc))
            else:
                old_count = len(st.session_state.get("hooks", []))
                st.session_state["hooks"] = [
                    hook.model_dump() for hook in result.hooks
                ]
                st.session_state["hooks_model_used"] = model
                st.session_state["hooks_input_signature"] = get_input_signature(
                    brief, segments, model, notes
                )
                st.session_state["hooks_proposals"] = {}
                st.session_state["hooks_epoch"] = (
                    st.session_state.get("hooks_epoch", 0) + 1
                )
                st.session_state.pop("selected_hooks", None)
                st.session_state.pop("creatives", None)
                for index in range(max(old_count, HOOK_COUNT)):
                    st.session_state.pop(f"hook_select_{index}", None)
                st.rerun()

    render_hook_results(brief, segments, model, notes)

    st.write("")
    if st.button("← Повернутися до аналізу ЦА"):
        st.session_state["stage"] = "audience"
        st.rerun()
