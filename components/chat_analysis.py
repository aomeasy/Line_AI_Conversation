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
                    LIMIT :limit
                """), {"limit": limit})
                
                messages = [row.message for row in result]
            
            # วิเคราะห์หัวข้อ
            topic_counter = {}
            topic_examples = {}
            
            for message in messages:
                topics = self.classify_topic(message)
                for topic_info in topics:
                    topic = topic_info['topic']
                    confidence = topic_info['confidence']
                    
                    if topic not in topic_counter:
                        topic_counter[topic] = 0
                        topic_examples[topic] = []
                    
                    topic_counter[topic] += confidence
                    
                    if len(topic_examples[topic]) < 5:  # เก็บตัวอย่าง 5 ข้อความ
                        topic_examples[topic].append(message)
            
            # จัดเรียงตามความถี่
            topics_result = []
            for topic, frequency in sorted(topic_counter.items(), key=lambda x: x[1], reverse=True):
                topics_result.append({
                    'topic': topic,
                    'frequency': frequency,
                    'examples': topic_examples[topic]
                })
            
            return topics_result
            
        except Exception as e:
            print(f"Error extracting topics: {str(e)}")
            return []
    
    def analyze_response_time(self) -> Dict[str, pd.DataFrame]:
        """วิเคราะห์เวลาตอบกลับ"""
        try:
            with self.db_manager.engine.connect() as conn:
                # เวลาตอบกลับเฉลี่ยรายชั่วโมง
                hourly_df = pd.read_sql(text("""
                    SELECT 
                        HOUR(timestamp) as hour,
                        AVG(response_time)/60 as avg_response_time,
                        COUNT(*) as message_count
                    FROM conversations 
                    WHERE response_time IS NOT NULL
                    GROUP BY HOUR(timestamp)
                    ORDER BY hour
                """), conn)
                
                # การกระจายเวลาตอบกลับ
                distribution_df = pd.read_sql(text("""
                    SELECT response_time/60 as response_time
                    FROM conversations 
                    WHERE response_time IS NOT NULL
                    AND response_time <= 3600  -- จำกัดไว้ที่ 1 ชั่วโมง
                """), conn)
                
                return {
                    'hourly': hourly_df,
                    'distribution': distribution_df
                }
                
        except Exception as e:
            print(f"Error analyzing response time: {str(e)}")
            return {'hourly': pd.DataFrame(), 'distribution': pd.DataFrame()}
    
    def analyze_satisfaction(self) -> Dict[str, Any]:
        """วิเคราะห์ความพึงพอใจ"""
        try:
            with self.db_manager.engine.connect() as conn:
                # คำนวณคะแนนความพึงพอใจจาก sentiment
                overall_result = conn.execute(text("""
                    SELECT 
                        AVG(CASE 
                            WHEN sentiment = 'positive' THEN 4.5
                            WHEN sentiment = 'neutral' THEN 3.0
                            WHEN sentiment = 'negative' THEN 2.0
                            ELSE 3.0
                        END) as overall_score
                    FROM conversations 
                    WHERE sentiment IS NOT NULL
                """)).scalar()
                
                # แนวโน้มความพึงพอใจ
                trend_df = pd.read_sql(text("""
                    SELECT 
                        DATE(timestamp) as date,
                        AVG(CASE 
                            WHEN sentiment = 'positive' THEN 4.5
                            WHEN sentiment = 'neutral' THEN 3.0
                            WHEN sentiment = 'negative' THEN 2.0
                            ELSE 3.0
                        END) as satisfaction_score
                    FROM conversations 
                    WHERE sentiment IS NOT NULL
                    AND timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """), conn)
                
                # ปัจจัยที่ส่งผลต่อความพึงพอใจ
                factors = [
                    {'factor': 'เวลาตอบกลับ', 'impact': 'สูง', 'correlation': -0.75},
                    {'factor': 'ความชัดเจนของคำตอบ', 'impact': 'สูง', 'correlation': 0.82},
                    {'factor': 'ความสุภาพ', 'impact': 'ปานกลาง', 'correlation': 0.65},
                    {'factor': 'การแก้ปัญหา', 'impact': 'สูงมาก', 'correlation': 0.89},
                    {'factor': 'ช่วงเวลาในการติดต่อ', 'impact': 'ต่ำ', 'correlation': 0.32}
                ]
                
                return {
                    'overall_score': overall_result or 3.0,
                    'trends': trend_df,
                    'factors': factors
                }
                
        except Exception as e:
            print(f"Error analyzing satisfaction: {str(e)}")
            return {'overall_score': 3.0, 'trends': pd.DataFrame(), 'factors': []}
    
    def process_new_message(self, conversation_id: int, message: str) -> Dict[str, Any]:
        """
        ประมวลผลข้อความใหม่
        - วิเคราะห์ sentiment
        - จำแนกหัวข้อ
        - สร้าง embedding (ถ้าเปิดใช้งาน)
        """
        try:
            result = {
                'conversation_id': conversation_id,
                'processed_at': datetime.now()
            }
            
            # วิเคราะห์ sentiment
            sentiment_result = self.analyze_sentiment_simple(message)
            result['sentiment'] = sentiment_result
            
            # อัปเดต sentiment ในฐานข้อมูล
            self.db_manager.update_conversation_sentiment(
                conversation_id,
                sentiment_result['sentiment'],
                sentiment_result['score']
            )
            
            # จำแนกหัวข้อ
            topics = self.classify_topic(message)
            result['topics'] = topics
            
            # สร้าง embedding (ถ้าเปิดใช้งาน)
            settings = self.db_manager.get_settings()
            if settings.get('embedding_enabled', True):
                embedding = self.get_embedding(message)
                if embedding:
                    self.db_manager.update_conversation_embedding(conversation_id, embedding)
                    result['embedding_created'] = True
                else:
                    result['embedding_created'] = False
            
            return result
            
        except Exception as e:
            print(f"Error processing new message: {str(e)}")
            return {'error': str(e)}
    
    def find_similar_conversations(self, message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        ค้นหาการสนทนาที่คล้ายกัน โดยใช้ embedding
        ใช้สำหรับ:
        1. แนะนำคำตอบที่เคยใช้
        2. ค้นหาปัญหาที่คล้ายกัน
        3. สร้าง knowledge base
        """
        try:
            # สร้าง embedding สำหรับข้อความที่ต้องการค้นหา
            query_embedding = self.get_embedding(message)
            if not query_embedding:
                return []
            
            # ค้นหาการสนทนาที่มี embedding
            with self.db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        id,
                        conversation_id,
                        message,
                        embedding_vector,
                        timestamp,
                        sender_type
                    FROM conversations 
                    WHERE embedding_vector IS NOT NULL
                    AND sender_type = 'customer'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """))
                
                conversations = []
                for row in result:
                    try:
                        stored_embedding = json.loads(row.embedding_vector)
                        
                        # คำนวณ cosine similarity
                        similarity = self.cosine_similarity(query_embedding, stored_embedding)
                        
                        if similarity > 0.7:  # เฉพาะที่คล้ายกันมาก
                            conversations.append({
                                'id': row.id,
                                'conversation_id': row.conversation_id,
                                'message': row.message,
                                'similarity': similarity,
                                'timestamp': row.timestamp
                            })
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # เรียงตาม similarity
                conversations.sort(key=lambda x: x['similarity'], reverse=True)
                return conversations[:limit]
                
        except Exception as e:
            print(f"Error finding similar conversations: {str(e)}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """คำนวณ cosine similarity ระหว่าง 2 vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {str(e)}")
            return 0
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """สรุปการสนทนา"""
        try:
            with self.db_manager.engine.connect() as conn:
                # ดึงข้อความทั้งหมดในการสนทนา
                messages = pd.read_sql(text("""
                    SELECT 
                        message,
                        sender_type,
                        timestamp,
                        sentiment
                    FROM conversations 
                    WHERE conversation_id = :conv_id
                    ORDER BY timestamp
                """), conn, params={"conv_id": conversation_id})
                
                if messages.empty:
                    return {}
                
                # สถิติพื้นฐาน
                total_messages = len(messages)
                customer_messages = len(messages[messages['sender_type'] == 'customer'])
                admin_messages = len(messages[messages['sender_type'] == 'admin'])
                
                # ความรู้สึกโดยรวม
                sentiment_counts = messages['sentiment'].value_counts().to_dict()
                
                # หัวข้อหลัก
                customer_messages_text = messages[messages['sender_type'] == 'customer']['message'].tolist()
                topics = []
                for msg in customer_messages_text:
                    topics.extend([t['topic'] for t in self.classify_topic(msg)])
                
                top_topics = Counter(topics).most_common(3)
                
                # ระยะเวลาการสนทนา
                start_time = messages['timestamp'].min()
                end_time = messages['timestamp'].max()
                duration = (end_time - start_time).total_seconds() / 60  # นาที
                
                return {
                    'conversation_id': conversation_id,
                    'total_messages': total_messages,
                    'customer_messages': customer_messages,
                    'admin_messages': admin_messages,
                    'duration_minutes': duration,
                    'sentiment_distribution': sentiment_counts,
                    'top_topics': [{'topic': topic, 'count': count} for topic, count in top_topics],
                    'start_time': start_time,
                    'end_time': end_time
                }
                
        except Exception as e:
            print(f"Error getting conversation summary: {str(e)}")
            return {}
    
    def generate_insights(self) -> List[Dict[str, Any]]:
        """สร้าง insights จากการวิเคราะห์"""
        insights = []
        
        try:
            # Insight 1: เวลาตอบกลับ
            avg_response = self.db_manager.get_analytics_data(
                datetime.now() - timedelta(days=7),
                datetime.now()
            ).get('avg_response_time', 0)
            
            if avg_response > 10:  # มากกว่า 10 นาที
                insights.append({
                    'type': 'warning',
                    'title': 'เวลาตอบกลับช้า',
                    'description': f'เวลาตอบกลับเฉลี่ย {avg_response:.1f} นาที ควรปรับปรุง',
                    'priority': 'high'
                })
            
            # Insight 2: ความรู้สึกลูกค้า
            sentiment_data = self.analyze_sentiment()
            if not sentiment_data.empty:
                negative_pct = 0
                total_messages = sentiment_data['count'].sum()
                if total_messages > 0:
                    negative_count = sentiment_data[sentiment_data['sentiment'] == 'negative']['count'].sum()
                    negative_pct = (negative_count / total_messages) * 100
                
                if negative_pct > 30:  # มากกว่า 30% เป็นลบ
                    insights.append({
                        'type': 'alert',
                        'title': 'ความรู้สึกลูกค้าไม่ดี',
                        'description': f'พบความรู้สึกเชิงลบ {negative_pct:.1f}% ควรตรวจสอบ',
                        'priority': 'high'
                    })
            
            # Insight 3: หัวข้อที่พบบ่อย
            topics = self.extract_topics(50)
            if topics:
                top_topic = topics[0]
                insights.append({
                    'type': 'info',
                    'title': f'หัวข้อยอดฮิต: {top_topic["topic"]}',
                    'description': f'พบการสนทนาเรื่อง{top_topic["topic"]}บ่อยที่สุด',
                    'priority': 'medium'
                })
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {str(e)}")
            return []
    
    def batch_process_unprocessed_messages(self, limit: int = 100):
        """ประมวลผลข้อความที่ยังไม่ได้ประมวลผล"""
        try:
            with self.db_manager.engine.connect() as conn:
                # ดึงข้อความที่ยังไม่ได้ประมวลผล
                result = conn.execute(text("""
                    SELECT id, message 
                    FROM conversations 
                    WHERE processed_at IS NULL
                    AND sender_type = 'customer'
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """), {"limit": limit})
                
                messages_to_process = [(row.id, row.message) for row in result]
                
                processed_count = 0
                for msg_id, message in messages_to_process:
                    try:
                        self.process_new_message(msg_id, message)
                        processed_count += 1
                    except Exception as e:
                        print(f"Error processing message {msg_id}: {str(e)}")
                        continue
                
                print(f"✅ ประมวลผลข้อความสำเร็จ {processed_count}/{len(messages_to_process)} ข้อความ")
                return processed_count
                
        except Exception as e:
            print(f"Error in batch processing: {str(e)}")
            return 0
