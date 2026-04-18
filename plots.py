# plots.py (charts only)
#============================NEW CODE=====================
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

def plot_segment_donut(rfm):
    """
    Builds a donut chart of customer distribution.
    Optimized: data aggregation happens BEFORE passing to Plotly.
    """
    # Compress dataset to 6 rows for instant rendering
    segment_counts = rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['segment', 'count']

    fig = px.pie(
        segment_counts, 
        values='count', 
        names='segment',
        hole=0.4, # Donut shape
        height=550 
    )

    # Fine-tuning margins and legend
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h", # Horizontal layout below chart
            yanchor="bottom",
            y=-0.1, 
            xanchor="center",
            x=0.5
        )
    )    
    return fig

def plot_heatmap(pivot):
    """
    Builds a static heatmap of revenue distribution by RFM.
    """
    # Compact size for nice display in right column
    fig, ax = plt.subplots(figsize=(5, 3.5)) 

    sns.heatmap(
        pivot, 
        annot=True, 
        fmt=".0f", 
        cmap="Blues", 
        ax=ax,
        cbar=False # Disable colorbar to save space
    )

    # Labels tuning for narrow column
    ax.set_title("RFM Heatmap — Revenue", fontsize=10, pad=15)
    ax.set_xlabel("Recency", fontsize=8)
    ax.set_ylabel("Frequency", fontsize=8)

    # Reduce axis tick font size
    ax.tick_params(axis='both', which='major', labelsize=8)

    # Auto-adjust elements to avoid overlapping
    fig.tight_layout()

    return fig

# #=======================OLD CODE==========================

# # Donut chart (Segment share)        
# import plotly.express as px
# import seaborn as sns
# import matplotlib.pyplot as plt


# def plot_segment_donut(rfm):
#     segment_counts = rfm['Segment'].value_counts().reset_index()
#     segment_counts.columns = ['segment', 'count']

#     # Draw pie chart
#     fig = px.pie(
#         segment_counts, 
#         values='count', 
#         names='segment',
#         #title='Customer base distribution by segments',
#         hole=0.4, # Make donut shape                 
#         #template="plotly",
#         #color_discrete_sequence=px.colors.qualitative.Plotly
#         height=550 # Increase chart height for desktop
#     )

#         # Remove extra margins around circle to make it larger
#     fig.update_layout(
#         margin=dict(l=20, r=20, t=30, b=20),
#         legend=dict(
#             orientation="h", # Horizontal legend
#             yanchor="bottom",
#             y=-0.1, # Move legend below chart
#             xanchor="center",
#             x=0.5
#         )
#     )    
#     return fig



# #=========================================================    


# def plot_heatmap(pivot):
#     # figsize=(5, 3.5) sets ideal aspect ratio for half screen
#     fig, ax = plt.subplots(figsize=(5, 3.5)) 

#     sns.heatmap(
#         pivot, 
#         annot=True, 
#         fmt=".0f", 
#         cmap="Blues", 
#         ax=ax,
#         cbar=False # Disable sidebar scale (Colorbar) to save space in column
#     )

#     # Labels tuning (reduced font size for narrow column)
#     ax.set_title("RFM Heatmap — Revenue", fontsize=10, pad=15)
#     ax.set_xlabel("Recency", fontsize=8)
#     ax.set_ylabel("Frequency", fontsize=8)

#     # Make tick labels slightly smaller
#     ax.tick_params(axis='both', which='major', labelsize=8)

#     # Auto-adjust elements to avoid cropping
#     fig.tight_layout()

#     return fig