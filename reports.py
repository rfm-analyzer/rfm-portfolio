# 2. reports.py (только таблицы)

# Финальный отчет для рассылки по email с указанием ID клиента
def final_report_to_email(rfm):
    return  rfm[['customer_id', 'Segment', 'monetary', 'frequency']]
    
    
    


#  Финальный отчет для отдела маркетинга 
def final_report_to_marketing(rfm):
     return (
         rfm.groupby('Segment')
            .agg(
                customers=('Segment', 'count'),
                revenue=('monetary', 'sum'),
                avg_check=('monetary', 'mean'),
                avg_freq=('frequency', 'mean')
        )
        .sort_values('revenue', ascending=False)
    )
   
    

# Сводная таблица для Тепловой катры
def build_rfm_pivot(rfm):
    return rfm.pivot_table(
        index='Recency',
        columns='Frequency',
        values='monetary',
        aggfunc='sum',
        observed=False
    )
    
