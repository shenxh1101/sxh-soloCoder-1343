import os
import json
import shutil
from datetime import datetime
from app.parsers.parser_factory import ParserFactory
from app.utils.file_utils import (
    extract_zip, get_supported_files, read_file_content,
    create_temp_dir, zip_directory, generate_unique_id
)
from app.utils.doc_builder import build_document_structure, save_json_document
from app.utils.html_generator import HTMLGenerator
from app.utils.plantuml_generator import generate_class_diagram
from app.utils.version_compare import compare_versions
from app.config import Config
from jinja2 import Environment, FileSystemLoader

class DocumentationProcessor:
    def __init__(self):
        self.html_generator = HTMLGenerator()
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def process_zip(self, zip_path, project_name=None, output_dir=None):
        if not project_name:
            project_name = os.path.splitext(os.path.basename(zip_path))[0]

        temp_dir = create_temp_dir(prefix='extract_')
        if output_dir is None:
            output_dir = create_temp_dir(prefix='output_')
        else:
            os.makedirs(output_dir, exist_ok=True)

        try:
            extract_zip(zip_path, temp_dir)
            parsed_files = self._parse_source_files(temp_dir)
            doc_structure = build_document_structure(parsed_files, project_name)

            json_path = os.path.join(output_dir, 'documentation.json')
            save_json_document(doc_structure, json_path)

            plantuml_path = os.path.join(output_dir, 'class_diagram.puml')
            generate_class_diagram(doc_structure, plantuml_path)

            html_dir = os.path.join(output_dir, 'html')
            self.html_generator.generate(doc_structure, html_dir)

            result = {
                'success': True,
                'project_name': project_name,
                'output_dir': output_dir,
                'html_dir': html_dir,
                'json_path': json_path,
                'plantuml_path': plantuml_path,
                'doc_structure': doc_structure,
                'generated_at': datetime.now().isoformat()
            }

            return result

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if output_dir is None:
                shutil.rmtree(output_dir, ignore_errors=True)
            raise

    def _parse_source_files(self, source_dir):
        parsed_files = []
        supported_files = get_supported_files(source_dir)

        for file_info in supported_files:
            try:
                parser = ParserFactory.get_parser(file_info['language'])
                if parser:
                    content = read_file_content(file_info['path'])
                    parsed_data = parser.parse(content, file_info['relative_path'])
                    if parsed_data:
                        parsed_files.append(parsed_data)
            except Exception as e:
                print(f"Error parsing {file_info['path']}: {e}")
                continue

        return parsed_files

    def compare_versions(self, zip_path_v1, zip_path_v2, name_v1=None, name_v2=None, output_dir=None):
        if output_dir is None:
            output_dir = create_temp_dir(prefix='compare_')
        os.makedirs(output_dir, exist_ok=True)

        v1_dir = os.path.join(output_dir, 'v1')
        v2_dir = os.path.join(output_dir, 'v2')
        os.makedirs(v1_dir, exist_ok=True)
        os.makedirs(v2_dir, exist_ok=True)

        result_v1 = self.process_zip(zip_path_v1, name_v1 or 'Version 1', output_dir=v1_dir)
        result_v2 = self.process_zip(zip_path_v2, name_v2 or 'Version 2', output_dir=v2_dir)

        report = compare_versions(result_v1['doc_structure'], result_v2['doc_structure'])

        report_json_path = os.path.join(output_dir, 'comparison_report.json')
        with open(report_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        template = self.jinja_env.get_template('compare_report.html')
        report_html = template.render(report=report)
        report_html_path = os.path.join(output_dir, 'comparison_report.html')
        with open(report_html_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

        return {
            'success': True,
            'report': report,
            'output_dir': output_dir,
            'report_json_path': report_json_path,
            'report_html_path': report_html_path,
            'v1_doc_path': result_v1['json_path'],
            'v2_doc_path': result_v2['json_path'],
            'v1_html_dir': result_v1['html_dir'],
            'v2_html_dir': result_v2['html_dir'],
            'v1_plantuml_path': result_v1['plantuml_path'],
            'v2_plantuml_path': result_v2['plantuml_path'],
            'generated_at': datetime.now().isoformat()
        }

    def package_for_download(self, output_dir):
        zip_path = output_dir + '.zip'
        zip_directory(output_dir, zip_path)
        return zip_path

    def create_preview(self, html_dir):
        from app.config import Config
        preview_id = generate_unique_id()
        preview_dir = os.path.join(Config.PREVIEW_FOLDER, preview_id)
        
        if os.path.exists(preview_dir):
            shutil.rmtree(preview_dir)
        
        shutil.copytree(html_dir, preview_dir)
        
        return preview_id, preview_dir
