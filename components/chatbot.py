import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
from utils.config import CHAT_API_URL, CHAT_MODEL

class ChatBot:
    """
    AI Chatbot สำหรับช่วยเหลือ Admin และตอบคำถามลูกค้า
    
    ความสามารถ:
    1. ตอบคำถามเกี่ยวกับข้อมูลการสนทนา
    2. วิเคราะห์และสรุปข้อมูล
    3. แนะนำการปรับปรุงบริการ
    4. ช่วยตอบลูกค้าอัตโนมัติ (ในอนาคต)
    """
    
    def __init__(self):
        self.model_url = CHAT_API_URL
        self.model_name = CHAT_MODEL
        self.system_prompt = """คุณคือ AI Assistant สำหรับระบบวิเคราะห์การสนทนา LINE OA 

คุณมีความสามารถในการ:
1. วิเคราะห์ข้อมูลการสนทนา
2. สรุปสถิติและแนวโน้ม
3. ให้คำแนะนำในการปรับปรุงบริการ
4. ตอบคำถามเกี่ยวกับข้อมูล

กรุณาตอบเป็นภาษาไทยที่เป็นมิตร สุภาพ และให้ข้อมูลที่เป็นประโยชน์
หากไม่มีข้อมูลเพียงพอ ให้แจ้งชัดเจน และแนะนำทางเลือกอื่น"""
    
    def get_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """ได้คำตอบจาก AI"""
        try:
            # เตรียม context จากข้อมูลการสนทนา
            context_text = self._prepare_context(context) if context else ""
            
            # สร้าง prompt
            full_prompt = f"""{self.system_prompt}

Context ข้อมูลการสนทนา (10 รายการล่าสุด):
{context_text}

คำถามจาก Admin: {user_message}

คำตอบ:"""

            # เรียก AI API
            response = requests.post(
                self.model_url,
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                # ตรวจสอบและปรับปรุงคำตอบ
                if ai_response:
                    return self._post_process_response(ai_response, user_message)
                else:
                    return "ขออภัย ไม่สามารถสร้างคำตอบได้ในขณะนี้"
            
            else:
                return f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI (Status: {response.status_code})"
                
        except requests.exceptions.Timeout:
            return "การเชื่อมต่อ AI หมดเวลา กรุณาลองใหม่อีกครั้ง"
        except requests.exceptions.ConnectionError:
            return "ไม่สามารถเชื่อมต่อกับ AI ได้ กรุณาตรวจสอบการตั้งค่า"
        except Exception as e:
            return f"เกิดข้อผิดพลาดไม่คาดคิด: {str(e)}"
    
    def _prepare_context(self, context: List[Dict]) -> str:
        """เตรียม context สำหรับ AI"""
        if not context:
            return ""
        
        context_lines = []
        for i, conv in enumerate(context[:10], 1):  # เอาแค่ 10 รายการล่าสุด
            timestamp = conv.get('timestamp', 'Unknown')
            user_id = conv.get('user_id', 'Unknown')
            sender = conv.get('sender_type', 'Unknown')
            message = conv.get('message', '')[:100]  # จำกัดความยาว
            sentiment = conv.get('sentiment', 'Unknown')
            
            context_lines.append(
                f"{i}. [{timestamp}] {sender} ({user_id}): {message} [ความรู้สึก: {sentiment}]"
            )
        
        return "\n".join(context_lines)
    
    def _post_process_response(self, response: str, original_question: str) -> str:
        """ปรับปรุงคำตอบก่อนส่งให้ผู้ใช้"""
        # ลบข้อความที่ไม่จำเป็น
        response = re.sub(r'^\s*คำตอบ:\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^\s*ตอบ:\s*', '', response, flags=re.MULTILINE)
        
        # เพิ่มความสุภาพ
        if not response.startswith(('สวัสดี', 'ขอบคุณ', 'ตาม')):
            response = f"ตามข้อมูลที่มี {response}"
        
        # จำกัดความยาว
        if len(response) > 2000:
            response = response[:1950] + "...\n\n(คำตอบถูกตัดทอนเนื่องจากยาวเกินไป)"
        
        return response.strip()
    
    def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """วิเคราะห์เจตนาของคำถาม"""
        question_lower = question.lower()
        
        intents = {
            'analytics': ['สถิติ', 'วิเคราะห์', 'จำนวน', 'กราฟ', 'ข้อมูล', 'รายงาน'],
            'sentiment': ['ความรู้สึก', 'พอใจ', 'ไม่พอใจ', 'โกรธ', 'ดีใจ', 'sentiment'],
            'topics': ['หัวข้อ', 'เรื่อง', 'ปัญหา', 'topic', 'ร้องเรียน'],
            'performance': ['ประสิทธิภาพ', 'เร็ว', 'ช้า', 'ตอบกลับ', 'response time'],
            'suggestions': ['แนะนำ', 'ปรับปรุง', 'พัฒนา', 'ช่วย', 'ควร']
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                detected_intents.append({
                    'intent': intent,
                    'confidence': score / len(keywords),
                    'keywords_found': score
                })
        
        # เรียงตาม confidence
        detected_intents.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'question': question,
            'intents': detected_intents[:3],  # เอาแค่ 3 อันแรก
            'primary_intent': detected_intents[0]['intent'] if detected_intents else 'general'
        }
    
    def generate_suggested_responses(self, customer_message: str, 
                                   context: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """
        สร้างคำตอบที่แนะนำสำหรับเจ้าหน้าที่
        ใช้สำหรับช่วยเจ้าหน้าที่ตอบลูกค้าได้เร็วขึ้น
        """
        try:
            # วิเคราะห์ประเภทของคำถามลูกค้า
            message_lower = customer_message.lower()
            
            suggested_responses = []
            
            # คำตอบสำหรับการทักทาย
            if any(greeting in message_lower for greeting in ['สวัสดี', 'ว', 'hello', 'hi']):
                suggested_responses.append({
                    'type': 'greeting',
                    'response': 'สวัสดีค่ะ ยินดีให้บริการ 🙏 มีอะไรให้ช่วยเหลือไหมคะ?',
                    'confidence': 0.9
                })
            
            # คำตอบสำหรับการสอบถามราคา
            elif any(price in message_lower for price in ['ราคา', 'เท่าไหร่', 'price', 'cost']):
                suggested_responses.extend([
                    {
                        'type': 'price_inquiry',
                        'response': 'สำหรับราคาสินค้าค่ะ ขอให้ส่งรูปหรือชื่อสินค้ามาให้หน่อยค่ะ จะได้เช็คราคาให้ถูกต้อง 💰',
                        'confidence': 0.85
                    },
                    {
                        'type': 'price_inquiry',
                        'response': 'ราคาสินค้าจะแตกต่างกันไปตามแต่ละรุ่นค่ะ ขอรบกวนส่งรายละเอียดสินค้าที่สนใจมาด้วยนะคะ',
                        'confidence': 0.8
                    }
                ])
            
            # คำตอบสำหรับการสอบถามการจัดส่ง
            elif any(shipping in message_lower for shipping in ['จัดส่ง', 'ส่ง', 'delivery', 'ship']):
                suggested_responses.extend([
                    {
                        'type': 'shipping',
                        'response': 'การจัดส่งใช้เวลา 2-3 วันทำการค่ะ หากต้องการเร่งด่วนสามารถเลือก EMS ได้ 🚚',
                        'confidence': 0.9
                    },
                    {
                        'type': 'shipping',
                        'response': 'สำหรับค่าจัดส่งค่ะ ภายในกรุงเทพ 50 บาท ต่างจังหวัด 80 บาท (Kerry) และ 120 บาท (EMS)',
                        'confidence': 0.85
                    }
                ])
            
            # คำตอบสำหรับการร้องเรียน
            elif any(complaint in message_lower for complaint in ['ร้องเรียน', 'ปัญหา', 'เสีย', 'แย่', 'ไม่ดี']):
                suggested_responses.extend([
                    {
                        'type': 'complaint',
                        'response': 'ขออภัยในความไม่สะดวกค่ะ 🙏 ขอรบกวนส่งรูปภาพหรือรายละเอียดปัญหามาให้ดูหน่อยค่ะ จะได้ช่วยแก้ไขให้',
                        'confidence': 0.9
                    },
                    {
                        'type': 'complaint',
                        'response': 'เสียใจด้วยนะคะที่มีปัญหา 😔 ขอดูรายละเอียดปัญหาหน่อยค่ะ เราจะรีบแก้ไขให้เร็วที่สุด',
                        'confidence': 0.85
                    }
                ])
            
            # คำตอบสำหรับการขอบคุณ
            elif any(thanks in message_lower for thanks in ['ขอบคุณ', 'thank', 'ขอบใจ']):
                suggested_responses.extend([
                    {
                        'type': 'thanks',
                        'response': 'ยินดีค่ะ หากมีอะไรอีกสามารถสอบถามมาได้เสมอนะคะ 😊',
                        'confidence': 0.95
                    },
                    {
                        'type': 'thanks',
                        'response': 'ไม่เป็นไรค่ะ ขอบคุณที่ใช้บริการด้วยค่ะ 🙏',
                        'confidence': 0.9
                    }
                ])
            
            # คำตอบทั่วไป
            else:
                suggested_responses.append({
                    'type': 'general',
                    'response': 'สวัสดีค่ะ ขอดูรายละเอียดหน่อยนะคะ จะได้ตอบคำถามให้ถูกต้องค่ะ 🤗',
                    'confidence': 0.6
                })
            
            # เรียงตาม confidence
            suggested_responses.sort(key=lambda x: x['confidence'], reverse=True)
            
            return suggested_responses[:3]  # คืนค่าแค่ 3 ตัวเลือก
            
        except Exception as e:
            print(f"Error generating suggested responses: {str(e)}")
            return []
    
    def generate_auto_response(self, customer_message: str, 
                             context: Optional[List[Dict]] = None,
                             confidence_threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """
        สร้างคำตอบอัตโนมัติสำหรับลูกค้า
        ใช้เมื่อเปิดใช้งาน auto_response ในการตั้งค่า
        """
        try:
            suggested = self.generate_suggested_responses(customer_message, context)
            
            if suggested and suggested[0]['confidence'] >= confidence_threshold:
                # ใช้ AI เพื่อปรับปรุงคำตอบให้เหมาะสมกับ context
                enhanced_response = self._enhance_response_with_context(
                    suggested[0]['response'], 
                    customer_message, 
                    context
                )
                
                return {
                    'response': enhanced_response,
                    'confidence': suggested[0]['confidence'],
                    'type': suggested[0]['type'],
                    'is_auto': True,
                    'timestamp': datetime.now()
                }
            
            return None  # ความมั่นใจไม่เพียงพอสำหรับตอบอัตโนมัติ
            
        except Exception as e:
            print(f"Error generating auto response: {str(e)}")
            return None
    
    def _enhance_response_with_context(self, base_response: str, 
                                     customer_message: str,
                                     context: Optional[List[Dict]]) -> str:
        """ปรับปรุงคำตอบด้วย AI โดยใช้ context"""
        try:
            context_text = self._prepare_context(context) if context else ""
            
            enhance_prompt = f"""ปรับปรุงคำตอบให้เหมาะสมกับบริบทการสนทนา:

ข้อความลูกค้า: {customer_message}
คำตอบเริ่มต้น: {base_response}

Context การสนทนา:
{context_text}

ปรับปรุงคำตอบให้:
1. เหมาะสมกับบริบท
2. สุภาพและเป็นมิตร
3. ตรงประเด็น
4. สั้นกระทัดรัด

คำตอบที่ปรับปรุงแล้ว:"""
            
            response = requests.post(
                self.model_url,
                json={
                    "model": self.model_name,
                    "prompt": enhance_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "max_tokens": 200
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced = result.get('response', '').strip()
                return enhanced if enhanced else base_response
            else:
                return base_response
                
        except Exception as e:
            print(f"Error enhancing response: {str(e)}")
            return base_response
    
    def get_conversation_insights(self, conversation_data: List[Dict]) -> str:
        """วิเคราะห์และให้ insights จากการสนทนา"""
        try:
            if not conversation_data:
                return "ไม่มีข้อมูลการสนทนาให้วิเคราะห์"
            
            # เตรียมข้อมูลสำหรับ AI
            convo_summary = self._summarize_conversation_for_ai(conversation_data)
            
            insights_prompt = f"""วิเคราะห์การสนทนานี้และให้ insights:

{convo_summary}

กรุณาวิเคราะห์:
1. ความรู้สึกโดยรวมของลูกค้า
2. ประเด็นหลักที่ลูกค้าสนใจ
3. ประสิทธิภาพการตอบกลับของเจ้าหน้าที่
4. ข้อเสนอแนะเพื่อปรับปรุงบริการ

การวิเคราะห์:"""
            
            response = requests.post(
                self.model_url,
                json={
                    "model": self.model_name,
                    "prompt": insights_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                insights = result.get('response', '').strip()
                return insights if insights else "ไม่สามารถวิเคราะห์ได้ในขณะนี้"
            else:
                return "เกิดข้อผิดพลาดในการวิเคราะห์"
                
        except Exception as e:
            print(f"Error getting insights: {str(e)}")
            return f"เกิดข้อผิดพลาด: {str(e)}"
    
    def _summarize_conversation_for_ai(self, conversation_data: List[Dict]) -> str:
        """สรุปการสนทนาสำหรับ AI วิเคราะห์"""
        lines = []
        
        for i, msg in enumerate(conversation_data[:20], 1):  # จำกัดแค่ 20 ข้อความ
            sender = msg.get('sender_type', 'unknown')
            message = msg.get('message', '')[:150]  # จำกัดความยาว
            timestamp = msg.get('timestamp', '')
            sentiment = msg.get('sentiment', 'neutral')
            
            lines.append(f"{i}. [{sender}] {message} (ความรู้สึก: {sentiment})")
        
        return "\n".join(lines)
    
    def check_service_availability(self) -> Dict[str, Any]:
        """ตรวจสอบความพร้อมของ AI service"""
        try:
            test_response = requests.post(
                self.model_url,
                json={
                    "model": self.model_name,
                    "prompt": "สวัสดี",
                    "stream": False,
                    "options": {"max_tokens": 10}
                },
                timeout=10
            )
            
            if test_response.status_code == 200:
                return {
                    'available': True,
                    'status': 'online',
                    'model': self.model_name,
                    'response_time': test_response.elapsed.total_seconds()
                }
            else:
                return {
                    'available': False,
                    'status': 'error',
                    'error_code': test_response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'available': False,
                'status': 'timeout',
                'error': 'Service timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'available': False,
                'status': 'connection_error',
                'error': 'Cannot connect to service'
            }
        except Exception as e:
            return {
                'available': False,
                'status': 'error',
                'error': str(e)
            }
    
    def get_help_suggestions(self, user_type: str = 'admin') -> List[str]:
        """ให้คำแนะนำคำถามที่สามารถถามได้"""
        if user_type == 'admin':
            return [
                "📊 สถิติการสนทนาวันนี้เป็นอย่างไร?",
                "😊 ความรู้สึกของลูกค้าโดยรวมเป็นอย่างไร?",
                "🏷️ หัวข้อไหนที่ลูกค้าสนทนากันบ่อยที่สุด?",
                "⏱️ เวลาตอบกลับเฉลี่ยเป็นเท่าไหร่?",
                "💡 มีข้อเสนอแนะในการปรับปรุงบริการไหม?",
                "📈 แนวโน้มการสนทนาในช่วง 7 วันที่ผ่านมา",
                "🎯 ปัญหาที่พบบ่อยที่สุดคืออะไร?",
                "🔍 วิเคราะห์ประสิทธิภาพทีมงาน"
            ]
        else:
            return [
                "🛍️ สอบถามข้อมูลสินค้า",
                "💰 สอบถามราคา",
                "🚚 สอบถามการจัดส่ง",
                "🔄 สอบถามการคืนสินค้า",
                "❓ สอบถามข้อมูลทั่วไป"
            ]
    
    def format_response_for_display(self, response: str) -> str:
        """จัดรูปแบบคำตอบให้แสดงผลดี"""
        # แปลง markdown basics
        response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)
        response = re.sub(r'\*(.*?)\*', r'<em>\1</em>', response)
        
        # แปลงรายการ
        response = re.sub(r'^\d+\.\s+', '• ', response, flags=re.MULTILINE)
        response = re.sub(r'^-\s+', '• ', response, flags=re.MULTILINE)
        
        # เพิ่ม emoji สำหรับหัวข้อ
        response = re.sub(r'สถิติ', '📊 สถิติ', response)
        response = re.sub(r'ความรู้สึก', '😊 ความรู้สึก', response)
        response = re.sub(r'หัวข้อ', '🏷️ หัวข้อ', response)
        response = re.sub(r'เวลาตอบกลับ', '⏱️ เวลาตอบกลับ', response)
        response = re.sub(r'ข้อเสนอแนะ', '💡 ข้อเสนอแนะ', response)
        
        return response