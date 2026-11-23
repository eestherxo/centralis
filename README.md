# Centralis

Centralis provides the SALISES visitor centre and resource inventory interfaces.

## Run locally

1. Create a virtual environment, install the Python requirements, and provide a JWT signing secret:

   ```powershell
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   $env:JWT_SECRET_KEY = "<a-long-random-secret>"
   ```

2. Create the first administrator account once:

   ```powershell
   .\venv\Scripts\flask.exe --app run.py create-first-admin
   ```

   The command prompts for the administrator's name, email, and password, then stores the account in `data/user.json`. It does not create a default account; the local `data/` directory is ignored by Git.

3. Start the backend in one terminal:

   ```powershell
   $env:JWT_SECRET_KEY = "<the-same-secret>"
   .\venv\Scripts\python.exe run.py
   ```

4. Start the frontend in another terminal:

   ```powershell
   Set-Location frontend
   npm ci
   npm run dev
   ```

The Vite development server proxies visitor, authentication, and inventory requests to `http://127.0.0.1:5000`.

## Inventory dashboard scope

The administrator dashboard uses the existing resource create, update, and delete endpoints. The existing inventory read endpoint returns only resources that are both available and in good condition. It does not provide a complete inventory listing or reservation/borrower details, so reserved, lost, or damaged records and responsible borrowers cannot currently be reviewed or managed from the dashboard.