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
