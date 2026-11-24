# Centralis

Centralis is the SALISES visitor centre application. It includes visitor registration and check-in, staff and administrator tools, inventory, reservations, fines, journal sales, and reports.

## Deploy the frontend to Vercel

The Vercel project serves the Vue frontend and proxies its `/api/*` requests to the Flask API. The Flask API must be running at a public HTTPS URL on a host with persistent storage. This repository currently stores records in JSON files, so do not use an ephemeral serverless filesystem for the API data.

1. Push this repository to GitHub, GitLab, or Bitbucket and import it into Vercel.
2. Set **Root Directory** to `frontend`.
3. Use these build settings:

   | Setting | Value |
   | --- | --- |
   | Framework preset | Vite |
   | Install command | `npm ci` |
   | Build command | `npm run build` |
   | Output directory | `dist` |

4. Deploy the Flask API separately on a persistent host. Give it a public HTTPS URL and configure its working directory at the repository root so the existing `data/` JSON store is on persistent storage. Set a strong `JWT_SECRET_KEY` in the API host's environment. A typical WSGI start command is `gunicorn run:app` (install `gunicorn` alongside `requirements.txt` on that host).
5. In Vercel, open **Project Settings → Environment Variables** and add:

   | Name | Value |
   | --- | --- |
   | `BACKEND_URL` | The Flask API's HTTPS origin, for example `https://centralis-api.example.com` |

   Keep this as a server-side variable. Do not prefix it with `VITE_`. The Vercel function in `frontend/api/[...path].js` forwards API requests and receipt/report downloads to this backend.
6. Redeploy after setting the environment variable.

The SPA rewrite in `frontend/vercel.json` serves the Vue application for direct page loads. Open `https://<your-vercel-domain>/auth` to reach staff and administrator sign-in. After sign-in, staff or admin users land in the dashboard; the existing visitor page remains at `/`.

### Create the first administrator

The repository does not expose a public first-admin setup endpoint. Create the first admin securely on the API host (or locally before deploying) using the Flask application shell:

```sh
flask --app run.py shell
```

Then, in the shell, enter:

```python
from app.modules.authentication import create_user
create_user({"name": "Administrator", "email": "admin@example.com", "password": "use-a-unique-password", "role": "admin"})
```

Change the sample name, email, and password. The user record is stored in `data/user.json`; ensure that directory persists on the API host. After the first administrator signs in at `/auth`, they can create staff accounts in the dashboard.

## Run locally

1. Create a virtual environment and install dependencies:

   ```powershell
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   $env:JWT_SECRET_KEY = "<a-long-random-secret>"
   ```

2. Start the Flask API in one terminal:

   ```powershell
   .\venv\Scripts\python.exe run.py
   ```

3. Start the Vite frontend in another terminal:

   ```powershell
   Set-Location frontend
   npm ci
   npm run dev
   ```

The Vite development server proxies API requests to `http://127.0.0.1:5000`. Create the first administrator with the Flask shell instructions above, then open `/auth` on the Vite development server.
