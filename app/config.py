import os
import tempfile
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    TEMP_OUTPUT_FOLDER = os.path.join(BASE_DIR, 'temp_output')
    PREVIEW_FOLDER = os.path.join(BASE_DIR, 'preview')
    
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    
    ALLOWED_EXTENSIONS = {'zip'}
    
    PREVIEW_EXPIRY_HOURS = 1
    
    TASK_STATUSES = {
        'PENDING': 'pending',
        'PROCESSING': 'processing',
        'COMPLETED': 'completed',
        'FAILED': 'failed'
    }
    
    SUPPORTED_LANGUAGES = {
        'python': ['.py'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.cc', '.c', '.h', '.hpp', '.cxx']
    }

    @staticmethod
    def init_app(app):
        for folder in [Config.UPLOAD_FOLDER, Config.TEMP_OUTPUT_FOLDER, Config.PREVIEW_FOLDER]:
            os.makedirs(folder, exist_ok=True)
