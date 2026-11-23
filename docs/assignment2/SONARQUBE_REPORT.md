# SonarQube report — `aceest-fitness`

|  |  |
|---|---|
| Dashboard | <http://localhost:9000/dashboard?id=aceest-fitness> |
| Quality gate | Sonar way: ✅ **Passed** |
| Generated | 2026-11-23 11:22 UTC |

## Quality gate conditions (new code)

| Metric | Actual | Fails if | Status |
|---|---|---|---|
| new_coverage | 100.0 | < 80 | ✅ |
| new_duplicated_lines_density | 0.0 | > 3 | ✅ |
| new_violations | 0 | > 0 | ✅ |

## Overall code

| Measure | Value | Rating |
|---|---|---|
| Bugs | 0 | A |
| Vulnerabilities | 1 | D |
| Security hotspots | 0 | A |
| Code smells | 0 | A |
| Coverage | 100.0 % |  |
| Duplicated lines | 0.0 % |  |
| Lines of code | 472 |  |
| Unit tests | 87 |  |
| Accepted issues | 0 |  |

## Open issues

| Severity | Rule | File:line | Message |
|---|---|---|---|
| CRITICAL | python:S4502 | `app.py:15` | Make sure disabling CSRF protection is safe here. |

## Reviewed issues (accepted or false positive)

None.

## Security hotspots

None.

## Analysis history

One analysis per Jenkins build of `main`; the version is the VERSION file.

| Analysis (UTC) | Version | Quality gate | Coverage % |
|---|---|---|---|
| 2026-11-23 11:10 | 2.2.0 | ✅ Passed | 100.0 |
| 2026-11-23 11:08 | 2.2.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:46 | 2.2.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:41 | 2.2.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:29 | 2.1.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:24 | 2.1.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:09 | 2.1.0 | ✅ Passed | 100.0 |
| 2026-11-23 10:00 | 2.0.0 | ✅ Passed | 100.0 |
| 2026-11-23 09:51 | 2.0.0 | ✅ Passed | 100.0 |
| 2026-11-23 09:43 | 2.0.0 | ✅ Passed | 100.0 |
