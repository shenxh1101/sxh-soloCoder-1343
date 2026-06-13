import re
from app.parsers.base_parser import BaseParser

class JavaScriptParser(BaseParser):
    language = 'javascript'

    def __init__(self):
        super().__init__()
        self.docblock_patterns = [
            r'/\*\*([\s\S]*?)\*/',
        ]

        self.class_pattern = re.compile(
            r'(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+([\w<>,\s]+))?(?:\s+implements\s+([\w<>,\s]+))?\s*\{',
            re.MULTILINE
        )
        self.interface_pattern = re.compile(
            r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w<>,\s]+))?\s*\{',
            re.MULTILINE
        )
        self.method_pattern = re.compile(
            r'(?:(public|private|protected|static|async|abstract)\s+)*(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{;]+))?\s*[;{]',
            re.MULTILINE
        )
        self.function_pattern = re.compile(
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*\{',
            re.MULTILINE
        )
        self.arrow_function_pattern = re.compile(
            r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^{=]+))?\s*=>',
            re.MULTILINE
        )
        self.constructor_pattern = re.compile(
            r'constructor\s*\(([^)]*)\)\s*\{',
            re.MULTILINE
        )
        self.attribute_pattern = re.compile(
            r'(?:(public|private|protected|static|readonly)\s+)*(\w+)\s*(?::\s*([^;=]+))?\s*[=;]',
            re.MULTILINE
        )
        self.import_pattern = re.compile(
            r'import\s+(?:(?:\{([^}]+)\}|([\w*]+))\s+from\s+)?[\'"]([^\'"]+)[\'"]',
            re.MULTILINE
        )

    def parse(self, content, relative_path):
        result = {
            'language': 'javascript',
            'relative_path': relative_path,
            'module_description': '',
            'author': '',
            'version': '',
            'classes': [],
            'functions': [],
            'imports': []
        }

        first_docblock = self._find_first_docblock(content)
        if first_docblock:
            result['module_description'] = self._extract_description(first_docblock)
            tags = self._extract_docblock_tags(first_docblock)
            result['author'] = tags.get('author', '')
            result['version'] = tags.get('version', '')

        for match in self.import_pattern.finditer(content):
            named_imports, default_import, module = match.groups()
            imports = []
            if named_imports:
                for imp in named_imports.split(','):
                    imp = imp.strip()
                    if imp:
                        as_parts = imp.split(' as ')
                        imports.append({
                            'name': as_parts[0].strip(),
                            'asname': as_parts[1].strip() if len(as_parts) > 1 else None,
                            'from_module': module
                        })
            if default_import:
                imports.append({
                    'name': default_import.strip(),
                    'asname': None,
                    'from_module': module
                })
            result['imports'].extend(imports)

        for match in self.interface_pattern.finditer(content):
            iface_info = self._parse_interface(match, content)
            result['classes'].append(iface_info)

        for match in self.class_pattern.finditer(content):
            class_info = self._parse_class(match, content)
            result['classes'].append(class_info)

        for match in self.function_pattern.finditer(content):
            func_info = self._parse_function_match(match, content, is_async='async' in match.group(0))
            if not self._is_inside_class(match.start(), content):
                result['functions'].append(func_info)

        for match in self.arrow_function_pattern.finditer(content):
            func_info = self._parse_arrow_function(match, content)
            if not self._is_inside_class(match.start(), content):
                result['functions'].append(func_info)

        return result

    def _find_first_docblock(self, content):
        match = re.search(r'/\*\*([\s\S]*?)\*/', content)
        if match:
            return match.group(0)
        return None

    def _find_docblock(self, content, pos):
        before = content[:pos].rstrip()
        match = re.search(r'/\*\*([\s\S]*?)\*/\s*$', before)
        if match:
            return match.group(0)
        return None

    def _is_inside_class(self, pos, content):
        class_matches = list(self.class_pattern.finditer(content))
        for cm in class_matches:
            if cm.start() < pos < self._find_matching_brace(content, cm.end() - 1):
                return True
        return False

    def _find_matching_brace(self, content, start):
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(content)

    def _get_class_body(self, content, class_start):
        brace_pos = content.find('{', class_start)
        if brace_pos == -1:
            return ''
        end_pos = self._find_matching_brace(content, brace_pos)
        return content[brace_pos + 1:end_pos]

    def _parse_interface(self, match, content):
        name, extends = match.groups()
        docblock = self._find_docblock(content, match.start())
        
        description = ''
        author = ''
        version = ''
        if docblock:
            description = self._extract_description(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        inheritance = []
        if extends:
            for e in extends.split(','):
                inheritance.append({'name': e.strip(), 'is_interface': True})

        body = self._get_class_body(content, match.start())
        methods = []
        attributes = []

        for m in self.method_pattern.finditer(body):
            method_info = self._parse_method(m, body, is_interface=True)
            methods.append(method_info)

        for a in self.attribute_pattern.finditer(body):
            access_mod, attr_name, attr_type = a.groups()
            attributes.append({
                'name': attr_name,
                'type': attr_type.strip() if attr_type else '',
                'access_modifier': access_mod or 'public'
            })

        return {
            'name': name,
            'description': description,
            'modifiers': ['interface'],
            'inheritance': inheritance,
            'methods': methods,
            'attributes': attributes,
            'author': author,
            'version': version
        }

    def _parse_class(self, match, content):
        name, extends, implements = match.groups()
        docblock = self._find_docblock(content, match.start())
        
        description = ''
        author = ''
        version = ''
        if docblock:
            description = self._extract_description(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        modifiers = []
        class_text = match.group(0)
        if 'abstract' in class_text:
            modifiers.append('abstract')
        if 'export' in class_text:
            modifiers.append('export')
        if 'default' in class_text:
            modifiers.append('default')

        inheritance = []
        if extends:
            for e in extends.split(','):
                inheritance.append({'name': e.strip(), 'is_interface': False})
        if implements:
            for i in implements.split(','):
                inheritance.append({'name': i.strip(), 'is_interface': True})

        body = self._get_class_body(content, match.start())
        methods = []
        attributes = []

        for c in self.constructor_pattern.finditer(body):
            constructor_info = self._parse_constructor(c, body)
            methods.append(constructor_info)

        for m in self.method_pattern.finditer(body):
            if m.group(2) == 'constructor':
                continue
            method_info = self._parse_method(m, body)
            methods.append(method_info)

        for a in self.attribute_pattern.finditer(body):
            access_mod, attr_name, attr_type = a.groups()
            if attr_name in ['function', 'if', 'for', 'while', 'return', 'class']:
                continue
            attributes.append({
                'name': attr_name,
                'type': attr_type.strip() if attr_type else '',
                'access_modifier': access_mod or 'public'
            })

        return {
            'name': name,
            'description': description,
            'modifiers': modifiers,
            'inheritance': inheritance,
            'methods': methods,
            'attributes': attributes,
            'author': author,
            'version': version
        }

    def _parse_constructor(self, match, body):
        params_str = match.group(1)
        docblock = self._find_docblock(body, match.start())
        
        params = self._parse_parameters(params_str)
        description = ''
        examples = []
        author = ''
        version = ''

        if docblock:
            description = self._extract_description(docblock)
            doc_params = self._extract_params(docblock)
            for dp in doc_params:
                for p in params:
                    if p['name'] == dp['name']:
                        p['description'] = dp['description']
                        if not p['type'] and dp['type']:
                            p['type'] = dp['type']
                        break
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        signature = f"constructor({params_str})"

        return {
            'name': 'constructor',
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': '',
            'return_description': '',
            'exceptions': [],
            'examples': examples,
            'is_method': True,
            'is_async': False,
            'modifiers': [],
            'access_modifier': 'public',
            'author': author,
            'version': version
        }

    def _parse_method(self, match, body, is_interface=False):
        modifiers_str, name, params_str, return_type = match.groups()
        
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if modifiers_str:
            modifiers = [m.strip() for m in modifiers_str.split() if m.strip()]
        
        is_async = 'async' in modifiers
        is_static = 'static' in modifiers
        access_modifier = 'public'
        for mod in modifiers:
            if mod in ['public', 'private', 'protected']:
                access_modifier = mod
                break

        params = self._parse_parameters(params_str)
        description = ''
        return_desc = ''
        exceptions = []
        examples = []
        author = ''
        version = ''

        if docblock:
            description = self._extract_description(docblock)
            doc_params = self._extract_params(docblock)
            for dp in doc_params:
                for p in params:
                    if p['name'] == dp['name']:
                        p['description'] = dp['description']
                        if not p['type'] and dp['type']:
                            p['type'] = dp['type']
                        break
            ret_info = self._extract_returns(docblock)
            if ret_info['type'] and not return_type:
                return_type = ret_info['type']
            return_desc = ret_info['description']
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        param_strs = []
        for p in params:
            ps = p['name']
            if p['type']:
                ps += f": {p['type']}"
            if p['default_value']:
                ps += f" = {p['default_value']}"
            param_strs.append(ps)

        rt = return_type.strip() if return_type else ''
        signature = f"{'async ' if is_async else ''}{name}({', '.join(param_strs)})"
        if rt:
            signature += f": {rt}"

        return {
            'name': name,
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': rt,
            'return_description': return_desc,
            'exceptions': exceptions,
            'examples': examples,
            'is_method': True,
            'is_async': is_async,
            'modifiers': modifiers,
            'access_modifier': access_modifier,
            'author': author,
            'version': version
        }

    def _parse_function_match(self, match, content, is_async=False):
        name, params_str, return_type = match.groups()
        docblock = self._find_docblock(content, match.start())
        
        params = self._parse_parameters(params_str)
        description = ''
        return_desc = ''
        exceptions = []
        examples = []
        author = ''
        version = ''

        if docblock:
            description = self._extract_description(docblock)
            doc_params = self._extract_params(docblock)
            for dp in doc_params:
                for p in params:
                    if p['name'] == dp['name']:
                        p['description'] = dp['description']
                        if not p['type'] and dp['type']:
                            p['type'] = dp['type']
                        break
            ret_info = self._extract_returns(docblock)
            if ret_info['type'] and not return_type:
                return_type = ret_info['type']
            return_desc = ret_info['description']
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        param_strs = []
        for p in params:
            ps = p['name']
            if p['type']:
                ps += f": {p['type']}"
            if p['default_value']:
                ps += f" = {p['default_value']}"
            param_strs.append(ps)

        rt = return_type.strip() if return_type else ''
        signature = f"{'async ' if is_async else ''}function {name}({', '.join(param_strs)})"
        if rt:
            signature += f": {rt}"

        modifiers = []
        func_text = match.group(0)
        if 'export' in func_text:
            modifiers.append('export')

        return {
            'name': name,
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': rt,
            'return_description': return_desc,
            'exceptions': exceptions,
            'examples': examples,
            'is_method': False,
            'is_async': is_async,
            'modifiers': modifiers,
            'access_modifier': 'public',
            'author': author,
            'version': version
        }

    def _parse_arrow_function(self, match, content):
        name, params_str, return_type = match.groups()
        docblock = self._find_docblock(content, match.start())
        
        is_async = 'async' in match.group(0)
        
        params = self._parse_parameters(params_str)
        description = ''
        return_desc = ''
        exceptions = []
        examples = []
        author = ''
        version = ''

        if docblock:
            description = self._extract_description(docblock)
            doc_params = self._extract_params(docblock)
            for dp in doc_params:
                for p in params:
                    if p['name'] == dp['name']:
                        p['description'] = dp['description']
                        if not p['type'] and dp['type']:
                            p['type'] = dp['type']
                        break
            ret_info = self._extract_returns(docblock)
            if ret_info['type'] and not return_type:
                return_type = ret_info['type']
            return_desc = ret_info['description']
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        param_strs = []
        for p in params:
            ps = p['name']
            if p['type']:
                ps += f": {p['type']}"
            if p['default_value']:
                ps += f" = {p['default_value']}"
            param_strs.append(ps)

        rt = return_type.strip() if return_type else ''
        signature = f"const {name} = {'async ' if is_async else ''}({', '.join(param_strs)})"
        if rt:
            signature += f": {rt}"
        signature += " =>"

        modifiers = []
        func_text = match.group(0)
        if 'export' in func_text:
            modifiers.append('export')

        return {
            'name': name,
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': rt,
            'return_description': return_desc,
            'exceptions': exceptions,
            'examples': examples,
            'is_method': False,
            'is_async': is_async,
            'modifiers': modifiers,
            'access_modifier': 'public',
            'author': author,
            'version': version
        }

    def _parse_parameters(self, params_str):
        params = []
        if not params_str or not params_str.strip():
            return params

        params_str = params_str.strip()
        depth = 0
        current = []
        parts = []

        for c in params_str:
            if c in '<([{':
                depth += 1
                current.append(c)
            elif c in '>)]}':
                depth -= 1
                current.append(c)
            elif c == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(c)

        if current:
            parts.append(''.join(current).strip())

        for part in parts:
            if not part:
                continue
            
            default_value = ''
            if '=' in part:
                parts2 = part.split('=', 1)
                part = parts2[0].strip()
                default_value = parts2[1].strip()

            param_type = ''
            param_name = part
            
            if ':' in part:
                type_parts = part.split(':', 1)
                param_name = type_parts[0].strip()
                param_type = type_parts[1].strip()

            param_name = param_name.replace('...', '')
            
            params.append({
                'name': param_name,
                'type': param_type,
                'default_value': default_value,
                'description': ''
            })

        return params
