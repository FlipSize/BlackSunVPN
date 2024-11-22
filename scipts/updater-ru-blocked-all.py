import requests
import base64
import os

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("Переменная окружения GITHUB_TOKEN не задана.")

REPO_OWNER = "FlipSize"
REPO_NAME = "BlackSunVPN"
FILE_PATH = "rules/ru-blocked-all" 

def fetch_latest_release_file():
    releases_url = "https://api.github.com/repos/runetfreedom/russia-blocked-geosite/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}

    response = requests.get(releases_url, headers=headers)
    if response.status_code != 200:
        print("Не удалось получить информацию о релизах:", response.status_code)
        return

    release_data = response.json()
    assets = release_data.get("assets", [])
    
    target_file_name = "ru-blocked-all.txt"
    for asset in assets:
        if asset["name"] == target_file_name:
            return asset["browser_download_url"]
    
    print(f"Файл {target_file_name} не найден в последнем релизе.")
    return None

def process_file(file_url):
    response = requests.get(file_url)
    if response.status_code != 200:
        print("Не удалось скачать файл:", response.status_code)
        return None

    lines = response.text.strip().splitlines()
    processed_lines = ["payload:"]
    for line in lines:
        if line.startswith("domain:"):
            domain = line.replace("domain:", "").strip()
            processed_lines.append(f"- '+.{domain}'")
    
    return "\n".join(processed_lines)

def upload_to_github(content):
    file_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(file_url, headers=headers)
    file_exists = response.status_code == 200
    
    payload = {
        "message": "Update ru-blocked-all",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    
    if file_exists:
        sha = response.json()["sha"]
        payload["sha"] = sha
    
    response = requests.put(file_url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"Файл успешно {'обновлен' if file_exists else 'создан'} на GitHub.")
    else:
        print(f"Ошибка при загрузке файла на GitHub: {response.status_code}, {response.text}")

def main():
    file_url = fetch_latest_release_file()
    if not file_url:
        return
    
    file_content = process_file(file_url)
    if not file_content:
        return
    
    upload_to_github(file_content)

if __name__ == "__main__":
    main()
