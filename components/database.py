import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import json
import hashlib
from typing import Optional, Dict, List, Any
import streamlit as st
from utils.config import TIDB_URL

class DatabaseManager:
    """จัดการการเชื่อมต่อและดำเนินการกับฐานข้อมูล TiDB"""
    
    def __init__(self):
        self.engine = None
        self.connect()
        self.init_tables()
    
    def connect(self):
        """สร้างการเชื่อมต่อกับ TiDB"""
        try:
            self.engine = create_engine(
                TIDB_URL,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ เชื่อมต่อ TiDB สำเร็จ")
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อ TiDB: {str(e)}")
            raise
    
    def init_tables(self):
        """สร้างตารางที่จำเป็น"""
        try:
            with self.engine.connect() as conn:
                # ตาราง conversations - เก็บข้อมูลการสนทนา
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        conversation_id VARCHAR(100) NOT NULL,
                        user_id VARCHAR(100) NOT NULL,
                        message TEXT NOT NULL,
                        message_type ENUM('text', 'image', 'video', 'audio', 'file', 'sticker', 'location') DEFAULT 'text',
                        sender_type ENUM('customer', 'admin', 'system') NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time INT DEFAULT NULL COMMENT 'เวลาตอบกลับในวินาที',
                        sentiment ENUM('positive', 'negative', 'neutral') DEFAULT NULL,
                        sentiment_score DECIMAL(3,2) DEFAULT NULL COMMENT 'คะแนนความรู้สึก -1 ถึง 1',
                        embedding_vector JSON DEFAULT NULL COMMENT 'Vector embedding สำหรับการค้นหา',
                        processed_at TIMESTAMP NULL COMMENT 'เวลาที่ประมวลผล AI',
                        metadata JSON DEFAULT NULL COMMENT 'ข้อมูลเพิ่มเติม เช่น location, file_info',
                        INDEX idx_conversation_id (conversation_id),
                        INDEX idx_user_id (user_id),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_sender_type (sender_type),
                        INDEX idx_sentiment (sentiment)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # ตาราง conversation_summary - สรุปการสนทนาแต่ละเรื่อง
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS conversation_summary (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        conversation_id VARCHAR(100) NOT NULL UNIQUE,
                        user_id VARCHAR(100) NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP NULL,
                        total_messages INT DEFAULT 0,
                        customer_messages INT DEFAULT 0,
                        admin_messages INT DEFAULT 0,
                        avg_response_time DECIMAL(10,2) DEFAULT NULL COMMENT 'เวลาตอบกลับเฉลี่ยในวินาที',
                        satisfaction_score DECIMAL(3,2) DEFAULT NULL COMMENT 'คะแนนความพึงพอใจ 1-5',
                        summary TEXT DEFAULT NULL COMMENT 'สรุปการสนทนาด้วย AI',
                        tags JSON DEFAULT NULL COMMENT 'แท็กหัวข้อการสนทนา',
                        status ENUM('active', 'closed', 'escalated') DEFAULT 'active',
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_user_id (user_id),
                        INDEX idx_start_time (start_time),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # ตาราง topics - หัวข้อที่พบจากการวิเคราะห์
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS topics (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        topic_name VARCHAR(200) NOT NULL,
                        topic_keywords JSON NOT NULL COMMENT 'คำสำคัญของหัวข้อ',
                        frequency INT DEFAULT 1,
                        embedding_vector JSON DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_topic (topic_name)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # ตาราง settings - การตั้งค่าระบบ
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        setting_key VARCHAR(100) NOT NULL UNIQUE,
                        setting_value TEXT,
                        setting_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # ตาราง analytics_cache - แคชผลการวิเคราะห์
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_cache (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        cache_key VARCHAR(255) NOT NULL UNIQUE,
                        cache_data JSON NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_expires (expires_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # ตาราง admin_users - ผู้ใช้ที่มีสิทธิ์เข้าถึงระบบ
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        full_name VARCHAR(100),
                        role ENUM('admin', 'manager', 'agent') DEFAULT 'agent',
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                
                # สร้างผู้ใช้ admin เริ่มต้น (password: admin123)
                default_admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
                conn.execute(text("""
                    INSERT IGNORE INTO admin_users (username, password_hash, email, full_name, role) 
                    VALUES ('admin', :password_hash, 'admin@company.com', 'System Administrator', 'admin')
                """), {"password_hash": default_admin_hash})
                
                # สร้างการตั้งค่าเริ่มต้น
                default_settings = [
                    ('line_token', '', 'string', 'LINE Channel Access Token'),
                    ('line_secret', '', 'string', 'LINE Channel Secret'),
                    ('webhook_url', '', 'string', 'Webhook URL for LINE'),
                    ('embedding_enabled', 'true', 'boolean', 'Enable embedding for similarity search'),
                    ('auto_response', 'false', 'boolean', 'Enable automatic AI responses'),
                    ('response_threshold', '80', 'number', 'Confidence threshold for auto response'),
                    ('max_response_time', '300', 'number', 'Maximum response time in seconds'),
                    ('business_hours_start', '09:00', 'string', 'Business hours start time'),
                    ('business_hours_end', '18:00', 'string', 'Business hours end time'),
                ]
                
                for setting in default_settings:
                    conn.execute(text("""
                        INSERT IGNORE INTO settings (setting_key, setting_value, setting_type, description)
                        VALUES (:key, :value, :type, :desc)
                    """), {
                        "key": setting[0],
                        "value": setting[1],
                        "type": setting[2],
                        "desc": setting[3]
                    })
                
                conn.commit()
                print("✅ สร้างตารางและข้อมูลเริ่มต้นสำเร็จ")
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างตาราง: {str(e)}")
            raise
    
    def check_connection(self) -> bool:
        """ตรวจสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Connection check failed: {str(e)}")
            return False
    
    def insert_conversation(self, conversation_data: Dict[str, Any]) -> int:
        """เพิ่มข้อมูลการสนทนาใหม่"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO conversations 
                    (conversation_id, user_id, message, message_type, sender_type, response_time, metadata)
                    VALUES (:conversation_id, :user_id, :message, :message_type, :sender_type, :response_time, :metadata)
                """), {
                    "conversation_id": conversation_data.get('conversation_id'),
                    "user_id": conversation_data.get('user_id'),
                    "message": conversation_data.get('message'),
                    "message_type": conversation_data.get('message_type', 'text'),
                    "sender_type": conversation_data.get('sender_type'),
                    "response_time": conversation_data.get('response_time'),
                    "metadata": json.dumps(conversation_data.get('metadata', {}))
                })
                conn.commit()
                return result.lastrowid
        except Exception as e:
            print(f"Error inserting conversation: {str(e)}")
            raise
    
    def get_total_conversations(self) -> int:
        """ดึงจำนวนการสนทนาทั้งหมด"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT conversation_id) as total 
                    FROM conversations
                """))
                return result.scalar() or 0
        except Exception as e:
            print(f"Error getting total conversations: {str(e)}")
            return 0
    
    def get_today_conversations(self) -> int:
        """ดึงจำนวนการสนทนาวันนี้"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT conversation_id) as total 
                    FROM conversations 
                    WHERE DATE(timestamp) = CURDATE()
                """))
                return result.scalar() or 0
        except Exception as e:
            print(f"Error getting today conversations: {str(e)}")
            return 0
    
    def get_analytics_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """ดึงข้อมูลสำหรับ analytics dashboard"""
        try:
            with self.engine.connect() as conn:
                # Total conversations
                total_conv = conn.execute(text("""
                    SELECT COUNT(DISTINCT conversation_id) as total
                    FROM conversations 
                    WHERE DATE(timestamp) BETWEEN :start_date AND :end_date
                """), {"start_date": start_date, "end_date": end_date}).scalar() or 0
                
                # Total messages
                total_msg = conn.execute(text("""
                    SELECT COUNT(*) as total
                    FROM conversations 
                    WHERE DATE(timestamp) BETWEEN :start_date AND :end_date
                """), {"start_date": start_date, "end_date": end_date}).scalar() or 0
                
                # Unique customers
                unique_customers = conn.execute(text("""
                    SELECT COUNT(DISTINCT user_id) as total
                    FROM conversations 
                    WHERE DATE(timestamp) BETWEEN :start_date AND :end_date
                """), {"start_date": start_date, "end_date": end_date}).scalar() or 0
                
                # Average response time
                avg_response = conn.execute(text("""
                    SELECT AVG(response_time)/60 as avg_minutes
                    FROM conversations 
                    WHERE response_time IS NOT NULL 
                    AND DATE(timestamp) BETWEEN :start_date AND :end_date
                """), {"start_date": start_date, "end_date": end_date}).scalar() or 0
                
                return {
                    'total_conversations': total_conv,
                    'total_messages': total_msg,
                    'unique_customers': unique_customers,
                    'avg_response_time': avg_response,
                    'conversation_change': 0,  # TODO: Calculate change from previous period
                    'message_change': 0,
                    'customer_change': 0
                }
        except Exception as e:
            print(f"Error getting analytics data: {str(e)}")
            return {}
    
    def get_daily_conversation_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """ดึงข้อมูลการสนทนารายวัน"""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(DISTINCT conversation_id) as conversations,
                        COUNT(*) as messages
                    FROM conversations 
                    WHERE DATE(timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """), conn, params={"start_date": start_date, "end_date": end_date})
                return df
        except Exception as e:
            print(f"Error getting daily conversation data: {str(e)}")
            return pd.DataFrame()
    
    def get_message_type_distribution(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """ดึงข้อมูลการกระจายประเภทข้อความ"""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text("""
                    SELECT 
                        message_type,
                        COUNT(*) as count
                    FROM conversations 
                    WHERE DATE(timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY message_type
                    ORDER BY count DESC
                """), conn, params={"start_date": start_date, "end_date": end_date})
                return df
        except Exception as e:
            print(f"Error getting message type distribution: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_conversations(self, limit: int = 10) -> pd.DataFrame:
        """ดึงการสนทนาล่าสุด"""
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text("""
                    SELECT 
                        conversation_id,
                        user_id,
                        LEFT(message, 100) as message_preview,
                        sender_type,
                        timestamp,
                        message_type
                    FROM conversations 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """), conn, params={"limit": limit})
                return df
        except Exception as e:
            print(f"Error getting recent conversations: {str(e)}")
            return pd.DataFrame()
    
    def get_filtered_conversations(self, customer_id: Optional[str] = None, 
                                 date: Optional[datetime] = None, 
                                 limit: int = 50) -> pd.DataFrame:
        """ดึงการสนทนาตามเงื่อนไข"""
        try:
            query = """
                SELECT 
                    conversation_id,
                    user_id,
                    message,
                    sender_type,
                    timestamp,
                    message_type
                FROM conversations 
                WHERE 1=1
            """
            params = {}
            
            if customer_id:
                query += " AND user_id = :customer_id"
                params["customer_id"] = customer_id
            
            if date:
                query += " AND DATE(timestamp) = :date"
                params["date"] = date.date()
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
                return df
        except Exception as e:
            print(f"Error getting filtered conversations: {str(e)}")
            return pd.DataFrame()
    
    def get_conversation_context(self, limit: int = 100) -> List[Dict[str, Any]]:
        """ดึง context การสนทนาสำหรับ chatbot"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        conversation_id,
                        user_id,
                        message,
                        sender_type,
                        timestamp,
                        sentiment
                    FROM conversations 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                return [dict(row._mapping) for row in result]
        except Exception as e:
            print(f"Error getting conversation context: {str(e)}")
            return []
    
    def get_settings(self) -> Dict[str, Any]:
        """ดึงการตั้งค่าระบบ"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT setting_key, setting_value, setting_type 
                    FROM settings
                """))
                
                settings = {}
                for row in result:
                    key = row.setting_key
                    value = row.setting_value
                    setting_type = row.setting_type
                    
                    # Convert value based on type
                    if setting_type == 'boolean':
                        value = value.lower() == 'true'
                    elif setting_type == 'number':
                        value = float(value) if value else 0
                    elif setting_type == 'json':
                        value = json.loads(value) if value else {}
                    
                    settings[key] = value
                
                return settings
        except Exception as e:
            print(f"Error getting settings: {str(e)}")
            return {}
    
    def update_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """อัปเดตการตั้งค่า"""
        try:
            with self.engine.connect() as conn:
                for key, value in settings_dict.items():
                    # Convert value to string based on type
                    if isinstance(value, bool):
                        str_value = 'true' if value else 'false'
                    elif isinstance(value, (dict, list)):
                        str_value = json.dumps(value)
                    else:
                        str_value = str(value)
                    
                    conn.execute(text("""
                        INSERT INTO settings (setting_key, setting_value) 
                        VALUES (:key, :value)
                        ON DUPLICATE KEY UPDATE 
                        setting_value = :value,
                        updated_at = CURRENT_TIMESTAMP
                    """), {"key": key, "value": str_value})
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating settings: {str(e)}")
            return False
    
    def update_conversation_sentiment(self, conversation_id: int, 
                                   sentiment: str, 
                                   sentiment_score: float) -> bool:
        """อัปเดตความรู้สึกของการสนทนา"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE conversations 
                    SET sentiment = :sentiment,
                        sentiment_score = :sentiment_score,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = :conversation_id
                """), {
                    "conversation_id": conversation_id,
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating sentiment: {str(e)}")
            return False
    
    def update_conversation_embedding(self, conversation_id: int, 
                                    embedding_vector: List[float]) -> bool:
        """อัปเดต embedding vector ของการสนทนา"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE conversations 
                    SET embedding_vector = :embedding_vector,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = :conversation_id
                """), {
                    "conversation_id": conversation_id,
                    "embedding_vector": json.dumps(embedding_vector)
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating embedding: {str(e)}")
            return False
    
    def cache_analytics_result(self, cache_key: str, data: Dict[str, Any], 
                             expires_hours: int = 1) -> bool:
        """เก็บผลการวิเคราะห์ในแคช"""
        try:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO analytics_cache (cache_key, cache_data, expires_at)
                    VALUES (:key, :data, :expires)
                    ON DUPLICATE KEY UPDATE
                    cache_data = :data,
                    expires_at = :expires,
                    created_at = CURRENT_TIMESTAMP
                """), {
                    "key": cache_key,
                    "data": json.dumps(data),
                    "expires": expires_at
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"Error caching result: {str(e)}")
            return False
    
    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """ดึงผลการวิเคราะห์จากแคช"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT cache_data 
                    FROM analytics_cache 
                    WHERE cache_key = :key AND expires_at > CURRENT_TIMESTAMP
                """), {"key": cache_key}).scalar()
                
                if result:
                    return json.loads(result)
                return None
        except Exception as e:
            print(f"Error getting cached result: {str(e)}")
            return None
    
    def cleanup_expired_cache(self):
        """ล้างแคชที่หมดอายุ"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM analytics_cache 
                    WHERE expires_at < CURRENT_TIMESTAMP
                """))
                conn.commit()
        except Exception as e:
            print(f"Error cleaning up cache: {str(e)}")
    
    def verify_admin_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """ตรวจสอบข้อมูลเข้าสู่ระบบ admin"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, username, email, full_name, role, is_active
                    FROM admin_users 
                    WHERE username = :username AND password_hash = :password_hash AND is_active = TRUE
                """), {"username": username, "password_hash": password_hash}).fetchone()
                
                if result:
                    # Update last login
                    conn.execute(text("""
                        UPDATE admin_users 
                        SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = :user_id
                    """), {"user_id": result.id})
                    conn.commit()
                    
                    return dict(result._mapping)
                return None
        except Exception as e:
            print(f"Error verifying credentials: {str(e)}")
            return None
