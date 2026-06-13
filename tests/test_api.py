"""
Flask API 集成测试。
测试REST API接口、任务队列和轮询功能。
"""

import os
import sys
import json
import time
import zipfile
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


def create_test_zip_from_samples():
    """从样本文件创建测试ZIP。"""
    samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
    temp_dir = tempfile.mkdtemp(prefix='api_test_')
    zip_path = os.path.join(temp_dir, 'test_api_project.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(samples_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, samples_dir)
                zipf.write(file_path, arcname)
    
    return zip_path, temp_dir


def test_health_check(client):
    """测试健康检查接口。"""
    print("\n" + "="*60)
    print("测试 API 健康检查")
    print("="*60)
    
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'Code Documentation Generator API'
    assert 'python' in data['supported_languages']
    assert 'javascript' in data['supported_languages']
    assert 'java' in data['supported_languages']
    assert 'cpp' in data['supported_languages']
    
    print(f"[OK] 状态码: {response.status_code}")
    print(f"[OK] 服务状态: {data['status']}")
    print(f"[OK] 支持语言: {', '.join(data['supported_languages'])}")
    print("\n[OK] 健康检查测试通过!")


def test_home_page(client):
    """测试主页。"""
    print("\n" + "="*60)
    print("测试 主页访问")
    print("="*60)
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Code Documentation Generator' in response.data or b'\xe4\xbb\xa3\xe7\xa0\x81' in response.data
    
    print(f"[OK] 状态码: {response.status_code}")
    print("[OK] 主页内容正确")
    print("\n[OK] 主页测试通过!")


def test_api_generate_task(client):
    """测试创建文档生成任务API。"""
    print("\n" + "="*60)
    print("测试 API 创建生成任务")
    print("="*60)
    
    zip_path, temp_dir = create_test_zip_from_samples()
    
    try:
        with open(zip_path, 'rb') as f:
            data = {
                'type': 'generate',
                'project_name': 'API Test Project',
                'file': (f, 'test_project.zip')
            }
            response = client.post('/api/tasks', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 202
        
        result = json.loads(response.data)
        assert 'task_id' in result
        assert result['type'] == 'generate'
        assert result['status'] in ['pending', 'processing', 'completed']
        assert 'status_url' in result
        
        task_id = result['task_id']
        print(f"[OK] 任务创建成功")
        print(f"  - 任务ID: {task_id}")
        print(f"  - 状态: {result['status']}")
        print(f"  - 状态URL: {result['status_url']}")
        
        # 轮询任务状态
        print("\n[WAIT] 轮询任务状态...")
        max_wait = 60
        start_time = time.time()
        final_status = None
        
        while time.time() - start_time < max_wait:
            status_response = client.get(f'/api/tasks/{task_id}')
            assert status_response.status_code == 200
            
            status_data = json.loads(status_response.data)
            current_status = status_data['status']
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] 状态: {current_status}")
            
            if current_status == 'completed':
                final_status = status_data
                break
            elif current_status == 'failed':
                print(f"  [FAIL] 任务失败: {status_data.get('error', '未知错误')}")
                assert False, f"任务失败: {status_data.get('error', '未知错误')}"
            
            time.sleep(2)
        
        assert final_status is not None, "任务超时未完成"
        assert final_status['status'] == 'completed'
        assert 'result' in final_status
        
        result_data = final_status['result']
        assert 'download_zip' in result_data or 'download_url' in result_data
        assert 'preview_id' in result_data
        assert 'preview_url' in result_data
        assert 'json_url' in result_data, "应包含结构化JSON下载地址"
        assert 'plantuml_url' in result_data, "应包含PlantUML下载地址"
        assert 'tasks/' in result_data['json_url'], "JSON URL应包含任务ID路径"
        assert 'tasks/' in result_data['plantuml_url'], "PlantUML URL应包含任务ID路径"
        
        print(f"\n[OK] 任务完成")
        print(f"  - 下载URL: {result_data.get('download_url', 'N/A')}")
        print(f"  - 预览URL: {result_data.get('preview_url', 'N/A')}")
        print(f"  - JSON URL: {result_data.get('json_url', 'N/A')}")
        print(f"  - PlantUML URL: {result_data.get('plantuml_url', 'N/A')}")
        
        def _test_url(name, url):
            path = url.replace('http://localhost', '')
            response = client.get(path)
            assert response.status_code == 200, f"{name}链接应可访问: {path}"
            print(f"[OK] {name}链接可访问")
        
        _test_url("文档站下载", result_data['download_url'])
        _test_url("预览", result_data['preview_url'])
        _test_url("JSON文档", result_data['json_url'])
        _test_url("PlantUML", result_data['plantuml_url'])
        
        print("\n[OK] API生成任务测试通过!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_api_list_tasks(client):
    """测试获取任务列表API。"""
    print("\n" + "="*60)
    print("测试 API 任务列表")
    print("="*60)
    
    response = client.get('/api/tasks')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'tasks' in data
    assert isinstance(data['tasks'], list)
    
    print(f"[OK] 状态码: {response.status_code}")
    print(f"[OK] 任务数量: {len(data['tasks'])}")
    
    if data['tasks']:
        print(f"[OK] 任务列表包含:")
        for task in data['tasks'][:3]:
            print(f"  - {task['task_id']}: {task['status']} ({task['type']})")
    
    print("\n✅ 任务列表测试通过!")


def test_api_invalid_task_type(client):
    """测试无效任务类型。"""
    print("\n" + "="*60)
    print("测试 API 无效任务类型")
    print("="*60)
    
    response = client.post('/api/tasks', 
                          data=json.dumps({'type': 'invalid_type'}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    
    print(f"[OK] 状态码: {response.status_code}")
    print(f"[OK] 错误信息: {data['error']}")
    print("\n[OK] 无效任务类型测试通过!")


def test_api_task_not_found(client):
    """测试不存在的任务ID。"""
    print("\n" + "="*60)
    print("测试 API 任务不存在")
    print("="*60)
    
    response = client.get('/api/tasks/nonexistent_task_id')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert 'error' in data
    
    print(f"[OK] 状态码: {response.status_code}")
    print(f"[OK] 错误信息: {data['error']}")
    print("\n[OK] 任务不存在测试通过!")


def test_api_compare_task(client):
    """测试版本对比任务API。"""
    print("\n" + "="*60)
    print("测试 API 版本对比任务")
    print("="*60)
    
    zip_path1, temp_dir1 = create_test_zip_from_samples()
    zip_path2, temp_dir2 = create_test_zip_from_samples()
    
    try:
        with open(zip_path1, 'rb') as f1, open(zip_path2, 'rb') as f2:
            data = {
                'type': 'compare',
                'name_v1': 'Version 1.0',
                'name_v2': 'Version 2.0',
                'file_v1': (f1, 'project_v1.zip'),
                'file_v2': (f2, 'project_v2.zip')
            }
            response = client.post('/api/tasks', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 202
        
        result = json.loads(response.data)
        assert 'task_id' in result
        assert result['type'] == 'compare'
        
        task_id = result['task_id']
        print(f"[OK] 对比任务创建成功")
        print(f"  - 任务ID: {task_id}")
        
        # 轮询任务状态
        print("\n[WAIT] 轮询任务状态...")
        max_wait = 60
        start_time = time.time()
        final_status = None
        
        while time.time() - start_time < max_wait:
            status_response = client.get(f'/api/tasks/{task_id}')
            status_data = json.loads(status_response.data)
            current_status = status_data['status']
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] 状态: {current_status}")
            
            if current_status == 'completed':
                final_status = status_data
                break
            elif current_status == 'failed':
                print(f"  [FAIL] 任务失败: {status_data.get('error', '未知错误')}")
                assert False, f"任务失败: {status_data.get('error', '未知错误')}"
            
            time.sleep(2)
        
        assert final_status is not None, "任务超时未完成"
        assert final_status['status'] == 'completed'
        
        result_data = final_status.get('result', {})
        assert 'report_json_url' in result_data, "应包含对比报告JSON地址"
        assert 'report_html_url' in result_data, "应包含对比报告HTML地址"
        assert 'download_url' in result_data, "应包含打包下载地址"
        assert 'v1_doc_url' in result_data, "应包含V1文档JSON地址"
        assert 'v2_doc_url' in result_data, "应包含V2文档JSON地址"
        assert 'v1_plantuml_url' in result_data, "应包含V1 PlantUML地址"
        assert 'v2_plantuml_url' in result_data, "应包含V2 PlantUML地址"
        assert 'tasks/' in result_data['report_json_url'], "报告URL应包含任务ID路径"
        assert '/v1/' in result_data['v1_doc_url'], "V1文档URL应包含v1子路径"
        
        print(f"\n[OK] 对比任务完成")
        print(f"  - 报告HTML URL: {result_data.get('report_html_url', 'N/A')}")
        print(f"  - 报告JSON URL: {result_data.get('report_json_url', 'N/A')}")
        print(f"  - 打包下载URL: {result_data.get('download_url', 'N/A')}")
        print(f"  - V1文档URL: {result_data.get('v1_doc_url', 'N/A')}")
        print(f"  - V2文档URL: {result_data.get('v2_doc_url', 'N/A')}")
        print(f"  - V1 PlantUML URL: {result_data.get('v1_plantuml_url', 'N/A')}")
        print(f"  - V2 PlantUML URL: {result_data.get('v2_plantuml_url', 'N/A')}")
        
        def _test_url(name, url):
            path = url.replace('http://localhost', '')
            response = client.get(path)
            assert response.status_code == 200, f"{name}链接应可访问: {path}"
            print(f"[OK] {name}链接可访问")
        
        _test_url("对比报告HTML", result_data['report_html_url'])
        _test_url("对比报告JSON", result_data['report_json_url'])
        _test_url("V1文档JSON", result_data['v1_doc_url'])
        _test_url("V2文档JSON", result_data['v2_doc_url'])
        _test_url("打包下载", result_data['download_url'])
        
        print("\n[OK] API版本对比任务测试通过!")
        
    finally:
        shutil.rmtree(temp_dir1, ignore_errors=True)
        shutil.rmtree(temp_dir2, ignore_errors=True)


def main():
    """运行API测试。"""
    print("[OK] 开始运行Flask API集成测试")
    print("="*60)
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        tests = [
            ('健康检查', lambda: test_health_check(client)),
            ('主页访问', lambda: test_home_page(client)),
            ('任务列表', lambda: test_api_list_tasks(client)),
            ('无效任务类型', lambda: test_api_invalid_task_type(client)),
            ('任务不存在', lambda: test_api_task_not_found(client)),
            ('创建生成任务', lambda: test_api_generate_task(client)),
            ('版本对比任务', lambda: test_api_compare_task(client)),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"\n[FAIL] 测试失败: {test_name}")
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
