import json
import os
from datetime import datetime

def build_document_structure(parsed_files, project_name='Unknown'):
    languages = set()
    total_classes = 0
    total_functions = 0
    total_interfaces = 0
    
    for file_data in parsed_files:
        languages.add(file_data.get('language', 'unknown'))
        total_classes += len(file_data.get('classes', []))
        total_functions += len(file_data.get('functions', []))
        total_interfaces += len(file_data.get('interfaces', []))
    
    structure = {
        'metadata': {
            'project_name': project_name,
            'generated_at': datetime.now().isoformat(),
            'version': '1.0',
            'total_files': len(parsed_files),
            'file_count': len(parsed_files),
            'language_count': len(languages),
            'languages': list(languages),
            'total_classes': total_classes,
            'total_functions': total_functions,
            'total_interfaces': total_interfaces
        },
        'files': parsed_files,
        'modules': [],
        'classes': [],
        'interfaces': [],
        'functions': [],
        'package_structure': {}
    }

    packages = {}

    for file_data in parsed_files:
        rel_path = file_data['relative_path']
        parts = rel_path.replace('\\', '/').split('/')
        module_name = '.'.join(parts[:-1]) if len(parts) > 1 else ''
        file_name = parts[-1]

        structure['modules'].append({
            'name': file_name,
            'full_name': rel_path,
            'module_path': module_name,
            'language': file_data['language'],
            'path': rel_path,
            'description': file_data.get('module_description', ''),
            'author': file_data.get('author', ''),
            'version': file_data.get('version', ''),
            'classes': file_data.get('classes', []),
            'functions': file_data.get('functions', []),
            'imports': file_data.get('imports', [])
        })

        for cls in file_data.get('classes', []):
            class_info = {
                'name': cls['name'],
                'module': rel_path,
                'language': file_data['language'],
                'description': cls.get('description', ''),
                'modifiers': cls.get('modifiers', []),
                'inheritance': cls.get('inheritance', []),
                'methods': cls.get('methods', []),
                'attributes': cls.get('attributes', []),
                'author': cls.get('author', file_data.get('author', '')),
                'version': cls.get('version', file_data.get('version', ''))
            }
            structure['classes'].append(class_info)

        for func in file_data.get('functions', []):
            if func.get('is_method', False):
                continue
            func_info = {
                'name': func['name'],
                'module': rel_path,
                'language': file_data['language'],
                'signature': func.get('signature', ''),
                'description': func.get('description', ''),
                'parameters': func.get('parameters', []),
                'return_type': func.get('return_type', ''),
                'return_description': func.get('return_description', ''),
                'exceptions': func.get('exceptions', []),
                'examples': func.get('examples', []),
                'author': func.get('author', file_data.get('author', '')),
                'version': func.get('version', file_data.get('version', ''))
            }
            structure['functions'].append(func_info)

        current = packages
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = {'type': 'file', 'path': rel_path, 'language': file_data['language']}
            else:
                if part not in current:
                    current[part] = {'type': 'directory', 'children': {}}
                current = current[part]['children']

    structure['package_structure'] = packages

    return structure

def save_json_document(structure, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    return output_path

def load_json_document(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)
