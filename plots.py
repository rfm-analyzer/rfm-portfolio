# 3. app.py (только графики)


# Donut chart (Доля каждого сегмента )        
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt


def plot_segment_donut(rfm):
    segment_counts = rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['segment', 'count']
    
    # Рисуем круговую диаграмму
    fig = px.pie(
        segment_counts, 
        values='count', 
        names='segment',
        #title='Распределение клиентской базы по сегментам',
        hole=0.4#, # Делаем форму пончика (donut chart)                 
        #template="plotly",
        #color_discrete_sequence=px.colors.qualitative.Plotly
    )
        # Увеличиваем размер диаграммы
    # fig.update_layout(
    #     width=800,           # Ширина в пикселях
    #     height=600,          # Высота в пикселях
    #     autosize=False,      # Отключаем авторазмер
    #     margin=dict(l=50, r=50, t=50, b=50),  # Отступы
    #     #margin=dict(l=30, r=30, t=30, b=30),
    #     font=dict(size=24)  # Увеличиваем шрифт подписей
    # )
        # Увеличиваем размер текста внутри диаграммы
    #fig.update_traces(
        #textposition='inside',
        #textinfo='percent+label',
        #textfont_size=14,
        #insidetextfont_size=24
    #)
    
    return fig

#========================СТАЛО=================================    
# def plot_heatmap(pivot):
#     # Уменьшаем размер фигуры
#     fig, ax = plt.subplots(figsize=(8, 6))  # Было (5,3) - слишком узко
    
#     # Настраиваем тепловую карту
#     sns.heatmap(
#         pivot, 
#         annot=True, 
#         fmt=".0f", 
#         cmap="Blues", 
#         ax=ax,
#         annot_kws={'size': 10},  # Размер текста внутри ячеек
#         cbar_kws={'shrink': 0.8},  # Уменьшаем цветовую шкалу
#         square=True  # Делаем ячейки квадратными
#     )
    
#     # Настройка подписей
#     ax.set_title("RFM Heatmap — Revenue", fontsize=12, pad=20)
#     ax.set_xlabel("Recency (давность покупок)", fontsize=10)
#     ax.set_ylabel("Frequency (частота покупок)", fontsize=10)
    
#     # Поворачиваем подписи для лучшей читаемости
#     #plt.xticks(rotation=45, ha='right', fontsize=9)
#     plt.xticks(rotation=0, ha='right', fontsize=9)
#     plt.yticks(rotation=0, fontsize=9)
    
#     plt.tight_layout()  # Автоматически подгоняет отступы
    
#     return fig
#===================БЫЛО======================================    
# Heanmap (Где лежат деньги?)
def plot_heatmap(pivot):
    fig, ax = plt.subplots(figsize=(5, 3))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
    ax.set_title("RFM Heatmap — Revenue")
        # Настройка подписей
    ax.set_title("RFM Heatmap — Revenue", fontsize=12, pad=20)
    ax.set_xlabel("Recency (давность покупок)", fontsize=10)
    ax.set_ylabel("Frequency (частота покупок)", fontsize=10)

  

    return fig 
#=========================================================    
 