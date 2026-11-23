# Evidence

## Cluster state at 2026-11-23 11:22 UTC

Stable release: `vinayaktekadebits/aceest-fitness:2.2.0-10`. URLs: Rolling update `http://localhost:30081`, Blue-green `http://localhost:30082`, Canary `http://localhost:30083`, A/B testing `http://localhost:30084`, Shadow `http://localhost:30085`.

| Deployment | Strategy | Image | Ready |
|---|---|---|---|
| `aceest-ab-a` | ab-testing | `vinayaktekadebits/aceest-fitness:2.2.0-8` | 1/1 |
| `aceest-ab-b` | ab-testing | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 1/1 |
| `aceest-ab-router` | ab-testing | `nginxinc/nginx-unprivileged:stable-alpine` | 1/1 |
| `aceest-blue` (live) | blue-green | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 2/2 |
| `aceest-canary` | canary | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 0/0 |
| `aceest-canary-stable` | canary | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 3/3 |
| `aceest-green` | blue-green | `vinayaktekadebits/aceest-fitness:2.2.0-8` | 2/2 |
| `aceest-rolling` | rolling | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 3/3 |
| `aceest-shadow` | shadow | `vinayaktekadebits/aceest-fitness:2.2.0-10` | 1/1 |
| `aceest-shadow-live` | shadow | `vinayaktekadebits/aceest-fitness:2.2.0-8` | 1/1 |
| `aceest-shadow-router` | shadow | `nginxinc/nginx-unprivileged:stable-alpine` | 1/1 |

## Step 11 — Version 2.2.1 and rollback

**Step 11.1: add readiness and versions unit tests**

![Step 11.1: add readiness and versions unit tests](screenshots/Step11.1%20add%20readiness%20and%20versions%20unit%20tests.png)

**Step 11.2: add readiness and versions manual testing**

![Step 11.2: add readiness and versions manual testing](screenshots/Step11.2%20add%20readiness%20and%20versions%20manual%20testing.png)

**Step 11.3: add readiness and versions manual testing docker**

![Step 11.3: add readiness and versions manual testing docker](screenshots/Step11.3%20add%20readiness%20and%20versions%20manual%20testing%20docker.png)

**Step 11.4: add readiness and versions CICD**

![Step 11.4: add readiness and versions CICD](screenshots/Step11.4%20add%20readiness%20and%20versions%20CICD.png)

## Step 12

**Step 12.0: add sonarqube**

![Step 12.0: add sonarqube](screenshots/Step12.0%20add%20sonarqube.png)

**Step 12.1: sonarqube scan**

![Step 12.1: sonarqube scan](screenshots/Step12.1%20sonarqube%20scan.png)

**Step 12.2: sonarqube report**

![Step 12.2: sonarqube report](screenshots/Step12.2%20sonarqube%20report.png)

**Step 12.3: sonarqube vulnerability**

![Step 12.3: sonarqube vulnerability](screenshots/Step12.3%20sonarqube%20vulnerability.png)

**Step 12.4: sonarqube vulnerability status**

![Step 12.4: sonarqube vulnerability status](screenshots/Step12.4%20sonarqube%20vulnerability%20status.png)

**Step 12.5: sonarqube CICD**

![Step 12.5: sonarqube CICD](screenshots/Step12.5%20sonarqube%20CICD.png)

## Step 13

**Step 13.0: dockerhub failed CI**

![Step 13.0: dockerhub failed CI](screenshots/Step13.0%20dockerhub%20failed%20CI.png)

**Step 13.1: dockerhub archive image version CI**

![Step 13.1: dockerhub archive image version CI](screenshots/Step13.1%20dockerhub%20archive%20image%20version%20CI.png)

**Step 13.2: dockerhub archive image version CI**

![Step 13.2: dockerhub archive image version CI](screenshots/Step13.2%20dockerhub%20archive%20image%20version%20CI.png)

## Step 14

**Step 14.0: k8s rolling update**

![Step 14.0: k8s rolling update](screenshots/Step14.0%20k8s%20rolling%20update.png)

**Step 14.1: k8s rolling update CD**

![Step 14.1: k8s rolling update CD](screenshots/Step14.1%20k8s%20rolling%20update%20CD.png)

**Step 14.2: k8s blue green**

![Step 14.2: k8s blue green](screenshots/Step14.2%20k8s%20blue%20green.png)

**Step 14.3: k8s blue green CD**

![Step 14.3: k8s blue green CD](screenshots/Step14.3%20k8s%20blue%20green%20CD.png)

**Step 14.4: k8s canary**

![Step 14.4: k8s canary](screenshots/Step14.4%20k8s%20canary.png)

**Step 14.5: k8s canary CD**

![Step 14.5: k8s canary CD](screenshots/Step14.5%20k8s%20canary%20CD.png)

## Step 15

**Step 15.0: body metrics unit testing**

![Step 15.0: body metrics unit testing](screenshots/Step15.0%20body%20metrics%20unit%20testing.png)

**Step 15.1: body metrics CICD**

![Step 15.1: body metrics CICD](screenshots/Step15.1%20body%20metrics%20CICD.png)

**Step 15.2: body metrics sonarqube**

![Step 15.2: body metrics sonarqube](screenshots/Step15.2%20body%20metrics%20sonarqube.png)

**Step 15.3: body metrics dockerhub**

![Step 15.3: body metrics dockerhub](screenshots/Step15.3%20body%20metrics%20dockerhub.png)

## Step 16

**Step 16.0: shadow analysis**

![Step 16.0: shadow analysis](screenshots/Step16.0%20shadow%20analysis.png)

**Step 16.1: shadow analysis CICD**

![Step 16.1: shadow analysis CICD](screenshots/Step16.1%20shadow%20analysis%20CICD.png)

## Step 17

**Step 17.0: ab testing**

![Step 17.0: ab testing](screenshots/Step17.0%20ab%20testing.png)

**Step 17.1: ab testing CICD**

![Step 17.1: ab testing CICD](screenshots/Step17.1%20ab%20testing%20CICD.png)

## Step 18

**Step 18.0: workout plan CICD zero downtime**

![Step 18.0: workout plan CICD zero downtime](screenshots/Step18.0%20workout%20plan%20CICD%20zero%20downtime.png)

**Step 18.1: workout plan unit testing**

![Step 18.1: workout plan unit testing](screenshots/Step18.1%20workout%20plan%20unit%20testing.png)

