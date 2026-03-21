# Deployment Package

This project is now prepared for two practical deployment paths for the Streamlit app and one for the Expo mobile app.

## Recommended Production Path

- Streamlit app: self-host locally or on a small VM and expose it with Cloudflare Tunnel
- Mobile app: build preview and production binaries with Expo EAS

This path keeps the app behind a passcode gate while avoiding direct inbound port exposure.

## Option 1: Streamlit Community Cloud

Best for:
- fastest public launch
- GitHub-based portfolio sharing
- lowest setup friction

Steps:
1. Push this repository to GitHub.
2. Make sure `requirements.txt` is committed.
3. Go to Streamlit Community Cloud and create a new app from the repository.
4. Set the entrypoint to `app.py`.
5. Deploy and choose your `streamlit.app` subdomain.
6. Open the deployed app, create the passcode, and save the public URL under `Access And Share Settings`.

Notes:
- This is the easiest public link for LinkedIn and GitHub.
- The app is local-first, so persistent data depends on the deployment environment’s filesystem behavior.

## Option 2: Self-Host + Cloudflare Tunnel

Best for:
- stronger control over runtime and persistence
- safer public exposure
- cleaner custom-domain story

Steps:
1. Start the app on the host:

```bash
streamlit run app.py
```

2. Install `cloudflared`.
3. Authenticate and create a tunnel in Cloudflare.
4. Use the example config in `deploy/cloudflared-config.example.yml`.
5. Route a public hostname to the local app on `http://localhost:8501`.
6. Save the resulting public URL in the app under `Access And Share Settings`.

Quick test tunnel:

```bash
cloudflared tunnel --url http://localhost:8501
```

Production tunnel:
- use a named tunnel
- use your domain
- keep `cloudflared` running as a service

## Mobile App Deployment

Best path:
- Expo EAS preview build for testers
- Expo EAS production build for App Store / Play Store submission

From `mobile_app/`:

```bash
npm install
npx eas login
npx eas build --platform all --profile preview
```

When ready for stores:

```bash
npx eas build --platform all --profile production
```

After build:
- copy the share/install URL
- save it in Streamlit under `Access And Share Settings` as the mobile app URL

## Final Launch Checklist

- Confirm `streamlit run app.py` works locally
- Confirm passcode setup and unlock flow work
- Confirm onboarding works for a fresh profile
- Confirm quiz save, exports, and markdown summary work
- Confirm home-lab completion gate works
- Confirm mobile app starts with `npm run start`
- Deploy the Streamlit app publicly
- Build the mobile preview app
- Save both public URLs in the Streamlit app
- Add both links to GitHub and LinkedIn

## GitHub / LinkedIn Assets

- Public app URL
- Mobile app install/share URL
- `data/exports/study_summary.md`
- 2-3 screenshots of the dashboard, labs, and prediction views
- short demo video or GIF
