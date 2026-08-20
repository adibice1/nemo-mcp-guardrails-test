# Container Images And Azure Container Instances

The GMS has separate production-style images for the FastAPI backend and
Next.js frontend. Docker Compose remains available for local integration tests,
but it is not required to build, tag, or push the images requested by the
deployment team.

## Image Contracts

| Image | Internal port | Purpose |
| --- | --- | --- |
| `guardrail-be` | `8000` | FastAPI management and guarded runtime API |
| `guardrail-fe` | `3000` | Next.js management UI and `/api/gms` proxy |

Internal ports belong to the processes inside each image. A local command such
as `-p 8080:8000` may map host port `8080` to backend port `8000`, but the image
itself still listens on `8000`. Azure Container Instances exposes container
ports directly and does not provide Docker-style port remapping.

The frontend is built with `NEXT_PUBLIC_API_BASE_URL=/api/gms`. Browser calls
therefore use the frontend origin, while the server-side route handler forwards
them to `GMS_API_BASE_URL`.

## GitHub MCP In The Backend Image

The backend image copies the pinned official GitHub MCP executable into
`/usr/local/bin/github-mcp-server` and sets:

```env
GITHUB_MCP_LAUNCH_MODE=native
```

The backend launches that executable over stdio with the selected app PAT,
read-only setting, and GitHub toolsets. It does not need Docker-in-Docker, a
Docker socket mount, or root access.

Running the Python API directly outside a container still defaults to
`GITHUB_MCP_LAUNCH_MODE=docker`, preserving the existing local development
workflow. `GITHUB_MCP_READ_ONLY=1` remains the safe default in both modes.

## Build Directly

Run these commands from the repository root. ACI uses Linux x86-64 images, so
the platform is explicit:

```powershell
docker build --platform linux/amd64 -t guardrail-be:latest .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_BASE_URL=/api/gms -t guardrail-fe:latest .\frontend
docker image ls --filter "reference=guardrail-*"
```

The final `.` in the backend command and `.\frontend` in the frontend command
are the build contexts. Running either command from the wrong directory can
make Docker unable to find the corresponding Dockerfile or source files.

## Test With Docker Run

Start the backend against a reachable PostgreSQL instance. The container must
not use `localhost` for a database running on the Windows host; use
`host.docker.internal` and the host's actual PostgreSQL port:

```powershell
docker run --rm --name guardrail-be --env-file .env -e DATABASE_URL="postgresql+psycopg://USER:PASSWORD@host.docker.internal:5433/nemo_mcp_guardrails" -p 8000:8000 guardrail-be:latest
```

In another terminal, verify the backend and start the frontend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
docker run --rm --name guardrail-fe -e GMS_API_BASE_URL=http://host.docker.internal:8000 -p 3000:3000 guardrail-fe:latest
```

Then open `http://127.0.0.1:3000/login` and verify the proxy:

```powershell
Invoke-RestMethod http://127.0.0.1:3000/api/gms/health
```

Replace the example database user, password, port, and database name with the
local values. The home computer normally uses host port `5433`; the work
computer may use `5432`. Never put real credentials in committed commands or
documentation.

## Optional Local Compose Test

Compose remains useful when Postgres, pgAdmin, backend, and frontend should be
started together:

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

The Compose backend now uses the same native GitHub MCP executable as ACI. It
does not mount `/var/run/docker.sock` or run as root. Local URLs remain:

```text
Frontend:       http://127.0.0.1:3000
Backend:        http://127.0.0.1:8000
Frontend proxy: http://127.0.0.1:3000/api/gms/health
pgAdmin:        http://127.0.0.1:5050
```

## Push To Azure Container Registry

After Azure CLI authentication and ACR login:

```powershell
az login
az acr login --name guardrail

docker tag guardrail-be:latest guardrail.azurecr.io/guardrail-be:latest
docker push guardrail.azurecr.io/guardrail-be:latest

docker tag guardrail-fe:latest guardrail.azurecr.io/guardrail-fe:latest
docker push guardrail.azurecr.io/guardrail-fe:latest
```

For repeatable releases, also tag both images with the same Git commit SHA
instead of deploying only mutable `latest` tags.

## Recommended ACI Layout

Deploy the frontend and backend in one Linux multi-container ACI group:

```text
Public request
-> frontend container :3000
-> Next.js /api/gms proxy
-> http://127.0.0.1:8000
-> backend container :8000
-> external PostgreSQL and Azure/OpenAI/GitHub services
```

Set this frontend runtime variable in the container group:

```env
GMS_API_BASE_URL=http://127.0.0.1:8000
```

Expose frontend port `3000` from the group. Keep backend port `8000` internal
unless another trusted application must call it directly. If a public standard
port such as `80` or TLS on `443` is required, place Azure Front Door,
Application Gateway, or another ingress/reverse proxy in front; do not change
the backend process to port `80` merely to imitate host port mapping.

Use an external persistent PostgreSQL service for deployment. A database
container inside ACI is ephemeral and is not the production persistence plan.
The deployment team should inject secrets at runtime and preferably grant ACI
managed identity permission to pull images from ACR.

## Required Runtime Configuration

The deployment team needs environment values for:

- PostgreSQL connection details or `DATABASE_URL`.
- `GMS_JWT_SECRET`.
- Azure OpenAI endpoint, API version, deployment, and credential.
- GitHub PAT environment references used by enabled app connectors.
- `GITHUB_MCP_READ_ONLY`, normally `1` except controlled write demos.
- Any existing NeMo runtime limits and debug flags required by the environment.

Do not bake these values into either image.

## Next Deployment Slice

1. Build and locally test both images with `docker run`.
2. Push one matching image pair to `guardrail.azurecr.io`.
3. Hand image names, ports, health endpoints, and runtime variables to the ACI
   deployment owner.
4. Validate login, policy CRUD, frontend proxy health, and one guarded GitHub
   request in the deployed environment.
5. Add GitHub Actions CI for tests/builds, then CD with GitHub-to-Azure OIDC and
   immutable commit-SHA image tags.

References:

- [Azure Container Instances container groups](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-container-groups)
- [ACI troubleshooting and port behavior](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-troubleshooting)
- [Pull ACR images from ACI with managed identity](https://learn.microsoft.com/en-us/azure/container-instances/using-azure-container-registry-mi)
- [GitHub MCP native binary configuration](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-copilot-cli.md)
