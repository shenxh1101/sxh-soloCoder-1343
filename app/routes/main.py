import os
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, abort, send_file, current_app
from werkzeug.utils import secure_filename
from app.utils.file_utils import allowed_file, generate_unique_id, cleanup_expired_previews
from app.config import Config

main_bp = Blueprint('main', __name__)

task_manager = None

def get_task_manager():
    global task_manager
    if task_manager is None:
        from app.utils.task_manager import TaskManager
        task_manager = TaskManager()
    return task_manager

@main_bp.route('/')
def index():
    return render_template('upload.html')

@main_bp.route('/preview/<preview_id>/')
@main_bp.route('/preview/<preview_id>/<path:filename>')
def preview(preview_id, filename='index.html'):
    preview_dir = os.path.join(Config.PREVIEW_FOLDER, preview_id)
    if not os.path.exists(preview_dir):
        abort(404)
    
    from datetime import datetime, timedelta
    mtime = datetime.fromtimestamp(os.path.getmtime(preview_dir))
    if datetime.now() - mtime > timedelta(hours=Config.PREVIEW_EXPIRY_HOURS):
        import shutil
        shutil.rmtree(preview_dir, ignore_errors=True)
        abort(404)
    
    return send_from_directory(preview_dir, filename)

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    base_dir = os.path.abspath(Config.TEMP_OUTPUT_FOLDER)
    file_path = os.path.abspath(os.path.join(base_dir, filename))
    
    if not file_path.startswith(base_dir):
        abort(400, 'Invalid path')
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404, 'File not found')
    
    download_name = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=download_name)

@main_bp.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    if not allowed_file(file.filename):
        return {'error': 'Only ZIP files are allowed'}, 400
    
    project_name = request.form.get('project_name', secure_filename(file.filename))
    if project_name:
        project_name = secure_filename(project_name)
    
    filename = secure_filename(file.filename)
    unique_id = generate_unique_id()
    zip_path = os.path.join(Config.UPLOAD_FOLDER, f"{unique_id}_{filename}")
    file.save(zip_path)
    
    tm = get_task_manager()
    task_id, task = tm.create_task(
        'generate',
        zip_path=zip_path,
        project_name=project_name
    )
    
    return {
        'task_id': task_id,
        'status': task['status'],
        'status_url': url_for('api.task_status', task_id=task_id, _external=True)
    }, 202

@main_bp.route('/compare', methods=['POST'])
def compare():
    if 'file_v1' not in request.files or 'file_v2' not in request.files:
        return {'error': 'Two files are required'}, 400
    
    file_v1 = request.files['file_v1']
    file_v2 = request.files['file_v2']
    
    if file_v1.filename == '' or file_v2.filename == '':
        return {'error': 'Both files must be selected'}, 400
    
    if not allowed_file(file_v1.filename) or not allowed_file(file_v2.filename):
        return {'error': 'Only ZIP files are allowed'}, 400
    
    name_v1 = request.form.get('name_v1', secure_filename(file_v1.filename))
    name_v2 = request.form.get('name_v2', secure_filename(file_v2.filename))
    
    unique_id = generate_unique_id()
    zip_path_v1 = os.path.join(Config.UPLOAD_FOLDER, f"{unique_id}_v1_{secure_filename(file_v1.filename)}")
    zip_path_v2 = os.path.join(Config.UPLOAD_FOLDER, f"{unique_id}_v2_{secure_filename(file_v2.filename)}")
    
    file_v1.save(zip_path_v1)
    file_v2.save(zip_path_v2)
    
    tm = get_task_manager()
    task_id, task = tm.create_task(
        'compare',
        zip_path_v1=zip_path_v1,
        zip_path_v2=zip_path_v2,
        name_v1=name_v1,
        name_v2=name_v2
    )
    
    return {
        'task_id': task_id,
        'status': task['status'],
        'status_url': url_for('api.task_status', task_id=task_id, _external=True)
    }, 202

@main_bp.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

@main_bp.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500
