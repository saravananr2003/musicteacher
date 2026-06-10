"""OpenAI-backed analysis helpers for Carnatic vocal practice."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


FOCUS_AREA_DESCRIPTIONS = {
    "Varisai": "Swarasthana accuracy, ascending/descending pattern correctness, and phrase clarity.",
    "Shruthi": "Pitch center stability, alignment to tambura/drone, and drift across the recording.",
    "Thalam": "Rhythmic alignment, eduppu, akshara consistency, and tempo steadiness.",
    "Gamakam": "Ornamentation shape, smoothness, and whether gamakas fit the raga/practice level.",
    "Raga Lakshanam": "Characteristic phrases, avoid notes, phrase endings, and raga identity.",
    "Pronunciation": "Sahitya clarity, vowel shaping, consonant articulation, and breath placement.",
}


ANALYSIS_JSON_SCHEMA = {
    "name": "carnatic_music_feedback",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "overall_score": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
            },
            "what_went_well": {
                "type": "array",
                "items": {"type": "string"},
            },
            "needs_improvement": {
                "type": "array",
                "items": {"type": "string"},
            },
            "timeline": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "focus_area": {"type": "string"},
                        "observation": {"type": "string"},
                        "recommendation": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["good", "minor", "moderate", "major"],
                        },
                    },
                    "required": [
                        "start_time",
                        "end_time",
                        "focus_area",
                        "observation",
                        "recommendation",
                        "severity",
                    ],
                },
            },
            "practice_plan": {
                "type": "array",
                "items": {"type": "string"},
            },
            "disclaimer": {"type": "string"},
        },
        "required": [
            "summary",
            "overall_score",
            "what_went_well",
            "needs_improvement",
            "timeline",
            "practice_plan",
            "disclaimer",
        ],
    },
    "strict": True,
}


@dataclass(frozen=True)
class PracticeContext:
    """Context supplied by the learner to improve the quality of feedback."""

    focus_areas: list[str]
    raga: str = ""
    tala: str = ""
    shruthi: str = ""
    practice_item: str = ""
    learner_level: str = "Beginner"
    notes: str = ""


def transcribe_audio(
    client: OpenAI,
    audio_bytes: bytes,
    filename: str,
    model: str = "whisper-1",
) -> dict[str, Any]:
    """Transcribe uploaded audio and ask for segment timestamps when available."""

    from io import BytesIO

    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename

    transcription = client.audio.transcriptions.create(
        model=model,
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    if hasattr(transcription, "model_dump"):
        return transcription.model_dump()
    if isinstance(transcription, dict):
        return transcription
    return {"text": str(transcription), "segments": []}


def analyze_practice(
    client: OpenAI,
    transcription: dict[str, Any],
    context: PracticeContext,
    model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """Generate Carnatic music feedback from transcription and learner context."""

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a careful Carnatic vocal music teacher. "
                            "Evaluate a learner's uploaded practice recording using the available "
                            "transcription and segment timestamps. Focus on practical, kind, "
                            "actionable coaching. Do not invent exact pitch measurements that are "
                            "not present in the data. If audio-only details such as shruthi drift "
                            "cannot be confirmed from the transcript, say what should be checked "
                            "and provide a practice recommendation."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": _build_analysis_prompt(transcription, context),
                    }
                ],
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": ANALYSIS_JSON_SCHEMA["name"],
                "schema": ANALYSIS_JSON_SCHEMA["schema"],
                "strict": ANALYSIS_JSON_SCHEMA["strict"],
            }
        },
    )

    output_text = response.output_text
    try:
        return json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI returned feedback that was not valid JSON.") from exc


def _build_analysis_prompt(transcription: dict[str, Any], context: PracticeContext) -> str:
    focus_descriptions = [
        f"- {area}: {FOCUS_AREA_DESCRIPTIONS.get(area, 'General Carnatic music feedback.')}"
        for area in context.focus_areas
    ]
    segments = _format_segments(transcription.get("segments", []))
    transcript_text = transcription.get("text", "").strip() or "(No words/swaras detected.)"

    return f"""
Learner context:
- Focus areas: {", ".join(context.focus_areas)}
- Learner level: {context.learner_level}
- Practice item: {context.practice_item or "Not specified"}
- Raga: {context.raga or "Not specified"}
- Tala: {context.tala or "Not specified"}
- Shruthi / pitch reference: {context.shruthi or "Not specified"}
- Additional notes: {context.notes or "None"}

Focus area definitions:
{chr(10).join(focus_descriptions)}

Transcription:
{transcript_text}

Timestamped transcription segments:
{segments}

Return feedback as JSON only. Requirements:
- Use the timeline array for time-scaled feedback.
- Reference segment start/end ranges when possible.
- Include both strengths and corrections.
- For Varisai, comment on swara pattern consistency when swaras are visible.
- For Shruthi, avoid claiming exact cents or frequencies unless present in the input.
- Keep recommendations short and practice-oriented.
""".strip()


def _format_segments(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return "No segment timestamps were returned. Use approximate ranges such as 'whole recording'."

    formatted: list[str] = []
    for segment in segments:
        start = _format_seconds(segment.get("start"))
        end = _format_seconds(segment.get("end"))
        text = str(segment.get("text", "")).strip()
        formatted.append(f"- {start} to {end}: {text}")
    return "\n".join(formatted)


def _format_seconds(value: Any) -> str:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return "unknown"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"
