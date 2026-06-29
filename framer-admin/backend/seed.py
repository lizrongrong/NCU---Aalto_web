"""
seed.py — 初始資料載入腳本
============================
這個腳本會：
1. 建立管理員帳號
2. 建立網站所有頁面（依照架構圖）
3. 為每個頁面建立基本區塊與欄位
4. 支援繁體中文（zh-TW）與英文（en-US）初始內容

執行方式：
  cd backend
  python seed.py

⚠️  注意：重複執行不會重複建資料（已有資料會跳過）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models import Page, Section, ContentField, User
from routers.auth import hash_password

# ─────────────────────────────────────────
# 初始管理員帳號設定
# 執行 seed.py 後，用這組帳密登入後台
# 正式上線前請務必修改密碼！
# ─────────────────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ncu-aalto-2024"   # ⚠️ 請在 .env 裡設定，或直接改這裡
ADMIN_EMAIL = "admin@example.com"


# ─────────────────────────────────────────
# 網站頁面架構（對應架構圖）
# 格式：{ slug, title, parent_slug, order, is_active }
# ─────────────────────────────────────────
PAGES = [
    {"slug": "home",            "title": "首頁",           "parent_slug": None,      "order": 1,  "active": True},
    {"slug": "about",           "title": "關於 Aalto EMBA","parent_slug": None,      "order": 2,  "active": True},
    {"slug": "about-aalto-emba","title": "關於 Aalto EMBA（子頁）","parent_slug": "about","order": 1,"active": True},
    {"slug": "about-aalto",     "title": "關於 Aalto",     "parent_slug": "about",   "order": 2,  "active": True},
    {"slug": "about-ncu",       "title": "關於中央大學",    "parent_slug": "about",   "order": 3,  "active": True},
    {"slug": "learning",        "title": "學習回饋",        "parent_slug": None,      "order": 3,  "active": True},
    {"slug": "alumni",          "title": "校友分享",        "parent_slug": "learning","order": 1,  "active": True},
    {"slug": "courses",         "title": "課程相關",        "parent_slug": None,      "order": 4,  "active": True},
    {"slug": "admission",       "title": "招生資訊",        "parent_slug": "courses", "order": 1,  "active": True},
    {"slug": "degree",          "title": "修業與學位",      "parent_slug": "courses", "order": 2,  "active": True},
    {"slug": "application",     "title": "入學申請",        "parent_slug": "courses", "order": 3,  "active": True},
    {"slug": "tuition",         "title": "學費與獎學金",    "parent_slug": "courses", "order": 4,  "active": True},
    {"slug": "faq",             "title": "FAQ 常見問題",    "parent_slug": "courses", "order": 5,  "active": True},
    {"slug": "contact",         "title": "聯絡方式",        "parent_slug": None,      "order": 5,  "active": True},
    {"slug": "search",          "title": "搜尋引擎",        "parent_slug": None,      "order": 6,  "active": True},
]


# ─────────────────────────────────────────
# 各頁面初始區塊與內容
# 格式：{ page_slug, key, name, type, order, fields }
# fields 格式：{ key, label, type, zh_TW, en_US }
# ─────────────────────────────────────────
SECTIONS_DATA = [

    # ════════════════════
    # 首頁 (home)
    # ════════════════════
    {
        "page_slug": "home", "key": "hero", "name": "頂部橫幅 (Hero)", "type": "hero", "order": 1,
        "fields": [
            {"key": "title",    "label": "主標題",   "type": "text",
             "zh": "國立中央大學 × 阿爾托大學 高階經營管理碩士在職學位學程",
             "en": "National Central University × Aalto University Executive MBA Program"},
            {"key": "subtitle", "label": "副標題",   "type": "text",
             "zh": "NCU × Aalto Executive MBA Program",
             "en": "NCU × Aalto University EMBA Program"},
            {"key": "description", "label": "敘述文字", "type": "text",
             "zh": "北歐創新 × 亞洲實戰 Leading with Global Vision",
             "en": "Nordic Innovation × Asia Action: Leading with Global Vision"},
             {"key": "image_url", "label": "背景圖片", "type": "image",
             "zh": "",
             "en": ""}
        ]
    },
    {
        "page_slug": "home", "key": "intro", "name": "計畫介紹", "type": "text", "order": 2,
        "fields": [
            {"key": "title",   "label": "區塊標題", "type": "text",
             "zh": "關於本計畫",
             "en": "About the Program"},
            
            # 副標題欄位
            {"key": "subtitle", "label": "副標題", "type": "text",
             "zh": "Lead with Nordic Vision.",
             "en": "Lead with Nordic Vision."},
            
            {"key": "content", "label": "介紹內文", "type": "textarea",
             "zh": "本學程結合國立中央大學與芬蘭阿爾托大學的師資與資源，培育具國際視野的高階管理人才。",
             "en": "This program combines faculty and resources from NCU and Aalto University to cultivate global business leaders."},
            
            # 圖片存放欄位
            {"key": "image_url", "label": "計畫圖片", "type": "image",
             "zh": "", 
             "en": ""}
        ]
    },
    # ════════════════════
    # 校友分享 (alumni_sharing)
    # ════════════════════
    {
        "page_slug": "alumni", # 校友分享頁編輯
        "key": "alumni_sharing", 
        "name": "校友分享", 
        "type": "list", # 定義為列表清單
        "order": 1,
        "fields": [
            {
                "key": "alumni_list", 
                "label": "校友分享清單", 
                "type": "list", # 巢狀列表結構
                "items": [
                    {"key": "title", "label": "標題", "type": "text"},
                    {"key": "summary", "label": "內容大綱", "type": "text"},
                    {"key": "is_active", "label": "狀態", "type": "boolean"},
                    {"key": "image_url", "label": "照片", "type": "image"},
                    {"key": "date", "label": "日期", "type": "date"},
                    {"key": "content", "label": "完整內容", "type": "richtext"}
                ]
            }
        ]
    },

    # ════════════════════
    # 招生資訊 (admission)
    # ════════════════════
    {
        "page_slug": "admission", "key": "admission-hero", "name": "招生 頂部", "type": "hero", "order": 1,
        "fields": [
            {"key": "title",    "label": "主標題", "type": "text",
             "zh": "招生資訊",
             "en": "Admission Information"},
            {"key": "subtitle", "label": "副標題", "type": "text",
             "zh": "開啟您的國際 EMBA 之旅",
             "en": "Begin your international EMBA journey"},
        ]
    },
    {
        "page_slug": "admission", "key": "admission-requirements", "name": "申請資格", "type": "list", "order": 2,
        "fields": [
            {"key": "title",   "label": "區塊標題", "type": "text",
             "zh": "申請資格",
             "en": "Requirements"},
            {"key": "content", "label": "資格說明", "type": "textarea",
             "zh": "• 大學畢業\n• 5年以上工作經驗\n• 具備基本英文能力",
             "en": "• Bachelor's degree\n• 5+ years work experience\n• Basic English proficiency"},
        ]
    },

    # ════════════════════
    # 聯絡方式 (contact)
    # ════════════════════
    {
        "page_slug": "contact", "key": "contact-info", "name": "聯絡資訊", "type": "text", "order": 1,
        "fields": [
            {"key": "title",   "label": "標題",    "type": "text",
             "zh": "聯絡我們",
             "en": "Contact Us"},
            {"key": "email",   "label": "Email",   "type": "text",
             "zh": "emba@cc.ncu.edu.tw",
             "en": "emba@cc.ncu.edu.tw"},
            {"key": "phone",   "label": "電話",    "type": "text",
             "zh": "(03) 422-7151 分機 57601",
             "en": "+886-3-422-7151 ext. 57601"},
            {"key": "address", "label": "地址",    "type": "text",
             "zh": "桃園市中壢區中大路 300 號",
             "en": "No. 300, Zhongda Rd., Zhongli Dist., Taoyuan City"},
        ]
    },
]


def seed_database():
    """執行初始資料載入"""
    # 確保資料表存在
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ─── 建立管理員帳號 ───
        existing_admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not existing_admin:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"✅ 管理員帳號已建立：{ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        else:
            print(f"⏭️  管理員帳號已存在，跳過")

        # ─── 建立頁面 ───
        page_objects = {}
        for p in PAGES:
            existing = db.query(Page).filter(Page.slug == p["slug"]).first()
            if not existing:
                page = Page(
                    slug=p["slug"],
                    title=p["title"],
                    parent_slug=p["parent_slug"],
                    display_order=p["order"],
                    is_active=p["active"],
                )
                db.add(page)
                db.commit()
                db.refresh(page)
                page_objects[p["slug"]] = page
                print(f"✅ 頁面已建立：{p['title']} ({p['slug']})")
            else:
                page_objects[p["slug"]] = existing
                print(f"⏭️  頁面已存在：{p['slug']}，跳過")

        # ─── 建立區塊與內容欄位 ───
        for sec_data in SECTIONS_DATA:
            page = page_objects.get(sec_data["page_slug"])
            if not page:
                print(f"⚠️  找不到頁面 {sec_data['page_slug']}，跳過區塊 {sec_data['key']}")
                continue

            existing_section = db.query(Section).filter(
                Section.page_id == page.id,
                Section.section_key == sec_data["key"]
            ).first()

            if not existing_section:
                section = Section(
                    page_id=page.id,
                    section_key=sec_data["key"],
                    name=sec_data["name"],
                    section_type=sec_data["type"],
                    display_order=sec_data["order"],
                )
                db.add(section)
                db.commit()
                db.refresh(section)
                print(f"  ✅ 區塊已建立：{sec_data['name']}")
            else:
                section = existing_section
                print(f"  ⏭️  區塊已存在：{sec_data['key']}，跳過")

            # 建立欄位（zh-TW 和 en-US 各一份）
            for field_data in sec_data.get("fields", []):
                
                # 👇 1. 判斷欄位類型，給予正確的初始值
                if field_data.get("type") in ["list", "global_list"]:
                    # 如果是清單類型，初始值給一個空的 JSON 陣列
                    zh_value = "[]"
                    en_value = "[]"
                else:
                    # 如果是普通欄位，安全地取得 zh 和 en 的值（找不到就給空字串）
                    zh_value = field_data.get("zh", "")
                    en_value = field_data.get("en", "")

                # 👇 2. 將整理好的值帶入原本的迴圈
                for locale, value in [("zh-TW", zh_value), ("en-US", en_value)]:
                    existing_field = db.query(ContentField).filter(
                        ContentField.section_id == section.id,
                        ContentField.field_key == field_data["key"],
                        ContentField.locale == locale,
                    ).first()

                    if not existing_field:
                        field = ContentField(
                            section_id=section.id,
                            field_key=field_data["key"],
                            field_value=value,
                            field_type=field_data["type"],
                            locale=locale,
                            label=field_data["label"],
                        )
                        db.add(field)

            db.commit()

        print("\n🎉 初始資料載入完成！")
        print(f"   後台登入帳號：{ADMIN_USERNAME}")
        print(f"   後台登入密碼：{ADMIN_PASSWORD}")
        print(f"   啟動伺服器後到 http://localhost:8000/docs 測試")

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
