# Music Teacher

Music Teacher is a Python UI app for Carnatic vocal practice feedback. Users can
upload a recorded voice clip, choose focus areas such as Varisai, Shruthi, and
Thalam, and receive OpenAI-generated feedback with timestamped observations and
practice recommendations.

## Features

- Streamlit web UI for uploading vocal recordings from your computer or Google Drive.
- Carnatic focus areas:
  - Varisai
  - Shruthi
  - Thalam
  - Gamakam
  - Raga Lakshanam
  - Pronunciation
- Optional practice context for raga, tala, shruthi, practice item, and learner
  level.
- OpenAI speech-to-text transcription with segment timestamps.
- Structured feedback including:
  - Overall score
  - What went well
  - Areas needing improvement
  - Timestamped timeline
  - Short practice plan

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. Configure your OpenAI API key:

   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

   You can also enter the key in the app sidebar or store it in
   `.streamlit/secrets.toml`:

   ```toml
   OPENAI_API_KEY = "your-api-key"
   ```

## Run

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Usage tips

- Upload short clips for focused feedback from your computer or a Google Drive share link.
- For Google Drive, share the file with **Anyone with the link** before loading it in the app.
- Mention the intended raga, tala, shruthi, and exercise when possible.
- Select only the focus areas you want reviewed for a clearer response.

## Notes on pitch accuracy

The app uses OpenAI transcription and language-model feedback. It can provide
useful coaching and timestamped recommendations, but exact shruthi or pitch-drift
measurements require dedicated pitch-tracking signal processing or teacher review.
The current feedback prompt avoids inventing exact pitch measurements when that
data is not present.