# EmailVerif frontend

React + Vite frontend for the EmailVerif application.

## Local development

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

`VITE_API_BASE_URL=/api` uses the local Vite proxy to the FastAPI backend on
port `8000`.

## Environment variables

Vite embeds `VITE_*` variables at build time. Add all values below to
`.env.local` for local development and to the Vercel project's **Environment
Variables** settings for Production and Preview:

```text
VITE_API_BASE_URL=https://your-public-backend.example.com/api
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

For a public deployment, `VITE_API_BASE_URL` must point to the deployed
backend. Leaving it as `/api` works locally but the Vercel project only serves
the React app, not the FastAPI service.

After changing an environment variable in Vercel, redeploy the project. The
Firebase web configuration is required for login and signup; without it the
public marketing page still renders, but authentication is unavailable.

## Vercel setup

The repository root is the Vercel project root:

- Framework: Vite
- Install command: `cd frontend && npm ci`
- Build command: `cd frontend && npm run build`
- Output directory: `frontend/dist`
- SPA rewrite: `/` to `/index.html`

The committed `vercel.json` already contains these settings.

### Public access

If a deployment redirects visitors to a Vercel login screen, open:

**Vercel Project → Settings → Deployment Protection**

Disable **Vercel Authentication** for the Production environment if the landing
page must be public. Preview deployments created for individual Git commits can
remain protected.

Do not use an ephemeral commit deployment URL as the production website. Use
the project's stable production domain or a connected custom domain.

## Verify a deployment

1. Open the stable deployment URL in a private browser window.
2. Confirm the network response for `/` is `200`, rather than a redirect to
   `vercel.com/sso-api`.
3. Confirm the HTML references a hashed file under `/assets/`.
4. Open browser DevTools and confirm there is no `auth/invalid-api-key` error.
5. Check the deployed backend directly with
   `https://your-backend.example.com/api/health`.

## Commands

```bash
npm run dev      # Start Vite locally
npm run build    # Create frontend/dist
npm run preview  # Preview the production build
npm run lint     # Run ESLint
```
