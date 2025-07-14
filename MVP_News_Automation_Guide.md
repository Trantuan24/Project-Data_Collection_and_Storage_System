# 🚀 HƯỚNG DẪN TRIỂN KHAI MVP HỆ THỐNG TỰ ĐỘNG HÓA TIN TỨC (4 GIỜ)

> **Mục tiêu:** Tạo một hệ thống tự động crawl tin tức từ Google Sheets, tóm tắt bằng AI và gửi kết quả qua WhatsApp/Email trong 4 giờ.

## 📋 TỔNG QUAN MVP

**MVP sẽ bao gồm:**
- ✅ Đọc URLs từ Google Sheets
- ✅ Crawl nội dung tin tức cơ bản
- ✅ Lưu vào SQLite database
- ✅ Tóm tắt bằng OpenAI API
- ✅ Gửi kết quả qua WhatsApp hoặc Email

**Timeline:**
- ⏰ Pre-requisites & Setup: 30 phút
- ⏰ n8n Workflow Creation: 90 phút  
- ⏰ Testing & Debugging: 60 phút
- ⏰ Deployment & Validation: 30 phút
- ⏰ Next Steps: 10 phút

---

## 🛠️ PHẦN 1: PRE-REQUISITES & SETUP (30 PHÚT)

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

**Bước 1.4: Đăng ký OpenAI API (8 phút)**
1. Truy cập: https://platform.openai.com/
2. Đăng ký account hoặc login
3. Vào **API Keys** section
4. Click **Create new secret key**
5. Copy và lưu API key (bắt đầu với `sk-`)
6. Kiểm tra credit balance (cần ít nhất $1)

**Bước 1.5: Setup WhatsApp (Optional - 5 phút)**
> **Lưu ý:** Nếu phức tạp, sẽ dùng Email backup

**Option A: WhatsApp Business API (Phức tạp)**
- Cần Meta Developer Account
- Verification process mất thời gian
- **Recommendation:** Skip cho MVP, dùng Email

**Option B: Email Backup (Đơn giản)**
1. Sử dụng Gmail SMTP
2. Tạo App Password cho Gmail:
   - Vào Google Account Settings
   - Security > 2-Step Verification
   - App passwords > Generate password
   - Lưu password này

---

## 🔧 PHẦN 2: N8N WORKFLOW CREATION (90 PHÚT)

### 📊 Workflow 1: URL Collection từ Google Sheets (20 phút)

**Bước 2.1: Tạo Workflow mới**
1. Trong n8n, click **New Workflow**
2. Đặt tên: `News URL Collection`
3. Click **Save**

**Bước 2.2: Thêm Google Sheets Node**
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

**Bước 2.9: Thêm SQLite Node**
1. Thêm **SQLite** node
2. Settings:
   - **Database**: `./news_database.db`
   - **Operation**: Execute Query
   - **Query**:
```sql
CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE,
  title TEXT,
  content TEXT,
  crawled_at TEXT,
  word_count INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO articles (url, title, content, crawled_at, word_count)
VALUES (?, ?, ?, ?, ?);
```

**Bước 2.10: Thêm Function Node để prepare SQL parameters**
```javascript
// Prepare data cho SQLite insertion
const items = [];

for (const item of $input.all()) {
  items.push({
    json: {
      query: `INSERT OR REPLACE INTO articles (url, title, content, crawled_at, word_count) 
              VALUES (?, ?, ?, ?, ?)`,
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

## 📧 PHẦN 3: OUTPUT CONFIGURATION (Email Backup)

### 📮 Setup Email Node (15 phút)

**Bước 3.1: Thêm Email Node**
1. Thêm **Send Email** node
2. Settings:
   - **Credential**: Create new
   - **SMTP Host**: smtp.gmail.com
   - **SMTP Port**: 587
   - **Secure**: Yes
   - **Username**: your-email@gmail.com
   - **Password**: App password từ bước 1.5

**Bước 3.2: Configure Email Content**
```javascript
// Email settings
{
  "to": "recipient@gmail.com",
  "subject": "📰 Tóm tắt tin tức ngày {{ $json.date }}",
  "text": `
Xin chào!

Đây là bản tóm tắt tin tức tự động cho ngày {{ $json.date }}:

{{ $json.summary }}

---
Tổng số bài viết đã xử lý: {{ $json.articleCount }}
Thời gian tạo: {{ $json.generatedAt }}

Hệ thống tự động hóa tin tức
  `,
  "options": {
    "priority": "normal"
  }
}
```

---

## 🔄 PHẦN 4: WORKFLOW AUTOMATION & SCHEDULING

### ⏰ Thêm Schedule Trigger (10 phút)

**Bước 4.1: Thêm Cron Node**
1. Ở đầu workflow, thêm **Schedule Trigger** node
2. Settings:
   - **Trigger Times**: Custom
   - **Cron Expression**: `0 8 * * *` (8:00 AM hàng ngày)
   - **Timezone**: Asia/Ho_Chi_Minh

**Bước 4.2: Connect tất cả nodes**
1. Kết nối các nodes theo thứ tự:
   - Schedule Trigger → Google Sheets
   - Google Sheets → Function (Process URLs)
   - Function → HTTP Request
   - HTTP Request → HTML Extract
   - HTML Extract → Function (Clean Data)
   - Function → SQLite
   - SQLite → OpenAI
   - OpenAI → Function (Format Summary)
   - Function → Send Email

**Bước 4.3: Save Workflow**
1. Click **Save**
2. Click **Activate** để enable workflow

---

## 🧪 PHẦN 5: TESTING & DEBUGGING (60 PHÚT)

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

**Bước 5.4: Test Database Storage**
1. Click vào SQLite node
2. Click **Test step**
3. **Expected Output**: Success message
4. **Troubleshooting**:
   - Permission error: Kiểm tra write permissions
   - SQL syntax: Kiểm tra query format

**Bước 5.5: Test AI Summarization**
1. Click vào OpenAI node
2. Click **Test step**
3. **Expected Output**: Vietnamese summary text
4. **Troubleshooting**:
   - API key error: Kiểm tra key format
   - Rate limit: Đợi 1 phút và thử lại
   - No credits: Top up OpenAI account

### 🔧 End-to-End Testing (30 phút)

**Bước 5.6: Manual Execution Test**
1. Click **Execute Workflow** button
2. Monitor execution trong **Executions** tab
3. Kiểm tra từng step có success không
4. Verify email được gửi thành công

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

## 🚀 PHẦN 6: DEPLOYMENT & VALIDATION (30 PHÚT)

### ✅ Production Checklist (15 phút)

**Bước 6.1: Verify All Connections**
1. Google Sheets: ✅ Reading URLs successfully
2. Web Crawling: ✅ Extracting content
3. Database: ✅ Storing articles
4. AI: ✅ Generating summaries
5. Email: ✅ Sending notifications

**Bước 6.2: Set Production Schedule**
1. Adjust cron expression nếu cần:
   - `0 8,18 * * *` (8 AM và 6 PM)
   - `0 */6 * * *` (Mỗi 6 giờ)
2. Click **Save** và **Activate**

**Bước 6.3: Monitor First Runs**
1. Vào **Executions** tab
2. Watch for successful executions
3. Check email inbox for summaries

### 📊 Success Validation (15 phút)

**MVP Success Criteria:**
- ✅ Workflow chạy không lỗi
- ✅ Crawl được ít nhất 1 article
- ✅ AI tạo được summary tiếng Việt
- ✅ Email được gửi thành công
- ✅ Database lưu trữ data

**Performance Metrics:**
- Execution time: < 5 phút
- Success rate: > 80%
- Email delivery: 100%

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
1. Replace SQLite với PostgreSQL
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

### Top 5 Common Issues

**1. "Google Sheets permission denied"**
```
Solution:
- Kiểm tra service account email đã được share sheet
- Verify Google Sheets API enabled
- Re-download credentials JSON
```

**2. "OpenAI API rate limit exceeded"**
```
Solution:
- Đợi 1 phút và retry
- Upgrade OpenAI plan
- Add delay giữa requests
```

**3. "HTTP Request timeout"**
```
Solution:
- Tăng timeout lên 15000ms
- Add retry logic
- Check website accessibility
```

**4. "Email authentication failed"**
```
Solution:
- Verify Gmail App Password
- Enable 2-factor authentication
- Try different SMTP provider
```

**5. "Workflow execution failed"**
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

**Test database connection:**
```sql
SELECT * FROM articles ORDER BY created_at DESC LIMIT 5;
```

**Verify workflow status:**
1. Vào n8n UI
2. Check **Workflows** tab
3. Verify **Active** status
4. Review **Executions** history

---

## 🎉 CONGRATULATIONS!

Bạn đã hoàn thành MVP hệ thống tự động hóa tin tức!

**What you've built:**
- ✅ Automated news collection từ Google Sheets
- ✅ Web crawling và content extraction
- ✅ AI-powered summarization
- ✅ Email notifications
- ✅ SQLite database storage
- ✅ Scheduled execution

**Next milestone:** Scale up với WhatsApp integration và advanced features!

---

*📝 Lưu file này để reference và continue development journey của bạn!*

