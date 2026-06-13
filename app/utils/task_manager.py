import os
import json
import threading
import time
from datetime import datetime
from app import tasks, tasks_lock
from app.config import Config
from app.utils.doc_processor import DocumentationProcessor
from app.utils.file_utils import generate_unique_id, cleanup_expired_previews, zip_directory

class TaskManager:
    def __init__(self):
        self.processor = DocumentationProcessor()

    def create_task(self, task_type, **kwargs):
        task_id = generate_unique_id()
        task = {
            'id': task_id,
            'type': task_type,
            'status': Config.TASK_STATUSES['PENDING'],
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'kwargs': kwargs
        }
        
        with tasks_lock:
            tasks[task_id] = task
        
        thread = threading.Thread(target=self._run_task, args=(task_id,), daemon=True)
        thread.start()
        
        return task_id, task

    def _run_task(self, task_id):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return
            task['status'] = Config.TASK_STATUSES['PROCESSING']
            task['started_at'] = datetime.now().isoformat()

        try:
            if task['type'] == 'generate':
                result = self._process_generate_task(task)
            elif task['type'] == 'compare':
                result = self._process_compare_task(task)
            else:
                raise ValueError(f"Unknown task type: {task['type']}")

            with tasks_lock:
                task['status'] = Config.TASK_STATUSES['COMPLETED']
                task['completed_at'] = datetime.now().isoformat()
                task['result'] = result

        except Exception as e:
            with tasks_lock:
                task['status'] = Config.TASK_STATUSES['FAILED']
                task['completed_at'] = datetime.now().isoformat()
                task['error'] = str(e)

    def _process_generate_task(self, task):
        task_id = task['id']
        zip_path = task['kwargs'].get('zip_path')
        project_name = task['kwargs'].get('project_name')

        if not zip_path or not os.path.exists(zip_path):
            raise ValueError('ZIP file not found')

        task_output_dir = os.path.join(Config.TEMP_OUTPUT_FOLDER, 'tasks', task_id)
        os.makedirs(task_output_dir, exist_ok=True)

        result = self.processor.process_zip(zip_path, project_name, output_dir=task_output_dir)
        
        download_zip_path = os.path.join(Config.TEMP_OUTPUT_FOLDER, 'tasks', f'{task_id}.zip')
        zip_directory(result['output_dir'], download_zip_path)
        
        preview_id, preview_dir = self.processor.create_preview(result['html_dir'])

        cleanup_expired_previews()

        task_prefix = f'tasks/{task_id}'
        return {
            'project_name': result['project_name'],
            'generated_at': result['generated_at'],
            'task_id': task_id,
            'json_path': f'{task_prefix}/documentation.json',
            'plantuml_path': f'{task_prefix}/class_diagram.puml',
            'download_zip': f'tasks/{task_id}.zip',
            'preview_id': preview_id,
            'preview_url': f'/preview/{preview_id}/index.html',
            'total_files': result['doc_structure']['metadata']['total_files'],
            'modules_count': len(result['doc_structure']['modules']),
            'classes_count': len(result['doc_structure']['classes']),
            'functions_count': len(result['doc_structure']['functions'])
        }

    def _process_compare_task(self, task):
        task_id = task['id']
        zip_path_v1 = task['kwargs'].get('zip_path_v1')
        zip_path_v2 = task['kwargs'].get('zip_path_v2')
        name_v1 = task['kwargs'].get('name_v1', 'Version 1')
        name_v2 = task['kwargs'].get('name_v2', 'Version 2')

        if not zip_path_v1 or not os.path.exists(zip_path_v1):
            raise ValueError('ZIP file for version 1 not found')
        if not zip_path_v2 or not os.path.exists(zip_path_v2):
            raise ValueError('ZIP file for version 2 not found')

        task_output_dir = os.path.join(Config.TEMP_OUTPUT_FOLDER, 'tasks', task_id)
        os.makedirs(task_output_dir, exist_ok=True)

        result = self.processor.compare_versions(
            zip_path_v1, zip_path_v2, name_v1, name_v2, output_dir=task_output_dir
        )
        
        download_zip_path = os.path.join(Config.TEMP_OUTPUT_FOLDER, 'tasks', f'{task_id}.zip')
        zip_directory(result['output_dir'], download_zip_path)

        task_prefix = f'tasks/{task_id}'
        return {
            'generated_at': result['generated_at'],
            'task_id': task_id,
            'report_json': f'{task_prefix}/comparison_report.json',
            'report_html': f'{task_prefix}/comparison_report.html',
            'download_zip': f'tasks/{task_id}.zip',
            'v1_doc': f'{task_prefix}/v1/documentation.json',
            'v2_doc': f'{task_prefix}/v2/documentation.json',
            'v1_plantuml': f'{task_prefix}/v1/class_diagram.puml',
            'v2_plantuml': f'{task_prefix}/v2/class_diagram.puml',
            'summary': result['report']['summary'],
            'total_changes': result['report']['summary']['total_changes']
        }

    def get_task_status(self, task_id):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return None
            return {
                'id': task['id'],
                'type': task['type'],
                'status': task['status'],
                'created_at': task['created_at'],
                'started_at': task['started_at'],
                'completed_at': task['completed_at'],
                'result': task['result'],
                'error': task['error']
            }

    def cleanup_old_tasks(self, max_age_hours=24):
        import shutil
        from datetime import datetime, timedelta
        
        now = datetime.now()
        to_delete = []
        
        with tasks_lock:
            for task_id, task in tasks.items():
                if task['completed_at']:
                    completed_at = datetime.fromisoformat(task['completed_at'])
                    if now - completed_at > timedelta(hours=max_age_hours):
                        to_delete.append(task_id)
            
            for task_id in to_delete:
                del tasks[task_id]
