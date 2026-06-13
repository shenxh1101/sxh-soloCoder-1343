import re
from app.parsers.base_parser import BaseParser

class CppParser(BaseParser):
    language = 'cpp'

    def __init__(self):
        super().__init__()
        self.docblock_patterns = [
            r'/\*\*([\s\S]*?)\*/',
            r'///([^\n]*)',
            r'//!([^\n]*)',
        ]

        self.class_pattern = re.compile(
            r'(?:template\s*<[^>]*>\s*)?(?:class|struct|union)\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{',
            re.MULTILINE
        )
        self.method_pattern = re.compile(
            r'(?:(virtual|static|inline|constexpr|explicit|friend)\s+)*([\w:<>*&\[\],\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?(?:override\s*)?(?:final\s*)?(?:noexcept\s*)?(?:=\s*\d+\s*)?[;{]',
            re.MULTILINE
        )
        self.constructor_pattern = re.compile(
            r'(?:(explicit|virtual)\s+)*(\w+)\s*\(([^)]*)\)\s*(?:\s*:\s*[^;{]+)?[;{]',
            re.MULTILINE
        )
        self.destructor_pattern = re.compile(
            r'(?:(virtual)\s+)*~(\w+)\s*\(\s*\)\s*(?:const\s*)?(?:override\s*)?(?:final\s*)?(?:noexcept\s*)?(?:=\s*(?:0|default|delete)\s*)?[;{]',
            re.MULTILINE
        )
        self.function_pattern = re.compile(
            r'(?:template\s*<[^>]*>\s*)?(?:(static|inline|constexpr|extern)\s+)*([\w:<>*&\[\],\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?(?:noexcept\s*)?[;{]',
            re.MULTILINE
        )
        self.attribute_pattern = re.compile(
            r'(?:(static|const|constexpr|mutable|volatile)\s+)*([\w:<>*&\[\],\s]+?)\s+(\w+)\s*(?:\[[^\]]*\])*\s*[=;]',
            re.MULTILINE
        )
        self.include_pattern = re.compile(
            r'#\s*include\s*[<"]([^>"]+)[>"]',
            re.MULTILINE
        )
        self.namespace_pattern = re.compile(
            r'namespace\s+(\w+)\s*\{',
            re.MULTILINE
        )
        self.access_specifier_pattern = re.compile(
            r'(public|private|protected)\s*:',
            re.MULTILINE
        )

    def parse(self, content, relative_path):
        result = {
            'language': 'cpp',
            'relative_path': relative_path,
            'module_description': '',
            'author': '',
            'version': '',
            'classes': [],
            'functions': [],
            'imports': [],
            'namespaces': []
        }

        first_docblock = self._find_first_docblock(content)
        if first_docblock:
            result['module_description'] = self._extract_description(first_docblock)
            tags = self._extract_docblock_tags(first_docblock)
            result['author'] = tags.get('author', '')
            result['version'] = tags.get('version', '')

        for match in self.include_pattern.finditer(content):
            inc = match.group(1)
            result['imports'].append({
                'name': inc,
                'from_module': ''
            })

        for match in self.namespace_pattern.finditer(content):
            result['namespaces'].append(match.group(1))

        for match in self.class_pattern.finditer(content):
            class_info = self._parse_class(match, content)
            result['classes'].append(class_info)

        for match in self.function_pattern.finditer(content):
            func_info = self._parse_function(match, content)
            if func_info and not self._is_inside_class(match.start(), content):
                result['functions'].append(func_info)

        return result

    def _find_first_docblock(self, content):
        match = re.search(r'/\*\*([\s\S]*?)\*/', content)
        if match:
            return match.group(0)
        
        lines = content.split('\n')
        doc_lines = []
        for line in lines[:20]:
            if line.strip().startswith('///') or line.strip().startswith('//!'):
                doc_lines.append(line)
            elif doc_lines and not line.strip().startswith('///') and not line.strip().startswith('//!'):
                break
        if doc_lines:
            return '\n'.join(doc_lines)
        return None

    def _find_docblock(self, content, pos):
        before = content[:pos].rstrip()
        
        block_match = re.search(r'/\*\*([\s\S]*?)\*/\s*$', before)
        if block_match:
            return block_match.group(0)
        
        lines = before.split('\n')
        doc_lines = []
        for line in reversed(lines[:-1]):
            stripped = line.strip()
            if stripped.startswith('///') or stripped.startswith('//!'):
                doc_lines.insert(0, line)
            elif stripped:
                break
        if doc_lines:
            return '\n'.join(doc_lines)
        return None

    def _is_inside_class(self, pos, content):
        class_matches = list(self.class_pattern.finditer(content))
        for cm in class_matches:
            start = cm.start()
            brace_pos = content.find('{', start)
            if brace_pos == -1:
                continue
            end_pos = self._find_matching_brace(content, brace_pos)
            if start < pos < end_pos:
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

    def _parse_class(self, match, content):
        template_match = re.search(r'template\s*<([^>]*)>', content[max(0, match.start()-100):match.start()])
        template_params = template_match.group(1) if template_match else ''
        
        name = match.group(1)
        inheritance_str = match.group(2)
        
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
        if 'struct' in class_text:
            modifiers.append('struct')
        if 'union' in class_text:
            modifiers.append('union')
        if template_params:
            modifiers.append('template')

        inheritance = []
        if inheritance_str:
            for base in inheritance_str.split(','):
                base = base.strip()
                if not base:
                    continue
                parts = base.split()
                is_virtual = 'virtual' in parts
                access = 'public'
                for mod in ['public', 'private', 'protected']:
                    if mod in parts:
                        access = mod
                        break
                base_name = parts[-1] if parts else base
                inheritance.append({
                    'name': base_name,
                    'access': access,
                    'is_virtual': is_virtual,
                    'is_interface': False
                })

        body = self._get_class_body(content, match.start())
        methods = []
        attributes = []

        current_access = 'private' if 'class' in class_text else 'public'
        
        sections = self._split_by_access_specifiers(body)
        
        for access, section_content in sections:
            current_access = access
            
            for d in self.destructor_pattern.finditer(section_content):
                destructor_info = self._parse_destructor(d, section_content, current_access)
                methods.append(destructor_info)

            for c in self.constructor_pattern.finditer(section_content):
                mod_str, cname, params_str = c.groups()
                if cname != name:
                    continue
                constructor_info = self._parse_constructor(c, section_content, current_access)
                methods.append(constructor_info)

            for m in self.method_pattern.finditer(section_content):
                method_info = self._parse_method(m, section_content, current_access)
                if method_info and method_info['name'] != name:
                    methods.append(method_info)

            for a in self.attribute_pattern.finditer(section_content):
                mods_str, attr_type, attr_name = a.groups()
                if attr_name in ['if', 'for', 'while', 'switch', 'return', 'class', 'new', 'delete', 'sizeof']:
                    continue
                
                modifiers_list = []
                if mods_str:
                    modifiers_list = [m.strip() for m in mods_str.split() if m.strip()]

                attributes.append({
                    'name': attr_name,
                    'type': attr_type.strip(),
                    'access_modifier': current_access,
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
            'template_params': template_params
        }

    def _split_by_access_specifiers(self, body):
        sections = []
        current_access = 'private'
        last_pos = 0
        
        for match in self.access_specifier_pattern.finditer(body):
            if match.start() > last_pos:
                sections.append((current_access, body[last_pos:match.start()]))
            current_access = match.group(1)
            last_pos = match.end()
        
        if last_pos < len(body):
            sections.append((current_access, body[last_pos:]))
        
        return sections

    def _parse_constructor(self, match, body, access_modifier='private'):
        mod_str, name, params_str = match.groups()
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]

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

        full_text = match.group(0)
        is_explicit = 'explicit' in full_text

        signature = f"{'explicit ' if is_explicit else ''}{name}({params_str})"

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

    def _parse_destructor(self, match, body, access_modifier='private'):
        mod_str, name = match.groups()
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]
        
        full_text = match.group(0)
        if 'virtual' in full_text and 'virtual' not in modifiers:
            modifiers.append('virtual')
        if 'override' in full_text:
            modifiers.append('override')
        if 'final' in full_text:
            modifiers.append('final')

        description = ''
        exceptions = []
        examples = []
        author = ''
        version = ''

        if docblock:
            description = self._extract_description(docblock)
            exceptions = self._extract_exceptions(docblock)
            examples = self._extract_examples(docblock)
            tags = self._extract_docblock_tags(docblock)
            author = tags.get('author', '')
            version = tags.get('version', '')

        signature = f"~{name}()"

        return {
            'name': '~' + name,
            'signature': signature,
            'description': description,
            'parameters': [],
            'return_type': '',
            'return_description': '',
            'exceptions': exceptions,
            'examples': examples,
            'is_method': True,
            'is_destructor': True,
            'modifiers': modifiers,
            'access_modifier': access_modifier,
            'author': author,
            'version': version
        }

    def _parse_method(self, match, body, access_modifier='private'):
        mod_str, return_type, name, params_str = match.groups()
        
        if name in ['if', 'for', 'while', 'switch', 'return', 'class', 'new', 'delete', 'sizeof', 'template']:
            return None
        
        docblock = self._find_docblock(body, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]
        
        full_text = match.group(0)
        if 'const' in full_text:
            modifiers.append('const')
        if 'override' in full_text:
            modifiers.append('override')
        if 'final' in full_text:
            modifiers.append('final')
        if 'noexcept' in full_text:
            modifiers.append('noexcept')
        if 'virtual' in full_text and 'virtual' not in modifiers:
            modifiers.append('virtual')

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
        if 'const' in full_text and 'const' not in signature:
            signature += ' const'

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

    def _parse_function(self, match, content):
        template_match = re.search(r'template\s*<([^>]*)>', content[max(0, match.start()-100):match.start()])
        
        mod_str, return_type, name, params_str = match.groups()
        
        if name in ['if', 'for', 'while', 'switch', 'return', 'class', 'new', 'delete', 'sizeof', 'template', 'operator']:
            return None
        
        docblock = self._find_docblock(content, match.start())
        
        modifiers = []
        if mod_str:
            modifiers = [m.strip() for m in mod_str.split() if m.strip()]
        if template_match:
            modifiers.append('template')

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

            tokens = part.split()
            if len(tokens) >= 2:
                param_type = ' '.join(tokens[:-1])
                param_name = tokens[-1].lstrip('*&')
            elif len(tokens) == 1:
                param_type = ''
                param_name = tokens[0].lstrip('*&')
            else:
                continue

            params.append({
                'name': param_name,
                'type': param_type,
                'default_value': default_value,
                'description': ''
            })

        return params
