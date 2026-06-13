import re
from app.parsers.base_parser import BaseParser

class JavaParser(BaseParser):
    language = 'java'

    def __init__(self):
        super().__init__()
        self.docblock_patterns = [
            r'/\*\*([\s\S]*?)\*/',
        ]

        self.class_pattern = re.compile(
            r'(?:public|private|protected|abstract|final|static)*\s*(?:class|interface|enum)\s+(\w+)(?:\s*<[^>]*>)?(?:\s+extends\s+([\w<>,\s]+))?(?:\s+implements\s+([\w<>,\s]+))?\s*\{',
            re.MULTILINE
        )
        self.method_pattern = re.compile(
            r'(?:(public|private|protected|static|final|abstract|synchronized|native|default)\s+)*([\w<>\[\],\s?]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+([\w,\s]+))?\s*[;{]',
            re.MULTILINE
        )
        self.constructor_pattern = re.compile(
            r'(?:(public|private|protected)\s+)*(\w+)\s*\(([^)]*)\)\s*(?:throws\s+([\w,\s]+))?\s*\{',
            re.MULTILINE
        )
        self.attribute_pattern = re.compile(
            r'(?:(public|private|protected|static|final|volatile|transient)\s+)+([\w<>\[\],\s?]+)\s+(\w+)\s*[=;]',
            re.MULTILINE
        )
        self.import_pattern = re.compile(
            r'import\s+(?:static\s+)?([\w\.]+)(?:\.\*)?\s*;',
            re.MULTILINE
        )
        self.package_pattern = re.compile(
            r'package\s+([\w\.]+)\s*;',
            re.MULTILINE
        )

    def parse(self, content, relative_path):
        result = {
            'language': 'java',
            'relative_path': relative_path,
            'module_description': '',
            'author': '',
            'version': '',
            'classes': [],
            'functions': [],
            'imports': [],
            'package': ''
        }

        first_docblock = self._find_first_docblock(content)
        if first_docblock:
            result['module_description'] = self._extract_description(first_docblock)
            tags = self._extract_docblock_tags(first_docblock)
            result['author'] = tags.get('author', '')
            result['version'] = tags.get('version', '')

        pkg_match = self.package_pattern.search(content)
        if pkg_match:
            result['package'] = pkg_match.group(1)

        for match in self.import_pattern.finditer(content):
            imp = match.group(1)
            result['imports'].append({
                'name': imp,
                'from_module': ''
            })

        for match in self.class_pattern.finditer(content):
            class_info = self._parse_class(match, content)
            result['classes'].append(class_info)

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

    def _parse_class(self, match, content):
        full_match = match.group(0)
        name = match.group(1)
        extends = match.group(2)
        implements = match.group(3)
        
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
        mod_pattern = re.compile(r'(public|private|protected|abstract|final|static|strictfp)')
        for m in mod_pattern.finditer(full_match):
            modifiers.append(m.group(1))

        class_type = 'class'
        if 'interface' in full_match:
            modifiers.append('interface')
            class_type = 'interface'
        if 'enum' in full_match:
            modifiers.append('enum')
            class_type = 'enum'

        inheritance = []
        if extends:
            for e in extends.split(','):
                e = e.strip()
                if e:
                    inheritance.append({'name': e, 'is_interface': False})
        if implements:
            for i in implements.split(','):
                i = i.strip()
                if i:
                    inheritance.append({'name': i, 'is_interface': True})

        body = self._get_class_body(content, match.start())
        methods = []
        attributes = []

        for c in self.constructor_pattern.finditer(body):
            mod_str, cname, params_str, throws = c.groups()
            if cname != name:
                continue
            constructor_info = self._parse_constructor(c, body)
            methods.append(constructor_info)

        for m in self.method_pattern.finditer(body):
            method_info = self._parse_method(m, body)
            if method_info and method_info['name'] != name:
                methods.append(method_info)

        for a in self.attribute_pattern.finditer(body):
            mods_str, attr_type, attr_name = a.groups()
            modifiers_list = []
            if mods_str:
                modifiers_list = [m.strip() for m in mods_str.split() if m.strip()]
            
            access_modifier = 'package-private'
            for mod in modifiers_list:
                if mod in ['public', 'private', 'protected']:
                    access_modifier = mod
                    break

            attributes.append({
                'name': attr_name,
                'type': attr_type.strip(),
                'access_modifier': access_modifier,
                'modifiers': modifiers_list
            })

        return {
            'name': name,
            'description': description,
            'modifiers': modifiers,
            'inheritance': inheritance,
            'methods': methods,
            'attributes': attributes,
            'author': author,
            'version': version,
            'class_type': class_type
        }

    def _parse_constructor(self, match, body):
        mod_str, name, params_str, throws_str = match.groups()
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]
        
        access_modifier = 'package-private'
        for mod in modifiers:
            if mod in ['public', 'private', 'protected']:
                access_modifier = mod
                break

        params = self._parse_parameters(params_str)
        description = ''
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
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        if throws_str:
            for t in throws_str.split(','):
                t = t.strip()
                if t and not any(e['name'] == t for e in exceptions):
                    exceptions.append({'name': t, 'description': ''})

        signature = f"{' '.join(modifiers + [name]) if modifiers else name}({params_str})"
        if throws_str:
            signature += f" throws {throws_str}"

        return {
            'name': name,
            'signature': signature,
            'description': description,
            'parameters': params,
            'return_type': '',
            'return_description': '',
            'exceptions': exceptions,
            'examples': examples,
            'is_method': True,
            'is_constructor': True,
            'modifiers': modifiers,
            'access_modifier': access_modifier,
            'author': author,
            'version': version
        }

    def _parse_method(self, match, body):
        mod_str, return_type, name, params_str, throws_str = match.groups()
        
        if name in ['if', 'for', 'while', 'switch', 'return', 'class', 'new']:
            return None
        
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]
        
        access_modifier = 'package-private'
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
            return_desc = ret_info['description']
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        if throws_str:
            for t in throws_str.split(','):
                t = t.strip()
                if t and not any(e['name'] == t for e in exceptions):
                    exceptions.append({'name': t, 'description': ''})

        rt = return_type.strip() if return_type else ''
        param_strs = []
        for p in params:
            ps = p['name']
            if p['type']:
                ps = f"{p['type']} {ps}"
            if p['default_value']:
                ps += f" = {p['default_value']}"
            param_strs.append(ps)

        signature = f"{' '.join(modifiers) + ' ' if modifiers else ''}{rt} {name}({', '.join(param_strs)})"
        if throws_str:
            signature += f" throws {throws_str}"

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
            'modifiers': modifiers,
            'access_modifier': access_modifier,
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
            
            tokens = part.split()
            if len(tokens) >= 2:
                param_type = ' '.join(tokens[:-1])
                param_name = tokens[-1]
            elif len(tokens) == 1:
                param_type = ''
                param_name = tokens[0]
            else:
                continue

            params.append({
                'name': param_name,
                'type': param_type,
                'default_value': '',
                'description': ''
            })

        return params
