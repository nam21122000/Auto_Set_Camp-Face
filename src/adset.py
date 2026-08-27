"""Tạo Nhóm quảng cáo (Ad Set) trên Facebook Ads."""
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet


def create_adset(
    account: AdAccount,
    name: str,
    campaign_id: str,
    daily_budget: int,
    billing_event: str,
    optimization_goal: str,
    targeting: dict,
    status: str = "PAUSED",
    start_time: str | None = None,
) -> AdSet:
    """
    Tạo 1 ad set mới trong campaign đã cho.

    daily_budget: đơn vị tiền tệ nhỏ nhất của tài khoản (VND không có phần thập
                  phân nên nhập nguyên giá trị VND, ví dụ 100000 = 100.000đ).
    billing_event: IMPRESSIONS, LINK_CLICKS, ...
    optimization_goal: POST_ENGAGEMENT, LINK_CLICKS, OFFSITE_CONVERSIONS,
                        REACH, VIDEO_VIEWS, ...
    targeting: dict theo cấu trúc Targeting của Facebook, ví dụ:
        {
          "geo_locations": {"countries": ["VN"]},
          "age_min": 18,
          "age_max": 45
        }
    """
    params = {
        AdSet.Field.name: name,
        AdSet.Field.campaign_id: campaign_id,
        AdSet.Field.daily_budget: daily_budget,
        AdSet.Field.billing_event: billing_event,
        AdSet.Field.optimization_goal: optimization_goal,
        AdSet.Field.targeting: targeting,
        AdSet.Field.status: status,
    }
    if start_time:
        params[AdSet.Field.start_time] = start_time

    return account.create_ad_set(params=params)
