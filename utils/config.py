# Configuration file for LINE OA Analytics Dashboard
# ไฟล์การตั้งค่าสำหรับระบบวิเคราะห์ LINE OA

# Database Configuration
TIDB_URL = "mysql+pymysql://2wGpw4Qa2maXMEz.root:FMDCS56nmOL9KSWg@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/ntdatabase?ssl_verify_cert=false"

# AI Embedding Configuration
# Embedding ใช้สำหรับ:
# 1. ค้นหาข้อความที่คล้ายกัน - เพื่อหาปัญหาหรือคำถามที่เคยมีมาแล้ว
# 2. จัดกลุ่มหัวข้อการสนทนา - เพื่อจำแนกประเภทของการสนทนา
# 3. แนะนำคำตอบที่เหมาะสม - เพื่อช่วยเจ้าหน้าที่ตอบได้เร็วขึ้น
# 4. วิเคราะห์ความคล้ายคลึงของปัญหา - เพื่อหาแนวโน้มและปัญหาที่เกิดซ้ำ
EMBEDDING_API_URL = "http://209.15.123.47:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text:latest"

# AI Chat Configuration  
# สำหรับ Chatbot ที่ช่วย:
# 1. ตอบคำถาม Admin - วิเคราะห์ข้อมูลและให้คำแนะนำ
# 2. ช่วยตอบลูกค้า - แนะนำคำตอบและตอบอัตโนมัติ (ในอนาคต)
# 3. สรุปการสนทนา - สร้างรายงานและ insights
CHAT_API_URL = "http://209.15.123.47:11434/api/generate" 
CHAT_MODEL = "Qwen3:14b"

# Application Settings
APP_NAME = "LINE OA Analytics Dashboard"
APP_VERSION = "1.0.0"
DEBUG_MODE = False

# Cache Settings
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
ANALYTICS_CACHE_TTL = 1800  # 30 minutes for analytics results
EMBEDDING_CACHE_TTL = 86400  # 24 hours for embeddings

# Analysis Settings
DEFAULT_SENTIMENT_THRESHOLD = 0.5
DEFAULT_TOPIC_CONFIDENCE = 0.7
MAX_SIMILAR_CONVERSATIONS = 10
BATCH_PROCESSING_LIMIT = 100

# Response Time Settings (in seconds)
GOOD_RESPONSE_TIME = 300  # 5 minutes
ACCEPTABLE_RESPONSE_TIME = 900  # 15 minutes
POOR_RESPONSE_TIME = 1800  # 30 minutes

# Business Hours
BUSINESS_HOURS_START = 9  # 9 AM
BUSINESS_HOURS_END = 18  # 6 PM
TIMEZONE = "Asia/Bangkok"

# Dashboard Settings
DEFAULT_DATE_RANGE = 7  # days
MAX_RECORDS_PER_PAGE = 100
CHART_COLOR_SCHEME = ["#4a5568", "#718096", "#a0aec0", "#cbd5e0", "#e2e8f0"]

# Security Settings
SESSION_TIMEOUT = 3600  # 1 hour
MAX_LOGIN_ATTEMPTS = 5
PASSWORD_MIN_LENGTH = 8

# API Timeouts (in seconds)
EMBEDDING_API_TIMEOUT = 30
CHAT_API_TIMEOUT = 60
DATABASE_TIMEOUT = 30

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File Upload Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS = ['.txt', '.csv', '.xlsx', '.json']

# Notification Settings
ADMIN_EMAIL = "admin@company.com"
ALERT_THRESHOLDS = {
    'high_negative_sentiment': 0.3,  # 30% negative messages
    'slow_response_time': 1800,  # 30 minutes average
    'high_message_volume': 1000,  # messages per day
}

# Feature Flags
FEATURES = {
    'embedding_enabled': True,
    'auto_response_enabled': False,  # ปิดไว้ก่อน รอพัฒนาเพิ่ม
    'sentiment_analysis_enabled': True,
    'topic_extraction_enabled': True,
    'real_time_analytics': True,
    'email_notifications': False,
    'advanced_charts': True,
    'export_data': True,
}

# Default Admin Credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # ควรเปลี่ยนหลังติดตั้ง

# Status Messages
STATUS_MESSAGES = {
    'db_connected': "✅ เชื่อมต่อฐานข้อมูลสำเร็จ",
    'db_error': "❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้",
    'ai_online': "✅ AI Service ออนไลน์",
    'ai_offline': "❌ AI Service ไม่พร้อมใช้งาน",
    'processing': "⏳ กำลังประมวลผล...",
    'completed': "✅ ประมวลผลเสร็จสิ้น",
    'error': "❌ เกิดข้อผิดพลาด",
}

# Theme Colors (Gray Theme)
COLORS = {
    'primary': '#4a5568',
    'secondary': '#718096', 
    'success': '#48bb78',
    'warning': '#ed8936',
    'error': '#f56565',
    'info': '#4299e1',
    'light': '#f7fafc',
    'dark': '#2d3748',
    'muted': '#a0aec0',
}

# Chart Configuration
CHART_CONFIG = {
    'default_height': 400,
    'default_width': 800,
    'color_palette': CHART_COLOR_SCHEME,
    'background_color': 'rgba(0,0,0,0)',
    'grid_color': '#e2e8f0',
    'text_color': '#4a5568',
    'font_family': 'Arial, sans-serif',
}

# Pagination Settings
PAGINATION = {
    'conversations_per_page': 20,
    'messages_per_page': 50,
    'topics_per_page': 15,
    'analytics_limit': 100,
}

# Export Settings
EXPORT_FORMATS = ['CSV', 'Excel', 'JSON']
EXPORT_LIMITS = {
    'conversations': 10000,
    'messages': 50000, 
    'analytics': 1000,
}

# Validation Rules
VALIDATION = {
    'user_id_max_length': 100,
    'message_max_length': 4000,
    'conversation_id_max_length': 100,
    'topic_name_max_length': 200,
}

# Performance Monitoring
PERFORMANCE_THRESHOLDS = {
    'db_query_timeout': 30,  # seconds
    'api_response_timeout': 60,  # seconds
    'memory_usage_limit': 512,  # MB
    'cpu_usage_limit': 80,  # percentage
}

# Development Settings (only for development)
if DEBUG_MODE:
    LOG_LEVEL = "DEBUG"
    CACHE_TTL = 60  # 1 minute for development
    API_TIMEOUT = 10  # shorter timeout for development
