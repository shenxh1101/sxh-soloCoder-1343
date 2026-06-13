import json
from datetime import datetime

PUBLIC_ACCESS = {'public', 'package-private', None}

def _is_public_method(method):
    access = method.get('access_modifier')
    if access in PUBLIC_ACCESS:
        return True
    name = method.get('name', '')
    if name.startswith('_') and not name.startswith('__') and not name.endswith('__'):
        return False
    if name.startswith('__') and not name.endswith('__'):
        return False
    return access not in ('private', 'protected')

def _is_public_class(cls):
    modifiers = cls.get('modifiers', [])
    if 'private' in modifiers or 'protected' in modifiers:
        return False
    return True

def _get_class_signatures(doc):
    signatures = {}
    for cls in doc.get('classes', []):
        if not _is_public_class(cls):
            continue
        key = f"{cls['module']}::{cls['name']}"
        methods = []
        for method in cls.get('methods', []):
            if not _is_public_method(method):
                continue
            params = ','.join([f"{p['type'] if p.get('type') else 'any'} {p['name']}" for p in method.get('parameters', [])])
            ret_type = method.get('return_type', 'void')
            methods.append(f"{ret_type} {method['name']}({params})")
        signatures[key] = {
            'name': cls['name'],
            'module': cls['module'],
            'methods': sorted(methods),
            'inheritance': cls.get('inheritance', []),
            'modifiers': cls.get('modifiers', [])
        }
    return signatures

def _get_function_signatures(doc):
    signatures = {}
    for func in doc.get('functions', []):
        key = f"{func['module']}::{func['name']}"
        params = ','.join([f"{p['type'] if p.get('type') else 'any'} {p['name']}" for p in func.get('parameters', [])])
        ret_type = func.get('return_type', 'void')
        signatures[key] = {
            'name': func['name'],
            'module': func['module'],
            'signature': f"{ret_type} {func['name']}({params})",
            'return_type': ret_type
        }
    return signatures

def compare_versions(doc_v1, doc_v2):
    classes_v1 = _get_class_signatures(doc_v1)
    classes_v2 = _get_class_signatures(doc_v2)
    functions_v1 = _get_function_signatures(doc_v1)
    functions_v2 = _get_function_signatures(doc_v2)

    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'v1_project': doc_v1['metadata']['project_name'],
            'v2_project': doc_v2['metadata']['project_name'],
            'v1_generated_at': doc_v1['metadata']['generated_at'],
            'v2_generated_at': doc_v2['metadata']['generated_at']
        },
        'classes': {
            'added': [],
            'removed': [],
            'modified': []
        },
        'functions': {
            'added': [],
            'removed': [],
            'modified': []
        },
        'public_api_changes': []
    }

    all_class_keys = set(classes_v1.keys()) | set(classes_v2.keys())
    for key in all_class_keys:
        if key in classes_v1 and key not in classes_v2:
            cls = classes_v1[key]
            report['classes']['removed'].append(cls)
            report['public_api_changes'].append({
                'type': 'class_removed',
                'name': cls['name'],
                'module': cls['module'],
                'message': f"Class '{cls['name']}' has been removed from module '{cls['module']}'"
            })
        elif key not in classes_v1 and key in classes_v2:
            cls = classes_v2[key]
            report['classes']['added'].append(cls)
            report['public_api_changes'].append({
                'type': 'class_added',
                'name': cls['name'],
                'module': cls['module'],
                'message': f"New class '{cls['name']}' has been added to module '{cls['module']}'"
            })
        else:
            cls1, cls2 = classes_v1[key], classes_v2[key]
            methods_removed = set(cls1['methods']) - set(cls2['methods'])
            methods_added = set(cls2['methods']) - set(cls1['methods'])
            if methods_removed or methods_added or cls1['inheritance'] != cls2['inheritance']:
                report['classes']['modified'].append({
                    'name': cls1['name'],
                    'module': cls1['module'],
                    'methods_added': list(methods_added),
                    'methods_removed': list(methods_removed),
                    'inheritance_changed': cls1['inheritance'] != cls2['inheritance'],
                    'old_inheritance': cls1['inheritance'],
                    'new_inheritance': cls2['inheritance']
                })
                for method in methods_removed:
                    report['public_api_changes'].append({
                        'type': 'method_removed',
                        'class': cls1['name'],
                        'module': cls1['module'],
                        'method': method,
                        'message': f"Method '{method}' has been removed from class '{cls1['name']}'"
                    })
                for method in methods_added:
                    report['public_api_changes'].append({
                        'type': 'method_added',
                        'class': cls1['name'],
                        'module': cls1['module'],
                        'method': method,
                        'message': f"New method '{method}' has been added to class '{cls1['name']}'"
                    })

    all_func_keys = set(functions_v1.keys()) | set(functions_v2.keys())
    for key in all_func_keys:
        if key in functions_v1 and key not in functions_v2:
            func = functions_v1[key]
            report['functions']['removed'].append(func)
            report['public_api_changes'].append({
                'type': 'function_removed',
                'name': func['name'],
                'module': func['module'],
                'message': f"Function '{func['name']}' has been removed from module '{func['module']}'"
            })
        elif key not in functions_v1 and key in functions_v2:
            func = functions_v2[key]
            report['functions']['added'].append(func)
            report['public_api_changes'].append({
                'type': 'function_added',
                'name': func['name'],
                'module': func['module'],
                'message': f"New function '{func['name']}' has been added to module '{func['module']}'"
            })
        else:
            func1, func2 = functions_v1[key], functions_v2[key]
            if func1['signature'] != func2['signature']:
                report['functions']['modified'].append({
                    'name': func1['name'],
                    'module': func1['module'],
                    'old_signature': func1['signature'],
                    'new_signature': func2['signature']
                })
                report['public_api_changes'].append({
                    'type': 'function_modified',
                    'name': func1['name'],
                    'module': func1['module'],
                    'old_signature': func1['signature'],
                    'new_signature': func2['signature'],
                    'message': f"Function '{func1['name']}' signature changed: {func1['signature']} → {func2['signature']}"
                })

    report['summary'] = {
        'total_changes': len(report['public_api_changes']),
        'classes_added': len(report['classes']['added']),
        'classes_removed': len(report['classes']['removed']),
        'classes_modified': len(report['classes']['modified']),
        'functions_added': len(report['functions']['added']),
        'functions_removed': len(report['functions']['removed']),
        'functions_modified': len(report['functions']['modified'])
    }

    return report
