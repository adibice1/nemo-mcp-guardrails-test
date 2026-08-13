# Local Containerisation

The GMS frontend and backend now run as production-style containers alongside
the existing Postgres and pgAdmin services.

## Services

| Service | Local URL or port | Purpose |
| --- | --- | --- |
| `frontend` | `http://127.0.0.1:3000` | Next.js management UI |
| `backend` | `http://127.0.0.1:8000` | FastAPI management and runtime API |
| `postgres` | `${POSTGRES_PORT:-5432}` | Persistent policy and management data |
| `pgadmin` | `http://127.0.0.1:5050` | Optional database administration UI |

The frontend image uses `NEXT_PUBLIC_API_BASE_URL=/api/gms`. Its Next.js route
handler proxies that same-origin path to the runtime-only
`GMS_API_BASE_URL=http://backend:8000`. Browser code therefore does not need to
resolve the private Compose service name.

## Start And Verify

Keep the real local `.env` at the repository root. Docker Compose injects it
into the backend at runtime; neither Docker image contains the file.

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

Verify each layer:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod http://127.0.0.1:3000/api/gms/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3000/login
```

Expected results are `status: ok`, `database: reachable`, proxy `status: ok`,
and HTTP `200` for Login.

To follow service logs:

```powershell
docker compose logs -f backend frontend
```

To stop only the app containers while leaving Postgres and pgAdmin running:

```powershell
docker compose stop backend frontend
```

`docker compose down` stops the whole stack but retains named volumes unless
`--volumes` is explicitly supplied. Do not use `--volumes` when local database
data must be preserved.

## GitHub MCP In Local Docker

The current backend launches GitHub MCP with the Docker CLI over stdio. Local
Compose therefore mounts Docker Desktop's `/var/run/docker.sock` into the
backend and runs that service as root. `GITHUB_MCP_READ_ONLY=1` remains the
safe default.

This socket mount grants broad control of the local Docker engine. It is a
development-only bridge, not the OpenShift production design. Before OpenShift
deployment, GitHub MCP should run as a separately managed container/sidecar or
remote MCP service with its own restricted identity and network boundary.

## Image Layout

- Root `Dockerfile`: multi-stage Python backend image. A temporary compiler
  stage builds Linux wheels; the runtime stage does not retain `g++`.
- `frontend/Dockerfile`: multi-stage Next.js standalone production image.
- Root and frontend `.dockerignore`: exclude secrets, development dependencies,
  caches, logs and generated output from image build contexts.
- `requirements.txt`: UTF-8 and Windows-only packages use platform markers so
  Linux image builds skip them.

## Next Deployment Slice

The next milestone is Azure Container Registry and GitHub Actions:

1. Create ACR repositories for `gms-backend` and `gms-frontend`.
2. Manually tag, push and pull one tested image pair.
3. Add pull-request CI for backend tests, frontend build and image builds.
4. Add main-branch CD using GitHub-to-Azure OIDC and the `AcrPush` role.
5. Tag immutable images with the Git commit SHA.

