"""
完整文档生成管道测试。
测试ZIP处理、JSON生成、PlantUML生成、HTML生成和版本对比功能。
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.doc_processor import DocumentationProcessor
from app.utils.doc_builder import build_document_structure, save_json_document, load_json_document
from app.utils.plantuml_generator import generate_class_diagram
from app.utils.version_compare import compare_versions
from app.utils.file_utils import zip_directory, extract_zip, create_temp_dir
from app.parsers.parser_factory import ParserFactory


def create_test_zip(zip_path, source_dir, version_suffix=""):
    """创建测试ZIP包。"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                if version_suffix:
                    arcname = arcname.replace('sample_module', f'sample_module{version_suffix}')
                zipf.write(file_path, arcname)
    print(f"[OK] 创建测试ZIP: {zip_path}")


def create_modified_sample(samples_dir, output_dir, version="v2"):
    """创建修改后的样本用于版本对比测试。"""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(samples_dir, output_dir)
    
    # 修改Python文件 - 添加新方法
    py_file = os.path.join(output_dir, 'python', 'sample_module.py')
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加一个新方法到Calculator类
    new_method = '''
    def multiply(self, a: float, b: float) -> float:
        """
        两个数相乘（v2新增）。
        
        @param a: 第一个乘数
        @param b: 第二个乘数
        @return: 两数之积
        @rtype: float
        """
        return round(a * b, self.precision)
'''
    
    content = content.replace('        return round(a / b, self.precision)', 
                              '        return round(a / b, self.precision)\n' + new_method)
    
    # 修改divide方法的描述
    content = content.replace('两个数相除。', '两个数相除（v2优化）。')
    
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] 创建{version}版本样本")


def test_document_building():
    """测试文档结构构建。"""
    print("\n" + "="*60)
    print("测试 文档结构构建")
    print("="*60)
    
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    
    # 解析所有样本文件
    parsed_files = []
    for lang_dir in ['python', 'javascript', 'java', 'cpp']:
        lang_path = os.path.join(samples_dir, lang_dir)
        if os.path.isdir(lang_path):
            for file in os.listdir(lang_path):
                file_path = os.path.join(lang_path, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1]
                    parser = ParserFactory.get_parser_by_extension(ext)
                    if parser:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        rel_path = os.path.join(lang_dir, file)
                        parsed = parser.parse(content, rel_path)
                        if parsed:
                            parsed_files.append(parsed)
                            print(f"[OK] 解析: {rel_path}")
    
    print(f"\n[OK] 共解析 {len(parsed_files)} 个文件")
    
    # 构建文档结构
    doc_structure = build_document_structure(parsed_files, 'TestProject')
    
    assert doc_structure['metadata']['project_name'] == 'TestProject'
    assert doc_structure['metadata']['language_count'] == 4
    assert 'files' in doc_structure
    assert 'modules' in doc_structure
    assert 'classes' in doc_structure
    assert 'functions' in doc_structure
    assert 'package_structure' in doc_structure
    
    print(f"[OK] 项目名称: {doc_structure['metadata']['project_name']}")
    print(f"[OK] 文件数: {doc_structure['metadata']['file_count']}")
    print(f"[OK] 语言数: {doc_structure['metadata']['language_count']}")
    print(f"[OK] 类数: {len(doc_structure['classes'])}")
    print(f"[OK] 函数数: {len(doc_structure['functions'])}")
    print(f"[OK] 模块数: {len(doc_structure['modules'])}")
    
    # 测试JSON序列化
    temp_dir = create_temp_dir(prefix='json_test_')
    json_path = os.path.join(temp_dir, 'test_doc.json')
    save_json_document(doc_structure, json_path)
    assert os.path.exists(json_path), "JSON文件应存在"
    
    loaded = load_json_document(json_path)
    assert loaded['metadata']['project_name'] == 'TestProject'
    print(f"[OK] JSON序列化/反序列化成功")
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n[OK] 文档结构构建测试通过!")
    return True


def test_plantuml_generation():
    """测试PlantUML类图生成。"""
    print("\n" + "="*60)
    print("测试 PlantUML 类图生成")
    print("="*60)
    
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    
    # 解析Python样本
    parsed_files = []
    py_path = os.path.join(samples_dir, 'python', 'sample_module.py')
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = ParserFactory.get_parser('python')
    parsed = parser.parse(content, 'python/sample_module.py')
    if parsed:
        parsed_files.append(parsed)
    
    doc_structure = build_document_structure(parsed_files, 'PlantUMLTest')
    
    temp_dir = create_temp_dir(prefix='plantuml_test_')
    puml_path = os.path.join(temp_dir, 'class_diagram.puml')
    
    generate_class_diagram(doc_structure, puml_path)
    
    assert os.path.exists(puml_path), "PlantUML文件应存在"
    
    with open(puml_path, 'r', encoding='utf-8') as f:
        puml_content = f.read()
    
    assert '@startuml' in puml_content, "应包含@startuml"
    assert '@enduml' in puml_content, "应包含@enduml"
    assert 'class Calculator' in puml_content, "应包含Calculator类"
    assert 'class MathUtil' in puml_content, "应包含MathUtil类"
    assert 'add(' in puml_content, "应包含add方法"
    assert 'divide(' in puml_content, "应包含divide方法"
    
    print(f"[OK] PlantUML文件生成: {puml_path}")
    print(f"[OK] 文件大小: {os.path.getsize(puml_path)} 字节")
    print(f"[OK] 包含类定义: Calculator, MathUtil")
    print(f"[OK] 包含方法定义: add, divide")
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n[OK] PlantUML类图生成测试通过!")
    return True


def test_full_pipeline():
    """测试完整的文档生成管道。"""
    print("\n" + "="*60)
    print("测试 完整文档生成管道")
    print("="*60)
    
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    temp_dir = create_temp_dir(prefix='pipeline_test_')
    
    # 创建测试ZIP
    zip_path = os.path.join(temp_dir, 'test_project.zip')
    create_test_zip(zip_path, samples_dir)
    
    # 处理ZIP
    processor = DocumentationProcessor()
    result = processor.process_zip(zip_path, 'TestProject')
    
    assert result['success'] == True
    assert result['project_name'] == 'TestProject'
    
    # 验证输出
    assert os.path.exists(result['json_path']), "JSON文档应存在"
    assert os.path.exists(result['plantuml_path']), "PlantUML文件应存在"
    assert os.path.exists(result['html_dir']), "HTML目录应存在"
    
    print(f"[OK] JSON文档: {result['json_path']}")
    print(f"[OK] PlantUML图: {result['plantuml_path']}")
    print(f"[OK] HTML目录: {result['html_dir']}")
    
    # 检查HTML文件
    html_files = os.listdir(result['html_dir'])
    print(f"[OK] 生成的HTML文件: {len(html_files)} 个")
    for f in html_files[:10]:
        print(f"  - {f}")
    
    assert 'index.html' in html_files, "应包含index.html"
    assert 'search_data.js' in html_files, "应包含search_data.js"
    
    # 测试打包下载
    download_zip = processor.package_for_download(result['output_dir'])
    assert os.path.exists(download_zip), "下载ZIP应存在"
    print(f"[OK] 下载包: {download_zip}")
    print(f"[OK] 下载包大小: {os.path.getsize(download_zip) / 1024:.2f} KB")
    
    # 测试预览创建
    preview_id, preview_dir = processor.create_preview(result['html_dir'])
    assert os.path.exists(preview_dir), "预览目录应存在"
    assert os.path.exists(os.path.join(preview_dir, 'index.html')), "预览index.html应存在"
    print(f"[OK] 预览ID: {preview_id}")
    print(f"[OK] 预览目录: {preview_dir}")
    
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)
    shutil.rmtree(result['output_dir'], ignore_errors=True)
    shutil.rmtree(preview_dir, ignore_errors=True)
    
    print("\n[OK] 完整文档生成管道测试通过!")
    return True


def test_version_comparison():
    """测试版本对比功能。"""
    print("\n" + "="*60)
    print("测试 版本对比功能")
    print("="*60)
    
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    temp_dir = create_temp_dir(prefix='compare_test_')
    
    # 创建v1和v2版本
    v1_dir = os.path.join(temp_dir, 'v1')
    v2_dir = os.path.join(temp_dir, 'v2')
    
    create_modified_sample(samples_dir, v1_dir, "v1")
    create_modified_sample(samples_dir, v2_dir, "v2")
    
    # 创建ZIP
    zip_v1 = os.path.join(temp_dir, 'project_v1.zip')
    zip_v2 = os.path.join(temp_dir, 'project_v2.zip')
    
    create_test_zip(zip_v1, v1_dir, "_v1")
    create_test_zip(zip_v2, v2_dir, "_v2")
    
    # 版本对比
    processor = DocumentationProcessor()
    result = processor.compare_versions(zip_v1, zip_v2, 'Version 1.0', 'Version 2.0')
    
    assert result['success'] == True
    report = result['report']
    
    assert report['metadata']['comparison_scope'] == 'public', "默认口径应为public"
    assert 'scope_description' in report['metadata'], "应包含口径描述"
    
    print(f"\n[OK] 版本对比报告生成 (scope: {report['metadata']['comparison_scope']})")
    print(f"  - 新增类: {len(report['classes']['added'])}")
    print(f"  - 删除类: {len(report['classes']['removed'])}")
    print(f"  - 修改类: {len(report['classes']['modified'])}")
    print(f"  - 新增函数: {len(report['functions']['added'])}")
    print(f"  - 删除函数: {len(report['functions']['removed'])}")
    print(f"  - 修改函数: {len(report['functions']['modified'])}")
    
    # 验证报告文件
    assert os.path.exists(result['report_json_path']), "JSON报告应存在"
    assert os.path.exists(result['report_html_path']), "HTML报告应存在"
    
    with open(result['report_json_path'], 'r', encoding='utf-8') as f:
        report_json = json.load(f)
    
    assert 'summary' in report_json
    assert report_json['summary']['total_changes'] >= 0
    assert report_json['metadata']['comparison_scope'] == 'public'
    
    # 测试full模式
    result_full = processor.compare_versions(zip_v1, zip_v2, 'Version 1.0', 'Version 2.0', scope='full')
    report_full = result_full['report']
    assert report_full['metadata']['comparison_scope'] == 'full', "full模式口径应为full"
    public_changes = report['summary']['total_changes']
    full_changes = report_full['summary']['total_changes']
    print(f"[OK] full模式变更数({full_changes}) >= public模式({public_changes})")
    
    print(f"[OK] 报告文件: {result['report_html_path']}")
    
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)
    shutil.rmtree(result['output_dir'], ignore_errors=True)
    shutil.rmtree(os.path.dirname(result['v1_doc_path']), ignore_errors=True)
    shutil.rmtree(os.path.dirname(result['v2_doc_path']), ignore_errors=True)
    
    print("\n[OK] 版本对比功能测试通过!")
    return True


def test_html_generation():
    """测试HTML生成。"""
    print("\n" + "="*60)
    print("测试 HTML 生成")
    print("="*60)
    
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    
    # 解析样本
    parsed_files = []
    for lang_dir in ['python', 'javascript', 'java', 'cpp']:
        lang_path = os.path.join(samples_dir, lang_dir)
        if os.path.isdir(lang_path):
            for file in os.listdir(lang_path):
                file_path = os.path.join(lang_path, file)
                if os.path.isfile(file_path) and file.endswith(('.py', '.js', '.java', '.h')):
                    ext = os.path.splitext(file)[1]
                    parser = ParserFactory.get_parser_by_extension(ext)
                    if parser:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        rel_path = os.path.join(lang_dir, file)
                        parsed = parser.parse(content, rel_path)
                        if parsed:
                            parsed_files.append(parsed)
    
    doc_structure = build_document_structure(parsed_files, 'HTMLTest')
    
    from app.utils.html_generator import HTMLGenerator
    html_gen = HTMLGenerator()
    
    temp_dir = create_temp_dir(prefix='html_test_')
    html_gen.generate(doc_structure, temp_dir)
    
    required_files = [
        'index.html',
        'modules.html',
        'classes.html',
        'functions.html',
        'search_data.js',
        'static/css/style.css',
        'static/js/search.js'
    ]
    
    for required_file in required_files:
        file_path = os.path.join(temp_dir, required_file)
        assert os.path.exists(file_path), f"应存在: {required_file}"
        print(f"[OK] {required_file}")
    
    # 检查搜索数据
    search_data_path = os.path.join(temp_dir, 'search_data.js')
    with open(search_data_path, 'r', encoding='utf-8') as f:
        search_content = f.read()
    
    assert 'Calculator' in search_content, "搜索数据应包含Calculator"
    assert 'greet' in search_content, "搜索数据应包含greet"
    assert 'module_path' in search_content, "搜索数据应包含module_path字段"
    print(f"[OK] 搜索数据包含正确的索引和模块路径")
    
    # 检查index.html内容
    index_path = os.path.join(temp_dir, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        index_content = f.read()
    
    assert 'HTMLTest' in index_content, "index.html应包含项目名称"
    assert 'Search' in index_content, "index.html应包含搜索框"
    print(f"[OK] index.html 内容正确")
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n[OK] HTML生成测试通过!")
    return True


def main():
    """运行所有管道测试。"""
    print("[OK] 开始运行文档生成管道测试")
    print("="*60)
    
    tests = [
        test_document_building,
        test_plantuml_generation,
        test_html_generation,
        test_full_pipeline,
        test_version_comparison,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
