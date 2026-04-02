# 4. app.py (только Streamlit)

import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials
#from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import uuid
from core import calculate_rfm
from reports import (
    final_report_to_email,
    final_report_to_marketing,
    build_rfm_pivot
)
from plots import plot_segment_donut, plot_heatmap


#-------------------название вкладки в браузере-------------------------
st.set_page_config(page_title="rfmanalyser",  layout="wide")#layout="centered" 

#-------------------функция загрузки-------------------------
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# ------------- создаем функцию автоматического определения столбцов-------------------
def find_columns(df):
    """Автоматический поиск индексов столбцов по ключевым словам"""
    cols = [c.lower() for c in df.columns]

    # Словари ключевых слов для поиска
    keywords = {
        'id': ['id', 'client', 'customer', 'клиент', 'покупатель', 'номер'],
        'date': ['date', 'time', 'дата', 'день', 'заказ'],
        'revenue': ['revenue', 'amount', 'sales', 'цена', 'сумма', 'выручка', 'total']
    }

    def get_index(keys):
        for i, col in enumerate(cols):
            if any(k in col for k in keys):
                return i
        return None
    
    return {
        'id': get_index(keywords['id']),
        'date': get_index(keywords['date']),
        'revenue': get_index(keywords['revenue'])
    }
# ------------- КОНЕЦ функции автоматического определения столбцов-------------------



if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# --------------ЦЕНТРУЕМ ЗАГОЛОВОК Col ИЛИ HTML:-------------------------
st.markdown("<h2 style='text-align: center; color: white;'>RFM-анализ клиентской базы</h2>", unsafe_allow_html=True)

#---------------------DEMO-------------------
demo_button = st.button("Попробовать DEMO")

if demo_button:
    st.session_state.demo_mode = True
else:
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False
# --------------КОНЕЦ ДЕМОНСТРАЦИИ ДЕМО:-------------------------

st.info(
"Загрузите Excel файл с транзакциями клиентов.\n"
"Файл должен содержать:\n"
"- ID клиента\n"
"- дату покупки\n"
"- сумму покупки"
)

#------------------Загрузка файла--------------------
uploaded_file = st.file_uploader("Загрузите ваши данные", type=[ 'xlsx'], key="file_uploader_key")# ,'csv'

#------------------Логика выбора--------------------
if st.session_state.demo_mode:
    df = pd.read_excel("/home/dmitrii/Jupyter_Python_SQL/rfm_project/data/abc_xyz_analisis_table.xlsx")
    st.success("Загружен демонстрационный датасет")  
    
elif uploaded_file is not None:
    df = load_data(uploaded_file)
    
else:
    st.info("Загрузите ваши данные или нажмите DEMO")
    st.stop()

# ============== КНОПКА ОЧИСТКИ ==============
if st.button("Очистить данные", type="secondary"): # 🗑️
    keys_to_clear = [
        "demo_mode",
        "analysis_done",
        "col_id_manual",
        "col_date_manual", 
        "col_amount_manual",
        "col_id",
        "col_date",
        "col_amount",
        "file_uploader_key"  # Сбрасываем загрузчик
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

                # Автоматический запуск анализа при правильных данных
    
st.write("Ваши исходные данные (первые три строки):")
st.dataframe(df.head(3))

found_indices = find_columns(df) #  Достаём все индексы колонок(без названий колонок просто индекс колонки  0,1,2... или None)
    
                # Проверяем, все ли столбцы найдены (не None)
#auto_success = all(v is not None for v in found_indices.values())

values = found_indices.values()

checks = []
for v in values:
    #v is not None  →  "v это не пустота?"
    check = (v is not None)
    checks.append(check)
    
auto_success = all(checks) # Функция all() проверяет, все ли True
# на этом этапе auto_success = True
#-------------------------СТАРЫЙ КОД---------------------------------------
                # Находим индексы столбцов содержащих нужные данные
if auto_success:
    idx_id = found_indices['id'] # индекс колонки содержащей подстроку "id"
    idx_date = found_indices['date'] # индекс колонки содержащей подстроку "date"
    idx_rev = found_indices['revenue'] # индекс колки содержащей подстроку "revenue"
    
    
                # Готовим датафрейм - матрицу для ручного сопоставления названий столбцов
    col_id = df.columns[idx_id]
    col_date = df.columns[idx_date]
    col_amount = df.columns[idx_rev]

    auto_run = True
else:
    st.warning("Не удалось автоматически определить столбцы. Выберите их вручную в выпадающих списках ниже.")


                # В выпадающем меню сопоставляем столбцы
    with st.expander("Настройка сопоставления столбцов", expanded=True):
        col_id = st.selectbox("ID Клиента", df.columns)
        col_date = st.selectbox("Дата заказа", df.columns)
        col_amount = st.selectbox("Выручка", df.columns)
        
        auto_run = False
        
#-----------------------Создаем кнопку и задаем условия----------------
rfm_button = st.button("Запустить RFM")

if rfm_button:
    #st.session_state.demo_mode = True
    if col_id is None or col_date is None or col_amount is None:
        st.warning("Выберите все столбцы")
        st.stop()

            # Дополнительная защита если один столбец выбран несколько раз
    if len({col_id, col_date, col_amount}) < 3:
        st.warning("Нельзя выбирать один и тот же столбец несколько раз")
        st.stop()
        
#------------------Валидация----------------------------------       
if uploaded_file and auto_run:      # файл загружен и автопоиск сработал        
    st.session_state.analysis_done = True
        
elif uploaded_file and rfm_button:  # файл загружен и ручной ввод сработал
    st.session_state.analysis_done = True
    
elif st.session_state.demo_mode:    # кнопка DEMO нажата
    st.session_state.analysis_done = True # переключатель в положение True


#------------------Запуск rfm-анализа---------------------------------- 
if st.session_state.analysis_done:  # если переключатель в положение True то запускаем rfm-анализ:

    
                # Формируем датафрейм 
    rfm_df = df[[col_id, col_date, col_amount]].copy()
    
                # Присваиваем технические названия столбцам
    rfm_df.columns = ['customer_id', 'order_date', 'revenue']
    
# БЫЛО: if st.session_state.analysis_done and rfm_df is not None:
#СТАЛО:
    st.session_state.analysis_done = True
    
                # Проверка объема необходимых данных для анализа
    if len(rfm_df) < 5:
        st.warning("Недостаточно данных для анализа") 
        st.stop()

                # Проверка количества уникальных клиентов для анализа
    if rfm_df['customer_id'].nunique() < 3:
        st.warning("Слишком мало уникальных клиентов для анализа")
        st.stop()

    
                # Валидация типов
    rfm_df['order_date'] = pd.to_datetime(rfm_df['order_date'], errors='coerce')
    rfm_df['revenue'] = pd.to_numeric(rfm_df['revenue'], errors='coerce')

                #  Проверяем, нет ли пустых значений после приведения типов
    if rfm_df.isnull().any().any():
        st.error("Ошибка в данных: некоторые значения не удалось преобразовать в дату или число.")
        st.write("Проблемные строки:")
        
                # Показываем строки с ошибками для отладки
        st.dataframe(
            rfm_df[rfm_df.isnull().any(axis=1)].head()
        )       
        st.stop()


                # Вызываем функции rfm-анализа
    

    rfm = calculate_rfm(rfm_df)
    
    email_report = final_report_to_email(rfm)
    
    marketing_report = final_report_to_marketing(rfm)
    
    pivot = build_rfm_pivot(rfm)

    
                # KPI metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Всего клиентов",
        rfm['customer_id'].nunique()
    )

    col2.metric(
        "Общая выручка",
        int(rfm['monetary'].sum())
    )

    col3.metric(
        "Средний чек",
        int(rfm['monetary'].mean())
    )

                # ФИЛЬТР СЕГМЕНТА  
    st.subheader("RFM таблица")


#-------------------------Выбор сегмента ----------------------    
    segment = st.selectbox("Нажмите плашку < Все >, чтобы выбрать сегмент клиентов (этот фильтр применим только к RFM-таблице)",
        ["Все"] + list(rfm['Segment'].unique())
        ) 
    
    rfm_filtered = rfm.copy()
    if segment != "Все":
        rfm_filtered = rfm_filtered[rfm_filtered['Segment'] == segment]
    st.dataframe(rfm_filtered)


                # Отчёт для Email
    st.subheader("Отчёт для Email")
    st.dataframe(email_report)   
        
                 # 1. Подготовка Excel файла в памяти
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        email_report.to_excel(writer, sheet_name='Отчёт для Email', index=False) 
            
                # 2. Кнопка скачивания для Excel
        st.download_button(
            label="Скачать 'Отчет для Email' в Excel файл",
            data=buffer.getvalue(),
            file_name="rfm_email_report.xlsx",
            mime="application/vnd.ms-excel"
        )
        
                # 3. Кнопка скачивания для csv
        st.download_button(
           "Скачать 'Oтчет для Email' в csv-файл",
           email_report.to_csv(index=False),
           file_name="rfm_email_report.csv"
        )

                # Отчёт для маркетинга
    st.subheader("Отчёт для маркетинга")
    st.dataframe(marketing_report)
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        marketing_report.to_excel(writer, sheet_name='Отчёт для маркетинга', index=False) 
            
                 # 2. Кнопка скачивания для Excel
        st.download_button(
            label="Скачать 'Отчёт для маркетинга' в Excel файл",
            data=buffer.getvalue(),
            file_name="rfm_marketing_report.xlsx",
            mime="application/vnd.ms-excel"
        )   
                # 1. Кнопка скачивания для csv
        st.download_button(
            "Скачать 'Отчет для маркетинга' в csv-файл",
            marketing_report.to_csv(),
            file_name="rfm_marketing_report.csv"
        )

 
                # Круговая диаграмма
  
    st.subheader("Распределение сегментов")

    donut = plot_segment_donut(rfm)

    st.plotly_chart(donut, use_container_width=True)
    
    

                # Тепловая карта
    
    st.subheader("RFM Тепловая карта")

    heatmap = plot_heatmap(pivot)

    st.pyplot(heatmap)

    
#----------------ФОРМА ЗАКАЗА ПРОФЕССИАНАЛЬНЫЙ АУДИТ ВЕРСИЯ ChatGPT------------------
    if not st.session_state.get("demo_mode", False) and st.session_state.analysis_done: 
        st.divider()
            
            #st.subheader("Хотите более точную сегментацию?")#📊
            
        st.warning("""
            Если в ваших днных есть заказы превышающие средний чек на несколько порядков, 
            то предлагаем вам заказать услугу **Профессиональный аудит**.
            """)
            #Крупные заказы (выбросы) могут искажать границы сегментов.
            #Мы можем провести более **глубокий аудит** ваших данных:
        st.markdown("""
             **Профессиональный аудит включает:**
            - обработку выбросов
            - более точную сегментацию
            - рекомендации по маркетингу
            """)# 💼
        with st.form("pro_analysis_form"):
            st.write("**Заказать профессиональный аудит**")          
            email = st.text_input("Введите ваш email для связи:",
            placeholder="example@mail.com") 
            comment = st.text_area("Кратко о задаче:", height=100)
            submitted = st.form_submit_button("Заказать услугу")#🚀
    


@st.cache_resource
def get_gspread_client():
    # Путь к JSON
    SERVICE_ACCOUNT_FILE = "/home/dmitrii/Jupyter_Python_SQL/rfm_project/credentials.json"

# Области доступа
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
]

# Авторизация
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
)
    return gspread.authorize(creds)

    #@st.cache_resource
    client = get_gspread_client()
    
    if submitted:
        if email:
            st.success("email корректный.")
        else:
            st.error("Введите корректный email")
        try:   
                      # Открываем таблицу по имени
            spreadsheet = client.open("streamlit_order_form")   
                
                      # Берём второй лист
            worksheet = spreadsheet.sheet1        
        
                 # Необходимо упростить - вместо df сделать список
            new_row = pd.DataFrame([{
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "email": email,
                    "comment": comment,
                    "app_version": "1.0"
                }])
            
            new_row_append = new_row.values[0].tolist()
            
                        # Записываем данные
            worksheet.append_row(new_row_append)
                                    
                        # Выводим на экран
            st.success("Заявка отправлена! Мы свяжемся с вами.")
    
        except:
            st.error("Не удалось установить соединение. Подождите 5 секунд и нажмите кнопку 'Заказать услугу' еще раз.")
    


#-------------------ФОРМА ОПРОСА О РАБОТЕ ПРИЛОЖЕНИЯ-----------------------------

        # Создаем форму опроса
if st.session_state.analysis_done: 
    st.divider()
    with st.form("feedback_form", clear_on_submit=True): # clear_on_submit - «очищать после отправки»
        st.write("**Помогите нам нам стать лучше!**")
        #st.write ("Ваше мнение:")
        
                    # Оценка (новое в Streamlit 1.30+)
        score = st.feedback("stars") # score - счет, оценка
    
                    # Что улучшить - features (фича) - функции
        features = st.multiselect(
            "Что стоит добавить?",
            ["Светлая тема", "Экспорт в PDF", "Скорость работы", "Больше графиков", "Улучшить дизайн"]
        )
        
                    # Текстовый отзыв
        comment = st.text_area("Ваши пожелания:")
    
                    # Создаем кнопку отправки отзыва
        submitted = st.form_submit_button("Отправить отзыв") #  submitted - представленный, поданный (отзыв), пожелание
    
    #@st.cache_resource
    client = get_gspread_client()
    
    if submitted:
        try:
                        # Открываем таблицу по имени
            spreadsheet = client.open("streamlit_feedback_form")
        
                        # Берём первый лист
            worksheet = spreadsheet.sheet1
            
                        # Необходимо упростить - вместо df сделать список
            new_row = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "score": score,
                "features": ", ".join(features),
                "comment": comment,
                "app_version": "1.0"
            }])
        
            new_row_append = new_row.values[0].tolist()
        
                        # Записываем данные
            worksheet.append_row(new_row_append)
                        
                        # Выводим на экран
            st.success("Спасибо! Ваш отзыв сохранён.")
    
        except:
            st.error("Не удалось установитьсоединение. Подождите 5 секунд и нажмите кнопку 'Отправить отзыв' еще раз.")
