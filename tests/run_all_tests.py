"""
测试运行器 - 运行所有测试并生成报告。
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test(script_name, description):
    """运行单个测试脚本。"""
    print("\n" + "="*70)
    print(f"▶ 运行: {description}")
    print("="*70)
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    start_time = time.time()
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        elapsed = time.time() - start_time
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print(result.stderr)
        
        success = result.returncode == 0
        status = "[PASS] 通过" if success else "[FAIL] 失败"
        
        print(f"\n{status} - 耗时: {elapsed:.2f}秒")
        
        return {
            'name': description,
            'script': script_name,
            'success': success,
            'elapsed': elapsed,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] 超时 - 耗时: {elapsed:.2f}秒")
        return {
            'name': description,
            'script': script_name,
            'success': False,
            'elapsed': elapsed,
            'output': '',
            'error': '测试超时'
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAIL] 错误: {e}")
        return {
            'name': description,
            'script': script_name,
            'success': False,
            'elapsed': elapsed,
            'output': '',
            'error': str(e)
        }


def generate_report(results, output_path):
    """生成测试报告。"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'passed': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'total_time': sum(r['elapsed'] for r in results),
        'results': results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


def print_summary(results):
    """打印测试摘要。"""
    print("\n" + "="*70)
    print("[STAT] 测试结果摘要")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    total_time = sum(r['elapsed'] for r in results)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} [FAIL]")
    print(f"总耗时: {total_time:.2f}秒")
    
    print("\n详细结果:")
    print("-" * 70)
    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "[FAIL]"
        print(f"{i:2d}. {status} {result['name']:<40} {result['elapsed']:>6.2f}s")
    print("-" * 70)
    
    if failed > 0:
        print("\n失败的测试:")
        for result in results:
            if not result['success']:
                print(f"  [FAIL] {result['name']}")
                if result['error']:
                    error_preview = result['error'][:200] + '...' if len(result['error']) > 200 else result['error']
                    print(f"     {error_preview}")
    
    return failed == 0


def main():
    """主函数。"""
    print("[OK] 代码文档生成器 - 完整测试套件")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ('test_parsers.py', '解析器单元测试'),
        ('test_pipeline.py', '文档生成管道测试'),
        ('test_api.py', 'Flask API集成测试'),
    ]
    
    results = []
    for script_name, description in tests:
        result = run_test(script_name, description)
        results.append(result)
        
        # 如果第一个测试失败，可能需要检查依赖
        if not result['success'] and script_name == 'test_parsers.py':
            print("\n[WARN]  解析器测试失败，检查是否需要安装依赖...")
            print("运行: pip install -r requirements.txt")
    
    # 生成报告
    report_path = os.path.join(os.path.dirname(__file__), 'test_report.json')
    report = generate_report(results, report_path)
    print(f"\n[DOC] 测试报告已保存: {report_path}")
    
    # 打印摘要
    all_passed = print_summary(results)
    
    print("\n" + "="*70)
    if all_passed:
        print("[PASS] 所有测试通过!")
    else:
        print("[WARN] 部分测试失败，请查看详细输出")
    print("="*70)
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
