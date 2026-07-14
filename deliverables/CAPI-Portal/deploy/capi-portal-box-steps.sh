#!/usr/bin/env bash
# =============================================================================
# CAPI Portal — stand up capi.asiansocial.org dark on the Elestio csweb box.
# Phase P of deliverables/CAPI-Portal/domain-restructure-plan.md.
# Run AFTER shipping the site (step 0):
#
#   cd deliverables/CAPI-Portal && tar czf - -C site . \
#     | ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 \
#       'mkdir -p /opt/app/capi-www && rm -rf /opt/app/capi-www/* && tar xzf - -C /opt/app/capi-www && ls /opt/app/capi-www'
#
#   ssh -i /c/Users/analy/.ssh/aspsi-csweb root@207.148.65.115 'bash -s' \
#     < deliverables/CAPI-Portal/deploy/capi-portal-box-steps.sh
#
# Idempotent. Same patterns as f2-api: loopback-published container, auto-SSL
# vhost, --no-deps discipline (no depends_on at all here — static only).
# =============================================================================
set -euo pipefail

echo "== [1/4] compose: capi-www static server (nginx:alpine, loopback 8788) =="
if grep -q '^  capi-www:' /opt/app/docker-compose.yml; then
  echo "   capi-www service already present — skipping"
else
  cp /opt/app/docker-compose.yml "/opt/app/docker-compose.yml.bak-$(date +%Y%m%d-%H%M%S)"
  cat >> /opt/app/docker-compose.yml <<'YAML'
  capi-www:
    image: nginx:alpine
    container_name: capi-www
    restart: unless-stopped
    mem_limit: 64m
    security_opt: ["no-new-privileges:true"]
    ports:
      - "127.0.0.1:8788:80"   # loopback only; elestio-nginx (host net) proxies in
    volumes:
      - /opt/app/capi-www:/usr/share/nginx/html:ro
YAML
  echo "   appended (backup kept alongside)"
fi

echo "== [2/4] start capi-www (no deps to drag in) =="
cd /opt/app
docker compose up -d --no-deps capi-www
sleep 2
curl -sf http://127.0.0.1:8788/ | head -c 80 && echo
curl -sf http://127.0.0.1:8788/uhc/ | grep -q "UHC Survey 2026" && echo "uhc page OK"
curl -sf http://127.0.0.1:8788/docs/ | grep -q "Documentation" && echo "docs page OK"

echo "== [3/4] nginx: allow-list capi + vhost =="
if grep -q 'capi.asiansocial.org' /opt/elestio/nginx/.env; then
  echo "   ALLOWED_DOMAINS already includes capi — skipping"
else
  sed -i.bak2 's/^ALLOWED_DOMAINS=.*/&|capi.asiansocial.org/' /opt/elestio/nginx/.env
fi
cat > /opt/elestio/nginx/conf.d/capi.asiansocial.org.conf <<'CONF'
server {
  listen 443 ssl;
  http2 on;
include resty-server-https.conf;
server_name capi.asiansocial.org;

  include /usr/local/openresty/nginx/conf/error-pages.conf;

  location / {
    proxy_http_version 1.1;
    proxy_pass http://127.0.0.1:8788;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
CONF

echo "== [4/4] nginx recreate (picks up ALLOWED_DOMAINS; csweb blips ~5s) =="
cd /opt/elestio/nginx
docker compose up -d
sleep 2
curl -sk --resolve capi.asiansocial.org:443:127.0.0.1 https://capi.asiansocial.org/ | head -c 80 && echo " <- vhost routes"
echo "== DONE. Public gate after DNS: curl https://capi.asiansocial.org/ =="
