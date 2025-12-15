pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKERHUB_USERNAME = 'zumarr'
        IMAGE_NAME = 'devops-flask-app'
        IMAGE_TAG = "${BUILD_NUMBER}"

        // ✅ FIX: Jenkins Kubernetes access
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
                    echo 'Code fetched successfully!'
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
                    echo 'Docker image built successfully!'

                    sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'

                    sh """
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                    """
                    echo 'Docker image pushed to DockerHub successfully!'
                }
            }
        }
        
        stage('Kubernetes Deployment') {
            steps {
                script {
                    echo '========== Stage 3: Deploying to Kubernetes =========='

                    // Verify Kubernetes access
                    sh 'kubectl get nodes'

                    // Create monitoring namespace
                    sh '''
                        kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f - || true
                    '''

                    // Apply MySQL resources
                    sh 'kubectl apply -f kubernetes/mysql-configmap.yaml'
                    sh 'kubectl apply -f kubernetes/pvc.yaml'
                    sh 'kubectl apply -f kubernetes/mysql-deployment.yaml'
                    sh 'kubectl apply -f kubernetes/mysql-service.yaml'

                    echo 'Waiting for MySQL to be ready...'
                    sh 'kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s || true'
                    sleep(time: 30, unit: 'SECONDS')

                    // Update Flask image
                    sh """
                        sed -i 's|image:.*|image: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}|g' kubernetes/deployment.yaml
                    """

                    // Deploy Flask app
                    sh 'kubectl apply -f kubernetes/deployment.yaml'
                    sh 'kubectl apply -f kubernetes/service.yaml'

                    echo 'Waiting for Flask deployment...'
                    sh 'kubectl wait --for=condition=available deployment/flask-app --timeout=300s || true'

                    sh 'kubectl get deployments'
                    sh 'kubectl get pods'
                    sh 'kubectl get services'

                    echo 'Application deployed to Kubernetes successfully!'
                }
            }
        }
        
        stage('Prometheus & Grafana Setup') {
            steps {
                script {
                    echo '========== Stage 4: Setting up Monitoring =========='

                    sh 'kubectl apply -f monitoring/prometheus-config.yaml'
                    sh 'kubectl apply -f monitoring/grafana-config.yaml'

                    echo 'Waiting for Prometheus...'
                    sh 'kubectl wait --for=condition=available deployment/prometheus -n monitoring --timeout=300s || true'

                    echo 'Waiting for Grafana...'
                    sh 'kubectl wait --for=condition=available deployment/grafana -n monitoring --timeout=300s || true'

                    sh 'kubectl get all -n monitoring'
                    echo 'Monitoring setup completed successfully!'
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
                        kubectl get all -n monitoring
                    '''

                    def minikubeIp = sh(script: 'minikube ip', returnStdout: true).trim()

                    echo """
                            ================================================
                            DEPLOYMENT SUCCESSFUL
                            ================================================
                            Application URL : http://${minikubeIp}:30080
                            Prometheus URL  : http://${minikubeIp}:30090
                            Grafana URL     : http://${minikubeIp}:30030

                            Grafana Login:
                            Username: admin
                            Password: admin123
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
