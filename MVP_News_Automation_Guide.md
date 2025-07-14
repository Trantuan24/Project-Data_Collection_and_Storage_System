# 🚀 HƯỚNG DẪN TRIỂN KHAI MVP HỆ THỐNG TỰ ĐỘNG HÓA TIN TỨC (4 GIỜ)

> **Mục tiêu:** Tạo một hệ thống tự động crawl tin tức từ Google Sheets, tóm tắt bằng AI và gửi kết quả qua WhatsApp/Email trong 4 giờ.

## 📋 TỔNG QUAN MVP

**MVP sẽ bao gồm:**
- ✅ Đọc URLs từ Google Sheets
- ✅ Nhận URLs từ WhatsApp messages (đơn giản)
- ✅ Crawl nội dung tin tức cơ bản
- ✅ Lưu vào MySQL database
- ✅ Tóm tắt bằng OpenAI API
- ✅ Gửi kết quả qua WhatsApp (primary output)

**Timeline:**
- ⏰ Pre-requisites & Setup: 45 phút
- ⏰ MySQL Database Setup: 30 phút
- ⏰ WhatsApp Basic Setup: 60 phút
- ⏰ n8n Workflow Creation: 120 phút
- ⏰ Testing & Debugging: 90 phút
- ⏰ Deployment & Validation: 45 phút
- **Total:** 6.5 giờ (realistic cho MVP)

---

## 🛠️ PHẦN 1: PRE-REQUISITES & SETUP (45 PHÚT)

### ✅ Checklist Chuẩn Bị

**Bước 1.1: Kiểm tra n8n đang chạy (2 phút)**
1. Mở browser và truy cập: `http://localhost:5678`
2. Bạn sẽ thấy n8n interface với menu bên trái
3. Nếu không load được, restart n8n service

**Bước 1.2: Tạo Google Service Account (10 phút)**
1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới hoặc chọn project hiện có
3. Vào **APIs & Services** > **Library**
4. Tìm và enable **Google Sheets API**
5. Vào **APIs & Services** > **Credentials**
6. Click **Create Credentials** > **Service Account**
7. Nhập tên: `n8n-news-automation`
8. Click **Create and Continue**
9. Chọn role: **Editor**
10. Click **Done**
11. Click vào service account vừa tạo
12. Vào tab **Keys** > **Add Key** > **Create New Key**
13. Chọn **JSON** và download file
14. Lưu file với tên: `google-credentials.json`

**Bước 1.3: Tạo Google Sheet (5 phút)**
1. Truy cập: https://sheets.google.com/
2. Tạo sheet mới với tên: `News URLs`
3. Tạo header row:
   - A1: `URL`
   - B1: `Category`
   - C1: `Status`
   - D1: `Added Date`
4. Thêm vài URLs mẫu:
   - A2: `https://vnexpress.net/`
   - A3: `https://tuoitre.vn/`
5. Share sheet với service account email (từ file JSON)
6. Copy Sheet ID từ URL (phần giữa `/d/` và `/edit`)

**Bước 1.4: Setup MySQL Database (15 phút)**
1. **Option A: Local MySQL Installation**
   - Download MySQL Community Server: https://dev.mysql.com/downloads/mysql/
   - Install với default settings
   - Set root password: `news_automation_2024`
   - Start MySQL service

2. **Option B: XAMPP (Recommended cho Windows)**
   - Download XAMPP: https://www.apachefriends.org/
   - Install và start Apache + MySQL
   - Access phpMyAdmin: http://localhost/phpmyadmin

3. **Create Database:**
   ```sql
   CREATE DATABASE news_automation;
   CREATE USER 'n8n_user'@'localhost' IDENTIFIED BY 'n8n_password';
   GRANT ALL PRIVILEGES ON news_automation.* TO 'n8n_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Test Connection:**
   - Host: localhost
   - Port: 3306
   - Database: news_automation
   - Username: n8n_user
   - Password: n8n_password

**Bước 1.5: Đăng ký OpenAI API (8 phút)**
1. Truy cập: https://platform.openai.com/
2. Đăng ký account hoặc login
3. Vào **API Keys** section
4. Click **Create new secret key**
5. Copy và lưu API key (bắt đầu với `sk-`)
6. Kiểm tra credit balance (cần ít nhất $1)

**Bước 1.6: Setup WhatsApp Business API (15 phút)**
> **Lưu ý:** Đây là primary output channel cho MVP

**WhatsApp Business API Setup:**
1. Truy cập: https://developers.facebook.com/
2. Login và tạo **New App** > **Business**
3. Add **WhatsApp** product
4. Get **Temporary Access Token** (24h - đủ cho MVP testing)
5. Get **Phone Number ID** từ WhatsApp settings
6. Test API với curl:
```bash
curl -X POST "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages" \
-H "Authorization: Bearer ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "messaging_product": "whatsapp",
  "to": "YOUR_PHONE_NUMBER",
  "type": "text",
  "text": {"body": "Test message từ n8n"}
}'
```

**Webhook Setup (Optional cho input):**
1. Sử dụng ngrok: `ngrok http 5678`
2. Configure webhook URL trong Meta Console
3. Set verify token: `your_verify_token`

---

## 🗄️ PHẦN 2: MYSQL DATABASE SETUP (30 PHÚT)

### 📊 Database Schema Creation

**Bước 2.1: Create Database Tables (15 phút)**
1. Access MySQL (phpMyAdmin hoặc MySQL Workbench)
2. Select database `news_automation`
3. Execute following SQL:

```sql
-- Articles table để lưu tin tức đã crawl
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    crawled_at DATETIME NOT NULL,
    word_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_url (url),
    INDEX idx_created_at (created_at)
);

-- Daily summaries table
CREATE TABLE daily_summaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    summary_date DATE NOT NULL UNIQUE,
    summary_content TEXT NOT NULL,
    article_count INT DEFAULT 0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_summary_date (summary_date)
);

-- URL tracking table
CREATE TABLE url_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE,
    source VARCHAR(50) DEFAULT 'sheets',
    added_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**Bước 2.2: Test Database Connection trong n8n (15 phút)**
1. Trong n8n, tạo workflow test: `MySQL Connection Test`
2. Thêm **MySQL** node
3. Configure connection:
   - Host: `localhost`
   - Port: `3306`
   - Database: `news_automation`
   - User: `n8n_user`
   - Password: `n8n_password`
4. Test với query: `SELECT 1 as test`
5. Verify connection successful

---

## � PHẦN 2: WHATSAPP BASIC SETUP (60 PHÚT)

### 🔧 WhatsApp Input Webhook (Optional - 30 phút)

**Bước 2.1: Tạo WhatsApp Webhook Workflow (nếu muốn nhận URLs qua WhatsApp)**
1. Tạo workflow mới: `WhatsApp Input Handler`
2. Thêm **Webhook** node:
   - Path: `/webhook/whatsapp`
   - Method: POST
3. Thêm **Function** node để extract URLs:
```javascript
// Extract URLs từ WhatsApp messages
const body = $json.body;
const items = [];

if (body.entry && body.entry[0].changes && body.entry[0].changes[0].value.messages) {
  const messages = body.entry[0].changes[0].value.messages;

  for (const message of messages) {
    const text = message.text?.body || '';
    const from = message.from;

    // Simple URL detection
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const urls = text.match(urlRegex);

    if (urls) {
      for (const url of urls) {
        items.push({
          json: {
            url: url,
            source: 'whatsapp',
            addedBy: from,
            timestamp: new Date().toISOString()
          }
        });
      }
    }
  }
}

return items;
```

**Bước 2.2: WhatsApp Output Setup (30 phút)**
1. Test WhatsApp Business API connection trong n8n
2. Tạo credential cho WhatsApp:
   - Access Token: từ bước 1.5
   - Phone Number ID: từ bước 1.5
3. Test gửi message đơn giản

---

## �🔧 PHẦN 4: N8N WORKFLOW CREATION (120 PHÚT)

### 📊 Workflow 1: URL Collection từ Google Sheets (20 phút)

**Bước 4.1: Tạo Workflow mới**
1. Trong n8n, click **New Workflow**
2. Đặt tên: `News URL Collection`
3. Click **Save**

**Bước 4.2: Thêm Google Sheets Node**
1. Click dấu **+** để thêm node
2. Tìm và chọn **Google Sheets**
3. Click **Add Google Sheets node**
4. Trong node settings:
   - **Credential**: Click **Create New**
   - **Credential Type**: Service Account
   - Upload file `google-credentials.json`
   - Click **Save**
   - **Resource**: Sheet
   - **Operation**: Read
   - **Document ID**: Paste Sheet ID từ bước 1.3
   - **Sheet Name**: Sheet1
   - **Range**: A:D

**Bước 2.3: Test Google Sheets Connection**
1. Click **Test step** trên Google Sheets node
2. Bạn sẽ thấy data từ sheet hiển thị
3. Nếu lỗi, kiểm tra lại Sheet ID và permissions

**Bước 2.4: Thêm Function Node để xử lý data**
1. Thêm **Function** node sau Google Sheets
2. Paste code sau:

```javascript
// Xử lý data từ Google Sheets
const items = [];

for (const item of $input.all()) {
  const url = item.json.URL;
  const category = item.json.Category || 'General';
  const status = item.json.Status || 'New';
  
  // Chỉ xử lý URLs mới
  if (status === 'New' && url && url.startsWith('http')) {
    items.push({
      json: {
        url: url,
        category: category,
        addedDate: new Date().toISOString(),
        status: 'Processing'
      }
    });
  }
}

return items;
```

**Bước 2.5: Test Function Node**
1. Click **Test step** trên Function node
2. Verify output chỉ chứa URLs hợp lệ

### 🕷️ Workflow 2: Web Crawling (25 phút)

**Bước 2.6: Thêm HTTP Request Node**
1. Thêm **HTTP Request** node
2. Settings:
   - **Method**: GET
   - **URL**: `{{ $json.url }}`
   - **Response Format**: String
   - **Timeout**: 10000

**Bước 2.7: Thêm HTML Extract Node**
1. Thêm **HTML Extract** node
2. Settings:
   - **Source Data**: HTML
   - **Extraction Values**:
     - **Key**: title
     - **CSS Selector**: title, h1
     - **Return Value**: Text
   - Thêm extraction value thứ 2:
     - **Key**: content  
     - **CSS Selector**: p
     - **Return Value**: Text
     - **Return Array**: Yes

**Bước 2.8: Thêm Function Node để clean data**
```javascript
// Clean và format crawled data
const items = [];

for (const item of $input.all()) {
  const title = item.json.title || 'No title';
  const contentArray = item.json.content || [];
  
  // Lấy 3 paragraphs đầu tiên
  const content = contentArray
    .slice(0, 3)
    .join(' ')
    .substring(0, 500) + '...';
  
  items.push({
    json: {
      url: item.json.url,
      title: title,
      content: content,
      crawledAt: new Date().toISOString(),
      wordCount: content.split(' ').length
    }
  });
}

return items;
```

### 💾 Workflow 3: Database Storage (20 phút)

**Bước 3.9: Thêm MySQL Node**
1. Thêm **MySQL** node
2. Settings:
   - **Credential**: Use credential từ bước 2.2
   - **Operation**: Execute Query
   - **Query**:
```sql
INSERT INTO articles (url, title, content, crawled_at, word_count)
VALUES (?, ?, ?, ?, ?)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  content = VALUES(content),
  crawled_at = VALUES(crawled_at),
  word_count = VALUES(word_count);
```

**Bước 3.10: Thêm Function Node để prepare SQL parameters**
```javascript
// Prepare data cho MySQL insertion
const items = [];

for (const item of $input.all()) {
  items.push({
    json: {
      query: `INSERT INTO articles (url, title, content, crawled_at, word_count)
              VALUES (?, ?, ?, ?, ?)
              ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                content = VALUES(content),
                crawled_at = VALUES(crawled_at),
                word_count = VALUES(word_count)`,
      parameters: [
        item.json.url,
        item.json.title,
        item.json.content,
        item.json.crawledAt,
        item.json.wordCount
      ]
    }
  });
}

return items;
```

### 🤖 Workflow 4: AI Summarization (25 phút)

**Bước 2.11: Thêm OpenAI Node**
1. Thêm **OpenAI** node
2. Settings:
   - **Credential**: Create new với API key từ bước 1.4
   - **Resource**: Text
   - **Operation**: Complete
   - **Model**: gpt-3.5-turbo
   - **Prompt**:
```
Tóm tắt các tin tức sau đây bằng tiếng Việt, ngắn gọn và dễ hiểu:

{% for item in $input.all() %}
Tiêu đề: {{ item.json.title }}
Nội dung: {{ item.json.content }}
---
{% endfor %}

Hãy tạo một bản tóm tắt 3-5 câu về những tin tức quan trọng nhất.
```

**Bước 2.12: Thêm Function Node để format summary**
```javascript
// Format AI summary cho output
const summary = $input.first().json.choices[0].message.content;

return [{
  json: {
    summary: summary,
    generatedAt: new Date().toISOString(),
    articleCount: $input.all().length,
    date: new Date().toLocaleDateString('vi-VN')
  }
}];
```

---

## � PHẦN 5: WHATSAPP OUTPUT CONFIGURATION (20 PHÚT)

### 📮 Setup WhatsApp Message Node (20 phút)

**Bước 5.1: Thêm WhatsApp Business Node**
1. Thêm **WhatsApp Business** node
2. Settings:
   - **Credential**: Use credential từ bước 2.2
   - **Resource**: Message
   - **Operation**: Send Text

**Bước 5.2: Configure WhatsApp Message Content**
```javascript
// WhatsApp message settings
{
  "messaging_product": "whatsapp",
  "to": "YOUR_PHONE_NUMBER", // Replace với số điện thoại nhận
  "type": "text",
  "text": {
    "body": `📰 *TÓM TẮT TIN TỨC NGÀY {{ $json.date }}*

{{ $json.summary }}

---
📊 Tổng số bài viết: {{ $json.articleCount }}
⏰ Thời gian tạo: {{ $json.generatedAt }}

🤖 _Hệ thống tự động hóa tin tức_`
  }
}
```

**Bước 5.3: Test WhatsApp Delivery**
1. Click **Test step** để gửi thử message
2. Kiểm tra WhatsApp nhận được message
3. Verify format hiển thị đúng

---

## 🔄 PHẦN 6: WORKFLOW AUTOMATION & SCHEDULING

### ⏰ Thêm Schedule Trigger (10 phút)

**Bước 4.1: Thêm Cron Node**
1. Ở đầu workflow, thêm **Schedule Trigger** node
2. Settings:
   - **Trigger Times**: Custom
   - **Cron Expression**: `0 8 * * *` (8:00 AM hàng ngày)
   - **Timezone**: Asia/Ho_Chi_Minh

**Bước 5.2: Connect tất cả nodes**
1. Kết nối các nodes theo thứ tự:
   - Schedule Trigger → Google Sheets
   - Google Sheets → Function (Process URLs)
   - Function → HTTP Request
   - HTTP Request → HTML Extract
   - HTML Extract → Function (Clean Data)
   - Function → MySQL
   - MySQL → OpenAI
   - OpenAI → Function (Format Summary)
   - Function → WhatsApp Business (Send Message)

**Bước 4.3: Save Workflow**
1. Click **Save**
2. Click **Activate** để enable workflow

---

## 🧪 PHẦN 7: TESTING & DEBUGGING (90 PHÚT)

### 🔍 Test Individual Nodes (30 phút)

**Bước 5.1: Test Google Sheets Connection**
1. Click vào Google Sheets node
2. Click **Test step**
3. **Expected Output**: Danh sách URLs từ sheet
4. **Troubleshooting**:
   - Nếu lỗi 403: Kiểm tra sheet permissions
   - Nếu lỗi 404: Kiểm tra Sheet ID
   - Nếu empty: Kiểm tra range A:D

**Bước 5.2: Test Web Crawling**
1. Click vào HTTP Request node
2. Click **Test step**
3. **Expected Output**: HTML content của website
4. **Troubleshooting**:
   - Timeout: Tăng timeout lên 15000ms
   - 403/404: Website có thể block crawling
   - SSL errors: Thêm option `"rejectUnauthorized": false`

**Bước 5.3: Test HTML Extraction**
1. Click vào HTML Extract node
2. Click **Test step**
3. **Expected Output**: Title và content array
4. **Troubleshooting**:
   - Empty title: Thử selector `h1, .title, [class*="title"]`
   - No content: Thử selector `.content, .article, main p`

**Bước 6.4: Test Database Storage**
1. Click vào MySQL node
2. Click **Test step**
3. **Expected Output**: Success message
4. **Troubleshooting**:
   - Connection error: Kiểm tra MySQL service running
   - Authentication error: Verify username/password
   - SQL syntax: Kiểm tra MySQL query format

**Bước 6.5: Test AI Summarization**
1. Click vào OpenAI node
2. Click **Test step**
3. **Expected Output**: Vietnamese summary text
4. **Troubleshooting**:
   - API key error: Kiểm tra key format
   - Rate limit: Đợi 1 phút và thử lại
   - No credits: Top up OpenAI account

**Bước 6.6: Test WhatsApp Delivery**
1. Click vào WhatsApp Business node
2. Click **Test step**
3. **Expected Output**: Success message
4. **Troubleshooting**:
   - Token error: Kiểm tra Access Token
   - Phone number error: Verify Phone Number ID
   - Message not received: Check phone number format

### 🔧 End-to-End Testing (45 phút)

**Bước 6.7: Manual Execution Test**
1. Click **Execute Workflow** button
2. Monitor execution trong **Executions** tab
3. Kiểm tra từng step có success không
4. Verify WhatsApp message được nhận thành công
5. Check message format và content

**Bước 5.7: Debug Common Issues**

**Issue 1: Workflow stops at HTTP Request**
```javascript
// Solution: Add error handling
try {
  // HTTP request code
} catch (error) {
  return [{
    json: {
      error: error.message,
      url: $json.url,
      status: 'failed'
    }
  }];
}
```

**Issue 2: Empty AI Summary**
- Check OpenAI credits
- Verify prompt format
- Test with simpler prompt

**Issue 3: Email not sending**
- Verify Gmail App Password
- Check spam folder
- Test with different email provider

**Issue 4: Database errors**
- Check file permissions
- Verify SQL syntax
- Test with simple INSERT query

---

## 🚀 PHẦN 8: DEPLOYMENT & VALIDATION (45 PHÚT)

### ✅ Production Checklist (25 phút)

**Bước 7.1: Verify All Connections**
1. Google Sheets: ✅ Reading URLs successfully
2. WhatsApp Input: ✅ Receiving URLs (if enabled)
3. Web Crawling: ✅ Extracting content
4. MySQL Database: ✅ Storing articles
5. AI: ✅ Generating summaries
6. WhatsApp Output: ✅ Sending notifications

**Bước 7.2: Set Production Schedule**
1. Adjust cron expression nếu cần:
   - `0 8,18 * * *` (8 AM và 6 PM)
   - `0 */6 * * *` (Mỗi 6 giờ)
2. Click **Save** và **Activate**

**Bước 7.3: Monitor First Runs**
1. Vào **Executions** tab
2. Watch for successful executions
3. Check WhatsApp messages for summaries
4. Verify message format và content

### 📊 Success Validation (20 phút)

**MVP Success Criteria:**
- ✅ Workflow chạy không lỗi
- ✅ Crawl được ít nhất 1 article
- ✅ AI tạo được summary tiếng Việt
- ✅ WhatsApp message được gửi thành công
- ✅ Database lưu trữ data
- ✅ WhatsApp input working (if enabled)

**Performance Metrics:**
- Execution time: < 5 phút
- Success rate: > 80%
- WhatsApp delivery: 100%
- Message format: Professional và readable

---

## 🎯 PHẦN 7: NEXT STEPS & SCALING (10 PHÚT)

### 🔄 Immediate Improvements

**Week 1 Enhancements:**
1. **WhatsApp Integration**: Setup WhatsApp Business API
2. **Better Crawling**: Add Puppeteer cho dynamic content
3. **Error Handling**: Comprehensive retry logic
4. **Monitoring**: Add Slack notifications

**Week 2-4 Scaling:**
1. **Multiple Sources**: Support nhiều news websites
2. **Categories**: Phân loại tin tức tự động
3. **User Management**: Multiple recipients
4. **Analytics**: Track engagement metrics

### 🛠️ Technical Debt

**Priority Fixes:**
1. Optimize MySQL performance với indexing
2. Add proper logging system
3. Implement rate limiting
4. Add data validation

**Security Improvements:**
1. Encrypt API keys
2. Add authentication
3. Implement access controls
4. Regular security audits

---

## 🆘 TROUBLESHOOTING GUIDE

### Top 6 Common Issues

**1. "MySQL connection failed"**
```
Solution:
- Verify MySQL service is running
- Check connection credentials (host, port, username, password)
- Test connection outside n8n first
- Ensure database 'news_automation' exists
- Check firewall settings
```

**2. "Google Sheets permission denied"**
```
Solution:
- Kiểm tra service account email đã được share sheet
- Verify Google Sheets API enabled
- Re-download credentials JSON
```

**3. "OpenAI API rate limit exceeded"**
```
Solution:
- Đợi 1 phút và retry
- Upgrade OpenAI plan
- Add delay giữa requests
```

**4. "HTTP Request timeout"**
```
Solution:
- Tăng timeout lên 15000ms
- Add retry logic
- Check website accessibility
```

**5. "MySQL query syntax error"**
```
Solution:
- Check MySQL syntax (different from SQLite)
- Verify table exists
- Check column names match schema
- Use MySQL-specific functions
```

**6. "Workflow execution failed"**
```
Solution:
- Check Executions tab for error details
- Test individual nodes
- Verify all credentials
- Check n8n logs
```

### Debug Commands

**Check n8n logs:**
```bash
# Windows
Get-Content "C:\Users\[username]\.n8n\logs\n8n.log" -Tail 50
```

**Test MySQL database connection:**
```sql
-- Test connection
SELECT 1 as connection_test;

-- Check tables exist
SHOW TABLES;

-- Check recent articles
SELECT * FROM articles ORDER BY created_at DESC LIMIT 5;

-- Check database size
SELECT
    table_name,
    table_rows,
    data_length,
    index_length
FROM information_schema.tables
WHERE table_schema = 'news_automation';
```

**Verify workflow status:**
1. Vào n8n UI
2. Check **Workflows** tab
3. Verify **Active** status
4. Review **Executions** history

---

## 🎉 CONGRATULATIONS!

Bạn đã hoàn thành MVP hệ thống tự động hóa tin tức với WhatsApp integration!

**What you've built:**
- ✅ Automated news collection từ Google Sheets
- ✅ WhatsApp input cho URLs (optional)
- ✅ Web crawling và content extraction
- ✅ AI-powered summarization
- ✅ WhatsApp notifications (primary output)
- ✅ MySQL database storage
- ✅ Scheduled execution

**Next milestone:** Scale up với advanced features, monitoring và production optimization!

---

*📝 Lưu file này để reference và continue development journey của bạn!*

