pipeline {
    agent any

    triggers {
        // VM is not reachable from GitHub, so poll for new commits every ~5 minutes
        pollSCM('H/5 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE = 'aceest-fitness'
        DEPLOY_PORT = '8000'
        SONAR_HOST_URL = 'http://localhost:9000'
        SONAR_TOKEN = credentials('sonarqube-token')
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()          // clean workspace -> clean build every time
                checkout scm
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
                        -Dsonar.projectVersion="$(cat VERSION)" \
                        -Dsonar.working.directory="$WORKSPACE/.scannerwork" \
                        -Dsonar.qualitygate.wait=true \
                        -Dsonar.qualitygate.timeout=300
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build --target runtime -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest .'
            }
        }

        stage('Test in Container') {
            steps {
                sh 'docker build --target test -t ${IMAGE}:test-${BUILD_NUMBER} .'
                sh 'docker run --rm ${IMAGE}:test-${BUILD_NUMBER}'
            }
        }

        stage('Deploy (blue-green)') {
            steps {
                sh 'bash deploy/blue-green.sh deploy ${IMAGE}:${BUILD_NUMBER}'
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if curl -fsS http://localhost:${DEPLOY_PORT}/health; then exit 0; fi
                        sleep 2
                    done
                    docker logs aceest-lb
                    exit 1
                '''
            }
        }

        stage('Mark Stable') {
            steps {
                sh 'docker tag ${IMAGE}:${BUILD_NUMBER} ${IMAGE}:stable'
            }
        }
    }

    post {
        always {
            sh 'docker image prune -f'
        }
        success {
            echo "Build ${BUILD_NUMBER} deployed (blue-green) to http://localhost:${DEPLOY_PORT}"
        }
        failure {
            echo "Build ${BUILD_NUMBER} failed - live traffic was not switched to the new version"
        }
    }
}
