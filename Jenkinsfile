pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKERHUB_USERNAME = 'zumarr'
        IMAGE_NAME = 'devops-flask-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        KUBECONFIG = '/home/ubuntu/.kube/config'
    }
    
    stages {
        stage('Code Fetch') {
            steps {
                script {
                    echo '========== Stage 1: Fetching Code from GitHub =========='
                    // Clean workspace
                    cleanWs()
                    
                    // Checkout code from GitHub
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
                    
                    // Build Docker image
                    sh """
                        docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker tag ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
                    """
                    
                    echo 'Docker image built successfully!'
                    
                    // Login to DockerHub
                    sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
                    
                    // Push to DockerHub
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
                    
                    // Create monitoring namespace if not exists
                    sh '''
                        kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
                    '''
                    
                    // Apply MySQL ConfigMap
                    sh 'kubectl apply -f k8s/mysql-configmap.yaml'
                    
                    // Apply PVC
                    sh 'kubectl apply -f k8s/pvc.yaml'
                    
                    // Deploy MySQL
                    sh 'kubectl apply -f k8s/mysql-deployment.yaml'
                    sh 'kubectl apply -f k8s/mysql-service.yaml'
                    
                    // Wait for MySQL to be ready
                    echo 'Waiting for MySQL to be ready...'
                    sh 'kubectl wait --for=condition=ready pod -l app=mysql --timeout=300s || true'
                    sleep(time: 30, unit: 'SECONDS')
                    
                    // Update deployment with new image
                    sh """
                        sed -i 's|image:.*|image: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}|g' k8s/deployment.yaml
                    """
                    
                    // Deploy Flask application
                    sh 'kubectl apply -f k8s/deployment.yaml'
                    sh 'kubectl apply -f k8s/service.yaml'
                    
                    // Wait for deployment to be ready
                    echo 'Waiting for application deployment to be ready...'
                    sh 'kubectl wait --for=condition=available deployment/flask-app --timeout=300s || true'
                    
                    // Get deployment status
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
                    
                    // Deploy Prometheus
                    sh 'kubectl apply -f monitoring/prometheus-config.yaml'
                    
                    // Deploy Grafana
                    sh 'kubectl apply -f monitoring/grafana-config.yaml'
                    
                    // Wait for Prometheus and Grafana to be ready
                    echo 'Waiting for Prometheus to be ready...'
                    sh 'kubectl wait --for=condition=available deployment/prometheus -n monitoring --timeout=300s || true'
                    
                    echo 'Waiting for Grafana to be ready...'
                    sh 'kubectl wait --for=condition=available deployment/grafana -n monitoring --timeout=300s || true'
                    
                    // Get monitoring status
                    sh 'kubectl get all -n monitoring'
                    
                    echo 'Monitoring setup completed successfully!'
                }
            }
        }
        
        stage('Deployment Verification') {
            steps {
                script {
                    echo '========== Verifying Deployment =========='
                    
                    // Get all resources
                    sh '''
                        echo "=== Pods ==="
                        kubectl get pods -o wide
                        
                        echo "=== Services ==="
                        kubectl get services
                        
                        echo "=== Deployments ==="
                        kubectl get deployments
                        
                        echo "=== PVCs ==="
                        kubectl get pvc
                        
                        echo "=== Monitoring Namespace ==="
                        kubectl get all -n monitoring
                    '''
                    
                    // Get Minikube IP for access URLs
                    def minikubeIp = sh(script: 'minikube ip', returnStdout: true).trim()
                    
                    echo """
                    ============================================
                    DEPLOYMENT SUCCESSFUL!
                    ============================================
                    Application URL: http://${minikubeIp}:30080
                    Prometheus URL: http://${minikubeIp}:30090
                    Grafana URL: http://${minikubeIp}:30030
                    
                    Grafana Credentials:
                    Username: admin
                    Password: admin123
                    ============================================
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
            // Cleanup on failure
            sh '''
                docker logout || true
            '''
        }
        always {
            // Cleanup Docker images to save space
            sh '''
                docker system prune -f || true
            '''
        }
    }
}