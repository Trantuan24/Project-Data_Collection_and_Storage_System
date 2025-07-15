# 🚀 HƯỚNG DẪN TRIỂN KHAI MVP HỆ THỐNG TỰ ĐỘNG HÓA TIN TỨC (4 GIỜ)

> **Mục tiêu:** Tạo một hệ thống tự động crawl tin tức từ Google Sheets, tóm tắt bằng AI và gửi kết quả qua WhatsApp/Email trong 4 giờ.

## 📋 TỔNG QUAN MVP

**MVP sẽ bao gồm:**
- ✅ Đọc URLs từ Google Sheets
- ✅ Nhận URLs từ WhatsApp messages (đơn giản)
- ✅ Crawl nội dung tin tức cơ bản
- ✅ Lưu vào MySQL database
- ✅ Tóm tắt bằng Google Gemini API (cost-effective)
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

**Bước 1.5: Setup Google Gemini API (10 phút)**
1. **Tạo Google Cloud Project:**
   - Truy cập: https://console.cloud.google.com/
   - Tạo project mới: `news-automation-gemini`
   - Enable billing cho project (cần credit card)

2. **Enable Gemini API:**
   - Vào **APIs & Services** > **Library**
   - Tìm "Generative Language API" (Gemini)
   - Click **Enable**

3. **Tạo API Key:**
   - Vào **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **API Key**
   - Copy API key (bắt đầu với `AIza`)
   - **Restrict API key**: Chọn "Generative Language API"

4. **Test API Connection:**
   ```bash
   curl -H 'Content-Type: application/json' \
        -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
        -X POST 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY'
   ```

5. **Cost Structure:**
   - **Gemini Pro**: $0.0005/1K characters (input), $0.0015/1K characters (output)
   - **Much cheaper than OpenAI**: ~10x cost savings
   - **Free tier**: 60 requests/minute

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

**IMPORTANT**: HTML Extract node không automatically pass URL từ previous node. Chúng ta sẽ fix trong Clean Data function.

**Bước 2.8: Thêm Function Node để clean data**
```javascript
// Clean và format crawled data - lấy URL gốc từ Google Sheets
const items = [];

// Get HTML Extract data (current input)
const htmlItems = $input.all();

// Get URL gốc từ Code node (Bước 2.4 - xử lý Google Sheets)
const googleSheetsItems = $('Code').all();

for (let i = 0; i < htmlItems.length; i++) {
  const htmlItem = htmlItems[i];
  const sheetsItem = googleSheetsItems[i]; // Corresponding Google Sheets item

  const title = htmlItem.json.title || 'No title';
  const contentArray = htmlItem.json.content || [];
  const url = sheetsItem?.json?.url || 'No URL'; // URL gốc từ Google Sheets

  // Lấy 3 paragraphs đầu tiên
  const content = contentArray
    .slice(0, 3)
    .join(' ')
    .substring(0, 500) + '...';

  items.push({
    json: {
      url: url,
      title: title,
      content: content,
      crawledAt: new Date().toISOString(),
      wordCount: content.split(' ').length
    }
  });
}

return items;
```

### 💾 Workflow 3: Database Storage (10 phút)

**Bước 3.9: MySQL Node - Store Articles (10 phút)**
1. Thêm **MySQL** node sau "Clean Data" function
2. **Name**: "Store Articles"

**Parameters Tab:**
- **Credential**: MySQL account 2
- **Operation**: Insert
- **Table**: articles
- **Columns**:
  - url: `{{ $json.url }}`
  - title: `{{ $json.title }}`
  - content: `{{ $json.content }}`
  - crawled_at: `{{ $json.crawledAt }}`
  - word_count: `{{ $json.wordCount }}`

**Options:**
- **Add option** → **Skip on Conflict**: ✅ ON

**Settings Tab:**
- **Always Output Data**: ✅ ON
- **Execute Once**: ❌ OFF
- **Retry On Fail**: ❌ OFF

**Bước 3.10: Function Node - Prepare for AI (5 phút)**
1. Thêm **Function** node sau "Store Articles"
2. **Name**: "Prepare AI Data"
3. **Code**:
```javascript
// Get original article data from Clean Data node (before MySQL)
const cleanDataItems = $('Clean Data').all();
const mysqlResults = $input.all();

console.log(`Database: ${mysqlResults.length} articles processed`);
console.log(`Clean Data: ${cleanDataItems.length} articles available`);

// Use original article data from Clean Data node
const articles = cleanDataItems
  .filter(item => item.json.url && item.json.url !== 'No URL')
  .map(item => ({
    url: item.json.url,
    title: item.json.title,
    content: item.json.content,
    wordCount: item.json.wordCount,
    crawledAt: item.json.crawledAt
  }));

return [{
  json: {
    articles: articles,
    articleCount: articles.length,
    timestamp: new Date().toISOString(),
    status: 'ready_for_ai'
  }
}];
```


### 🤖 Workflow 4: AI Summarization - Individual Article Processing (25 phút)

**Bước 4.1: Function Node - Prepare Individual Articles (5 phút)**
1. Thêm **Function** node sau "Prepare AI Data"
2. **Name**: "Split Articles for AI"
3. **Code**:
```javascript
// Split articles array thành individual items để process riêng biệt
const inputData = $input.first().json;
const articles = inputData.articles || [];

console.log(`Processing ${articles.length} articles individually`);

// Return each article as separate item
return articles.map((article, index) => ({
  json: {
    article: article,
    articleIndex: index,
    totalArticles: articles.length,
    timestamp: inputData.timestamp
  }
}));
```

**Bước 4.2: Basic LLM Chain với Google Gemini - Generate Individual Summary (15 phút)**
1. Thêm **Basic LLM Chain** node sau "Split Articles for AI"
2. **Name**: "AI Summarize Individual"

**Parameters Tab:**
- **Source for Prompt (User Message)**: Define below
- **Prompt (User Message)**:
```
Tóm tắt bài báo sau bằng tiếng Việt trong 2-3 câu ngắn gọn. Chỉ trả về nội dung tóm tắt, không thêm lời giới thiệu hay kết luận.

Tiêu đề: {{$json.article.title}}

Nội dung: {{$json.article.content}}

Trả về trực tiếp nội dung tóm tắt bằng tiếng Việt, 2-3 câu, tập trung vào thông tin quan trọng nhất.
```

**Model Selection (scroll xuống):**
- **Model**: Click dropdown → chọn **Google Gemini Chat Model**
- **Credential**: Google Gemini(PaLM) Api account (từ bước 1.5)
- **Model Name**: gemini-pro hoặc gemini-1.5-pro
- **Options**:
  - **Require Specific Output Format**: ❌ OFF
  - **Enable Fallback Model**: ❌ OFF

**Settings Tab:**
- **Always Output Data**: ✅ ON
- **Execute Once**: ❌ OFF (để process multiple articles)
- **Retry On Fail**: ✅ ON (retry: 2 times)

**Bước 4.3: Function Node - Collect Individual Summaries (5 phút)**
1. Thêm **Function** node sau "AI Summarize Individual"
2. **Name**: "Collect Summaries"
3. **Code**:
```javascript
// Collect all individual summaries và combine thành final output
const allSummaries = $input.all();

console.log('=== COLLECT SUMMARIES DEBUG ===');
console.log(`Collected ${allSummaries.length} individual summaries`);

// Debug: Log first item structure để understand data flow
if (allSummaries.length > 0) {
  console.log('First item structure:', JSON.stringify(allSummaries[0], null, 2));
}

// Extract summaries và original article data
const summariesWithArticles = allSummaries.map((item, index) => {
  console.log(`Processing item ${index + 1}:`);

  // Get original article data từ input (trước khi AI processing)
  const originalData = $('Split Articles for AI').all()[index];
  const originalArticle = originalData?.json?.article || {};

  // Get AI response
  const aiResponse = item.json;

  console.log(`Article ${index + 1} - Title: ${originalArticle.title}`);
  console.log(`Article ${index + 1} - URL: ${originalArticle.url}`);
  console.log(`Article ${index + 1} - AI Response keys:`, Object.keys(aiResponse));

  // Extract summary từ Basic LLM Chain response - try multiple fields
  let summary = aiResponse.text ||
                aiResponse.response ||
                aiResponse.message ||
                aiResponse.content ||
                'Không thể tạo tóm tắt';

  // Clean summary - remove AI conversation prefixes
  if (summary && summary !== 'Không thể tạo tóm tắt') {
    // Remove common AI prefixes
    summary = summary
      .replace(/^(Chắc chắn rồi\.|Dưới đây là|Tôi sẽ|Đây là).*?:/i, '')
      .replace(/^(Bản tóm tắt|Tóm tắt).*?:/i, '')
      .trim();
  }

  console.log(`Article ${index + 1} - Cleaned summary: ${summary.substring(0, 100)}...`);

  return {
    title: originalArticle.title || 'Không có tiêu đề',
    url: originalArticle.url || '',
    originalContent: originalArticle.content || '',
    summary: summary.trim(),
    wordCount: originalArticle.wordCount || 0,
    crawledAt: originalArticle.crawledAt || new Date().toISOString()
  };
});

// Create final output structure
const finalOutput = {
  summaries: summariesWithArticles,
  totalArticles: summariesWithArticles.length,
  successfulSummaries: summariesWithArticles.filter(s =>
    s.summary !== 'Không thể tạo tóm tắt' &&
    s.title !== 'Không có tiêu đề'
  ).length,
  timestamp: new Date().toISOString(),
  status: 'summaries_ready'
};

console.log(`Final output: ${finalOutput.successfulSummaries}/${finalOutput.totalArticles} summaries successful`);
console.log('Sample summary:', finalOutput.summaries[0]);

return [{
  json: finalOutput
}];
```

**🔧 TROUBLESHOOTING Individual Article Summarization:**

**1. Verify Split Articles Function:**
- ✅ **Check "Split Articles for AI"** output có multiple items
- ✅ **Each item** có structure: `{article: {...}, articleIndex: 0}`
- ❌ **Không có empty articles**

**2. Verify Basic LLM Chain Individual Processing:**
- ✅ **AI Summarize Individual** node processes each article separately
- ✅ **Template syntax** `{{$json.article.title}}` works correctly
- ✅ **Multiple executions** cho multiple articles

**3. Check Individual Article Input Structure:**
```javascript
// Each item từ "Split Articles for AI" should có format:
{
  "article": {
    "url": "https://...",
    "title": "...",
    "content": "...",
    "wordCount": 150,
    "crawledAt": "2025-01-14T..."
  },
  "articleIndex": 0,
  "totalArticles": 3,
  "timestamp": "2025-01-14T..."
}
```

**4. Test Google Gemini API Connection:**
- Kiểm tra **Google Gemini(PaLM) Api account** credential trong Basic LLM Chain
- Verify API key có sufficient quota
- Test với simple prompt: "Hello" trước
- Ensure model dropdown shows "Google Gemini Chat Model"

**5. Debug Individual Processing:**
- Click **"Execute step"** trên "Split Articles for AI" → should show multiple items
- Click **"Execute step"** trên "AI Summarize Individual" → should process each item
- Check console logs trong "Collect Summaries" để see final results

**6. Common Fixes:**
- **No multiple items**: Check "Split Articles for AI" function returns array
- **Empty summaries**: Verify template `{{$json.article.title}}` syntax
- **API quota exceeded**: Individual processing uses more API calls
- **Timeout issues**: Add delay between API calls nếu cần

**7. Data Quality Issues:**
- **"Không có tiêu đề"**: Check "Split Articles for AI" output structure
- **Empty URLs**: Verify original crawling data có URLs
- **AI conversation prefixes**: Use cleaned prompt template
- **Missing summaries**: Check Basic LLM Chain response fields

**8. Performance Optimization:**
- **Rate limiting**: Google Gemini có 60 requests/minute limit
- **Batch size**: Process max 10 articles at once để avoid timeout
- **Error handling**: Some articles có thể fail, others vẫn success

**🔧 IMMEDIATE DEBUG STEPS:**
1. **Add "Debug AI Responses" node** để check data flow
2. **Check console logs** trong từng Function node
3. **Verify original article data** từ crawling steps
4. **Test với 1 article** trước khi process multiple

**Bước 4.4: Debug Function Node - Check Data Quality (5 phút)**
1. Thêm **Function** node sau "AI Summarize Individual" (trước "Collect Summaries")
2. **Name**: "Debug AI Responses"
3. **Code**:
```javascript
// Debug AI responses để check data quality
const allResponses = $input.all();

console.log('=== AI RESPONSES DEBUG ===');
console.log(`Total responses: ${allResponses.length}`);

allResponses.forEach((response, index) => {
  console.log(`\n--- Response ${index + 1} ---`);
  console.log('Full response:', JSON.stringify(response.json, null, 2));

  // Check for AI response text
  const text = response.json.text || response.json.response || response.json.message;
  console.log(`Response text: ${text ? text.substring(0, 100) + '...' : 'EMPTY'}`);

  // Check original article data
  const originalData = $('Split Articles for AI').all()[index];
  if (originalData) {
    console.log(`Original title: ${originalData.json.article?.title || 'MISSING'}`);
    console.log(`Original URL: ${originalData.json.article?.url || 'MISSING'}`);
  }
});

// Pass through data unchanged
return $input.all();
```

**Bước 4.5: Test Individual Summarization (5 phút)**
1. **Execute "Split Articles for AI"** → should show multiple items (1 per article)
2. **Execute "AI Summarize Individual"** → should process each article separately
3. **Execute "Debug AI Responses"** → check console logs for data quality
4. **Execute "Collect Summaries"** → should combine all summaries

**Expected Final Output Structure:**
```json
{
  "summaries": [
    {
      "title": "Báo VnExpress - Báo tiếng Việt nhiều người xem nhất",
      "url": "https://vnexpress.net/...",
      "originalContent": "Chính phủ vừa giao Bộ Khoa học...",
      "summary": "Chính phủ giao Bộ KH&CN xây dựng đề án trọng dụng nhân tài chất lượng cao...",
      "wordCount": 86,
      "crawledAt": "2025-01-14T..."
    },
    {
      "title": "Báo Tuổi Trẻ - Tin tức mới nhất...",
      "url": "https://tuoitre.vn/...",
      "originalContent": "Giám đốc Công an Hà Nội cho biết...",
      "summary": "Công an Hà Nội dự kiến đến 18-12 sẽ lắp đủ camera AI...",
      "wordCount": 35,
      "crawledAt": "2025-01-14T..."
    }
  ],
  "totalArticles": 2,
  "successfulSummaries": 2,
  "timestamp": "2025-01-14T15:30:00.000Z",
  "status": "summaries_ready"
}
```

---

## � PHẦN 5: WHATSAPP OUTPUT CONFIGURATION (20 PHÚT)

### 📮 Setup WhatsApp Message Node (20 phút)

**Bước 5.1: Function Node - Format WhatsApp Message (5 phút)**
1. Thêm **Function** node sau "Collect Summaries"
2. **Name**: "Format WhatsApp Message"
3. **Code**:
```javascript
// Format message cho WhatsApp với individual summaries
const data = $input.first().json;
const summaries = data.summaries || [];

console.log(`Formatting WhatsApp message for ${summaries.length} summaries`);

// Create formatted message với từng summary riêng biệt
const summaryTexts = summaries.map((item, index) => {
  const title = item.title ? item.title.substring(0, 40) : 'Không có tiêu đề';
  const summary = item.summary || 'Không có tóm tắt';
  const url = item.url || '';

  return `📄 *Bài ${index + 1}: ${title}...*\n${summary}\n🔗 ${url}`;
}).join('\n\n');

const message = `📰 *TÓM TẮT TIN TỨC HÀNG NGÀY* 📰\n\n${summaryTexts}\n\n📊 *Thống kê:*\n• Tổng số bài: ${data.totalArticles}\n• Tóm tắt thành công: ${data.successfulSummaries}\n• Thời gian: ${new Date(data.timestamp).toLocaleString('vi-VN')}\n\n🤖 _Tin tức được tự động tóm tắt bởi AI - Mỗi bài có summary riêng biệt_`;

console.log('WhatsApp message formatted successfully');
console.log('Message length:', message.length);

return [{
  json: {
    whatsapp_message: message,
    summaryCount: summaries.length,
    messageLength: message.length
  }
}];
```

**Bước 5.2: Thêm WhatsApp Business Node**
1. Thêm **WhatsApp Business** node sau "Format WhatsApp Message"
2. Settings:
   - **Credential**: Use credential từ bước 2.2
   - **Resource**: Message
   - **Operation**: Send Text
   - **To**: YOUR_PHONE_NUMBER (replace với số điện thoại nhận)
   - **Message**: `{{$json.whatsapp_message}}`

**Bước 5.3: Test Individual Summarization Workflow**
1. **Execute "Split Articles for AI"** → verify multiple items output
2. **Execute "AI Summarize Individual"** → check each article gets summarized
3. **Execute "Collect Summaries"** → verify all summaries collected
4. **Execute "Format WhatsApp Message"** → check message format
5. **Execute "WhatsApp Business"** → test delivery

**Expected WhatsApp Message Format:**
```
📰 *TÓM TẮT TIN TỨC HÀNG NGÀY* 📰

📄 *Bài 1: Báo VnExpress - Báo tiếng Việt nhiều...*
Chính phủ giao Bộ KH&CN xây dựng đề án trọng dụng nhân tài chất lượng cao cho khoa học công nghệ, trình Thủ tướng trong tháng 9. Đây là nhiệm vụ cụ thể hóa Nghị quyết 57 của Bộ Chính trị.
🔗 https://vnexpress.net/xay-dung-de-an-trong-dung-nhan-tai-khoa-hoc-cong-nghe-4913987.html

📄 *Bài 2: Báo Tuổi Trẻ - Tin tức mới nhất...*
Công an Hà Nội dự kiến đến 18-12 sẽ lắp đủ camera AI để giao thông không cần cảnh sát giao thông nữa.
🔗 https://tuoitre.vn/...

📊 *Thống kê:*
• Tổng số bài: 2
• Tóm tắt thành công: 2
• Thời gian: 14/01/2025, 15:30:00

🤖 _Tin tức được tự động tóm tắt bởi AI - Mỗi bài có summary riêng biệt_
```

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
   - MySQL → Function (Prepare AI Data)
   - Prepare AI Data → Function (Split Articles for AI)
   - Split Articles for AI → Basic LLM Chain (AI Summarize Individual)
   - AI Summarize Individual → Function (Collect Summaries)
   - Collect Summaries → Function (Format WhatsApp Message)
   - Format WhatsApp Message → WhatsApp Business (Send Message)

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
1. Click vào Google Gemini node
2. Click **Test step**
3. **Expected Output**: Vietnamese summary text
4. **Troubleshooting**:
   - API key error: Kiểm tra Gemini API key format
   - Rate limit: Đợi 1 phút và thử lại (60 requests/minute limit)
   - Quota exceeded: Check Google Cloud billing

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
- Check Google Gemini API quota
- Verify prompt format for Gemini
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

**3. "Google Gemini API quota exceeded"**
```
Solution:
- Đợi 1 phút và retry (60 requests/minute limit)
- Check Google Cloud billing status
- Add delay giữa requests (1-2 seconds)
- Consider upgrading to paid tier for higher limits
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

