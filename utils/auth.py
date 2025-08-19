import streamlit as st
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

def check_admin_auth() -> bool:
    """ตรวจสอบการยืนยันตัวตนของ Admin"""
    
    # ตรวจสอบว่าเข้าสู่ระบบแล้วหรือยัง
    if st.session_state.get('authenticated', False):
        # ตรวจสอบ session timeout
        if 'auth_timestamp' in st.session_state:
            auth_time = st.session_state['auth_timestamp']
            current_time = datetime.now()
            
            # ถ้าเกิน 1 ชั่วโมง ให้ logout
            if current_time - auth_time > timedelta(hours=1):
                logout()
                return False
        
        return True
    
    # แสดงหน้า login
    show_login_page()
    return False

def show_login_page():
    """แสดงหน้าเข้าสู่ระบบ"""
    
    # CSS สำหรับหน้า login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        color: white;
        text-align: center;
        margin-top: 10vh;
    }
    .login-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .login-subtitle {
        font-size: 1rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: none;
        padding: 12px;
        font-size: 16px;
        background: rgba(255,255,255,0.9);
    }
    .login-button {
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: bold;
        color: white;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .login-button:hover {
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container หลัก
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Logo และ Title
    st.markdown("""
    <div class="login-title">🔐 Admin Login</div>
    <div class="login-subtitle">LINE OA Analytics Dashboard</div>
    """, unsafe_allow_html=True)
    
    # Form การเข้าสู่ระบบ
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="ชื่อผู้ใช้",
            key="login_username"
        )
        
        password = st.text_input(
            "Password", 
            type="password",
            placeholder="รหัสผ่าน",
            key="login_password"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 เข้าสู่ระบบ", 
                use_container_width=True
            )
        
        if submitted:
            if authenticate_user(username, password):
                st.success("✅ เข้าสู่ระบบสำเร็จ!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ข้อมูลการเข้าสู่ระบบทดสอบ
    st.markdown("---")
    with st.expander("ℹ️ ข้อมูลการเข้าสู่ระบบทดสอบ"):
        st.write("**Username:** admin")
        st.write("**Password:** admin123")
        st.warning("⚠️ กรุณาเปลี่ยนรหัสผ่านหลังจากเข้าสู่ระบบครั้งแรก")

def authenticate_user(username: str, password: str) -> bool:
    """ตรวจสอบข้อมูลการเข้าสู่ระบบ"""
    try:
        # ตรวจสอบ rate limiting
        if not check_rate_limit(username):
            st.error("🚫 ล็อกอินล้มเหลวหลายครั้ง กรุณาลองใหม่ในอีก 15 นาที")
            return False
        
        # ตรวจสอบข้อมูลกับฐานข้อมูล
        if 'db_manager' in st.session_state:
            user_data = st.session_state.db_manager.verify_admin_credentials(username, password)
            
            if user_data:
                # บันทึก session
                st.session_state['authenticated'] = True
                st.session_state['user_data'] = user_data
                st.session_state['auth_timestamp'] = datetime.now()
                
                # ล้าง rate limiting
                clear_rate_limit(username)
                
                return True
            else:
                # บันทึกความล้มเหลว
                record_failed_attempt(username)
                return False
        
        # Fallback สำหรับกรณีที่ไม่มี database
        from utils.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
        if username == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
            st.session_state['authenticated'] = True
            st.session_state['user_data'] = {
                'username': username,
                'role': 'admin',
                'full_name': 'System Administrator'
            }
            st.session_state['auth_timestamp'] = datetime.now()
            clear_rate_limit(username)
            return True
        
        record_failed_attempt(username)
        return False
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}")
        return False

def check_rate_limit(username: str) -> bool:
    """ตรวจสอบ rate limiting สำหรับการ login"""
    rate_limit_key = f"login_attempts_{username}"
    
    if rate_limit_key not in st.session_state:
        st.session_state[rate_limit_key] = []
    
    # ลบความพยายามเก่าที่เกิน 15 นาที
    current_time = datetime.now()
    attempts = st.session_state[rate_limit_key]
    valid_attempts = [
        attempt for attempt in attempts 
        if current_time - attempt < timedelta(minutes=15)
    ]
    st.session_state[rate_limit_key] = valid_attempts
    
    # ตรวจสอบจำนวนความพยายาม
    return len(valid_attempts) < 5

def record_failed_attempt(username: str):
    """บันทึกความพยายาม login ที่ล้มเหลว"""
    rate_limit_key = f"login_attempts_{username}"
    
    if rate_limit_key not in st.session_state:
        st.session_state[rate_limit_key] = []
    
    st.session_state[rate_limit_key].append(datetime.now())

def clear_rate_limit(username: str):
    """ล้าง rate limiting หลังจาก login สำเร็จ"""
    rate_limit_key = f"login_attempts_{username}"
    if rate_limit_key in st.session_state:
        del st.session_state[rate_limit_key]

def logout():
    """ออกจากระบบ"""
    # ล้างข้อมูล session
    keys_to_clear = ['authenticated', 'user_data', 'auth_timestamp']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ ออกจากระบบเรียบร้อย")
    time.sleep(1)
    st.rerun()

def get_current_user() -> Optional[Dict[str, Any]]:
    """ดึงข้อมูลผู้ใช้ปัจจุบัน"""
    if st.session_state.get('authenticated', False):
        return st.session_state.get('user_data')
    return None

def require_role(required_role: str) -> bool:
    """ตรวจสอบสิทธิ์ตาม role"""
    user_data = get_current_user()
    if not user_data:
        return False
    
    user_role = user_data.get('role', 'agent')
    
    # Role hierarchy: admin > manager > agent
    role_hierarchy = {
        'admin': 3,
        'manager': 2,
        'agent': 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def show_user_info():
    """แสดงข้อมูลผู้ใช้ในแถบด้านข้าง"""
    user_data = get_current_user()
    if user_data:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 ข้อมูลผู้ใช้")
            
            # รูปโปรไฟล์
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="
                    width: 60px; 
                    height: 60px; 
                    border-radius: 50%; 
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                ">
                    👤
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ข้อมูลผู้ใช้
            st.write(f"**ชื่อ:** {user_data.get('full_name', 'ไม่ระบุ')}")
            st.write(f"**ตำแหน่ง:** {get_role_display(user_data.get('role', 'agent'))}")
            st.write(f"**ผู้ใช้:** {user_data.get('username', 'Unknown')}")
            
            # แสดงเวลาการเข้าสู่ระบบ
            if 'auth_timestamp' in st.session_state:
                login_time = st.session_state['auth_timestamp']
                st.write(f"**เข้าสู่ระบบ:** {login_time.strftime('%H:%M:%S')}")
            
            # ปุ่มออกจากระบบ
            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                logout()

def get_role_display(role: str) -> str:
    """แปลง role เป็นชื่อที่แสดงผล"""
    role_names = {
        'admin': '👑 ผู้ดูแลระบบ',
        'manager': '👔 ผู้จัดการ',
        'agent': '👨‍💼 เจ้าหน้าที่'
    }
    return role_names.get(role, '❓ ไม่ระบุ')

def create_admin_user(username: str, password: str, email: str, full_name: str, role: str = 'agent') -> bool:
    """สร้างผู้ใช้ admin ใหม่"""
    try:
        # ตรวจสอบสิทธิ์ (เฉพาะ admin เท่านั้นที่สร้างผู้ใช้ใหม่ได้)
        if not require_role('admin'):
            return False
        
        # Hash รหัสผ่าน
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # บันทึกลงฐานข้อมูล
        if 'db_manager' in st.session_state:
            with st.session_state.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                
                conn.execute(text("""
                    INSERT INTO admin_users (username, password_hash, email, full_name, role)
                    VALUES (:username, :password_hash, :email, :full_name, :role)
                """), {
                    "username": username,
                    "password_hash": password_hash,
                    "email": email,
                    "full_name": full_name,
                    "role": role
                })
                conn.commit()
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")
        return False

def change_password(current_password: str, new_password: str) -> bool:
    """เปลี่ยนรหัสผ่าน"""
    try:
        user_data = get_current_user()
        if not user_data:
            return False
        
        username = user_data['username']
        
        # ตรวจสอบรหัสผ่านเก่า
        if not authenticate_user(username, current_password):
            st.error("รหัสผ่านปัจจุบันไม่ถูกต้อง")
            return False
        
        # Hash รหัสผ่านใหม่
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # อัปเดตในฐานข้อมูล
        if 'db_manager' in st.session_state:
            with st.session_state.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                
                conn.execute(text("""
                    UPDATE admin_users 
                    SET password_hash = :password_hash,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE username = :username
                """), {
                    "password_hash": new_password_hash,
                    "username": username
                })
                conn.commit()
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน: {str(e)}")
        return False

def validate_password_strength(password: str) -> Dict[str, Any]:
    """ตรวจสอบความแข็งแกร่งของรหัสผ่าน"""
    score = 0
    feedback = []
    
    # ความยาว
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("รหัสผ่านควรมีอย่างน้อย 8 ตัวอักษร")
    
    # ตัวอักษรใหญ่
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("ควรมีตัวอักษรใหญ่")
    
    # ตัวอักษรเล็ก
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("ควรมีตัวอักษรเล็ก")
    
    # ตัวเลข
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("ควรมีตัวเลข")
    
    # อักขระพิเศษ
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("ควรมีอักขระพิเศษ")
    
    # คำนวณความแข็งแกร่ง
    if score <= 2:
        strength = "อ่อนแอ"
        color = "red"
    elif score <= 3:
        strength = "ปานกลาง"
        color = "orange"
    elif score <= 4:
        strength = "ดี"
        color = "green"
    else:
        strength = "แข็งแกร่งมาก"
        color = "darkgreen"
    
    return {
        'score': score,
        'strength': strength,
        'color': color,
        'feedback': feedback,
        'is_strong': score >= 4
    }

def show_password_strength_meter(password: str):
    """แสดงเครื่องวัดความแข็งแกร่งของรหัสผ่าน"""
    if not password:
        return
    
    validation = validate_password_strength(password)
    
    # แสดงแถบความแข็งแกร่ง
    progress_html = f"""
    <div style="margin: 10px 0;">
        <div style="background-color: #e0e0e0; border-radius: 10px; height: 10px;">
            <div style="
                background-color: {validation['color']}; 
                width: {(validation['score']/5)*100}%; 
                height: 100%; 
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
        <small style="color: {validation['color']};">
            ความแข็งแกร่ง: {validation['strength']}
        </small>
    </div>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)
    
    # แสดงคำแนะนำ
    if validation['feedback']:
        with st.expander("💡 คำแนะนำในการปรับปรุงรหัสผ่าน"):
            for tip in validation['feedback']:
                st.write(f"• {tip}")

def get_user_activity_log(username: str, limit: int = 10) -> list:
    """ดึงบันทึกกิจกรรมของผู้ใช้"""
    try:
        if 'db_manager' in st.session_state:
            with st.session_state.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                
                result = conn.execute(text("""
                    SELECT 
                        last_login,
                        created_at,
                        updated_at,
                        is_active
                    FROM admin_users 
                    WHERE username = :username
                """), {"username": username})
                
                user_info = result.fetchone()
                if user_info:
                    return [{
                        'activity': 'เข้าสู่ระบบล่าสุด',
                        'timestamp': user_info.last_login,
                        'details': 'เข้าสู่ระบบผ่านเว็บ'
                    }]
        
        return []
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลกิจกรรม: {str(e)}")
        return []