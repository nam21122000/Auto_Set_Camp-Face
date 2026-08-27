"""
Upload ảnh/video và tạo Ad Creative.
Hỗ trợ 2 cách:
  1. Dùng lại 1 bài post có sẵn trên Fanpage (existing post) -> giống thao tác
     "Sử dụng bài viết hiện có" trên Ads Manager.
  2. Tạo creative mới từ ảnh + nội dung tự viết.
"""
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.advideo import AdVideo


def upload_image(account: AdAccount, image_path: str) -> str:
    """Upload ảnh lên thư viện quảng cáo, trả về image_hash."""
    image = AdImage(parent_id=account.get_id())
    image[AdImage.Field.filename] = image_path
    image.remote_create()
    return image[AdImage.Field.hash]


def upload_video(account: AdAccount, video_path: str) -> str:
    """Upload video lên thư viện quảng cáo, trả về video_id."""
    video = AdVideo(parent_id=account.get_id())
    video[AdVideo.Field.filename] = video_path
    video.remote_create()
    return video.get_id()


def _with_multi_advertiser_ads(params: dict, multi_advertiser_ads: bool) -> dict:
    """
    Bật/tắt "Quảng cáo đa bên" (Multi-advertiser ads) — tick "Quảng cáo của bạn
    có thể xuất hiện cùng với những quảng cáo khác trong cùng 1 đơn vị quảng
    cáo để thu hút mọi người khám phá". Mặc định BẬT (giống hành vi mặc định
    trên giao diện Ads Manager).
    """
    params["contextual_multi_ads"] = {
        "enroll_status": "OPT_IN" if multi_advertiser_ads else "OPT_OUT"
    }
    return params


def create_creative_from_existing_post(
    account: AdAccount,
    page_id: str,
    post_id: str,
    name: str,
    multi_advertiser_ads: bool = True,
) -> AdCreative:
    """
    Tạo creative từ 1 bài post đã đăng sẵn trên Fanpage.
    post_id: chỉ phần số sau dấu "_" trong ID bài viết (không kèm page_id).
    multi_advertiser_ads: tick "Quảng cáo đa bên" như ảnh chụp cấu hình mẫu
                           (mặc định True, giống mặc định trên Ads Manager).
    """
    object_story_id = f"{page_id}_{post_id}"
    params = {
        AdCreative.Field.name: name,
        AdCreative.Field.object_story_id: object_story_id,
    }
    params = _with_multi_advertiser_ads(params, multi_advertiser_ads)
    return account.create_ad_creative(params=params)


def create_creative_from_image(
    account: AdAccount,
    page_id: str,
    message: str,
    link: str,
    image_hash: str,
    name: str,
    call_to_action_type: str = "SHOP_NOW",
    multi_advertiser_ads: bool = True,
) -> AdCreative:
    """Tạo creative mới (dạng link ad với 1 ảnh) thay vì dùng post có sẵn."""
    object_story_spec = {
        "page_id": page_id,
        "link_data": {
            "message": message,
            "link": link,
            "image_hash": image_hash,
            "call_to_action": {"type": call_to_action_type},
        },
    }
    params = {
        AdCreative.Field.name: name,
        AdCreative.Field.object_story_spec: object_story_spec,
    }
    params = _with_multi_advertiser_ads(params, multi_advertiser_ads)
    return account.create_ad_creative(params=params)


def create_creative_from_video(
    account: AdAccount,
    page_id: str,
    message: str,
    video_id: str,
    thumbnail_url: str,
    name: str,
    call_to_action_type: str = "SHOP_NOW",
    link: str = "",
    multi_advertiser_ads: bool = True,
) -> AdCreative:
    """Tạo creative mới dạng video (dùng cho các mẫu '-VIDEO-AI' như trong tài khoản)."""
    video_data = {
        "video_id": video_id,
        "message": message,
        "image_url": thumbnail_url,
        "call_to_action": {
            "type": call_to_action_type,
            "value": {"link": link} if link else {},
        },
    }
    object_story_spec = {
        "page_id": page_id,
        "video_data": video_data,
    }
    params = {
        AdCreative.Field.name: name,
        AdCreative.Field.object_story_spec: object_story_spec,
    }
    params = _with_multi_advertiser_ads(params, multi_advertiser_ads)
    return account.create_ad_creative(params=params)
