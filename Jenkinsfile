pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKERHUB_USERNAME = 'zumarr'
        IMAGE_NAME = 'devops-flask-app'
        IMAGE_TAG = "${BUILD_NUMBER}"

        // Jenkins Kubernetes access
        KUBECONFIG = "/var/lib/jenkins/.kube/config"
    }
    
    stages {

        stage('Code Fetch') {
            steps {
                script {
                    echo '========== Stage 1: Fetching Code from GitHub =========='
                    cleanWs()
                    git branch: 'main',
                        url: 'https://github.com/Farwah19/devOps-final.git'
                    sh 'ls -la'
                }
            }
        }
        
        stage('Docker Image Creation') {
            steps {
                script {
                    echo '========== Stage 2: Building Docker Image =========='

                    sh """
                        docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                    """

                    sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'

                    sh """
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                    """
                }
            }
        }
        
        stage('Kubernetes Deployment') {
            steps {
                script {
                    echo '========== Stage 3: Deploying to Kubernetes =========='

                    sh 'kubectl get nodes'

                    // MySQL setup
                    sh 'kubectl apply -f kubernetes/mysql-configmap.yaml'
                    sh 'kubectl apply -f kubernetes/pvc.yaml'
                    sh 'kubectl apply -f kubernetes/mysql-deployment.yaml'
                    sh 'kubectl apply -f kubernetes/mysql-service.yaml'

                    echo 'Waiting for MySQL to be ready...'
                    sh 'kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s || true'
                    sleep(time: 30, unit: 'SECONDS')

                    // Update image tag
                    sh """
                        sed -i 's|image:.*|image: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}|g' kubernetes/deployment.yaml
                    """

                    // Deploy Flask app
                    sh 'kubectl apply -f kubernetes/deployment.yaml'
                    sh 'kubectl apply -f kubernetes/service.yaml'

                    sh 'kubectl wait --for=condition=available deployment/flask-app --timeout=300s || true'

                    sh '''
                        kubectl get deployments
                        kubectl get pods
                        kubectl get services
                    '''
                }
            }
        }
        
        stage('Deployment Verification') {
            steps {
                script {
                    echo '========== Verifying Deployment =========='

                    sh '''
                        kubectl get pods -o wide
                        kubectl get services
                        kubectl get deployments
                        kubectl get pvc
                    '''

                    def minikubeIp = sh(script: 'minikube ip', returnStdout: true).trim()

                    echo """
                        ================================================
                        DEPLOYMENT SUCCESSFUL
                        ================================================
                        Application URL : http://${minikubeIp}:30080
                        ================================================
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '========== Pipeline Completed Successfully! =========='
        }
        failure {
            echo '========== Pipeline Failed! =========='
            sh 'docker logout || true'
        }
        always {
            sh 'docker system prune -f || true'
        }
    }
}
