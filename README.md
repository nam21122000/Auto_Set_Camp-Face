# FB Ads Automation

Script tự động tạo **Chiến dịch (Campaign) → Nhóm quảng cáo (Ad Set) → Quảng cáo (Ad)**
trên Facebook Ads Manager bằng Facebook Marketing API chính thức, thay vì tạo tay
từng chiến dịch theo mẫu đặt tên như trong tài khoản (VD: `Adela Shop-...-MDU6507-Nam-26/8-VIDEO-AI`).

Toàn bộ chiến dịch/adset/ad được khai báo trong **1 file YAML**, script sẽ đọc và tạo
tự động qua API. Mặc định mọi thứ tạo ra ở trạng thái **PAUSED** để bạn kiểm tra lại
trước khi bật thật.

---

## 1. Yêu cầu trước khi bắt đầu

- Python 3.9+
- Có quyền **Quản trị viên (Admin)** hoặc ít nhất quyền quảng cáo trên Ad Account
  và trên Fanpage sẽ dùng để đăng quảng cáo
- Có tài khoản **Meta Business Suite / Business Manager**
  (https://business.facebook.com)

---

## 2. Lấy thông tin để gọi được API (làm từ đầu)

Bạn cần 4 thông tin: `FB_APP_ID`, `FB_APP_SECRET`, `FB_ACCESS_TOKEN`, `FB_AD_ACCOUNT_ID`.

### Bước 1 — Tạo App trên Meta for Developers
1. Vào https://developers.facebook.com/apps → **Create App**
2. Chọn loại app **Business**
3. Đặt tên app tùy ý (VD: `Adela Ads Automation`) → Create App

### Bước 2 — Thêm sản phẩm Marketing API
1. Trong app vừa tạo, vào **Add Product** → tìm **Marketing API** → Set Up

### Bước 3 — Lấy App ID và App Secret
1. Vào **App Settings → Basic**
2. Copy **App ID** → dán vào `FB_APP_ID`
3. Bấm **Show** cạnh **App Secret** → copy → dán vào `FB_APP_SECRET`

### Bước 4 — Tạo System User để lấy Access Token dài hạn (khuyến nghị)
Cách này cho token **không tự hết hạn** (khác với token lấy từ Graph API Explorer
chỉ sống 1-2 giờ), phù hợp để chạy script lâu dài.

1. Vào **Business Settings** (business.facebook.com/settings) → **Users → System Users**
2. **Add** → đặt tên (VD: `automation-bot`) → chọn vai trò **Admin** → Create System User
3. Bấm **Add Assets**:
   - Ở mục **Ad Accounts**: chọn đúng Ad Account cần dùng (VD: tài khoản đang chứa
     các chiến dịch `Adela Shop-...`) → tick quyền **Manage campaigns**
   - Ở mục **Pages**: chọn Fanpage sẽ dùng để đăng quảng cáo → tick quyền quản lý
4. Bấm **Generate New Token**:
   - Chọn app vừa tạo ở Bước 1
   - Tick các quyền (scope): `ads_management`, `ads_read`, `business_management`,
     `pages_show_list`, `pages_read_engagement`
   - Bấm **Generate Token** → copy token → dán vào `FB_ACCESS_TOKEN`

> Token của System User có thể để **không hết hạn (Never)** khi generate — nên chọn
> tùy chọn đó nếu có, để không phải tạo lại token mỗi vài ngày.

### Bước 5 — Lấy Ad Account ID
Mở Ads Manager, nhìn trên URL sẽ thấy dạng:
```
adsmanager.facebook.com/adsmanager/manage/campaigns?act=887602053973002&...
```
Số sau `act=` chính là Ad Account ID → dán vào `FB_AD_ACCOUNT_ID`
(có ghi `act_` ở đầu hay không đều được, script tự xử lý).

### Bước 6 — App phải ở chế độ Live để chạy thật với tài khoản ngoài
Nếu app đang ở **Development mode**, chỉ các tài khoản có vai trò trong app (admin,
developer, tester) mới gọi được API. Muốn dùng rộng rãi cần **App Review** cho quyền
`ads_management`. Nếu chỉ chạy nội bộ cho chính Business Manager của bạn, thường
**không bắt buộc** phải qua review — kiểm tra thông báo trong App Dashboard nếu gặp lỗi quyền.

---

## 3. Cài đặt dự án

```bash
git clone <repo-cua-ban>
cd fb-ads-automation

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## 4. Cấu hình chiến dịch cần tạo

Sao chép file mẫu rồi chỉnh sửa theo dữ liệu thật:

```bash
cp config/campaigns.example.yaml config/campaigns.yaml
```

Mở `config/campaigns.yaml`, mỗi chiến dịch cần khai báo:
- `name`, `objective`, `status`, `special_ad_categories`
- danh sách `adsets`: ngân sách, targeting (đối tượng), tối ưu hóa
- trong mỗi adset là danh sách `ads`, mỗi ad chọn **1 trong 3 cách** tạo nội dung:
  1. `existing_post_id` — dùng lại 1 bài viết đã đăng sẵn trên Fanpage (giống thao
     tác "Sử dụng bài viết hiện có" bạn hay làm khi tạo tay)
  2. `video_path` + `thumbnail_url` — upload video mới từ máy
  3. `image_path` — upload ảnh mới từ máy

Xem đầy đủ ví dụ và comment giải thích trong `config/campaigns.example.yaml`.

**Objective hợp lệ thường dùng:** `OUTCOME_ENGAGEMENT`, `OUTCOME_TRAFFIC`,
`OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_AWARENESS`, `OUTCOME_APP_PROMOTION`.

**Lưu ý ngân sách:** VND không có phần thập phân, nhập nguyên số tiền
(VD `100000` = 100.000đ/ngày).

---

## 5. Chạy thử (dry-run) trước khi tạo thật

```bash
python run.py config/campaigns.yaml --dry-run
```
Lệnh này chỉ in ra cây Campaign → AdSet → Ad sẽ được tạo, **không gọi API thật**,
giúp bạn kiểm tra file YAML có đúng cấu trúc không trước khi tốn quota API.

## 6. Chạy thật

```bash
python run.py config/campaigns.yaml
```
Script sẽ tạo lần lượt từng Campaign, AdSet, Ad và in ra ID tương ứng. Mọi thứ
mặc định ở trạng thái **PAUSED** — vào Ads Manager kiểm tra lại rồi tự bật (Bật/Tắt)
khi đã ưng ý.

---

## 7. Cấu trúc dự án

```
fb-ads-automation/
├── README.md
├── requirements.txt
├── run.py                # điểm chạy chính
├── config/
│   └── campaigns.example.yaml
├── assets/                # để ảnh/video local dùng cho ad ở đây
└── src/
    ├── fb_client.py       # khởi tạo kết nối API
    ├── campaign.py        # tạo Campaign
    ├── adset.py            # tạo Ad Set
    ├── creative.py         # upload ảnh/video + tạo Ad Creative
    ├── ad.py                # tạo Ad
    └── cli.py               # đọc YAML và chạy toàn bộ pipeline
```

---

## 8. Đẩy dự án này lên GitHub của bạn

Claude không thể tự tạo repo trên tài khoản GitHub của bạn (không có quyền truy cập),
nhưng bạn chỉ cần vài lệnh sau:

```bash
cd fb-ads-automation
git init
git add .
git commit -m "Init: FB Ads automation script"

# Tạo 1 repo trống trên github.com trước (đừng tick "Add README"), sau đó:
git remote add origin https://github.com/<username>/<ten-repo>.git
git branch -M main
git push -u origin main
```

> Nếu muốn, có thể kết nối GitHub trực tiếp trong Claude ở lần trò chuyện sau để
> Claude tạo/commit thẳng vào repo giúp bạn.

---

## 9. Lưu ý quan trọng

  quản lý tài khoản quảng cáo của bạn (`.gitignore` đã chặn sẵn).
- Rate limit: Marketing API giới hạn số request/giờ theo tier của app — nếu tạo
  số lượng lớn campaign cùng lúc, nên thêm độ trễ (`time.sleep`) giữa các lần gọi.
- Facebook thường xuyên rà soát để tránh tạo hàng loạt nội dung trùng lặp/spam —
  đảm bảo nội dung/targeting hợp lệ theo chính sách quảng cáo để tránh bị khóa tài khoản.
- Muốn tạo **A/B test** (Thử nghiệm A/B) hoặc **nhân bản (Duplicate)** hàng loạt từ
  1 campaign gốc thay vì khai báo lại từ đầu — có thể mở rộng thêm 1 script dùng
  `campaign.create_copy()` của SDK, nói với Claude nếu cần bổ sung.
