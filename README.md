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
