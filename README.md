# LINE OA Analytics Dashboard

ระบบวิเคราะห์และสรุปการสนทนา LINE Official Account ด้วย AI สำหรับ Admin

![Dashboard Preview](https://via.placeholder.com/800x400/4a5568/ffffff?text=LINE+OA+Analytics+Dashboard)

## 📋 คุณสมบัติหลัก

### 🔍 การวิเคราะห์ขั้นสูง
- **Sentiment Analysis** - วิเคราะห์ความรู้สึกของลูกค้า (บวก/ลบ/เป็นกลาง)
- **Topic Classification** - จำแนกหัวข้อการสนทนาอัตโนมัติ
- **Response Time Analysis** - วิเคราะห์เวลาตอบกลับ
- **Customer Satisfaction** - วัดความพึงพอใจของลูกค้า

### 🤖 AI-Powered Features
- **Embedding Search** - ค้นหาการสนทนาที่คล้ายกันด้วย Vector Similarity
- **Smart Chatbot** - ตอบคำถาม Admin และช่วยวิเคราะห์ข้อมูล
- **Auto Response Suggestions** - แนะนำคำตอบสำหรับเจ้าหน้าที่
- **Conversation Insights** - สร้าง Insights อัตโนมัติ

### 📊 Dashboard & Visualization
- **Real-time Analytics** - สถิติแบบเรียลไทม์
- **Interactive Charts** - กราฟแบบโต้ตอบได้
- **Export Data** - ส่งออกข้อมูลเป็น CSV, Excel
- **Mobile Responsive** - ใช้งานได้บนมือถือ

### 🔐 ระบบรักษาความปลอดภัย
- **Role-based Access** - จัดการสิทธิ์ตาม Role (Admin/Manager/Agent)
- **Session Management** - จัดการ Session อัตโนมัติ
- **Rate Limiting** - ป้องกัน Brute Force Attack

## 🛠️ เทคโนโลยีที่ใช้

### Backend
- **Database**: TiDB (MySQL-compatible)
- **AI Models**: 
  - Embedding: `nomic-embed-text:latest`
  - Chat: `Qwen3:14b`
- **Framework**: Streamlit + SQLAlchemy

### Frontend
- **UI Framework**: Streamlit
- **Charts**: Plotly
- **Styling**: Custom CSS (Gray Theme)

## 🚀 การติดตั้งและรัน

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd line-oa-analytics
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Environment (ไม่จำเป็นต้องสร้าง .env)
ข้อมูลการเชื่อมต่อได้ระบุไว้ใน `utils/config.py` แล้ว:

```python
# Database
TIDB_URL = "mysql+pymysql://2wGpw4Qa2maXMEz.root:FMDCS56nmOL9KSWg@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/ntdatabase?ssl_verify_cert=false"

# AI APIs
EMBEDDING_API_URL = "http://209.15.123.47:11434/api/embeddings"
CHAT_API_URL = "http://209.15.123.47:11434/api/generate"
```

### 4. รันแอปพลิเคชัน
```bash
streamlit run main.py
```

### 5. เข้าถึงระบบ
เปิดเบราว์เซอร์ไปที่: `http://localhost:8501`

**ข้อมูลเข้าสู่ระบบเริ่มต้น:**
- Username: `admin`
- Password: `admin123`

## 📁 โครงสร้างไฟล์

```
line-oa-analytics/
├── main.py                 # ไฟล์หลักของแอปพลิเคชัน
├── requirements.txt        # Python dependencies
├── README.md              # คู่มือนี้
├── components/
│   ├── database.py        # จัดการฐานข้อมูล TiDB
│   ├── chat_analysis.py   # วิเคราะห์การสนทนา + AI
│   └── chatbot.py         # AI Chatbot สำหรับ Admin
└── utils/
    ├── config.py          # การตั้งค่าและ constants
    └── auth.py            # ระบบยืนยันตัวตน
```

## 🗄️ โครงสร้างฐานข้อมูล

### ตารางหลัก

#### `conversations`
เก็บข้อมูลการสนทนาทั้งหมด
```sql
- id (BIGINT, PK, AUTO_INCREMENT)
- conversation_id (VARCHAR(100)) - ID การสนทนา
- user_id (VARCHAR(100)) - ID ผู้ใช้
- message (TEXT) - เนื้อหาข้อความ
- message_type (ENUM) - ประเภทข้อความ (text/image/etc.)
- sender_type (ENUM) - ผู้ส่ง (customer/admin/system)
- timestamp (TIMESTAMP) - เวลาส่งข้อความ
- response_time (INT) - เวลาตอบกลับ (วินาที)
- sentiment (ENUM) - ความรู้สึก (positive/negative/neutral)
- sentiment_score (DECIMAL) - คะแนนความรู้สึก (-1 ถึง 1)
- embedding_vector (JSON) - Vector สำหรับ similarity search
- processed_at (TIMESTAMP) - เวลาที่ประมวลผล AI
- metadata (JSON) - ข้อมูลเพิ่มเติม
```

#### `conversation_summary`
สรุปการสนทนาแต่ละเรื่อง
```sql
- id (BIGINT, PK)
- conversation_id (VARCHAR(100), UNIQUE)
- user_id (VARCHAR(100))
- start_time, end_time (TIMESTAMP)
- total_messages, customer_messages, admin_messages (INT)
- avg_response_time (DECIMAL)
- satisfaction_score (DECIMAL) - คะแนนความพึงพอใจ 1-5
- summary (TEXT) - สรุปด้วย AI
- tags (JSON) - แท็กหัวข้อ
- status (ENUM) - สถานะ (active/closed/escalated)
```

#### `topics`
หัวข้อที่พบจากการวิเคราะห์
```sql
- id (BIGINT, PK)
- topic_name (VARCHAR(200))
- topic_keywords (JSON) - คำสำคัญ
- frequency (INT) - ความถี่ที่พบ
- embedding_vector (JSON)
```

#### `settings`
การตั้งค่าระบบ
```sql
- setting_key (VARCHAR(100), UNIQUE)
- setting_value (TEXT)
- setting_type (ENUM) - string/number/boolean/json
- description (TEXT)
```

#### `admin_users`
ผู้ใช้ที่มีสิทธิ์เข้าถึง
```sql
- username (VARCHAR(50), UNIQUE)
- password_hash (VARCHAR(255))
- email, full_name (VARCHAR)
- role (ENUM) - admin/manager/agent
- is_active (BOOLEAN)
- last_login (TIMESTAMP)
```

## 🤖 AI และ Embedding

### เหตุผลที่ใช้ Embedding
1. **ค้นหาความคล้ายคลึง** - หาการสนทนาที่มีปัญหาคล้ายกัน
2. **จัดกลุ่มหัวข้อ** - จำแนกประเภทการสนทนาอัตโนมัติ
3. **แนะนำคำตอบ** - ช่วยเจ้าหน้าที่ตอบได้เร็วขึ้น
4. **วิเคราะห์แนวโน้ม** - หาปัญหาที่เกิดซ้ำและแนวโน้ม

### การทำงานของ AI Chatbot
- ตอบคำถามเกี่ยวกับสถิติการสนทนา
- วิเคราะห์และสรุปข้อมูล
- ให้คำแนะนำการปรับปรุงบริการ
- แนะนำคำตอบสำหรับเจ้าหน้าที่ (อนาคต)

## ⚙️ การตั้งค่า

### หน้า Settings
- **LINE Configuration**
  - Channel Access Token
  - Channel Secret  
  - Webhook URL

- **AI Configuration**
  - เปิด/ปิด Embedding
  - เปิด/ปิดการตอบกลับอัตโนมัติ
  - ตั้งค่าความมั่นใจในการตอบอัตโนมัติ

## 📊 การใช้งานหลัก

### 1. Dashboard
- ดูสถิติการสนทนาแบบ Overview
- กราฟการสนทนารายวัน
- การกระจายประเภทข้อความ
- การสนทนาล่าสุด

### 2. Chat Analysis
- **Sentiment Analysis** - วิเคราะห์ความรู้สึกลูกค้า
- **Topic Analysis** - หัวข้อที่พบบ่อย
- **Response Time** - เวลาตอบกลับรายชั่วโมง
- **Satisfaction** - คะแนนความพึงพอใจ

### 3. Conversation Logs
- ดูประวัติการสนทนา
- กรองตามลูกค้า/วันที่
- ค้นหาการสนทนา

### 4. AI Chatbot
- ถามคำถามเกี่ยวกับข้อมูล
- ขอสรุปและวิเคราะห์
- ขอคำแนะนำการปรับปรุง

## 🚀 การ Deploy บน Streamlit Cloud

### 1. Push code ไปยัง GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. เข้า [share.streamlit.io](https://share.streamlit.io/)

### 3. เชื่อมต่อ GitHub repository

### 4. ตั้งค่า:
- **Main file path**: `main.py`
- **Python version**: 3.9+

### 5. Deploy!
แอปจะ deploy อัตโนมัติและได้ URL สำหรับเข้าถึง

## 🔧 การปรับแต่ง

### เปลี่ยนธีมสี
แก้ไขใน `utils/config.py`:
```python
COLORS = {
    'primary': '#4a5568',    # สีหลัก
    'secondary': '#718096',  # สีรอง
    # ... เปลี่ยนตามต้องการ
}
```

### เพิ่ม AI Model ใหม่
แก้ไขใน `utils/config.py`:
```python
CHAT_MODEL = "your-new-model:latest"
EMBEDDING_MODEL = "your-embedding-model:latest"
```

### ปรับการตั้งค่า Database
แก้ไข `TIDB_URL` ใน `utils/config.py`

## 🐛 การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อฐานข้อมูล
1. ตรวจสอบ `TIDB_URL` ใน config.py
2. ตรวจสอบ Network connectivity
3. ดูข้อผิดพลาดใน Console

### ปัญหา AI ไม่ทำงาน
1. ตรวจสอบ `EMBEDDING_API_URL` และ `CHAT_API_URL`
2. ลองเข้าถึง API โดยตรง
3. ตรวจสอบ Model name

### ปัญหาการ Login
1. ใช้ admin/admin123 สำหรับครั้งแรก
2. ตรวจสอบตาราง `admin_users` ในฐานข้อมูล
3. ล้าง session state ใน browser

## 📞 การสนับสนุน

หากมีปัญหาหรือข้อสงสัย:

1. ตรวจสอบ [Issues](https://github.com/your-repo/issues)
2. สร้าง Issue ใหม่พร้อมรายละเอียด
3. ติดต่อผู้พัฒนา

## 📝 License

MIT License - ใช้งานได้อย่างอิสระ

---

**พัฒนาด้วย ❤️ สำหรับการวิเคราะห์การสนทนา LINE OA**

## 🔄 การอัปเดตและบำรุงรักษา

### การอัปเดต Code
```bash
git pull origin main
pip install -r requirements.txt --upgrade
streamlit run main.py
```

### การสำรองข้อมูล
แนะนำให้สำรองฐานข้อมูลเป็นประจำ:
```sql
-- Export สำคัญ tables
SELECT * FROM conversations INTO OUTFILE 'backup_conversations.csv';
SELECT * FROM conversation_summary INTO OUTFILE 'backup_summary.csv';
```

### การตรวจสอบประสิทธิภาพ
- ตรวจสอบขนาดฐานข้อมูล
- ล้างข้อมูล cache ที่หมดอายุ
- ตรวจสอบ AI API response time

## 🌟 Roadmap และ Features ที่กำลังพัฒนา

### Phase 1 (ปัจจุบัน)
- ✅ Basic Analytics Dashboard
- ✅ Sentiment Analysis
- ✅ Topic Classification
- ✅ AI Chatbot for Admin
- ✅ User Authentication

### Phase 2 (กำลังพัฒนา)
- 🔄 Auto Response สำหรับลูกค้า
- 🔄 Advanced Charts และ Visualization
- 🔄 Email Notifications
- 🔄 Mobile App
- 🔄 API สำหรับ Integration

### Phase 3 (อนาคต)
- 📋 Machine Learning Models
- 📋 Predictive Analytics
- 📋 Multi-language Support
- 📋 Advanced Security Features
- 📋 Real-time Dashboard

## 🎯 Use Cases

### สำหรับ Business Owner
- ติดตามความพึงพอใจของลูกค้า
- เข้าใจปัญหาและความต้องการลูกค้า
- วัดประสิทธิภาพทีมบริการลูกค้า
- ตัดสินใจเชิงกลยุทธ์จากข้อมูล

### สำหรับ Customer Service Manager
- จัดการและมอบหมายงานทีม
- ติดตามเวลาตอบกลับ
- ระบุจุดที่ต้องปรับปรุง
- สร้างรายงานประจำเดือน

### สำหรับ Customer Service Agent
- ดูประวัติการสนทนาลูกค้า
- ได้รับคำแนะนำการตอบ
- ติดตามปัญหาที่ยังไม่แก้ไข
- เรียนรู้จากการสนทนาที่ผ่านมา

## 📈 KPI และ Metrics ที่วัดได้

### Customer Satisfaction Metrics
- Net Promoter Score (NPS)
- Customer Satisfaction Score (CSAT)
- Sentiment Distribution
- Resolution Rate

### Operational Metrics
- Average Response Time
- First Contact Resolution
- Message Volume
- Agent Productivity

### Business Metrics
- Customer Retention
- Issue Categories
- Peak Hours Analysis
- Conversion Rate

## 🔒 ความปลอดภัยและการปกป้องข้อมูล

### Data Security
- การเข้ารหัสข้อมูลในฐานข้อมูล
- SSL/TLS สำหรับการส่งข้อมูล
- Role-based Access Control
- Session Management

### Privacy Protection
- ไม่เก็บข้อมูลส่วนบุคคลที่ไม่จำเป็น
- มีระบบลบข้อมูลเก่าอัตโนมัติ
- ปฏิบัติตาม PDPA
- การ Anonymize ข้อมูลสำหรับการวิเคราะห์

### Compliance
- PDPA (Personal Data Protection Act)
- SOC 2 Type II principles
- ISO 27001 guidelines
- GDPR considerations (สำหรับลูกค้าสากล)

## 💡 Tips และ Best Practices

### สำหรับ Admin
1. **ตรวจสอบข้อมูลเป็นประจำ** - ดู Dashboard ทุกวันเพื่อติดตามแนวโน้ม
2. **ใช้ AI Chatbot** - ถามคำถามเพื่อได้ insights เชิงลึก
3. **ตั้งค่า Alert** - กำหนด threshold สำหรับปัญหาที่ต้องจับตา
4. **สำรองข้อมูล** - Export ข้อมูลสำคัญเป็นประจำ

### สำหรับ Developer
1. **ใช้ Environment Variables** - สำหรับ Production deployment
2. **Monitor Performance** - ติดตาม API response time และ database performance
3. **Update Dependencies** - อัปเดต packages เป็นประจำ
4. **Test Thoroughly** - ทดสอบทุก feature ก่อน deploy

### สำหรับ Data Analysis
1. **Clean Data Regularly** - ล้างข้อมูลที่ไม่ถูกต้องหรือซ้ำซ้อน
2. **Validate Results** - ตรวจสอบผลการวิเคราะห์ด้วยตา
3. **Cross-reference** - เปรียบเทียบกับข้อมูลจากแหล่งอื่น
4. **Document Insights** - บันทึก insights ที่ได้เพื่อการติดตามผล

---

## 🙋‍♂️ คำถามที่พบบ่อย (FAQ)

### Q: ทำไมต้องใช้ Embedding?
A: Embedding ช่วยให้ระบบเข้าใจความหมายของข้อความได้ดีกว่าการจับคู่คำแบบธรรมดา สามารถหาการสนทนาที่คล้ายกัน แม้ใช้คำต่างกันก็ตาม

### Q: AI Chatbot ตอบคำถามได้แม่นยำแค่ไหน?
A: ขึ้นอยู่กับคุณภาพและปริมาณข้อมูล ยิ่งมีข้อมูลการสนทนามาก ยิ่งตอบได้แม่นยำขึ้น

### Q: สามารถใช้กับ LINE Official Account อื่นได้ไหม?
A: ได้ แค่เปลี่ยน LINE Token ในหน้า Settings

### Q: ข้อมูลจะปลอดภัยไหม?
A: ข้อมูลเก็บใน TiDB ที่มีการเข้ารหัส และระบบมี Role-based Access Control

### Q: สามารถ Export ข้อมูลได้ไหม?
A: ได้ สามารถ Export เป็น CSV, Excel หรือ JSON

### Q: จะเพิ่ม Feature ใหม่ได้อย่างไร?
A: สามารถแก้ไข Code ได้ตาม Open Source License หรือติดต่อทีมพัฒนา

---

**🚀 เริ่มต้นใช้งาน LINE OA Analytics Dashboard วันนี้!**