pipeline {
    agent any

    triggers {
        // VM is not reachable from GitHub, so poll for new commits every ~5 minutes
        pollSCM('H/5 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds()
        timeout(time: 60, unit: 'MINUTES')
    }

    environment {
        DOCKERHUB_REPO = 'vinayaktekadebits/aceest-fitness'
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_TOKEN = credentials('sonarqube-token')
        KUBECONFIG = credentials('kubeconfig')     // file credential: path to a kubeconfig for Minikube
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()          // clean workspace -> clean build every time
                checkout scm
                script {
                    // VERSION holds the release number; the build number makes every image unique
                    env.APP_VERSION = readFile('VERSION').trim()
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.APP_VERSION}-${env.BUILD_NUMBER}"
                    env.IMAGE = "${env.DOCKERHUB_REPO}:${env.IMAGE_TAG}"
                    currentBuild.displayName = "#${env.BUILD_NUMBER} v${env.IMAGE_TAG}"
                }
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '. .venv/bin/activate && flake8 .'
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -v --junitxml=reports/junit.xml \
                        --cov=aceest --cov=app --cov=ACEest_Fitness \
                        --cov-report=term --cov-report=xml:reports/coverage.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                // Runs the scanner in a container. The workspace is mounted at the same path, so
                // the file paths in coverage.xml match. qualitygate.wait makes the scanner wait
                // for SonarQube's verdict and fail this stage if the quality gate fails.
                sh '''
                    docker run --rm --network host --user "$(id -u):$(id -g)" \
                        -e SONAR_HOST_URL -e SONAR_TOKEN -e SONAR_USER_HOME="$WORKSPACE/.sonar" \
                        -v "$WORKSPACE:$WORKSPACE" -w "$WORKSPACE" \
                        sonarsource/sonar-scanner-cli:latest \
                        -Dsonar.projectVersion="$APP_VERSION" \
                        -Dsonar.working.directory="$WORKSPACE/.scannerwork" \
                        -Dsonar.qualitygate.wait=true \
                        -Dsonar.qualitygate.timeout=300
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build --target runtime \
                        --build-arg APP_VERSION="$APP_VERSION" \
                        --build-arg GIT_COMMIT="$GIT_SHORT" \
                        --label org.opencontainers.image.source="$(git config --get remote.origin.url)" \
                        -t "$IMAGE" -t "$DOCKERHUB_REPO:$APP_VERSION" -t "$DOCKERHUB_REPO:latest" .
                '''
            }
        }

        stage('Test in Container') {
            steps {
                sh 'docker build --target test -t "aceest-fitness:test-$BUILD_NUMBER" .'
                sh 'docker run --rm "aceest-fitness:test-$BUILD_NUMBER"'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                        usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        docker push "$IMAGE"
                        docker push "$DOCKERHUB_REPO:$APP_VERSION"
                        docker push "$DOCKERHUB_REPO:latest"
                    '''
                }
            }
        }

        stage('Archive Artifacts') {
            steps {
                // build artifacts of this version: source bundle, build info and test reports
                sh '''
                    mkdir -p dist
                    git archive --format=tar.gz --prefix="aceest-fitness-$APP_VERSION/" \
                        -o "dist/aceest-fitness-$IMAGE_TAG-src.tar.gz" HEAD
                    printf '{"version": "%s", "build": "%s", "commit": "%s", "image": "%s", "digest": "%s"}\n' \
                        "$APP_VERSION" "$BUILD_NUMBER" "$GIT_SHORT" "$IMAGE" \
                        "$(docker image inspect -f '{{index .RepoDigests 0}}' "$IMAGE")" > dist/build-info.json
                    cat dist/build-info.json
                '''
                archiveArtifacts artifacts: 'dist/*, reports/*.xml', fingerprint: true
            }
        }

        // Progressive delivery: each strategy is its own environment with its own URL.
        // The cheapest checks with the smallest blast radius run first (shadow: no user sees
        // the new version; canary: ~25 % of one endpoint). A failed stage rolls its own strategy
        // back and stops the build, so the stages after it never receive the bad version.
        // A stage is skipped until its script exists (each strategy was added in its own PR).
        stage('Deploy: Shadow') {
            when { expression { fileExists('deploy/k8s/shadow.sh') } }
            steps {
                sh 'bash deploy/k8s/shadow.sh deploy "$IMAGE"'
            }
        }

        stage('Deploy: Canary') {
            when { expression { fileExists('deploy/k8s/canary.sh') } }
            steps {
                sh 'bash deploy/k8s/canary.sh deploy "$IMAGE"'
            }
        }

        stage('Deploy: Rolling Update') {
            when { expression { fileExists('deploy/k8s/rolling.sh') } }
            steps {
                sh 'bash deploy/k8s/rolling.sh deploy "$IMAGE"'
            }
        }

        stage('Deploy: Blue-Green') {
            when { expression { fileExists('deploy/k8s/blue-green.sh') } }
            steps {
                sh 'bash deploy/k8s/blue-green.sh deploy "$IMAGE"'
            }
        }

        stage('Deploy: A/B Testing') {
            when { expression { fileExists('deploy/k8s/ab-testing.sh') } }
            steps {
                sh 'bash deploy/k8s/ab-testing.sh deploy "$IMAGE"'
            }
        }

        stage('Mark Stable') {
            steps {
                sh '''
                    bash deploy/k8s/release.sh mark-stable "$IMAGE"
                    docker tag "$IMAGE" "$DOCKERHUB_REPO:stable"
                    docker push "$DOCKERHUB_REPO:stable"
                    bash deploy/k8s/status.sh
                '''
            }
        }
    }

    post {
        always {
            sh 'docker logout > /dev/null 2>&1 || true'
            sh 'docker image prune -f'
        }
        success {
            echo "Build ${env.BUILD_NUMBER}: ${env.IMAGE} passed every stage and is the new stable release"
        }
        failure {
            echo "Build ${env.BUILD_NUMBER} failed. The failed deploy stage rolled its strategy back; later stages were not run."
        }
    }
}
