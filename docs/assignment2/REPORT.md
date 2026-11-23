# ACEest Fitness & Gym — Assignment 2: CI/CD with Jenkins, SonarQube, Docker Hub and Kubernetes

|  |  |
|---|---|
| Author | VinayakTekade-BITS |
| Repository | <https://github.com/VinayakTekade-BITS/aceest-fitness> |
| Docker Hub | <https://hub.docker.com/r/vinayaktekadebits/aceest-fitness/tags> |
| Commit | `1681b6a` on `docs-a2` |
| Generated | 2026-11-23 11:22 UTC by `docs/assignment2/generate_report.py` |

## 1. CI/CD architecture overview

Every change goes through a branch and a pull request (GitHub Actions checks it). Jenkins polls `main` every 5 minutes and runs the whole pipeline: lint, unit tests, SonarQube quality gate, Docker image, tests inside the container, push to Docker Hub, and deployment to Minikube with five strategies. Each strategy is its own environment with its own URL, and all of them run at the same time.

```text
developer ─► feature branch ─► pull request ─► GitHub Actions (lint, image, tests)
                                   │ merge
                                   ▼
            Jenkins (polls main) ─► Lint ─► Unit Tests ─► SonarQube quality gate
              ─► Docker Build ─► Test in Container ─► Push to Docker Hub ─► Archive
              ─► Shadow ─► Canary ─► Rolling ─► Blue-Green ─► A/B ─► Mark Stable
                                   │ kubectl
                                   ▼
            Minikube, namespace aceest: one Service (NodePort) per strategy
```

| Concern | Tool | Where |
|---|---|---|
| Version control | Git, GitHub: branches, pull requests, tags `vX.Y.Z` | `git tag`, Releases |
| Build server | Jenkins Pipeline, polls GitHub (the VM accepts no webhooks) | `Jenkinsfile` |
| Tests | Pytest with coverage, also inside the container | `tests/` |
| Code quality | SonarQube Community, quality gate enforced by the scanner | `sonar-project.properties` |
| Container | Docker multi-stage image, non-root, health check | `Dockerfile` |
| Registry | Docker Hub, one tag per version and per build | vinayaktekadebits/aceest-fitness |
| Deployment | Kubernetes (Minikube), five strategies | `k8s/`, `deploy/k8s/` |

Jenkins stages: Checkout → Install → Lint → Unit Tests → SonarQube Analysis → Docker Build → Test in Container → Push to Docker Hub → Archive Artifacts → Deploy: Shadow → Deploy: Canary → Deploy: Rolling Update → Deploy: Blue-Green → Deploy: A/B Testing → Mark Stable.

### Deployment strategies

| Strategy | URL | How it works | Rollback |
|---|---|---|---|
| Rolling update | `http://localhost:30081` | 3 replicas replaced one pod at a time (maxSurge 1, maxUnavailable 0, readiness probe) | automatic `kubectl rollout undo`; the failed revision is deleted |
| Blue-green | `http://localhost:30082` | new version on the idle color, tested via the preview port 30086, then the Service selector switches all traffic at once | traffic is never switched to a failing color; manual: `blue-green.sh rollback` |
| Canary | `http://localhost:30083` | 1 canary pod next to 3 stable pods (~25 % of requests); 60 test requests must give 0 errors, then the stable track is promoted | canary scaled to 0, stable track untouched |
| A/B testing | `http://localhost:30084` | nginx router: X-Variant header, else ab_variant cookie, else 50/50; A = previous stable release, B = new release | variant B rolled back to its previous image |
| Shadow | `http://localhost:30085` | nginx mirrors every request to the shadow track (own database); users only get the live answer; the shadow must answer all copies without a 5xx | shadow scaled to 0; users never saw it |

The deploy stages run from the smallest to the largest blast radius. A failing stage rolls its own strategy back and stops the build, so later strategies never receive the bad version. The image of the last fully successful build is recorded as the stable release (ConfigMap `aceest-release`, Docker Hub tag `stable`).

## 2. Challenges faced and mitigation strategies

| Challenge | Mitigation |
|---|---|
| The SonarQube scanner container could not write its work folder (`AccessDenied: /tmp/.scannerwork`) when it ran as the Jenkins user. | Set `sonar.working.directory` to the Jenkins workspace and mount the workspace at the same path, so the paths in `coverage.xml` also match. |
| SonarQube reported a critical vulnerability (S4502, CSRF) on `Flask(__name__)`. | Reviewed it: the API is stateless JSON with no cookies or sessions, so CSRF does not apply. Marked it *Accepted* with that justification instead of adding a CSRF library that would break the API. |
| The "Sonar way" quality gate fails on **any** new issue; a test that compared an expression with itself (S5863) would have blocked a release. | Rewrote the test, and treated the gate as a hard rule: the build stops before an image is pushed. |
| Jenkins runs as a different Linux user and could not use the Minikube config in my home folder. | Exported a self-contained (flattened) kubeconfig and stored it as a Jenkins *Secret file* credential. |
| A few requests failed with 502 while pods were replaced. | `maxUnavailable: 0`, readiness probes on `/ready`, and a 5 s `preStop` sleep so that a pod leaves the Service before it stops. A request loop then saw only HTTP 200. |
| `kubectl rollout undo` keeps the failed revision, so a later manual rollback could bring the broken image back. | After an automatic rollback the script deletes the failed ReplicaSet. |
| The A/B smoke test passed with a broken variant B, because retries were sent to variant A at random. | The check tests each variant separately with the `X-Variant` header. |
| Several versions share one SQLite database during a release, and the shadow receives copies of real writes. | Only additive schema changes (new tables, nullable columns). The shadow has its own throw-away database. |
| With the Docker driver, Minikube NodePorts are only reachable inside the VM. | Started Minikube with `--ports` for 30081-30086, so the strategies are reachable at `http://<vm-ip>:<port>`. |

## 3. Key automation outcomes

- **Tests:** 87 passed in 8.27s, coverage 100%; the same suite runs inside the test image on every build.
- **SonarQube:** quality gate ✅ passed; 0 bugs, 1 vulnerabilities, 0 code smells, coverage 100.0 %, duplication 0.0 % (see [SONARQUBE_REPORT.md](SONARQUBE_REPORT.md)).
- **Jenkins:** 7 of the last 10 builds succeeded; every merge to `main` was built, tested and deployed without manual steps.
- **Docker Hub:** 16 tags, including every release (2.0.0, 2.1.0, 2.2.0), one tag per Jenkins build, `latest` and `stable`.
- **Releases:** 2 version tags, each with its Docker image (table below).
- **Zero downtime:** a request loop running during a release saw only HTTP 200 on every strategy (see [EVIDENCE.md](EVIDENCE.md)).

### Releases

| Tag | Date | Description |
|---|---|---|
| `v2.0.0` | 2026-11-23 | v2.0.0: Kubernetes-ready app (readiness, version info), ACEest_Fitness.py entry point |
| `v2.1.0` | 2026-11-23 | v2.1.0: body metrics and client summary |

Evidence: [EVIDENCE.md](EVIDENCE.md) (screenshots and cluster state) · [SONARQUBE_REPORT.md](SONARQUBE_REPORT.md)
