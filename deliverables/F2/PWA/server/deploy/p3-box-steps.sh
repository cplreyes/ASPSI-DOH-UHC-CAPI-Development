#!/usr/bin/env bash
# =============================================================================
# f2-api P3 — app re-point + host RENAME hcw -> uhc-hcw (decided 2026-07-08,
# Option C: capi portal now, csweb untouched; F2 host = uhc-hcw.asiansocial.org).
# Run AFTER shipping both artifacts (step 0 in the README):
#   server dist (with static serving) -> /opt/f2-api/dist
#   app build (VITE_F2_PROXY_URL=https://uhc-hcw.asiansocial.org) -> /opt/app/f2-www
#
#   ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 'bash -s' \
#     < deliverables/F2/PWA/server/deploy/p3-box-steps.sh
#
# Idempotent. P2 lesson applied: --no-deps so lamp-mysql8 is never recreated.
# =============================================================================
set -euo pipefail

echo "== [1/5] rename box state: hcw -> uhc-hcw (compose origin, allow-list, vhost) =="
if grep -q 'PWA_ORIGIN=https://hcw.asiansocial.org' /opt/app/docker-compose.yml; then
  sed -i 's|PWA_ORIGIN=https://hcw.asiansocial.org|PWA_ORIGIN=https://uhc-hcw.asiansocial.org|' /opt/app/docker-compose.yml
  echo "   compose PWA_ORIGIN renamed"
fi
if grep -q '|hcw.asiansocial.org' /opt/elestio/nginx/.env; then
  sed -i 's/|hcw.asiansocial.org/|uhc-hcw.asiansocial.org/' /opt/elestio/nginx/.env
  echo "   ALLOWED_DOMAINS renamed"
fi
rm -f /opt/elestio/nginx/conf.d/hcw.asiansocial.org.conf
cat > /opt/elestio/nginx/conf.d/uhc-hcw.asiansocial.org.conf <<'CONF'
server {
  listen 443 ssl;
  http2 on;
include resty-server-https.conf;
server_name uhc-hcw.asiansocial.org;

  include /usr/local/openresty/nginx/conf/error-pages.conf;

  # API routes -> f2-api on loopback (nginx runs with network_mode: host).
  # /admin/api/ listed explicitly: the SPA fallback below must never swallow
  # the Admin Portal's calls (P1b review catch).
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

  # P3: f2-api serves the PWA static build + #528 SPA fallback itself.
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

echo "== [2/5] compose: F2_WWW_DIR env + ro volume on the f2-api service =="
if grep -q 'F2_WWW_DIR' /opt/app/docker-compose.yml; then
  echo "   already wired — skipping"
else
  cp /opt/app/docker-compose.yml "/opt/app/docker-compose.yml.bak-$(date +%Y%m%d-%H%M%S)"
  sed -i 's|^      - F2_FILES_DIR=/opt/app/f2-files$|      - F2_FILES_DIR=/opt/app/f2-files\n      - F2_WWW_DIR=/opt/app/f2-www|' /opt/app/docker-compose.yml
  sed -i 's|^      - /opt/app/f2-files:/opt/app/f2-files$|      - /opt/app/f2-files:/opt/app/f2-files\n      - /opt/app/f2-www:/opt/app/f2-www:ro|' /opt/app/docker-compose.yml
  grep -q 'F2_WWW_DIR' /opt/app/docker-compose.yml || { echo "sed failed to wire F2_WWW_DIR"; exit 1; }
fi

echo "== [3/5] rebuild + restart f2-api ONLY (--no-deps: MySQL untouched) =="
cd /opt/app
docker compose build f2-api
docker compose up -d --no-deps f2-api
sleep 3
docker logs f2-api --tail 3

echo "== [4/5] nginx recreate (picks up renamed ALLOWED_DOMAINS + vhost; csweb blips ~5s) =="
cd /opt/elestio/nginx
docker compose up -d

echo "== [5/5] smoke: API json + SPA index + #528 fallback + vhost-by-SNI =="
curl -sf http://127.0.0.1:8787/api/health && echo
curl -sf http://127.0.0.1:8787/ | head -c 80 && echo
curl -sf "http://127.0.0.1:8787/enroll?token=smoke" | grep -q '<html' && echo "SPA fallback OK"
curl -s  http://127.0.0.1:8787/api/nope | grep -q E_NOT_FOUND && echo "API 404 stays JSON OK"
sleep 2
curl -sk --resolve uhc-hcw.asiansocial.org:443:127.0.0.1 https://uhc-hcw.asiansocial.org/api/health && echo " <- vhost routes (self-signed until DNS + first public hit)"
echo "== DONE. Public gate after DNS: curl https://uhc-hcw.asiansocial.org/api/health =="
