# AGENTS.md

## Cursor Cloud specific instructions

### Repository layout

- `main` currently contains only a short README.
- The full **Music Teacher** Streamlit app lives on branch `cursor/carnatic-music-teacher-app-3a14` (`app.py`, `carnatic_teacher/`, `requirements.txt`).
- Check out that branch (or merge it) before installing dependencies or running the app.

### Services

| Service | Required | How to run |
|---------|----------|------------|
| Streamlit app | Yes | `source .venv/bin/activate && streamlit run app.py` |
| OpenAI API | Yes (for analysis) | `export OPENAI_API_KEY="..."`, `.streamlit/secrets.toml`, or sidebar input |

There is no database, Docker stack, or separate API server.

### One-time VM setup

Ubuntu images may need `python3.12-venv` before creating a virtualenv:

```bash
sudo apt-get install -y python3.12-venv
```

### Run / develop

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"   # optional for UI-only smoke tests
streamlit run app.py
```

Default URL: http://localhost:8501

### Lint / tests

No linter, formatter, or test suite is configured in this repo. Smoke-test by importing `carnatic_teacher` and loading the Streamlit UI.

### Gotchas

- **API key**: Upload + form submission works without a key, but analysis shows: "Add an OpenAI API key to analyze the recording."
- **Branch**: Do not assume `app.py` exists on `main`.
- **Secrets file**: `.streamlit/secrets.toml` is gitignored; create it locally if you prefer secrets over env vars.
