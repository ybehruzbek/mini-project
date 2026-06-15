import requests
import zipfile
import io

# 1. Get latest workflow runs
resp = requests.get('https://api.github.com/repos/ybehruzbek/mini-project/actions/runs')
runs = resp.json().get('workflow_runs', [])
if not runs:
    print('No runs found')
    exit()

latest_run = runs[0]
print(f'Latest Run ID: {latest_run["id"]}')
print(f'Status: {latest_run["status"]}, Conclusion: {latest_run["conclusion"]}')

# 2. Get logs URL
logs_url = latest_run['logs_url']
print(f'Fetching logs from: {logs_url}')

# 3. Download and extract logs
log_resp = requests.get(logs_url)
if log_resp.status_code == 200:
    with zipfile.ZipFile(io.BytesIO(log_resp.content)) as z:
        for filename in z.namelist():
            if 'Run Bot.txt' in filename or 'Install Dependencies.txt' in filename:
                print(f'\n--- {filename} ---')
                print(z.read(filename).decode('utf-8')[-2000:])
else:
    print('Failed to download logs:', log_resp.status_code)
