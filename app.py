import streamlit as st
from supabase import create_client, Client
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import seaborn as sns
from datetime import datetime, timedelta
import json
import numpy as np
import io
from PIL import Image

# Set page configuration with a more professional look
st.set_page_config(
    page_title="ChatHub Pro Dashboard",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.1);
        border-bottom-color: rgb(99, 102, 241);
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .css-1v3fvcr {
        background-color: #f8f9fa;
    }
    .dataframe {
        font-size: 0.9rem;
    }
    .stButton>button {
        background-color: rgb(99, 102, 241);
        color: white;
        border: none;
        border-radius: 0.25rem;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: rgb(79, 82, 221);
    }
    .stSelectbox>div>div {
        background-color: white;
        border-radius: 0.25rem;
    }
    .stDateInput>div>div {
        background-color: white;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to convert matplotlib figure to streamlit
def plt_to_streamlit(fig, use_container_width=True):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    st.image(img, use_column_width=use_container_width)
    plt.close(fig)

# Supabase credentials
SUPABASE_URL = "https://svjindgyokubrdxesdlp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2amluZGd5b2t1YnJkeGVzZGxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk1OTM2MTQsImV4cCI6MjA1NTE2OTYxNH0.P_giMWMPtnBT4Ca7AsHCcuNtoV0OWgsY6VHTqDqh0Sw"

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# App header with logo and title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://via.placeholder.com/80x80.png?text=CH", width=80)
with col2:
    st.title("💬 Chat-Hub Pro Dashboard")
    st.markdown("<p style='font-size: 1.2rem; color: #6B7280;'>Comprehensive analytics for your conversational AI platform</p>", unsafe_allow_html=True)

# Create tabs for better organization
tabs = st.tabs(["📊 Overview", "👥 User Analysis", "💬 Conversation Details", "📈 Advanced Analytics"])

# Date filter in sidebar
st.sidebar.header("Filters")
with st.sidebar.expander("Date Range", expanded=True):
    # Calculate default date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    date_range = st.date_input(
        "Select Date Range",
        value=(start_date.date(), end_date.date()),
        key="date_range"
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
    else:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[0], datetime.max.time())

# Fetch data with date filter
@st.cache_data(ttl=300)
def fetch_chat_logs(start_date, end_date):
    # Convert dates to ISO format for Supabase query
    start_iso = start_date.isoformat()
    end_iso = end_date.isoformat()
    
    # Query with date filter
    response = supabase.table("chat_logs") \
        .select("*") \
        .gte("timestamp", start_iso) \
        .lte("timestamp", end_iso) \
        .execute()
    
    if hasattr(response, 'data'):
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            # Calculate message_length if not already present
            if "message_length" not in df.columns or df["message_length"].isna().any():
                df["message_length"] = df["user_message"].str.len()
            return df
    return pd.DataFrame()

# Fetch data
chat_logs_df = fetch_chat_logs(start_date, end_date)

# Check if data exists
if chat_logs_df.empty:
    st.warning("No chat logs found for the selected date range.")
else:
    # Additional filters in sidebar
    with st.sidebar.expander("Additional Filters", expanded=True):
        # Filter by sentiment
        if "sentiment_label" in chat_logs_df.columns:
            sentiment_options = ["All"] + list(chat_logs_df["sentiment_label"].dropna().unique())
            selected_sentiment = st.selectbox("Sentiment", sentiment_options)
            
            if selected_sentiment != "All":
                chat_logs_df = chat_logs_df[chat_logs_df["sentiment_label"] == selected_sentiment]
        
        # Filter by drop-off
        if "drop_off" in chat_logs_df.columns:
            drop_off_options = ["All", "Yes", "No"]
            selected_drop_off = st.selectbox("Drop-off", drop_off_options)
            
            if selected_drop_off == "Yes":
                chat_logs_df = chat_logs_df[chat_logs_df["drop_off"] == True]
            elif selected_drop_off == "No":
                chat_logs_df = chat_logs_df[chat_logs_df["drop_off"] == False]
    
    # Display user count and other metrics in sidebar
    st.sidebar.header("Quick Stats")
    st.sidebar.metric("Total Users", chat_logs_df["email"].nunique())
    st.sidebar.metric("Total Conversations", chat_logs_df["conversation_id"].nunique())
    st.sidebar.metric("Total Messages", len(chat_logs_df))
    
    # OVERVIEW TAB
    with tabs[0]:
        # Top metrics row
        st.subheader("📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0;font-size:1rem;color:#6B7280;">Total Conversations</h3>
                <p style="margin:0;font-size:2rem;font-weight:bold;color:#111827;">{chat_logs_df["conversation_id"].nunique()}</p>
                <p style="margin:0;font-size:0.8rem;color:#6B7280;">Unique conversation threads</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0;font-size:1rem;color:#6B7280;">Total Users</h3>
                <p style="margin:0;font-size:2rem;font-weight:bold;color:#111827;">{chat_logs_df["email"].nunique()}</p>
                <p style="margin:0;font-size:0.8rem;color:#6B7280;">Unique users engaged</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            avg_response_time = chat_logs_df["response_time"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0;font-size:1rem;color:#6B7280;">Avg Response Time</h3>
                <p style="margin:0;font-size:2rem;font-weight:bold;color:#111827;">{avg_response_time:.2f}s</p>
                <p style="margin:0;font-size:0.8rem;color:#6B7280;">Average bot response time</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            drop_off_rate = 0
            if "drop_off" in chat_logs_df.columns:
                drop_off_rate = (chat_logs_df["drop_off"] == True).mean() * 100
            
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0;font-size:1rem;color:#6B7280;">Drop-off Rate</h3>
                <p style="margin:0;font-size:2rem;font-weight:bold;color:#111827;">{drop_off_rate:.1f}%</p>
                <p style="margin:0;font-size:0.8rem;color:#6B7280;">Users who abandoned chat</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Daily message volume chart
        st.subheader("📈 Daily Message Volume")
        
        # Group by date and count messages
        chat_logs_df["date"] = chat_logs_df["timestamp"].dt.date
        daily_volume = chat_logs_df.groupby("date").size().reset_index(name="message_count")
        
        # Create line chart with Matplotlib
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(daily_volume["date"], daily_volume["message_count"], marker='o', linestyle='-', color='#6366f1')
        
        # Format the x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        # Add labels and grid
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Messages')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Tight layout to ensure everything fits
        fig.tight_layout()
        
        # Display the plot in Streamlit
        plt_to_streamlit(fig)
        
        # Sentiment distribution if available
        if "sentiment_label" in chat_logs_df.columns and chat_logs_df["sentiment_label"].notna().any():
            st.subheader("😊 Sentiment Distribution")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Pie chart for sentiment distribution
                sentiment_counts = chat_logs_df["sentiment_label"].value_counts().reset_index()
                sentiment_counts.columns = ["sentiment", "count"]
                
                colors = {
                    "positive": "#4ade80",  # Green
                    "neutral": "#60a5fa",   # Blue
                    "negative": "#f87171"   # Red
                }
                
                # Map colors to sentiments, with fallback for unexpected values
                color_map = [colors.get(s.lower(), "#9ca3af") for s in sentiment_counts["sentiment"]]
                
                # Create pie chart with matplotlib
                fig, ax = plt.subplots(figsize=(8, 8))
                wedges, texts, autotexts = ax.pie(
                    sentiment_counts["count"], 
                    labels=sentiment_counts["sentiment"],
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=color_map,
                    wedgeprops=dict(width=0.5)  # For donut chart
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.axis('equal')
                
                # Create a white circle at the center for donut chart
                centre_circle = plt.Circle((0, 0), 0.3, fc='white')
                ax.add_patch(centre_circle)
                
                # Style the labels and percentages
                plt.setp(autotexts, size=10, weight="bold")
                plt.setp(texts, size=12)
                
                # Display the plot
                plt_to_streamlit(fig)
            
            with col2:
                # Sentiment score distribution if available
                if "sentiment_score" in chat_logs_df.columns and chat_logs_df["sentiment_score"].notna().any():
                    # Histogram of sentiment scores with matplotlib
                    fig, ax = plt.subplots(figsize=(8, 5))
                    
                    # Create histogram
                    n, bins, patches = ax.hist(
                        chat_logs_df["sentiment_score"],
                        bins=20,
                        color='#6366f1',
                        alpha=0.7
                    )
                    
                    # Add labels and title
                    ax.set_xlabel('Sentiment Score (-1 to 1)')
                    ax.set_ylabel('Count')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Tight layout
                    fig.tight_layout()
                    
                    # Display the plot
                    plt_to_streamlit(fig)
        
        # Recent chat logs table
        st.subheader("📜 Recent Chat Logs")
        
        # Create a more readable dataframe for display
        display_df = chat_logs_df[["timestamp", "email", "user_message", "chatbot_reply", "response_time"]].copy()
        display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Add sentiment if available
        if "sentiment_label" in chat_logs_df.columns:
            display_df["sentiment"] = chat_logs_df["sentiment_label"]
        
        # Sort by timestamp (newest first)
        display_df = display_df.sort_values(by="timestamp", ascending=False)
        
        # Display with pagination
        page_size = 10
        total_pages = len(display_df) // page_size + (1 if len(display_df) % page_size > 0 else 0)
        
        col1, col2 = st.columns([4, 1])
        with col2:
            page_number = st.number_input("Page", min_value=1, max_value=max(1, total_pages), value=1)
        
        start_idx = (page_number - 1) * page_size
        end_idx = min(start_idx + page_size, len(display_df))
        
        st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True)
    
    # USER ANALYSIS TAB
    with tabs[1]:
        st.subheader("👥 User Engagement Analysis")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Top users by message count
            user_message_counts = chat_logs_df.groupby("email").size().reset_index(name="message_count")
            user_message_counts = user_message_counts.sort_values(by="message_count", ascending=False).head(10)
            
            # Create horizontal bar chart with matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot horizontal bars
            bars = ax.barh(
                user_message_counts["email"],
                user_message_counts["message_count"],
                color='#6366f1'
            )
            
            # Add value labels to the bars
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width + 0.5,
                    bar.get_y() + bar.get_height()/2,
                    f'{int(width)}',
                    ha='left',
                    va='center'
                )
            
            # Customize the plot
            ax.set_xlabel('Number of Messages')
            ax.set_title('Top Users by Message Count')
            ax.invert_yaxis()  # To have the highest value at the top
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
        
        with col2:
            # Average response time by user
            user_response_times = chat_logs_df.groupby("email")["response_time"].mean().reset_index()
            user_response_times = user_response_times.sort_values(by="response_time").head(10)
            
            # Create horizontal bar chart with matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot horizontal bars
            bars = ax.barh(
                user_response_times["email"],
                user_response_times["response_time"],
                color='#6366f1'
            )
            
            # Add value labels to the bars
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width + 0.1,
                    bar.get_y() + bar.get_height()/2,
                    f'{width:.2f}s',
                    ha='left',
                    va='center'
                )
            
            # Customize the plot
            ax.set_xlabel('Average Response Time (s)')
            ax.set_title('Users with Fastest Response Times')
            ax.invert_yaxis()  # To have the fastest response at the top
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
        
        # User explorer
        st.subheader("🔍 User Explorer")
        
        selected_email = st.selectbox("Select User by Email", [""] + list(chat_logs_df["email"].unique()))
        
        if selected_email:
            user_data = chat_logs_df[chat_logs_df["email"] == selected_email]
            
            # User metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Messages", len(user_data))
            
            with col2:
                st.metric("Conversations", user_data["conversation_id"].nunique())
            
            with col3:
                avg_response_time = user_data["response_time"].mean()
                st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
            
            with col4:
                if "message_length" in user_data.columns:
                    avg_message_length = user_data["message_length"].mean()
                    st.metric("Avg Message Length", f"{avg_message_length:.0f} chars")
            
            # User conversation history
            st.subheader(f"Conversation History for {selected_email}")
            
            # Group by conversation
            conversations = user_data.sort_values(by="timestamp")
            
            # Display conversations grouped by conversation_id
            for conv_id, conv_data in conversations.groupby("conversation_id"):
                with st.expander(f"Conversation {conv_id} - {conv_data['timestamp'].min().strftime('%Y-%m-%d %H:%M')}"):
                    for _, row in conv_data.iterrows():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.markdown(f"**{row['timestamp'].strftime('%H:%M:%S')}**")
                        
                        with col2:
                            st.markdown(f"**User:** {row['user_message']}")
                            st.markdown(f"**Bot:** {row['chatbot_reply']}")
                            
                            # Show additional metadata
                            metadata = []
                            if "response_time" in row:
                                metadata.append(f"Response time: {row['response_time']:.2f}s")
                            if "sentiment_label" in row and pd.notna(row["sentiment_label"]):
                                metadata.append(f"Sentiment: {row['sentiment_label']}")
                            if "sentiment_score" in row and pd.notna(row["sentiment_score"]):
                                metadata.append(f"Score: {row['sentiment_score']:.2f}")
                            
                            if metadata:
                                st.markdown(f"*{' | '.join(metadata)}*")
                            
                            st.markdown("---")
    
    # CONVERSATION DETAILS TAB
    with tabs[2]:
        st.subheader("💬 Conversation Analysis")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Message length distribution
            if "message_length" in chat_logs_df.columns:
                # Create histogram with matplotlib
                fig, ax = plt.subplots(figsize=(8, 5))
                
                # Plot histogram
                n, bins, patches = ax.hist(
                    chat_logs_df["message_length"],
                    bins=30,
                    color='#6366f1',
                    alpha=0.7
                )
                
                # Add labels and title
                ax.set_xlabel('Message Length (characters)')
                ax.set_ylabel('Count')
                ax.set_title('User Message Length Distribution')
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Tight layout
                fig.tight_layout()
                
                # Display the plot
                plt_to_streamlit(fig)
        
        with col2:
            # Response time distribution
            # Create histogram with matplotlib
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Plot histogram
            n, bins, patches = ax.hist(
                chat_logs_df["response_time"],
                bins=30,
                color='#6366f1',
                alpha=0.7
            )
            
            # Add labels and title
            ax.set_xlabel('Response Time (seconds)')
            ax.set_ylabel('Count')
            ax.set_title('Response Time Distribution')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
        
        # Conversation length analysis
        st.subheader("Conversation Length Analysis")
        
        # Calculate messages per conversation
        conv_lengths = chat_logs_df.groupby("conversation_id").size().reset_index(name="message_count")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Histogram of conversation lengths
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Plot histogram
            n, bins, patches = ax.hist(
                conv_lengths["message_count"],
                bins=20,
                color='#6366f1',
                alpha=0.7
            )
            
            # Add labels
            ax.set_xlabel('Messages per Conversation')
            ax.set_ylabel('Number of Conversations')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
        
        with col2:
            # Drop-off analysis if available
            if "drop_off" in chat_logs_df.columns:
                # Group conversations and check if any message has drop_off=True
                conv_drop_offs = chat_logs_df.groupby("conversation_id")["drop_off"].any().reset_index()
                
                # Count conversations with and without drop-offs
                drop_off_counts = conv_drop_offs["drop_off"].value_counts()
                
                # Create labels for the pie chart
                labels = ['Completed', 'Dropped Off']
                sizes = [
                    drop_off_counts.get(False, 0),
                    drop_off_counts.get(True, 0)
                ]
                colors = ['#4ade80', '#f87171']
                
                # Create pie chart
                fig, ax = plt.subplots(figsize=(8, 8))
                
                # Plot pie chart
                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    wedgeprops=dict(width=0.5)  # For donut chart
                )
                
                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.axis('equal')
                
                # Create a white circle at the center for donut chart
                centre_circle = plt.Circle((0, 0), 0.3, fc='white')
                ax.add_patch(centre_circle)
                
                # Add title
                ax.set_title('Conversation Completion Rate')
                
                # Style the labels and percentages
                plt.setp(autotexts, size=10, weight="bold")
                plt.setp(texts, size=12)
                
                # Display the plot
                plt_to_streamlit(fig)
    
    # ADVANCED ANALYTICS TAB
    with tabs[3]:
        st.subheader("📈 Advanced Analytics")
        
        # Check if we have scraped data
        has_scraped_data = "scraped_data" in chat_logs_df.columns and not chat_logs_df["scraped_data"].isna().all()
        
        if has_scraped_data:
            # Sample of scraped data for analysis
            st.subheader("Scraped Data Analysis")
            
            # Extract a sample of non-null scraped data
            scraped_samples = chat_logs_df[chat_logs_df["scraped_data"].notna()].head(5)
            
            if not scraped_samples.empty:
                for i, row in enumerate(scraped_samples.iterrows()):
                    _, data = row
                    with st.expander(f"Scraped Data Sample {i+1}"):
                        try:
                            # If it's already a dict, use it directly
                            if isinstance(data["scraped_data"], dict):
                                scraped_json = data["scraped_data"]
                            else:
                                # Otherwise parse it as JSON
                                scraped_json = json.loads(data["scraped_data"])
                            
                            st.json(scraped_json)
                        except:
                            st.text(str(data["scraped_data"]))
        
        # Time-based analysis
        st.subheader("Time-Based Analysis")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Messages by hour of day
            chat_logs_df["hour"] = chat_logs_df["timestamp"].dt.hour
            hourly_counts = chat_logs_df.groupby("hour").size().reset_index(name="message_count")
            
            # Ensure all hours are represented
            all_hours = pd.DataFrame({"hour": range(24)})
            hourly_counts = all_hours.merge(hourly_counts, on="hour", how="left").fillna(0)
            
            # Create bar chart with matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot bars
            bars = ax.bar(
                hourly_counts["hour"],
                hourly_counts["message_count"],
                color='#6366f1',
                alpha=0.7
            )
            
            # Add labels and title
            ax.set_xlabel('Hour of Day (24h)')
            ax.set_ylabel('Number of Messages')
            ax.set_title('Message Volume by Hour of Day')
            
            # Set x-axis ticks to show all hours
            ax.set_xticks(range(0, 24, 2))
            ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
        
        with col2:
            # Messages by day of week
            chat_logs_df["day_of_week"] = chat_logs_df["timestamp"].dt.day_name()
            
            # Define day order
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            # Count messages by day
            day_counts = chat_logs_df.groupby("day_of_week").size().reset_index(name="message_count")
            
            # Ensure all days are represented and in correct order
            day_counts["day_of_week"] = pd.Categorical(day_counts["day_of_week"], categories=day_order, ordered=True)
            day_counts = day_counts.sort_values("day_of_week")
            
            # Create bar chart with matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot bars
            bars = ax.bar(
                day_counts["day_of_week"],
                day_counts["message_count"],
                color='#6366f1',
                alpha=0.7
            )
            
            # Add labels and title
            ax.set_xlabel('Day of Week')
            ax.set_ylabel('Number of Messages')
            ax.set_title('Message Volume by Day of Week')
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Tight layout
            fig.tight_layout()
            
            # Display the plot
            plt_to_streamlit(fig)
            
        # Add time of day vs response time analysis
        st.subheader("Response Time Analysis by Time of Day")
        
        # Group by hour and calculate average response time
        hourly_response_times = chat_logs_df.groupby("hour")["response_time"].mean().reset_index()
        
        # Ensure all hours are represented
        hourly_response_times = all_hours.merge(hourly_response_times, on="hour", how="left").fillna(0)
        
        # Create line chart with matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot line
        ax.plot(
            hourly_response_times["hour"],
            hourly_response_times["response_time"],
            marker='o',
            linestyle='-',
            color='#6366f1'
        )
        
        # Add labels and title
        ax.set_xlabel('Hour of Day (24h)')
        ax.set_ylabel('Average Response Time (seconds)')
        ax.set_title('Response Time by Hour of Day')
        
        # Set x-axis ticks to show all hours
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Tight layout
        fig.tight_layout()
        
        # Display the plot
        plt_to_streamlit(fig)

# Run the app
if __name__ == "__main__":
    print("Dashboard is running at http://localhost:8501")
