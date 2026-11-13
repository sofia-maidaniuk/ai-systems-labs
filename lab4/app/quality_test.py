"""ЛР4 — перевірка якості локальної моделі для AI Marketing Strategist.

Запуск (у теці з bench.py та активованим .venv):
    python quality_test.py --label before --limit 2
    python quality_test.py --label before

Після оптимізації:
    python quality_test.py --label after --model qwen3:4b-instruct-2507-q4_K_M

Результати зберігаються у app/tests/quality_<label>.json.
"""

import argparse
import json
import time
from pathlib import Path

from openai import OpenAI


BRIEFS = [
    {
        "id": 1,
        "topic": "Клуб майстрів манікюру",
        "text": "Онлайн-клуб для майстрів манікюру за підпискою 390 грн/міс. У клубі є практичні уроки, зустрічі з експертами та професійна спільнота. Мета реклами — нові підписки.",
    },
    {
        "id": 2,
        "topic": "Клуб для жінок-водіїв",
        "text": "Підписний клуб для жінок, які вже мають водійське посвідчення, але невпевнено почуваються на дорозі. Є уроки паркування, розбір ситуацій і підтримка спільноти. 390 грн/міс. Мета — залучення учасниць.",
    },
    {
        "id": 3,
        "topic": "Онлайн-англійська",
        "text": "Онлайн-курси англійської для дорослих з уроками в малих групах двічі на тиждень. Вартість 2600 грн/міс. Мета — заявки на пробне заняття.",
    },
    {
        "id": 4,
        "topic": "Преміальний салон краси",
        "text": "Салон краси у Житомирі: догляд за волоссям, фарбування, індивідуальні консультації. Середній чек від 1500 грн. Мета — записи на послуги, акцент на сервісі та якості.",
    },
    {
        "id": 5,
        "topic": "Локальна кав'ярня",
        "text": "Невелика кав'ярня у центрі Житомира. Пропонує каву та сніданки, працює з 8:00. Мета — залучити відвідувачів у будні вранці. Рекламний бюджет невеликий.",
    },
    {
        "id": 6,
        "topic": "CRM для малого бізнесу",
        "text": "Хмарна CRM для малих сервісних компаній: облік клієнтів, заявок, завдань і статусів замовлень. Підписка від 600 грн/міс. Мета — заявки на демонстрацію продукту (B2B).",
    },
    {
        "id": 7,
        "topic": "Вироби з натурального каменю",
        "text": "Компанія виготовляє стільниці й підвіконня з натурального каменю за індивідуальними розмірами. Фіксованої ціни немає: розрахунок після консультації. Мета — отримати заявки на прорахунок.",
    },
    {
        "id": 8,
        "topic": "Фітнес-підписка",
        "text": "Онлайн-платформа домашніх тренувань із короткими відеозаняттями та різними рівнями складності. Підписка 490 грн/міс. Мета — реєстрації. Не можна обіцяти гарантованого схуднення.",
    },
    {
        "id": 9,
        "topic": "Екотовари без зазначеної ціни",
        "text": "Магазин багаторазових пляшок, контейнерів і сумок для покупок. Є доставка Україною. Ціну та точні умови доставки не вказано. Мета — переходи до каталогу.",
    },
    {
        "id": 10,
        "topic": "Неповний бриф",
        "text": "Запускаємо новий продукт. Потрібна реклама. Іншої інформації поки немає.",
    },
]

SYSTEM = (
    "Ти асистент українськомовного маркетолога. "
    "Працюй лише з фактами, які містяться у брифі. "
    "Сегменти аудиторії та рекламні ідеї — гіпотези, а не доведені факти. "
    "Не вигадуй цін, результатів, відгуків, знижок і характеристик. "
    "Якщо даних бракує, вкажи, що потрібно уточнити. "
    "Відповідай українською коротко й конкретно, лише валідним JSON."
)

AUDIENCE_PROMPT = """Проаналізуй маркетинговий бриф:
{brief}

Створи рівно ТРИ можливі сегменти ЦА. Для кожного вкажи назву,
основну потребу, можливий біль та можливе заперечення.
Також назви до трьох даних, яких бракує для впевненішого аналізу.
Кожне поле — не більше одного короткого речення.
Формат JSON, без пояснень поза JSON:
{{"segments":[{{"name":"...","need":"...","pain":"...","objection":"..."}}],
"missing_info":["..."]}}
"""

CREATIVE_PROMPT = """Маркетинговий бриф:
{brief}

Обраний гіпотетичний сегмент аудиторії:
{segment}

Створи рівно ТРИ РІЗНІ рекламні концепції саме для цього сегмента.
Кожна повинна містити angle (підхід), hook (заголовок),
body (одне-два речення рекламного тексту), cta (заклик до дії),
visual (коротка ідея візуалу). Не вигадуй факти та обіцянки.
Формат JSON, без пояснень поза JSON:
{{"concepts":[{{"angle":"...","hook":"...","body":"...","cta":"...","visual":"..."}}]}}
"""


def ask_json(client, model, prompt, limit):
    started = time.perf_counter()
    answer = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        seed=1,
        max_tokens=limit,
        response_format={"type": "json_object"},
    )
    raw = answer.choices[0].message.content or ""
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Відповідь не є JSON-об'єктом")
    return {
        "text": raw,
        "data": parsed,
        "seconds": round(time.perf_counter() - started, 2),
        "finish_reason": answer.choices[0].finish_reason,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:4b-instruct-2507-q8_0")
    parser.add_argument("--label", choices=["before", "after"], default="before")
    parser.add_argument("--limit", type=int, default=10, help="Кількість тестових брифів, від 1 до 10")
    args = parser.parse_args()
    if not 1 <= args.limit <= len(BRIEFS):
        parser.error("--limit має бути від 1 до 10")

    folder = Path(__file__).resolve().parent / "tests"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "briefs.json").write_text(
        json.dumps(BRIEFS, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    path = folder / f"quality_{args.label}.json"
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama", timeout=240, max_retries=1)
    entries = []

    for brief in BRIEFS[:args.limit]:
        print(f"[{brief['id']}/{args.limit}] {brief['topic']}", flush=True)
        entry = {"brief": brief, "audience": None, "creatives": None, "error": None}
        try:
            first = ask_json(client, args.model, AUDIENCE_PROMPT.format(brief=brief["text"]), 650)
            entry["audience"] = first
            segments = first["data"].get("segments", [])
            if len(segments) != 3:
                raise ValueError(f"Очікували 3 сегменти, отримали {len(segments)}")
            chosen = segments[0]  # однакове правило вибору сегмента для порівняння моделей
            second = ask_json(
                client, args.model,
                CREATIVE_PROMPT.format(
                    brief=brief["text"],
                    segment=json.dumps(chosen, ensure_ascii=False),
                ),
                750,
            )
            entry["creatives"] = second
            concepts = second["data"].get("concepts", [])
            if len(concepts) != 3:
                raise ValueError(f"Очікували 3 концепції, отримали {len(concepts)}")
            print("  Готово: 3 сегменти, 3 концепції", flush=True)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  Помилка: {entry['error']}", flush=True)
        entries.append(entry)
        path.write_text(
            json.dumps({"model": args.model, "label": args.label, "results": entries},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    good = sum(item["error"] is None for item in entries)
    print(f"\nУспішних тестів: {good}/{len(entries)}")
    print(f"Результати збережено: {path}")
    print("Цей показник оцінює лише технічне виконання; зміст відповідей треба перевірити окремо.")


if __name__ == "__main__":
    main()
