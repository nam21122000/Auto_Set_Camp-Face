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
    B = ID PAGE
    H = Tên Campaign
    I = Ngân sách chiến dịch (VNĐ/ngày, có thể ghi dạng "3.000.000 đ")
    O = ID POST (bài viết có sẵn trên Page dùng làm creative)
    P = Kết quả (script tự ghi "Thành công - ..." hoặc "Lỗi: ...")
"""
import json
import os
import re
from dataclasses import dataclass

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Cột trong sheet - sửa ở đây nếu sau này bạn đổi vị trí cột trong Google Sheet
COL_AD_ACCOUNT_ID = "A"
COL_PAGE_ID = "B"
COL_CAMPAIGN_NAME = "H"
COL_DAILY_BUDGET = "I"
COL_POST_ID = "O"
COL_RESULT = "P"

HEADER_ROW = 1
FIRST_DATA_ROW = 2


@dataclass
class SheetRow:
    row_number: int
    ad_account_id: str
    page_id: str
    campaign_name: str
    daily_budget: int
    post_id: str


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


def _col_to_index(col_letter: str) -> int:
    return gspread.utils.a1_to_rowcol(f"{col_letter}1")[1] - 1


def read_rows(worksheet: gspread.Worksheet) -> list[SheetRow]:
    """
    Đọc toàn bộ dòng có dữ liệu trong sheet.

    - Bỏ qua dòng trống hoàn toàn.
    - Bỏ qua dòng đã có giá trị ở cột Kết quả (P) - coi như đã chạy trước đó,
      tránh tạo trùng campaign khi chạy lại script nhiều lần.
    - Dòng thiếu dữ liệu bắt buộc hoặc sai định dạng ngân sách sẽ được ghi thẳng
      "Lỗi: ..." vào cột Kết quả và bị bỏ qua, không đưa vào danh sách trả về.
    """
    values = worksheet.get_all_values()

    idx_account = _col_to_index(COL_AD_ACCOUNT_ID)
    idx_page = _col_to_index(COL_PAGE_ID)
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
        campaign_name = cell(row, idx_name)
        budget_raw = cell(row, idx_budget)
        post_id = cell(row, idx_post)
        result = cell(row, idx_result)

        if not any([ad_account_id, page_id, campaign_name, budget_raw, post_id]):
            continue  # dòng trống

        if result:
            continue  # đã chạy trước đó (đã có kết quả)

        missing = [
            label
            for label, val in [
                ("ID tài khoản", ad_account_id),
                ("ID PAGE", page_id),
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

        rows.append(
            SheetRow(
                row_number=row_number,
                ad_account_id=ad_account_id,
                page_id=page_id,
                campaign_name=campaign_name,
                daily_budget=daily_budget,
                post_id=post_id,
            )
        )

    return rows


def write_result(worksheet: gspread.Worksheet, row_number: int, message: str) -> None:
    """Ghi kết quả (thành công/lỗi) vào cột Kết quả (P) của đúng dòng đó."""
    worksheet.update_acell(f"{COL_RESULT}{row_number}", message)
