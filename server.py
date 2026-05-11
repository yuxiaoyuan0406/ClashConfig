from flask import Flask, request, send_file
import subprocess
import os
import tempfile

app = Flask(__name__)


@app.route('/')
def get_config():
    url = request.args.get('url')
    user_agent = request.args.get('ua')
    if not url:
        return "No URL provided", 400

    with tempfile.NamedTemporaryFile(prefix='clash-config-', suffix='.yaml', delete=False) as tmp:
        output_path = tmp.name

    cmd = ['python', 'main.py', '--url', url, '--output', output_path]
    if user_agent:
        cmd.extend(['--user-agent', user_agent])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if os.path.exists(output_path):
            os.remove(output_path)
        return result.stderr or "Failed to generate output file", 500

    if os.path.exists(output_path):
        response = send_file(output_path, as_attachment=True, download_name='config.yaml')
        # Flask sends the file after this function returns; removing immediately
        # can break some servers. Keep the temp file for system cleanup instead.
        return response
    return "Failed to generate output file", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6789)
