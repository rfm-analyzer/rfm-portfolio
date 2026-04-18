## 3. reports.py (tables only)

# Final report for email distribution with customer ID
def final_report_to_email(rfm):
    return rfm[['customer_id', 'Segment', 'monetary', 'frequency']]


# Final report for marketing department
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


# Pivot table for Heatmap
def build_rfm_pivot(rfm):
    return rfm.pivot_table(
        index='Recency',
        columns='Frequency',
        values='monetary',
        aggfunc='sum',
        observed=False
    )