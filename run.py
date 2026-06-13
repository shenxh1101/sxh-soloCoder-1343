import os
import sys
from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 代码文档生成器服务启动中...")
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"🌐 支持语言: Python / JavaScript / Java / C++")
    print(f"📁 上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"📄 临时输出: {app.config['TEMP_OUTPUT_FOLDER']}")
    print(f"👁️  预览目录: {app.config['PREVIEW_FOLDER']}")
    print(f"⏱️  预览有效期: {app.config['PREVIEW_EXPIRY_HOURS']} 小时")
    print("="*60)
    
    app.run(host=host, port=port, debug=debug, threaded=True)
