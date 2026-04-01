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
    return fig



# Heanmap (Где лежат деньги?)
def plot_heatmap(pivot):
    fig, ax = plt.subplots(figsize=(5, 3))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
    ax.set_title("RFM Heatmap — Revenue")
    return fig 
    
    #Это старый рабочий код
    #plt.figure(figsize=(8, 5))
    #sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues")
    #plt.title("RFM Heatmap — Revenue")
    #plt.show() 

    
    # В ноутбуке return рисует две тепловые катры при вызове plot_heatmap(pivot)
    # Без return рисует одну катру при вызове plot_heatmap(pivot)
    
#def plot_heatmap(pivot):
#    fig = plt.figure(figsize=(8, 5))
#    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues")
#    plt.title("RFM Heatmap — Revenue")
#    #return fig