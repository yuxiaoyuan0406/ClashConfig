from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def get_config():
    url = request.args.get('url')
    if url:
        # 调用 get_config.py 脚本
        subprocess.run(['python', 'main.py', '--url', url, '--output', 'output.yaml'])
        # 确保文件已生成
        if os.path.exists('output.yaml'):
            status = send_file('output.yaml')
            subprocess.run(['rm', 'output.yaml'])
            return status
        else:
            return "Failed to generate output file", 500
    else:
        return "No URL provided", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6789)
