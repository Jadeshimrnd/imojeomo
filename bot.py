import os
import random
import sys
from pathlib import Path

# 업로드 등으로 가상환경의 원래 Python 경로가 달라진 경우에도
# 프로젝트에 설치된 패키지를 찾을 수 있게 합니다.
local_site_packages = Path(__file__).parent / ".venv" / "Lib" / "site-packages"
if local_site_packages.exists():
    sys.path.insert(0, str(local_site_packages))

from dotenv import load_dotenv
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SECTION_DIVIDER = "━━━━━━━━━━━━━━"
CHOICE_DIVIDER = "──────────────"


MENUS = [
    {"name": "김치찌개", "taste": "spicy", "weight": "hearty", "methods": {"delivery", "out"}},
    {"name": "제육볶음", "taste": "spicy", "weight": "hearty", "methods": {"delivery", "out", "cook"}},
    {"name": "마라탕", "taste": "spicy", "weight": "hearty", "methods": {"delivery", "out"}},
    {"name": "떡볶이", "taste": "spicy", "weight": "light", "methods": {"delivery", "out", "cook"}},
    {"name": "순두부찌개", "taste": "spicy", "weight": "light", "methods": {"delivery", "out", "cook"}},
    {"name": "설렁탕", "taste": "mild", "weight": "hearty", "methods": {"delivery", "out"}},
    {"name": "샤브샤브", "taste": "mild", "weight": "hearty", "methods": {"out", "cook"}},
    {"name": "닭곰탕", "taste": "mild", "weight": "hearty", "methods": {"delivery", "out", "cook"}},
    {"name": "연어덮밥", "taste": "mild", "weight": "light", "methods": {"delivery", "out"}},
    {"name": "잔치국수", "taste": "mild", "weight": "light", "methods": {"delivery", "out", "cook"}},
    {"name": "비빔밥", "taste": "fresh", "weight": "hearty", "methods": {"delivery", "out", "cook"}},
    {"name": "포케", "taste": "fresh", "weight": "light", "methods": {"delivery", "out", "cook"}},
    {"name": "월남쌈", "taste": "fresh", "weight": "light", "methods": {"out", "cook"}},
    {"name": "메밀소바", "taste": "fresh", "weight": "light", "methods": {"delivery", "out", "cook"}},
    {"name": "닭가슴살 샐러드", "taste": "fresh", "weight": "light", "methods": {"delivery", "cook"}},
]

MOOD_LABELS = {
    "tired": "조금 지침",
    "normal": "무난함",
    "happy": "기분 좋음",
    "exhausted": "완전히 방전됨",
}
HUNGER_LABELS = {"light": "가볍게", "hearty": "든든하게"}
TASTE_LABELS = {"spicy": "매콤하게", "mild": "담백하게", "fresh": "산뜻하게", "any": "상관없음"}
METHOD_LABELS = {"delivery": "배달", "out": "외식", "cook": "직접 요리"}

MOOD_CHOICES = {
    "😮‍💨 조금 지쳤어": "tired",
    "🙂 무난했어": "normal",
    "😄 기분 좋은 날": "happy",
    "🫠 완전히 방전": "exhausted",
}
HUNGER_CHOICES = {
    "🥗 가볍게 먹고 싶어": "light",
    "🍚 든든하게 먹고 싶어": "hearty",
}
TASTE_CHOICES = {
    "🌶️ 매콤하게": "spicy",
    "🍲 담백하게": "mild",
    "🥬 산뜻하게": "fresh",
    "🤷 상관없어": "any",
}
METHOD_CHOICES = {
    "🛵 배달": "delivery",
    "🚶 외식": "out",
    "👩‍🍳 직접 요리": "cook",
}

MENU_REASONS = {
    "김치찌개": "칼칼하고 익숙한 국물이 지친 하루를 편안하게 풀어줄 것 같아",
    "제육볶음": "매콤달콤한 양념과 따뜻한 밥 한 숟갈이면 확실한 만족감이 들 거야",
    "마라탕": "좋아하는 재료를 골라 먹는 재미까지 있어서 기분 전환하기 좋아",
    "떡볶이": "쫄깃한 식감과 매콤달콤한 맛이 답답했던 기분을 가볍게 바꿔줄 거야",
    "순두부찌개": "부드러운 순두부와 따뜻한 국물이 속을 포근하게 달래줘",
    "설렁탕": "자극적이지 않은 깊은 국물이라 천천히 몸을 쉬게 해주기 좋아",
    "샤브샤브": "따뜻한 국물에 채소와 고기를 하나씩 익혀 먹는 시간이 여유를 줄 거야",
    "닭곰탕": "담백한 닭고기와 뜨끈한 국물이 기운을 차분히 채워줄 것 같아",
    "연어덮밥": "부드러운 연어와 밥의 조합이 깔끔하면서도 은근히 만족스러워",
    "잔치국수": "따뜻한 육수와 부드러운 면이라 힘들이지 않고 편하게 먹을 수 있어",
    "비빔밥": "여러 나물과 고추장을 한입에 섞어 먹으면 맛도 영양도 균형 있게 챙길 수 있어",
    "포케": "신선한 재료와 다양한 식감 덕분에 가볍게 먹어도 심심하지 않을 거야",
    "월남쌈": "아삭한 채소를 직접 싸 먹는 재미가 있어서 저녁 시간이 산뜻해질 거야",
    "메밀소바": "시원한 육수와 담백한 면이 입맛을 깔끔하게 정리해줘",
    "닭가슴살 샐러드": "속은 가볍게 두면서 단백질은 든든히 챙길 수 있어",
}

RECIPES = {
    "김치찌개": {
        "ingredients": "신김치 1컵, 돼지고기 150g, 두부 1/2모, 대파, 고춧가루 1큰술, 국간장 1큰술",
        "steps": [
            "냄비에 돼지고기와 김치를 3분 정도 볶아줘.",
            "물 500ml와 고춧가루, 국간장을 넣고 15분 끓여줘.",
            "두부와 대파를 넣고 5분 더 끓이면 완성이야.",
        ],
        "tip": "김치 국물을 두세 숟갈 넣으면 국물 맛이 더 깊어져.",
    },
    "제육볶음": {
        "ingredients": "돼지고기 300g, 양파 1/2개, 대파, 고추장 2큰술, 고춧가루·간장·설탕 각 1큰술",
        "steps": [
            "고기에 양념을 넣고 10분 정도 재워줘.",
            "센 불에 고기를 볶다가 양파와 대파를 넣어줘.",
            "고기가 익고 양념이 잘 배면 불을 꺼줘.",
        ],
        "tip": "마지막에 참기름을 조금 두르면 향이 훨씬 좋아져.",
    },
    "마라탕": {
        "ingredients": "마라탕 소스, 사골육수 500ml, 청경채, 배추, 버섯, 두부, 당면, 원하는 고기",
        "steps": [
            "당면은 미리 불리고 채소와 고기를 먹기 좋게 손질해줘.",
            "육수에 마라탕 소스를 풀고 단단한 재료부터 넣어 끓여줘.",
            "채소와 당면을 넣고 5분 정도 더 끓여줘.",
        ],
        "tip": "소스는 처음부터 많이 넣지 말고 간을 보면서 추가해줘.",
    },
    "떡볶이": {
        "ingredients": "떡 300g, 어묵 2장, 대파, 고추장 2큰술, 고춧가루·설탕 각 1큰술, 간장 1/2큰술",
        "steps": [
            "물 500ml에 양념을 모두 풀어 끓여줘.",
            "떡과 어묵을 넣고 중불에서 10분 정도 졸여줘.",
            "대파를 넣고 소스가 걸쭉해질 때까지 조금 더 끓여줘.",
        ],
        "tip": "삶은 달걀이나 라면사리를 곁들이면 더 든든해.",
    },
    "순두부찌개": {
        "ingredients": "순두부 1봉, 달걀 1개, 애호박, 양파, 대파, 고춧가루 1큰술, 국간장 1큰술",
        "steps": [
            "냄비에 기름과 고춧가루, 대파를 넣고 약불에서 볶아줘.",
            "물 400ml와 채소를 넣고 5분 끓여줘.",
            "순두부를 넣고 끓인 뒤 달걀을 올려 마무리해줘.",
        ],
        "tip": "참치액이나 새우젓을 조금 넣으면 감칠맛이 살아나.",
    },
    "설렁탕": {
        "ingredients": "시판 사골육수 500ml, 삶은 소고기 100g, 소면, 대파, 소금, 후추",
        "steps": [
            "사골육수를 냄비에 넣고 충분히 끓여줘.",
            "삶은 소고기와 따로 삶은 소면을 그릇에 담아줘.",
            "뜨거운 육수를 붓고 대파, 소금, 후추를 곁들여줘.",
        ],
        "tip": "소면은 찬물에 헹궈 전분기를 빼야 국물이 깔끔해.",
    },
    "샤브샤브": {
        "ingredients": "샤브용 소고기 300g, 알배추, 청경채, 버섯, 숙주, 칼국수, 멸치육수 1L",
        "steps": [
            "육수를 끓이고 배추와 버섯처럼 단단한 채소를 먼저 넣어줘.",
            "고기는 먹을 만큼씩 살짝 익혀 채소와 함께 먹어줘.",
            "남은 육수에 칼국수를 넣어 마무리해줘.",
        ],
        "tip": "간장 2, 식초 1, 설탕 1 비율로 섞으면 간단한 찍어 먹는 소스가 돼.",
    },
    "닭곰탕": {
        "ingredients": "닭가슴살 또는 닭다리살 300g, 대파, 마늘 5알, 물 1L, 소금, 후추",
        "steps": [
            "물에 닭고기와 마늘을 넣고 25분 정도 끓여줘.",
            "익은 닭고기를 꺼내 먹기 좋게 찢어줘.",
            "닭고기를 국물에 다시 넣고 대파, 소금, 후추로 간해줘.",
        ],
        "tip": "밥을 말고 후추를 넉넉히 뿌리면 간단하고 든든해.",
    },
    "연어덮밥": {
        "ingredients": "생연어 150g, 밥 1공기, 양파 1/4개, 간장 2큰술, 식초·올리고당 각 1큰술, 와사비",
        "steps": [
            "간장과 식초, 올리고당을 섞어 소스를 만들어줘.",
            "밥 위에 얇게 썬 양파와 연어를 올려줘.",
            "소스와 와사비를 취향껏 곁들여줘.",
        ],
        "tip": "양파는 찬물에 5분 담가두면 매운맛이 부드러워져.",
    },
    "잔치국수": {
        "ingredients": "소면 1인분, 멸치육수 500ml, 애호박, 당근, 달걀, 국간장 1큰술",
        "steps": [
            "멸치육수에 채 썬 채소를 넣고 익혀줘.",
            "소면을 삶아 찬물에 충분히 헹궈 그릇에 담아줘.",
            "국간장으로 간한 뜨거운 육수를 붓고 달걀지단을 올려줘.",
        ],
        "tip": "김가루와 양념장을 조금 올리면 풍미가 더 좋아져.",
    },
    "비빔밥": {
        "ingredients": "밥 1공기, 시금치, 당근, 애호박, 버섯, 달걀 1개, 고추장, 참기름",
        "steps": [
            "채소를 채 썰어 각각 소금 간을 살짝 하며 볶아줘.",
            "밥 위에 준비한 채소와 달걀프라이를 보기 좋게 올려줘.",
            "고추장과 참기름을 넣고 골고루 비벼줘.",
        ],
        "tip": "남은 반찬이나 나물을 활용하면 더 빠르게 만들 수 있어.",
    },
    "포케": {
        "ingredients": "현미밥 1공기, 연어 또는 닭가슴살 150g, 오이, 아보카도, 옥수수, 간장 2큰술, 식초 1큰술",
        "steps": [
            "단백질과 채소를 한입 크기로 썰어줘.",
            "그릇에 밥을 담고 준비한 재료를 나란히 올려줘.",
            "간장과 식초를 섞은 소스를 뿌려줘.",
        ],
        "tip": "김가루나 날치알을 올리면 식감과 감칠맛이 좋아져.",
    },
    "월남쌈": {
        "ingredients": "라이스페이퍼, 새우 또는 소고기 200g, 파프리카, 오이, 당근, 깻잎, 스위트칠리소스",
        "steps": [
            "고기는 익히고 채소는 가늘게 채 썰어줘.",
            "라이스페이퍼를 미지근한 물에 짧게 적셔줘.",
            "재료를 올려 단단하게 말고 소스에 찍어 먹어줘.",
        ],
        "tip": "라이스페이퍼는 오래 담그면 찢어지니 한 번만 빠르게 적셔줘.",
    },
    "메밀소바": {
        "ingredients": "메밀면 1인분, 쯔유 80ml, 찬물 160ml, 무, 대파, 김가루, 와사비",
        "steps": [
            "메밀면을 표시 시간에 맞춰 삶아줘.",
            "찬물에 여러 번 헹군 뒤 얼음물에 잠깐 담가줘.",
            "쯔유와 찬물을 섞고 무, 대파, 김가루를 곁들여줘.",
        ],
        "tip": "면의 물기를 확실히 빼야 장국 맛이 싱거워지지 않아.",
    },
    "닭가슴살 샐러드": {
        "ingredients": "닭가슴살 150g, 샐러드 채소, 방울토마토, 달걀 1개, 올리브유 1큰술, 식초 1큰술",
        "steps": [
            "닭가슴살에 소금과 후추를 뿌려 노릇하게 구워줘.",
            "씻은 채소와 토마토, 삶은 달걀을 그릇에 담아줘.",
            "썬 닭가슴살을 올리고 올리브유와 식초를 뿌려줘.",
        ],
        "tip": "견과류나 치즈를 조금 더하면 포만감과 식감이 좋아져.",
    },
}

from extra_menus import EXTRA_MENUS, EXTRA_REASONS, EXTRA_RECIPES

MENUS.extend(EXTRA_MENUS)
MENU_REASONS.update(EXTRA_REASONS)
RECIPES.update(EXTRA_RECIPES)


def keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=data) for label, data in row] for row in rows]
    )


def reply_keyboard(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="버튼을 눌러서 알려줘",
    )


async def send_next(query, text: str, reply_markup=None) -> None:
    """Keep the previous question and record the button the user selected."""
    selected_label = None
    if query.message.reply_markup:
        for row in query.message.reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == query.data:
                    selected_label = button.text
                    break
            if selected_label:
                break

    if selected_label and query.message.text:
        await query.edit_message_text(
            f"{query.message.text}\n\n{CHOICE_DIVIDER}\n✓ 내가 고른 답\n{selected_label}"
        )
    else:
        await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        f"{SECTION_DIVIDER}\n{text}",
        reply_markup=reply_markup,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    context.user_data["stage"] = "mood"
    buttons = reply_keyboard(
        [
            ["😮‍💨 조금 지쳤어", "🙂 무난했어"],
            ["😄 기분 좋은 날", "🫠 완전히 방전"],
        ]
    )
    await update.message.reply_text(
        f"🌙 MOMUK · 오늘의 저녁\n{SECTION_DIVIDER}\n\n"
        "왔어? 오늘도 정말 수고 많았어.\n"
        "저녁만큼은 고민하지 않게 내가 같이 골라줄게 🍽️\n\n"
        "💬 오늘 하루는 어땠어?",
        reply_markup=buttons,
    )


async def select_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    mood = query.data.split(":", 1)[1]
    context.user_data["mood"] = mood

    reactions = {
        "tired": "조금 지쳤구나. 오늘 하루 잘 버텨줘서 고마워.",
        "normal": "별일 없이 지나온 하루였구나. 그래도 오늘 하루 수고했어.",
        "happy": "기분 좋은 하루였다니 나도 좋네. 저녁까지 기분 좋게 이어가 보자.",
        "exhausted": "많이 힘들었겠다. 지금은 아무 생각 말고 잠깐 기대도 돼. 메뉴는 내가 골라줄게.",
    }
    await send_next(
        query,
        f"{reactions[mood]}\n\n지금 배는 어느 정도 고파? 네 속에 맞춰서 골라주고 싶어.",
        reply_markup=keyboard(
            [[("🥗 가볍게 먹고 싶어", "hunger:light"), ("🍚 든든하게 먹고 싶어", "hunger:hearty")]]
        ),
    )


async def select_hunger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["hunger"] = query.data.split(":", 1)[1]
    await send_next(
        query,
        "응, 알겠어. 그럼 지금 제일 당기는 맛은 어떤 쪽이야? 천천히 골라도 돼.",
        reply_markup=keyboard(
            [
                [("🌶️ 매콤하게", "taste:spicy"), ("🍲 담백하게", "taste:mild")],
                [("🥬 산뜻하게", "taste:fresh"), ("🤷 상관없어", "taste:any")],
            ]
        ),
    )


async def select_taste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["taste"] = query.data.split(":", 1)[1]
    await send_next(
        query,
        "좋아, 거의 다 골랐어. 마지막으로 오늘은 어떻게 먹고 싶어? 편한 쪽으로 말해줘.",
        reply_markup=keyboard(
            [
                [("🛵 배달", "method:delivery"), ("🚶 외식", "method:out")],
                [("👩‍🍳 직접 요리", "method:cook")],
            ]
        ),
    )


def recommend(profile: dict, excluded: set[str] | None = None) -> list[dict]:
    excluded = excluded or set()
    scored = []
    for menu in MENUS:
        if menu["name"] in excluded or profile["method"] not in menu["methods"]:
            continue
        score = 0
        if profile["taste"] == "any" or menu["taste"] == profile["taste"]:
            score += 3
        if menu["weight"] == profile["hunger"]:
            score += 3
        if profile["mood"] in {"tired", "exhausted"} and profile["method"] == "delivery":
            score += 1
        scored.append((score + random.random(), menu))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [menu for _, menu in scored[:3]]


def reason_for(menu: dict, profile: dict) -> str:
    return MENU_REASONS[menu["name"]]


def format_recipe(menu_name: str) -> str:
    recipe = RECIPES[menu_name]
    steps = "\n".join(
        f"{index}. {step}" for index, step in enumerate(recipe["steps"], 1)
    )
    return (
        f"🧺 준비 재료\n{CHOICE_DIVIDER}\n{recipe['ingredients']}\n\n"
        f"🍳 만드는 순서\n{CHOICE_DIVIDER}\n{steps}\n\n"
        f"💡 작은 팁\n{CHOICE_DIVIDER}\n{recipe['tip']}"
    )


async def show_recommendations(query, context: ContextTypes.DEFAULT_TYPE, retry: bool = False) -> None:
    profile = context.user_data
    required = {"mood", "hunger", "taste", "method"}
    if not required.issubset(profile):
        await send_next(
            query,
            "이전 대화가 조금 오래돼서 내용을 다시 확인해야 할 것 같아. "
            "아래 버튼을 누르면 내가 처음부터 차근차근 물어볼게.",
            reply_markup=keyboard([[("💛 다시 시작하기", "action:restart")]]),
        )
        return
    previous = set(profile.get("last_recommendations", [])) if retry else set()
    menus = recommend(profile, previous)
    if len(menus) < 3:
        menus = recommend(profile)
    profile["last_recommendations"] = [menu["name"] for menu in menus]

    summary = (
        "📌 오늘의 취향\n"
        f"• 컨디션: {MOOD_LABELS[profile['mood']]}\n"
        f"• 식사량: {HUNGER_LABELS[profile['hunger']]}\n"
        f"• 입맛: {TASTE_LABELS[profile['taste']]}\n"
        f"• 식사 방법: {METHOD_LABELS[profile['method']]}"
    )
    number_icons = ["1️⃣", "2️⃣", "3️⃣"]
    lines = [
        f"{number_icons[index]} {menu['name']}\n└ {reason_for(menu, profile)}"
        for index, menu in enumerate(menus)
    ]
    intro = (
        "아까보다 더 마음에 들 수 있게 다시 골라봤어."
        if retry
        else "네가 말해준 걸 하나씩 생각하면서 골라봤어."
    )
    await send_next(
        query,
        f"✨ 오늘의 추천\n\n{intro}\n\n{summary}\n\n{CHOICE_DIVIDER}\n\n"
        + "\n\n".join(lines)
        + "\n\n부담 갖지 말고, 지금 마음이 조금이라도 가는 걸 골라봐.",
        reply_markup=keyboard(
            [
                [(f"✅ {menu['name']}", f"pick:{index}") for index, menu in enumerate(menus)],
                [("🔄 다른 메뉴 추천", "action:retry"), ("처음부터", "action:restart")],
            ]
        ),
    )


async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["method"] = query.data.split(":", 1)[1]
    await show_recommendations(query, context)


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    if action == "retry":
        await show_recommendations(query, context, retry=True)
        return

    context.user_data.clear()
    await send_next(
        query,
        "괜찮아, 우리 천천히 다시 골라보자. 오늘 하루는 어땠어?",
        reply_markup=keyboard(
            [
                [("😮‍💨 조금 지쳤어", "mood:tired"), ("🙂 무난했어", "mood:normal")],
                [("😄 기분 좋은 날", "mood:happy"), ("🫠 완전히 방전", "mood:exhausted")],
            ]
        ),
    )


async def select_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":", 1)[1])
    choices = context.user_data.get("last_recommendations", [])
    if index >= len(choices):
        await send_next(
            query,
            "추천 정보가 조금 오래됐네. 괜찮아, 다시 같이 골라보자.",
            reply_markup=keyboard([[("💛 다시 시작하기", "action:restart")]]),
        )
        return
    selected = choices[index]
    await send_next(
        query,
        f"그럼 오늘 저녁은 {selected} 어때? 잘 골랐어 😊\n\n"
        f"집에서 만들어 먹고 싶을 때 볼 수 있게 간단한 레시피도 챙겨왔어.\n\n"
        f"{format_recipe(selected)}\n\n"
        "맛있게 천천히 먹고, 오늘은 푹 쉬자. "
        "다음에 또 고민되면 아래 버튼을 눌러줘. 내가 같이 골라줄게.",
        reply_markup=keyboard([[("🍽️ 다시 골라보기", "action:restart")]]),
    )


async def send_text_recommendations(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    retry: bool = False,
) -> None:
    profile = context.user_data
    previous = set(profile.get("last_recommendations", [])) if retry else set()
    menus = recommend(profile, previous)
    if len(menus) < 3:
        menus = recommend(profile)

    names = [menu["name"] for menu in menus]
    profile["last_recommendations"] = names
    profile["stage"] = "menu"

    summary = (
        "📌 오늘의 취향\n"
        f"• 컨디션: {MOOD_LABELS[profile['mood']]}\n"
        f"• 식사량: {HUNGER_LABELS[profile['hunger']]}\n"
        f"• 입맛: {TASTE_LABELS[profile['taste']]}\n"
        f"• 식사 방법: {METHOD_LABELS[profile['method']]}"
    )
    number_icons = ["1️⃣", "2️⃣", "3️⃣"]
    menu_lines = [
        f"{number_icons[index]} {menu['name']}\n└ {reason_for(menu, profile)}"
        for index, menu in enumerate(menus)
    ]
    intro = (
        "아까보다 더 마음에 들 수 있게 다시 골라봤어."
        if retry
        else "네가 말해준 걸 하나씩 생각하면서 골라봤어."
    )
    await message.reply_text(
        f"{SECTION_DIVIDER}\n✨ 오늘의 추천\n\n{intro}\n\n"
        f"{summary}\n\n{CHOICE_DIVIDER}\n\n"
        + "\n\n".join(menu_lines)
        + "\n\n부담 갖지 말고, 지금 마음이 조금이라도 가는 걸 골라봐.",
        reply_markup=reply_keyboard(
            [[names[0], names[1]], [names[2]], ["🔄 다른 메뉴 추천", "💛 처음부터"]]
        ),
    )


async def handle_text_choice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.message
    text = message.text
    stage = context.user_data.get("stage")

    if text in {"💛 처음부터", "🍽️ 다시 골라보기", "💛 다시 시작하기"}:
        await start(update, context)
        return

    if stage == "mood" and text in MOOD_CHOICES:
        mood = MOOD_CHOICES[text]
        context.user_data["mood"] = mood
        context.user_data["stage"] = "hunger"
        reactions = {
            "tired": "조금 지쳤구나. 오늘 하루 잘 버텨줘서 고마워.",
            "normal": "별일 없이 지나온 하루였구나. 그래도 오늘 하루 수고했어.",
            "happy": "기분 좋은 하루였다니 나도 좋네. 저녁까지 기분 좋게 이어가 보자.",
            "exhausted": "많이 힘들었겠다. 지금은 아무 생각 말고 잠깐 기대도 돼. 메뉴는 내가 골라줄게.",
        }
        await message.reply_text(
            f"{SECTION_DIVIDER}\n{reactions[mood]}\n\n"
            "🍚 지금 배는 어느 정도 고파? 네 속에 맞춰서 골라주고 싶어.",
            reply_markup=reply_keyboard(
                [["🥗 가볍게 먹고 싶어", "🍚 든든하게 먹고 싶어"]]
            ),
        )
        return

    if stage == "hunger" and text in HUNGER_CHOICES:
        context.user_data["hunger"] = HUNGER_CHOICES[text]
        context.user_data["stage"] = "taste"
        await message.reply_text(
            f"{SECTION_DIVIDER}\n응, 알겠어. 그럼 지금 제일 당기는 맛은 어떤 쪽이야?\n"
            "천천히 골라도 돼.",
            reply_markup=reply_keyboard(
                [
                    ["🌶️ 매콤하게", "🍲 담백하게"],
                    ["🥬 산뜻하게", "🤷 상관없어"],
                ]
            ),
        )
        return

    if stage == "taste" and text in TASTE_CHOICES:
        context.user_data["taste"] = TASTE_CHOICES[text]
        context.user_data["stage"] = "method"
        await message.reply_text(
            f"{SECTION_DIVIDER}\n좋아, 거의 다 골랐어.\n"
            "마지막으로 오늘은 어떻게 먹고 싶어? 편한 쪽으로 말해줘.",
            reply_markup=reply_keyboard(
                [["🛵 배달", "🚶 외식"], ["👩‍🍳 직접 요리"]]
            ),
        )
        return

    if stage == "method" and text in METHOD_CHOICES:
        context.user_data["method"] = METHOD_CHOICES[text]
        await send_text_recommendations(message, context)
        return

    if stage == "menu":
        if text == "🔄 다른 메뉴 추천":
            await send_text_recommendations(message, context, retry=True)
            return
        if text in context.user_data.get("last_recommendations", []):
            context.user_data["stage"] = "done"
            await message.reply_text(
                f"{SECTION_DIVIDER}\n🍽️ 오늘의 선택 · {text}\n\n"
                "잘 골랐어 😊 집에서 만들어 먹고 싶을 때 볼 수 있게 "
                "간단한 레시피도 챙겨왔어.\n\n"
                f"{format_recipe(text)}\n\n"
                "맛있게 천천히 먹고, 오늘은 푹 쉬자.",
                reply_markup=reply_keyboard([["🍽️ 다시 골라보기"]]),
            )
            return

    await message.reply_text(
        "지금 화면에 보이는 선택지 중에서 골라주면 내가 이어서 도와줄게 😊"
    )


async def setup_bot(application: Application) -> None:
    await application.bot.set_my_commands(
        [BotCommand("start", "momuk 시작하기")]
    )
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


def main() -> None:
    if not TOKEN:
        raise RuntimeError(".env 파일에 TELEGRAM_BOT_TOKEN을 설정해 주세요.")

    app = Application.builder().token(TOKEN).post_init(setup_bot).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_mood, pattern=r"^mood:"))
    app.add_handler(CallbackQueryHandler(select_hunger, pattern=r"^hunger:"))
    app.add_handler(CallbackQueryHandler(select_taste, pattern=r"^taste:"))
    app.add_handler(CallbackQueryHandler(select_method, pattern=r"^method:"))
    app.add_handler(CallbackQueryHandler(handle_action, pattern=r"^action:"))
    app.add_handler(CallbackQueryHandler(select_menu, pattern=r"^pick:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_choice))

    print("momuk이 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.")
    app.run_polling()


if __name__ == "__main__":
    main()
