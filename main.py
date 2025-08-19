import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from components.database import DatabaseManager
from components.chat_analysis import ChatAnalyzer
from components.chatbot import ChatBot
from utils.auth import check_admin_auth
from utils.config import *


# Page configuration
st.set_page_config(
    page_title="LINE OA Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for gray theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4a5568, #718096);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar-content {
        background-color: #edf2f7;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .chat-message {
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .admin-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .customer-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def check_database():
    try:
        # สมมติว่ามีฟังก์ชันเชื่อม DB
        # db_manager.test_connection()
        return True, None
    except Exception as e:
        return False, str(e)

def check_embedding_api():
    try:
        r = requests.get("http://209.15.123.47:11434/api/embedding/health")  # endpoint สมมติ
        if r.status_code == 200:
            return True, "nomic-embed-text:latest"
        else:
            return False, None
    except Exception as e:
        return False, str(e)
        
def check_chat_api():
    try:
        r = requests.get("http://209.15.123.47:11434/api/generate/health")  # endpoint สมมติ
        if r.status_code == 200:
            return True, "Qwen3:14b"
        else:
            return False, None
    except Exception as e:
        return False, str(e)
        
def render_status_card(title, ok, model=None, error=None):
    color = "#1e5631" if ok else "#8b0000"
    status_text = "🟢 พร้อมใช้งาน" if ok else "🔴 ไม่พร้อมใช้งาน"

    html = f"""
    <div style="background-color:{color};padding:15px;border-radius:12px;color:white;">
        <h4>{title}</h4>
        <p>{status_text}</p>
    """
    if model:
        html += f"<p><b>Model:</b> {model}</p>"
    if error and not ok:
        html += f"<p style='font-size:12px;color:#ffcccc;'>{error}</p>"
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

def main():
    st.title("📊 สถานะระบบ")
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if 'chat_analyzer' not in st.session_state:
        st.session_state.chat_analyzer = ChatAnalyzer(st.session_state.db_manager)
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatBot()
        
    col1, col2, col3 = st.columns(3)

    # Database
    db_ok, db_err = check_database()
    with col1:
        render_status_card("Database", db_ok, error=db_err)

    # Embedding API
    emb_ok, emb_info = check_embedding_api()
    with col2:
        render_status_card("Embedding API", emb_ok, model=emb_info if emb_ok else None, error=None if emb_ok else emb_info)

    # Chat API
    chat_ok, chat_info = check_chat_api()
    with col3:
        render_status_card("Chat API", chat_ok, model=chat_info if chat_ok else None, error=None if chat_ok else chat_info)

    # Authentication check
    if not check_admin_auth():
        return

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 LINE OA Analytics Dashboard</h1>
        <p>ระบบวิเคราะห์และสรุปการสนทนา LINE Official Account</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/200x80/4a5568/ffffff?text=LOGO", width=200)
        
        # Navigation
        page = st.selectbox(
            "เลือกหน้า",
            ["Dashboard", "Chat Analysis", "Conversation Logs", "AI Chatbot", "Settings"],
            index=0
        )


    
        # Quick stats
        st.subheader("สถิติด่วน")
        try:
            total_chats = st.session_state.db_manager.get_total_conversations()
            today_chats = st.session_state.db_manager.get_today_conversations()
            
            st.metric("การสนทนาทั้งหมด", total_chats)
            st.metric("การสนทนาวันนี้", today_chats)
        except Exception as e:
            st.error(f"ข้อผิดพลาด: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Main content based on selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Chat Analysis":
        show_chat_analysis()
    elif page == "Conversation Logs":
        show_conversation_logs()
    elif page == "AI Chatbot":
        show_chatbot()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    st.header("📈 Dashboard Overview")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("วันที่เริ่มต้น", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", datetime.now())
    
    if start_date > end_date:
        st.error("วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุด")
        return
    
    try:
        # Get analytics data
        analytics_data = st.session_state.db_manager.get_analytics_data(start_date, end_date)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="การสนทนาทั้งหมด",
                value=analytics_data.get('total_conversations', 0),
                delta=analytics_data.get('conversation_change', 0)
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="ข้อความทั้งหมด",
                value=analytics_data.get('total_messages', 0),
                delta=analytics_data.get('message_change', 0)
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="ลูกค้าเฉพาะ",
                value=analytics_data.get('unique_customers', 0),
                delta=analytics_data.get('customer_change', 0)
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="เวลาตอบกลับเฉลี่ย",
                value=f"{analytics_data.get('avg_response_time', 0):.1f} นาที"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily conversation chart
            daily_data = st.session_state.db_manager.get_daily_conversation_data(start_date, end_date)
            if not daily_data.empty:
                fig = px.line(
                    daily_data, 
                    x='date', 
                    y='conversations',
                    title='การสนทนารายวัน',
                    color_discrete_sequence=['#4a5568']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Message type distribution
            message_types = st.session_state.db_manager.get_message_type_distribution(start_date, end_date)
            if not message_types.empty:
                fig = px.pie(
                    message_types,
                    values='count',
                    names='message_type',
                    title='การกระจายประเภทข้อความ',
                    color_discrete_sequence=['#718096', '#a0aec0', '#cbd5e0']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent conversations table
        st.subheader("การสนทนาล่าสุด")
        recent_conversations = st.session_state.db_manager.get_recent_conversations(limit=10)
        if not recent_conversations.empty:
            st.dataframe(
                recent_conversations,
                use_container_width=True,
                hide_index=True
            )
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}")

def show_chat_analysis():
    st.header("🔍 Chat Analysis")
    
    # Analysis options
    analysis_type = st.selectbox(
        "เลือกประเภทการวิเคราะห์",
        ["Sentiment Analysis", "Topic Analysis", "Response Time Analysis", "Customer Satisfaction"]
    )
    
    if analysis_type == "Sentiment Analysis":
        show_sentiment_analysis()
    elif analysis_type == "Topic Analysis":
        show_topic_analysis()
    elif analysis_type == "Response Time Analysis":
        show_response_time_analysis()
    elif analysis_type == "Customer Satisfaction":
        show_satisfaction_analysis()

def show_conversation_logs():
    st.header("💬 Conversation Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        customer_filter = st.text_input("ค้นหาลูกค้า (User ID)")
    
    with col2:
        date_filter = st.date_input("วันที่", datetime.now())
    
    with col3:
        limit = st.number_input("จำนวนข้อความ", min_value=10, max_value=1000, value=50)
    
    # Get conversation data
    try:
        conversations = st.session_state.db_manager.get_filtered_conversations(
            customer_id=customer_filter if customer_filter else None,
            date=date_filter,
            limit=limit
        )
        
        if not conversations.empty:
            for _, conv in conversations.iterrows():
                message_class = "admin-message" if conv['sender_type'] == 'admin' else "customer-message"
                st.markdown(f"""
                <div class="chat-message {message_class}">
                    <strong>{conv['sender_type'].upper()}</strong> - {conv['timestamp']}<br>
                    <strong>User:</strong> {conv['user_id']}<br>
                    <p>{conv['message']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ไม่พบข้อมูลการสนทนา")
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {str(e)}")

def show_chatbot():
    st.header("🤖 AI Chatbot Assistant")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("ถามคำถามเกี่ยวกับข้อมูลการสนทนา..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("กำลังคิด..."):
                try:
                    # Get response from chatbot
                    response = st.session_state.chatbot.get_response(
                        prompt, 
                        context=st.session_state.db_manager.get_conversation_context()
                    )
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                except Exception as e:
                    error_msg = f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def show_settings():
    st.header("⚙️ Settings")
    
    # LINE Settings
    st.subheader("LINE Configuration")
    
    # Get current settings
    current_settings = st.session_state.db_manager.get_settings()
    
    with st.form("line_settings"):
        line_token = st.text_input(
            "LINE Channel Access Token",
            value=current_settings.get('line_token', ''),
            type="password",
            help="ใส่ Channel Access Token จาก LINE Developers Console"
        )
        
        line_secret = st.text_input(
            "LINE Channel Secret",
            value=current_settings.get('line_secret', ''),
            type="password",
            help="ใส่ Channel Secret จาก LINE Developers Console"
        )
        
        webhook_url = st.text_input(
            "Webhook URL",
            value=current_settings.get('webhook_url', ''),
            help="URL สำหรับรับ Webhook จาก LINE"
        )
        
        submitted = st.form_submit_button("บันทึกการตั้งค่า")
        
        if submitted:
            try:
                st.session_state.db_manager.update_settings({
                    'line_token': line_token,
                    'line_secret': line_secret,
                    'webhook_url': webhook_url
                })
                st.success("บันทึกการตั้งค่าเรียบร้อย!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")
    
    # AI Settings
    st.subheader("AI Configuration")
    
    with st.form("ai_settings"):
        embedding_enabled = st.checkbox(
            "เปิดใช้งาน Embedding",
            value=current_settings.get('embedding_enabled', True),
            help="ใช้สำหรับการค้นหาและจัดกลุ่มข้อความที่คล้ายกัน"
        )
        
        auto_response = st.checkbox(
            "เปิดใช้งานการตอบกลับอัตโนมัติ",
            value=current_settings.get('auto_response', False),
            help="ให้ AI ช่วยตอบกลับลูกค้าอัตโนมัติ"
        )
        
        response_threshold = st.slider(
            "ความมั่นใจในการตอบกลับอัตโนมัติ (%)",
            min_value=50,
            max_value=95,
            value=current_settings.get('response_threshold', 80),
            help="ถ้าความมั่นใจต่ำกว่านี้ จะส่งให้เจ้าหน้าที่ตอบ"
        )
        
        ai_submitted = st.form_submit_button("บันทึกการตั้งค่า AI")
        
        if ai_submitted:
            try:
                st.session_state.db_manager.update_settings({
                    'embedding_enabled': embedding_enabled,
                    'auto_response': auto_response,
                    'response_threshold': response_threshold
                })
                st.success("บันทึกการตั้งค่า AI เรียบร้อย!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")
    
    # Database Status
    st.subheader("Database Status")
    try:
        db_status = st.session_state.db_manager.check_connection()
        if db_status:
            st.success("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        else:
            st.error("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
    except Exception as e:
        st.error(f"❌ ข้อผิดพลาดในการตรวจสอบฐานข้อมูล: {str(e)}")

def show_sentiment_analysis():
    """แสดงผลการวิเคราะห์ความรู้สึก"""
    try:
        sentiment_data = st.session_state.chat_analyzer.analyze_sentiment()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution pie chart
            fig = px.pie(
                sentiment_data,
                values='count',
                names='sentiment',
                title='การกระจายความรู้สึก',
                color_discrete_map={
                    'positive': '#48bb78',
                    'negative': '#f56565',
                    'neutral': '#718096'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment trend over time
            trend_data = st.session_state.chat_analyzer.get_sentiment_trend()
            if not trend_data.empty:
                fig = px.line(
                    trend_data,
                    x='date',
                    y='sentiment_score',
                    title='แนวโน้มความรู้สึกตามเวลา',
                    color_discrete_sequence=['#4a5568']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ความรู้สึก: {str(e)}")

def show_topic_analysis():
    """แสดงผลการวิเคราะห์หัวข้อ"""
    try:
        topics = st.session_state.chat_analyzer.extract_topics()
        
        if topics:
            st.subheader("หัวข้อที่พบบ่อย")
            
            for i, topic in enumerate(topics[:10], 1):
                st.write(f"{i}. **{topic['topic']}** (ความถี่: {topic['frequency']})")
                with st.expander(f"ตัวอย่างข้อความ - หัวข้อ {i}"):
                    for example in topic['examples'][:3]:
                        st.write(f"- {example}")
        else:
            st.info("ไม่พบข้อมูลหัวข้อ")
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์หัวข้อ: {str(e)}")

def show_response_time_analysis():
    """แสดงผลการวิเคราะห์เวลาตอบกลับ"""
    try:
        response_data = st.session_state.chat_analyzer.analyze_response_time()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Average response time by hour
            hourly_data = response_data.get('hourly', pd.DataFrame())
            if not hourly_data.empty:
                fig = px.bar(
                    hourly_data,
                    x='hour',
                    y='avg_response_time',
                    title='เวลาตอบกลับเฉลี่ยรายชั่วโมง',
                    color_discrete_sequence=['#4a5568']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Response time distribution
            distribution = response_data.get('distribution', pd.DataFrame())
            if not distribution.empty:
                fig = px.histogram(
                    distribution,
                    x='response_time',
                    title='การกระจายเวลาตอบกลับ',
                    color_discrete_sequence=['#718096']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์เวลาตอบกลับ: {str(e)}")

def show_satisfaction_analysis():
    """แสดงผลการวิเคราะห์ความพึงพอใจ"""
    try:
        satisfaction_data = st.session_state.chat_analyzer.analyze_satisfaction()
        
        # Overall satisfaction score
        overall_score = satisfaction_data.get('overall_score', 0)
        st.metric("คะแนนความพึงพอใจโดยรวม", f"{overall_score:.1f}/5.0")
        
        # Satisfaction trends
        trend_data = satisfaction_data.get('trends', pd.DataFrame())
        if not trend_data.empty:
            fig = px.line(
                trend_data,
                x='date',
                y='satisfaction_score',
                title='แนวโน้มความพึงพอใจ',
                color_discrete_sequence=['#4a5568']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Factors affecting satisfaction
        factors = satisfaction_data.get('factors', [])
        if factors:
            st.subheader("ปัจจัยที่ส่งผลต่อความพึงพอใจ")
            for factor in factors[:5]:
                st.write(f"- **{factor['factor']}**: {factor['impact']} (สหสัมพันธ์: {factor['correlation']:.2f})")
    
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ความพึงพอใจ: {str(e)}")

if __name__ == "__main__":

    main()




