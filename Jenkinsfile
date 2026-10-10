pipeline {
    agent any

    triggers {
        // VM is not reachable from GitHub, so poll for new commits every ~5 minutes
        pollSCM('H/5 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE = 'aceest-fitness'
        DEPLOY_PORT = '8000'
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
                sh '. .venv/bin/activate && pytest -v --junitxml=reports/junit.xml --cov=aceest --cov=app --cov-report=term'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
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
