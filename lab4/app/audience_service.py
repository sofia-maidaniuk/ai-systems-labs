from pydantic import ValidationError

from config import GENERATION_PARAMS
from llm import LLMError, generate_text
from prompts.audience import (
    AUDIENCE_SYSTEM_PROMPT,
    AUDIENCE_REVISION_PROMPT,
    build_audience_prompt,
    build_audience_revision_prompt,
)
from schemas import AudienceAnalysis, AudienceSegment


def analyze_audience(brief: dict, model: str) -> AudienceAnalysis:
    params = GENERATION_PARAMS["audience"]

    response = generate_text(
        model=model,
        system_prompt=AUDIENCE_SYSTEM_PROMPT,
        user_prompt=build_audience_prompt(brief),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    try:
        return AudienceAnalysis.model_validate_json(response)

    except ValidationError as exc:
        raise LLMError(
            "Модель повернула результат, який не відповідає "
            "структурі аналізу ЦА. Спробуйте повторити "
            "генерацію або перевірити ліміт токенів."
        ) from exc


def revise_audience_segment(
    brief: dict,
    segment: dict,
    feedback: str,
    model: str,
) -> AudienceSegment:
    params = GENERATION_PARAMS["revision"]

    response = generate_text(
        model=model,
        system_prompt=AUDIENCE_REVISION_PROMPT,
        user_prompt=build_audience_revision_prompt(
            brief,
            segment,
            feedback,
        ),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    try:
        return AudienceSegment.model_validate_json(response)

    except ValidationError as exc:
        raise LLMError(
            "Не вдалося перевірити оновлений сегмент. "
            "Спробуйте переформулювати правку."
        ) from exc
