import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("Переменная окружения GITHUB_TOKEN не задана.")

REPO_OWNER = "FlipSize"
REPO_NAME = "BlackSunVPN"
FILE_PATH = "rules/ru-blocked"

# URL для скачивания файлов
REPO_1_URL = "https://api.github.com/repos/runetfreedom/russia-blocked-geosite/releases/latest"
REPO_2_URL = "https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts.txt"

def fetch_file_from_repo_1():
    """Загружает последний релиз из первого репозитория."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(REPO_1_URL, headers=headers)
    if response.status_code != 200:
        print("Не удалось получить информацию о релизах:", response.status_code)
        return []
    
    release_data = response.json()
    assets = release_data.get("assets", [])
    target_file_name = "ru-blocked.txt"
    
    for asset in assets:
        if asset["name"] == target_file_name:
            file_url = asset["browser_download_url"]
            return fetch_and_process_file(file_url)
    
    print(f"Файл {target_file_name} не найден в последнем релизе.")
    return []

def fetch_file_from_repo_2():
    """Загружает данные из второго репозитория (hosts.txt)."""
    response = requests.get(REPO_2_URL)
    if response.status_code != 200:
        print("Не удалось скачать файл с hosts.txt:", response.status_code)
        return []
    return process_hosts_file(response.text)

def fetch_and_process_file(file_url):
    """Загружает и обрабатывает файл по URL."""
    response = requests.get(file_url)
    if response.status_code != 200:
        print("Не удалось скачать файл:", response.status_code)
        return []
    
    return process_ru_blocked_file(response.text)

def process_ru_blocked_file(content):
    """Обрабатывает файл ru-blocked.txt."""
    lines = content.strip().splitlines()
    domains = []
    
    for line in lines:
        if line.startswith("domain:"):
            domain = line.replace("domain:", "").strip()
            domains.append(domain)
    
    return domains

def process_hosts_file(content):
    """Обрабатывает файл hosts.txt."""
    lines = content.strip().splitlines()
    domains = []
    
    for line in lines:
        line = line.strip()
        # Игнорируем комментарии и пустые строки
        if line.startswith("#") or not line:
            continue
        domains.append(line)
    
    return domains

def generate_payload(domains):
    """Генерирует строку с payload для загрузки на GitHub."""
    processed_lines = ["payload:"]
    seen_domains = set()  # Множество для проверки на дубли
    
    for domain in domains:
        if domain not in seen_domains:
            seen_domains.add(domain)
            processed_lines.append(f"- '+.{domain}'")
    
    return "\n".join(processed_lines)

def upload_to_github(content):
    """Загружает файл на GitHub."""
    file_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(file_url, headers=headers)
    file_exists = response.status_code == 200
    
    payload = {
        "message": "Update ru-blocked",
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
    # Получаем домены из первого репозитория
    domains_from_repo_1 = fetch_file_from_repo_1()
    if not domains_from_repo_1:
        return
    
    # Получаем домены из второго репозитория
    domains_from_repo_2 = fetch_file_from_repo_2()
    if not domains_from_repo_2:
        return
    
    # Объединяем оба списка доменов и устраняем дубли
    all_domains = domains_from_repo_1 + domains_from_repo_2
    
    # Генерируем payload
    file_content = generate_payload(all_domains)
    
    # Загружаем на GitHub
    upload_to_github(file_content)

if __name__ == "__main__":
    main()
