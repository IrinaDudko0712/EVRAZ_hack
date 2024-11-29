import subprocess
import faiss
from sentence_transformers import SentenceTransformer

# Инициализация базы знаний для RAG
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

# Инициализация модели и базы знаний
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(knowledge_base)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)


def search_knowledge_base(query):
    """Поиск по базе знаний."""
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k=1)
    return knowledge_base[indices[0][0]]


# Функции анализа кода
def run_isort(file_path):
    """Запуск isort для упорядочивания импортов."""
    subprocess.run(["isort", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_yapf(file_path):
    """Запуск yapf для форматирования кода."""
    subprocess.run(["yapf", "--in-place", "--style", ".style.yapf", file_path])


def run_flake8(file_path):
    """Запуск flake8 для анализа PEP 8."""
    result = subprocess.run(["flake8", file_path], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def run_pylint(file_path):
    """Запуск pylint для анализа качества кода."""
    result = subprocess.run(["pylint", file_path], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def run_radon(file_path):
    """Запуск radon для оценки сложности кода."""
    result = subprocess.run(["radon", "cc", file_path, "-a"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def autopep8_format(file_path):
    """Форматирование кода для исправления пробелов с помощью autopep8."""
    subprocess.run(["autopep8", "--in-place", "--aggressive", file_path])
    with open(file_path, "r") as f:
        return f.read()


def format_with_black(file_path):
    """Форматирование кода для исправления пробелов с помощью black."""
    subprocess.run(["black", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with open(file_path, "r") as f:
        return f.read()


def analyze_code_with_context(file_path):
    """Анализ кода с использованием инструментов и базы знаний."""
    reports = {
        "flake8": run_flake8(file_path),
        "pylint": run_pylint(file_path),
        "radon": run_radon(file_path),
    }

    context = {
        tool: search_knowledge_base(report) for tool, report in reports.items() if report
    }

    return {"reports": reports, "context": context}


def run_vulture(file_path):
    """Запуск vulture для поиска неиспользуемого кода."""
    result = subprocess.run(["vulture", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()




def check_file(test_code):
    with open("test_code.py", "w") as f:
        f.write(test_code)

    # Упорядочивание импортов с помощью isort
    print("Форматирование импортов с помощью isort:")
    run_isort("test_code.py")
    with open("test_code.py", "r") as f:
        print(f.read())
    print()

    # Форматирование кода с помощью yapf
    print("Форматирование кода с помощью yapf:")
    run_yapf("test_code.py")
    with open("test_code.py", "r") as f:
        print(f.read())
    print()

    # Тестирование поиска в базе знаний
    print("Тестирование поиска в базе знаний:")
    query = "Что такое PEP 8?"
    result = search_knowledge_base(query)
    print(f"Запрос: {query}")
    print(f"Результат: {result}")
    print()

    # Тестирование flake8
    print("Тестирование flake8:")
    print(run_flake8("test_code.py"))
    print()

    # Тестирование pylint
    print("Тестирование pylint:")
    print(run_pylint("test_code.py"))
    print()

    # Тестирование radon
    print("Тестирование radon:")
    print(run_radon("test_code.py"))
    print()

    # Тестирование autopep8
    print("Форматирование кода с помощью autopep8:")
    formatted_code = autopep8_format("test_code.py")
    print(formatted_code)
    print()

    print("Форматирование кода с помощью black:")
    formatted_code_black = format_with_black("test_code.py")
    print(formatted_code_black)

    vulture_report = run_vulture("test_code.py")
    print("Результаты анализа с помощью vulture:")
    print(vulture_report)