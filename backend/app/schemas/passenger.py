from typing import Literal, Optional, Dict, Any, Union
from pydantic import BaseModel

GenderType = Literal["m", "f"]
ArchetypeId = Literal["male_young", "female_young", "female_elderly"]
TicketStatus = Literal["validated", "not_checked"]
PassengerTrait = Literal["polite", "demanding", "anxious"]


class PassengerProfile(BaseModel):
    first_name: str
    last_name: str
    patronymic: str
    full_name: str
    gender: GenderType
    trait: PassengerTrait
    age: int
    birth_date: str  # "15.04.2001"
    passport_data: str  # "45 21 789123"
    archetype_id: ArchetypeId
    state: str  # "neutral", "sleeping", etc.
    sprite_url: str  # "/assets/passengers/male_young/neutral.png"
    destination: str
    ticket_status: TicketStatus
    observation: str  # Текстовое описание того, что видит проводник глазами


class ScenarioOptionSchema(BaseModel):
    id: str
    text: str
    action_type: Optional[str] = "click"
    hold_time_ms: Optional[int] = None
    next_step: Optional[str] = None
    why_correct: Optional[str] = None
    what_if_wrong: Optional[str] = None
    expected_rule: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ScenarioStepSchema(BaseModel):
    prompt: Union[str, Dict[str, str]]
    timer_seconds: int = 15
    phase: Optional[str] = "learning"
    action_type: Optional[str] = "choice"
    expected_rule: Optional[str] = None
    options: list[ScenarioOptionSchema] = []


class ActiveIncidentSchema(BaseModel):
    incident_id: str
    title: str
    phase: Optional[str] = "learning"
    start_step: str = "step_1"
    steps: Dict[str, ScenarioStepSchema]


class SeatInfo(BaseModel):
    seat_id: str  # "1A", "2B", etc.
    row: int  # 1..12
    letter: Literal["A", "B", "C", "D"]
    is_occupied: bool
    passenger: Optional[PassengerProfile] = None
    active_incident: Optional[ActiveIncidentSchema] = None


class CabinManifestResponse(BaseModel):
    train_number: str = "754"
    wagon_number: str = "03"
    wagon_class: str = "Комфорт"
    total_seats: int = 48
    occupied_count: int
    validated_count: int
    seats: list[SeatInfo]


class StationEventRequest(BaseModel):
    station_index: int


class StationEventResponse(BaseModel):
    station_index: int
    station_name: str
    is_technical: bool
    disembarked_count: int
    disembarked_passengers: list[str]
    boarded_count: int
    boarded_passengers: list[str]
    total_passengers: int
    manifest: CabinManifestResponse


class TripStatePayload(BaseModel):
    time_seconds: float
    speed: float
    shift_phase: str
