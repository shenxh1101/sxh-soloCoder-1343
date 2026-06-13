import re
import ast
from app.parsers.base_parser import BaseParser

class PythonParser(BaseParser):
    language = 'python'

    def __init__(self):
        super().__init__()
        self.docblock_patterns = [
            r'"""(.*?)"""',
            r"'''(.*?)'''",
        ]

    def parse(self, content, relative_path):
        result = {
            'language': 'python',
            'relative_path': relative_path,
            'module_description': '',
            'author': '',
            'version': '',
            'classes': [],
            'functions': [],
            'imports': []
        }

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return result

        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            result['module_description'] = self._extract_description(module_docstring)
            tags = self._extract_docblock_tags(module_docstring)
            result['author'] = tags.get('author', '')
            result['version'] = tags.get('version', '')

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'name': alias.name,
                        'asname': alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'name': f"{module}.{alias.name}" if module else alias.name,
                        'asname': alias.asname,
                        'from_module': module
                    })
        result['imports'] = imports

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._parse_class(node, content)
                result['classes'].append(class_info)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._parse_function(node, content, is_method=False)
                result['functions'].append(func_info)

        return result

    def _parse_class(self, node, content):
        class_docstring = ast.get_docstring(node)
        class_desc = ''
        class_author = ''
        class_version = ''

        if class_docstring:
            class_desc = self._extract_description(class_docstring)
            tags = self._extract_docblock_tags(class_docstring)
            class_author = tags.get('author', '')
            class_version = tags.get('version', '')

        bases = []
        for base in node.bases:
            base_name = self._get_type_name(base)
            if base_name:
                bases.append(base_name)

        modifiers = []
        for dec in node.decorator_list:
            dec_name = self._get_type_name(dec)
            if dec_name:
                modifiers.append(dec_name)

        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                method_info = self._parse_function(item, content, is_method=True)
                methods.append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_type = self._get_type_name(item.value) if hasattr(item, 'value') else ''
                        attributes.append({
                            'name': target.id,
                            'type': attr_type,
                            'access_modifier': 'private' if target.id.startswith('_') else 'public'
                        })
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_type = self._get_type_name(item.annotation) if item.annotation else ''
                attributes.append({
                    'name': item.target.id,
                    'type': attr_type,
                    'access_modifier': 'private' if item.target.id.startswith('_') else 'public'
                })

        return {
            'name': node.name,
            'description': class_desc,
            'modifiers': modifiers,
            'inheritance': bases,
            'methods': methods,
            'attributes': attributes,
            'author': class_author,
            'version': class_version,
            'line_number': node.lineno
        }

    def _parse_function(self, node, content, is_method=False):
        func_docstring = ast.get_docstring(node)
        
        params = []
        for i, arg in enumerate(node.args.args):
            param_name = arg.arg
            param_type = self._get_type_name(arg.annotation) if arg.annotation else ''
            
            default_value = ''
            defaults_idx = i - (len(node.args.args) - len(node.args.defaults))
            if defaults_idx >= 0 and defaults_idx < len(node.args.defaults):
                default_value = self._get_default_value(node.args.defaults[defaults_idx])
            
            params.append({
                'name': param_name,
                'type': param_type,
                'default_value': default_value,
                'description': ''
            })

        for i, arg in enumerate(node.args.kwonlyargs):
            param_name = arg.arg
            param_type = self._get_type_name(arg.annotation) if arg.annotation else ''
            
            default_value = ''
            if node.args.kw_defaults and i < len(node.args.kw_defaults) and node.args.kw_defaults[i]:
                default_value = self._get_default_value(node.args.kw_defaults[i])
            
            params.append({
                'name': param_name,
                'type': param_type,
                'default_value': default_value,
                'description': ''
            })

        if node.args.vararg:
            params.append({
                'name': '*' + node.args.vararg.arg,
                'type': self._get_type_name(node.args.vararg.annotation) if node.args.vararg.annotation else '',
                'default_value': '',
                'description': ''
            })

        if node.args.kwarg:
            params.append({
                'name': '**' + node.args.kwarg.arg,
                'type': self._get_type_name(node.args.kwarg.annotation) if node.args.kwarg.annotation else '',
                'default_value': '',
                'description': ''
            })

        return_type = self._get_type_name(node.returns) if node.returns else ''

        description = ''
        return_desc = ''
        exceptions = []
        examples = []
        author = ''
        version = ''

        if func_docstring:
            description = self._extract_description(func_docstring)
            doc_params = self._extract_params(func_docstring)
            
            for dp in doc_params:
                for p in params:
                    if p['name'] == dp['name']:
                        p['description'] = dp['description']
                        if not p['type'] and dp['type']:
                            p['type'] = dp['type']
                        break
            
            ret_info = self._extract_returns(func_docstring)
            if ret_info['type']:
                return_type = return_type or ret_info['type']
            return_desc = ret_info['description']
            
            exceptions = self._extract_exceptions(func_docstring)
            examples = self._extract_examples(func_docstring)
            
            tags = self._extract_docblock_tags(func_docstring)
            author = tags.get('author', '')
            version = tags.get('version', '')

        modifiers = []
        access_modifier = 'public'
        if node.name.startswith('_') and not node.name.startswith('__'):
            access_modifier = 'protected'
        elif node.name.startswith('__') and node.name.endswith('__'):
            access_modifier = 'public'
        elif node.name.startswith('__'):
            access_modifier = 'private'

        for dec in node.decorator_list:
            dec_name = self._get_type_name(dec)
            if dec_name in ['staticmethod', 'classmethod', 'property', 'abstractmethod']:
                modifiers.append(dec_name)

        param_strs = []
        for p in params:
            ps = p['name']
            if p['type']:
                ps += f": {p['type']}"
            if p['default_value']:
                ps += f" = {p['default_value']}"
            param_strs.append(ps)
        
        signature = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({', '.join(param_strs)})"
        if return_type:
            signature += f" -> {return_type}"

        return {
            'name': node.name,
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': return_type,
            'return_description': return_desc,
            'exceptions': exceptions,
            'examples': examples,
            'is_method': is_method,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'modifiers': modifiers,
            'access_modifier': access_modifier,
            'author': author,
            'version': version,
            'line_number': node.lineno
        }

    def _get_type_name(self, node):
        if not node:
            return ''
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_type_name(node.value)}.{node.attr}"
            elif isinstance(node, ast.Subscript):
                base = self._get_type_name(node.value)
                slice_val = self._get_type_name(node.slice)
                return f"{base}[{slice_val}]" if slice_val else base
            elif isinstance(node, ast.Tuple):
                return ', '.join([self._get_type_name(e) for e in node.elts])
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.List):
                return 'list'
            elif isinstance(node, ast.Dict):
                return 'dict'
            elif isinstance(node, ast.Call):
                return self._get_type_name(node.func)
            elif hasattr(node, 'id'):
                return node.id
        except:
            pass
        return ''

    def _get_default_value(self, node):
        if not node:
            return ''
        try:
            if isinstance(node, ast.Constant):
                val = node.value
                if isinstance(val, str):
                    return f"'{val}'"
                return str(val)
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_type_name(node.value)}.{node.attr}"
            elif isinstance(node, ast.List):
                return '[]'
            elif isinstance(node, ast.Dict):
                return '{}'
            elif isinstance(node, ast.Call):
                return f"{self._get_type_name(node.func)}()"
        except:
            pass
        return '...'
