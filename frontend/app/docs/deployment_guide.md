# Doctor Discovery Deployment Guide

## Overview

This guide provides instructions for deploying the Doctor Discovery application in various environments, from local development to production.

## Prerequisites

1. **System Requirements**
   - Python 3.8+
   - pip (Python package manager)
   - Git
   - Virtual environment tool (venv, conda, etc.)

2. **Dependencies**
   - Streamlit
   - pandas
   - plotly
   - httpx
   - pytest (for testing)

## Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd doctor-discovery
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   streamlit run main.py
   ```

## Docker Deployment

1. **Build Docker Image**
   ```bash
   docker build -t doctor-discovery .
   ```

2. **Run Container**
   ```bash
   docker run -p 8501:8501 doctor-discovery
   ```

3. **Docker Compose**
   ```yaml
   version: '3'
   services:
     app:
       build: .
       ports:
         - "8501:8501"
       environment:
         - API_BASE_URL=http://api:8000
       depends_on:
         - api
     api:
       image: doctor-discovery-api
       ports:
         - "8000:8000"
   ```

## Cloud Deployment

### AWS Elastic Beanstalk

1. **Create Application**
   ```bash
   eb init doctor-discovery
   ```

2. **Create Environment**
   ```bash
   eb create production
   ```

3. **Deploy**
   ```bash
   eb deploy
   ```

### Google Cloud Run

1. **Build Container**
   ```bash
   gcloud builds submit --tag gcr.io/<project-id>/doctor-discovery
   ```

2. **Deploy**
   ```bash
   gcloud run deploy doctor-discovery \
     --image gcr.io/<project-id>/doctor-discovery \
     --platform managed \
     --region <region>
   ```

### Azure App Service

1. **Create Web App**
   ```bash
   az webapp create --resource-group <resource-group> \
     --plan <app-service-plan> \
     --name <app-name> \
     --runtime "PYTHON:3.8"
   ```

2. **Deploy**
   ```bash
   az webapp up --name <app-name> \
     --resource-group <resource-group> \
     --runtime "PYTHON:3.8"
   ```

## Production Configuration

1. **Environment Variables**
   ```bash
   # .env file
   API_BASE_URL=https://api.example.com
   DEBUG=False
   LOG_LEVEL=INFO
   ```

2. **Security Settings**
   ```python
   # main.py
   st.set_page_config(
       page_title="Doctor Discovery",
       page_icon="👨‍⚕️",
       layout="wide",
       initial_sidebar_state="expanded",
       menu_items={
           'Get Help': None,
           'Report a bug': None,
           'About': None
       }
   )
   ```

3. **Logging Configuration**
   ```python
   # logging_config.py
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('app.log'),
           logging.StreamHandler()
       ]
   )
   ```

## Monitoring and Maintenance

1. **Health Checks**
   ```python
   # health_check.py
   async def check_health():
       try:
           response = await api_client.get_health()
           return response.status_code == 200
       except Exception:
           return False
   ```

2. **Performance Monitoring**
   - Set up application insights
   - Monitor API response times
   - Track error rates

3. **Backup Strategy**
   - Regular database backups
   - Configuration backups
   - Log rotation

## Scaling

1. **Horizontal Scaling**
   - Use load balancer
   - Multiple instances
   - Session management

2. **Vertical Scaling**
   - Increase resources
   - Optimize database
   - Cache configuration

## Security

1. **SSL/TLS**
   - Enable HTTPS
   - Configure certificates
   - Update security headers

2. **Access Control**
   - Implement authentication
   - Role-based access
   - API key management

3. **Data Protection**
   - Encrypt sensitive data
   - Secure storage
   - Regular security audits

## Troubleshooting

1. **Common Issues**
   - Connection errors
   - Performance problems
   - Memory issues

2. **Debugging Tools**
   - Log analysis
   - Performance profiling
   - Error tracking

3. **Recovery Procedures**
   - Backup restoration
   - Service recovery
   - Incident response

## Updates and Maintenance

1. **Version Control**
   - Semantic versioning
   - Changelog maintenance
   - Release notes

2. **Update Process**
   - Test in staging
   - Backup before update
   - Rollback plan

3. **Regular Maintenance**
   - Dependency updates
   - Security patches
   - Performance optimization

## Support

1. **Documentation**
   - API documentation
   - User guides
   - Troubleshooting guides

2. **Monitoring**
   - Error tracking
   - Usage analytics
   - Performance metrics

3. **Contact Information**
   - Support email
   - Issue tracker
   - Emergency contacts 