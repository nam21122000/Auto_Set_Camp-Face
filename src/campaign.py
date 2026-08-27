"""Tạo Chiến dịch (Campaign) trên Facebook Ads."""
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign


def create_campaign(
    account: AdAccount,
    name: str,
    objective: str = "OUTCOME_ENGAGEMENT",
    status: str = "PAUSED",
    special_ad_categories: list | None = None,
    daily_budget: int | None = None,
    buying_type: str = "AUCTION",
    bid_strategy: str | None = None,
    bid_amount: int | None = None,
) -> Campaign:
    """
    Tạo 1 campaign mới.

    objective: OUTCOME_ENGAGEMENT, OUTCOME_TRAFFIC, OUTCOME_SALES,
               OUTCOME_LEADS, OUTCOME_AWARENESS, OUTCOME_APP_PROMOTION ...
               (VD: "Lượt tương tác" trên giao diện = OUTCOME_ENGAGEMENT)
    status: PAUSED (khuyến nghị khi test) hoặc ACTIVE
    daily_budget: ngân sách ngày ở CẤP CAMPAIGN (Ngân sách chiến dịch / CBO).
                  Nếu để ngân sách ở cấp AdSet (Ngân sách nhóm quảng cáo) thì
                  bỏ qua tham số này (để None).
    buying_type: "AUCTION" (Đấu giá, mặc định) hoặc "RESERVED".
    bid_strategy / bid_amount: CHỈ dùng khi có daily_budget (dùng CBO) — với
                  CBO, bid_strategy phải khai báo ở CẤP CAMPAIGN, không phải
                  cấp AdSet, nếu không Facebook sẽ báo lỗi 400 đòi bid_amount
                  dù đã chọn LOWEST_COST_WITHOUT_CAP (error_subcode 1815857).
                  Nếu KHÔNG dùng CBO (đặt ngân sách ở AdSet) thì bỏ qua 2 tham
                  số này ở đây và khai báo bid_strategy trong adset thay vào.
    """
    params = {
        Campaign.Field.name: name,
        Campaign.Field.objective: objective,
        Campaign.Field.status: status,
        Campaign.Field.special_ad_categories: special_ad_categories or [],
        Campaign.Field.buying_type: buying_type,
    }
    if daily_budget:
        # Dùng ngân sách cấp Campaign (CBO - "Ngân sách chiến dịch").
        # KHÔNG set is_adset_budget_sharing_enabled ở đây: field này dùng cho
        # 1 tính năng khác ("chia sẻ ngân sách linh hoạt" giữa các adset khi
        # KHÔNG dùng CBO) và Facebook sẽ trả lỗi 400 (error_subcode 4834002)
        # nếu vừa có daily_budget cấp campaign vừa set field này = true.
        params[Campaign.Field.daily_budget] = daily_budget
        # Với CBO, bid_strategy bắt buộc phải nằm ở params của Campaign.
        params[Campaign.Field.bid_strategy] = bid_strategy or "LOWEST_COST_WITHOUT_CAP"
        if bid_amount:
            params[Campaign.Field.bid_amount] = bid_amount

    return account.create_campaign(params=params)
