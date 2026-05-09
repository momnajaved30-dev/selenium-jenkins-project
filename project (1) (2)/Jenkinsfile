pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME = 'ecommerce-test-app'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the repository from GitHub
                checkout scm
            }
        }

        stage('Build Test Image') {
            steps {
                script {
                    // Build the Docker image from Dockerfile.test
                    echo "Building Docker image for testing..."
                    sh "docker build -t ${DOCKER_IMAGE_NAME} -f Dockerfile.test ."
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    // Run the container which will execute run_tests.sh
                    echo "Running tests in Docker container..."
                    sh "docker run --rm ${DOCKER_IMAGE_NAME}"
                }
            }
        }
    }


}
