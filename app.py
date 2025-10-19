import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def read_data(fname):
    return pd.read_parquet(fname)

def add_moving_averages(df):
    df = df.set_index("date")
    df = pd.DataFrame(df["close"].resample("1h").mean().dropna().astype("float32"))
    if df["close"].iloc[0] > 1000:
        df["ma5"] = df["close"].rolling(5).mean().round(2)
        df["ma20"] = df["close"].rolling(20).mean().round(2)
    return df

def combine_dfs(spx, vix):
    return spx.join(vix, how="left", rsuffix="_vix").dropna()

def create_plot(df):
    st.set_page_config(layout="wide", page_title="SPX - VIX Analysis")
    st.title("📈 SPX & VIX Chart")
    
    # Sidebar controls
    st.sidebar.header("Controls")
    show_5h = st.sidebar.checkbox("Show 5H Average", value=True)
    show_20h = st.sidebar.checkbox("Show 20H Average", value=True)
    show_vix = st.sidebar.checkbox("Show VIX", value=True)
    
    # Date range selector
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(df.index.min().date(), df.index.max().date()),
        min_value=df.index.min().date(),
        max_value=df.index.max().date()
    )
    
    # Filter dataframe by date range
    if len(date_range) == 2:
        mask = (df.index.date >= date_range[0]) & (df.index.date <= date_range[1])
        df_filtered = df[mask]
    else:
        df_filtered = df
    
    # Create numeric index for plotting (avoids gaps in non-trading hours)
    df_filtered = df_filtered.copy()
    df_filtered['numeric_index'] = range(len(df_filtered))
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('SPX Price with Moving Averages', 'VIX'),
        row_heights=[0.7, 0.3] if show_vix else [1.0, 0.0]
    )
    
    # SPX Price
    fig.add_trace(
        go.Scatter(
            x=df_filtered['numeric_index'],
            y=df_filtered['close'],
            name='SPX',
            line=dict(color='#2E86AB', width=2),
            hovertemplate='<b>%{text}</b><br>Price: $%{y:.2f}<extra></extra>',
            text=df_filtered.index.strftime('%Y-%m-%d %H:%M')
        ),
        row=1, col=1
    )
    
    # 5H Average
    if show_5h and 'ma5' in df_filtered.columns:
        fig.add_trace(
            go.Scatter(
                x=df_filtered['numeric_index'],
                y=df_filtered['ma5'],
                name='5H Avg',
                line=dict(color='#F77F00', width=1.5, dash='dash'),
                hovertemplate='<b>%{text}</b><br>5H Avg: $%{y:.2f}<extra></extra>',
                text=df_filtered.index.strftime('%Y-%m-%d %H:%M')
            ),
            row=1, col=1
        )
    
    # 20H Average
    if show_20h and 'ma20' in df_filtered.columns:
        fig.add_trace(
            go.Scatter(
                x=df_filtered['numeric_index'],
                y=df_filtered['ma20'],
                name='20H Avg',
                line=dict(color='#06A77D', width=1.5, dash='dot'),
                hovertemplate='<b>%{text}</b><br>20H Avg: $%{y:.2f}<extra></extra>',
                text=df_filtered.index.strftime('%Y-%m-%d %H:%M')
            ),
            row=1, col=1
        )
    
    # VIX
    if show_vix and 'close_vix' in df_filtered.columns:
        fig.add_trace(
            go.Scatter(
                x=df_filtered['numeric_index'],
                y=df_filtered['close_vix'],
                name='VIX',
                line=dict(color='#D62828', width=2),
                fill='tozeroy',
                fillcolor='rgba(214, 40, 40, 0.1)',
                hovertemplate='<b>%{text}</b><br>VIX: %{y:.2f}<extra></extra>',
                text=df_filtered.index.strftime('%Y-%m-%d %H:%M')
            ),
            row=2, col=1
        )
    
    # Update x-axis to show datetime labels at intervals
    tick_interval = max(1, len(df_filtered) // 10)
    tick_positions = df_filtered['numeric_index'][::tick_interval]
    tick_labels = df_filtered.index[::tick_interval].strftime('%Y-%m-%d %H:%M')
    
    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_positions,
        ticktext=tick_labels,
        tickangle=-45,
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=700,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=30, t=80, b=60)
    )
    
    fig.update_yaxes(title_text="SPX Price ($)", row=1, col=1)
    if show_vix:
        fig.update_yaxes(title_text="VIX", row=2, col=1)
    
    # Display plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    st.subheader("📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current SPX", f"${df_filtered['close'].iloc[-1]:.2f}", 
                  f"{df_filtered['close'].iloc[-1] - df_filtered['close'].iloc[0]:.2f}")
    with col2:
        if 'close_vix' in df_filtered.columns:
            st.metric("Current VIX", f"{df_filtered['close_vix'].iloc[-1]:.2f}",
                      f"{df_filtered['close_vix'].iloc[-1] - df_filtered['close_vix'].iloc[0]:.2f}")
    with col3:
        st.metric("SPX Range", f"${df_filtered['close'].max() - df_filtered['close'].min():.2f}")
    with col4:
        if 'close_vix' in df_filtered.columns:
            st.metric("VIX Range", f"{df_filtered['close_vix'].max() - df_filtered['close_vix'].min():.2f}")
    
    # Show dataframe
    if st.checkbox("Show Raw Data"):
        st.dataframe(df_filtered.drop(columns=['numeric_index']).tail(50))

def main():
    spx = read_data("SPX.parquet")
    vix = read_data("VIX4y.parquet")
    spx = add_moving_averages(spx)
    vix = add_moving_averages(vix)
    df = combine_dfs(spx, vix)
    
    create_plot(df)

if __name__ == "__main__":
    main()