Forecast GGW
Интеллектуальная система прогнозирования продаж и сценарного анализа в ресторанном бизнесе

Описание проекта
Forecast GGW — web‑приложение (Streamlit) для автоматизации управленческих решений в HoReCa.
Система:

загружает данные о продажах (Excel / SQLite),

строит недельные прогнозы спроса (Facebook Prophet),

рассчитывает порционность и рекомендованные закупки,

моделирует «what‑if»‑сценарии (цены, акции, новые рестораны),

формирует управленческие отчёты (Excel, интерактивные графики),

позволяет задавать вопросы к данным на естественном языке (OpenAI API).

Архитектура модульная: все вычислительные блоки отделены от интерфейса и могут использоваться как SDK.

Ключевые возможности
Модуль	Назначение	Основные технологии
data_loader.py	Импорт Excel, CRUD в SQLite	pandas, sqlite3
forecasting.py	Прогноз по (ресторан × продукт) и запись в БД	prophet, streamlit.cache_data
portion_calc.py	Перевод прогноза в кол‑во порций	pandas, plotly
scenario_planning.py	«Что если»‑анализ (цены, порции, новые точки)	numpy, plotly
analysis_restaurants.py & behavior_analysis.py	Дашборды по сезонности, локациям, продуктам	plotly.express
reports.py	Экспорт топов и сводок в Excel	xlsxwriter
openai_integration.py	Чат‑бот для аналитики	openai, langchain

Структура репозитория
├── main.py                 # точка входа Streamlit
├── data_loader.py          # загрузка/БД
├── forecasting.py          # прогноз спроса
├── portion_calc.py         # порционность
├── scenario_planning.py    # сценарное моделирование
├── analysis_restaurants.py # дашборды
├── behavior_analysis.py    # сезонный анализ
├── reports.py              # отчёты
├── data_preprocessing.py   # базовая очистка
├── requirements.txt        # зависимости
├── .env                    # переменные окружения (ключ OpenAI)
└── README.md               # текущий файл
Требования к окружению
Компонент	Версия
Python	≥ 3.10
Streamlit	1.41.1
Prophet	1.1.6
Система	Windows / macOS / Linux

Полный список — в requirements.txt.

Установка
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env .env.local
Укажите переменную OPENAI_API_KEY в .env.local.

SQLite‑файл database.db создаётся автоматически в корне проекта.

Быстрый старт

streamlit run main.py
Загрузка данных → выберите Excel или «Загрузить из БД».

Прогнозирование спроса → укажите продукт, ресторан, горизонт (1‑4 недели).

Расчёт порционности → получите объём закупок в килограммах и порциях.

Что если? → смоделируйте изменение цен, порций, открытие точек.

Генерация отчётов → сформируйте Excel одним кликом.

Спросите ИИ → задайте вопрос на естественном языке (например, «Продажи П/Ф Чили в Казань Mega за 2024») и получите ответ с объяснениями модели.
