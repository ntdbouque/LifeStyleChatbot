from typing import List, Optional
from typing_extensions import TypedDict, Literal


# =========================
# 1. PROFILE
# =========================

class UserProfileMemory(TypedDict, total=False):
    """Thông tin cơ bản của user (không chứa bệnh/thuốc)."""
    name: str
    year_of_birth: int
    gender: Literal["male", "female", "other"]
    height_cm: float
    weight_kg: float
    bmi: float
    smoking_status: Literal["never", "former", "current"]
    alcohol_use: Literal["none", "occasional", "regular"]
    preferred_language: Literal["vi", "en"]
    explain_style: Literal["short", "detailed"]


# =========================
# 2. LIFESTYLE
# =========================

class DietInfo(TypedDict, total=False):
    salt_intake: Literal["low", "medium", "high"]
    sugar_intake: Literal["low", "medium", "high"]
    processed_food: Literal["rare", "sometimes", "frequent"]
    vegetable_fruit: Literal["low", "medium", "high"]
    meal_pattern: Literal["regular", "irregular", "skips_meals"]
    special_diet: Optional[
        Literal["dash", "mediterranean", "low_carb", "low_fat", "other"]
    ]


class PhysicalActivityInfo(TypedDict, total=False):
    activity_level: Literal["low", "moderate", "high"]
    exercise_days_per_week: int
    exercise_minutes_per_session: int
    preferred_exercises: List[str]
    limitations: List[str]  # vd: ["knee_pain", "back_pain", "heart_disease"]


class SleepInfo(TypedDict, total=False):
    average_sleep_hours: float
    sleep_quality: Literal["poor", "fair", "good"]
    sleep_issues: List[str]  # vd: ["difficulty_falling_asleep", "waking_up_early"]


class StressInfo(TypedDict, total=False):
    stress_level: Literal["low", "moderate", "high"]
    main_stressors: List[str]     # vd: ["work", "family", "financial"]
    coping_methods: List[str]     # vd: ["exercise", "meditation", "none"]


class HabitsInfo(TypedDict, total=False):
    smoking_status: Literal["never", "former", "current"]
    alcohol_use: Literal["none", "occasional", "regular"]


class LifestyleMemory(TypedDict, total=False):
    """Thói quen sống phục vụ tư vấn lối sống cho THA & ĐTĐ."""
    diet: DietInfo
    physical_activity: PhysicalActivityInfo
    sleep: SleepInfo
    stress: StressInfo
    habits: HabitsInfo


# =========================
# 3. MEASUREMENT SUMMARY
# =========================

class BloodPressureValue(TypedDict, total=False):
    sys: int
    dia: int
    time: str  # ISO 8601, vd: "2025-12-06T08:30:00+07:00"


class GlucoseValue(TypedDict, total=False):
    value: float
    unit: Literal["mmol/L", "mg/dL"]
    context: Literal["fasting", "postprandial", "random"]
    time: str  # ISO 8601


class MeasurementHabits(TypedDict, total=False):
    bp_per_day: int
    glucose_per_day: int
    adherence: Literal["regular", "irregular"]


class MeasurementSummaryMemory(TypedDict, total=False):
    """Tóm tắt chỉ số gần đây, không phải toàn bộ time-series."""
    last_bp: Optional[BloodPressureValue]
    last_glucose: Optional[GlucoseValue]
    bp_pattern_note: Optional[str]
    glucose_pattern_note: Optional[str]
    measurement_habits: MeasurementHabits


# =========================
# 4. PREFERENCES (cách bot nên tư vấn)
# =========================

class CommunicationPreferences(TypedDict, total=False):
    explain_style: Literal["short", "detailed"]
    tone: Literal["friendly", "formal", "neutral"]
    use_analogies: bool
    language: Literal["vi", "en"]


class ReminderPreferences(TypedDict, total=False):
    allow_medication_reminders: bool
    allow_measurement_reminders: bool
    preferred_times: List[str]  # ["07:00", "20:00"]


class PreferencesMemory(TypedDict, total=False):
    communication: CommunicationPreferences
    reminders: ReminderPreferences

### TỔNG HỢP (TẠM)

class UserInfo(TypedDict, total=False):
    """
    Long-term memory tổng hợp cho 1 user trong ứng dụng y tế.
    Có thể chứa profile, lifestyle, measurement_summary, preferences.
    Các field đều optional để có thể update từng phần.
    """
    profile: UserProfileMemory
    lifestyle: LifestyleMemory
    measurement_summary: MeasurementSummaryMemory
    preferences: PreferencesMemory
