"""Streamlit UI for Carnatic music practice feedback."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from openai import OpenAI

from carnatic_teacher.openai_analysis import (
    FOCUS_AREA_DESCRIPTIONS,
    PracticeContext,
    analyze_practice,
    transcribe_audio,
)


LEARNER_LEVELS = ["Beginner", "Intermediate", "Advanced"]
DEFAULT_FOCUS_AREAS = ["Varisai", "Shruthi", "Thalam"]
SUPPORTED_AUDIO_TYPES = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "ogg", "wav", "webm"]


def main() -> None:
    st.set_page_config(
        page_title="Carnatic Music Teacher",
        page_icon=":musical_note:",
        layout="wide",
    )

    st.title("Carnatic Music Teacher")
    st.caption(
        "Upload a vocal practice recording and receive timestamped feedback for "
        "Carnatic music fundamentals."
    )

    _render_how_it_works()

    api_key = _get_api_key()
    uploaded_audio = st.file_uploader(
        "Upload your recorded voice practice",
        type=SUPPORTED_AUDIO_TYPES,
        help="Short practice clips work best for focused feedback.",
    )

    if uploaded_audio:
        st.audio(uploaded_audio.getvalue())

    with st.form("practice_context"):
        st.subheader("Practice details")

        col_left, col_right = st.columns(2)
        with col_left:
            focus_areas = st.multiselect(
                "What should the teacher focus on?",
                options=list(FOCUS_AREA_DESCRIPTIONS.keys()),
                default=DEFAULT_FOCUS_AREAS,
            )
            learner_level = st.selectbox("Learner level", LEARNER_LEVELS)
            practice_item = st.text_input(
                "Practice item",
                placeholder="Example: Sarali Varisai 1, Janta Varisai, Alankaram",
            )
        with col_right:
            raga = st.text_input("Raga", placeholder="Example: Mayamalavagowla")
            tala = st.text_input("Tala", placeholder="Example: Adi tala")
            shruthi = st.text_input("Shruthi / pitch reference", placeholder="Example: C#, 1 kattai")

        notes = st.text_area(
            "Additional notes",
            placeholder="Mention teacher instructions, target tempo, or known trouble spots.",
        )

        analyze_clicked = st.form_submit_button("Analyze recording", type="primary")

    if analyze_clicked:
        _run_analysis(
            api_key=api_key,
            uploaded_audio=uploaded_audio,
            context=PracticeContext(
                focus_areas=focus_areas,
                raga=raga,
                tala=tala,
                shruthi=shruthi,
                practice_item=practice_item,
                learner_level=learner_level,
                notes=notes,
            ),
        )


def _render_how_it_works() -> None:
    with st.expander("How this works", expanded=False):
        st.markdown(
            """
            1. The recording is transcribed with OpenAI speech-to-text.
            2. The transcript and available timestamps are evaluated against the selected Carnatic focus areas.
            3. The app returns strengths, corrections, a timestamped timeline, and a short practice plan.

            For precise pitch tracking, pair this feedback with a tambura/shruthi box and a teacher's review.
            """
        )


def _get_api_key() -> str:
    env_key = os.getenv("OPENAI_API_KEY", "")
    secrets_key = ""
    try:
        secrets_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secrets_key = ""

    if env_key or secrets_key:
        return env_key or secrets_key

    with st.sidebar:
        st.header("OpenAI settings")
        return st.text_input(
            "OpenAI API key",
            type="password",
            help="You can also set OPENAI_API_KEY in your environment or .streamlit/secrets.toml.",
        )


def _run_analysis(
    api_key: str,
    uploaded_audio: Any,
    context: PracticeContext,
) -> None:
    if not api_key:
        st.error("Add an OpenAI API key to analyze the recording.")
        return

    if uploaded_audio is None:
        st.error("Upload an audio recording before starting analysis.")
        return

    if not context.focus_areas:
        st.error("Select at least one focus area.")
        return

    client = OpenAI(api_key=api_key)
    audio_bytes = uploaded_audio.getvalue()

    try:
        with st.status("Transcribing and analyzing your recording...", expanded=True) as status:
            st.write("Transcribing the uploaded audio with timestamps.")
            transcription = transcribe_audio(
                client=client,
                audio_bytes=audio_bytes,
                filename=uploaded_audio.name,
            )

            st.write("Generating Carnatic music feedback.")
            feedback = analyze_practice(
                client=client,
                transcription=transcription,
                context=context,
            )
            status.update(label="Analysis complete", state="complete")

    except Exception as exc:
        st.exception(exc)
        return

    _render_feedback(feedback, transcription)


def _render_feedback(feedback: dict[str, Any], transcription: dict[str, Any]) -> None:
    st.subheader("Teacher feedback")

    score_col, summary_col = st.columns([1, 3])
    with score_col:
        st.metric("Overall score", f"{feedback.get('overall_score', '-')}/10")
    with summary_col:
        st.write(feedback.get("summary", "No summary returned."))

    good_col, improve_col = st.columns(2)
    with good_col:
        st.markdown("### What went well")
        _render_bullets(feedback.get("what_went_well", []))
    with improve_col:
        st.markdown("### Needs improvement")
        _render_bullets(feedback.get("needs_improvement", []))

    st.markdown("### Timeline")
    timeline = feedback.get("timeline", [])
    if timeline:
        st.dataframe(timeline, use_container_width=True, hide_index=True)
    else:
        st.info("No timeline entries were returned.")

    st.markdown("### Practice plan")
    _render_bullets(feedback.get("practice_plan", []))

    with st.expander("Transcript"):
        st.write(transcription.get("text", "No transcript returned."))

    disclaimer = feedback.get("disclaimer")
    if disclaimer:
        st.caption(disclaimer)


def _render_bullets(items: list[str]) -> None:
    if not items:
        st.write("No items returned.")
        return
    for item in items:
        st.markdown(f"- {item}")


if __name__ == "__main__":
    main()
