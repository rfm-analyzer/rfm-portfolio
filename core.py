# 1. core.py (только чистая логика)

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns


# Переводим RFM в маркетинговый сегмент
def rfm_segment(row):

    if row['Recency'] >= 4 and row['Frequency'] >= 4:
        return 'VIP (Лучшие)'
    
    elif row['Recency'] >= 4 and row['Frequency'] <= 2:
        return 'New Customers (Новички)' 
    
    elif row['Recency'] <= 2 and row['Frequency'] >= 4:
        return 'At Risk (Под угрозой оттока)' 
    
    elif row['Recency'] <= 2 and row['Frequency'] <= 2:
        return 'Lost (Уснувшие)' 
    
    elif row['Frequency'] >= 4:
        return 'Loyal (Лояльные)' 
    
    else:
        return 'Average (Середнячки)'


# Это ядро приложения:
def calculate_rfm(df):
    df['order_date'] = pd.to_datetime(df['order_date'])

    snapshot_date = df['order_date'].max() + pd.Timedelta(days=1)

    rfm = df.groupby('customer_id').agg({
        'order_date': lambda x: (snapshot_date - x.max()).days,
        'customer_id': 'count',
        'revenue': 'sum'
    })

    rfm.columns = ['recency', 'frequency', 'monetary']

    # RFM scoring
    rfm['Recency'] = pd.qcut(rfm['recency'], q=5, labels=[5,4,3,2,1], duplicates="drop")
    rfm['Frequency'] = pd.qcut(rfm['frequency'], q=5, labels=[1,2,3,4,5], duplicates='drop')
    rfm['Monetary'] = pd.qcut(rfm['monetary'], q=5, labels=[1,2,3,4,5])

    rfm['RFM_Score'] = (
        rfm['Recency'].astype(str) +
        rfm['Frequency'].astype(str) +
        rfm['Monetary'].astype(str)
    )

    # 👇 вот здесь применяем сегментацию
    rfm['Segment'] = rfm.apply(rfm_segment, axis=1)
    
    return rfm.reset_index()
    




