# APP MAP V2 (Production Architecture)

## 1) Mục tiêu
Kiến trúc crawl doanh nghiệp linh hoạt, mở rộng nhanh nguồn dữ liệu, chịu được trang khó crawl, có cơ chế lọc trùng/merge chất lượng cao, và vận hành ổn định ở quy mô lớn.

## 2) Kiến trúc tổng thể
```text
[Frontend UI]
   -> [API Gateway (FastAPI)]
      -> [Job Orchestrator]
         -> [Task Queue]
            -> [Connector Workers] -> [Fetch Layer: HTTP -> Browser Fallback -> Proxy]
               -> [Extraction Layer]
               -> [Normalize Layer]
               -> [Dedup + Merge Layer]
               -> [Quality Scoring]
               -> [Storage Layer: SQLite/Postgres]
      -> [Search/Filter API]
      -> [Export API CSV/XLSX]

[Observability: logs + metrics + job monitor]
```

## 3) Cấu trúc thư mục đề xuất
```text
crawl-company/
  app/
    main.py
    core/
      config.py
      logging.py
      rate_limit.py
      retry.py
      proxy_pool.py
    api/
      crawl.py
      companies.py
      import_export.py
      jobs.py
    connectors/
      base.py
      google_maps.py
      yellowpages.py
      linkedin_company.py
      registry_open_data.py
      website_discovery.py
    fetchers/
      http_fetcher.py
      browser_fetcher.py
      anti_bot.py
    pipeline/
      orchestrator.py
      extractor.py
      normalizer.py
      deduper.py
      merger.py
      scorer.py
    models/
      company.py
      company_source.py
      crawl_job.py
      crawl_task.py
      crawl_log.py
    repositories/
      company_repo.py
      job_repo.py
    workers/
      crawl_worker.py
    static/
      index.html
      app.js
      styles.css
  tests/
    unit/
    integration/
    e2e/
  requirements.txt
  APP_MAP.md
  APP_MAP_V2.md
```

## 4) Luồng xử lý dữ liệu
1. User tạo crawl job từ UI (`query/country/region/industry`).
2. API ghi `crawl_job` + enqueue tasks theo từng connector.
3. Worker lấy task:
   - chạy connector discovery để lấy candidate records/urls.
   - fetch nội dung theo chiến lược: `HTTP first`, fail thì `Browser`, fail nữa thì `Proxy`.
4. Extraction lấy field mục tiêu: tên, địa chỉ, city, state, website, email, phone, mô tả, FB, YouTube, X, LinkedIn, Truth.
5. Normalizer chuẩn hóa tên/domain/phone/address.
6. Deduper phát hiện trùng, Merger hợp nhất record theo policy.
7. Scorer chấm điểm chất lượng và gắn cờ confidence.
8. Lưu vào DB + ghi provenance (nguồn nào tạo field nào).
9. UI truy vấn dữ liệu + export CSV/XLSX.

## 5) Strategy crawl trang khó
- Bậc 1: HTTP fetch (`httpx`) với timeout + retry + user-agent rotation.
- Bậc 2: Browser fetch (Playwright) cho JS rendering/infinite scroll.
- Bậc 3: Proxy rotation/residential proxy cho domain bị block.
- Bậc 4: Captcha detected -> mark `manual_review` hoặc provider bypass.
- Cache HTML snapshot để tránh crawl lặp.

## 6) Cơ chế lọc trùng và merge
### 6.1 Dedup keys
- Strong key:
  - normalized root domain trùng.
  - email doanh nghiệp trùng.
- Soft key:
  - fuzzy name + city/state/country.
  - phone normalized + name gần giống.

### 6.2 Merge policy
- Không ghi đè bừa: chỉ thay field cũ khi:
  - field cũ rỗng, hoặc
  - nguồn mới có score cao hơn.
- Giữ provenance theo field (`field_source`, `field_updated_at`).
- Lưu các alias tên công ty để hỗ trợ search.

## 7) Mô hình dữ liệu khuyến nghị
- `companies`
  - record canonical sau dedupe/merge.
- `company_sources`
  - raw/enriched records từ từng nguồn, map về `company_id`.
- `crawl_jobs`
  - trạng thái job tổng (`pending/running/done/failed`).
- `crawl_tasks`
  - trạng thái task per connector.
- `crawl_logs`
  - lỗi, retry count, block type, latency.

## 8) API map V2
- `POST /api/jobs/crawl` tạo crawl job.
- `GET /api/jobs/{job_id}` xem tiến độ.
- `GET /api/jobs/{job_id}/tasks` xem task từng connector.
- `GET /api/companies` tìm kiếm/lọc nâng cao.
- `POST /api/import` import CSV/XLSX.
- `GET /api/export/csv` export CSV.
- `GET /api/export/xlsx` export Excel.

## 9) Công nghệ đề xuất
- Backend: Python + FastAPI
- Crawl HTTP: httpx + bs4/lxml
- Crawl browser: Playwright
- Queue: RQ/Celery (Redis broker)
- DB:
  - Dev: SQLite
  - Prod: PostgreSQL
- Export: pandas + openpyxl
- Frontend: HTML/CSS/JS hoặc React nếu cần dashboard mạnh

## 10) Roadmap triển khai
1. Tách code hiện tại thành `api`, `pipeline`, `connectors`, `models`.
2. Bổ sung `crawl_jobs/crawl_tasks` + worker queue.
3. Thêm browser fetcher + anti-bot policy.
4. Thêm dedupe/merge/scoring đầy đủ.
5. Bổ sung dashboard trạng thái job + metrics.
6. Viết test unit/integration/e2e, mục tiêu coverage >= 80%.
