import os

def generate_class_diagram(doc_structure, output_path):
    lines = ['@startuml', 'skinparam classAttributeIconSize 0', '']

    for cls in doc_structure.get('classes', []):
        class_name = cls['name']
        modifiers = cls.get('modifiers', [])
        
        stereotype = []
        if 'abstract' in modifiers:
            stereotype.append('abstract')
        if 'interface' in modifiers:
            stereotype.append('interface')
        if 'static' in modifiers:
            stereotype.append('static')
        
        stereo_str = f"<<{', '.join(stereotype)}>>" if stereotype else ''
        
        class_decl = f"class {class_name} {stereo_str}" if stereo_str else f"class {class_name}"
        lines.append(class_decl + ' {')

        for attr in cls.get('attributes', []):
            visibility = '-'
            if attr.get('access_modifier') == 'public':
                visibility = '+'
            elif attr.get('access_modifier') == 'protected':
                visibility = '#'
            attr_type = attr.get('type', '')
            attr_str = f"  {visibility} {attr_type} {attr['name']}" if attr_type else f"  {visibility} {attr['name']}"
            lines.append(attr_str)

        for method in cls.get('methods', []):
            visibility = '-'
            if method.get('access_modifier') == 'public':
                visibility = '+'
            elif method.get('access_modifier') == 'protected':
                visibility = '#'
            
            method_mods = method.get('modifiers', [])
            prefix = ''
            if 'static' in method_mods:
                prefix = '{static} '
            if 'abstract' in method_mods:
                prefix = '{abstract} '
            
            params = []
            for p in method.get('parameters', []):
                p_str = f"{p['name']}"
                if p.get('type'):
                    p_str += f": {p['type']}"
                params.append(p_str)
            
            ret_type = method.get('return_type', 'void')
            method_str = f"  {visibility} {prefix}{method['name']}({', '.join(params)}): {ret_type}"
            lines.append(method_str)

        lines.append('}')
        lines.append('')

        for parent in cls.get('inheritance', []):
            if isinstance(parent, dict):
                parent_name = parent.get('name', str(parent))
            else:
                parent_name = str(parent)
            if parent_name:
                if 'interface' in modifiers or (isinstance(parent, dict) and parent.get('is_interface')):
                    lines.append(f"{class_name} ..|> {parent_name}")
                else:
                    lines.append(f"{class_name} --|> {parent_name}")

    lines.append('')
    lines.append('@enduml')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return output_path
