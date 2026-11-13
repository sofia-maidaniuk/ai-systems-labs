from pydantic import ValidationError

from config import GENERATION_PARAMS
from llm import LLMError, generate_text
from prompts.hooks import (
    HOOKS_SYSTEM_PROMPT,
    HOOKS_REVISION_PROMPT,
    build_hooks_prompt,
    build_hook_revision_prompt,
)
from schemas import HooksResult, HookItem


def generate_hooks(
    brief: dict,
    segments: list[dict],
    model: str,
    notes: str = "",
) -> HooksResult:
    params = GENERATION_PARAMS["hooks"]

    response = generate_text(
        model=model,
        system_prompt=HOOKS_SYSTEM_PROMPT,
        user_prompt=build_hooks_prompt(
            brief=brief,
            segments=segments,
            notes=notes,
        ),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    try:
        return HooksResult.model_validate_json(response)
    except ValidationError as exc:
        raise LLMError(
            "Модель повернула некоректний результат або не 10 хуків. "
            "Спробуйте повторити генерацію."
        ) from exc


def revise_hook(
    brief: dict,
    segments: list[dict],
    hook: dict,
    feedback: str,
    model: str,
    notes: str = "",
) -> HookItem:
    params = GENERATION_PARAMS["revision"]

    response = generate_text(
        model=model,
        system_prompt=HOOKS_REVISION_PROMPT,
        user_prompt=build_hook_revision_prompt(
            brief=brief,
            segments=segments,
            hook=hook,
            feedback=feedback,
            notes=notes,
        ),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    try:
        return HookItem.model_validate_json(response)
    except ValidationError as exc:
        raise LLMError(
            "Модель повернула некоректну AI-правку. "
            "Спробуйте переформулювати побажання."
        ) from exc
