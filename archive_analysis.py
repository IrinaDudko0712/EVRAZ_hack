import zipfile
import os
import json
import csv
import fnmatch

import requests
import json
import pandas as pd
import subprocess
import faiss
from sentence_transformers import SentenceTransformer


####   Подготовка архива   ######

# Преобразование списка папок в дерево
expected_folders_tree = {
    "core": {
        "models": None,
        "services": None,
        "usecases": None,
    },
    "adapters": {
        "db": None,
        "api*": None,
        "ui": None,
    },
    "tests": {}
}


def unzip_and_list_files_from_file(zip_file, extract_to):
    # Используем BytesIO для работы с файлом в памяти
    zip_name = "uploaded_archive"  # Или задайте имя по заголовкам, если известно
    extract_folder = os.path.join(extract_to, zip_name)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
        return list_files(extract_folder)


def list_files(directory):
    if not os.path.exists(directory):
        print(f"[ERROR] Directory does not exist: {directory}")
        return set(), {}

    folder_structure = {}
    folder_list = set()

    for root, dirs, files in os.walk(directory):
        relative_path = os.path.relpath(root, directory).replace("\\", "/")
        if relative_path == ".":
            relative_path = ""
        if relative_path and not relative_path.startswith("."):
            folder_list.add(relative_path)

        # Создаем вложенную структуру для папок и файлов
        current_level = folder_structure
        if relative_path:
            parts = relative_path.split("/")
            for part in parts:
                current_level = current_level.setdefault(part, {})

        for dir_name in dirs:
            if not dir_name.startswith("."):
                current_level[dir_name] = {}

        for file_name in files:
            if not file_name.startswith("."):
                current_level[file_name] = None  # Файлы отмечаем как None

    return folder_list, folder_structure


def check_structure(found_folders, folder_tree, base_path=""):
    results = {}
    for folder, subfolders in folder_tree.items():
        full_path = f"{base_path}/{folder}".strip("/")
        if "*" in folder:
            matching_folders = [f for f in found_folders if fnmatch.fnmatch(f, full_path)]
            folder_exists = bool(matching_folders)
        else:
            folder_exists = full_path in found_folders
        results[full_path] = 1 if folder_exists else 0
        if subfolders:
            results.update(check_structure(found_folders, subfolders, full_path))
    return results


def generate_report(check_results, zip_name):
    report_lines = []
    for folder, status in check_results.items():
        if status:
            report_lines.append(f'Folder "{folder}" is in project "{zip_name}".')
        else:
            report_lines.append(f'Folder "{folder}" is missing in project "{zip_name}".')
    return "\n".join(report_lines)


def save_structure_to_md_as_tree(folder_structure, zip_name, output_path):
    def write_structure_as_tree_md(structure, prefix=""):
        lines = []
        for name, content in structure.items():
            lines.append(f"{prefix}- {name}")
            if isinstance(content, dict):  # Если это папка
                lines.extend(
                    write_structure_as_tree_md(content, prefix + "  "))  # Увеличиваем отступ для вложенных папок
        return lines

    md_content = [
        f"# Folder Structure for Project '{zip_name}'\n",
        "```",
        *write_structure_as_tree_md(folder_structure),
        "```"
    ]

    with open(output_path, "w") as md_file:
        md_file.write("\n".join(md_content))
    print(f"Folder structure in Markdown format for '{zip_name}' saved to: {output_path}")


def save_report_to_csv(check_results, output_path):
    with open(output_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Folder", "Status"])
        for folder, status in check_results.items():
            writer.writerow([folder, "Present" if status else "Missing"])
    print(f"Report saved to CSV: {output_path}")


def analyze_zip_from_file(zip_file, extract_folder, output_folder):
    zip_name = "uploaded_archive"
    target_folder = os.path.join(extract_folder, zip_name)

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    found_folders, folder_structure = unzip_and_list_files_from_file(zip_file, extract_folder)
    root_folder_candidates = [folder for folder in found_folders if "/" not in folder and folder]
    filtered_candidates = [f for f in root_folder_candidates if not f.startswith(".")]
    root_folder = filtered_candidates[0] if len(filtered_candidates) == 1 else ""
    found_folders_in_root = {
        f[len(root_folder) + 1:] if root_folder and f.startswith(root_folder + "/") else f
        for f in found_folders
    }

    check_results = check_structure(found_folders_in_root, expected_folders_tree)
    report = generate_report(check_results, zip_name)

    structure_md_path = os.path.join(output_folder, f"{zip_name}_folder_structure.md")
    save_structure_to_md_as_tree(folder_structure, zip_name, structure_md_path)

    csv_output_path = os.path.join(output_folder, f"{zip_name}_structure_check_result.csv")
    save_report_to_csv(check_results, csv_output_path)

    txt_output_path = os.path.join(output_folder, f"{zip_name}_structure_check_result.txt")
    with open(txt_output_path, "w") as txt_file:
        txt_file.write(report)
    print(f"Report saved to TXT: {txt_output_path}")

    return csv_output_path  # Возвращаем путь к CSV


####  Анализ архива   #####

API_URL = "http://84.201.152.196:8020/v1/completions"
API_KEY = "GSeOiIxvB3jpNqZPiedbT7itLerwukZG"
system = "Вы являетесь тимлидом команды и ваша обязанность заключается в проверке иерархии проекта на ее соответствие гексагональной архитектуре python. Проверьте, правильно ли расположены файлы и соответствуют ли они их назвачению. "
knowledge_base = [
    "PEP 8 — это стандарт форматирования кода в Python.",
    "Цикломатическая сложность выше 10 указывает на необходимость рефакторинга.",
    "Bandit проверяет безопасность Python-кода.",
    "Radon оценивает сложность кода и помогает выявить места, требующие рефакторинга.",
    "Autopep8 автоматически форматирует код в соответствии с PEP 8.",
    "Black — это строгий инструмент форматирования Python-кода.",
    "isort упорядочивает импорты для соблюдения стандартов.",
    "yapf форматирует код с учетом стилей PEP 8 и пользовательских конфигураций.",
]

def get_prompt_for_struct(struct):
  first_part=struct[0]
  second_part = struct[1]
  if second_part:
     missing_elements = f"В проекте отсутствуют элементы архитектуры: {', '.join(second_part)}."
  else:
       missing_elements = "Все элементы архитектуры присутствуют."


  prompt = '''### INSTRUCTION:
    # {}
    # База знаний : {}
    # ### СТРУКТУРА ПРОЕКТА:
    # Структура проекта на Python состоит только из данных директорий: {}.
    # {}

    # ### КОММЕНТАРИИ к РЕШЕНИЮ:
    # {}
    # '''


  comments = ""

  formatted_prompt = prompt.format(system,knowledge_base, first_part,missing_elements, comments)

  data = {
      "model": "mistral-nemo-instruct-2407",
      "messages": [
          {"role": "system", "content": formatted_prompt}
      ],
      "max_tokens": 1024,
      "temperature": 0.3
  }
  headers = {
      "Authorization": API_KEY,
      "Content-Type": "application/json"
  }
  response = requests.post(API_URL, headers=headers, data=json.dumps(data))
  if response.status_code == 200:
      result = response.json()
      print(result.get("choices", [{}])[0].get("message", {}).get("content", ""))
      ans = result.get("choices", [{}])[0].get("message", {}).get("content", "")
      return ans
  else:
      print("Ошибка:", response.status_code, response.text)

def get_analize_struct(file):
  test_data = pd.read_csv(file)
  struct_test_present = []
  struct_test_missing=[]
  for i in range(test_data.shape[0]):
      if test_data['Status'][i]=='Present':
        struct_test_present.append(test_data['Folder'][i])
      else:
        struct_test_missing.append(test_data['Folder'][i])
  struct = (struct_test_present, struct_test_missing)
  r = get_prompt_for_struct(struct)
  return r

def run(file):
  ans = get_analize_struct(file)
  return ans


#### выходная функция проверки #####

def archive_analysis(input):
    extract_folder = 'extracted_folder/'
    output_folder = '.'
    f = open(zip_file_path, "wb")
    f.write(input)
    f.close()

    check_results = analyze_zip(input, extract_folder, output_folder)
    os.remove(zip_file_path)
    os.remove(extract_folder)

    output = run(check_results)
    print(output)
    f = open("output.md", "wb")
    f.write(output)
    f.close()
    os.remove("output.md")

    return f
