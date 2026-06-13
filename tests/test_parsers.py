"""
多语言解析器单元测试。
测试Python、JavaScript、Java和C++解析器的基本功能。
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.parser_factory import ParserFactory
from app.parsers.python_parser import PythonParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.java_parser import JavaParser
from app.parsers.cpp_parser import CppParser


def read_sample_file(path):
    """读取示例文件内容。"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_python_parser():
    """测试Python解析器。"""
    print("\n" + "="*60)
    print("测试 Python 解析器")
    print("="*60)
    
    sample_path = os.path.join(os.path.dirname(__file__), 'samples', 'python', 'sample_module.py')
    content = read_sample_file(sample_path)
    
    parser = PythonParser()
    result = parser.parse(content, 'python/sample_module.py')
    
    assert result is not None, "解析结果不应为None"
    assert result['language'] == 'python', "语言应为python"
    assert result['relative_path'] == 'python/sample_module.py', "文件路径不匹配"
    
    module_name = os.path.splitext(os.path.basename(result['relative_path']))[0]
    print(f"[OK] 模块: {module_name}")
    print(f"[OK] 描述: {result['module_description'][:50]}...")
    print(f"[OK] 作者: {result['author']}")
    print(f"[OK] 版本: {result['version']}")
    
    assert len(result['classes']) >= 2, f"至少应有2个类，实际有{len(result['classes'])}个"
    assert len(result['functions']) >= 2, f"至少应有2个函数，实际有{len(result['functions'])}个"
    
    calc_class = next((c for c in result['classes'] if c['name'] == 'Calculator'), None)
    assert calc_class is not None, "应找到Calculator类"
    print(f"\n[OK] 类: {calc_class['name']}")
    print(f"  - 描述: {calc_class['description'][:30]}...")
    print(f"  - 方法数: {len(calc_class['methods'])}")
    
    add_method = next((m for m in calc_class['methods'] if m['name'] == 'add'), None)
    assert add_method is not None, "应找到add方法"
    print(f"    [OK] 方法: {add_method['signature']}")
    print(f"      - 参数: {[p['name'] for p in add_method['parameters']]}")
    print(f"      - 返回: {add_method['return_type']}")
    print(f"      - 示例数: {len(add_method['examples'])}")
    
    divide_method = next((m for m in calc_class['methods'] if m['name'] == 'divide'), None)
    assert divide_method is not None, "应找到divide方法"
    print(f"    [OK] 方法: {divide_method['name']}")
    print(f"      - 异常: {[e['name'] for e in divide_method.get('exceptions', [])]}")
    print(f"      - 描述: {divide_method.get('description', '')[:30]}...")
    
    greet_func = next((f for f in result['functions'] if f['name'] == 'greet'), None)
    assert greet_func is not None, "应找到greet函数"
    print(f"\n[OK] 函数: {greet_func['signature']}")
    
    print("\n[OK] Python 解析器测试通过!")
    return True


def test_javascript_parser():
    """测试JavaScript解析器。"""
    print("\n" + "="*60)
    print("测试 JavaScript 解析器")
    print("="*60)
    
    sample_path = os.path.join(os.path.dirname(__file__), 'samples', 'javascript', 'sample_module.js')
    content = read_sample_file(sample_path)
    
    parser = JavaScriptParser()
    result = parser.parse(content, 'javascript/sample_module.js')
    
    assert result is not None, "解析结果不应为None"
    assert result['language'] == 'javascript', "语言应为javascript"
    
    module_name = os.path.splitext(os.path.basename(result['relative_path']))[0]
    print(f"[OK] 模块: {module_name}")
    print(f"[OK] 描述: {result['module_description'][:50]}...")
    print(f"[OK] 作者: {result['author']}")
    print(f"[OK] 版本: {result['version']}")
    
    assert len(result['classes']) >= 2, f"至少应有2个类，实际有{len(result['classes'])}个"
    assert len(result['functions']) >= 2, f"至少应有2个函数，实际有{len(result['functions'])}个"
    
    calc_class = next((c for c in result['classes'] if c['name'] == 'Calculator'), None)
    assert calc_class is not None, "应找到Calculator类"
    print(f"\n[OK] 类: {calc_class['name']}")
    print(f"  - 方法数: {len(calc_class['methods'])}")
    
    add_method = next((m for m in calc_class['methods'] if m['name'] == 'add'), None)
    assert add_method is not None, "应找到add方法"
    print(f"    [OK] 方法: {add_method['signature']}")
    print(f"      - 参数: {[p['name'] for p in add_method['parameters']]}")
    print(f"      - 返回: {add_method.get('return_type', '')}")
    
    interfaces = result.get('interfaces', [])
    if interfaces:
        print(f"\n[OK] 接口: {interfaces[0]['name']}")
    
    print("\n[OK] JavaScript 解析器测试通过!")
    return True


def test_java_parser():
    """测试Java解析器。"""
    print("\n" + "="*60)
    print("测试 Java 解析器")
    print("="*60)
    
    sample_path = os.path.join(os.path.dirname(__file__), 'samples', 'java', 'SampleModule.java')
    content = read_sample_file(sample_path)
    
    parser = JavaParser()
    result = parser.parse(content, 'java/SampleModule.java')
    
    assert result is not None, "解析结果不应为None"
    assert result['language'] == 'java', "语言应为java"
    
    module_name = os.path.splitext(os.path.basename(result['relative_path']))[0]
    print(f"[OK] 模块: {module_name}")
    print(f"[OK] 包: {result.get('package', 'N/A')}")
    print(f"[OK] 描述: {result['module_description'][:50]}...")
    print(f"[OK] 作者: {result['author']}")
    print(f"[OK] 版本: {result['version']}")
    
    assert len(result['classes']) >= 2, f"至少应有2个类，实际有{len(result['classes'])}个"
    
    interfaces = result.get('interfaces', [])
    enums = result.get('enums', [])
    
    calc_class = next((c for c in result['classes'] if c['name'] == 'Calculator'), None)
    assert calc_class is not None, "应找到Calculator类"
    print(f"\n[OK] 类: {calc_class['name']}")
    print(f"  - 方法数: {len(calc_class['methods'])}")
    
    add_method = next((m for m in calc_class['methods'] if m['name'] == 'add'), None)
    assert add_method is not None, "应找到add方法"
    print(f"    [OK] 方法: {add_method['signature']}")
    print(f"      - 参数: {[p['name'] for p in add_method['parameters']]}")
    print(f"      - 返回: {add_method['return_type']}")
    
    divide_method = next((m for m in calc_class['methods'] if m['name'] == 'divide'), None)
    assert divide_method is not None, "应找到divide方法"
    assert len(divide_method['exceptions']) >= 1, "divide方法应抛出异常"
    print(f"    [OK] 方法: {divide_method['name']}")
    print(f"      - 异常: {[e['name'] for e in divide_method['exceptions']]}")
    
    if interfaces:
        print(f"\n[OK] 接口: {interfaces[0]['name']}")
    if enums:
        print(f"[OK] 枚举: {enums[0]['name']}")
    
    print("\n[OK] Java 解析器测试通过!")
    return True


def test_cpp_parser():
    """测试C++解析器。"""
    print("\n" + "="*60)
    print("测试 C++ 解析器")
    print("="*60)
    
    sample_path = os.path.join(os.path.dirname(__file__), 'samples', 'cpp', 'sample_module.h')
    content = read_sample_file(sample_path)
    
    parser = CppParser()
    result = parser.parse(content, 'cpp/sample_module.h')
    
    assert result is not None, "解析结果不应为None"
    assert result['language'] == 'cpp', "语言应为cpp"
    
    module_name = os.path.splitext(os.path.basename(result['relative_path']))[0]
    print(f"[OK] 模块: {module_name}")
    print(f"[OK] 命名空间: {result.get('namespace', 'N/A')}")
    print(f"[OK] 描述: {result['module_description'][:50]}...")
    print(f"[OK] 作者: {result['author']}")
    print(f"[OK] 版本: {result['version']}")
    
    assert len(result['classes']) >= 2, f"至少应有2个类，实际有{len(result['classes'])}个"
    assert len(result['functions']) >= 2, f"至少应有2个函数，实际有{len(result['functions'])}个"
    
    structs = result.get('structs', [])
    enums = result.get('enums', [])
    
    calc_class = next((c for c in result['classes'] if c['name'] == 'Calculator'), None)
    assert calc_class is not None, "应找到Calculator类"
    print(f"\n[OK] 类: {calc_class['name']}")
    print(f"  - 方法数: {len(calc_class['methods'])}")
    
    add_method = next((m for m in calc_class['methods'] if m['name'] == 'add'), None)
    assert add_method is not None, "应找到add方法"
    print(f"    [OK] 方法: {add_method['signature']}")
    print(f"      - 参数: {[p['name'] for p in add_method['parameters']]}")
    print(f"      - 返回: {add_method.get('return_type', '')}")
    print(f"      - 示例数: {len(add_method.get('examples', []))}")
    
    divide_method = next((m for m in calc_class['methods'] if m['name'] == 'divide'), None)
    assert divide_method is not None, "应找到divide方法"
    print(f"    [OK] 方法: {divide_method['name']}")
    print(f"      - 异常: {[e['name'] for e in divide_method.get('exceptions', [])]}")
    print(f"      - 描述: {divide_method.get('description', '')[:30]}...")
    
    if structs:
        print(f"\n[OK] 结构体: {structs[0]['name']}")
    if enums:
        print(f"[OK] 枚举: {enums[0]['name']}")
    
    greet_func = next((f for f in result['functions'] if f['name'] == 'greet'), None)
    assert greet_func is not None, "应找到greet函数"
    print(f"[OK] 函数: {greet_func['signature']}")
    
    print("\n[OK] C++ 解析器测试通过!")
    return True


def test_parser_factory():
    """测试解析器工厂。"""
    print("\n" + "="*60)
    print("测试 解析器工厂")
    print("="*60)
    
    # 测试按语言获取解析器
    python_parser = ParserFactory.get_parser('python')
    assert python_parser is not None, "应获取到python解析器"
    assert isinstance(python_parser, PythonParser), "类型应为PythonParser"
    print("[OK] Python 解析器获取成功")
    
    js_parser = ParserFactory.get_parser('javascript')
    assert js_parser is not None, "应获取到javascript解析器"
    assert isinstance(js_parser, JavaScriptParser), "类型应为JavaScriptParser"
    print("[OK] JavaScript 解析器获取成功")
    
    java_parser = ParserFactory.get_parser('java')
    assert java_parser is not None, "应获取到java解析器"
    assert isinstance(java_parser, JavaParser), "类型应为JavaParser"
    print("[OK] Java 解析器获取成功")
    
    cpp_parser = ParserFactory.get_parser('cpp')
    assert cpp_parser is not None, "应获取到cpp解析器"
    assert isinstance(cpp_parser, CppParser), "类型应为CppParser"
    print("[OK] C++ 解析器获取成功")
    
    # 测试按扩展名获取语言
    assert ParserFactory.get_language_by_extension('.py') == 'python', ".py应为python"
    assert ParserFactory.get_language_by_extension('.js') == 'javascript', ".js应为javascript"
    assert ParserFactory.get_language_by_extension('.java') == 'java', ".java应为java"
    assert ParserFactory.get_language_by_extension('.cpp') == 'cpp', ".cpp应为cpp"
    assert ParserFactory.get_language_by_extension('.h') == 'cpp', ".h应为cpp"
    print("[OK] 扩展名到语言映射正确")
    
    # 测试按扩展名获取解析器
    py_parser = ParserFactory.get_parser_by_extension('.py')
    assert isinstance(py_parser, PythonParser), ".py应获取PythonParser"
    print("[OK] 按扩展名获取解析器成功")
    
    print("\n[OK] 解析器工厂测试通过!")
    return True


def main():
    """运行所有解析器测试。"""
    print("[OK] 开始运行解析器单元测试")
    print("="*60)
    
    tests = [
        test_parser_factory,
        test_python_parser,
        test_javascript_parser,
        test_java_parser,
        test_cpp_parser,
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
