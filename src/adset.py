"""Tạo Nhóm quảng cáo (Ad Set) trên Facebook Ads."""
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet


def create_adset(
    account: AdAccount,
    name: str,
    campaign_id: str,
    billing_event: str,
    optimization_goal: str,
    targeting: dict,
    daily_budget: int | None = None,
    status: str = "PAUSED",
    start_time: str | None = None,
    end_time: str | None = None,
    bid_strategy: str | None = "LOWEST_COST_WITHOUT_CAP",
    bid_amount: int | None = None,
    promoted_object: dict | None = None,
    destination_type: str | None = None,
) -> AdSet:
    """
    Tạo 1 ad set mới trong campaign đã cho.

    daily_budget: đơn vị tiền tệ nhỏ nhất của tài khoản (VND không có phần thập
                  phân nên nhập nguyên giá trị VND, ví dụ 100000 = 100.000đ).
                  Để None nếu ngân sách đã đặt ở CẤP CAMPAIGN (CBO/"Ngân sách
                  chiến dịch") — Facebook không cho phép đặt ngân sách ở cả
                  2 cấp cùng lúc.
    billing_event: IMPRESSIONS, LINK_CLICKS, ...
    optimization_goal: POST_ENGAGEMENT, LINK_CLICKS, OFFSITE_CONVERSIONS,
                        REACH, VIDEO_VIEWS, CONVERSATIONS (tối ưu số cuộc trò
                        chuyện/tin nhắn — dùng khi destination_type=MESSENGER,
                        tương ứng mục tiêu hiệu quả "Tối đa hóa số lượt nhắn
                        tin" hoặc "...lượt mua qua tin nhắn" trên giao diện) ...
    destination_type: để trống với quảng cáo thường. Đặt "MESSENGER" khi muốn
                       "Đích đến của tin nhắn" = Messenger (giống ảnh chụp cấu
                       hình "Nhóm quảng cáo Lượt tương tác mới"), khi đó nên
                       dùng optimization_goal="CONVERSATIONS" và promoted_object
                       chỉ cần {"page_id": "..."}.
    bid_strategy: LOWEST_COST_WITHOUT_CAP (mặc định, để Facebook tự tối ưu giá),
                  LOWEST_COST_WITH_BID_CAP (phải kèm bid_amount = giá thầu tối đa),
                  COST_CAP (phải kèm bid_amount = mức chi phí mục tiêu).
                  QUAN TRỌNG: nếu campaign đang dùng CBO ("Ngân sách chiến
                  dịch" — daily_budget khai báo ở cấp campaign), phải truyền
                  bid_strategy=None ở đây (không đặt ở AdSet), vì với CBO
                  Facebook bắt buộc bid_strategy phải nằm ở params của
                  Campaign, đặt trùng ở cả AdSet sẽ gây lỗi 400 đòi bid_amount
                  dù đã chọn LOWEST_COST_WITHOUT_CAP (error_subcode 1815857).
    bid_amount: chỉ cần khi bid_strategy khác LOWEST_COST_WITHOUT_CAP.
    promoted_object: bắt buộc với optimization_goal = POST_ENGAGEMENT/PAGE_LIKES/
                      CONVERSATIONS, ví dụ {"page_id": "1294066237122353"} — cho
                      Facebook biết đối tượng "chuyển đổi" chính là Page đó,
                      tránh bị đòi hỏi phải gắn Pixel.
    start_time / end_time: chuỗi ISO 8601, ví dụ "2026-08-27T14:40:00+0700".
                            Bỏ end_time (None) nếu không đặt ngày kết thúc
                            (giống ô "Đặt ngày kết thúc" để trống trên giao diện).
    targeting: dict theo cấu trúc Targeting của Facebook, ví dụ:
        {
          "geo_locations": {"countries": ["VN"]},
          "age_min": 18,
          "age_max": 45,
          "publisher_platforms": ["facebook", "messenger"],
          "device_platforms": ["mobile"],
          "wifi_only": false
        }
        publisher_platforms giới hạn nền tảng chạy quảng cáo (VD chỉ Facebook +
        Messenger, tắt Instagram/Audience Network/Threads). device_platforms
        giới hạn loại thiết bị (["mobile"] = chỉ di động). Nếu không tự khai
        báo "targeting_automation", mặc định sẽ TẮT "Đối tượng Advantage"
        (advantage_audience: 0) để giữ đúng đối tượng bạn nhắm tới.
    """
    targeting = dict(targeting)  # tránh sửa trực tiếp dict gốc từ config
    targeting.setdefault("targeting_automation", {"advantage_audience": 0})

    params = {
        AdSet.Field.name: name,
        AdSet.Field.campaign_id: campaign_id,
        AdSet.Field.billing_event: billing_event,
        AdSet.Field.optimization_goal: optimization_goal,
        AdSet.Field.targeting: targeting,
        AdSet.Field.status: status,
    }
    if bid_strategy:
        # Chỉ set khi KHÔNG dùng CBO ở campaign (xem lưu ý ở docstring)
        params[AdSet.Field.bid_strategy] = bid_strategy
    if daily_budget:
        # Chỉ set nếu ngân sách nằm ở cấp AdSet (không dùng CBO ở campaign)
        params[AdSet.Field.daily_budget] = daily_budget
    if start_time:
        params[AdSet.Field.start_time] = start_time
    if end_time:
        params[AdSet.Field.end_time] = end_time
    if bid_amount:
        params[AdSet.Field.bid_amount] = bid_amount
    if promoted_object:
        params[AdSet.Field.promoted_object] = promoted_object
    if destination_type:
        params[AdSet.Field.destination_type] = destination_type

    return account.create_ad_set(params=params)
