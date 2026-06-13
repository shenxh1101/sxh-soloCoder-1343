import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader
from app.config import Config

class HTMLGenerator:
    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.env.filters['tojson'] = lambda x: json.dumps(x, ensure_ascii=False)

    def generate(self, doc_structure, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
        static_src = os.path.join(os.path.dirname(__file__), '..', 'static')
        static_dst = os.path.join(output_dir, 'static')
        if os.path.exists(static_dst):
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)

        self._generate_index(doc_structure, output_dir)
        self._generate_module_list(doc_structure, output_dir)
        self._generate_modules(doc_structure, output_dir)
        self._generate_class_list(doc_structure, output_dir)
        self._generate_classes(doc_structure, output_dir)
        self._generate_function_list(doc_structure, output_dir)
        self._generate_functions(doc_structure, output_dir)
        self._generate_search_data(doc_structure, output_dir)
        
        return output_dir

    def _generate_module_list(self, doc_structure, output_dir):
        template = self.env.get_template('index.html')
        html = template.render(
            metadata=doc_structure['metadata'],
            package_structure=doc_structure['package_structure'],
            modules=doc_structure['modules'],
            classes=doc_structure['classes'],
            functions=doc_structure['functions'],
            active_tab='modules'
        )
        with open(os.path.join(output_dir, 'modules.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_class_list(self, doc_structure, output_dir):
        template = self.env.get_template('index.html')
        html = template.render(
            metadata=doc_structure['metadata'],
            package_structure=doc_structure['package_structure'],
            modules=doc_structure['modules'],
            classes=doc_structure['classes'],
            functions=doc_structure['functions'],
            active_tab='classes'
        )
        with open(os.path.join(output_dir, 'classes.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_function_list(self, doc_structure, output_dir):
        template = self.env.get_template('index.html')
        html = template.render(
            metadata=doc_structure['metadata'],
            package_structure=doc_structure['package_structure'],
            modules=doc_structure['modules'],
            classes=doc_structure['classes'],
            functions=doc_structure['functions'],
            active_tab='functions'
        )
        with open(os.path.join(output_dir, 'functions.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_index(self, doc_structure, output_dir):
        template = self.env.get_template('index.html')
        html = template.render(
            metadata=doc_structure['metadata'],
            package_structure=doc_structure['package_structure'],
            modules=doc_structure['modules'],
            classes=doc_structure['classes'],
            functions=doc_structure['functions']
        )
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_modules(self, doc_structure, output_dir):
        modules_dir = os.path.join(output_dir, 'modules')
        os.makedirs(modules_dir, exist_ok=True)
        
        template = self.env.get_template('module.html')
        
        for module in doc_structure['modules']:
            html = template.render(
                module=module,
                metadata=doc_structure['metadata']
            )
            safe_name = module['full_name'].replace('/', '_').replace('\\', '_')
            with open(os.path.join(modules_dir, f'{safe_name}.html'), 'w', encoding='utf-8') as f:
                f.write(html)

    def _generate_classes(self, doc_structure, output_dir):
        classes_dir = os.path.join(output_dir, 'classes')
        os.makedirs(classes_dir, exist_ok=True)
        
        template = self.env.get_template('class.html')
        
        for cls in doc_structure['classes']:
            html = template.render(
                cls=cls,
                metadata=doc_structure['metadata']
            )
            safe_name = f"{cls['module'].replace('/', '_').replace('\\', '_')}_{cls['name']}"
            with open(os.path.join(classes_dir, f'{safe_name}.html'), 'w', encoding='utf-8') as f:
                f.write(html)

    def _generate_functions(self, doc_structure, output_dir):
        if not doc_structure['functions']:
            return
            
        functions_dir = os.path.join(output_dir, 'functions')
        os.makedirs(functions_dir, exist_ok=True)
        
        template = self.env.get_template('function.html')
        
        for func in doc_structure['functions']:
            html = template.render(
                func=func,
                metadata=doc_structure['metadata']
            )
            safe_name = f"{func['module'].replace('/', '_').replace('\\', '_')}_{func['name']}"
            with open(os.path.join(functions_dir, f'{safe_name}.html'), 'w', encoding='utf-8') as f:
                f.write(html)

    def _generate_search_data(self, doc_structure, output_dir):
        search_data = []
        
        for module in doc_structure['modules']:
            search_data.append({
                'type': 'module',
                'name': module['name'],
                'full_name': module['full_name'],
                'description': module['description'],
                'url': f"modules/{module['full_name'].replace('/', '_').replace('\\', '_')}.html"
            })
        
        for cls in doc_structure['classes']:
            search_data.append({
                'type': 'class',
                'name': cls['name'],
                'full_name': f"{cls['module']}::{cls['name']}",
                'description': cls['description'],
                'url': f"classes/{cls['module'].replace('/', '_').replace('\\', '_')}_{cls['name']}.html"
            })
            
            for method in cls.get('methods', []):
                search_data.append({
                    'type': 'method',
                    'name': f"{cls['name']}.{method['name']}",
                    'full_name': f"{cls['module']}::{cls['name']}.{method['name']}",
                    'description': method['description'],
                    'url': f"classes/{cls['module'].replace('/', '_').replace('\\', '_')}_{cls['name']}.html#method-{method['name']}"
                })
        
        for func in doc_structure['functions']:
            search_data.append({
                'type': 'function',
                'name': func['name'],
                'full_name': f"{func['module']}::{func['name']}",
                'description': func['description'],
                'url': f"functions/{func['module'].replace('/', '_').replace('\\', '_')}_{func['name']}.html"
            })
        
        search_json = json.dumps(search_data, ensure_ascii=False)
        
        with open(os.path.join(output_dir, 'search_data.js'), 'w', encoding='utf-8') as f:
            f.write(f'var SEARCH_DATA = {search_json};')
