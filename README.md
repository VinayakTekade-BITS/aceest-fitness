# ACEest Fitness & Gym — Flask API with CI/CD

![CI](https://github.com/VinayakTekade-BITS/aceest-fitness/actions/workflows/main.yml/badge.svg)

REST API for ACEest Fitness & Gym: training programs, client profiles (calories, BMI),
weekly adherence, workout logs and memberships. Built with Flask and SQLite, packaged with
Docker, and validated by GitHub Actions and Jenkins on every change.

## Project structure

```
docs/                   # Screenshots for the whole assignment
app.py                  # Flask app factory, health endpoint, JSON error handling
aceest/
  programs.py           # Fat Loss / Muscle Gain / Beginner programs
  clients.py            # client profiles, calorie and BMI calculation
  tracking.py           # weekly adherence + workout logs
  membership.py         # membership renewal and status
  db.py                 # SQLite connection and schema
tests/                  # pytest suite
Dockerfile              # multi-stage: base -> test -> runtime
Jenkinsfile             # Jenkins BUILD + deploy pipeline
deploy/blue-green.sh    # blue-green deploy and switch (rollback) script
.github/workflows/main.yml  # GitHub Actions pipeline
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/programs` | List programs |
| GET | `/programs/<code>` | Workout + diet plan (`FL`, `MG`, `BG`) |
| POST | `/clients` | Create client `{name, age, height_cm, weight_kg, program}` → calories |
| GET | `/clients` | List clients |
| GET | `/clients/<name>` | Client profile |
| GET | `/clients/<name>/bmi` | BMI and category |
| POST / GET | `/clients/<name>/progress` | Log / list weekly adherence `{week, adherence}` |
| POST / GET | `/clients/<name>/workouts` | Log / list workouts `{workout_type, duration_min, date?, notes?}` |
| POST / GET | `/clients/<name>/membership` | Renew `{months}` / check status |

Errors are returned as JSON: `{"error": "..."}` with status 400, 404 or 409.

## Local setup

Requirements: Python 3.9+, Docker.

```bash
git clone https://github.com/VinayakTekade-BITS/aceest-fitness.git
cd aceest-fitness
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python app.py                       # http://localhost:5000
```

Example:

```bash
curl -X POST localhost:5000/clients -H 'Content-Type: application/json' \
  -d '{"name":"Arjun","age":28,"height_cm":175,"weight_kg":80,"program":"MG"}'
curl localhost:5000/clients/Arjun/bmi
```

### Run with Docker

```bash
docker build -t aceest-fitness .
docker run -d -p 5000:5000 -v aceest-data:/app/data aceest-fitness
```

The runtime image is based on `python:3.12-slim`, runs as a non-root user, contains only the
application code, and is served by gunicorn with a container health check.

## Running tests manually

```bash
flake8 .                                          # lint
pytest -v                                         # unit tests
pytest --cov=aceest --cov=app --cov-report=term   # with coverage

docker build --target test -t aceest-fitness:test .
docker run --rm aceest-fitness:test               # tests inside the container
```

## CI/CD overview

```
git push ──► GitHub ──┬──► GitHub Actions (every push and pull request)
                      │      Build & Lint ─► Docker Image Assembly ─► Tests in container
                      │
                      └──► Jenkins (polls main every 5 min)
                             Checkout (clean) ─► Install ─► Lint ─► Unit Tests ─► Docker Build ─► Test in Container
                             ─► Deploy (blue-green) ─► Smoke Test ─► Mark Stable
```

**GitHub Actions** (`.github/workflows/main.yml`) runs on every push to any branch and on every
pull request:

1. **Build & Lint** — installs dependencies, compiles all sources and runs flake8.
2. **Docker Image Assembly** — builds the `runtime` and `test` images and passes them on as an artifact.
3. **Automated Testing** — runs the pytest suite inside the test container, then starts the runtime
   container and checks `/health`.

Pull requests show the result as status checks; `main` is protected so failing PRs cannot be merged.

**Jenkins** (`Jenkinsfile`) is the secondary BUILD and quality gate. A Pipeline job reads the
Jenkinsfile from this repository and polls `main` every 5 minutes. Each build starts from an empty
workspace, creates a fresh virtualenv, lints, runs the tests (JUnit report published in Jenkins),
builds the Docker image tagged with the build number, and re-runs the tests inside the container.

## Continuous Deployment

Every green Jenkins build of `main` is deployed automatically to the build VM using a
**blue-green** strategy. The live app is at `http://<vm-ip>:8000`.

```
                 ┌─► aceest-blue  (:8001)
:8000 aceest-lb ─┤        one color is live, the other holds the previous version
 (nginx)         └─► aceest-green (:8002)
```

1. **Deploy** (`deploy/blue-green.sh deploy <image>`): starts the new image on the idle color
   and smoke-tests it on that color's own port. If the test passes, nginx switches all traffic to it.
   If it fails, traffic is not switched and the build fails, so users never see the broken version.
2. **Smoke Test**: calls `/health` through the load balancer.
3. **Mark Stable**: tags the image that passed as `aceest-fitness:stable`.

Both colors share the `aceest-data` Docker volume, so client data survives deployments.
The `X-Color` response header shows which color answered:

```bash
curl -sI localhost:8000/health | grep -i x-color
```

**Rollback** takes about 1 second. The previous version is still running on the other color:

```bash
bash deploy/blue-green.sh switch blue     # or green
```

### Deployment history

The deployment strategy evolved in three steps (see the `cd/*` pull requests):

| Strategy | How it worked | Why it was replaced |
|---|---|---|
| Recreate | Stop the container, start the new one, roll back to `stable` on failure | A few seconds of downtime on every deploy |
| Rolling update | 3 replicas behind nginx, replaced one at a time | Mixed versions during a rollout; rolling back is slow |
| **Blue-green** (current) | New version tested next to the live one, then traffic switches at once | — |

## Branching and commits

- `main` is always releasable; work happens on `feature/*`, `infra/*`, `ci/*`, `cd/*` and `docs/*` branches.
- Every change is merged through a pull request after CI passes.
- Commit messages follow Conventional Commits (`feat:`, `test:`, `ci:`, `cd:`, `build:`, `docs:`).
