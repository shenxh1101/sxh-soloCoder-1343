import json
from datetime import datetime


def _is_public_method(method, scope='public'):
    if scope == 'full':
        return True
    access = method.get('access_modifier')
    name = method.get('name', '')
    if access in ('private', 'protected'):
        return False
    if name.startswith('__') and not name.endswith('__'):
        return False
    if name.startswith('_') and not name.startswith('__'):
        return False
    if access == 'package-private':
        return False
    return True


def _is_public_class(cls, scope='public'):
    if scope == 'full':
        return True
    modifiers = cls.get('modifiers', [])
    if 'private' in modifiers or 'protected' in modifiers:
        return False
    access = cls.get('access_modifier')
    if access in ('private', 'protected', 'package-private'):
        return False
    name = cls.get('name', '')
    if scope == 'public' and name.startswith('_') and not name.startswith('__'):
        return False
    return True


def _is_public_function(func, scope='public'):
    if scope == 'full':
        return True
    access = func.get('access_modifier')
    if access in ('private', 'protected'):
        return False
    name = func.get('name', '')
    if name.startswith('__') and not name.endswith('__'):
        return False
    if name.startswith('_') and not name.startswith('__'):
        return False
    if access == 'package-private':
        return False
    return True


def _get_class_signatures(doc, scope='public'):
    signatures = {}
    for cls in doc.get('classes', []):
        if not _is_public_class(cls, scope):
            continue
        key = f"{cls['module']}::{cls['name']}"
        methods = []
        for method in cls.get('methods', []):
            if not _is_public_method(method, scope):
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


def _get_function_signatures(doc, scope='public'):
    signatures = {}
    for func in doc.get('functions', []):
        if not _is_public_function(func, scope):
            continue
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


def compare_versions(doc_v1, doc_v2, scope='public'):
    classes_v1 = _get_class_signatures(doc_v1, scope)
    classes_v2 = _get_class_signatures(doc_v2, scope)
    functions_v1 = _get_function_signatures(doc_v1, scope)
    functions_v2 = _get_function_signatures(doc_v2, scope)

    changes_key = 'public_api_changes' if scope == 'public' else 'all_changes'

    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'v1_project': doc_v1['metadata']['project_name'],
            'v2_project': doc_v2['metadata']['project_name'],
            'v1_generated_at': doc_v1['metadata']['generated_at'],
            'v2_generated_at': doc_v2['metadata']['generated_at'],
            'comparison_scope': scope,
            'scope_description': 'Public API only (excludes private, protected, package-private, and internal members)' if scope == 'public' else 'Full comparison (includes all classes, methods, and functions)'
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
        changes_key: []
    }

    all_class_keys = set(classes_v1.keys()) | set(classes_v2.keys())
    for key in all_class_keys:
        if key in classes_v1 and key not in classes_v2:
            cls = classes_v1[key]
            report['classes']['removed'].append(cls)
            report[changes_key].append({
                'type': 'class_removed',
                'name': cls['name'],
                'module': cls['module'],
                'message': f"Class '{cls['name']}' has been removed from module '{cls['module']}'"
            })
        elif key not in classes_v1 and key in classes_v2:
            cls = classes_v2[key]
            report['classes']['added'].append(cls)
            report[changes_key].append({
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
                    report[changes_key].append({
                        'type': 'method_removed',
                        'class': cls1['name'],
                        'module': cls1['module'],
                        'method': method,
                        'message': f"Method '{method}' has been removed from class '{cls1['name']}'"
                    })
                for method in methods_added:
                    report[changes_key].append({
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
            report[changes_key].append({
                'type': 'function_removed',
                'name': func['name'],
                'module': func['module'],
                'message': f"Function '{func['name']}' has been removed from module '{func['module']}'"
            })
        elif key not in functions_v1 and key in functions_v2:
            func = functions_v2[key]
            report['functions']['added'].append(func)
            report[changes_key].append({
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
                report[changes_key].append({
                    'type': 'function_modified',
                    'name': func1['name'],
                    'module': func1['module'],
                    'old_signature': func1['signature'],
                    'new_signature': func2['signature'],
                    'message': f"Function '{func1['name']}' signature changed: {func1['signature']} -> {func2['signature']}"
                })

    report['summary'] = {
        'total_changes': len(report[changes_key]),
        'classes_added': len(report['classes']['added']),
        'classes_removed': len(report['classes']['removed']),
        'classes_modified': len(report['classes']['modified']),
        'functions_added': len(report['functions']['added']),
        'functions_removed': len(report['functions']['removed']),
        'functions_modified': len(report['functions']['modified'])
    }

    return report
