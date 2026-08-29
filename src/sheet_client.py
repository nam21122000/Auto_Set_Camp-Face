"""
Đọc danh sách campaign cần tạo từ Google Sheet, và ghi kết quả (thành công/lỗi)
ngược lại vào sheet sau khi chạy.

Xác thực bằng Service Account (không cần đăng nhập tay, sheet có thể để riêng tư -
chỉ cần share sheet cho email của Service Account).

Credentials được đọc TRỰC TIẾP từ biến môi trường GOOGLE_CREDENTIALS (nội dung
JSON key dạng text, y hệt cách đặt secret trên GitHub Actions) - không ghi ra
file trung gian, tránh lỗi hỏng định dạng JSON (ký tự \\r, encoding...) khi ghi
qua shell.

Cấu trúc cột đang dùng trong sheet (xem README phần Google Sheet):
    A = ID tài khoản (Ad Account ID)
    C = ID PAGE
    E = Mã (dùng để đặt tên AdSet/Ad, VD "MDU3984" -> "AdSet - MDU3984")
    H = Ngày bắt đầu chạy (VD "30/8", không cần ghi năm - tự lấy năm hiện tại,
        nếu ngày/tháng đã qua trong năm nay thì tự hiểu là năm sau)
    I = Giờ bắt đầu chạy (VD "00:00")
    K = Tên Campaign
    L = Ngân sách chiến dịch (VNĐ/ngày, có thể ghi dạng "3.000.000 đ")
    Q = ID POST (bài viết có sẵn trên Page dùng làm creative)
    R = Kết quả (script tự ghi "Thành công - ..." hoặc "Lỗi: ...")

Ngày/Giờ (H, I) là TUỲ CHỌN: để trống cả 2 thì AdSet/Ad chạy ngay khi được bật
(không đặt lịch); nếu điền thì phải điền ĐỦ CẢ 2 cột.
"""
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Việt Nam không có giờ mùa hè -> lệch cố định UTC+7
VN_TZ = timezone(timedelta(hours=7))

# Cột trong sheet - sửa ở đây nếu sau này bạn đổi vị trí cột trong Google Sheet
COL_AD_ACCOUNT_ID = "A"
COL_PAGE_ID = "C"
COL_CODE = "E"
COL_DATE = "H"
COL_TIME = "I"
COL_CAMPAIGN_NAME = "K"
COL_DAILY_BUDGET = "L"
COL_POST_ID = "Q"
COL_RESULT = "R"

HEADER_ROW = 1
FIRST_DATA_ROW = 2


@dataclass
class SheetRow:
    row_number: int
    ad_account_id: str
    page_id: str
    code: str
    campaign_name: str
    daily_budget: int
    post_id: str
    start_time: str | None = None  # ISO 8601, VD "2026-08-30T00:00:00+07:00"


def _get_client() -> gspread.Client:
    """
    Ưu tiên đọc credentials từ GOOGLE_CREDENTIALS (nội dung JSON dạng text,
    dùng cho GitHub Actions secret). Nếu không có, fallback sang
    GOOGLE_SERVICE_ACCOUNT_FILE (đường dẫn file JSON, dùng khi chạy local với
    file key sẵn trên máy) để tương thích ngược.
    """
    raw_json = os.getenv("GOOGLE_CREDENTIALS")
    if raw_json:
        try:
            info = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"GOOGLE_CREDENTIALS không phải JSON hợp lệ: {e}. "
                "Kiểm tra lại đã dán ĐÚNG NGUYÊN nội dung file JSON key vào secret chưa."
            ) from e
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    key_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_path:
        raise EnvironmentError(
            "Thiếu credentials Google: cần GOOGLE_CREDENTIALS (nội dung JSON) "
            "hoặc GOOGLE_SERVICE_ACCOUNT_FILE (đường dẫn file JSON). "
            "Xem README phần 'Kết nối Google Sheet'."
        )
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Không tìm thấy file key Service Account: {key_path}")

    creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return gspread.authorize(creds)


def get_worksheet() -> gspread.Worksheet:
    """Mở đúng tab (worksheet) trong Google Sheet dựa theo GOOGLE_SHEET_ID / GOOGLE_SHEET_TAB."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise EnvironmentError("Thiếu GOOGLE_SHEET_ID trong .env")
    tab_name = os.getenv("GOOGLE_SHEET_TAB", "Data")

    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    return spreadsheet.worksheet(tab_name)


def _parse_budget(raw: str) -> int:
    """'3.000.000 đ' hoặc '3000000' -> 3000000. VND không có phần thập phân."""
    digits = re.sub(r"[^\d]", "", raw or "")
    if not digits:
        raise ValueError(f"không đọc được số tiền từ giá trị '{raw}'")
    return int(digits)


def _parse_start_time(date_raw: str, time_raw: str) -> str:
    """
    'Ngày' dạng "30/8" (không có năm) + 'giờ' dạng "00:00" -> ISO 8601 có múi
    giờ VN, VD "2026-08-30T00:00:00+07:00".

    Tự suy ra năm: dùng năm hiện tại; nếu ngày đó đã qua hơn 1 ngày so với hôm
    nay thì hiểu là năm sau (VD chạy vào tháng 12 mà ghi ngày "5/1" -> hiểu là
    ngày 5/1 năm sau, không phải đã qua).
    """
    date_match = re.match(r"^\s*(\d{1,2})\s*/\s*(\d{1,2})\s*$", date_raw or "")
    if not date_match:
        raise ValueError(f"cột Ngày sai định dạng '{date_raw}', cần dạng VD '30/8'")
    time_match = re.match(r"^\s*(\d{1,2})\s*:\s*(\d{2})\s*$", time_raw or "")
    if not time_match:
        raise ValueError(f"cột giờ sai định dạng '{time_raw}', cần dạng VD '00:00'")

    day, month = int(date_match.group(1)), int(date_match.group(2))
    hour, minute = int(time_match.group(1)), int(time_match.group(2))

    today = datetime.now(VN_TZ).date()
    year = today.year
    try:
        candidate = date(year, month, day)
    except ValueError as e:
        raise ValueError(f"ngày/tháng không hợp lệ '{date_raw}': {e}") from e

    if candidate < today - timedelta(days=1):
        candidate = date(year + 1, month, day)

    dt = datetime(candidate.year, candidate.month, candidate.day, hour, minute, tzinfo=VN_TZ)
    return dt.isoformat()


def _col_to_index(col_letter: str) -> int:
    return gspread.utils.a1_to_rowcol(f"{col_letter}1")[1] - 1


def read_rows(worksheet: gspread.Worksheet) -> list[SheetRow]:
    """
    Đọc toàn bộ dòng có dữ liệu trong sheet.

    - Bỏ qua dòng trống hoàn toàn.
    - Bỏ qua dòng đã có giá trị ở cột Kết quả (R) - coi như đã chạy trước đó,
      tránh tạo trùng campaign khi chạy lại script nhiều lần.
    - Dòng thiếu dữ liệu bắt buộc hoặc sai định dạng ngân sách/ngày giờ sẽ được
      ghi thẳng "Lỗi: ..." vào cột Kết quả và bị bỏ qua, không đưa vào danh sách
      trả về.
    """
    values = worksheet.get_all_values()

    idx_account = _col_to_index(COL_AD_ACCOUNT_ID)
    idx_page = _col_to_index(COL_PAGE_ID)
    idx_code = _col_to_index(COL_CODE)
    idx_date = _col_to_index(COL_DATE)
    idx_time = _col_to_index(COL_TIME)
    idx_name = _col_to_index(COL_CAMPAIGN_NAME)
    idx_budget = _col_to_index(COL_DAILY_BUDGET)
    idx_post = _col_to_index(COL_POST_ID)
    idx_result = _col_to_index(COL_RESULT)

    def cell(row: list[str], idx: int) -> str:
        return row[idx].strip() if idx < len(row) else ""

    rows: list[SheetRow] = []
    for row_number, row in enumerate(values[HEADER_ROW:], start=FIRST_DATA_ROW):
        ad_account_id = cell(row, idx_account)
        page_id = cell(row, idx_page)
        code = cell(row, idx_code)
        date_raw = cell(row, idx_date)
        time_raw = cell(row, idx_time)
        campaign_name = cell(row, idx_name)
        budget_raw = cell(row, idx_budget)
        post_id = cell(row, idx_post)
        result = cell(row, idx_result)

        if not any([ad_account_id, page_id, code, campaign_name, budget_raw, post_id]):
            continue  # dòng trống

        if result:
            continue  # đã chạy trước đó (đã có kết quả)

        missing = [
            label
            for label, val in [
                ("ID tài khoản", ad_account_id),
                ("ID PAGE", page_id),
                ("Mã", code),
                ("Tên Campaign", campaign_name),
                ("Ngân sách", budget_raw),
                ("ID POST", post_id),
            ]
            if not val
        ]
        if missing:
            write_result(worksheet, row_number, f"Lỗi: thiếu {', '.join(missing)}")
            continue

        try:
            daily_budget = _parse_budget(budget_raw)
        except ValueError as e:
            write_result(worksheet, row_number, f"Lỗi: {e}")
            continue

        # Ngày/Giờ là tuỳ chọn - để trống cả 2 thì không đặt lịch (chạy ngay khi bật)
        start_time: str | None = None
        if date_raw or time_raw:
            if not (date_raw and time_raw):
                write_result(
                    worksheet,
                    row_number,
                    "Lỗi: cần điền đủ cả Ngày và giờ, hoặc để trống cả 2",
                )
                continue
            try:
                start_time = _parse_start_time(date_raw, time_raw)
            except ValueError as e:
                write_result(worksheet, row_number, f"Lỗi: {e}")
                continue

        rows.append(
            SheetRow(
                row_number=row_number,
                ad_account_id=ad_account_id,
                page_id=page_id,
                code=code,
                campaign_name=campaign_name,
                daily_budget=daily_budget,
                post_id=post_id,
                start_time=start_time,
            )
        )

    return rows


def write_result(worksheet: gspread.Worksheet, row_number: int, message: str) -> None:
    """Ghi kết quả (thành công/lỗi) vào cột Kết quả (R) của đúng dòng đó."""
    worksheet.update_acell(f"{COL_RESULT}{row_number}", message)
