# Crawl Company Platform

Nền tảng crawl dữ liệu doanh nghiệp theo quốc gia, khu vực, ngành nghề với lưu trữ SQLite và giao diện tìm kiếm/export.

## Dữ liệu thu thập
- `name`
- `address`
- `city`
- `state`
- `website`
- `email`
- `phone`
- `short_description`
- `facebook`
- `youtube`
- `x`
- `linkedin`
- `truth`
- + metadata: `country`, `region`, `industry`, `source_url`

## Kiến trúc hiện tại
- `app/api/`: routes theo domain (`crawl`, `companies`, `import_export`, `ui`)
- `app/pipeline/`: `CrawlContext`, `CrawlOrchestrator`
- `app/pipeline/processors/`: `normalizer`, `deduper`, `merger`, `scorer`
- `app/connectors/`: plugin connectors (hiện có `WebsiteDiscoveryConnector`)
- `app/fetchers/`: `HttpFetcher`, `BrowserFetcher`, `FallbackFetcher` (`HTTP -> Browser`)
- `app/repositories/`: DB access layer
- `app/models/`: SQLAlchemy models
- `app/core/`: constants/config dùng chung

## Cài đặt
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
# optional cho browser fallback:
playwright install chromium
uvicorn app.main:app --reload
```

Mở: http://127.0.0.1:8000

## API chính
- `POST /api/crawl`
- `GET /api/companies`
- `POST /api/import` (CSV/XLSX)
- `GET /api/export/csv`
- `GET /api/export/xlsx`
- `POST /api/ai/company-analysis` — phân tích một doanh nghiệp bằng OpenRouter. Body: `{"company_id": 123, "language": "vi"}`.
- `POST /api/contact/inspect` — nhận URL, tìm form ở trang gốc và các trang Contact cùng domain, phát hiện CAPTCHA.
- `POST /api/contact/submit` — điền và gửi một form không có CAPTCHA sau khi client xác nhận.
- `POST /api/contact/sheet/run` — tự đọc tab `company`, xử lý batch tối đa 100 dòng và ghi trạng thái vào cột `Contact`.
- `GET /api/contact/sheet/status/{job_id}` — xem tiến độ job.
- `POST /api/sheet/sync` — xóa dữ liệu DB hiện có và đồng bộ tab `company` vào DB.

## Đã triển khai
- Fallback fetch cho trang khó: HTTP -> Browser.
- Lọc trùng nhiều lớp: domain/email/name+location.
- Merge record trùng theo độ đầy đủ dữ liệu.
- Quality score nội bộ để ưu tiên record tốt hơn.
- Contact form chỉ gửi trong cùng domain, dừng khi phát hiện CAPTCHA, và UI yêu cầu xác nhận trước khi gửi.
- Sheet worker chỉ đọc các dòng có website và `Contact` đang trống; mỗi batch ghi kết quả ngay sau khi crawl xong.

### Google Sheets worker

Để worker ghi được Sheet, tạo Google Service Account, chia sẻ spreadsheet cho email của service account với quyền Editor, rồi cấu hình một trong hai biến môi trường `GOOGLE_SERVICE_ACCOUNT_FILE` hoặc `GOOGLE_SERVICE_ACCOUNT_JSON`. Không commit file JSON khóa vào repository.

## Roadmap
- Phase 4: queue worker + job monitor dashboard.

### Đăng nhập Google và Microsoft 365

App yêu cầu đăng nhập trước khi truy cập giao diện và API. Tạo OAuth app ở Google Cloud Console và Microsoft Entra ID, sau đó cấu hình:

```env
AUTH_BASE_URL=https://ten-mien-cua-ban.example
AUTH_SESSION_SECRET=<chuoi-ngau-nhien-dai>
GOOGLE_CLIENT_ID=<google-client-id>
GOOGLE_CLIENT_SECRET=<google-client-secret>
MICROSOFT_CLIENT_ID=<entra-application-client-id>
MICROSOFT_CLIENT_SECRET=<entra-client-secret>

# AI qua OpenRouter
OPENROUTER_API_KEY=<openrouter-api-key>
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b
OPENROUTER_MODEL_FALLBACK_1=poolside/laguna-s-2.1
OPENROUTER_MODEL_FALLBACK_2=inclusionai/ling-3.0-flash-fin
OPENROUTER_SITE_URL=https://ten-mien-cua-ban.example
OPENROUTER_APP_NAME=Company Crawl Platform
OPENROUTER_MAX_TOKENS=2048
```

Đăng ký đúng callback URL tương ứng:
- `https://ten-mien-cua-ban.example/auth/google/callback`
- `https://ten-mien-cua-ban.example/auth/microsoft/callback`

Có thể chỉ cấu hình một nhà cung cấp; nút chưa cấu hình sẽ không hiển thị. Khi chạy local, dùng `AUTH_BASE_URL=http://127.0.0.1:9997` và đăng ký callback cùng địa chỉ đó.