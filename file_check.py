import requests
import json
import pandas as pd
import subprocess
import faiss
from sentence_transformers import SentenceTransformer

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