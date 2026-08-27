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
        params[Campaign.Field.daily_budget] = daily_budget
        # Dùng ngân sách cấp Campaign (CBO) -> cho phép chia sẻ ngân sách giữa các AdSet
        params["is_adset_budget_sharing_enabled"] = True
    else:
        # Ngân sách đặt ở cấp AdSet -> Facebook bắt buộc phải chỉ định rõ field này
        params["is_adset_budget_sharing_enabled"] = False

    return account.create_campaign(params=params)
