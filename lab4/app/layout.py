import streamlit as st


STAGES = [
    ("brief", "Бриф"),
    ("audience", "Аудиторія"),
    ("hooks", "Хуки"),
    ("creatives", "Креативи"),
]


def render_header(stage):
    st.html(
        """
        <div class="ams-topline">
            <div class="ams-wordmark">
                <div class="ams-symbol">✦</div>
                AI / MARKETING STRATEGIST
            </div>
            <div class="ams-topnote">
                LOCAL CREATIVE WORKSPACE · V1
            </div>
        </div>
        """
    )

    if stage == "brief":
        st.html(
            """
            <div class="ams-hero">
                <div class="ams-hero-star" aria-hidden="true">✳</div>

                <div class="ams-hero-content">
                    <div class="ams-eyebrow">
                        ✦ Від ідеї до сильного повідомлення
                    </div>

                    <h1>
                        Маркетинг починається<br>
                        з <em>правильних сенсів.</em>
                    </h1>

                    <p>
                        Опишіть свій продукт. Далі ми проаналізуємо
                        аудиторію, знайдемо сильні хуки та підготуємо
                        тексти рекламних креативів.
                    </p>
                </div>

                <div class="ams-hero-foot">
                    <span>
                        <span class="ams-red-dot">●</span>
                        ПРАЦЮЄ ЛОКАЛЬНО НА ВАШОМУ КОМП’ЮТЕРІ
                    </span>
                    <span>
                        <b>BRIEF</b> / AUDIENCE / HOOKS / CREATIVES
                    </span>
                </div>
            </div>
            """
        )

    steps = "".join(
        (
            f'<div class="ams-step'
            f'{" active" if name == stage else ""}">'
            f"<strong>{number:02d}</strong> {label}"
            "</div>"
        )
        for number, (name, label) in enumerate(STAGES, start=1)
    )

    st.html(
        f'<div class="ams-steps" aria-label="Етапи роботи">'
        f"{steps}</div>"
    )


def render_footer(stage):
    step_number = next(
        (
            number
            for number, (name, _) in enumerate(STAGES, start=1)
            if name == stage
        ),
        1,
    )

    st.html(
        f"""
        <div class="ams-endnote">
            ✦ AI Marketing Strategist ·
            Локальна розробка · Крок {step_number:02d} / 04
        </div>
        """
    )