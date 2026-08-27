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

    return account.create_campaign(params=params)
