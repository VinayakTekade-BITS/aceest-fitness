#!/usr/bin/env python3
"""Generate the Assignment 2 report from the live state of the project.

Writes three files next to this script:
  REPORT.md            the 2-3 page report: architecture, challenges, automation outcomes
  SONARQUBE_REPORT.md  quality gate, metrics, issues and analysis history from SonarQube
  EVIDENCE.md          the screenshots in screenshots/, grouped by runbook step

Run it on the VM, from anywhere inside the repository:
  python3 docs/assignment2/generate_report.py

Environment variables (none of them is written to the report):
  SONAR_TOKEN                   required for the SonarQube sections
  SONAR_HOST_URL                default http://localhost:9000
  SONAR_PROJECT                 default aceest-fitness
  DOCKERHUB_REPO                default: the value in the Jenkinsfile
  JENKINS_USER, JENKINS_TOKEN   optional, adds the Jenkins build history
  JENKINS_URL, JENKINS_JOB      default http://localhost:8080 and aceest-fitness
  PUBLIC_HOST                   host name or IP for the URLs, default: first IP of this machine
"""
import base64
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(
    subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE, capture_output=True,
                   text=True, check=True).stdout.strip()
)
SCREENSHOTS = HERE / "screenshots"
NAMESPACE = "aceest"

SONAR_URL = os.environ.get("SONAR_HOST_URL", "http://localhost:9000").rstrip("/")
SONAR_TOKEN = os.environ.get("SONAR_TOKEN", "")
SONAR_PROJECT = os.environ.get("SONAR_PROJECT", "aceest-fitness")
JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080").rstrip("/")
JENKINS_JOB = os.environ.get("JENKINS_JOB", "aceest-fitness")

STRATEGIES = [
    # name, service, node port, how it works, rollback
    ("Rolling update", "aceest-rolling", 30081,
     "3 replicas replaced one pod at a time (maxSurge 1, maxUnavailable 0, readiness probe)",
     "automatic `kubectl rollout undo`; the failed revision is deleted"),
    ("Blue-green", "aceest-bluegreen", 30082,
     "new version on the idle color, tested via the preview port 30086, then the Service "
     "selector switches all traffic at once",
     "traffic is never switched to a failing color; manual: `blue-green.sh rollback`"),
    ("Canary", "aceest-canary", 30083,
     "1 canary pod next to 3 stable pods (~25 % of requests); 60 test requests must give "
     "0 errors, then the stable track is promoted",
     "canary scaled to 0, stable track untouched"),
    ("A/B testing", "aceest-ab-router", 30084,
     "nginx router: X-Variant header, else ab_variant cookie, else 50/50; A = previous "
     "stable release, B = new release",
     "variant B rolled back to its previous image"),
    ("Shadow", "aceest-shadow-router", 30085,
     "nginx mirrors every request to the shadow track (own database); users only get the "
     "live answer; the shadow must answer all copies without a 5xx",
     "shadow scaled to 0; users never saw it"),
]

RATING = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}


def log(message):
    print(">> " + message, file=sys.stderr)


def run(*cmd, cwd=ROOT, timeout=600):
    """stdout of a command, or None if it fails or is not installed."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def get_json(url, user=None, password=None, timeout=15):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    if user is not None:
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        request.add_header("Authorization", "Basic " + credentials)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (OSError, ValueError) as err:
        log(f"   could not read {url.split('?')[0]}: {err}")
        return None


def sonar(path, **params):
    if not SONAR_TOKEN:
        return None
    return get_json(f"{SONAR_URL}{path}?{urllib.parse.urlencode(params)}", SONAR_TOKEN, "")


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def icon(ok):
    return "✅" if ok else "❌"


# ------------------------------------------------------------------ data collection
def git_info():
    log("Git history")
    remote = (run("git", "remote", "get-url", "origin") or "").strip()
    path = re.sub(r"^(git@github\.com:|https://github\.com/)", "", remote).removesuffix(".git")
    tags = []
    # date of the tagged commit (not of the tag), so back-filled tags show the real release date
    out = run("git", "for-each-ref", "--sort=version:refname",
              "--format=%(refname:short)|%(if)%(*objectname)%(then)%(*committerdate:short)"
              "%(else)%(committerdate:short)%(end)|%(contents:subject)", "refs/tags")
    for line in (out or "").splitlines():
        name, day, subject = line.split("|", 2)
        tags.append((name, day, subject))
    return {
        "url": f"https://github.com/{path}" if path else remote,
        "head": (run("git", "rev-parse", "--short", "HEAD") or "").strip(),
        "branch": (run("git", "rev-parse", "--abbrev-ref", "HEAD") or "").strip(),
        "author": (run("git", "config", "user.name") or "").strip(),
        "tags": tags,
    }


def pytest_results():
    log("Unit tests")
    python = ROOT / ".venv" / "bin" / "python"
    try:
        found = python.exists()
    except OSError:          # e.g. a virtualenv created on another operating system
        found = False
    if not found:
        return None
    out = run(str(python), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--cov=aceest",
              "--cov=app", "--cov=ACEest_Fitness", "--cov-report=term")
    if out is None:
        return {"summary": "pytest failed - run it by hand to see why", "coverage": "n/a"}
    summary = next((line.strip("= ") for line in reversed(out.splitlines())
                    if " passed" in line or " failed" in line), "")
    coverage = next((line.split()[-1] for line in out.splitlines() if line.startswith("TOTAL")),
                    "n/a")
    return {"summary": summary, "coverage": coverage}


def sonar_data():
    log("SonarQube")
    if not SONAR_TOKEN:
        log("   SONAR_TOKEN is not set - SonarQube sections are skipped")
        return None
    metrics = ("alert_status,bugs,reliability_rating,vulnerabilities,security_rating,"
               "security_hotspots,security_review_rating,code_smells,sqale_rating,coverage,"
               "duplicated_lines_density,ncloc,tests,accepted_issues")
    measures = sonar("/api/measures/component", component=SONAR_PROJECT, metricKeys=metrics)
    if measures is None:
        return None
    gate = sonar("/api/qualitygates/project_status", projectKey=SONAR_PROJECT) or {}
    gate_name = (sonar("/api/qualitygates/get_by_project", project=SONAR_PROJECT) or {}).get(
        "qualityGate", {}).get("name", "")
    open_issues = sonar("/api/issues/search", components=SONAR_PROJECT,
                        issueStatuses="OPEN,CONFIRMED", ps=100) or {}
    accepted = sonar("/api/issues/search", components=SONAR_PROJECT,
                     issueStatuses="ACCEPTED,FALSE_POSITIVE", additionalFields="comments",
                     ps=100) or {}
    hotspots = sonar("/api/hotspots/search", project=SONAR_PROJECT, ps=100) or {}
    analyses = sonar("/api/project_analyses/search", project=SONAR_PROJECT, ps=30) or {}
    history = sonar("/api/measures/search_history", component=SONAR_PROJECT,
                    metrics="alert_status,coverage", ps=500) or {}
    return {
        "measures": {m["metric"]: m.get("value", "") for m in
                     measures["component"].get("measures", [])},
        "gate": gate.get("projectStatus", {}),
        "gate_name": gate_name,
        "open": open_issues.get("issues", []),
        "accepted": accepted.get("issues", []),
        "hotspots": hotspots.get("hotspots", []),
        "analyses": analyses.get("analyses", []),
        "history": {m["metric"]: {h["date"]: h.get("value") for h in m.get("history", [])}
                    for m in history.get("measures", [])},
    }


def dockerhub_tags(repo):
    log("Docker Hub")
    if not repo or "<" in repo:
        return None
    url, tags = f"https://hub.docker.com/v2/repositories/{repo}/tags?page_size=100", []
    for _ in range(5):                      # at most 500 tags
        data = get_json(url)
        if data is None:
            return tags or None
        tags += [(t["name"], (t.get("last_updated") or "")[:10], t.get("full_size") or 0)
                 for t in data.get("results", [])]
        url = data.get("next")
        if not url:
            break
    return tags


def jenkins_builds():
    log("Jenkins")
    user, token = os.environ.get("JENKINS_USER"), os.environ.get("JENKINS_TOKEN")
    if not user or not token:
        log("   JENKINS_USER / JENKINS_TOKEN not set - build history is skipped")
        return None
    tree = "builds[number,result,timestamp,duration,displayName]{0,20}"
    data = get_json(f"{JENKINS_URL}/job/{JENKINS_JOB}/api/json?tree={urllib.parse.quote(tree)}",
                    user, token)
    return None if data is None else data.get("builds", [])


def cluster_state():
    log("Kubernetes")
    out = run("kubectl", "-n", NAMESPACE, "get", "deployments,services,configmaps", "-o", "json",
              timeout=60)
    if out is None:
        return None
    items = json.loads(out).get("items", [])
    state = {"deployments": [], "services": {}, "stable": ""}
    for item in items:
        kind, name = item["kind"], item["metadata"]["name"]
        if kind == "Deployment":
            state["deployments"].append((
                name,
                item["metadata"].get("labels", {}).get("strategy", ""),
                item["spec"]["template"]["spec"]["containers"][0]["image"],
                f'{item["status"].get("readyReplicas", 0)}/{item["spec"].get("replicas", 0)}',
            ))
        elif kind == "Service":
            state["services"][name] = item["spec"].get("selector", {})
        elif kind == "ConfigMap" and name == "aceest-release":
            state["stable"] = item.get("data", {}).get("image", "")
    return state


# ------------------------------------------------------------------ report writers
def write_sonar_report(sq, host, generated):
    lines = [f"# SonarQube report — `{SONAR_PROJECT}`", ""]
    if sq is None:
        lines.append("_SonarQube data not available: set SONAR_TOKEN and re-run the generator._")
        return "\n".join(lines) + "\n"
    m, gate = sq["measures"], sq["gate"]
    passed = gate.get("status") == "OK"
    lines += [
        table(["", ""], [
            ["Dashboard", f"<http://{host}:9000/dashboard?id={SONAR_PROJECT}>"],
            ["Quality gate", f"{sq['gate_name'] or 'default'}: "
                             f"{icon(passed)} **{'Passed' if passed else gate.get('status')}**"],
            ["Generated", generated],
        ]),
        "",
        "## Quality gate conditions (new code)",
        "",
    ]
    conditions = gate.get("conditions", [])
    if conditions:
        lines.append(table(["Metric", "Actual", "Fails if", "Status"], [
            [c["metricKey"], c.get("actualValue", ""),
             f'{"<" if c["comparator"] == "LT" else ">"} {c["errorThreshold"]}',
             icon(c["status"] == "OK")] for c in conditions]))
    else:
        lines.append("_No conditions evaluated yet (first analysis: there is no new code)._")
    lines += [
        "",
        "## Overall code",
        "",
        table(["Measure", "Value", "Rating"], [
            ["Bugs", m.get("bugs", ""), RATING.get(m.get("reliability_rating"), "")],
            ["Vulnerabilities", m.get("vulnerabilities", ""),
             RATING.get(m.get("security_rating"), "")],
            ["Security hotspots", m.get("security_hotspots", ""),
             RATING.get(m.get("security_review_rating"), "")],
            ["Code smells", m.get("code_smells", ""), RATING.get(m.get("sqale_rating"), "")],
            ["Coverage", f'{m.get("coverage", "")} %', ""],
            ["Duplicated lines", f'{m.get("duplicated_lines_density", "")} %', ""],
            ["Lines of code", m.get("ncloc", ""), ""],
            ["Unit tests", m.get("tests", ""), ""],
            ["Accepted issues", m.get("accepted_issues", "0"), ""],
        ]),
        "",
        "## Open issues",
        "",
    ]
    if sq["open"]:
        lines.append(table(["Severity", "Rule", "File:line", "Message"], [
            [i.get("severity", ""), i["rule"],
             f'`{i["component"].split(":", 1)[-1]}:{i.get("line", "")}`', i["message"]]
            for i in sq["open"]]))
    else:
        lines.append("None.")
    lines += ["", "## Reviewed issues (accepted or false positive)", ""]
    if sq["accepted"]:
        lines.append(table(["Rule", "File:line", "Message", "Decision", "Justification"], [
            [i["rule"], f'`{i["component"].split(":", 1)[-1]}:{i.get("line", "")}`',
             i["message"], i.get("issueStatus", i.get("resolution", "")),
             " ".join(c.get("markdown", "") for c in i.get("comments", []))]
            for i in sq["accepted"]]))
    else:
        lines.append("None.")
    lines += ["", "## Security hotspots", ""]
    if sq["hotspots"]:
        lines.append(table(["Status", "Rule", "File:line", "Message"], [
            [h.get("status", ""), h.get("ruleKey", ""),
             f'`{h["component"].split(":", 1)[-1]}:{h.get("line", "")}`', h["message"]]
            for h in sq["hotspots"]]))
    else:
        lines.append("None.")
    lines += ["", "## Analysis history", "",
              "One analysis per Jenkins build of `main`; the version is the VERSION file.", ""]
    gate_history = sq["history"].get("alert_status", {})
    coverage_history = sq["history"].get("coverage", {})
    rows = []
    for analysis in sq["analyses"]:
        date = analysis["date"]
        status = gate_history.get(date)
        rows.append([date[:16].replace("T", " "), analysis.get("projectVersion", ""),
                     {"OK": "✅ Passed", "ERROR": "❌ Failed"}.get(status, status or ""),
                     coverage_history.get(date, "")])
    lines.append(table(["Analysis (UTC)", "Version", "Quality gate", "Coverage %"], rows)
                 if rows else "No analyses found.")
    return "\n".join(lines) + "\n"


def write_report(info, tests, sq, tags, builds, host, dockerhub_repo, generated):
    stages = re.findall(r"stage\('([^']+)'\)", (ROOT / "Jenkinsfile").read_text(encoding="utf-8"))
    challenges = HERE / "challenges.md"
    m = (sq or {}).get("measures", {})
    gate_ok = sq is not None and sq["gate"].get("status") == "OK"
    out = [
        "# ACEest Fitness & Gym — Assignment 2: CI/CD with Jenkins, SonarQube, Docker Hub "
        "and Kubernetes",
        "",
        table(["", ""], [
            ["Author", info["author"]],
            ["Repository", f"<{info['url']}>"],
            ["Docker Hub", f"<https://hub.docker.com/r/{dockerhub_repo}/tags>"],
            ["Commit", f"`{info['head']}` on `{info['branch']}`"],
            ["Generated", f"{generated} by `docs/assignment2/generate_report.py`"],
        ]),
        "",
        "## 1. CI/CD architecture overview",
        "",
        "Every change goes through a branch and a pull request (GitHub Actions checks it). "
        "Jenkins polls `main` every 5 minutes and runs the whole pipeline: lint, unit tests, "
        "SonarQube quality gate, Docker image, tests inside the container, push to Docker Hub, "
        "and deployment to Minikube with five strategies. Each strategy is its own environment "
        "with its own URL, and all of them run at the same time.",
        "",
        "```text",
        "developer ─► feature branch ─► pull request ─► GitHub Actions (lint, image, tests)",
        "                                   │ merge",
        "                                   ▼",
        "            Jenkins (polls main) ─► Lint ─► Unit Tests ─► SonarQube quality gate",
        "              ─► Docker Build ─► Test in Container ─► Push to Docker Hub ─► Archive",
        "              ─► Shadow ─► Canary ─► Rolling ─► Blue-Green ─► A/B ─► Mark Stable",
        "                                   │ kubectl",
        "                                   ▼",
        "            Minikube, namespace aceest: one Service (NodePort) per strategy",
        "```",
        "",
        table(["Concern", "Tool", "Where"], [
            ["Version control", "Git, GitHub: branches, pull requests, tags `vX.Y.Z`",
             "`git tag`, Releases"],
            ["Build server", "Jenkins Pipeline, polls GitHub (the VM accepts no webhooks)",
             "`Jenkinsfile`"],
            ["Tests", "Pytest with coverage, also inside the container", "`tests/`"],
            ["Code quality", "SonarQube Community, quality gate enforced by the scanner",
             "`sonar-project.properties`"],
            ["Container", "Docker multi-stage image, non-root, health check", "`Dockerfile`"],
            ["Registry", "Docker Hub, one tag per version and per build", dockerhub_repo],
            ["Deployment", "Kubernetes (Minikube), five strategies", "`k8s/`, `deploy/k8s/`"],
        ]),
        "",
        "Jenkins stages: " + " → ".join(stages) + ".",
        "",
        "### Deployment strategies",
        "",
        table(["Strategy", "URL", "How it works", "Rollback"],
              [[name, f"`http://{host}:{port}`", how, back]
               for name, _, port, how, back in STRATEGIES]),
        "",
        "The deploy stages run from the smallest to the largest blast radius. A failing stage "
        "rolls its own strategy back and stops the build, so later strategies never receive "
        "the bad version. The image of the last fully successful build is recorded as the "
        "stable release (ConfigMap `aceest-release`, Docker Hub tag `stable`).",
        "",
        "## 2. Challenges faced and mitigation strategies",
        "",
        challenges.read_text(encoding="utf-8").strip() if challenges.exists()
        else "_Write this section in `docs/assignment2/challenges.md` and re-run the generator._",
        "",
        "## 3. Key automation outcomes",
        "",
    ]
    bullets = []
    if tests:
        bullets.append(f"**Tests:** {tests['summary']}, coverage {tests['coverage']}; the same "
                       "suite runs inside the test image on every build.")
    if sq:
        bullets.append(
            f"**SonarQube:** quality gate {icon(gate_ok)} {'passed' if gate_ok else 'failed'}; "
            f"{m.get('bugs', '?')} bugs, {m.get('vulnerabilities', '?')} vulnerabilities, "
            f"{m.get('code_smells', '?')} code smells, coverage {m.get('coverage', '?')} %, "
            f"duplication {m.get('duplicated_lines_density', '?')} % "
            "(see [SONARQUBE_REPORT.md](SONARQUBE_REPORT.md)).")
    if builds:
        ok = sum(b.get("result") == "SUCCESS" for b in builds)
        bullets.append(f"**Jenkins:** {ok} of the last {len(builds)} builds succeeded; every "
                       "merge to `main` was built, tested and deployed without manual steps.")
    if tags is not None:
        versions = sorted({t[0] for t in tags if re.fullmatch(r"\d+\.\d+\.\d+", t[0])},
                          key=lambda v: [int(p) for p in v.split(".")])
        bullets.append(f"**Docker Hub:** {len(tags)} tags, including every release "
                       f"({', '.join(versions)}), one tag per Jenkins build, `latest` and "
                       "`stable`.")
    # commit and pull-request statistics are in the Assignment 1 report; here only the releases
    releases = [t for t in info["tags"] if re.fullmatch(r"v\d+\.\d+\.\d+", t[0])]
    bullets.append(f"**Releases:** {len(releases)} version tags, each with its Docker image "
                   "(table below).")
    # claims about demos only appear when the screenshot that proves them exists
    shot_names = " ".join(p.name.lower() for p in SCREENSHOTS.glob("*")) \
        if SCREENSHOTS.is_dir() else ""
    if "downtime" in shot_names:
        bullets.append("**Zero downtime:** a request loop running during a release saw only "
                       "HTTP 200 on every strategy (see [EVIDENCE.md](EVIDENCE.md)).")
    if "rollback" in shot_names:
        bullets.append("**Rollback:** a deliberately broken release was stopped and rolled back "
                       "automatically; switching blue-green back takes one command (see "
                       "[EVIDENCE.md](EVIDENCE.md)).")
    out += [f"- {b}" for b in bullets]
    out += ["", "### Releases", ""]
    out.append(table(["Tag", "Date", "Description"],
                     [[f"`{name}`", day, subject] for name, day, subject in info["tags"]])
               if info["tags"] else "No tags yet.")
    out += ["", "Evidence: [EVIDENCE.md](EVIDENCE.md) (screenshots and cluster state) · "
                "[SONARQUBE_REPORT.md](SONARQUBE_REPORT.md)"]
    return "\n".join(out) + "\n"


STEP_TITLES = {
    0: "Preparation", 1: "Version 2.0.0", 2: "SonarQube", 3: "Docker Hub",
    4: "Kubernetes and rolling update", 5: "Blue-green", 6: "Canary", 7: "Version 2.1.0",
    8: "Shadow", 9: "A/B testing", 10: "Version 2.2.0", 11: "Version 2.2.1 and rollback",
}


def write_evidence(cluster, host, generated):
    lines = ["# Evidence", ""]
    if cluster:
        live = cluster["services"].get("aceest-bluegreen", {}).get("color", "")
        lines += [
            f"## Cluster state at {generated}", "",
            f"Stable release: `{cluster['stable'] or '-'}`. URLs: "
            + ", ".join(f"{name} `http://{host}:{port}`" for name, _, port, _, _ in STRATEGIES)
            + ".", "",
            table(["Deployment", "Strategy", "Image", "Ready"], [
                [f"`{n}`" + (" (live)" if live and n == f"aceest-{live}" else ""), s, f"`{i}`", r]
                for n, s, i, r in sorted(cluster["deployments"])]),
            "",
        ]
    shots = []
    if SCREENSHOTS.is_dir():
        shots = sorted((p for p in SCREENSHOTS.iterdir()
                        if p.suffix.lower() in (".png", ".jpg", ".jpeg")),
                       key=lambda p: natural_key(p.name))
    if not shots:
        lines.append("_No screenshots in `docs/assignment2/screenshots/` yet._")
        return "\n".join(lines) + "\n"
    current = None
    for shot in shots:
        match = re.match(r"^Step(\d+)(\.\d+)?[\s_-]*(.*)$", shot.stem)
        if match:
            number = int(match.group(1))
            group = f"Step {number} — {STEP_TITLES.get(number, '')}".rstrip(" —")
            caption = f"Step {number}{match.group(2) or ''}: {match.group(3)}"
        else:
            group = "Other evidence"
            caption = shot.stem
        if group != current:
            lines += [f"## {group}", ""]
            current = group
        lines += [f"**{caption}**", "",
                  f"![{caption}](screenshots/{urllib.parse.quote(shot.name)})", ""]
    return "\n".join(lines) + "\n"


def natural_key(name):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def main():
    addresses = (run("hostname", "-I") or "").split()
    host = os.environ.get("PUBLIC_HOST") or (addresses[0] if addresses else "localhost")
    jenkinsfile = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
    match = re.search(r"DOCKERHUB_REPO\s*=\s*'([^']+)'", jenkinsfile)
    dockerhub_repo = os.environ.get("DOCKERHUB_REPO") or (match.group(1) if match else "")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    info = git_info()
    tests = pytest_results()
    sq = sonar_data()
    tags = dockerhub_tags(dockerhub_repo)
    builds = jenkins_builds()
    cluster = cluster_state()

    files = {
        "REPORT.md": write_report(info, tests, sq, tags, builds, host, dockerhub_repo,
                                  generated),
        "SONARQUBE_REPORT.md": write_sonar_report(sq, host, generated),
        "EVIDENCE.md": write_evidence(cluster, host, generated),
    }
    for name, text in files.items():
        (HERE / name).write_text(text, encoding="utf-8")
        log(f"wrote {(HERE / name).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
