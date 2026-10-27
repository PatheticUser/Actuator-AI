# Deploying Actuator AI on Oracle Cloud — Always Free Ubuntu ARM64 (Ampere A1)

Self-contained production deployment behind **Caddy 2** on a **linux/arm64**
VM. Replaces the old PaaS setup (the `render.yaml` / `docker-compose.prod.yml`
files were removed; there are no Railway files left in the repo).

```
Internet
   │  :80 (ACME http-01 + redirect)  :443/tcp + :443/udp (HTTPS + HTTP/3)
   ▼
┌─ OCI VM (Ubuntu 24.04 aarch64) ────────────────────────────────┐
│  docker bridge network: actuator-edge                          │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐   │
│  │ caddy       │───▶│ app :8000        │───▶│ postgres :5432│   │
│  │ :80/:443    │    │ FastAPI+React    │    │ 16-alpine     │   │
│  └─────────────┘    └──────────────────┘    └───────────────┘   │
│   only service        never published        never published    │
│   with host ports                                            │
└───────────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

| Item | Value |
|---|---|
| OCI shape | **VM.Standard.A1.Flex** (Ampere A1) — Always Free allows 4 OCPU / 24 GB |
| OS | Ubuntu 24.04 aarch64 (or 22.04) |
| Arch check | `uname -m` → `aarch64` |
| DNS | An **A record** for your domain → the VM public IP (needed before the first TLS issuance) |
| Ports | 80/tcp, 443/tcp (+ 443/udp for HTTP/3), 22/tcp (SSH) |

```bash
uname -m                 # must print: aarch64
free -h                  # 24 GB on the full Always Free allocation
nproc                    # 4
```

---

## 2. Install Docker Engine (arm64 apt packages)

```bash
# Remove distro/docker.io & snap docker if present
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  sudo apt-get remove -y $pkg
done

# Official Docker apt repository (multi-arch: uses dpkg --print-architecture)
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
                        docker-buildx-plugin docker-compose-plugin

# Run docker without sudo
sudo usermod -aG docker "$USER"
newgrp docker
```

Verify the daemon is really running on arm64:

```bash
docker version                 # Server Architecture: aarch64
docker compose version         # needs >= v2.24
docker run --rm --platform linux/arm64 alpine:3 uname -m   # → aarch64
```

> **Minimum:** Docker Engine 24+ / Docker Compose **v2.24+**.
> On OCI, also make Docker start on boot: `sudo systemctl enable docker`.

---

## 3. OCI VCN & Security List (the cloud-side firewall)

Create the network with the VCN Wizard (*"Create VCN with internet connectivity"*),
which produces: VCN + public subnet + internet gateway + route table
(`0.0.0.0/0 → Internet Gateway`) + a default Security List.

Then edit **Virtual Cloud Networks → your VCN → Security Lists →
Default Security List → Add Ingress Rules**:

| # | Source | Protocol | Dest. port | Purpose |
|---|---|---|---|---|
| 1 | `0.0.0.0/0` | TCP | **80** | HTTP → HTTPS redirect + Let's Encrypt http-01 |
| 2 | `0.0.0.0/0` | TCP | **443** | HTTPS (app + WebSocket `wss://`) |
| 3 | `0.0.0.0/0` | UDP | **443** | HTTP/3 (optional, drop this rule to disable) |
| 4 | `<your-ip>/32` | TCP | **22** | SSH — **never leave 22 open to 0.0.0.0/0** |

Notes:

* Security Lists are **stateful** — return traffic is allowed automatically;
  you only define ingress.
* Default egress (`0.0.0.0/0` all protocols) must stay open: apt, git,
  Docker Hub, Let's Encrypt, and the LLM APIs are all outbound.
* A **Network Security Group** on the instance works identically if you
  prefer NSGs over Security Lists — apply the same four rules.
* Do **not** open 5432 or 8000 at the VCN level: those services are
  intentionally unpublished and reachable only on the Docker bridge.

---

## 4. Host firewall on Ubuntu (exact commands)

### 4a. ufw (recommended)

```bash
sudo apt-get update && sudo apt-get install -y ufw

sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow 22/tcp  comment 'SSH'
sudo ufw allow 80/tcp  comment 'HTTP + ACME'
sudo ufw allow 443/tcp comment 'HTTPS + WebSocket'
sudo ufw allow 443/udp comment 'HTTP/3'

sudo ufw --force enable
sudo ufw status verbose          # verify BEFORE closing this SSH session
```

`ufw status` must show `Status: active` with exactly those four rules.

### 4b. iptables (equivalent, persistent across reboots)

Only run this instead of ufw — never both (ufw manages the iptables chains).

```bash
sudo apt-get update && sudo apt-get install -y iptables-persistent

# Order matters: established sessions first so SSH is never dropped
sudo iptables -I INPUT 1 -i lo -j ACCEPT
sudo iptables -I INPUT 2 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

sudo iptables -A INPUT -p tcp --dport 22  -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80  -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 443 -j ACCEPT

# ICMP so ping-based monitoring keeps working
sudo iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Everything else from NEW connections is dropped
sudo iptables -A INPUT -m conntrack --ctstate NEW -j DROP
sudo iptables -P INPUT DROP

# Persist (survives reboot)
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L INPUT -n --line-numbers     # verify
```

Rollback if you lock yourself out from a *new* session (an existing SSH
session keeps working because of the ESTABLISHED rule):
`sudo ufw disable` or `sudo iptables -P INPUT ACCEPT`.

### 4c. How this interacts with Docker (important)

Docker publishes container ports through its own `nat`/`DOCKER-USER` chains,
which **bypass ufw/INPUT rules** for published ports. That is exactly why
this stack publishes **only** Caddy's 80/443:

* `docker ps` must never show `0.0.0.0:8000` or `0.0.0.0:5432`.
* `app` and `postgres` sit on the `actuator-edge` bridge with `expose` only,
  so there is nothing for an attacker to reach even though ufw "doesn't see"
  Docker traffic.
* If you later need DB access from your laptop, publish it bound to
  loopback only (`127.0.0.1:5432:5432`, commented template in
  `docker-compose.yml`) and reach it through an SSH tunnel:
  `ssh -L 5432:localhost:5432 ubuntu@<vm-ip>`.

---

## 5. Deploy the application

```bash
git clone <your-repo-url> actuator-ai && cd actuator-ai

cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production        # see table below
```

| Key | Required | Notes |
|---|---|---|
| `DOMAIN` | ✅ | FQDN pointed at the VM public IP; also used as the Caddy site address |
| `ACME_EMAIL` | ✅ | Let's Encrypt account email |
| `SECRET_KEY` | ✅ | `openssl rand -hex 32` — app **refuses to boot** in production with the default |
| `CORS_ORIGINS` | ✅ | `https://your.domain,https://www.your.domain` |
| `POSTGRES_PASSWORD` | ✅ | `openssl rand -hex 24` — must match for app and db (both read the same file) |
| `OPENAI_API_KEY` | ✅ | LLM provider token; use with `OPENAI_BASE_URL` and `OPENAI_MODEL` for Cloudflare or another OpenAI-compatible endpoint |
| `DOCKER_PLATFORM` | – | `linux/arm64` (default, native on Ampere A1) |
| `WEB_CONCURRENCY` | – | uvicorn workers, `2` is a good default for 4 OCPU |
| `DATABASE_URL` | – | leave commented to use the bundled Postgres |
| `WS…` block | – | documentation only: WS endpoint is `wss://<DOMAIN>/api/v1/chat/ws` |

```bash
docker compose up -d --build
```

First boot sequence: build image → `postgres` initialises
`backend/db/schema.sql` → `app` creates/seeds 21 business tables →
`app` healthcheck passes → `caddy` starts and requests the certificate.

---

## 6. Verify the deployment

### 6.1 Container status

```bash
docker ps
```

Expected shape (healthy within ~60 s of the first `up`):

```
CONTAINER ID   IMAGE              COMMAND                  PORTS                                     STATUS
xxxx           caddy:2-alpine     "/caddy run --…"         0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp   Up (healthy)
xxxx           actuator-ai:latest "sh -c exec uv run …"    8000/tcp                                   Up (healthy)
xxxx           postgres:16-alpine "docker-entrypoint.s…"   5432/tcp                                   Up (healthy)
```

Three containers, **all `healthy`**, and only `caddy` publishing ports.

```bash
docker compose ps                                  # same view, compose-managed
docker images --format '{{.Repository}}:{{.Tag}} {{.Architecture}}'
#   actuator-ai:latest arm64
docker exec actuator-app uname -m                  # → aarch64
```

### 6.2 Health checks

```bash
# a) Through the proxy (real user path — validates DNS + TLS + routing)
curl -fsS https://<DOMAIN>/health
#   {"status":"ok","database":"ok","project":"Actuator AI",...}
#   (GET /healthz returns the identical payload — use it for external
#    uptime monitors or a cloud load-balancer health probe.)

# b) Direct container-to-container (bypasses Caddy)
docker compose exec app curl -fsS http://localhost:8000/health

# c) Raw health status as Docker sees it
docker inspect --format '{{.State.Health.Status}}' actuator-app
docker inspect --format '{{json .State.Health}}' actuator-app

# d) HTTP→HTTPS redirect
curl -sI http://<DOMAIN>/health | head -1          # HTTP/1.1 308 Permanent Redirect

# e) Database
docker compose exec postgres pg_isready -U actuator -d actuator_ai
#   /var/run/postgresql:5432 - accept

# f) Caddy admin API (this is also its container healthcheck)
docker compose exec caddy wget -qO- http://localhost:2019/config/ | head -c 120

# g) TLS certificate (issuer should be Let's Encrypt, not self-signed)
echo | openssl s_client -connect <DOMAIN>:443 -servername <DOMAIN> 2>/dev/null \
  | openssl x509 -noout -issuer -dates
```

> `/health` returns `"status":"ok"` only when the DB round-trip succeeds;
> a `degraded`/`unhealthy` container therefore always points at the
> database or migrations — check `docker compose logs postgres app`.

### 6.3 WebSocket (streaming chat)

```bash
curl -i -N --max-time 5 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  "https://<DOMAIN>/api/v1/chat/ws"
```

Expect `HTTP/1.1 101 Switching Protocols` with
`Sec-Websocket-Accept: …`. curl itself then exits with code `28`
timeout — that is expected: the server keeps the socket open waiting for
the first frame, and `--max-time 5` cuts it. The line that matters is the
`101`. A `403`/`400` from Caddy means the `@ws` handle
block or the upgrade headers are broken; a `308` means you used `http://`.

In the browser DevTools → Network → WS tab the socket must show
`wss://<DOMAIN>/api/v1/chat/ws` with status `101`.

### 6.4 Logs & log rotation

```bash
docker compose logs -f --tail=100 app
docker inspect --format '{{json .HostConfig.LogConfig}}' actuator-app
#   {"Type":"json-file","Config":{"max-size":"10m","max-file":"5"}}
```

Each container keeps at most 5 × 10 MB of JSON logs (enforced by Docker's
`json-file` driver, declared in `docker-compose.yml`).

---

## 7. Day-2 operations

```bash
# Update after git pull
docker compose up -d --build

# Backup the database
docker compose exec -T postgres pg_dump -U actuator actuator_ai \
  | gzip > "backup-$(date +%F-%H%M).sql.gz"

# Restore
gunzip -c backup-YYYY-MM-DD.sql.gz | \
  docker compose exec -T postgres psql -U actuator -d actuator_ai

# Backup TLS certs + config (caddy_data volume)
docker run --rm -v actuator-ai_caddy_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/caddy-data.tgz -C /data .

# Disk housekeeping (never touches named volumes unless --volumes is added)
docker image prune -af

# Reboot resilience
sudo systemctl enable docker    # containers have restart: unless-stopped
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `actuator-app` restarting, log shows `SECRET_KEY must be set` | default secret in production | set `SECRET_KEY` in `.env.production`, `docker compose up -d` |
| `compose fails: env file .env.production not found` | template not copied | `cp .env.production.example .env.production` |
| `caddy` unhealthy, log `HTTP 403 ... too many requests` | Let's Encrypt rate limit | wait, or test with `staging` ACME first; confirm DNS A record |
| `unable to get local issuer certificate` | self-signed cert | `DOMAIN` must be a real DNS name, not an IP (or use Option B in `Caddyfile`) |
| `502 Bad Gateway` | app still starting or crashed | `docker compose logs app`, check `/health` |
| `Health: starting` forever | first boot seeding takes long | watch `docker compose logs -f app`; lower `WEB_CONCURRENCY` if OOM |
| Build fails with `exec format error` | building for the wrong arch | unset `DOCKER_PLATFORM`, or on non-arm64 hosts install qemu-binfmt |
| WebSocket connects then closes at 60 s | an external proxy buffers/timeouts | confirm traffic goes through this stack's Caddy (`flush_interval -1`, `timeouts` block) |
| OOM kills under load | 24 GB shared, but small shapes | reduce `WEB_CONCURRENCY`, uncomment `mem_limit` in compose |

---

## 9. What was removed in the migration

* `render.yaml` — deleted (PaaS deploy config).
* `docker-compose.prod.yml` — deleted; everything now lives in the single
  production `docker-compose.yml`.
* No Railway files (`railway.json` / `railway.toml` / `nixpacks.toml`) exist
  or were added.
* Runtime env moved from PaaS dashboards to `.env.production` (gitignored),
  with `.env.production.example` as the tracked template.
