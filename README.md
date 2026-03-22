# NetSecure StudyOS

NetSecure StudyOS is a local-first certification study system with an upgraded Streamlit app and a new Expo React Native mobile scaffold.

## What Changed

- Refreshed the Streamlit dashboard with stronger spacing, cleaner cards, better chart styling, and clearer strong/weak topic sections.
- Added a first-run onboarding flow that captures target exam, target date, weekly study hours, and self-rated domain confidence.
- Added a local passcode gate with hashed passcode storage, basic lockout protection, and editable public/mobile share-link settings.
- Improved adaptive learning logic so recent misses matter more, repeated correct answers reduce topic urgency, and readiness is more stable.
- Added `Recommended Next Topic`, `Confidence By Domain`, and a local `Predicted Score` feature.
- Upgraded the 100-question fatigue simulation with live progress, pacing, block review, top missed topics, and a recovery plan.
- Added persistent in-progress quiz/exam sessions with local resume support.
- Added a spaced-repetition review queue plus topic streak/history views.
- Added a markdown export that creates a polished study summary for GitHub or LinkedIn.
- Added certification-specific home lab walkthroughs with step-by-step directions and resume bullet suggestions.
- Locked home-lab resume bullets behind full completion plus a required Built / Verified / Evidence reflection note.
- Expanded the certification catalog across CompTIA, Cisco, AWS, and Azure with starter domains, generated quiz content, and matching home labs.
- Improved study plans with estimated time per topic, why each topic matters, and stronger weak-area prioritization.
- Improved cheat sheets with cleaner structure, key terms, memory tips, why-it-matters notes, and watch-outs.
- Added Power BI export prep for quiz history, weak topics, and readiness history under `data/exports/`.
- Added a new Expo Router mobile scaffold in `mobile_app/`.

## Project Structure

- `app.py`: Streamlit entrypoint and UI.
- `tracker.py`: Readiness, weak-topic ranking, domain confidence, prediction, fatigue analysis, and study-plan logic.
- `storage.py`: Local JSON storage plus CSV export helpers.
- `data/sessions/`: Saved in-progress quiz and simulator sessions.
- `data/mobile_sync.json`: Shared local sync snapshot for the mobile app.
- `utils.py`: Shared Streamlit UI styling and chart helpers.
- `exams.py`: Exam domains, question bank, and cheat-sheet content.
- `mobile_app/`: Expo React Native scaffold with placeholder screens and shared theme files.

## Run The Streamlit App

1. Create or activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

The app still runs locally on `http://localhost:8501`, and `.streamlit/config.toml` keeps LAN access enabled through `0.0.0.0`.

On first protected launch, the app now requires you to create a local passcode before broader sharing.

## Persistence Modes

- Local Mac run: `streamlit run app.py` keeps JSON persistence enabled for the study profile, quiz history, saved sessions, exports, and mobile sync files under `data/`.
- Streamlit Community Cloud: the app automatically switches to demo mode and keeps profile/results/session data in memory for the current browser session instead of writing local JSON files.
- If file persistence becomes unavailable unexpectedly, the app degrades to the same in-memory behavior and shows a warning instead of crashing.
- Optional overrides:
  - `NETSECURE_STUDYOS_FORCE_CLOUD_MODE=1` forces memory/demo mode.
  - `NETSECURE_STUDYOS_FORCE_LOCAL_PERSISTENCE=1` forces local file persistence checks.

## Deployment

Deployment assets are included in [DEPLOYMENT.md](/Users/rjnoord/Desktop/netsecure-studyos/DEPLOYMENT.md) and the [deploy](/Users/rjnoord/Desktop/netsecure-studyos/deploy) folder.

- `DEPLOYMENT.md`: main deployment runbook
- `deploy/cloudflared-config.example.yml`: named-tunnel example
- `deploy/start_cloudflare_quick_tunnel.sh`: quick public-share helper
- `deploy/launch_checklist.md`: final launch checklist

## Start The Mobile App

1. Open a terminal in `mobile_app/`.
2. Install dependencies:

```bash
npm install
```

3. Start Expo:

```bash
npm run start
```

Then run `npm run ios`, `npm run android`, or scan the QR code in Expo Go.

For wider sharing of the mobile app, `mobile_app/eas.json` is included for EAS builds.

## Power BI Export Path

Use the export buttons in the Streamlit dashboard. Files are saved to `data/exports/`.

- `quiz_history.csv`
- `weak_topics_<exam>.csv`
- `readiness_history_<exam>.csv`

These are written locally so Power BI can point at a stable folder for refresh.

## Mac And iPhone Access

- Start the Streamlit app on your Mac with `streamlit run app.py`.
- On your Mac, open `http://localhost:8501`.
- On another device on the same network, open `http://YOUR-MAC-IP:8501`.
- If macOS prompts you about incoming connections for Python or Streamlit, allow them.

## Notes

- The Streamlit app remains fully local with no external API calls.
- On first local launch, the app walks through onboarding and saves the study profile to `data/user_profile.json`.
- The mobile app reads the shared local sync snapshot in `mobile_app/data/mobile_sync.json` when local file persistence is available.
- Data directories are created automatically on startup for local runs.
