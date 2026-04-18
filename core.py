# core.py (pure logic)
# =======================NEW CODE=============================
import pandas as pd
import numpy as np
import pandas as pd
from datetime import datetime


def calculate_rfm(df):
    """
    Core application: data aggregation and RFM metrics calculation.
    Optimized for large data volumes.
    """
    df['order_date'] = pd.to_datetime(df['order_date'])

    # Snapshot date (max date in logs + 1 day)
    snapshot_date = df['order_date'].max() + pd.Timedelta(days=1)

    # Fast aggregation via groupby
    rfm = df.groupby('customer_id').agg({
        'order_date': lambda x: (snapshot_date - x.max()).days,
        'customer_id': 'count',
        'revenue': 'sum'
    })

    rfm.columns = ['recency', 'frequency', 'monetary']

    # RFM scoring using quantiles
    # duplicates="drop" prevents errors when many customers have the same frequency
    rfm['Recency'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop")
    rfm['Frequency'] = pd.qcut(rfm['frequency'], q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    rfm['Monetary'] = pd.qcut(rfm['monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")


    # Convert to numeric type for fast vectorized segmentation
    R = rfm['Recency'].astype(int)
    F = rfm['Frequency'].astype(int)

    # VECTORIZED SEGMENTATION (Instead of slow apply)
    conditions = [
        (R >= 4) & (F >= 4), # VIP
        (R >= 4) & (F <= 2), # New Customers
        (R <= 2) & (F >= 4), # At Risk
        (R <= 2) & (F <= 2), # Lost
        (F >= 4)             # Loyal
    ]

    choices = [
        'VIP (Best)', 
        'New Customers', 
        'At Risk (Churn Risk)', 
        'Lost (Dormant)', 
        'Loyal'
    ]

    # Everything not matched becomes 'Average'
    rfm['Segment'] = np.select(conditions, choices, default='Average')

    # Keep string score for display
    rfm['RFM_Score'] = (
        rfm['Recency'].astype(str) +
        rfm['Frequency'].astype(str) +
        rfm['Monetary'].astype(str)
    )

    return rfm.reset_index()

#========================OLD CODE==============================
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# import numpy as np 

# # Convert RFM to marketing segment
# def rfm_segment(row):

#     if row['Recency'] >= 4 and row['Frequency'] >= 4:
#         return 'VIP (Best)'

#     elif row['Recency'] >= 4 and row['Frequency'] <= 2:
#         return 'New Customers' 

#     elif row['Recency'] <= 2 and row['Frequency'] >= 4:
#         return 'At Risk (Churn Risk)' 

#     elif row['Recency'] <= 2 and row['Frequency'] <= 2:
#         return 'Lost (Dormant)' 

#     elif row['Frequency'] >= 4:
#         return 'Loyal' 

#     else:
#         return 'Average'


# # This is the core of the application:
# def calculate_rfm(df):
#     df['order_date'] = pd.to_datetime(df['order_date'])

#     snapshot_date = df['order_date'].max() + pd.Timedelta(days=1)

#     rfm = df.groupby('customer_id').agg({
#         'order_date': lambda x: (snapshot_date - x.max()).days,
#         'customer_id': 'count',
#         'revenue': 'sum'
#     })

#     rfm.columns = ['recency', 'frequency', 'monetary']

#     # RFM scoring
#     rfm['Recency'] = pd.qcut(rfm['recency'], q=5, labels=[5,4,3,2,1], duplicates="drop")
#     rfm['Frequency'] = pd.qcut(rfm['frequency'], q=5, labels=[1,2,3,4,5], duplicates='drop')
#     rfm['Monetary'] = pd.qcut(rfm['monetary'], q=5, labels=[1,2,3,4,5])

#     rfm['RFM_Score'] = (
#         rfm['Recency'].astype(str) +
#         rfm['Frequency'].astype(str) +
#         rfm['Monetary'].astype(str)
#     )

#     # Apply segmentation here
#     rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

#     return rfm.reset_index()