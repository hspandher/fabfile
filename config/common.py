import os
from fabric.api import run

QA_CODE_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deploy_dir/qa_shine')
QA_BRANCH_NAME = 'quality_assurance'

STAGING_CODE_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deploy_dir/staging_shine')
STAGING_BRANCH_NAME = 'staging'

EMAIL_HOST = '172.22.65.145'
EMAIL_PORT = 25
SERVER_EMAIL = 'Shine Deployment <noreply@noone.com>'

PROJECT_NAME = 'fabfile'
