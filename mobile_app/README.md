# NetSecure StudyOS Mobile App

This folder contains a frontend-first Expo React Native app scaffold for NetSecure StudyOS.

## Stack

- Expo with TypeScript
- Expo Router for file-based navigation
- Shared theme tokens in `theme/index.ts`
- Reusable layout components in `components/`

## Screens

- Dashboard
- Quiz
- Exam Simulator
- Weak Topics
- Study Plan
- Cheat Sheets
- Predicted Score

## Run

1. Open a terminal in `mobile_app/`.
2. Install dependencies:

```bash
npm install
```

3. Start Expo:

```bash
npm run start
```

4. Then launch on:

- iOS simulator with `npm run ios`
- Android emulator with `npm run android`
- Expo Go by scanning the QR code from `npm run start`

## Sharing The Mobile App

- For quick testing, use Expo Go and the QR code from `npm run start`.
- For broader sharing or installable builds, use EAS with the included `eas.json`.
- Typical flow:

```bash
npx eas login
npx eas build --platform all --profile preview
```

- Save the resulting install/share URL in the Streamlit app under `Access And Share Settings` so users can find it in one place.

## Notes

- The app reads a shared local sync snapshot from `mobile_app/data/mobile_sync.json`.
- The Streamlit app refreshes that snapshot whenever profile/readiness data is updated or a quiz result is saved.
- The structure is App Store-ready from a frontend standpoint: typed routes, themed components, reusable screen shells, and clean screen separation.
