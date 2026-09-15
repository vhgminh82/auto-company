const REGION_BY_COUNTRY = {
  'United States': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Washington'],
  Vietnam: ['Ho Chi Minh City', 'Ha Noi', 'Da Nang', 'Binh Duong', 'Dong Nai', 'Hai Phong'],
  Canada: ['Ontario', 'Quebec', 'British Columbia', 'Alberta'],
  Germany: ['Bavaria', 'Berlin', 'Hamburg', 'Hesse'],
  Japan: ['Tokyo', 'Osaka', 'Aichi', 'Kanagawa'],
};

const INDUSTRIES = [
  'Machinery', 'Manufacturing', 'Automotive', 'Electronics', 'Logistics', 'Construction',
  'Textile', 'Food & Beverage', 'IT Services', 'Healthcare', 'Education', 'Retail',
  'Finance', 'Energy', 'Real Estate', 'Agriculture', 'Tourism', 'Telecommunications'
];

const COUNTRY_NAMES = {
  AE: 'United Arab Emirates', AU: 'Australia', BH: 'Bahrain', Canada: 'Canada',
  CN: 'China', EG: 'Egypt', GB: 'United Kingdom', HK: 'Hong Kong',
  'Hoa Kỳ': 'United States', IL: 'Israel', IN: 'India', JO: 'Jordan', JP: 'Japan',
  KR: 'South Korea', KW: 'Kuwait', LB: 'Lebanon', MX: 'Mexico', MY: 'Malaysia',
  NZ: 'New Zealand', OM: 'Oman', PH: 'Philippines', PR: 'Puerto Rico',
  PS: 'Palestine', QA: 'Qatar', SA: 'Saudi Arabia', TH: 'Thailand', TR: 'Turkey',
  TW: 'Taiwan', VN: 'Vietnam',
};
const INDUSTRY_LABELS = {Machinery: 'Máy móc', Manufacturing: 'Sản xuất', Automotive: 'Ô tô & phụ tùng', Electronics: 'Điện tử & công nghệ', Logistics: 'Logistics & phân phối', Construction: 'Xây dựng & vật liệu', Textile: 'May mặc', 'Food & Beverage': 'Thực phẩm & đồ uống', Healthcare: 'Y tế & chăm sóc sức khỏe', 'Plastic injection molding service': 'Dịch vụ ép nhựa', 'Machining manufacturer': 'Gia công cơ khí', 'Mold maker': 'Làm khuôn', 'Wood supplier': 'Gỗ', 'Packaging company': 'Bao bì & đóng gói'};
const INDUSTRY_GROUPS = [['Cơ khí chính xác', ['precision', 'machining', 'machine shop', 'cơ khí chính xác']], ['Khuôn', ['mold', 'mould', 'tool & die', 'khuôn']], ['Ép nhựa', ['plastic injection', 'molding supplier', 'ép nhựa']], ['Gỗ', ['wood', 'gỗ']], ['Thực phẩm', ['food', 'baking', 'thực phẩm']], ['May mặc', ['textile', 'textiles', 'may mặc']], ['Điện tử & công nghệ', ['electronic', 'electronics', 'điện tử']], ['Ô tô & phụ tùng', ['automotive', 'auto parts', 'vehicle', 'ô tô']], ['Máy móc & thiết bị', ['machinery', 'machine', 'equipment', 'máy móc']], ['Kim loại & gia công', ['metal', 'steel', 'welder', 'welding', 'foundry', 'kim loại']], ['Bao bì & in ấn', ['packaging', 'paper', 'print', 'bao bì', 'in ấn']], ['Hóa chất & nhựa', ['chemical', 'polymer', 'polythene', 'plastic resin', 'hóa chất']], ['Cao su & foam', ['rubber', 'foam', 'cao su']], ['Xây dựng & vật liệu', ['construction', 'roofing', 'gypsum', 'building materials', 'xây dựng']], ['Logistics & phân phối', ['logistics', 'warehouse', 'distributor', 'wholesaler', 'phân phối']], ['Dịch vụ công nghiệp', ['industrial', 'factory', 'manufacturer', 'supplier']], ['Thương mại & bán lẻ', ['retail', 'store', 'shop', 'trading', 'thương mại']], ['Y tế', ['health', 'medical', 'sanitation', 'y tế']], ['Năng lượng', ['energy', 'năng lượng']], ['Nông nghiệp', ['agriculture', 'farm', 'nông nghiệp']], ['Nội thất & gia dụng', ['home', 'household', 'furniture', 'nội thất']], ['Giày dép & da', ['shoe', 'leather', 'giày', 'da']], ['Trang sức', ['jewelry', 'trang sức']], ['Tư vấn & kỹ thuật', ['engineer', 'engineering', 'consultant', 'tư vấn', 'kỹ thuật']], ['Sản xuất công nghiệp', ['manufacturing', 'production', 'sản xuất']], ['Công ty & văn phòng', ['company', 'corporate', 'holding', 'office', 'công ty', 'văn phòng']], ['Dịch vụ khác', ['service', 'repair', 'dịch vụ']], ['Khác', []]];

const TABLE_COLUMNS = [
  null,
  'name', 'industry', 'country', 'address', 'city', 'state', 'website', 'contact', 'email', 'email_2', 'phone',
  'short_description', 'facebook', 'facebook_alt', 'youtube', 'x', 'linkedin',
  'truth',
];
const TABLE_EDIT_FIELDS = [null, 'name', 'industry', 'country', 'address', 'city', 'state', 'website', 'contact', 'email', 'email_2', 'phone', 'short_description', 'facebook', 'facebook_alt', 'youtube', 'x', 'linkedin', 'truth'];
const TABLE_LABELS = {name: 'Tên cty', industry: 'Ngành', country: 'Quốc gia', address: 'Địa chỉ', city: 'Khu vực', state: 'Bang/Tỉnh', website: 'Website', contact: 'Contact', email: 'Email', email_2: 'Email 2', phone: 'SĐT', short_description: 'Mô tả', facebook: 'FB', facebook_alt: 'FB phụ', youtube: 'Youtube', x: 'X', linkedin: 'LinkedIn', truth: 'Truth'};
let displayedCompanies = [];
let tableRows = [];
let sortColumn = '';
let sortDirection = 1;
const VIRTUAL_ROW_HEIGHT = 42;
const VIRTUAL_WINDOW = 100;
const COUNTRY_SOURCE_COLUMNS = [
  ['place_name', 'Tên địa điểm'], ['country', 'Quốc gia'], ['state', 'Bang'], ['city', 'Thành phố'], ['region', 'Khu vực'],
  ...Array.from({length: 16}, (_, index) => [`keyword_${index + 1}`, ''])
];

function setOptions(selectEl, values, placeholder) {
  selectEl.innerHTML = '';

  const allOption = document.createElement('option');
  allOption.value = '';
  allOption.textContent = 'All';
  selectEl.appendChild(allOption);

  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = placeholder;
  placeholderOption.disabled = true;
  selectEl.appendChild(placeholderOption);

  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    selectEl.appendChild(option);
  });

  selectEl.selectedIndex = 0;
}

function initTabs() {
  const storageKey = 'companyCrawl.activeTab';
  const buttons = [...document.querySelectorAll('.tab-button')];

  const activateTab = (button) => {
    buttons.forEach((item) => item.classList.toggle('active', item === button));
    document.querySelectorAll('.tab-content').forEach((panel) => { panel.hidden = panel.id !== button.dataset.tab; });
    localStorage.setItem(storageKey, button.dataset.tab);
    if (button.dataset.tab === 'emktTab') {
      Promise.all([loadEmktAccounts(), loadEmktList()]).then(() => renderCampaignListOptions()).catch((error) => {
        document.getElementById('emktAccountStatus').textContent = `eMKT lỗi tải tài khoản/list: ${error.message}`;
      });
    }
  };

  buttons.forEach((button) => button.addEventListener('click', () => activateTab(button)));
  const savedTab = localStorage.getItem(storageKey);
  activateTab(buttons.find((button) => button.dataset.tab === savedTab) || buttons[0]);
}

async function loadCountrySource() {
  const status = document.getElementById('countrySourceStatus');
  const fetchJson = async (url) => {
    const response = await fetch(url);
    const contentType = response.headers.get('content-type') || '';
    const body = await response.text();
    let payload;
    try {
      payload = body ? JSON.parse(body) : null;
    } catch {
      throw new Error(`${response.status} ${response.statusText}: ${body.slice(0, 120)}`);
    }
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}: ${payload?.detail || body.slice(0, 120)}`);
    }
    if (!contentType.includes('application/json')) {
      throw new Error(`${response.status} ${response.statusText}: Phản hồi không phải JSON.`);
    }
    return payload;
  };
  try {
    const [rows, keywords] = await Promise.all([
      fetchJson(`/api/country-source?limit=25000&country=${encodeURIComponent(document.getElementById('countrySourceCountryFilter')?.value || '')}&city=${encodeURIComponent(document.getElementById('countrySourceCityFilter')?.value || '')}&state=${encodeURIComponent(document.getElementById('countrySourceStateFilter')?.value || '')}`),
      fetchJson('/api/country-source/keywords'),
    ]);
    let stats = {total_locations: rows.length, pending_locations: 0, pending_combinations: 0};
    try {
      stats = await fetchJson('/api/country-source/stats');
    } catch (error) {
      console.warn('Không tải được thống kê dữ liệu quốc gia:', error);
    }
    window.countrySourceRows = rows;
    window.countryKeywords = keywords;
    renderCountrySourceTable();
    status.textContent = `Có ${stats.total_locations} địa điểm; còn ${stats.pending_locations} địa điểm / ${stats.pending_combinations} tổ hợp từ khóa–địa điểm chưa có V.`;
  } catch (error) {
    status.textContent = `Không tải được dữ liệu quốc gia: ${error.message}`;
  }
}

function activeKeywordForGroup(groupPosition) {
  const active = (window.countryKeywords || []).find((item) =>
    (item.group_position || item.position) === groupPosition && Number(item.active) === 1
  );
  return active ? active.position : groupPosition;
}

function renderCountrySourceTable() {
  const rows = window.countrySourceRows || [];
    const headers = ['Tên địa điểm', 'Quốc gia', 'Bang', 'Thành phố', 'Khu vực', ...Array.from({length: 16}, (_, i) => `Từ khóa ${i + 1}`)];
    document.querySelector('#countrySourceTable thead').innerHTML = `<tr>${headers.map((header, index) => index < 5 ? `<th>${header}</th>` : `<th><button class="keyword-header" data-keyword-position="${index - 4}" type="button">${header}</button></th>`).join('')}</tr>`;
    document.querySelector('#countrySourceTable tbody').innerHTML = rows.map((row) => `<tr>${COUNTRY_SOURCE_COLUMNS.map(([key]) => {
      const value = String(row[key] || '');
      const safeValue = value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
      return `<td>${safeValue}</td>`;
    }).join('')}</tr>`).join('');
}

async function openKeywordModal(position) {
  const keyword = (window.countryKeywords || []).find((item) => item.position === position);
  if (!keyword) return;
  document.getElementById('keywordModalTitle').textContent = `Từ khóa ${position}`;
  renderKeywordRows(position);
  document.getElementById('keywordModal').hidden = false;
}

function renderKeywordRows(activePosition) {
  const container = document.getElementById('keywordRows');
  container.innerHTML = '';
  const visible = (window.countryKeywords || []).filter((item) => (item.group_position || item.position) === activePosition);
  const storedActive = activeKeywordForGroup(activePosition);
  visible.forEach((item) => {
    const row = document.createElement('div');
    row.className = 'keyword-display-row';
    row.innerHTML = `<input type="radio" name="activeKeyword" value="${item.position}" ${item.position === storedActive ? 'checked' : ''}><span>${item.keyword || '(trống)'}</span>`;
    if (item.position > 16) {
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'delete-keyword-btn';
      remove.textContent = 'Xóa';
      remove.onclick = () => deleteKeyword(item.position, activePosition, item.keyword);
      row.appendChild(remove);
    }
    container.appendChild(row);
  });
}

async function deleteKeyword(position, groupPosition, keyword) {
  if (!window.confirm(`Xóa từ khóa "${keyword}"?`)) return;
  const response = await fetch(`/api/country-source/keywords/${position}`, {method: 'DELETE'});
  if (!response.ok) {
    const result = await response.json();
    window.alert(result.detail || 'Không thể xóa từ khóa.');
    return;
  }
  window.countryKeywords = await (await fetch('/api/country-source/keywords')).json();
  if (activeKeywordForGroup(groupPosition) === position) {
    localStorage.removeItem(`activeKeywordPosition_${groupPosition}`);
    renderCountrySourceTable();
  }
  renderKeywordRows(groupPosition);
}

function addKeywordRow() {
  const row = document.createElement('div');
  row.className = 'keyword-select-row';
  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Nhập từ khóa mới';
  const remove = document.createElement('button');
  remove.type = 'button'; remove.textContent = 'Lưu';
  remove.onclick = () => saveNewKeyword(row);
  row.append(input, remove);
  document.getElementById('keywordRows').appendChild(row);
}

async function saveNewKeyword(row) {
  const input = row.querySelector('input');
  const keyword = input.value.trim();
  if (!keyword) return;
  const groupPosition = Number(document.getElementById('keywordModalTitle').textContent.replace(/\D/g, ''));
  const response = await fetch('/api/country-source/keywords', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({keyword, group_position: groupPosition})});
  if (!response.ok) return;
  row.remove();
  window.countryKeywords = await (await fetch('/api/country-source/keywords')).json();
  renderKeywordRows(Number(document.getElementById('keywordModalTitle').textContent.replace(/\D/g, '')));
}

async function saveAllNewKeywords() {
  const rows = [...document.querySelectorAll('#keywordRows .keyword-select-row')];
  for (const row of rows) await saveNewKeyword(row);
  loadCountrySource();
}

function emktEscape(value) {
  return String(value || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

function fillEmktFilter(select, values, label) {
  select.innerHTML = `<option value="">${label}</option>`;
  values.forEach((value) => {
    const option = document.createElement('option'); option.value = value; option.textContent = value; select.appendChild(option);
  });
}

async function loadEmktList() {
  const lists = await (await fetch('/api/emkt/lists')).json();
  window.emktLists = lists;
  document.getElementById('emktListSummary').textContent = `${lists.length} list · tổng số khách hàng được quản lý độc lập với bảng dữ liệu chính`;
  document.getElementById('emktListCustomers').innerHTML = lists.length ? `<table class="campaign-table"><thead><tr><th>List</th><th>Bộ lọc</th><th>Khách hàng</th><th>Thống kê / thao tác</th></tr></thead><tbody>${lists.map((item) => `<tr><td><button class="campaign-name list-open-btn" type="button" data-list-open="${item.id}">${emktEscape(item.name)}</button></td><td>${emktEscape(item.country_filter || 'Tất cả quốc gia')}<br>${emktEscape(item.industry_filter || 'Tất cả ngành')}<br>${emktEscape(item.query_filter || '')}</td><td>${item.customer_count} khách hàng có email hợp lệ</td><td><button type="button" data-list-edit="${item.id}">Sửa</button><button type="button" class="danger-button" data-list-delete="${item.id}">Xóa</button></td></tr>`).join('')}</tbody></table><div id="emktSelectedListCustomers"></div>` : '<p>Chưa có list. Bấm + New để tạo danh mục khách hàng.</p>';
}

async function showEmktListCustomers(listId) {
  const list = (window.emktLists || []).find((item) => item.id === Number(listId));
  const rows = await (await fetch(`/api/emkt/lists/${listId}/customers`)).json();
  window.emktCustomerRows = rows;
  window.emktCustomerListId = Number(listId);
  window.emktCustomerSort = {field: '', direction: 1};
  renderEmktListCustomers(list);
}

function renderEmktListCustomers(list) {
  const listId = window.emktCustomerListId;
  const target = document.getElementById('emktSelectedListCustomers');
  if (!target) return;
  const term = (document.getElementById('emktCustomerSearch')?.value || '').trim().toLowerCase();
  const sort = window.emktCustomerSort || {field: '', direction: 1};
  let rows = (window.emktCustomerRows || []).filter((row) => `${row.name} ${row.email} ${row.website}`.toLowerCase().includes(term));
  if (sort.field) rows.sort((left, right) => String(left[sort.field] || '').localeCompare(String(right[sort.field] || ''), 'vi', {numeric: true}) * sort.direction);
  const arrow = (field) => sort.field === field ? (sort.direction > 0 ? ' ▲' : ' ▼') : '';
  target.innerHTML = `<h3>Khách hàng trong list: ${emktEscape(list?.name || '')} (${rows.length})</h3><div class="customer-toolbar"><input id="emktCustomerSearch" type="search" placeholder="Tìm theo email..." value="${emktEscape(term)}" /><span>${rows.length}/${(window.emktCustomerRows || []).length}</span></div>${rows.length ? `<table class="campaign-table customer-table"><thead><tr><th><button type="button" class="sort-header" data-customer-sort="name">Khách hàng${arrow('name')}</button></th><th><button type="button" class="sort-header" data-customer-sort="email">Email${arrow('email')}</button></th><th><button type="button" class="sort-header" data-customer-sort="website">Website${arrow('website')}</button></th><th>Blacklist / thao tác</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${emktEscape(row.name)}</td><td>${emktEscape(row.email || 'chưa có')}</td><td>${emktEscape(row.website)}</td><td><label class="customer-blacklist"><input type="checkbox" data-member-blacklist="${listId}:${row.id || ''}:${emktEscape(row.email || '')}" ${row.blacklisted ? 'checked' : ''} /> Không gửi</label>${row.manual ? '' : ` <button type="button" class="danger-button" data-member-delete="${listId}:${row.id}">Xóa khỏi list</button>`}</td></tr>`).join('')}</tbody></table>` : '<p>Không tìm thấy khách hàng.</p>'}`;
}

async function loadEmktAccounts() {
  const accounts = await (await fetch('/api/emkt/accounts')).json();
  window.emktAccounts = accounts;
  const select = document.getElementById('emktAccountSelect');
  select.innerHTML = '<option value="">Chọn tài khoản gửi</option>';
  accounts.forEach((account) => {
    const option = document.createElement('option'); option.value = account.id; option.textContent = `${account.name} — ${account.from_email}`; select.appendChild(option);
  });
  document.getElementById('emktAccounts').innerHTML = accounts.length ? accounts.map((account) => `<div class="emkt-account"><strong>${emktEscape(account.name)}</strong> · ${emktEscape(account.provider || 'ses')} · ${emktEscape(account.smtp_host)}:${account.smtp_port} (${emktEscape(account.smtp_security)}) · gửi từ ${emktEscape(account.from_email)} <button type="button" data-emkt-edit="${account.id}">Sửa</button><button type="button" data-emkt-test="${account.id}">Kiểm tra</button><button type="button" class="danger-button" data-emkt-delete="${account.id}">Xóa</button></div>`).join('') : '<p>Chưa có tài khoản gửi email.</p>';
}

async function loadEmktCampaigns() {
  const campaigns = await (await fetch('/api/emkt/campaigns')).json();
  window.emktCampaigns = campaigns;
  renderEmktCampaigns(campaigns);
  await loadEmktStats();
}

async function loadEmktStats() {
  const period = document.getElementById('emktStatsPeriod')?.value || 'all';
  const params = new URLSearchParams({period});
  if (period === 'custom') { params.set('start', document.getElementById('emktStatsStart').value); params.set('end', document.getElementById('emktStatsEnd').value); }
  const stats = await (await fetch(`/api/emkt/stats?${params}`)).json();
  const metric = (label, value, rate = '') => `<div class="emkt-stat-card">${label}<strong>${Number(value || 0).toLocaleString('vi-VN')}</strong>${rate ? `<small>${rate}</small>` : ''}</div>`;
  document.getElementById('emktStats').innerHTML = `<div class="emkt-stats-grid">${metric('Campaign', stats.campaigns)}${metric('Tổng email', stats.total)}${metric('Đã gửi', stats.sent)}${metric('Đã đến', stats.delivered, `Tỷ lệ: ${stats.delivery_rate}%`)}${metric('Đã mở', stats.opened, `Tỷ lệ: ${stats.open_rate}%`)}${metric('Đã click', stats.clicked, `Tỷ lệ: ${stats.click_rate}%`)}${metric('Bounce', stats.bounced, `Tỷ lệ: ${stats.bounce_rate}%`)}${metric('Complaint', stats.complained)}${metric('Thất bại', stats.failed)}${metric('Đang chờ', stats.pending)}</div><h3>Chi tiết theo campaign</h3>${stats.campaign_rows.length ? `<div class="campaign-table-wrap"><table class="campaign-table stats-table"><thead><tr><th>Campaign</th><th>Tổng</th><th>Gửi</th><th>Đến</th><th>Mở</th><th>Click</th><th>Bounce</th><th>Complaint</th><th>Lỗi</th></tr></thead><tbody>${stats.campaign_rows.map((row) => `<tr><td>${emktEscape(row.name)}</td><td>${row.total}</td><td>${row.sent}</td><td>${row.delivered}</td><td>${row.opened}</td><td>${row.clicked}</td><td>${row.bounced}</td><td>${row.complained}</td><td>${row.failed}</td></tr>`).join('')}</tbody></table></div>` : '<p>Không có dữ liệu trong khoảng thời gian này.</p>'}`;
}

function campaignDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString('vi-VN', {dateStyle: 'medium', timeStyle: 'short'});
}

function renderEmktCampaigns(campaigns) {
  const target = document.getElementById('emktCampaigns');
  const pageSize = 10;
  const totalPages = Math.max(1, Math.ceil(campaigns.length / pageSize));
  const requestedPage = Number.isFinite(Number(window.emktCampaignPage)) ? Number(window.emktCampaignPage) : 1;
  const page = Math.max(1, Math.min(requestedPage, totalPages));
  window.emktCampaignPage = page;
  const pageRows = campaigns.slice((page - 1) * pageSize, page * pageSize);
  document.getElementById('emktCampaignCount').textContent = campaigns.length;
  document.getElementById('emktCampaignPage').textContent = page;
  document.getElementById('emktCampaignPrev').disabled = page <= 1;
  document.getElementById('emktCampaignNext').disabled = page >= totalPages;
  target.innerHTML = campaigns.length ? `<div class="campaign-table-wrap"><table class="campaign-table"><thead><tr><th>Status</th><th>Name</th><th>Lists</th><th>SES</th><th>Timestamps</th><th>Stats</th><th></th></tr></thead><tbody>${pageRows.map((campaign) => { const names = (campaign.list_ids || []).map((id) => (window.emktLists || []).find((list) => list.id === id)?.name).filter(Boolean); const listLabel = names.length ? names.join(', ') : (campaign.country_filter || campaign.industry_filter ? 'Bộ lọc cũ' : 'Chưa chọn list'); return `<tr><td><span class="campaign-status ${emktEscape(campaign.status)}">${emktEscape(campaign.status)}</span></td><td><div class="campaign-name">${emktEscape(campaign.name)}</div><div class="campaign-subject">${emktEscape(campaign.subject)}</div></td><td>• ${emktEscape(listLabel)}</td><td>${emktEscape(campaign.account_name || 'Chưa xác định')}</td><td><b>Created</b> ${campaignDate(campaign.created_at)}<br><b>Started</b> ${campaignDate(campaign.started_at)}<br><b>Ended</b> ${campaignDate(campaign.completed_at)}</td><td><b>Sent</b> ${campaign.sent} / ${campaign.total}<br><b>Failed</b> ${campaign.failed}<br><b>Pending</b> ${campaign.pending}</td><td class="campaign-actions"><button type="button" data-emkt-edit="${campaign.id}" ${['sending','queued'].includes(campaign.status) ? 'disabled' : ''}>Sửa</button><button type="button" data-emkt-history="${campaign.id}">History</button><button type="button" data-emkt-recipients="${campaign.id}">▣</button><button type="button" data-emkt-run="${campaign.id}" ${['sending','queued'].includes(campaign.status) ? 'disabled' : ''}>▶</button><button type="button" class="danger-button" data-emkt-stop="${campaign.id}" ${campaign.status === 'sending' ? '' : 'disabled'}>■</button><button type="button" class="danger-button" data-emkt-delete-campaign="${campaign.id}" ${['sending','queued'].includes(campaign.status) ? 'disabled' : ''}>Xóa</button></td></tr>`; }).join('')}</tbody></table></div>` : '<p>Chưa có chiến dịch.</p>';
}

async function showCampaignHistory(campaignId) {
  const body = document.getElementById('emktHistoryBody');
  body.textContent = 'Đang tải...';
  document.getElementById('emktHistoryModal').hidden = false;
  const rows = await (await fetch(`/api/emkt/campaigns/${campaignId}/history`)).json();
  body.innerHTML = rows.length ? `<table class="campaign-table emkt-history-table"><thead><tr><th>Lần / trạng thái</th><th>Thời gian</th><th>Kết quả</th></tr></thead><tbody>${rows.map((row, index) => `<tr><td><strong>Lần ${rows.length - index}</strong><br><span class="campaign-status ${emktEscape(row.status)}">${emktEscape(row.status)}</span></td><td><b>Bắt đầu:</b> ${campaignDate(row.started_at)}<br><b>Kết thúc:</b> ${campaignDate(row.completed_at)}</td><td><b>Tổng:</b> ${row.total}<br><b>Thành công:</b> ${row.sent}<br><b>Thất bại:</b> ${row.failed}<br><b>Chờ:</b> ${row.pending}</td></tr>`).join('')}</tbody></table>` : '<p>Campaign chưa có lần gửi nào.</p>';
}

async function editEmktCampaign(campaignId) {
  const campaign = await (await fetch(`/api/emkt/campaigns/${campaignId}`)).json();
  const form = document.getElementById('emktCampaignForm');
  form.dataset.editId = campaignId;
  form.elements.name.value = campaign.name || '';
  form.elements.account_id.value = campaign.account_id || '';
  form.elements.subject.value = campaign.subject || '';
  form.elements.scheduled_at.value = campaign.scheduled_at ? new Date(campaign.scheduled_at).toISOString().slice(0, 16) : '';
  form.elements.html_body.value = campaign.html_body || '';
  form.elements.text_body.value = campaign.text_body || '';
  form.querySelectorAll('input[name="list_ids"]').forEach((input) => { input.checked = (campaign.list_ids || []).includes(Number(input.value)); });
  document.getElementById('emktCampaignStatus').textContent = `Đang sửa campaign #${campaignId}`;
  form.hidden = false; form.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function renderCampaignListOptions() {
  const target = document.getElementById('emktCampaignListOptions');
  if (!target) return;
  const lists = window.emktLists || [];
  target.innerHTML = lists.length ? lists.map((list) => `<label><input type="checkbox" name="list_ids" value="${list.id}" /> <span>${emktEscape(list.name)}</span><small>${Number(list.customer_count || 0).toLocaleString('vi-VN')} email</small></label>`).join('') : '<span>Chưa có list. Hãy tạo list trước.</span>';
}

async function loadEmkt() {
  try {
    await Promise.all([loadEmktAccounts(), loadEmktList()]);
    renderCampaignListOptions();
  } catch (error) {
    document.getElementById('emktAccountStatus').textContent = `eMKT lỗi tải tài khoản/list: ${error.message}`;
  }
  try {
    const [countries, industries, facetCounts] = await Promise.all([(await fetch('/api/countries')).json(), (await fetch('/api/industries')).json(), (await fetch('/api/emkt/lists/facet-counts')).json()]);
    document.getElementById('emktListCountry').innerHTML = '<option value="">Tất cả quốc gia</option>';
    document.getElementById('emktListIndustry').innerHTML = '<option value="">Tất cả ngành</option>';
    countries.forEach((value) => document.getElementById('emktListCountry').insertAdjacentHTML('beforeend', `<option value="${emktEscape(value)}">${emktEscape(COUNTRY_NAMES[value] || value)} (${facetCounts.countries[value] || 0})</option>`));
    buildIndustrySelectOptions(document.getElementById('emktListIndustry'), industries, facetCounts.industries);
    buildMultiOptions('emktNewListCountryOptions', 'country_filter', countries, (value) => COUNTRY_NAMES[value] || value, facetCounts.countries);
    buildIndustryGroupOptions('emktNewListIndustryOptions', 'industry_filter', industries, facetCounts.industries);
    await loadEmktCampaigns();
  } catch (error) { document.getElementById('emktAccountStatus').textContent += ` eMKT lỗi tải bộ lọc: ${error.message}`; }
}

function buildMultiOptions(containerId, fieldName, values, labeler, counts = {}) {
  const target = document.getElementById(containerId);
  target.innerHTML = values.map((value) => `<label><input type="checkbox" data-multi-field="${fieldName}" value="${emktEscape(value)}" /> <span>${emktEscape(labeler(value))}</span><small>${counts[value] || 0}</small></label>`).join('');
  target.querySelectorAll('input').forEach((input) => input.addEventListener('change', () => syncMultiOptions(fieldName)));
}
function getIndustryGroups(values, counts = {}) {
  const used = new Set();
  return INDUSTRY_GROUPS.map(([label, terms]) => {
    const groupValues = values.filter((value) => {
      const match = terms.length ? terms.some((term) => value.toLowerCase().includes(term)) : true;
      if (match && !used.has(value)) { used.add(value); return true; }
      return false;
    });
    return {label, values: groupValues, count: groupValues.reduce((sum, value) => sum + (counts[value] || 0), 0)};
  });
}
function buildIndustrySelectOptions(select, values, counts) {
  const groups = getIndustryGroups(values, counts);
  select.insertAdjacentHTML('beforeend', groups.map((group) => `<option value="${emktEscape(group.values.join(','))}" ${group.values.length ? '' : 'disabled'}>${emktEscape(group.label)} (${group.count})</option>`).join(''));
}
function buildIndustryGroupOptions(containerId, fieldName, values, counts) {
  const groups = getIndustryGroups(values, counts);
  const target = document.getElementById(containerId);
  target.innerHTML = groups.map((group) => `<label class="${group.values.length ? '' : 'muted'}"><input type="checkbox" data-multi-field="${fieldName}" value="${emktEscape(group.values.join(','))}" ${group.values.length ? '' : 'disabled'} /> <span>${emktEscape(group.label)}</span><small>${group.count}</small></label>`).join('');
  target.querySelectorAll('input').forEach((input) => input.addEventListener('change', () => syncMultiOptions(fieldName)));
}
async function updateContactNewListCount() {
  const target = document.getElementById("contactNewListCount");
  if (!target) return;
  const params = new URLSearchParams({
    country_filter: document.getElementById("contactNewListCountry")?.value || "",
    industry_filter: document.getElementById("contactNewListIndustry")?.value || "",
  });
  target.textContent = "Đang tính số khách hàng...";
  try {
    const response = await fetch(`/api/contact-campaign/selection-count?${params}`);
    const data = await response.json();
    target.textContent = `Khách hàng: ${Number(data.count || 0).toLocaleString("vi-VN")}`;
  } catch (error) {
    target.textContent = "Khách hàng: 0";
  }
}

function syncMultiOptions(fieldName) {
  const values = [...document.querySelectorAll(`input[data-multi-field="${fieldName}"]:checked`)].map((input) => input.value);
  const prefix = fieldName.startsWith('contact_') ? 'contactNewList' : 'emktNewList';
  const suffix = fieldName.includes('country') ? 'Country' : 'Industry';
  document.getElementById(`${prefix}${suffix}`).value = values.join(',');
  if (!fieldName.startsWith('contact_')) previewNewList();
  else updateContactNewListCount();
}

setInterval(() => {
  if (!document.getElementById('emktTab').hidden) loadEmktCampaigns();
}, 5000);

document.getElementById('emktStatsPeriod').addEventListener('change', (event) => {
  const custom = event.target.value === 'custom';
  document.getElementById('emktStatsStart').disabled = !custom;
  document.getElementById('emktStatsEnd').disabled = !custom;
});
document.getElementById('emktStatsApply').addEventListener('click', loadEmktStats);

async function saveEmktAccountFromModal() {
  const form = document.getElementById('emktAccountForm');
  const values = Object.fromEntries(new FormData(form));
  const payload = {};
  ['name', 'provider', 'smtp_host', 'smtp_port', 'smtp_security', 'smtp_username', 'smtp_password', 'from_email', 'from_name', 'configuration_set', 'region', 'access_key_id', 'secret_access_key'].forEach((key) => { payload[key] = values[key] || ''; });
  const editId = form.dataset.editId || '';
  const response = await fetch(editId ? `/api/emkt/accounts/${editId}` : '/api/emkt/accounts', {method: editId ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || 'Không lưu được tài khoản SES.');
  form.dataset.accountId = body.id;
  await loadEmktAccounts();
  return body.id;
}

function applyEmailProviderPreset(provider) {
  const form = document.getElementById('emktAccountForm');
  const presets = {
    google: {host: 'smtp.gmail.com', port: 465, security: 'ssl'},
    zoho: {host: 'smtp.zoho.com', port: 465, security: 'ssl'},
    ses: {host: 'email-smtp.us-east-1.amazonaws.com', port: 465, security: 'ssl'},
  };
  const preset = presets[provider];
  if (!preset) return;
  form.elements.smtp_host.value = preset.host;
  form.elements.smtp_port.value = preset.port;
  form.elements.smtp_security.value = preset.security;
}

document.getElementById('openEmktAccountBtn').addEventListener('click', () => {
  const form = document.getElementById('emktAccountForm'); form.reset(); form.elements.provider.value = 'ses'; delete form.dataset.editId;
  document.getElementById('emktAccountModal').hidden = false;
  document.getElementById('emktAccountModalStatus').textContent = '';
});
document.getElementById('emktAccountForm').elements.provider.addEventListener('change', (event) => {
  applyEmailProviderPreset(event.target.value);
});
document.getElementById('closeEmktAccountModal').addEventListener('click', () => { document.getElementById('emktAccountModal').hidden = true; });
document.getElementById('emktAccountForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const status = document.getElementById('emktAccountModalStatus');
  try {
    await saveEmktAccountFromModal();
    document.getElementById('emktAccountModal').hidden = true;
  } catch (error) { status.textContent = error.message; }
});
document.getElementById('testEmktAccountBtn').addEventListener('click', async () => {
  const form = document.getElementById('emktAccountForm'); const values = Object.fromEntries(new FormData(form)); const status = document.getElementById('emktAccountModalStatus');
  if (!values.test_to_email) { status.textContent = 'Nhập email nhận thử trước.'; return; }
  const button = document.getElementById('testEmktAccountBtn'); button.disabled = true;
  try {
    const accountId = form.dataset.accountId || await saveEmktAccountFromModal();
    const response = await fetch(`/api/emkt/accounts/${accountId}/send-test`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({to_email: values.test_to_email, subject: 'Email kiểm tra SMTP AWS SES', body: 'Đây là email kiểm tra kết nối SMTP AWS SES.'})});
    const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Gửi thử thất bại.');
    status.textContent = `Đã gửi thử tới ${body.to_email}. Message ID: ${body.message_id}`;
  } catch (error) { status.textContent = error.message; } finally { button.disabled = false; }
});

document.getElementById('emktAccounts').addEventListener('click', async (event) => {
  const editId = event.target.dataset.emktEdit;
  if (editId) {
    const account = (window.emktAccounts || []).find(item => item.id === Number(editId));
    if (!account) return;
    const form = document.getElementById('emktAccountForm'); form.dataset.editId = editId;
    form.elements.name.value = account.name; form.elements.provider.value = account.provider || 'ses'; form.elements.smtp_host.value = account.smtp_host; form.elements.smtp_port.value = account.smtp_port; form.elements.smtp_security.value = account.smtp_security; form.elements.from_email.value = account.from_email; form.elements.from_name.value = account.from_name || ''; form.elements.configuration_set.value = account.configuration_set || '';
    form.elements.region.value = account.region || 'us-west-2'; form.elements.access_key_id.value = account.access_key_id || ''; form.elements.secret_access_key.value = ''; form.elements.smtp_username.value = account.smtp_username || ''; form.elements.smtp_password.value = '';
    document.querySelector('#emktAccountModal h2').textContent = 'Sửa tài khoản gửi email';
    document.getElementById('emktAccountModal').hidden = false; document.getElementById('emktAccountModalStatus').textContent = 'Nhập IAM credentials để gửi qua SES API; để trống secret khi không đổi.';
    return;
  }
  const testId = event.target.dataset.emktTest;
  const deleteId = event.target.dataset.emktDelete;
  if (testId) {
    event.target.disabled = true;
    const response = await fetch(`/api/emkt/accounts/${testId}/test`, {method: 'POST'}); const body = await response.json();
    alert(response.ok ? `SMTP OK — ${body.host}:${body.port} (${body.security})` : (body.detail || 'Kiểm tra SMTP thất bại.')); event.target.disabled = false;
  }
  if (deleteId && confirm('Xóa cấu hình tài khoản SES này?')) {
    const response = await fetch(`/api/emkt/accounts/${deleteId}`, {method: 'DELETE'}); const body = await response.json();
    if (!response.ok) alert(body.detail || 'Không thể xóa.'); else await loadEmktAccounts();
  }
});

document.getElementById('emktCampaignForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const status = document.getElementById('emktCampaignStatus');
  const values = Object.fromEntries(new FormData(event.target));
  values.list_ids = [...event.target.querySelectorAll('input[name="list_ids"]:checked')].map((input) => Number(input.value));
  if (!values.list_ids.length) { status.textContent = 'Hãy chọn ít nhất một list.'; return; }
  values.account_id = Number(values.account_id); values.recipient_limit = 50000;
  const editId = event.target.dataset.editId;
  const response = await fetch(editId ? `/api/emkt/campaigns/${editId}` : '/api/emkt/campaigns', {method: editId ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(values)}); const body = await response.json();
  status.textContent = response.ok ? `Đã lưu chiến dịch #${body.id}.` : (body.detail || 'Không lưu được chiến dịch.');
  if (response.ok) { event.target.hidden = true; delete event.target.dataset.editId; await loadEmktCampaigns(); }
});

document.getElementById('openNewCampaignBtn').addEventListener('click', () => {
  const form = document.getElementById('emktCampaignForm');
  delete form.dataset.editId; form.reset(); renderCampaignListOptions();
  form.hidden = false;
  form.scrollIntoView({behavior: 'smooth', block: 'start'});
});
document.querySelectorAll('.emkt-subtab').forEach((button) => button.addEventListener('click', () => {
  const selected = button.dataset.emktTab;
  document.querySelectorAll('.emkt-subtab').forEach((item) => item.classList.toggle('active', item === button));
  document.querySelectorAll('.emkt-subpanel').forEach((panel) => { panel.hidden = panel.dataset.emktPanel !== selected; });
}));
document.getElementById('emktListLoadBtn').addEventListener('click', loadEmktList);
document.getElementById('openNewListBtn').addEventListener('click', () => { const form = document.getElementById('emktListForm'); form.reset(); delete form.dataset.editId; document.getElementById('emktListModal').hidden = false; document.getElementById('emktListModalStatus').textContent = ''; });
document.getElementById('closeEmktListModal').addEventListener('click', () => { document.getElementById('emktListModal').hidden = true; });
document.getElementById('emktListForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const status = document.getElementById('emktListModalStatus');
  status.textContent = 'Đang lưu...';
  try {
    const values = Object.fromEntries(new FormData(event.target));
    values.blacklist = Boolean(values.blacklist);
    const editId = event.target.dataset.editId;
    values.query_filter = '';
    const response = await fetch(editId ? `/api/emkt/lists/${editId}` : '/api/emkt/lists', {method: editId ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(values)});
    const body = await response.json();
    if (!response.ok) { status.textContent = body.detail || 'Không tạo được list.'; return; }
    event.target.reset(); delete event.target.dataset.editId; document.getElementById('emktListModal').hidden = true; await loadEmktList();
  } catch (error) { status.textContent = `Không thể lưu list: ${error.message}`; }
});
function restoreMultiOptions(fieldName, value) {
  const selected = new Set(String(value || '').split(',').map((item) => item.trim()).filter(Boolean));
  document.querySelectorAll(`input[data-multi-field="${fieldName}"]`).forEach((input) => {
    input.checked = input.value.split(',').some((item) => selected.has(item.trim()));
  });
}
async function previewNewList() {
  const form = document.getElementById('emktListForm');
  const params = new URLSearchParams({country_filter: form.elements.country_filter.value, industry_filter: form.elements.industry_filter.value, manual_emails: form.elements.manual_emails.value});
  try {
    const response = await fetch(`/api/emkt/lists/preview?${params}`);
    const result = await response.json();
    document.getElementById('emktListPreview').textContent = `Khách hàng có email hợp lệ: ${result.valid_email_customers}`;
  } catch (error) { document.getElementById('emktListPreview').textContent = 'Không thể tính số khách hàng.'; }
}
document.getElementById('emktNewListCountry').addEventListener('change', previewNewList);
document.getElementById('emktNewListIndustry').addEventListener('change', previewNewList);
document.getElementById('emktListForm').elements.manual_emails.addEventListener('input', previewNewList);
document.getElementById('emktListCustomers').addEventListener('click', async (event) => {
  const openId = event.target.dataset.listOpen;
  const editId = event.target.dataset.listEdit;
  const deleteId = event.target.dataset.listDelete;
  const customerSort = event.target.dataset.customerSort;
  const memberBlacklist = event.target.dataset.memberBlacklist;
  const memberDelete = event.target.dataset.memberDelete;
  if (openId) await showEmktListCustomers(openId);
  if (editId) {
    const item = (window.emktLists || []).find((row) => row.id === Number(editId));
    if (!item) return;
    const form = document.getElementById('emktListForm'); form.dataset.editId = editId; form.elements.name.value = item.name; form.elements.blacklist.checked = Boolean(item.blacklist); form.elements.manual_emails.value = item.manual_emails || ''; form.elements.country_filter.value = item.country_filter || ''; form.elements.industry_filter.value = item.industry_filter || ''; restoreMultiOptions('country_filter', item.country_filter); restoreMultiOptions('industry_filter', item.industry_filter); document.getElementById('emktListModal').hidden = false; document.getElementById('emktListModalStatus').textContent = ''; previewNewList();
  }
  if (deleteId && confirm('Xóa list này? Dữ liệu trong bảng company không bị xóa.')) { await fetch(`/api/emkt/lists/${deleteId}`, {method: 'DELETE'}); await loadEmktList(); }
  if (customerSort) { const sort = window.emktCustomerSort || {field: '', direction: 1}; window.emktCustomerSort = {field: customerSort, direction: sort.field === customerSort ? -sort.direction : 1}; renderEmktListCustomers((window.emktLists || []).find((row) => row.id === window.emktCustomerListId)); }
  if (memberBlacklist) {
    const [targetListId, companyId, email] = memberBlacklist.split(':');
    const checked = event.target.checked;
    if (companyId) {
      const response = await fetch(`/api/emkt/lists/${targetListId}/customers/${companyId}/blacklist`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({blacklisted: checked})});
      if (!response.ok) event.target.checked = !checked;
    } else {
      const list = (window.emktLists || []).find((row) => row.id === Number(targetListId));
      const blocked = new Set(String(list?.blacklist_emails || '').split(',').map((item) => item.trim().toLowerCase()).filter(Boolean));
      checked ? blocked.add(email.toLowerCase()) : blocked.delete(email.toLowerCase());
      const response = await fetch(`/api/emkt/lists/${targetListId}`, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...list, blacklist_emails: [...blocked].join(',')})});
      if (response.ok) { list.blacklist_emails = [...blocked].join(','); } else event.target.checked = !checked;
    }
    const row = (window.emktCustomerRows || []).find((item) => (companyId && String(item.id) === companyId) || (!companyId && item.email.toLowerCase() === email.toLowerCase()));
    if (row) row.blacklisted = checked;
  }
  if (memberDelete && confirm('Xóa khách hàng khỏi list này? Dữ liệu bảng company không bị xóa.')) {
    const [targetListId, companyId] = memberDelete.split(':');
    const response = await fetch(`/api/emkt/lists/${targetListId}/customers/${companyId}`, {method: 'DELETE'});
    if (response.ok) { await loadEmktList(); await showEmktListCustomers(targetListId); }
  }
});
document.getElementById('emktListCustomers').addEventListener('input', (event) => {
  if (event.target.id === 'emktCustomerSearch') renderEmktListCustomers((window.emktLists || []).find((row) => row.id === window.emktCustomerListId));
});
document.getElementById('emktCampaignSearchBtn').addEventListener('click', () => {
  const term = document.getElementById('emktCampaignSearch').value.trim().toLowerCase();
  renderEmktCampaigns((window.emktCampaigns || []).filter((campaign) => `${campaign.name} ${campaign.subject}`.toLowerCase().includes(term)));
});
document.getElementById('emktCampaignSearch').addEventListener('keydown', (event) => {
  if (event.key === 'Enter') document.getElementById('emktCampaignSearchBtn').click();
});
document.getElementById('emktCampaignPrev').addEventListener('click', () => { window.emktCampaignPage = Math.max(1, (window.emktCampaignPage || 1) - 1); renderEmktCampaigns(window.emktCampaigns || []); });
document.getElementById('emktCampaignNext').addEventListener('click', () => { window.emktCampaignPage = (window.emktCampaignPage || 1) + 1; renderEmktCampaigns(window.emktCampaigns || []); });

document.getElementById('emktPreviewBtn').addEventListener('click', () => {
  const values = Object.fromEntries(new FormData(document.getElementById('emktCampaignForm')));
  const preview = document.getElementById('emktPreviewModalBody');
  const htmlBody = (values.html_body || '').replaceAll('{{company_name}}', 'Công ty mẫu').replaceAll('{{website}}', 'https://example.com/');
  preview.innerHTML = htmlBody ? `<iframe sandbox="" title="Email preview" style="width:100%;min-height:360px;border:0" srcdoc="${emktEscape(htmlBody).replaceAll('&#x27;', '&apos;')}"></iframe>` : `<pre>${emktEscape(values.text_body || 'Chưa có nội dung.')}</pre>`;
  document.getElementById('emktPreviewModal').hidden = false;
});
document.getElementById('closeEmktPreviewModal').addEventListener('click', () => { document.getElementById('emktPreviewModal').hidden = true; });
document.getElementById('closeEmktHistoryModal').addEventListener('click', () => { document.getElementById('emktHistoryModal').hidden = true; });
document.getElementById('emktHistoryModal').addEventListener('click', (event) => {
  if (event.target.id === 'emktHistoryModal') event.currentTarget.hidden = true;
});

document.getElementById('emktCampaigns').addEventListener('click', async (event) => {
  const editId = event.target.dataset.emktEdit;
  const deleteCampaignId = event.target.dataset.emktDeleteCampaign;
  const historyId = event.target.dataset.emktHistory;
  const previewId = event.target.dataset.emktRecipients;
  const runId = event.target.dataset.emktRun;
  const stopId = event.target.dataset.emktStop;
  if (editId) { await editEmktCampaign(editId); return; }
  if (deleteCampaignId && confirm('Xóa campaign này và toàn bộ lịch sử người nhận?')) {
    const response = await fetch(`/api/emkt/campaigns/${deleteCampaignId}`, {method: 'DELETE'});
    const body = await response.json();
    if (!response.ok) alert(body.detail || 'Không thể xóa campaign.'); else await loadEmktCampaigns();
    return;
  }
  if (historyId) { await showCampaignHistory(historyId); return; }
  if (previewId) { const body = await (await fetch(`/api/emkt/campaigns/${previewId}/recipients-preview`)).json(); alert(`Có ${body.total} người nhận hợp lệ.\n\n${body.sample.map((row) => `${row.email} — ${row.company_name}`).join('\n')}`); }
  if (runId && confirm('Tôi xác nhận có quyền gửi email tới danh sách đã lọc và muốn bắt đầu chiến dịch.')) { const response = await fetch(`/api/emkt/campaigns/${runId}/start`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({confirm: true})}); const body = await response.json(); if (!response.ok) alert(body.detail || 'Không thể chạy chiến dịch.'); await loadEmktCampaigns(); }
  if (stopId) { await fetch(`/api/emkt/campaigns/${stopId}/stop`, {method: 'POST'}); await loadEmktCampaigns(); }
});

async function initDropdowns() {
  const tableCountryFilterEl = document.getElementById('tableCountryFilter');
  const tableIndustryFilterEl = document.getElementById('tableIndustryFilter');

  const crawlCountries = Object.keys(REGION_BY_COUNTRY);
  let countries = [];
  try {
    countries = await (await fetch('/api/countries')).json();
  } catch (error) {
    countries = crawlCountries;
  }
  setOptions(tableCountryFilterEl, countries, 'Lọc theo quốc gia');
  [...tableCountryFilterEl.options].forEach((option) => {
    if (option.value && COUNTRY_NAMES[option.value]) option.textContent = COUNTRY_NAMES[option.value];
  });
  try {
    setOptions(tableIndustryFilterEl, await (await fetch('/api/industries')).json(), 'Lọc theo ngành');
  } catch (error) {
    setOptions(tableIndustryFilterEl, INDUSTRIES, 'Lọc theo ngành');
  }
}

async function fetchCompanies() {
  const q = document.getElementById('searchQ').value;
  const country = document.getElementById('tableCountryFilter').value;
  const industry = document.getElementById('tableIndustryFilter').value || document.getElementById('searchIndustry').value;

  const limit = document.getElementById('displayLimit').value;
  const params = new URLSearchParams({ q, country, industry, limit });
  const [res, countRes] = await Promise.all([
    fetch(`/api/companies?${params.toString()}`),
    fetch('/api/companies/count'),
  ]);
  displayedCompanies = await res.json();
  const {total} = await countRes.json();
  document.getElementById('tableTotal').textContent = `Tổng dữ liệu: ${Number(total).toLocaleString('vi-VN')}`;
  renderCompanies();
}

function renderCompanies() {
  let data = [...displayedCompanies];
  if (sortColumn) {
    const collator = new Intl.Collator('vi', { numeric: true, sensitivity: 'base' });
    data.sort((a, b) => sortDirection * collator.compare(String(a[sortColumn] || ''), String(b[sortColumn] || '')));
  }
  tableRows = data;
  renderVisibleRows();
  document.getElementById('tableCount').textContent = `Đang hiển thị ${data.length} dòng`;

  document.querySelectorAll('#companyTable thead th').forEach((th, index) => {
    const key = TABLE_COLUMNS[index];
    const label = TABLE_LABELS[key] || th.dataset.label || th.textContent.replace(/\s+[▲▼]$/, '');
    th.dataset.label = label;
    th.textContent = key && key === sortColumn ? `${label} ${sortDirection === 1 ? '▲' : '▼'}` : label;
    th.setAttribute('aria-sort', key && key === sortColumn ? (sortDirection === 1 ? 'ascending' : 'descending') : 'none');
  });
}

function renderVisibleRows() {
  const wrap = document.querySelector('.table-wrap');
  const tbody = document.querySelector('#companyTable tbody');
  const total = tableRows.length;
  const start = Math.max(0, Math.min(Math.floor(wrap.scrollTop / VIRTUAL_ROW_HEIGHT), Math.max(0, total - VIRTUAL_WINDOW)));
  const end = Math.min(total, start + VIRTUAL_WINDOW);

  tbody.innerHTML = '';
  if (start > 0) {
    const spacer = document.createElement('tr');
    spacer.innerHTML = `<td colspan="19" style="height:${start * VIRTUAL_ROW_HEIGHT}px;padding:0;border:0"></td>`;
    tbody.appendChild(spacer);
  }
  tableRows.slice(start, end).forEach((c, index) => {
    const tr = document.createElement('tr');
    const values = [
      start + index + 1,
      c.name, c.industry, c.country, c.address, c.city, c.state, c.website, c.contact, c.email, c.email_2, c.phone, c.short_description,
      c.facebook, c.facebook_alt, c.youtube, c.x, c.linkedin, c.truth,
    ];
    values.forEach((v, cellIndex) => {
      const td = document.createElement('td');
      td.dataset.companyId = c.id;
      td.dataset.field = TABLE_EDIT_FIELDS[cellIndex] || '';
      if (window.currentUser?.is_admin && td.dataset.field) {
        td.contentEditable = 'true';
        td.classList.add('admin-editable-cell');
      }
      td.textContent = v || '';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  if (end < total) {
    const spacer = document.createElement('tr');
    spacer.innerHTML = `<td colspan="19" style="height:${(total - end) * VIRTUAL_ROW_HEIGHT}px;padding:0;border:0"></td>`;
    tbody.appendChild(spacer);
  }
}

document.querySelector('#companyTable tbody').addEventListener('focusout', async (event) => {
  const cell = event.target.closest('.admin-editable-cell');
  if (!cell || !window.currentUser?.is_admin) return;
  const row = tableRows.find(item => item.id === Number(cell.dataset.companyId));
  const value = cell.textContent.trim();
  if (!row || String(row[cell.dataset.field] || '') === value) return;
  const response = await fetch(`/api/companies/${cell.dataset.companyId}`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({field: cell.dataset.field, value})});
  if (!response.ok) { cell.textContent = row[cell.dataset.field] || ''; window.alert('Không lưu được dữ liệu.'); return; }
  row[cell.dataset.field] = value;
});

function initTableSort() {
  document.querySelectorAll('#companyTable thead th').forEach((th, index) => {
    th.title = 'Click để sắp xếp';
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const key = TABLE_COLUMNS[index];
      if (!key) return;
      if (sortColumn === key) sortDirection *= -1;
      else { sortColumn = key; sortDirection = 1; }
      renderCompanies();
    });
  });
  document.querySelector('.table-wrap').addEventListener('scroll', () => window.requestAnimationFrame(renderVisibleRows));
}

async function runCrawl() {
  const crawlBtn = document.getElementById('crawlBtn');
  const progressEl = document.getElementById('crawlProgress');
  const resultEl = document.getElementById('crawlResult');

  const body = {
    query: document.getElementById('query').value,
    country: document.getElementById('country').value,
    region: document.getElementById('region')?.value || '',
    industry: document.getElementById('industry').value,
    max_companies: Number(document.getElementById('max_companies').value || -1),
  };

  crawlBtn.disabled = true;
  crawlBtn.textContent = 'Running...';
  resultEl.textContent = '';
  progressEl.textContent = 'Đang bắt đầu crawl...';

  try {
    const res = await fetch('/api/crawl/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        const evt = JSON.parse(line);

        if (evt.type === 'progress') {
          if (evt.stage === 'connector') {
            progressEl.textContent = `Đang lấy dữ liệu: ${evt.collected} doanh nghiệp (nguồn: ${evt.connector}, batch: ${evt.last_batch})`;
          } else if (evt.stage === 'normalize') {
            progressEl.textContent = `Đang chuẩn hóa dữ liệu: ${evt.normalized}/${evt.collected}`;
          } else if (evt.stage === 'postprocess') {
            progressEl.textContent = `Đang lọc trùng/hợp nhất: final ${evt.final}`;
          }
        }

        if (evt.type === 'done') {
          resultEl.textContent = `Fetched: ${evt.fetched}, SkippedVisited: ${evt.skipped_visited}, Eligible: ${evt.eligible}, Inserted: ${evt.inserted}`;
          progressEl.textContent = 'Hoàn tất crawl.';
        }
      }
    }
  } catch (error) {
    progressEl.textContent = `Crawl lỗi: ${error}`;
  } finally {
    crawlBtn.disabled = false;
    crawlBtn.textContent = 'Run Crawl';
  }

  await fetchCompanies();
}

async function importFile() {
  const fileInput = document.getElementById('importFile');
  if (!fileInput.files.length) return;

  const fd = new FormData();
  fd.append('file', fileInput.files[0]);

  const res = await fetch('/api/import', { method: 'POST', body: fd });
  const result = await res.json();
  alert(`Imported ${result.inserted}/${result.rows}`);
  await fetchCompanies();
}

async function clearData() {
  if (!confirm('Xóa toàn bộ dữ liệu companies và lịch sử visited?')) return;
  const res = await fetch('/api/companies', { method: 'DELETE' });
  const result = await res.json();
  alert(`Deleted companies: ${result.deleted_companies}, visited: ${result.deleted_visited}`);
  await fetchCompanies();
}

let contactScenarioEditingId = null;
function parseScenarioFields(value) {
  return Object.fromEntries(value.split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => { const i = line.indexOf('='); return i > 0 ? [line.slice(0, i).trim(), line.slice(i + 1).trim()] : ['', '']; }).filter(([key]) => key));
}
async function loadContactCampaign() {
  const [scenarios, lists, runs] = await Promise.all([
    fetch('/api/contact-campaign/scenarios').then(r => r.json()), fetch('/api/contact-campaign/lists').then(r => r.json()), fetch('/api/contact-campaign/runs').then(r => r.json())
  ]);
  window.contactScenarios = scenarios; window.contactLists = lists;
  if (document.getElementById('contactListCountryFilter')?.options.length === 1) { const [countries, industries, facets] = await Promise.all([fetch('/api/countries').then(r => r.json()), fetch('/api/industries').then(r => r.json()), fetch('/api/contact-campaign/facets').then(r => r.json())]); document.getElementById('contactListCountryFilter').innerHTML = '<option value="">Tất cả quốc gia</option>' + countries.map(x => `<option value="${emktEscape(x)}">${emktEscape(COUNTRY_NAMES[x] || x)}</option>`).join(''); document.getElementById('contactListIndustryFilter').innerHTML = '<option value="">Tất cả ngành</option>' + industries.map(x => `<option value="${emktEscape(x)}">${emktEscape(x)}</option>`).join(''); if (!document.getElementById('contactNewListCountryOptions').innerHTML) { buildMultiOptions('contactNewListCountryOptions', 'contact_country_filter', countries, x => COUNTRY_NAMES[x] || x, facets.countries); buildIndustryGroupOptions('contactNewListIndustryOptions', 'contact_industry_filter', industries, facets.industries); updateContactNewListCount(); } }
  document.getElementById('contactScenarioSelect').innerHTML = '<option value="">Chọn kịch bản</option>' + scenarios.map(x => `<option value="${x.id}">${emktEscape(x.name)}</option>`).join('');
  document.getElementById('contactListOptions').innerHTML = lists.length ? lists.map(x => `<label><input type="checkbox" name="contact_list_ids" value="${x.id}" /> ${emktEscape(x.name)} <small>${x.customer_count} contact</small></label>`).join('') : '<span>Chưa có list contact.</span>';
  const countryFilter = document.getElementById('contactListCountryFilter')?.value || '';
  const industryFilter = document.getElementById('contactListIndustryFilter')?.value || '';
  const visibleLists = lists.filter(x => (!countryFilter || x.country_filter?.includes(countryFilter)) && (!industryFilter || x.industry_filter?.includes(industryFilter)));
  document.getElementById('contactLists').innerHTML = visibleLists.length ? `<table class="campaign-table"><thead><tr><th>List</th><th>Bộ lọc</th><th>Khách hàng</th><th>Thống kê / thao tác</th></tr></thead><tbody>${visibleLists.map(x => `<tr><td><button class="campaign-name list-open-btn" type="button" data-contact-list-open="${x.id}">${emktEscape(x.name)}</button></td><td>${emktEscape(x.country_filter || 'Tất cả quốc gia')}<br>${emktEscape(x.industry_filter || 'Tất cả ngành')}</td><td>${x.customer_count} contact hợp lệ</td><td><button type="button" data-contact-list-edit="${x.id}">Sửa</button> <button type="button" class="danger-button" data-contact-list-delete="${x.id}">Xóa</button></td></tr>`).join('')}</tbody></table><div id="contactSelectedListCustomers"></div>` : '<p>Chưa có list contact.</p>';
  document.getElementById('contactScenarios').innerHTML = scenarios.length ? `<table class="campaign-table"><thead><tr><th>Tên kịch bản</th><th>Trường gửi</th><th>Thao tác</th></tr></thead><tbody>${scenarios.map(x => `<tr><td>${emktEscape(x.name)}</td><td>${Object.keys(x.fields || {}).length}</td><td><button type="button" data-contact-scenario-edit="${x.id}">Sửa</button> <button type="button" class="danger-button" data-contact-scenario-delete="${x.id}">Xóa</button></td></tr>`).join('')}</tbody></table>` : '<p>Chưa có kịch bản.</p>';
  document.getElementById('contactHistory').innerHTML = runs.length ? `<table class="campaign-table contact-history-table"><thead><tr><th>Lần</th><th>Trạng thái</th><th>List</th><th>Kịch bản</th><th>Thời gian</th><th>Tổng</th><th>Thành công</th><th>Lỗi</th><th>Captcha</th></tr></thead><tbody>${runs.map(x => { const scenario = scenarios.find(item => item.id === x.scenario_id); const listNames = (x.list_ids || []).map(id => lists.find(item => item.id === id)?.name).filter(Boolean); return `<tr><td><button type="button" class="contact-run-link" data-contact-run-details="${x.id}">Lần ${x.id}</button></td><td>${emktEscape(x.status)}</td><td>${emktEscape(listNames.join(', ') || 'Không xác định')}</td><td>${emktEscape(scenario?.name || 'Không xác định')}</td><td>${campaignDate(x.started_at)}<br>${campaignDate(x.completed_at)}</td><td>${x.total}</td><td>${x.success}</td><td>${x.failed}</td><td>${x.captcha}</td></tr>`; }).join('')}</tbody></table>` : '<p>Chưa có lịch sử chạy.</p>';
}
async function showContactRunDetails(runId) {
  const modal = document.getElementById("contactRunDetailsModal");
  const summary = document.getElementById("contactRunDetailsSummary");
  const body = document.getElementById("contactRunDetailsBody");
  modal.hidden = false; body.textContent = "Đang tải...";
  const rows = await (await fetch(`/api/contact-campaign/run/${runId}/details`)).json();
  const counts = rows.reduce((acc, row) => { acc[row.status] = (acc[row.status] || 0) + 1; return acc; }, {});
  summary.innerHTML = `<div class="contact-detail-summary"><span>Tổng: ${rows.length}</span><span class="success">Thành công: ${counts.success || 0}</span><span class="failed">Thất bại: ${counts.failed || 0}</span><span class="captcha">CAPTCHA: ${counts.captcha || 0}</span></div>`;
  body.innerHTML = rows.length ? `<div class="campaign-table-wrap"><table class="campaign-table contact-details-table"><thead><tr><th>Công ty</th><th>Website</th><th>Trạng thái</th><th>Chi tiết</th><th>Thời gian</th></tr></thead><tbody>${rows.map(row => `<tr><td>${emktEscape(row.company_name)}</td><td>${emktEscape(row.website)}</td><td>${emktEscape(row.status)}</td><td>${emktEscape(row.message)}</td><td>${campaignDate(row.created_at)}</td></tr>`).join("")}</tbody></table></div>` : "Lần chạy này chưa lưu chi tiết từng website. Các lần chạy mới sẽ hiển thị đầy đủ.";
}
async function startContactCampaign() {
  const button = document.getElementById("startContactCampaignBtn");
  const stopButton = document.getElementById("stopContactCampaignBtn");
  const status = document.getElementById("contactCampaignStatus");
  const log = document.getElementById("contactRunLog");
  const scenarioId = Number(document.getElementById("contactScenarioSelect").value);
  const listIds = [...document.querySelectorAll("[name=contact_list_ids]:checked")].map(x => Number(x.value));
  if (!scenarioId || !listIds.length) { status.textContent = "Hãy chọn kịch bản và ít nhất một list."; return; }
  button.disabled = true; stopButton.disabled = false; log.textContent = "Đang khởi động...";
  const response = await fetch("/api/contact-campaign/run", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({scenario_id:scenarioId, list_ids:listIds})});
  const body = await response.json();
  if (!response.ok) { status.textContent = body.detail || "Không thể bắt đầu."; button.disabled = false; stopButton.disabled = true; return; }
  window.contactRunId = body.run_id;
  window.contactCampaignTimer = setInterval(async () => {
    const run = await (await fetch(`/api/contact-campaign/run/${body.run_id}`)).json();
    status.textContent = `Đang chạy: ${run.processed}/${run.total} · thành công ${run.success} · lỗi ${run.failed} · CAPTCHA ${run.captcha}`;
    document.getElementById("contactCurrentResult").textContent = `Thành công: ${run.success} · Lỗi: ${run.failed} · CAPTCHA: ${run.captcha}`;
    log.textContent = (run.logs || []).map(x => { const detail = `${x.company || "Không rõ công ty"} · website: ${x.website || "không có"} · ${x.message || x.status}`; return `[${x.progress || "?/?"}] [${x.time || ""}] ${detail}`; }).join("\n") || "Chưa có log.";
    log.scrollTop = log.scrollHeight;
    if (["completed", "failed", "stopped"].includes(run.status)) {
      clearInterval(window.contactCampaignTimer); button.disabled = false; stopButton.disabled = true;
      status.textContent = run.status === "completed" ? "Đã hoàn tất." : run.status === "stopped" ? "Đã dừng." : "Lần chạy bị lỗi.";
      await loadContactCampaign();
    }
  }, 1500);
}
function openContactScenario(id = null) { contactScenarioEditingId = id; const item = id ? window.contactScenarios.find(x => x.id === id) : null; const form = document.getElementById('contactScenarioForm'); form.reset(); form.elements.name.value = item?.name || ''; form.elements.description.value = item?.description || ''; form.elements.reference_website.value = item?.reference_website || ''; document.querySelectorAll('[data-scenario-field]').forEach(input => { input.value = item?.fields?.[input.dataset.scenarioField] || ''; }); const custom = Object.entries(item?.fields || {}).filter(([key]) => !['name','company','email','phone','subject','website','address','message'].includes(key)); form.elements.custom_fields.value = custom.map(([k,v]) => `${k}=${v}`).join('\n'); document.getElementById('contactScenarioModal').hidden = false; }
async function generateContactScenarioWithAI() { const form = document.getElementById('contactScenarioForm'); const status = document.getElementById('contactScenarioStatus'); const description = form.elements.description.value.trim(); if (!description) { status.textContent = 'Hãy nhập mô tả cho AI trước.'; return; } const button = document.getElementById('contactScenarioAiBtn'); button.disabled = true; status.textContent = 'AI đang tạo nội dung...'; try { const response = await fetch('/api/ai/contact-generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({description, reference_website: form.elements.reference_website.value.trim()})}); const raw = await response.text(); let body = {}; try { body = raw ? JSON.parse(raw) : {}; } catch { throw new Error(`Server trả về dữ liệu không hợp lệ (HTTP ${response.status}). Hãy đăng nhập lại hoặc cập nhật server.`); } if (!response.ok) throw new Error(body.detail || `AI không tạo được nội dung (HTTP ${response.status}).`); const fields = body.fields || {}; document.querySelectorAll('[data-scenario-field]').forEach(input => { if (fields[input.dataset.scenarioField]) input.value = fields[input.dataset.scenarioField]; }); const custom = fields.custom_fields || {}; form.elements.custom_fields.value = Object.entries(custom).map(([key, value]) => `${key}=${value}`).join('\n'); status.textContent = 'AI đã điền nội dung, hãy kiểm tra trước khi lưu.'; } catch (error) { status.textContent = error.message; } finally { button.disabled = false; } }
async function saveContactScenario(event) { event.preventDefault(); const form = event.target; const fields = Object.fromEntries([...form.querySelectorAll('[data-scenario-field]')].filter(input => input.value.trim()).map(input => [input.dataset.scenarioField, input.value.trim()])); Object.assign(fields, parseScenarioFields(form.elements.custom_fields.value)); const payload = {name: form.elements.name.value.trim(), description: form.elements.description.value.trim(), reference_website: form.elements.reference_website.value.trim(), fields}; const url = contactScenarioEditingId ? `/api/contact-campaign/scenarios/${contactScenarioEditingId}` : '/api/contact-campaign/scenarios'; const response = await fetch(url, {method: contactScenarioEditingId ? 'PUT' : 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); const body = await response.json(); if (!response.ok) { document.getElementById('contactScenarioStatus').textContent = body.detail || 'Không lưu được.'; return; } document.getElementById('contactScenarioModal').hidden = true; await loadContactCampaign(); }

async function inspectContact() {
  const status = document.getElementById('contactStatus');
  const container = document.getElementById('contactForms');
  const url = document.getElementById('contactUrl').value.trim();
  if (!url) return;
  status.textContent = 'Đang kiểm tra trang và các trang Contact...';
  container.innerHTML = '';
  const res = await fetch('/api/contact/inspect', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url}) });
  const data = await res.json();
  if (data.error) { status.textContent = data.error; return; }
  status.textContent = `Tìm thấy ${data.forms.length} form; ${data.contact_pages.length} trang Contact.`;
  data.forms.forEach((form, index) => {
    const box = document.createElement('div'); box.className = 'contact-form';
    box.innerHTML = `<h3>Form ${index + 1} — ${form.page_url}</h3><p>${form.has_captcha ? '⚠ Có CAPTCHA: không thể tự gửi.' : 'Không phát hiện CAPTCHA.'}</p>`;
    form.fields.forEach(field => {
      const label = document.createElement('label'); label.textContent = `${field.label}${field.required ? ' *' : ''}`;
      const input = field.type === 'textarea' ? document.createElement('textarea') : field.type === 'select' ? document.createElement('select') : document.createElement('input');
      input.name = field.name; input.dataset.formIndex = index; input.placeholder = field.name; input.required = field.required;
      if (field.type === 'select') field.options.forEach(option => { const el = document.createElement('option'); el.value = option.value; el.textContent = option.label; input.appendChild(el); });
      label.appendChild(input); box.appendChild(label);
    });
    if (!form.has_captcha) {
      const confirm = document.createElement('label'); confirm.className = 'confirm';
      confirm.innerHTML = '<input type="checkbox"> Tôi xác nhận muốn gửi form này.';
      const button = document.createElement('button'); button.textContent = 'Gửi tin';
      button.onclick = async () => {
        if (!confirm.querySelector('input').checked) { alert('Hãy xác nhận trước khi gửi.'); return; }
        const fields = {}; box.querySelectorAll('[data-form-index]').forEach(el => fields[el.name] = el.value);
        button.disabled = true;
        const result = await fetch('/api/contact/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({page_url:form.page_url, action:form.action, form_index:form.form_index, fields, confirm:true})});
        const body = await result.json(); alert(body.message || body.detail || 'Có lỗi khi gửi.'); button.disabled = false;
      };
      box.append(confirm, button);
    }
    container.appendChild(box);
  });
}

async function runSheetJob() {
  const button = document.getElementById('runSheetBtn');
  const status = document.getElementById('sheetStatus');
  button.disabled = true;
  status.textContent = 'Đang khởi động job...';
  try {
    const res = await fetch('/api/contact/sheet/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
      spreadsheet_url: document.getElementById('sheetUrl').value.trim(),
      sheet_name: document.getElementById('sheetName').value.trim() || 'company',
      batch_size: Number(document.getElementById('sheetBatchSize').value || 100),
    })});
    const started = await res.json();
    if (!res.ok) throw new Error(started.detail || 'Không khởi động được job.');
    const timer = setInterval(async () => {
      const current = await (await fetch(started.status_url)).json();
      status.textContent = current.status === 'error' ? `Lỗi: ${current.error}` : `Trạng thái: ${current.status}; ${current.processed}/${current.total} dòng đã ghi.`;
      if (current.status === 'done' || current.status === 'error') { clearInterval(timer); button.disabled = false; }
    }, 3000);
  } catch (error) {
    status.textContent = `Lỗi: ${error.message}`;
    button.disabled = false;
  }
}

async function runDbContactJob() {
  const button = document.getElementById('runDbContactBtn');
  const stopButton = document.getElementById('stopDbContactBtn');
  const status = document.getElementById('dbContactStatus');
  button.disabled = true;
  stopButton.disabled = false;
  status.textContent = 'DB: Đang khởi động...';
  try {
    const res = await fetch('/api/contact/db/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({batch_size: 100})});
    const started = await res.json();
    if (!res.ok) throw new Error(started.detail || 'Không khởi động được job DB.');
    window.currentDbContactJobId = started.job_id;
    const timer = setInterval(async () => {
      const current = await (await fetch(started.status_url)).json();
      status.textContent = current.status === 'error' ? `DB lỗi: ${current.error}` : `DB: ${current.status}; ${current.processed}/${current.total} dòng đã cập nhật.`;
      if (['done','error','stopped'].includes(current.status)) { clearInterval(timer); button.disabled = false; stopButton.disabled = true; await fetchCompanies(); }
    }, 3000);
  } catch (error) {
    status.textContent = `DB lỗi: ${error.message}`;
    button.disabled = false;
    stopButton.disabled = true;
  }
}

document.getElementById('searchBtn').addEventListener('click', fetchCompanies);
document.getElementById('filterBtn').addEventListener('click', fetchCompanies);
document.getElementById('displayLimit').addEventListener('change', fetchCompanies);
let enrichDataTimer;

async function refreshEnrichDataStatus() {
  const button = document.getElementById('enrichDataBtn');
  const stopButton = document.getElementById('stopEnrichDataBtn');
  const statusEl = document.getElementById('enrichDataStatus');
  const response = await fetch('/api/contact-enrichment/status');
  if (!response.ok) throw new Error('Status request failed');
  const {status, current, total, remaining, found, latest, error} = await response.json();
  if (status === 'running') {
    button.disabled = true;
    stopButton.disabled = false;
    statusEl.textContent = total
      ? `Đang tìm : ${current}/${total}/${remaining || 0}, đã tìm được ${found || 0} dữ liệu mới${latest ? ` (mới nhất: ${latest})` : ''}`
      : 'Đang chuẩn bị hoàn thiện dữ liệu...';
    clearTimeout(enrichDataTimer);
    enrichDataTimer = setTimeout(refreshEnrichDataStatus, 3000);
  } else {
    button.disabled = false;
    stopButton.disabled = true;
    if (status === 'completed') statusEl.textContent = `Hoàn tất: đã tìm được ${found || 0} dữ liệu mới.`;
    if (status === 'failed') statusEl.textContent = `Hoàn thiện dữ liệu bị lỗi${error ? `: ${error}` : '.'}`;
  }
}

document.getElementById('enrichDataBtn').addEventListener('click', async () => {
  let response;
  try {
    response = await fetch('/api/contact-enrichment/start', {method: 'POST'});
  } catch (error) {
    document.getElementById('enrichDataStatus').textContent = 'Không thể kết nối máy chủ.';
    return;
  }
  if (!response.ok) {
    document.getElementById('enrichDataStatus').textContent = 'Không thể khởi động hoàn thiện dữ liệu.';
    return;
  }
  try {
    await refreshEnrichDataStatus();
  } catch (error) {
    document.getElementById('enrichDataStatus').textContent = 'Không đọc được trạng thái job.';
  }
});

document.getElementById('stopEnrichDataBtn').addEventListener('click', async () => {
  const response = await fetch('/api/contact-enrichment/stop', {method: 'POST'});
  if (!response.ok) {
    document.getElementById('enrichDataStatus').textContent = 'Không thể dừng hoàn thiện dữ liệu.';
    return;
  }
  clearTimeout(enrichDataTimer);
  document.getElementById('enrichDataStatus').textContent = 'Đã dừng hoàn thiện dữ liệu.';
  document.getElementById('enrichDataBtn').disabled = false;
  document.getElementById('stopEnrichDataBtn').disabled = true;
});
document.getElementById('startContactCampaignBtn').addEventListener('click', startContactCampaign);
document.getElementById('newContactScenarioBtn').addEventListener('click', () => openContactScenario());
document.getElementById("stopContactCampaignBtn").addEventListener("click", async () => {
  if (!window.contactRunId) return;
  await fetch(`/api/contact-campaign/run/${window.contactRunId}/stop`, {method:"POST"});
  document.getElementById("contactCampaignStatus").textContent = "Đang dừng...";
});
let contactListEditingId = null;
document.getElementById('newContactListBtn').addEventListener('click', () => { contactListEditingId = null; const form = document.getElementById('contactListForm'); form.reset(); document.querySelectorAll('#contactListForm [data-multi-field]').forEach(x => x.checked = false); document.getElementById('contactListModal').hidden = false; });
document.getElementById('closeContactListModal').addEventListener('click', () => { document.getElementById('contactListModal').hidden = true; });
document.getElementById('contactListForm').addEventListener('submit', async event => { event.preventDefault(); const form = event.target; const payload = Object.fromEntries(new FormData(form)); const url = contactListEditingId ? `/api/contact-campaign/lists/${contactListEditingId}` : '/api/contact-campaign/lists'; const response = await fetch(url, {method: contactListEditingId ? 'PUT' : 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); const body = await response.json(); if (!response.ok) { document.getElementById('contactListModalStatus').textContent = body.detail || 'Không lưu được list.'; return; } document.getElementById('contactListModal').hidden = true; await loadContactCampaign(); });
document.getElementById('contactListFilterBtn').addEventListener('click', loadContactCampaign);
function restoreContactMultiOptions(fieldName, value) { const selected = new Set(String(value || '').split(',').map(x => x.trim()).filter(Boolean)); document.querySelectorAll(`input[data-multi-field="${fieldName}"]`).forEach(input => { input.checked = input.value.split(',').some(x => selected.has(x.trim())); }); syncMultiOptions(fieldName); }
document.getElementById('contactLists').addEventListener('click', async event => { const edit = event.target.closest('[data-contact-list-edit]'); const del = event.target.closest('[data-contact-list-delete]'); const open = event.target.closest('[data-contact-list-open]'); if (open) { const rows = await (await fetch(`/api/contact-campaign/lists/${open.dataset.contactListOpen}/customers`)).json(); document.getElementById('contactSelectedListCustomers').innerHTML = `<h3>Khách hàng trong list (${rows.length})</h3><table class="campaign-table"><thead><tr><th>Khách hàng</th><th>Email</th><th>Website</th></tr></thead><tbody>${rows.map(x => `<tr><td>${emktEscape(x.name)}</td><td>${emktEscape(x.email)}</td><td>${emktEscape(x.website)}</td></tr>`).join('')}</tbody></table>`; } if (edit) { const item = window.contactLists.find(x => x.id === Number(edit.dataset.contactListEdit)); contactListEditingId = item.id; const form = document.getElementById('contactListForm'); form.elements.name.value = item.name; form.elements.country_filter.value = item.country_filter || ''; form.elements.industry_filter.value = item.industry_filter || ''; document.querySelectorAll('#contactListForm [data-multi-field]').forEach(x => x.checked = false); restoreContactMultiOptions('contact_country_filter', item.country_filter); restoreContactMultiOptions('contact_industry_filter', item.industry_filter); document.getElementById('contactListModal').hidden = false; } if (del && confirm('Xóa list contact này?')) { await fetch(`/api/contact-campaign/lists/${del.dataset.contactListDelete}`, {method:'DELETE'}); await loadContactCampaign(); } });
document.getElementById("closeContactRunDetailsModal").addEventListener("click", () => { document.getElementById("contactRunDetailsModal").hidden = true; });
document.getElementById("contactHistory").addEventListener("click", event => { const button = event.target.closest("[data-contact-run-details]"); if (button) showContactRunDetails(Number(button.dataset.contactRunDetails)); });
document.getElementById('closeContactScenarioModal').addEventListener('click', () => { document.getElementById('contactScenarioModal').hidden = true; });
document.getElementById('contactScenarioForm').addEventListener('submit', saveContactScenario);
document.getElementById('contactScenarioAiBtn').addEventListener('click', generateContactScenarioWithAI);
document.querySelectorAll('[data-contact-panel]').forEach(button => button.addEventListener('click', () => { document.querySelectorAll('[data-contact-panel]').forEach(x => x.classList.toggle('active', x === button)); document.querySelectorAll('.contact-subpanel').forEach(x => { x.hidden = x.id !== `contact${button.dataset.contactPanel[0].toUpperCase()}${button.dataset.contactPanel.slice(1)}Panel`; }); if (button.dataset.contactPanel === 'history') loadContactCampaign(); }));
document.getElementById('contactScenarios').addEventListener('click', async event => { const edit = event.target.closest('[data-contact-scenario-edit]'); const del = event.target.closest('[data-contact-scenario-delete]'); if (edit) openContactScenario(Number(edit.dataset.contactScenarioEdit)); if (del && confirm('Xóa kịch bản này?')) { await fetch(`/api/contact-campaign/scenarios/${del.dataset.contactScenarioDelete}`, {method:'DELETE'}); await loadContactCampaign(); } });
document.getElementById('runSheetBtn').addEventListener('click', runSheetJob);
document.getElementById('addKeywordBtn').addEventListener('click', addKeywordRow);
document.getElementById('keywordRows').addEventListener('change', (event) => {
  if (event.target.name === 'activeKeyword') {
    const groupPosition = Number(document.getElementById('keywordModalTitle').textContent.replace(/\D/g, ''));
    fetch(`/api/country-source/keywords/${event.target.value}/active`, {
      method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({active: true})
    }).then(async (response) => {
      if (!response.ok) throw new Error('Không lưu được từ khóa active.');
      window.countryKeywords = await (await fetch('/api/country-source/keywords')).json();
      renderKeywordRows(groupPosition);
      renderCountrySourceTable();
    }).catch((error) => window.alert(error.message));
  }
});

let countryCrawlTimer;

async function refreshCountryCrawlStatus() {
  const progress = document.getElementById('countryCrawlProgress');
  const button = document.getElementById('startCountryCrawlBtn');
  const stopButton = document.getElementById('stopCountryCrawlBtn');
  try {
    const status = await (await fetch('/api/country-crawl/status')).json();
    if (status.running || status.state === 'running') {
      progress.textContent = status.total
        ? `Đang tìm tổ hợp từ khóa–địa điểm: ${status.current}/${status.total}, đã tìm được ${status.found || 0} doanh nghiệp`
        : 'Đang chuẩn bị tìm...';
      button.disabled = true;
      stopButton.disabled = false;
      clearTimeout(countryCrawlTimer);
      countryCrawlTimer = setTimeout(refreshCountryCrawlStatus, 2000);
    } else {
      button.disabled = false;
      stopButton.disabled = true;
      if (status.state === 'done') {
        progress.textContent = `Hoàn tất ${status.current}/${status.total} tổ hợp từ khóa–địa điểm, đã tìm được ${status.found || 0} doanh nghiệp`;
        loadCountrySource();
      } else if (status.state === 'stopped') {
        progress.textContent = `Đã dừng : ${status.current}/${status.total}, đã tìm được ${status.found || 0} doanh nghiệp`;
      } else if (status.state === 'failed') {
        progress.textContent = 'Tìm doanh nghiệp bị lỗi.';
      }
    }
  } catch (error) {
    progress.textContent = 'Không đọc được tiến độ tìm kiếm.';
    button.disabled = false;
  }
}

document.getElementById('startCountryCrawlBtn').addEventListener('click', async () => {
  const response = await fetch('/api/country-crawl/start', {method: 'POST'});
  if (!response.ok) {
    document.getElementById('countryCrawlProgress').textContent = 'Không thể khởi động tìm kiếm.';
    return;
  }
  document.getElementById('countryCrawlProgress').textContent = 'Đang chuẩn bị tìm...';
  refreshCountryCrawlStatus();
});
document.getElementById('countrySourceFilterBtn').addEventListener('click', loadCountrySource);

document.getElementById('stopCountryCrawlBtn').addEventListener('click', async () => {
  const response = await fetch('/api/country-crawl/stop', {method: 'POST'});
  if (!response.ok) {
    document.getElementById('countryCrawlProgress').textContent = 'Không thể dừng tìm kiếm.';
    return;
  }
  clearTimeout(countryCrawlTimer);
  refreshCountryCrawlStatus();
});
document.getElementById('closeKeywordModal').addEventListener('click', () => { document.getElementById('keywordModal').hidden = true; });
document.querySelector('#countrySourceTable thead').addEventListener('click', (event) => {
  const button = event.target.closest('.keyword-header');
  if (button) openKeywordModal(Number(button.dataset.keywordPosition));
});

async function initAuthAndSettings() {
  const user = await (await fetch('/api/auth/me')).json();
  window.currentUser = user;
  document.getElementById('currentUser').textContent = user.name ? `${user.name} (${user.email})` : user.email;
  if (!user.is_admin) {
    document.getElementById('enrichDataBtn').hidden = true;
    document.getElementById('stopEnrichDataBtn').hidden = true;
    document.getElementById('startCountryCrawlBtn').hidden = true;
    document.getElementById('stopCountryCrawlBtn').hidden = true;
    return;
  }
  const settingsBtn = document.getElementById('settingsBtn');
  document.querySelector('.auth-bar')?.prepend(settingsBtn);
  settingsBtn.hidden = false;
  const aiForm = document.getElementById('aiSettingsForm');
  const aiStatus = document.getElementById('aiSettingsStatus');
  const loadAISettings = async () => {
    const response = await fetch('/api/ai/settings');
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Không tải được cài đặt AI.');
    aiForm.elements.primary_model.value = data.primary_model || '';
    aiForm.elements.fallback_model_1.value = data.fallback_model_1 || '';
    aiForm.elements.fallback_model_2.value = data.fallback_model_2 || '';
    aiForm.elements.custom_prompt.value = data.custom_prompt || '';
    aiForm.elements.primary_model.placeholder = data.defaults.primary_model;
    aiForm.elements.fallback_model_1.placeholder = data.defaults.fallback_model_1;
    aiForm.elements.fallback_model_2.placeholder = data.defaults.fallback_model_2;
    aiStatus.textContent = data.has_api_key ? '' : 'Chưa có OPENROUTER_API_KEY trên server.';
  };
  settingsBtn.addEventListener('click', async () => {
    document.getElementById('settingsModal').hidden = false;
    try { await loadAISettings(); } catch (error) { aiStatus.textContent = error.message; }
    const target = document.getElementById('pendingUsers');
    const users = await (await fetch('/api/auth/users')).json();
    target.innerHTML = users.length ? `<table class="campaign-table"><thead><tr><th>Email</th><th>Tên</th><th>Trạng thái</th><th></th></tr></thead><tbody>${users.map(x => `<tr><td>${emktEscape(x.email)}</td><td>${emktEscape(x.name || '')}</td><td>${x.status}</td><td><span class="settings-user-actions">${x.status === 'pending' ? `<button type="button" data-approve-user="${x.id}">Duyệt</button><button type="button" class="danger-button" data-reject-user="${x.id}">Từ chối</button>` : ''}</span></td></tr>`).join('')}</tbody></table>` : '<p>Chưa có tài khoản.</p>';
  });
  aiForm.addEventListener('submit', async (event) => {
    event.preventDefault(); aiStatus.textContent = 'Đang lưu...';
    const response = await fetch('/api/ai/settings', {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(new FormData(aiForm)))});
    const body = await response.json(); aiStatus.textContent = response.ok ? 'Đã lưu cài đặt AI.' : (body.detail || 'Không lưu được cài đặt AI.');
    if (response.ok) await loadAISettings();
  });
  aiForm.querySelectorAll('[data-ai-test]').forEach((button) => button.addEventListener('click', async () => {
    const field = aiForm.elements[button.dataset.aiTest];
    const model = field.value.trim() || field.placeholder;
    const status = document.getElementById('aiTestStatus');
    if (!model) { status.textContent = 'Chưa có model để test.'; return; }
    button.disabled = true; status.textContent = `Đang test ${model}...`;
    try { const response = await fetch('/api/ai/test', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model})}); const body = await response.json(); status.textContent = response.ok ? `${model}: OK (${body.response})` : (body.detail || 'Test thất bại.'); } catch (error) { status.textContent = error.message; } finally { button.disabled = false; }
  }));
  document.getElementById('closeSettingsModal').addEventListener('click', () => { document.getElementById('settingsModal').hidden = true; });
  document.getElementById('pendingUsers').addEventListener('click', async (event) => {
    const button = event.target.closest('[data-approve-user], [data-reject-user]');
    if (!button) return;
    const status = button.dataset.approveUser ? 'approved' : 'rejected';
    await fetch(`/api/auth/users/${button.dataset.approveUser || button.dataset.rejectUser}?status=${status}`, {method: 'PATCH'});
    settingsBtn.click();
  });
}

initTableSort();
initTabs();
initDropdowns().then(fetchCompanies);
initAuthAndSettings().catch(() => {});
loadEmkt();
loadContactCampaign();
loadCountrySource();
refreshCountryCrawlStatus();
refreshEnrichDataStatus();

const githubUpdateBtn = document.getElementById('githubUpdateBtn');
if (githubUpdateBtn) {
  githubUpdateBtn.addEventListener('click', async () => {
    const status = document.getElementById('settingsUpdateStatus');
    githubUpdateBtn.disabled = true;
    status.textContent = 'Đang kiểm tra GitHub...';
    try {
      const check = await (await fetch('/api/system/update/check')).json();
      if (!check.ok) throw new Error(check.message || 'Không kiểm tra được GitHub');
      if (!check.updated) {
        status.textContent = 'Đã là bản mới nhất (' + check.local + ').';
        return;
      }
      if (!confirm('Có phiên bản mới trên GitHub (' + check.remote + '). Cập nhật ngay?')) {
        status.textContent = 'Đã hủy cập nhật.';
        return;
      }
      status.textContent = 'Đang cập nhật...';
      const result = await (await fetch('/api/system/update', {method: 'POST'})).json();
      if (!result.ok) throw new Error(result.message || 'Cập nhật thất bại');
      status.textContent = result.message || 'Đã cập nhật.';
    } catch (error) {
      status.textContent = 'Lỗi: ' + error.message;
    } finally {
      githubUpdateBtn.disabled = false;
    }
  });
}
