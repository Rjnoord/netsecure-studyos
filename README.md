# NetSecure StudyOS

An AI-powered certification study platform built for cybersecurity and cloud exam preparation, with adaptive quizzes, performance analytics, and cross-platform delivery across web and mobile.

**Live App:** `[Add live app link here]`  
**Mobile Build:** `[Add Expo / App Store / TestFlight link here]`

**Keywords:** Python, Streamlit, React Native, Expo, analytics, adaptive learning, mobile development, cloud deployment, automation, debugging, operational efficiency, cybersecurity

## At A Glance

- Built a cross-platform certification study system using **Python, Streamlit, React Native, and Expo**
- Designed **adaptive quiz logic** and **performance analytics** for personalized study workflows
- Shipped with a **local-first architecture** and **cloud fallback** for more reliable deployment behavior
- Focused on **operational efficiency, automation, debugging, and deployment readiness**

## Overview

NetSecure StudyOS is a portfolio project built around a practical problem: certification prep tools are often static, generic, and weak on feedback. I built this system to create a more useful study experience for learners preparing for cybersecurity, cloud, and IT certifications.

The platform combines a Python + Streamlit web app with an Expo React Native mobile app to support flexible study sessions across devices. Instead of serving a fixed set of questions, it adapts to user performance, highlights weak domains, tracks readiness over time, and is structured to run well both locally and in deployment-friendly environments.

## What The App Does

NetSecure StudyOS helps users prepare for technical certifications with an AI-informed study workflow that:

- adapts quiz difficulty and topic selection based on recent performance
- tracks progress and weak areas over time
- provides analytics for readiness, confidence, and study patterns
- supports both web and mobile usage
- can run locally or in a cloud-friendly deployment mode

## Key Features

- **Adaptive Quizzes:** Personalized question flow that prioritizes weak domains and recent misses.
- **Analytics Dashboard:** Readiness tracking, confidence trends, weak-topic analysis, and study insights.
- **Mobile + Web Experience:** Streamlit for browser-based study sessions and Expo React Native for mobile access.
- **Cloud Deployment Ready:** Structured for local-first use with deployment options for public sharing and portfolio demos.
- **Study Session Persistence:** Saves progress, exports study data, and supports resumed sessions.
- **Certification-Focused Design:** Built around realistic exam preparation workflows rather than generic flashcards.

## Tech Stack

- **Backend / App Logic:** Python
- **Web App:** Streamlit
- **Mobile App:** React Native with Expo
- **AI Tutor:** Claude API (`claude-sonnet-4-6`) via the Anthropic Python SDK
- **Version Control / Collaboration:** GitHub
- **Deployment:** Cloud-hosted Streamlit workflow, Cloudflare tunnel support, Expo EAS mobile builds
- **Data / Analytics:** Pandas, Plotly, local JSON + CSV exports

## Architecture

NetSecure StudyOS uses a **local-first architecture** with a **cloud-safe fallback path**:

- **Local storage mode:** On local runs, the app writes study profiles, quiz history, saved sessions, and export files under the `data/` directory. This keeps the workflow fast and simple for development and personal use.
- **Cloud fallback mode:** In cloud-style environments where filesystem persistence is limited or unavailable, the app falls back to in-memory/session-based behavior instead of failing. This allows the project to stay demoable and portfolio-ready even on managed hosting platforms.
- **Shared mobile sync concept:** The web app can generate local sync data used by the mobile experience, supporting a broader cross-platform study workflow.

This architecture reflects a practical engineering tradeoff: prioritize operational simplicity for local use while keeping the app resilient in real deployment environments.

## Project Structure

- `app.py` - Streamlit entry point and primary UI
- `tracker.py` - readiness scoring, weak-topic ranking, and study analytics
- `storage.py` - local persistence, export logic, and fallback behavior
- `exams.py` - certification domains, question content, and study materials
- `utils.py` - shared UI and helper logic
- `data/` - local persistence for sessions, exports, and sync artifacts
- `mobile_app/` - Expo React Native mobile application
- `DEPLOYMENT.md` - deployment notes for web and mobile distribution

## Setup

### Web App

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your [Anthropic API key](https://console.anthropic.com/). This enables the AI Tutor feature. The app runs without it — AI Tutor panels will show a fallback message if the key is missing or invalid.

4. Start the Streamlit app:

```bash
streamlit run app.py
```

5. Open the app at `http://localhost:8501`

### Mobile App

1. Move into the mobile project:

```bash
cd mobile_app
```

2. Install dependencies:

```bash
npm install
```

3. Start Expo:

```bash
npm run start
```

4. Run on a device or simulator:

```bash
npm run ios
```

```bash
npm run android
```

You can also scan the Expo QR code to test on a physical device using Expo Go.

## Deployment

This project is set up for practical portfolio deployment:

- **Web:** Streamlit Community Cloud or self-hosting with Cloudflare Tunnel
- **Mobile:** Expo EAS for preview builds and production distribution

See [DEPLOYMENT.md](/Users/rjnoord/Desktop/netsecure-studyos/DEPLOYMENT.md) for the deployment workflow.

## What I Learned

Building NetSecure StudyOS pushed me to think beyond feature delivery and focus more on how a system performs in real use.

- I became more intentional about operational efficiency by keeping the project simple to run locally while still making it flexible enough to deploy, demo, and share.
- I spent more time designing for automation and repeatability, especially around analytics, exports, study tracking, and cross-platform workflows.
- I got more experience debugging real-world issues like persistence constraints, environment-specific behavior, and the differences between local development and hosted deployment.
- It also sharpened how I think about tradeoffs between speed, maintainability, usability, and the practical realities of shipping a working product.

## How I Used AI To Improve Efficiency

I used AI as a practical development tool to reduce friction and keep execution moving.

- It helped me move faster during prototyping, feature refinement, and implementation when I needed to test ideas quickly.
- I used it to work through bottlenecks in logic, edge cases, and debugging so I could spend more time on architecture, product decisions, and code quality.
- It also helped speed up process-heavy work like content drafting, workflow organization, and iteration across both the web and mobile experiences.
- The biggest benefit was shorter turnaround between idea, validation, and delivery, which made the overall development process more efficient.

## Future Improvements

- Add stronger AI-based score prediction and recommendation logic
- Publish the mobile app through the App Store / Play Store
- Replace local JSON persistence with a production database layer
- Expand the analytics dashboard with deeper benchmarking and reporting
- Add authenticated cloud sync across devices

## Why This Project Matters

NetSecure StudyOS sits at the intersection of **cybersecurity domain knowledge** and **software engineering execution**. It demonstrates full-stack product thinking, analytics-driven decision-making, deployment awareness, and cross-platform development within a single project. For recruiters, it reflects the ability to build software that is technically grounded, user-focused, and shaped by real operational constraints.
