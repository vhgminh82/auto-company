# APP MAP

## 1) Mục tiêu app
Hệ thống crawl dữ liệu doanh nghiệp theo `query/country/region/industry`, lưu vào SQLite, cho phép tìm kiếm và export CSV/XLSX trên giao diện web.

## 2) Cấu trúc thư mục
```text
crawl-company/
  README.md
  requirements.txt
  APP_MAP.md
  companies.db                # sinh ra sau khi chạy
  app/
    main.py                   # FastAPI app + routes
    database.py               # SQLite engine/session
    models.py                 # SQLAlchemy model Company
    schemas.py                # Pydantic schemas
    services/
      crawler.py              # search + fetch + extract pipeline
    static/
      index.html              # frontend UI
      styles.css              # giao diện bảng
      app.js                  # gọi API + render table
```

## 3) Module map
- `app/main.py`
  - Khởi tạo FastAPI, CORS, static mount.
  - API crawl/search/import/export.
  - Điều phối lưu dữ liệu từ service vào DB.

- `app/database.py`
  - Cấu hình `sqlite:///./companies.db`.
  - `SessionLocal`, `Base`, `get_db()`.

- `app/models.py`
  - Model `Company` với 13 trường chính + metadata (`country`, `region`, `industry`, `source_url`).
  - Unique key hiện tại: `(name, website)`.

- `app/schemas.py`
  - `CrawlRequest`: input crawl.
  - `CompanyOut`: output trả frontend.

- `app/services/crawler.py`
  - `search_websites()` tìm candidate URLs.
  - `extract_company_from_website()` parse title/email/phone/social/description.
  - `crawl_companies()` chạy pipeline và trả list company records.

- `app/static/*`
  - `index.html`: form crawl, form filter, nút import/export, bảng dữ liệu.
  - `app.js`: gọi API `/api/crawl`, `/api/companies`, `/api/import`.
  - `styles.css`: style giao diện.

## 4) API map
- `GET /`
  - Trả UI.

- `POST /api/crawl`
  - Input: `query`, `country`, `region`, `industry`, `max_companies`.
  - Flow: crawl -> insert SQLite -> trả `fetched/inserted`.

- `GET /api/companies`
  - Query filter: `q`, `country`, `region`, `industry`, `limit`.
  - Trả danh sách company cho bảng.

- `POST /api/import`
  - Upload `.csv/.xlsx`.
  - Parse bằng pandas, insert DB, bỏ qua record trùng theo unique key.

- `GET /api/export/csv`
  - Export toàn bộ DB ra CSV.

- `GET /api/export/xlsx`
  - Export toàn bộ DB ra Excel.

## 5) Data flow map
1. User nhập tiêu chí crawl ở frontend.
2. Frontend gọi `POST /api/crawl`.
3. Backend gọi `crawl_companies()` để lấy dữ liệu thô từ web.
4. Backend normalize mức cơ bản + lưu `Company` vào SQLite.
5. Frontend gọi `GET /api/companies` để hiển thị dạng bảng.
6. User export bằng `/api/export/csv` hoặc `/api/export/xlsx`.

## 6) Điểm mở rộng (khuyến nghị)
- Tách `connectors/` theo nguồn để linh hoạt hơn.
- Thêm `deduper.py` cho so trùng theo domain/email/fuzzy-name.
- Thêm `browser_fetcher.py` (Playwright) cho trang render JS/anti-bot.
- Thêm `crawl_jobs` + queue worker để chạy nền và theo dõi trạng thái.
