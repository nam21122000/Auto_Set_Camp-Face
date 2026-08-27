"""
CLI để tự động tạo Campaign + AdSet + Ad trên Facebook Ads Manager
dựa theo 1 file cấu hình YAML.

Cách chạy:
    python run.py config/campaigns.example.yaml
    python run.py config/campaigns.example.yaml --dry-run
"""
import argparse

import yaml
from dotenv import load_dotenv

from src.ad import create_ad
from src.adset import create_adset
from src.campaign import create_campaign
from src.creative import (
    create_creative_from_existing_post,
    create_creative_from_image,
    create_creative_from_video,
    upload_image,
    upload_video,
)
from src.fb_client import get_ad_account, init_api


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_cta_value(ad_cfg: dict) -> dict | None:
    """
    Nếu ad khai báo destination: "messenger" trong config, trả về cta_value
    trỏ nút CTA đến Messenger thay vì link web. Ngược lại trả None (dùng
    hành vi mặc định là {"link": link}).
    """
    if ad_cfg.get("destination") == "messenger":
        return {"app_destination": "MESSENGER"}
    return None


def _build_creative(account, ad_cfg: dict):
    """Chọn cách tạo creative dựa trên các field có trong config của ad."""
    name = f"Creative - {ad_cfg['name']}"

    if ad_cfg.get("existing_post_id"):
        return create_creative_from_existing_post(
            account,
            page_id=ad_cfg["page_id"],
            post_id=ad_cfg["existing_post_id"],
            name=name,
        )

    if ad_cfg.get("existing_video_id"):
        # Dùng trực tiếp 1 video/Reel đã có sẵn trên Page (không cần upload lại)
        return create_creative_from_video(
            account,
            page_id=ad_cfg["page_id"],
            message=ad_cfg.get("message", ""),
            video_id=ad_cfg["existing_video_id"],
            thumbnail_url=ad_cfg["thumbnail_url"],
            name=name,
            call_to_action_type=ad_cfg.get("call_to_action", "SHOP_NOW"),
            link=ad_cfg.get("link", ""),
            cta_value=_build_cta_value(ad_cfg),
        )

    if ad_cfg.get("video_path"):
        video_id = upload_video(account, ad_cfg["video_path"])
        return create_creative_from_video(
            account,
            page_id=ad_cfg["page_id"],
            message=ad_cfg.get("message", ""),
            video_id=video_id,
            thumbnail_url=ad_cfg["thumbnail_url"],
            name=name,
            call_to_action_type=ad_cfg.get("call_to_action", "SHOP_NOW"),
            link=ad_cfg.get("link", ""),
            cta_value=_build_cta_value(ad_cfg),
        )

    if ad_cfg.get("image_path"):
        image_hash = upload_image(account, ad_cfg["image_path"])
        return create_creative_from_image(
            account,
            page_id=ad_cfg["page_id"],
            message=ad_cfg.get("message", ""),
            link=ad_cfg.get("link", ""),
            image_hash=image_hash,
            name=name,
            call_to_action_type=ad_cfg.get("call_to_action", "SHOP_NOW"),
        )

    raise ValueError(
        f"Ad '{ad_cfg['name']}' cần có 1 trong 4: existing_post_id / "
        f"existing_video_id / image_path / video_path trong file config."
    )


def run(config_path: str, dry_run: bool = False) -> None:
    load_dotenv()

    config = load_config(config_path)

    if dry_run:
        print("=== DRY-RUN: chỉ in kế hoạch, KHÔNG gọi API thật ===\n")
    else:
        init_api()

    account = get_ad_account() if not dry_run else None

    for camp_cfg in config.get("campaigns", []):
        print(f"\n=== Campaign: {camp_cfg['name']} ===")
        if dry_run:
            campaign_id = "<sẽ-tạo>"
        else:
            campaign = create_campaign(
                account,
                name=camp_cfg["name"],
                objective=camp_cfg.get("objective", "OUTCOME_ENGAGEMENT"),
                status=camp_cfg.get("status", "PAUSED"),
                special_ad_categories=camp_cfg.get("special_ad_categories", []),
                daily_budget=camp_cfg.get("daily_budget"),
            )
            campaign_id = campaign["id"]
            print(f"  -> Campaign ID: {campaign_id}")

        for adset_cfg in camp_cfg.get("adsets", []):
            print(f"  --- AdSet: {adset_cfg['name']}")
            if dry_run:
                adset_id = "<sẽ-tạo>"
            else:
                adset = create_adset(
                    account,
                    name=adset_cfg["name"],
                    campaign_id=campaign_id,
                    # Chỉ truyền daily_budget ở đây khi KHÔNG dùng ngân sách cấp
                    # Campaign (nếu camp_cfg đã có daily_budget thì để None,
                    # AdSet dùng chung ngân sách campaign - CBO).
                    daily_budget=(
                        adset_cfg.get("daily_budget")
                        if not camp_cfg.get("daily_budget")
                        else None
                    ),
                    billing_event=adset_cfg.get("billing_event", "IMPRESSIONS"),
                    optimization_goal=adset_cfg.get(
                        "optimization_goal", "POST_ENGAGEMENT"
                    ),
                    targeting=adset_cfg["targeting"],
                    status=adset_cfg.get("status", "PAUSED"),
                    bid_strategy=adset_cfg.get(
                        "bid_strategy", "LOWEST_COST_WITHOUT_CAP"
                    ),
                    bid_amount=adset_cfg.get("bid_amount"),
                    # Chỉ dùng promoted_object khi tự khai báo rõ trong config
                    # (VD chạy chiến dịch Lượt thích Trang) - KHÔNG tự suy ra,
                    # vì dễ khiến Facebook hiểu nhầm sang loại chiến dịch khác.
                    promoted_object=adset_cfg.get("promoted_object"),
                    destination_type=adset_cfg.get("destination_type"),
                )
                adset_id = adset["id"]
                print(f"      -> AdSet ID: {adset_id}")

            for ad_cfg in adset_cfg.get("ads", []):
                print(f"      ..... Ad: {ad_cfg['name']}")
                if dry_run:
                    continue

                creative = _build_creative(account, ad_cfg)
                ad = create_ad(
                    account,
                    name=ad_cfg["name"],
                    adset_id=adset_id,
                    creative_id=creative["id"],
                    status=ad_cfg.get("status", "PAUSED"),
                )
                print(f"          -> Ad ID: {ad['id']}")

    print("\nHoàn tất!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tự động tạo Campaign/AdSet/Ad trên Facebook Ads Manager"
    )
    parser.add_argument("config", help="Đường dẫn tới file config YAML")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ in ra kế hoạch sẽ tạo, không gọi API thật (an toàn để kiểm tra trước)",
    )
    args = parser.parse_args()
    run(args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
