import json
import random
from pathlib import Path
from typing import Literal, Optional
from app.core.config import PROJECT_ROOT, BACKEND_DIR
from app.schemas.passenger import (
    PassengerProfile,
    SeatInfo,
    CabinManifestResponse,
    ArchetypeId,
    TicketStatus,
    PassengerTrait,
)

PASSENGERS_FILE = PROJECT_ROOT / "backend" / "data" / "passengers.json"
if not PASSENGERS_FILE.exists():
    PASSENGERS_FILE = BACKEND_DIR / "data" / "passengers.json"

with open(PASSENGERS_FILE, "r", encoding="utf-8") as f:
    names_data = json.load(f)

MALE_FIRST_NAMES = names_data["male_first_names"]
MALE_PATRONYMICS = names_data["male_patronymics"]
FEMALE_YOUNG_FIRST_NAMES = names_data["female_young_first_names"]
FEMALE_ELDERLY_FIRST_NAMES = names_data["female_elderly_first_names"]
FEMALE_PATRONYMICS = names_data["female_patronymics"]
BASE_LAST_NAMES = names_data["base_last_names"]

PASSPORT_REGIONS = [45, 46, 40, 78, 28, 50, 60, 33, 76, 52, 69]

# Места, которые остаются пустыми по умолчанию (10 мест из 48 при загрузке 80%)
DEFAULT_EMPTY_SEATS = {"1D", "4A", "5D", "7B", "8C", "10B", "11C", "12A", "12B", "12D"}


def make_female_last_name(base: str) -> str:
    """Формирует корректное женское окончание русской фамилии."""
    if base.endswith("ов") or base.endswith("ев") or base.endswith("ёв") or base.endswith("ин"):
        return base + "а"
    if base.endswith("ский"):
        return base[:-2] + "ая"
    if base.endswith("ый") or base.endswith("ий"):
        return base[:-2] + "ая"
    return base + "а"


def generate_passport(age: int) -> str:
    """Генерирует реалистичные паспортные данные РФ: серия (4 цифры) и номер (6 цифр)."""
    region = random.choice(PASSPORT_REGIONS)
    # Год выдачи паспорта: не раньше 14 лет и не позднее 2025 года
    min_issue_year = max(14, (2026 - age + 14) % 100)
    max_issue_year = 25
    if min_issue_year > max_issue_year:
        issue_year = random.randint(14, 25)
    else:
        issue_year = random.randint(min_issue_year, max_issue_year)

    number = random.randint(100000, 999999)
    return f"{region:02d} {issue_year:02d} {number:06d}"


def generate_birth_date(age: int) -> str:
    """Вычисляет дату рождения для симуляционного 2026 года."""
    year = 2026 - age
    month = random.randint(1, 12)
    # Используем до 28 дней, чтобы избежать проблем с февралем
    day = random.randint(1, 28)
    return f"{day:02d}.{month:02d}.{year}"


def get_observation_text(archetype: ArchetypeId, state: str) -> str:
    """Формирует живое диегетическое описание того, что видит проводник при осмотре."""
    if state == "gadget":
        return "Пассажир в беспроводных наушниках, увлеченно смотрит в экран смартфона."
    if state == "reading":
        return "Пассажирка в аккуратных очках сосредоточенно читает книгу в мягком переплете."
    if state == "sleeping":
        if archetype == "male_young":
            return "Молодой человек спит, надвинув капюшон и откинувшись на подголовник кресла."
        elif archetype == "female_elderly":
            return "Пожилая пассажирка тихо дремлет, укутавшись в теплый дорожный шарф."
        else:
            return "Девушка спокойно спит, повернувшись к окну с дорожной подушкой."
    if state == "annoyed":
        return "Пассажир хмурится, недовольно посматривает по сторонам и теребит дефлектор вентиляции."
    if state == "drunk_scattered":
        return "Пассажир с рассеянным взглядом, слегка покачивается в кресле, на столике банка напитка."
    if state == "drunk_angry":
        return "Пассажир с покрасневшим лицом, эмоционально спорит и привлекает внимание соседей."
    if state == "happy":
        return "Пассажир в приподнятом настроении, с легкой улыбкой наблюдает за пролетающим за окном пейзажем."
    # neutral
    return "Пассажир спокойно отдыхает в кресле, наслаждаясь плавной и тихой поездкой."


def generate_passenger(
    archetype: Optional[ArchetypeId] = None,
    destination: Optional[str] = None,
    ticket_status: Optional[TicketStatus] = None,
    is_boarding: bool = True,
) -> PassengerProfile:
    """Генерирует случайного пассажира под заданный или случайный архетип."""
    if archetype is None:
        # 45% male_young, 35% female_young, 20% female_elderly
        archetype = random.choices(
            ["male_young", "female_young", "female_elderly"],
            weights=[45, 35, 20],
            k=1,
        )[0]

    if archetype == "male_young":
        gender = "m"
        age = random.randint(18, 27)
        first_name = random.choice(MALE_FIRST_NAMES)
        patronymic = random.choice(MALE_PATRONYMICS)
        last_name = random.choice(BASE_LAST_NAMES)
        # Если только сел - не спит!
        states = ["neutral", "gadget", "happy"] if is_boarding else ["neutral", "gadget", "sleeping", "happy"]
        weights = [40, 40, 20] if is_boarding else [35, 30, 25, 10]
        state = random.choices(states, weights=weights, k=1)[0]
        trait: PassengerTrait = random.choices(["polite", "anxious", "demanding"], weights=[40, 10, 50], k=1)[0]
    elif archetype == "female_young":
        gender = "f"
        age = random.randint(18, 30)
        first_name = random.choice(FEMALE_YOUNG_FIRST_NAMES)
        patronymic = random.choice(FEMALE_PATRONYMICS)
        last_name = make_female_last_name(random.choice(BASE_LAST_NAMES))
        states = ["neutral", "happy", "gadget"] if is_boarding else ["neutral", "happy", "sleeping", "gadget"]
        weights = [50, 30, 20] if is_boarding else [40, 25, 20, 15]
        state = random.choices(states, weights=weights, k=1)[0]
        trait: PassengerTrait = random.choices(["polite", "anxious", "demanding"], weights=[50, 30, 20], k=1)[0]
    else:  # female_elderly
        gender = "f"
        age = random.randint(60, 75)
        first_name = random.choice(FEMALE_ELDERLY_FIRST_NAMES)
        patronymic = random.choice(FEMALE_PATRONYMICS)
        last_name = make_female_last_name(random.choice(BASE_LAST_NAMES))
        states = ["reading", "neutral"] if is_boarding else ["reading", "neutral", "sleeping"]
        weights = [60, 40] if is_boarding else [40, 30, 30]
        state = random.choices(states, weights=weights, k=1)[0]
        trait: PassengerTrait = random.choices(["polite", "anxious", "demanding"], weights=[70, 20, 10], k=1)[0]

    full_name = f"{last_name} {first_name} {patronymic}"
    birth_date = generate_birth_date(age)
    passport_data = generate_passport(age)
    sprite_url = f"/assets/{archetype}/{state}.png"

    if destination is None:
        destination = "Санкт-Петербург (Главный)" if random.random() < 0.75 else "Новая Тверь"

    if ticket_status is None:
        ticket_status = "validated" if random.random() < 0.65 else "not_checked"

    observation = get_observation_text(archetype, state)

    return PassengerProfile(
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
        full_name=full_name,
        gender=gender,
        trait=trait,
        age=age,
        birth_date=birth_date,
        passport_data=passport_data,
        archetype_id=archetype,
        state=state,
        sprite_url=sprite_url,
        destination=destination,
        ticket_status=ticket_status,
        observation=observation,
    )


def generate_cabin_manifest(occupancy_rate: float = 0.8) -> CabinManifestResponse:
    """
    Генерирует манифест вагона № 03 класса «Комфорт» (12 рядов 2+2, 48 мест)
    с пассажирскими профилями, паспортами РФ и привязкой к спрайтам.
    """
    letters: list[Literal["A", "B", "C", "D"]] = ["A", "B", "C", "D"]
    total_seats = 48
    target_occupied = max(4, min(total_seats, round(total_seats * occupancy_rate)))

    all_seat_ids = [f"{r}{l}" for r in range(1, 13) for l in letters]
    random.shuffle(all_seat_ids)
    occupied_set = set(all_seat_ids[:target_occupied])

    seats: list[SeatInfo] = []
    validated_count = 0

    for row in range(1, 13):
        for letter in letters:
            seat_id = f"{row}{letter}"
            is_occupied = seat_id in occupied_set
            passenger: Optional[PassengerProfile] = None

            if is_occupied:
                passenger = generate_passenger(is_boarding=True)
                if passenger.ticket_status == "validated":
                    validated_count += 1

            seats.append(
                SeatInfo(
                    seat_id=seat_id,
                    row=row,
                    letter=letter,
                    is_occupied=is_occupied,
                    passenger=passenger,
                )
            )

    return CabinManifestResponse(
        train_number="754",
        wagon_number="03",
        wagon_class="Комфорт",
        total_seats=total_seats,
        occupied_count=len(occupied_set),
        validated_count=validated_count,
        seats=seats,
    )
