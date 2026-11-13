from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)

from config import OLLAMA_BASE_URL, REQUEST_TIMEOUT


class LLMError(Exception):
    pass


def get_client():
    return OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )


def get_error_details(exc):
    try:
        error_data = exc.response.json()

        if isinstance(error_data, dict):
            details = error_data.get("error", error_data)

            if isinstance(details, dict):
                return str(details.get("message", details))

            return str(details)

        return str(error_data)

    except ValueError:
        return exc.response.text


def list_models():
    try:
        response = get_client().models.list()
        return [model.id for model in response.data]

    except APITimeoutError as exc:
        raise LLMError(
            "Ollama не відповідає вчасно."
        ) from exc

    except APIConnectionError as exc:
        raise LLMError(
            "Не вдалося підключитися до Ollama. "
            "Перевірте, чи запущений сервер."
        ) from exc

    except APIStatusError as exc:
        raise LLMError(
            f"Помилка Ollama HTTP {exc.status_code}: "
            f"{get_error_details(exc)}"
        ) from exc


def generate_text(
    model,
    system_prompt,
    user_prompt,
    temperature,
    max_tokens,
    json_mode=False,
):
    request = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        request["response_format"] = {
            "type": "json_object",
        }

    try:
        response = get_client().chat.completions.create(
            **request
        )

    except APITimeoutError as exc:
        raise LLMError(
            "Час очікування відповіді минув. "
            "Спробуйте повторити запит."
        ) from exc

    except APIConnectionError as exc:
        raise LLMError(
            "Немає з'єднання з Ollama. "
            "Переконайтеся, що сервер працює."
        ) from exc

    except APIStatusError as exc:
        raise LLMError(
            f"Модель повернула помилку HTTP {exc.status_code}: "
            f"{get_error_details(exc)}"
        ) from exc

    if not response.choices:
        raise LLMError(
            "Модель не повернула відповідь."
        )

    choice = response.choices[0]

    if choice.finish_reason == "length":
        raise LLMError(
            "Модель досягла ліміту токенів і не завершила "
            "відповідь. Потрібно збільшити max_tokens "
            "або перевірити доступний контекст моделі."
        )

    answer = choice.message.content

    if not isinstance(answer, str) or not answer.strip():
        raise LLMError(
            "Модель повернула порожню відповідь."
        )

    return answer.strip()


def check_connection(model):
    available_models = list_models()

    if model not in available_models:
        raise LLMError(
            f"Модель {model} не знайдено в Ollama. "
            f"Завантажте її: ollama pull {model}"
        )

    return generate_text(
        model=model,
        system_prompt=(
            "Ти перевіряєш підключення до застосунку. "
            "Відповідай українською, одним словом."
        ),
        user_prompt="Напиши слово ГОТОВО.",
        temperature=0,
        max_tokens=32,
    )
