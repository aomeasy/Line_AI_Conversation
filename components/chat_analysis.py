import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import re
from sqlalchemy import text
from utils.config import EMBEDDING_API_URL, EMBEDDING_MODEL, CHAT_API_URL, CHAT_MODEL

class ChatAnalyzer:
    """คลาสสำหรับวิเคราะห์การสนทนา"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # คำสำคัญสำหรับการวิเคราะห์ sentiment
        self.positive_keywords = [
            'ดี', 'เยี่ยม', 'สุดยอด', 'ชอบ', 'พอใจ', 'ประทับใจ', 'ขอบคุณ', 'สวย', 'เก่ง',
            'ใช่', 'โอเค', 'ตกลง', 'ยอดเยี่ยม', 'เจ๋ง', 'เลิศ', 'perfect', 'good', 'great',
            'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome', 'love', 'like'
        ]
        
        self.negative_keywords = [
            'แย่', 'ไม่ดี', 'เสีย', 'ชัง', 'เกลียด', 'โกรธ', 'ผิดหวัง', 'น่าเบื่อ', 'แปลก',
            'ไม่', 'อย่า', 'หยุด', 'ปัญหา', 'ข้อผิดพลาด', 'เสียใจ', 'bad', 'terrible',
            'awful', 'hate', 'angry', 'disappointed', 'problem', 'error', 'wrong'
        ]
        
        # หัวข้อการสนทนาที่พบบ่อย
        self.topic_keywords = {
            'การสั่งซื้อ': ['สั่ง', 'ซื้อ', 'order', 'buy', 'purchase', 'เก็บเงิน', 'จ่าย', 'ชำระ'],
            'การจัดส่ง': ['จัดส่ง', 'ส่ง', 'delivery', 'ship', 'ขนส่ง', 'รับ', 'ได้รับ'],
            'สินค้า': ['สินค้า', 'ของ', 'product', 'item', 'คุณภาพ', 'เสียหาย', 'ใหม่'],
            'ราคา': ['ราคา', 'เงิน', 'price', 'cost', 'แพง', 'ถูก', 'ค่า', 'บาท'],
            'การคืนสินค้า': ['คืน', 'เปลี่ยน', 'return', 'refund', 'exchange', 'แลก'],
            'บริการ': ['บริการ', 'service', 'ช่วย', 'help', 'สอบถาม', 'แนะนำ'],
            'โปรโมชั่น': ['โปร', 'ลด', 'promotion', 'discount', 'sale', 'แถม'],
            'การร้องเรียน': ['ร้องเรียน', 'complaint', 'แจ้ง', 'ปัญหา', 'เรื่อง']
        }
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        ได้ embedding vector จาก text
        Embedding ใช้สำหรับ:
        1. ค้นหาข้อความที่คล้ายกัน
        2. จัดกลุ่มหัวข้อการสนทนา
        3. แนะนำคำตอบที่เหมาะสม
        4. วิเคราะห์ความคล้ายคลึงของปัญหา
        """
        try:
            response = requests.post(
                EMBEDDING_API_URL,
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                print(f"Error getting embedding: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error in get_embedding: {str(e)}")
            return None
    
    def analyze_sentiment_simple(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ความรู้สึกแบบง่าย (rule-based)"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = max(-0.8, -0.5 - (negative_count - positive_count) * 0.1)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': abs(score)
        }
    
    def classify_topic(self, text: str) -> List[Dict[str, Any]]:
        """จำแนกหัวข้อของข้อความ"""
        text_lower = text.lower()
        topics_found = []
        
        for topic, keywords in self.topic_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            
            if keyword_count > 0:
                confidence = min(1.0, keyword_count / len(keywords) * 2)
                topics_found.append({
                    'topic': topic,
                    'confidence': confidence,
                    'keywords_found': keyword_count
                })
        
        # เรียงตาม confidence
        topics_found.sort(key=lambda x: x['confidence'], reverse=True)
        return topics_found[:3]  # คืนค่าแค่ 3 หัวข้อแรก
    
    def analyze_sentiment(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> pd.DataFrame:
        """วิเคราะห์ความรู้สึกของการสนทนา"""
        try:
            # ตรวจสอบ cache ก่อน
            cache_key = f"sentiment_analysis_{start_date}_{end_date}"
            cached_result = self.db_manager.get_cached_result(cache_key)
            
            if cached_result:
                return pd.DataFrame(cached_result)
            
            # Query ข้อมูลจากฐานข้อมูล
            query = """
                SELECT sentiment, COUNT(*) as count
                FROM conversations 
                WHERE sentiment IS NOT NULL
            """
            params = {}
            
            if start_date and end_date:
                query += " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                params.update({"start_date": start_date, "end_date": end_date})
            
            query += " GROUP BY sentiment"
            
            with self.db_manager.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
            
            # บันทึกลง cache
            if not df.empty:
                self.db_manager.cache_analytics_result(cache_key, df.to_dict('records'))
            
            return df
            
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return pd.DataFrame()
    
    def get_sentiment_trend(self, days: int = 30) -> pd.DataFrame:
        """ดึงแนวโน้มความรู้สึกตามเวลา"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with self.db_manager.engine.connect() as conn:
                df = pd.read_sql(text("""
                    SELECT 
                        DATE(timestamp) as date,
                        AVG(sentiment_score) as sentiment_score,
                        COUNT(*) as message_count
                    FROM conversations 
                    WHERE sentiment_score IS NOT NULL
                    AND DATE(timestamp) BETWEEN :start_date AND :end_date
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """), conn, params={"start_date": start_date, "end_date": end_date})
            
            return df
            
        except Exception as e:
            print(f"Error getting sentiment trend: {str(e)}")
            return pd.DataFrame()
    
    def extract_topics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """สกัดหัวข้อจากการสนทนา"""
        try:
            # ดึงข้อความล่าสุด
            with self.db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT message 
                    FROM conversations 
                    WHERE sender_type = 'customer'
                    ORDER BY timestamp DESC
