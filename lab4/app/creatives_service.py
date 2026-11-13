import re

from pydantic import ValidationError

from config import GENERATION_PARAMS
from llm import LLMError, generate_text
from prompts.creatives import (
    CREATIVE_SYSTEM_PROMPT,
    CREATIVE_REVISION_PROMPT,
    build_creative_prompt,
    build_creative_revision_prompt,
)
from schemas import CreativeDraft


PRICE_PATTERN = re.compile(
    r"(?<!\w)(\d[\d \u00a0]*(?:[.,]\d{1,2})?)"
    r"\s*(грн|₴|UAH|USD|EUR|€|\$)"
    r"|(?<!\w)([€$₴])\s*"
    r"(\d[\d \u00a0]*(?:[.,]\d{1,2})?)",
    re.IGNORECASE,
)

PRICE_KEY_PATTERN = re.compile(
    r"price|pricing|cost|fee|ціна|вартіст|тариф|оплат",
    re.IGNORECASE,
)


def price_amounts(text: str) -> set[str]:
    amounts = set()

    for match in PRICE_PATTERN.finditer(text):
        raw = match.group(1) or match.group(4)

        amount = (
            raw.replace(" ", "")
            .replace("\u00a0", "")
            .replace(",", ".")
        )

        amounts.add(amount)

    return amounts


def find_price_facts(brief: dict) -> list[str]:
    facts = []
    seen = set()

    def append(value):
        clean = " ".join(value.split())

        if clean and clean not in seen:
            seen.add(clean)
            facts.append(clean)

    def visit(value, key=""):
        if isinstance(value, dict):
            for subkey, child in value.items():
                visit(child, str(subkey))

        elif isinstance(value, list):
            for child in value:
                visit(child, key)

        elif isinstance(value, (str, int, float)):
            if isinstance(value, bool):
                return

            text = str(value).strip()

            if not text or text in {"0", "0.0", "0,00"}:
                return

            if (
                PRICE_KEY_PATTERN.search(key)
                and re.search(r"\d", text)
            ):
                append(f"{key}: {text}")

            for match in PRICE_PATTERN.finditer(text):
                start = max(0, match.start() - 45)
                end = min(len(text), match.end() + 50)

                append(text[start:end])

    visit(brief)

    return facts[:12]


def parse_creative_response(response: str) -> CreativeDraft:
    try:
        return CreativeDraft.model_validate_json(response)

    except ValidationError as exc:
        raise LLMError(
            "Модель повернула некоректний формат "
            "рекламного креативу."
        ) from exc


def validate_draft(
    draft: CreativeDraft,
    price_facts: list[str],
    previous_price: str = "",
) -> CreativeDraft:
    if draft.body_style == "text" and len(draft.body) != 1:
        raise LLMError(
            "Текстове підсилення повинно містити "
            "одне речення."
        )

    if draft.body_style == "bullets" and len(draft.body) < 2:
        raise LLMError(
            "Для списку переваг потрібно "
            "щонайменше два пункти."
        )

    if price_facts:
        if not draft.price.strip():
            draft.price = previous_price.strip()

        if not draft.price.strip():
            raise LLMError(
                "У брифі є ціна, але модель "
                "не додала її до креативу."
            )

        available_amounts = set()

        for fact in price_facts:
            available_amounts.update(
                price_amounts(fact)
            )

        shown_amounts = price_amounts(draft.price)

        if (
            available_amounts
            and not shown_amounts.intersection(
                available_amounts
            )
        ):
            raise LLMError(
                "AI використав ціну, якої немає "
                "в маркетинговому брифі."
            )

    else:
        draft.price = ""

    return draft


def extract_exact_cta(feedback: str) -> str | None:
    match = re.search(
        r"(?im)^\s*"
        r"(?:(?:зам[іи]ни|зм[іи]ни|постав|"
        r"вкажи|напиши|зроби|онови)\s+)?"
        r"(?:текст\s+)?"
        r"(?:CTA|СТА|кнопк\w*)"
        r"\s*[:—–-]\s*(.+?)\s*$",
        feedback,
    )

    if match is None:
        return None

    return match.group(1).strip().strip('«»"“”')


def requested_fields(feedback: str) -> set[str]:
    text = feedback.casefold()

    if re.search(
        r"(?:весь|всю|повністю|цілком).*креатив"
        r"|креатив.*(?:повністю|цілком|весь)",
        text,
    ):
        return {"body_style", "body", "cta", "price"}

    fields = set()

    if re.search(
        r"\bcta\b|\bста\b|кнопк|заклик",
        text,
    ):
        fields.add("cta")

    if re.search(
        r"ціну|ціна|ціни|цінов|тариф|вартіст|"
        r"\bprice\b",
        text,
    ):
        fields.add("price")

    if re.search(
        r"підсил|буліт|переваг|"
        r"основн.{0,15}текст|"
        r"опис|текстов.{0,10}блок",
        text,
    ):
        fields.update({"body_style", "body"})

    if not fields:
        return {"body_style", "body", "cta", "price"}

    return fields


def as_creative(
    draft: CreativeDraft,
    hook: str,
    approach: str,
) -> dict:
    return {
        "hook": hook,
        "approach": approach,
        "body_style": draft.body_style,
        "body": draft.body,
        "price": draft.price.strip(),
        "cta": draft.cta.strip(),
    }


def generate_creative(
    brief: dict,
    segments: list[dict],
    hook: dict,
    model: str,
    notes: str = "",
) -> dict:
    params = GENERATION_PARAMS.get(
        "creatives",
        {
            "temperature": 0.4,
            "max_tokens": 700,
        },
    )

    price_facts = find_price_facts(brief)

    response = generate_text(
        model=model,
        system_prompt=CREATIVE_SYSTEM_PROMPT,
        user_prompt=build_creative_prompt(
            brief=brief,
            segments=segments,
            hook=hook,
            price_facts=price_facts,
            notes=notes,
        ),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    draft = parse_creative_response(response)

    draft = validate_draft(
        draft=draft,
        price_facts=price_facts,
    )

    return as_creative(
        draft,
        hook["text"],
        hook["approach"],
    )


def revise_creative(
    brief: dict,
    segments: list[dict],
    creative: dict,
    feedback: str,
    model: str,
    notes: str = "",
) -> dict:
    fields = requested_fields(feedback)
    exact_cta = extract_exact_cta(feedback)

    if exact_cta is not None:
        if not 3 <= len(exact_cta) <= 60:
            raise LLMError(
                "CTA повинен містити від 3 до 60 символів."
            )

        if fields == {"cta"}:
            return {
                **creative,
                "cta": exact_cta,
            }

    params = GENERATION_PARAMS.get(
        "revision",
        {
            "temperature": 0.3,
            "max_tokens": 900,
        },
    )

    price_facts = find_price_facts(brief)

    response = generate_text(
        model=model,
        system_prompt=CREATIVE_REVISION_PROMPT,
        user_prompt=build_creative_revision_prompt(
            brief=brief,
            segments=segments,
            creative=creative,
            price_facts=price_facts,
            feedback=feedback,
            notes=notes,
        ),
        temperature=params["temperature"],
        max_tokens=params["max_tokens"],
        json_mode=True,
    )

    draft = parse_creative_response(response)

    updated = creative.copy()

    if "body" in fields:
        updated["body"] = draft.body.copy()
        updated["body_style"] = draft.body_style

    if "cta" in fields:
        updated["cta"] = (
            exact_cta
            if exact_cta is not None
            else draft.cta.strip()
        )

    if "price" in fields:
        updated["price"] = draft.price.strip()

    if "body" in fields:
        hook_text = " ".join(
            creative["hook"].casefold().split()
        )

        for item in updated["body"]:
            item_text = " ".join(
                item.casefold().split()
            )

            if item_text == hook_text:
                raise LLMError(
                    "AI повторив хук замість підсилення. "
                    "Правку не застосовано."
                )

    try:
        final_draft = CreativeDraft.model_validate(
            {
                "body_style": updated["body_style"],
                "body": updated["body"],
                "cta": updated["cta"],
                "price": updated["price"],
            }
        )

    except ValidationError as exc:
        raise LLMError(
            "Результат AI-правки не відповідає "
            "структурі рекламного креативу."
        ) from exc

    final_draft = validate_draft(
        draft=final_draft,
        price_facts=price_facts,
        previous_price=creative.get("price", ""),
    )

    if "price" in fields:
        requested_amounts = price_amounts(feedback)

        if (
            requested_amounts
            and not requested_amounts.intersection(
                price_amounts(final_draft.price)
            )
        ):
            raise LLMError(
                "AI не врахував ціну, зазначену "
                "в побажанні. Спробуйте уточнити правку."
            )

    return as_creative(
        final_draft,
        creative["hook"],
        creative["approach"],
    )