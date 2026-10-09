# Home Computer: Online Database Access

Updated 2026-10-09. Online provider, hostname, database name, credentials, and
network access requirements still need confirmation from the deployment owner.
This guide uses placeholders; no online connection or database copy was made.

## Choose The Connection You Need

| Setup | Where requests go | Where account/policy changes are stored |
| --- | --- | --- |
| Home frontend + home API + local PostgreSQL | API at 127.0.0.1:8000, DB at localhost:5433 | Home database only |
| Home frontend + deployed API | Deployed frontend's /api/gms proxy | Database used by the deployed backend |
| Home frontend + home API + online PostgreSQL | API at 127.0.0.1:8000, DB at the online hostname | Shared online database |

The work computer's confirmed local DB is Docker PostgreSQL on 5432. Home's
5433 is a local Docker mapping, not the online server's port. Matching account
passwords on two sites do not prove they share a database. Restoring a local
backup online makes a separate copy; later changes do not automatically sync.

## Option A: Use The Deployed API From Your Home Frontend

This uses the online database through the deployed backend and does not require
database credentials on the home computer.

1. Obtain the deployed frontend's actual base URL and confirm its `/api/gms/health`
   endpoint is reachable. The backend's private port 8000 is not the public URL.
2. Set ignored `frontend/.env.local` to the actual deployed proxy URL. Example
   when the deployment has HTTPS:

   ```env
   NEXT_PUBLIC_API_BASE_URL=https://DEPLOYED_GMS_HOST/api/gms
   ```

   Use the deployment's actual scheme/host; HTTPS is not assumed to have been
   configured by this project. Do not place database credentials in frontend
   configuration.
3. The deployed backend must allow your home frontend origin through
   `NEMO_CORS_ORIGINS`, e.g. `http://localhost:3000` and/or
   `http://127.0.0.1:3000`. A different frontend port needs its own origin.
4. Stop any other Next development server using this frontend's `.next`
   directory, then run `npm.cmd run dev` from `frontend/`. Restart after changing
   `NEXT_PUBLIC_API_BASE_URL`; it is incorporated into the browser bundle.
5. Open the local Login page and sign in to an account in the deployed DB.
   Sign in again when switching backend targets; stored tokens belong to the
   backend that issued them.

New features also require the deployed backend version that implements them.
The new password-change endpoint is currently a source change; these changes
have not been built/published/deployed to the online service by this session.

## Option B: Connect Your Home Python Backend Directly To Online PostgreSQL

1. Obtain the database host, port, database name, database username/password,
   TLS settings/root CA, and any VPN/private-network or firewall requirements.
   These are database credentials, distinct from your GMS management login.
   If public access is used, the provider must permit the home public IP.
2. Preserve your current local `.env` privately so you can return to port 5433.
   Set DATABASE_URL in the ignored repository-root `.env`. For example:

   ```env
   DATABASE_URL=postgresql+psycopg://DB_USER:URL_ENCODED_PASSWORD@ONLINE_DB_HOST:5432/DB_NAME?sslmode=verify-full
   ```

   Replace every placeholder and use the provider's actual port. SQLAlchemy
   requires URL encoding for special characters in user/password components,
   such as `%40` for `@` and `%2F` for `/`.
   [SQLAlchemy URL documentation](https://docs.sqlalchemy.org/en/20/core/engines.html#escaping-special-characters-such-as-signs-in-passwords)

   Configure the provider's trusted root certificate. If needed, append
   `&sslrootcert=C:/certs/provider-root-ca.pem` using a real local certificate
   path; URL-encode spaces or other special characters in that query value.
   `verify-full` checks the server certificate and hostname. Follow the
   provider's CA instructions; do not turn off certificate verification to
   conceal a connection error.
   [PostgreSQL SSL documentation](https://www.postgresql.org/docs/current/libpq-ssl.html)
3. Keep the home frontend pointed at the home API:

   ```env
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
   ```

4. Verify the target and connectivity without migrations or table creation.
   From the repository root, this prints only host/port/database and a success
   flag, never the connection URL or password:

   ```powershell
   @'
   import sys
   sys.path.insert(0, "src")
   from sqlalchemy import create_engine, text
   from sqlalchemy.engine import make_url
   from nemo_mcp_guardrails.database.connection import get_database_url
   url = make_url(get_database_url())
   print({"host": url.host, "port": url.port, "database": url.database})
   try:
       engine = create_engine(url, connect_args={"connect_timeout": 5})
       with engine.connect() as connection:
           print("Database reachable:", connection.execute(text("SELECT 1")).scalar() == 1)
       engine.dispose()
   except Exception as error:
       print("Connection failed:", type(error).__name__)
       raise SystemExit(1) from None
   '@ | .\.venv\Scripts\python.exe -
   ```

   An already-set process DATABASE_URL takes precedence over `.env`. If the
   printed host is still localhost, inspect that override before proceeding.
5. Confirm the online schema matches this source version, then restart the home
   API with `.\.venv\Scripts\python.exe scripts/run_api.py`. Startup currently
   calls `create_all` and can create missing prototype tables. This particular
   password/UI change needs no migration. Restart the frontend if its API URL
   changed and sign in using an account in the online database.

Use the direct Python launcher for this option: `docker-compose.yml` explicitly
overrides the backend DATABASE_URL to its local `postgres` service. Merely
editing `.env` does not change the Compose backend's target.

The local GMS_JWT_SECRET can remain local when signing into the home API; it
does not need to match the deployed backend simply to share database rows.
Switching API targets requires a fresh login. Deploy the updated password-version
validation to every backend using the shared DB for consistent session revocation.

## DBeaver And Returning To Local Development

For DBeaver, create a separate online connection using the online host/port,
database, username and original unencoded password. Configure its SSL/CA
settings according to the provider. Keep the existing `localhost:5433` home
connection as a separate entry and label the online connection clearly.

When the home API uses the shared database, User Management and policy CRUD
change shared rows immediately, including accounts used by the deployed site.
Use isolated tests such as `test_management_password_change.py` for regression
checks; existing Postgres integration tests/seeds/migrations can mutate whichever
database DATABASE_URL selects and should stay on local development data unless
their online execution is deliberately authorized.

To return home to local mode, restore its local DATABASE_URL with port 5433,
restore the frontend API URL to `http://127.0.0.1:8000`, restart both processes,
and sign in to the local DB. Preserve work/home port differences and never
commit `.env`, `.env.local`, connection passwords, or copied production secrets.
