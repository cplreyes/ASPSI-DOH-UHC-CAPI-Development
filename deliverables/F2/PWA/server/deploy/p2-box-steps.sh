#!/usr/bin/env bash
# =============================================================================
# f2-api P2 — stand up dark on the Elestio csweb box (root@207.148.65.115).
# Run from Windows Git Bash AFTER shipping /opt/f2-api (step 0 in the README):
#
#   ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 'bash -s' \
#     < deliverables/F2/PWA/server/deploy/p2-box-steps.sh
#
# Idempotent — safe to re-run; every step guards against double-apply.
# Secrets: BOTH values (DB password + JWT signing key) are generated ON the box
# and written straight into /opt/app/.env — they never transit chat or the dev
# machine. Fresh JWT key note: the Worker's key can't be read back out of
# Cloudflare (secrets are write-only), so hcw mints its own. Old Worker tokens
# won't verify on hcw — irrelevant pre-P4, and P5 re-enrolls every UAT device.
# A never-transited key also has no P6 rotation debt.
# =============================================================================
set -euo pipefail

echo "== [1/7] DDL: f2-api tables into csweb_f2 (idempotent) =="
docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot csweb_f2' \
  < /opt/f2-api/ddl/f2_api_tables.sql
docker exec lamp-mysql8 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -N -e "SHOW TABLES" csweb_f2'

echo "== [2/7] least-priv MySQL user f2api (password minted here, box-only) =="
if grep -q '^F2_DB_PASSWORD=' /opt/app/.env; then
  echo "   F2_DB_PASSWORD already in /opt/app/.env — skipping"
else
  PW=$(openssl rand -hex 24)
  docker exec -i lamp-mysql8 sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot' <<SQL
CREATE USER IF NOT EXISTS 'f2api'@'%' IDENTIFIED BY '$PW';
GRANT SELECT, INSERT, UPDATE, DELETE ON csweb_f2.* TO 'f2api'@'%';
FLUSH PRIVILEGES;
SQL
  echo "F2_DB_PASSWORD=$PW" >> /opt/app/.env
  echo "   created f2api + stored password in /opt/app/.env"
fi

echo "== [3/7] JWT signing key (minted here, box-only — see header note) =="
if grep -q '^F2_JWT_SIGNING_KEY=' /opt/app/.env; then
  echo "   F2_JWT_SIGNING_KEY already in /opt/app/.env — skipping"
else
  echo "F2_JWT_SIGNING_KEY=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')" >> /opt/app/.env
  echo "   minted + stored in /opt/app/.env"
fi

echo "== [4/7] compose: merge the f2-api service into /opt/app/docker-compose.yml =="
if grep -q '^  f2-api:' /opt/app/docker-compose.yml; then
  echo "   f2-api service already present — skipping"
else
  cp /opt/app/docker-compose.yml "/opt/app/docker-compose.yml.bak-$(date +%Y%m%d-%H%M%S)"
  cat >> /opt/app/docker-compose.yml <<'YAML'
  f2-api:
    build: /opt/f2-api
    container_name: f2-api
    restart: unless-stopped
    mem_limit: 256m
    security_opt: ["no-new-privileges:true"]
    labels:
      - "com.centurylinklabs.watchtower.enable=false"   # locally built, not pullable
    ports:
      - "127.0.0.1:8787:8787"   # loopback only; elestio-nginx runs on the host net
    environment:
      - JWT_SIGNING_KEY=${F2_JWT_SIGNING_KEY}
      - F2_DB_HOST=database
      - F2_DB_USER=f2api
      - F2_DB_PASSWORD=${F2_DB_PASSWORD}
      - F2_DB_NAME=csweb_f2
      - F2_FILES_DIR=/opt/app/f2-files
      - PWA_ORIGIN=https://uhc-hcw.asiansocial.org
    volumes:
      - /opt/app/f2-files:/opt/app/f2-files
    depends_on:
      - database
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8787/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
YAML
  echo "   appended (backup kept alongside)"
fi

echo "== [5/7] admin-files dir (R2 replacement) =="
mkdir -p /opt/app/f2-files
chown 1000:1000 /opt/app/f2-files   # node user in node:22-alpine

echo "== [6/7] build + start f2-api =="
cd /opt/app
docker compose build f2-api
docker compose up -d f2-api
sleep 3
docker logs f2-api --tail 5
curl -sf http://127.0.0.1:8787/api/health && echo || { echo "HEALTH CHECK FAILED"; exit 1; }

echo "== [7/7] nginx: allow-list the domain + vhost + recreate (csweb blips ~5s) =="
if grep -q 'uhc-hcw.asiansocial.org' /opt/elestio/nginx/.env; then
  echo "   ALLOWED_DOMAINS already includes hcw — skipping"
else
  sed -i.bak 's/^ALLOWED_DOMAINS=.*/&|uhc-hcw.asiansocial.org/' /opt/elestio/nginx/.env
fi
cat > /opt/elestio/nginx/conf.d/uhc-hcw.asiansocial.org.conf <<'CONF'
server {
  listen 443 ssl;
  http2 on;
include resty-server-https.conf;
server_name uhc-hcw.asiansocial.org;

  include /usr/local/openresty/nginx/conf/error-pages.conf;

  # API routes -> f2-api on loopback (nginx runs with network_mode: host).
  # /admin/api/ is listed explicitly: at P3 the fallback below becomes the SPA
  # and would otherwise swallow the Admin Portal's calls (P1b review catch).
  location ~ ^/(exec|verify-token|api/|admin/api/) {
    client_max_body_size 100m;
    proxy_http_version 1.1;
    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
    proxy_connect_timeout 180s;
    proxy_pass http://127.0.0.1:8787;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
  }

  # P2 (dark): everything else also hits the API (JSON 404s are fine).
  # P3 swaps this block for the static PWA root + SPA fallback (#528).
  location / {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8787;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
  }
}
CONF
cd /opt/elestio/nginx
docker compose up -d   # recreates elestio-nginx so the new ALLOWED_DOMAINS applies

echo "== DONE. After DNS (hcw -> 207.148.65.115) propagates, the P2 gate is: =="
echo "   curl https://uhc-hcw.asiansocial.org/api/health   (first hit also triggers cert issuance)"
