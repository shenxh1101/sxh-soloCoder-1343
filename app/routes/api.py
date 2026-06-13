import os
from flask import Blueprint, request, jsonify, url_for
from werkzeug.utils import secure_filename
from app.utils.file_utils import allowed_file, generate_unique_id
from app.config import Config

api_bp = Blueprint('api', __name__)

task_manager = None

def get_task_manager():
    global task_manager
    if task_manager is None:
        from app.utils.task_manager import TaskManager
        task_manager = TaskManager()
    return task_manager

@api_bp.route('/tasks', methods=['POST'])
def create_task():
    task_type = request.json.get('type') if request.is_json else request.form.get('type')
    
    if not task_type:
        return jsonify({'error': 'Task type is required'}), 400
    
    if task_type == 'generate':
        return _create_generate_task()
    elif task_type == 'compare':
        return _create_compare_task()
    else:
        return jsonify({'error': f'Unknown task type: {task_type}'}), 400

def _create_generate_task():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only ZIP files are allowed'}), 400
    
    project_name = request.form.get('project_name') or secure_filename(file.filename)
    
    unique_id = generate_unique_id()
    filename = secure_filename(file.filename)
    zip_path = os.path.join(Config.UPLOAD_FOLDER, f"{unique_id}_{filename}")
    file.save(zip_path)
    
    tm = get_task_manager()
    task_id, task = tm.create_task(
        'generate',
        zip_path=zip_path,
        project_name=project_name
    )
    
    return jsonify({
        'task_id': task_id,
        'type': 'generate',
        'status': task['status'],
        'created_at': task['created_at'],
        'status_url': url_for('api.task_status', task_id=task_id, _external=True)
    }), 202

def _create_compare_task():
    file_v1 = request.files.get('file_v1')
    file_v2 = request.files.get('file_v2')
    
    if not file_v1 or not file_v2:
        return jsonify({'error': 'Two files are required'}), 400
    
    if file_v1.filename == '' or file_v2.filename == '':
        return jsonify({'error': 'Both files must be selected'}), 400
    
    if not allowed_file(file_v1.filename) or not allowed_file(file_v2.filename):
        return jsonify({'error': 'Only ZIP files are allowed'}), 400
    
    name_v1 = request.form.get('name_v1') or secure_filename(file_v1.filename)
    name_v2 = request.form.get('name_v2') or secure_filename(file_v2.filename)
    scope = request.form.get('scope', 'public')
    if scope not in ('public', 'full'):
        scope = 'public'
    
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
        name_v2=name_v2,
        scope=scope
    )
    
    return jsonify({
        'task_id': task_id,
        'type': 'compare',
        'status': task['status'],
        'created_at': task['created_at'],
        'scope': scope,
        'status_url': url_for('api.task_status', task_id=task_id, _external=True)
    }), 202

@api_bp.route('/tasks/<task_id>', methods=['GET'])
def task_status(task_id):
    tm = get_task_manager()
    status = tm.get_task_status(task_id)
    
    if not status:
        return jsonify({'error': 'Task not found'}), 404
    
    response = {
        'task_id': status['id'],
        'type': status['type'],
        'status': status['status'],
        'created_at': status['created_at'],
        'started_at': status['started_at'],
        'completed_at': status['completed_at']
    }
    
    if status['error']:
        response['error'] = status['error']
    
    if status['result']:
        result = dict(status['result'])
        response['result'] = result
        
        if 'artifacts' in result:
            for artifact in result['artifacts']:
                if 'path' in artifact:
                    artifact['download_url'] = url_for(
                        'main.download_file',
                        filename=artifact['path'],
                        _external=True
                    )
        
        if status['type'] == 'generate':
            if 'json_path' in result:
                result['json_url'] = url_for(
                    'main.download_file',
                    filename=result['json_path'],
                    _external=True
                )
            if 'plantuml_path' in result:
                result['plantuml_url'] = url_for(
                    'main.download_file',
                    filename=result['plantuml_path'],
                    _external=True
                )
            if 'download_zip' in result:
                result['download_url'] = url_for(
                    'main.download_file',
                    filename=result['download_zip'],
                    _external=True
                )
            if 'preview_id' in result:
                result['preview_url'] = url_for(
                    'main.preview',
                    preview_id=result['preview_id'],
                    filename='index.html',
                    _external=True
                )
        
        elif status['type'] == 'compare':
            if 'report_json' in result:
                result['report_json_url'] = url_for(
                    'main.download_file',
                    filename=result['report_json'],
                    _external=True
                )
            if 'report_html' in result:
                result['report_html_url'] = url_for(
                    'main.download_file',
                    filename=result['report_html'],
                    _external=True
                )
            if 'download_zip' in result:
                result['download_url'] = url_for(
                    'main.download_file',
                    filename=result['download_zip'],
                    _external=True
                )
            if 'v1_doc' in result:
                result['v1_doc_url'] = url_for(
                    'main.download_file',
                    filename=result['v1_doc'],
                    _external=True
                )
            if 'v2_doc' in result:
                result['v2_doc_url'] = url_for(
                    'main.download_file',
                    filename=result['v2_doc'],
                    _external=True
                )
            if 'v1_plantuml' in result:
                result['v1_plantuml_url'] = url_for(
                    'main.download_file',
                    filename=result['v1_plantuml'],
                    _external=True
                )
            if 'v2_plantuml' in result:
                result['v2_plantuml_url'] = url_for(
                    'main.download_file',
                    filename=result['v2_plantuml'],
                    _external=True
                )
    
    return jsonify(response), 200

@api_bp.route('/tasks', methods=['GET'])
def list_tasks():
    from app import tasks, tasks_lock
    with tasks_lock:
        task_list = []
        for task_id, task in tasks.items():
            task_list.append({
                'task_id': task_id,
                'type': task['type'],
                'status': task['status'],
                'created_at': task['created_at'],
                'completed_at': task['completed_at']
            })
    return jsonify({'tasks': task_list}), 200

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Code Documentation Generator API',
        'supported_languages': ['python', 'javascript', 'java', 'cpp'],
        'version': '1.0'
    }), 200
