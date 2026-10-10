# ACEest Fitness & Gym — DevOps Assignment 1 Report

## 1. Objective

Implement an automated CI/CD workflow for the ACEest Fitness & Gym Flask application:
version control with Git and GitHub, unit tests with Pytest, containerisation with Docker,
a Jenkins BUILD and quality gate, and a GitHub Actions pipeline that lints, builds and tests
the application in a container on every push and pull request. The Jenkins pipeline was then
extended with continuous deployment to the build VM.

## 2. Architecture

```
developer ─► git push ─► GitHub ──┬──► GitHub Actions: Build & Lint ─► Docker Image Assembly ─► Tests in container
                                  │
                                  └──► Jenkins (polls main): Checkout ─► Install ─► Lint ─► Unit Tests
                                        ─► Docker Build ─► Test in Container ─► Deploy ─► Smoke Test ─► Mark Stable
                                                                                   │
                                                         VM: nginx :8000 ─► blue :8001 / green :8002
```

## 3. Deliverables

| File | Purpose | Present |
|---|---|---|
| `app.py` | Flask application entry point | ✅ |
| `requirements.txt` | Runtime dependencies | ✅ |
| `tests` | Pytest suite | ✅ |
| `Dockerfile` | Container image (multi-stage) | ✅ |
| `.github/workflows/main.yml` | GitHub Actions pipeline | ✅ |
| `Jenkinsfile` | Jenkins BUILD and deploy pipeline | ✅ |
| `README.md` | Project documentation | ✅ |
| `deploy/blue-green.sh` | Blue-green deployment script | ✅ |

## 4. Application

Flask REST API ported from the Tkinter desktop versions (v1.0 – v3.2.4).
Endpoints found in the code:

| Method | Path | Defined in |
|---|---|---|
| GET | `/` | `app.py` |
| GET | `/health` | `app.py` |
| POST | `/clients` | `aceest/clients.py` |
| GET | `/clients` | `aceest/clients.py` |
| GET | `/clients/<name>` | `aceest/clients.py` |
| GET | `/clients/<name>/bmi` | `aceest/clients.py` |
| GET | `/clients/<name>/membership` | `aceest/membership.py` |
| POST | `/clients/<name>/membership` | `aceest/membership.py` |
| GET | `/programs` | `aceest/programs.py` |
| GET | `/programs/<code>` | `aceest/programs.py` |
| POST | `/clients/<name>/progress` | `aceest/tracking.py` |
| GET | `/clients/<name>/progress` | `aceest/tracking.py` |
| POST | `/clients/<name>/workouts` | `aceest/tracking.py` |
| GET | `/clients/<name>/workouts` | `aceest/tracking.py` |

## 5. Version control

### Pull requests merged into main

| PR | Branch | Title | Merged |
|---|---|---|---|
| [#1](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/1) | `feature/programs-api` | feat: Flask API with health and programs endpoints | 2026-10-10 |
| [#2](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/2) | `infra/docker` | build: containerise the app with a multi-stage Dockerfile | 2026-10-10 |
| [#3](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/3) | `ci/github-actions` | ci: add GitHub Actions pipeline for lint, docker build and containerised tests) | 2026-10-10 |
| [#4](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/4) | `ci/jenkins` | ci: add Jenkins build pipeline | 2026-10-10 |
| [#5](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/5) | `feature/clients` | feat: client profiles with SQLite storage, calories and BMI | 2026-10-10 |
| [#6](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/6) | `cd/deploy` | cd: automatic deployment to VM staging via Jenkins | 2026-10-10 |
| [#7](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/7) | `feature/progress-workouts` | feat: weekly adherence tracking and workout logging | 2026-10-10 |
| [#8](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/8) | `cd/rolling-update` | cd: zero-downtime rolling update behind an nginx load balancer | 2026-10-10 |
| [#9](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/9) | `feature/membership` | feat: membership renewal and status checks | 2026-10-10 |
| [#10](https://github.com/VinayakTekade-BITS/aceest-fitness/pull/10) | `cd/blue-green` | cd: blue-green deployment with instant rollback | 2026-10-10 |

### Commit graph

```
* d867641 2026-10-11 docs: add setup, testing and CI/CD overview to README
*   edf5587 2026-10-10 Merge pull request #10 from VinayakTekade-BITS/cd/blue-green
|\  
| * 1516de3 2026-10-10 cd: remove rolling update script in favour of blue-green
| * a5eebb3 2026-10-10 cd: switch Jenkins deploy stage to blue-green
| * ff3bbb1 2026-10-10 cd: add blue-green deploy and switch script
|/  
*   6ecc946 2026-10-10 Merge pull request #9 from VinayakTekade-BITS/feature/membership
|\  
| * 40744e2 2026-10-10 test: cover membership status and renewal rules
| * c417ae1 2026-10-10 feat: add membership renewal and status endpoints
|/  
*   403d29d 2026-10-10 Merge pull request #8 from VinayakTekade-BITS/cd/rolling-update
|\  
| * c527524 2026-10-10 cd: switch Jenkins deploy stage to rolling update
| * e00b698 2026-10-10 cd: add rolling update script with nginx load balancer
|/  
*   152d635 2026-10-10 Merge pull request #7 from VinayakTekade-BITS/feature/progress-workouts
|\  
| * 668d90e 2026-10-10 test: cover progress and workout logging
| * 17ad111 2026-10-10 feat: add weekly adherence tracking and workout logging endpoints
|/  
*   8f1c5c1 2026-10-10 Merge pull request #6 from VinayakTekade-BITS/cd/deploy
|\  
| * 57666da 2026-10-10 cd: deploy to staging container with smoke test and rollback
|/  
*   dda4d2c 2026-10-10 Merge pull request #5 from VinayakTekade-BITS/feature/clients
|\  
| * a69fe90 2026-10-10 test: cover client creation, validation, calories and BMI
| * 681f2f5 2026-10-10 feat: add client profiles with SQLite storage, calorie and BMI calculation
|/  
*   3ada8e6 2026-10-10 Merge pull request #4 from VinayakTekade-BITS/ci/jenkins
|\  
| * 24d786c 2026-10-10 ci: add Jenkinsfile with clean build, lint, tests and docker stages
|/  
*   49e24d6 2026-10-10 Merge pull request #3 from VinayakTekade-BITS/ci/github-actions
|\  
| * af41339 2026-10-10 ci: add GitHub Actions pipeline for lint, docker build and containerised tests
|/  
*   72759f8 2026-10-10 Merge pull request #2 from VinayakTekade-BITS/infra/docker
|\  
| * d448cc2 2026-10-10 build: add multi-stage Dockerfile with non-root runtime and test target
|/  
*   82f28cb 2026-10-10 Merge pull request #1 from VinayakTekade-BITS/feature/programs-api
|\  
| * 9efb924 2026-10-10 test: add pytest suite for health and programs endpoints
| * 0edb983 2026-10-10 feat: add Flask app with health and programs endpoints
|/  
* 1b7a410 2026-10-10 chore: initial commit
```

## 6. Testing

| Check | Result |
|---|---|
| flake8 | ✅ no issues |
| pytest | ✅ 56 passed in 4.53s |
| Coverage | 99% |

Tests per file:

| Test file | Tests |
|---|---|
| `tests/test_clients.py` | 21 |
| `tests/test_membership.py` | 12 |
| `tests/test_programs.py` | 8 |
| `tests/test_tracking.py` | 15 |

Coverage by module:

```
Name                   Stmts   Miss  Cover
------------------------------------------
aceest/__init__.py         2      0   100%
aceest/clients.py         67      0   100%
aceest/db.py              13      0   100%
aceest/membership.py      32      0   100%
aceest/programs.py        13      0   100%
aceest/tracking.py        47      0   100%
app.py                    24      1    96%
------------------------------------------
TOTAL                    198      1    99%
```

## 7. Docker

| Property | Value |
|---|---|
| Base image | `python:3.12-slim` |
| Build stages | `base test runtime` |
| Image size | 125 MB |
| Layers | 23 |
| Runs as | ✅ `appuser` (non-root) |
| Health check | ✅ yes |
| Start command | `gunicorn --bind 0.0.0.0:5000 --workers 2 app:app` |
| Tests inside the container | ✅ 56 passed in 1.55s |

## 8. CI/CD pipelines

### GitHub Actions (`.github/workflows/main.yml`)

Runs on every push and pull request. Jobs: Build & Lint → Docker Image Assembly → Automated Testing (in container).

Latest workflow runs:

| Run | Branch | Event | Commit | Result | Date |
|---|---|---|---|---|---|
| [#29](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38078584087) | `main` | push | `4709e62` | ✅ success | 2026-10-10 |
| [#28](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38078488681) | `main` | push | `2591f8e` | ✅ success | 2026-10-10 |
| [#27](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38078354683) | `docs/readme` | pull_request | `d867641` | ✅ success | 2026-10-10 |
| [#26](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38078132023) | `docs/readme` | push | `d867641` | ✅ success | 2026-10-10 |
| [#25](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38077842665) | `docs/readme` | push | `d39bd11` | ✅ success | 2026-10-10 |
| [#24](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38075541210) | `main` | push | `edf5587` | ✅ success | 2026-10-10 |
| [#23](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38075185302) | `cd/blue-green` | pull_request | `1516de3` | ✅ success | 2026-10-10 |
| [#22](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38075072791) | `cd/blue-green` | push | `1516de3` | ✅ success | 2026-10-10 |
| [#21](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38073891182) | `main` | push | `6ecc946` | ✅ success | 2026-10-10 |
| [#20](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38073765674) | `feature/membership` | pull_request | `40744e2` | ✅ success | 2026-10-10 |
| [#19](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38073722087) | `feature/membership` | push | `40744e2` | ✅ success | 2026-10-10 |
| [#18](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38072772178) | `main` | push | `403d29d` | ✅ success | 2026-10-10 |
| [#17](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38072665910) | `cd/rolling-update` | pull_request | `c527524` | ✅ success | 2026-10-10 |
| [#16](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38072606857) | `cd/rolling-update` | push | `c527524` | ✅ success | 2026-10-10 |
| [#15](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/runs/38071959215) | `main` | push | `152d635` | ✅ success | 2026-10-10 |

15 of the last 15 runs succeeded.

### Jenkins (`Jenkinsfile`)

Polls `main` every 5 minutes. Stages: Checkout → Install → Lint → Unit Tests → Docker Build → Test in Container → Deploy (blue-green) → Smoke Test → Mark Stable.

## 9. Continuous deployment

| | |
|---|---|
| Strategy | Blue-green |
| Live URL | `http://<vm-ip>:8000` |
| Health check | ✅ `{"status":"ok"}` |
| Live color | green |
| Last stable image | 2026-10-11 00:38 (UTC) |

Running containers:

| Container | Image | Status | Ports |
|---|---|---|---|
| `aceest-green` | `aceest-fitness:12` | Up 20 minutes (healthy) | 0.0.0.0:8002->5000/tcp, [::]:8002->5000/tcp |
| `aceest-blue` | `aceest-fitness:10` | Up 52 minutes (healthy) | 0.0.0.0:8001->5000/tcp, [::]:8001->5000/tcp |
| `aceest-lb` | `nginx:alpine` | Up 2 hours | 0.0.0.0:8000->80/tcp, [::]:8000->80/tcp |

Deployment strategy history (each change was its own `cd/*` pull request):

| Strategy | How it works | Why it was replaced |
|---|---|---|
| Recreate | Stop the container, start the new one; roll back to `stable` on failure | Seconds of downtime on every deploy |
| Rolling update | 3 replicas behind nginx, replaced one at a time | Mixed versions during a rollout; slow rollback |
| **Blue-green** (current) | New version tested next to the live one, then nginx switches all traffic | — |

## 10. Evidence

### Step 1 — Flask application

**Step 1.0: Initialise flask app**

![Step 1.0: Initialise flask app](Screenshots/Step1.0%20Initialise%20flask%20app.png)

**Step 1.1: Manual testing flask app**

![Step 1.1: Manual testing flask app](Screenshots/Step1.1%20manual%20testing%20flask%20app.png)

**Step 1.2: Unit testing flask app**

![Step 1.2: Unit testing flask app](Screenshots/Step1.2%20unit%20testing%20flask%20app.png)

### Step 2 — Docker image

**Step 2.0: Docker build**

![Step 2.0: Docker build](Screenshots/Step2.0%20docker%20build.png)

**Step 2.1: Docker run app**

![Step 2.1: Docker run app](Screenshots/Step2.1%20docker%20run%20app.png)

**Step 2.2: Docker run test**

![Step 2.2: Docker run test](Screenshots/Step2.2%20docker%20run%20test.png)

### Step 3 — GitHub Actions CI

**Step 3.0: Setup github actions ci**

![Step 3.0: Setup github actions ci](Screenshots/Step3.0%20setup%20github%20actions%20ci.png)

**Step 3.1: Ci checks on pr**

![Step 3.1: Ci checks on pr](Screenshots/Step3.1%20ci%20checks%20on%20pr.png)

### Step 4 — Jenkins pipeline

**Step 4.0: Setup jenkins pipeline**

![Step 4.0: Setup jenkins pipeline](Screenshots/Step4.0%20setup%20jenkins%20pipeline.png)

**Step 4.1: Config jenkins pipeline**

![Step 4.1: Config jenkins pipeline](Screenshots/Step4.1%20config%20jenkins%20pipeline.png)

**Step 4.2: Run jenkins pipeline**

![Step 4.2: Run jenkins pipeline](Screenshots/Step4.2%20run%20jenkins%20pipeline.png)

### Step 5 — Feature: clients

**Step 5.0: Feature clients manual testing**

![Step 5.0: Feature clients manual testing](Screenshots/Step5.0%20feature%20clients%20manual%20testing.png)

**Step 5.1: Feature clients unit testing**

![Step 5.1: Feature clients unit testing](Screenshots/Step5.1%20feature%20clients%20unit%20testing.png)

**Step 5.2: Feature clients github action ci**

![Step 5.2: Feature clients github action ci](Screenshots/Step5.2%20feature%20clients%20github%20action%20ci.png)

**Step 5.3: Feature clients jenkins ci**

![Step 5.3: Feature clients jenkins ci](Screenshots/Step5.3%20feature%20clients%20jenkins%20ci.png)

### Step 6 — Continuous deployment (Recreate)

**Step 6.0: Setup jenkins cicd**

![Step 6.0: Setup jenkins cicd](Screenshots/Step6.0%20setup%20jenkins%20cicd.png)

**Step 6.1: Deploy step jenkins cicd**

![Step 6.1: Deploy step jenkins cicd](Screenshots/Step6.1%20deploy%20step%20jenkins%20cicd.png)

**Step 6.2: Test deployed version**

![Step 6.2: Test deployed version](Screenshots/Step6.2%20test%20deployed%20version.png)

### Step 7 — Feature: progress and workouts

**Step 7.0: Feature tracking and logging unit testing**

![Step 7.0: Feature tracking and logging unit testing](Screenshots/Step7.0%20feature%20tracking%20and%20logging%20unit%20testing.png)

**Step 7.1: Feature tracking and logging ci**

![Step 7.1: Feature tracking and logging ci](Screenshots/Step7.1%20feature%20tracking%20and%20logging%20ci.png)

**Step 7.2: Feature tracking and logging cicd**

![Step 7.2: Feature tracking and logging cicd](Screenshots/Step7.2%20feature%20tracking%20and%20logging%20cicd.png)

**Step 7.3: Feature tracking and logging deploy**

![Step 7.3: Feature tracking and logging deploy](Screenshots/Step7.3%20feature%20tracking%20and%20logging%20deploy.png)

**Step 7.4: Feature tracking and logging test deployed**

![Step 7.4: Feature tracking and logging test deployed](Screenshots/Step7.4%20feature%20tracking%20and%20logging%20test%20deployed.png)

### Step 8 — Rolling update deployment

**Step 8.0: Rolling deployments cicd**

![Step 8.0: Rolling deployments cicd](Screenshots/Step8.0%20rolling%20deployments%20cicd.png)

**Step 8.1: Rolling deployments deploy logs**

![Step 8.1: Rolling deployments deploy logs](Screenshots/Step8.1%20rolling%20deployments%20deploy%20logs.png)

**Step 8.2: Rolling deployments verify**

![Step 8.2: Rolling deployments verify](Screenshots/Step8.2%20rolling%20deployments%20verify.png)

**Step 8.3: Rolling deployments no downtime**

![Step 8.3: Rolling deployments no downtime](Screenshots/Step8.3%20rolling%20deployments%20no%20downtime.png)

### Step 9 — Feature: membership

**Step 9.0: Feature membership unit test coverage**

![Step 9.0: Feature membership unit test coverage](Screenshots/Step9.0%20feature%20membership%20unit%20test%20coverage.png)

**Step 9.1: Feature membership ci**

![Step 9.1: Feature membership ci](Screenshots/Step9.1%20feature%20membership%20ci.png)

**Step 9.2: Feature membership cicd**

![Step 9.2: Feature membership cicd](Screenshots/Step9.2%20feature%20membership%20cicd.png)

**Step 9.2: Feature membership deploy logs**

![Step 9.2: Feature membership deploy logs](Screenshots/Step9.2%20feature%20membership%20deploy%20logs.png)

**Step 9.3: Feature membership deploy verify**

![Step 9.3: Feature membership deploy verify](Screenshots/Step9.3%20feature%20membership%20deploy%20verify.png)

### Step 10 — Blue-green deployment

**Step 10.0: Blue-green deployment blue cd**

![Step 10.0: Blue-green deployment blue cd](Screenshots/Step10.0%20blue-green%20deployment%20blue%20cd.png)

**Step 10.1: Blue-green deployment green cd**

![Step 10.1: Blue-green deployment green cd](Screenshots/Step10.1%20blue-green%20deployment%20green%20cd.png)

**Step 10.2: Blue-green deployment verify**

![Step 10.2: Blue-green deployment verify](Screenshots/Step10.2%20blue-green%20deployment%20verify.png)

### Artifacts

**Blue green deployment**

![Blue green deployment](Screenshots/Artifact%20blue%20green%20deployment.png)

**Docker images created**

![Docker images created](Screenshots/Artifact%20docker%20images%20created.png)

**Git history**

![Git history](Screenshots/Artifact%20git%20history.png)

**Rolling deployment**

![Rolling deployment](Screenshots/Artifact%20rolling%20deployment.png)

## 11. Challenges and learnings

- **Docker permission for Jenkins:** the `Docker Build` stage failed with `permission denied ... docker.sock`
  until the Jenkins service user was added to the `docker` group.
- **Variable lost after `newgrp`:** `newgrp docker` opens a new shell, so a shell variable set before it was empty.
  I used the user name directly instead.
- **Moving from Recreate to rolling and blue-green:** each first run had to remove the previous strategy's
  containers to free port 8000.

## 12. Conclusion

The ACEest Fitness & Gym application was moved from a desktop Tkinter script to a tested
Flask REST API, packaged as a slim, non-root Docker image. Every push and pull request is
validated by GitHub Actions (lint, image build, tests inside the container), and every merge to
`main` is rebuilt by Jenkins as an independent quality gate and deployed automatically to the VM.
The deployment strategy evolved from Recreate to a rolling update to blue-green, giving zero-downtime
releases and one-command rollback.
