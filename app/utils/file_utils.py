import os
import zipfile
import shutil
import uuid
import hashlib
from datetime import datetime, timedelta
from app.config import Config

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def extract_zip(zip_path, extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

def get_supported_files(directory):
    supported_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            for lang, exts in Config.SUPPORTED_LANGUAGES.items():
                if ext in exts:
                    supported_files.append({
                        'path': file_path,
                        'relative_path': os.path.relpath(file_path, directory),
                        'language': lang,
                        'extension': ext
                    })
                    break
    return supported_files

def read_file_content(file_path):
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
        return f.read()

def generate_unique_id():
    return str(uuid.uuid4())

def generate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_temp_dir(prefix='docgen_'):
    temp_dir = os.path.join(Config.TEMP_OUTPUT_FOLDER, prefix + generate_unique_id())
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def cleanup_expired_previews():
    now = datetime.now()
    expiry_hours = Config.PREVIEW_EXPIRY_HOURS
    for item in os.listdir(Config.PREVIEW_FOLDER):
        item_path = os.path.join(Config.PREVIEW_FOLDER, item)
        if os.path.isdir(item_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            if now - mtime > timedelta(hours=expiry_hours):
                shutil.rmtree(item_path, ignore_errors=True)

def zip_directory(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    return output_zip
