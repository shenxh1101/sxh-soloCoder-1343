import re
from abc import ABC, abstractmethod

class BaseParser(ABC):
    language = 'base'

    def __init__(self):
        self.docblock_patterns = [
            r'/\*\*(.*?)\*/',
            r'/\*(.*?)\*/',
        ]

    @abstractmethod
    def parse(self, content, relative_path):
        pass

    def _extract_docblock_tags(self, docstring):
        if not docstring:
            return {}
        
        tags = {}
        
        author_match = re.search(r'@author\s+([^\n@]+)', docstring)
        if author_match:
            tags['author'] = author_match.group(1).strip()
        
        version_match = re.search(r'@version\s+([^\n@]+)', docstring)
        if version_match:
            tags['version'] = version_match.group(1).strip()
        
        deprecated_match = re.search(r'@deprecated', docstring)
        if deprecated_match:
            tags['deprecated'] = True
        
        since_match = re.search(r'@since\s+([^\n@]+)', docstring)
        if since_match:
            tags['since'] = since_match.group(1).strip()
        
        return tags

    def _extract_params(self, docstring):
        params = []
        param_patterns = [
            r'@param\s+(?:\{([^}]+)\})?\s*(\w+)\s*([^\n@]*)',
            r'@param\s+(\w+)\s*:\s*(\w+)\s*([^\n@]*)',
            r'@param\s+(\w+)\s+([^\n@]*)',
        ]
        
        for pattern in param_patterns:
            for match in re.finditer(pattern, docstring):
                groups = match.groups()
                if len(groups) == 3 and groups[1] and groups[1] not in [':', '']:
                    if ':' in match.group(0):
                        param_type = groups[1] if groups[1] else ''
                        param_name = groups[0]
                        param_desc = groups[2].strip()
                    else:
                        param_type = groups[0] if groups[0] else ''
                        param_name = groups[1]
                        param_desc = groups[2].strip()
                elif len(groups) >= 2:
                    param_type = groups[0] if groups[0] else ''
                    param_name = groups[1]
                    param_desc = groups[2].strip() if len(groups) > 2 and groups[2] else ''
                else:
                    continue
                
                params.append({
                    'name': param_name,
                    'type': param_type,
                    'description': param_desc
                })
        
        return params

    def _extract_returns(self, docstring):
        return_info = {'type': '', 'description': ''}
        
        return_patterns = [
            r'@return[s]?\s+(?:\{([^}]+)\})?\s*([^\n@]*)',
            r'@return[s]?\s+(\w+)\s+([^\n@]*)',
            r'@returns?\s*:\s*(\w+)\s*([^\n@]*)',
        ]
        
        for pattern in return_patterns:
            match = re.search(pattern, docstring)
            if match:
                groups = match.groups()
                return_info['type'] = groups[0] if groups[0] else ''
                return_info['description'] = groups[1].strip() if len(groups) > 1 and groups[1] else ''
                break
        
        return return_info

    def _extract_exceptions(self, docstring):
        exceptions = []
        ex_patterns = [
            r'@throws?\s+(?:\{([^}]+)\})?\s*(\w+)\s*([^\n@]*)',
            r'@throws?\s+(\w+)\s*([^\n@]*)',
            r'@exception\s+(\w+)\s*([^\n@]*)',
        ]
        
        for pattern in ex_patterns:
            for match in re.finditer(pattern, docstring):
                groups = match.groups()
                if len(groups) >= 2:
                    ex_name = groups[0] if groups[0] else (groups[1] if groups[1] else '')
                    ex_desc = groups[2].strip() if len(groups) > 2 and groups[2] else (groups[1].strip() if len(groups) > 1 and groups[1] else '')
                    exceptions.append({
                        'name': ex_name,
                        'description': ex_desc
                    })
        
        return exceptions

    def _extract_examples(self, docstring):
        examples = []
        example_patterns = [
            r'@example\s*([\s\S]*?)(?=\n\s*@|\n\s*\*/|$)',
            r'@example\s+<pre>([\s\S]*?)</pre>',
            r'```[\w]*\n([\s\S]*?)```',
        ]
        
        for pattern in example_patterns:
            for match in re.finditer(pattern, docstring):
                code = match.group(1).strip()
                if code:
                    examples.append(code)
        
        return examples

    def _clean_docstring(self, docstring):
        if not docstring:
            return ''
        
        lines = []
        for line in docstring.split('\n'):
            cleaned = line.strip()
            cleaned = re.sub(r'^[\s*#/]+', '', cleaned)
            cleaned = re.sub(r'[\s*#/]+$', '', cleaned)
            if cleaned:
                lines.append(cleaned)
        
        return '\n'.join(lines).strip()

    def _extract_description(self, docstring):
        if not docstring:
            return ''
        
        cleaned = self._clean_docstring(docstring)
        lines = cleaned.split('\n')
        desc_lines = []
        
        for line in lines:
            if line.startswith('@'):
                break
            desc_lines.append(line)
        
        return '\n'.join(desc_lines).strip()
