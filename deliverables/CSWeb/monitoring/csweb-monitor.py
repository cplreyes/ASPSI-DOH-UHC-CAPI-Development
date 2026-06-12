#!/usr/bin/env python3
"""CSWeb breakout/cron health monitor — aspsi-csweb-prod.

Runs from host cron every 15 min. Checks:
  1. stuck breakout jobs   (cspro_jobs.status=1 older than STUCK_MIN)
  2. dead process-cases cron (log not written in DEAD_MIN)
  3. new ERROR lines in the process-cases log and CSWeb app logs
Alerts via Elestio postfix (SMTP 172.17.0.1:25) to MAIL_TO; if
SLACK_WEBHOOK_URL is set in /etc/csweb-monitor.conf it posts there too.
Per-condition alerts are throttled to one per SUPPRESS_H hours.

State: /var/lib/csweb-monitor/   Config: /etc/csweb-monitor.conf
"""
import json, os, smtplib, subprocess, sys, time, urllib.request
from email.message import EmailMessage

CONF = "/etc/csweb-monitor.conf"
STATE_DIR = "/var/lib/csweb-monitor"
PC_LOG = "/var/log/csweb-process-cases.log"
APP_LOG_DIR = "/opt/app/lamp/www/csweb/var/logs"
BREAKOUTS = ["csweb_f1_breakout", "csweb_f3_breakout", "csweb_f4_breakout"]
STUCK_MIN = 20
DEAD_MIN = 20
SUPPRESS_H = 6

def load_conf():
    conf = {"MAIL_TO": "carlpatricklreyes@gmail.com", "SLACK_WEBHOOK_URL": "",
            "MAIL_FROM": "csweb-monitor@csweb.asiansocial.org",
            "SMTP_HOST": "172.17.0.1", "SMTP_PORT": "25"}
    if os.path.exists(CONF):
        for line in open(CONF):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf

def mysql(query):
    pw = ""
    for line in open("/opt/app/.env"):
        if line.startswith("MYSQL_ROOT_PASSWORD"):
            pw = line.split("=", 1)[1].strip()
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql",
         f"-uroot", f"-p{pw}", "--silent", "-e", query],
        cwd="/opt/app", capture_output=True, text=True,
        stdin=subprocess.DEVNULL, timeout=60)
    return r.stdout.strip()

def throttled(key):
    f = os.path.join(STATE_DIR, f"alert-{key}")
    if os.path.exists(f) and time.time() - os.path.getmtime(f) < SUPPRESS_H * 3600:
        return True
    open(f, "w").write(str(time.time()))
    return False

def tail_new_lines(path, key):
    """Lines appended to path since the last run (by byte offset)."""
    if not os.path.exists(path):
        return []
    off_file = os.path.join(STATE_DIR, f"off-{key}")
    size = os.path.getsize(path)
    last = int(open(off_file).read()) if os.path.exists(off_file) else 0
    if size < last:          # rotated
        last = 0
    with open(path, errors="replace") as fh:
        fh.seek(last)
        new = fh.read()
    open(off_file, "w").write(str(size))
    return new.splitlines()

def check_stuck_jobs():
    probs = []
    for db in BREAKOUTS:
        out = mysql(
            f"SELECT COUNT(*) FROM {db}.cspro_jobs WHERE status=1 "
            f"AND modified_time < NOW() - INTERVAL {STUCK_MIN} MINUTE;")
        if out and out != "0":
            probs.append(f"{db}: {out} breakout job(s) stuck >={STUCK_MIN}min "
                         f"(status=1) — check {APP_LOG_DIR}/ui.dev.log")
    return probs

def check_cron_alive():
    if not os.path.exists(PC_LOG):
        return [f"{PC_LOG} missing — process-cases cron never ran?"]
    age = (time.time() - os.path.getmtime(PC_LOG)) / 60
    if age > DEAD_MIN:
        return [f"process-cases cron silent for {age:.0f} min "
                f"(expected every 5) — check 'crontab -l' and docker"]
    return []

def check_new_errors():
    probs = []
    err = [l for l in tail_new_lines(PC_LOG, "pclog")
           if "error" in l.lower() or "exception" in l.lower()]
    if err:
        probs.append(f"process-cases log: {len(err)} new error line(s); first: "
                     + err[0][:200])
    for name in sorted(os.listdir(APP_LOG_DIR)):
        if not name.endswith(".log"):
            continue
        path = os.path.join(APP_LOG_DIR, name)
        new = [l for l in tail_new_lines(path, f"app-{name}")
               if ".ERROR" in l or ".CRITICAL" in l]
        if new:
            probs.append(f"{name}: {len(new)} new ERROR/CRITICAL line(s); first: "
                         + new[0][:200])
    return probs

def alert(conf, problems):
    body = ("CSWeb monitor on aspsi-csweb-prod found:\n\n- "
            + "\n- ".join(problems)
            + "\n\nHost: csweb.asiansocial.org (207.148.65.115)\n"
              "Runbook: deliverables/CSWeb/CSWeb-Sync-Report-and-Case-Breakout-Setup.md\n")
    msg = EmailMessage()
    msg["Subject"] = f"[CSWeb ALERT] {len(problems)} problem(s) on aspsi-csweb-prod"
    msg["From"] = conf["MAIL_FROM"]
    msg["To"] = conf["MAIL_TO"]
    msg.set_content(body)
    try:
        with smtplib.SMTP(conf["SMTP_HOST"], int(conf["SMTP_PORT"]), timeout=30) as s:
            s.send_message(msg)
        print("alert mailed to", conf["MAIL_TO"])
    except Exception as e:
        print("MAIL FAILED:", e, file=sys.stderr)
    if conf.get("SLACK_WEBHOOK_URL"):
        try:
            req = urllib.request.Request(
                conf["SLACK_WEBHOOK_URL"],
                data=json.dumps({"text": ":rotating_light: " + body}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=30)
            print("alert posted to Slack")
        except Exception as e:
            print("SLACK FAILED:", e, file=sys.stderr)

def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    conf = load_conf()
    if "--test" in sys.argv:
        alert(conf, ["TEST ALERT — csweb-monitor installed and mail path works. "
                     "No action needed."])
        return
    problems = []
    for key, probs in (("stuck", check_stuck_jobs()),
                       ("cron", check_cron_alive()),
                       ("errors", check_new_errors())):
        fresh = [p for p in probs if not throttled(f"{key}-{hash(p) & 0xffff:x}")]
        problems += fresh
        for p in probs:
            print("found:", p)
    if problems:
        alert(conf, problems)
    else:
        print("ok")

if __name__ == "__main__":
    main()
