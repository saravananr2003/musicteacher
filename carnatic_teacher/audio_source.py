"""Helpers for loading practice recordings from local uploads or Google Drive."""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests

SUPPORTED_AUDIO_TYPES = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "ogg", "wav", "webm"]

GOOGLE_DRIVE_FILE_ID_PATTERNS = (
    r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
    r"https?://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
    r"https?://drive\.google\.com/uc\?(?:export=download&)?id=([a-zA-Z0-9_-]+)",
    r"https?://docs\.google\.com/uc\?(?:export=download&)?id=([a-zA-Z0-9_-]+)",
)


@dataclass(frozen=True)
class AudioRecording:
    name: str
    data: bytes


def audio_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def is_supported_audio(filename: str) -> bool:
    return audio_extension(filename) in SUPPORTED_AUDIO_TYPES


def extract_google_drive_file_id(url: str) -> str | None:
    trimmed = url.strip()
    for pattern in GOOGLE_DRIVE_FILE_ID_PATTERNS:
        match = re.search(pattern, trimmed)
        if match:
            return match.group(1)
    return None


def download_google_drive_audio(url: str) -> AudioRecording:
    file_id = extract_google_drive_file_id(url)
    if not file_id:
        raise ValueError(
            "Could not read a Google Drive file ID from that link. "
            "Paste a share link like https://drive.google.com/file/d/FILE_ID/view"
        )

    session = requests.Session()
    download_url = "https://drive.google.com/uc?export=download"
    try:
        response = session.get(download_url, params={"id": file_id}, stream=True, timeout=60)
        response.raise_for_status()

        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                response = session.get(
                    download_url,
                    params={"id": file_id, "confirm": value},
                    stream=True,
                    timeout=60,
                )
                response.raise_for_status()
                break
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise ValueError(
                "Could not download that Google Drive file. Check the link, make sure the "
                "file still exists, and share it with 'Anyone with the link'."
            ) from exc
        raise ValueError(
            "Could not download that Google Drive file. Confirm the link is public and try again."
        ) from exc
    except requests.RequestException as exc:
        raise ValueError(
            "Could not reach Google Drive. Check the link and your network connection."
        ) from exc

    filename = _filename_from_response(response) or f"google_drive_recording_{file_id}.mp3"
    if not is_supported_audio(filename):
        raise ValueError(
            f"Google Drive file '{filename}' is not a supported audio type. "
            f"Use one of: {', '.join(SUPPORTED_AUDIO_TYPES)}."
        )

    return AudioRecording(name=filename, data=response.content)


def _filename_from_response(response: requests.Response) -> str | None:
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename*=" in content_disposition:
        encoded_name = content_disposition.split("filename*=")[-1].split("''", 1)[-1]
        return encoded_name.strip('"\'')
    if "filename=" in content_disposition:
        return content_disposition.split("filename=")[-1].strip('"\'')
    return None
