"""
routers/pages.py — 頁面管理 CRUD API
=======================================
提供所有頁面、區塊、欄位的新增/讀取/更新/刪除功能。

API 設計原則：
- GET    ：讀取（不需登入，Framer 前台也能直接呼叫）
- POST   ：新增（需要登入）
- PUT    ：更新（需要登入）
- DELETE ：刪除（需要登入）
"""

from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Page, Section, ContentField, User
from schemas import (
    PageCreate, PageUpdate, PageOut, PageListItem,
    SectionCreate, SectionUpdate, SectionOut,
    ContentFieldCreate, ContentFieldUpdate, ContentFieldOut,
    LocaleContentUpdate
)
from routers.auth import verify_token

# 建立路由器
router = APIRouter(prefix="/api/v1", tags=["頁面管理"])


# ════════════════════════════════════════
# 📋 Page（頁面）API
# ════════════════════════════════════════

@router.get("/pages", response_model=List[PageListItem], summary="取得所有頁面列表")
def get_pages(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="是否包含停用頁面（需登入）")
):
    """
    取得所有頁面的列表（不含詳細內容）。
    這個 API 不需要登入，Framer 前台可以直接呼叫。

    **Framer Code Component 用法：**
    ```javascript
    const response = await fetch('http://localhost:8000/api/v1/pages');
    const pages = await response.json();
    ```
    """
    query = db.query(Page)

    # 預設只顯示啟用的頁面
    if not include_inactive:
        query = query.filter(Page.is_active == True)

    pages = query.order_by(Page.display_order).all()

    # 加上每個頁面的區塊數量
    result = []
    for page in pages:
        item = PageListItem(
            id=page.id,
            slug=page.slug,
            title=page.title,
            parent_slug=page.parent_slug,
            display_order=page.display_order,
            is_active=page.is_active,
            section_count=len(page.sections)
        )
        result.append(item)

    return result


@router.get("/pages/{slug}", response_model=PageOut, summary="取得指定頁面的完整內容")
def get_page(
    slug: str,
    locale: Optional[str] = Query(None, description="語系篩選：zh-TW 或 en-US"),
    db: Session = Depends(get_db)
):
    """
    取得指定頁面的完整內容（含所有區塊與欄位）。
    可用 locale 參數篩選語系。

    **Framer Code Component 用法：**
    ```javascript
    // 取得首頁的繁體中文內容
    const response = await fetch(
      'http://localhost:8000/api/v1/pages/home?locale=zh-TW'
    );
    const page = await response.json();

    // 取得第一個區塊的標題
    const heroTitle = page.sections
      .find(s => s.section_key === 'hero')
      ?.content_fields
      .find(f => f.field_key === 'title')
      ?.field_value;
    ```
    """
    page = db.query(Page).filter(Page.slug == slug, Page.is_active == True).first()

    if not page:
        raise HTTPException(status_code=404, detail=f"找不到頁面：{slug}")

    # 如果有指定 locale，過濾欄位
    if locale:
        for section in page.sections:
            section.content_fields = [
                f for f in section.content_fields
                if f.locale == locale
            ]

    return page


@router.post("/pages", response_model=PageOut, status_code=status.HTTP_201_CREATED,
             summary="新增頁面（需要登入）")
def create_page(
    page_data: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)  # 需要登入
):
    """新增一個新頁面（後台管理用）"""
    # 檢查 slug 是否重複
    existing = db.query(Page).filter(Page.slug == page_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"頁面 slug 已存在：{page_data.slug}")

    page = Page(**page_data.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.put("/pages/{slug}", response_model=PageOut, summary="更新頁面基本資訊（需要登入）")
def update_page(
    slug: str,
    page_data: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """更新頁面的標題、排序、啟用狀態等基本資訊"""
    page = db.query(Page).filter(Page.slug == slug).first()

    if not page:
        raise HTTPException(status_code=404, detail=f"找不到頁面：{slug}")

    # 只更新有傳入的欄位（None 表示不改）
    update_data = page_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(page, key, value)

    db.commit()
    db.refresh(page)
    return page


# ════════════════════════════════════════
# 📦 Section（區塊）API
# ════════════════════════════════════════

@router.post("/pages/{slug}/sections", response_model=SectionOut,
             status_code=status.HTTP_201_CREATED, summary="新增區塊（需要登入）")
def create_section(
    slug: str,
    section_data: SectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """在指定頁面新增一個區塊"""
    page = db.query(Page).filter(Page.slug == slug).first()

    if not page:
        raise HTTPException(status_code=404, detail=f"找不到頁面：{slug}")

    section = Section(page_id=page.id, **section_data.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.put("/sections/{section_id}", response_model=SectionOut, summary="更新區塊（需要登入）")
def update_section(
    section_id: int,
    section_data: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """更新區塊名稱、排序等"""
    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊 ID：{section_id}")

    update_data = section_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(section, key, value)

    db.commit()
    db.refresh(section)
    return section


@router.delete("/sections/{section_id}", summary="刪除區塊（需要登入）")
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """刪除區塊（同時刪除該區塊的所有欄位）"""
    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊 ID：{section_id}")

    db.delete(section)
    db.commit()
    return {"message": f"已刪除區塊：{section.name}"}


# ════════════════════════════════════════
# 📝 ContentField（內容欄位）API
# ════════════════════════════════════════

@router.put("/sections/{section_id}/fields", response_model=List[ContentFieldOut],
            summary="批量更新區塊內容（需要登入）⭐ 最常用")
def update_section_content(
    section_id: int,
    update_data: LocaleContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    ⭐ 這是後台最常用的 API！
    一次更新一個區塊在指定語系下的所有欄位值。

    **前端使用方式：**
    ```javascript
    const token = localStorage.getItem('token');
    await fetch(`/api/v1/sections/${sectionId}/fields`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        locale: 'zh-TW',
        fields: {
          title: '校友分享',
          subtitle: '聆聽真實的聲音'
        }
      })
    });
    ```
    """
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊 ID：{section_id}")

    updated_fields = []

    for field_key, field_value in update_data.fields.items():
        # 查找是否已有這個 locale + field_key 的欄位
        existing_field = db.query(ContentField).filter(
            ContentField.section_id == section_id,
            ContentField.field_key == field_key,
            ContentField.locale == update_data.locale
        ).first()

        if existing_field:
            # 更新已有的欄位
            existing_field.field_value = str(field_value)
            updated_fields.append(existing_field)
        else:
            # 建立新欄位（欄位第一次輸入內容）
            new_field = ContentField(
                section_id=section_id,
                field_key=field_key,
                field_value=str(field_value),
                locale=update_data.locale
            )
            db.add(new_field)
            updated_fields.append(new_field)

    db.commit()

    # 重新查詢確保資料最新
    for field in updated_fields:
        db.refresh(field)

    return updated_fields


@router.post("/sections/{section_id}/fields", response_model=ContentFieldOut,
             status_code=status.HTTP_201_CREATED, summary="新增欄位（需要登入）")
def create_field(
    section_id: int,
    field_data: ContentFieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """在區塊內新增一個欄位（通常在設定階段用，日常操作用批量更新）"""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊 ID：{section_id}")

    field = ContentField(section_id=section_id, **field_data.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/fields/{field_id}", summary="刪除欄位（需要登入）")
def delete_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """刪除單一欄位"""
    field = db.query(ContentField).filter(ContentField.id == field_id).first()

    if not field:
        raise HTTPException(status_code=404, detail=f"找不到欄位 ID：{field_id}")

    db.delete(field)
    db.commit()
    return {"message": f"已刪除欄位：{field.field_key}"}


# ════════════════════════════════════════
# 🔍 Framer 前台專用端點（最友善的 API）
# ════════════════════════════════════════

@router.get("/content/{slug}/{section_key}", summary="取得特定區塊內容（Framer 前台用）")
def get_section_content(
    slug: str,
    section_key: str,
    locale: str = Query("zh-TW", description="語系"),
    db: Session = Depends(get_db)
):
    # 查找頁面 (如果整個頁面被停用，還是回傳 404)
    page = db.query(Page).filter(Page.slug == slug, Page.is_active == True).first()
    if not page:
        raise HTTPException(status_code=404, detail=f"找不到頁面：{slug}")

    # 查找區塊 (⚠️ 注意：這裡拿掉 is_active==True 的過濾，讓 Framer 也能讀到停用的區塊)
    section = db.query(Section).filter(
        Section.page_id == page.id,
        Section.section_key == section_key
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊：{section_key}")

    # 取得該語系的所有欄位
    fields = db.query(ContentField).filter(
        ContentField.section_id == section.id,
        ContentField.locale == locale
    ).all()

    fields_dict = {field.field_key: field.field_value for field in fields}

    return {
        "page": slug,
        "section": section_key,
        "locale": locale,
        "section_name": section.name,
        "is_active": section.is_active,  # 👈 關鍵：把狀態傳給 Framer！
        "fields": fields_dict
    }


# ════════════════════════════════════════
# 🗑️  Page DELETE（刪除頁面）
# ════════════════════════════════════════

@router.delete("/pages/{slug}", summary="刪除頁面（需要登入）")
def delete_page(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    刪除指定頁面，同時刪除其下所有區塊與欄位（CASCADE）。
    若該頁面有子頁面，子頁面的 parent_slug 會被清空（變為頂層頁面）。
    """
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail=f"找不到頁面：{slug}")

    # 將子頁面的 parent_slug 清空，避免孤兒資料
    db.query(Page).filter(Page.parent_slug == slug).update({"parent_slug": None})

    db.delete(page)
    db.commit()
    return {"message": f"已刪除頁面：{page.title}（{slug}）"}


# ════════════════════════════════════════
# 🌳 頁面樹狀結構（後台管理用）
# ════════════════════════════════════════

@router.get("/page-tree", summary="取得頁面樹狀結構（後台管理用）")
def get_page_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """
    回傳完整的頁面樹狀結構，方便後台渲染階層式頁面管理介面。

    回傳格式：
    [
      { id, slug, title, is_active, section_count, children: [...] },
      ...
    ]
    """
    all_pages = db.query(Page).order_by(Page.display_order).all()

    # 先建立 dict（slug -> page data）
    page_map = {}
    for p in all_pages:
        page_map[p.slug] = {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "parent_slug": p.parent_slug,
            "display_order": p.display_order,
            "is_active": p.is_active,
            "section_count": len(p.sections),
            "children": []
        }

    # 建立樹狀結構
    roots = []
    for slug, page in page_map.items():
        parent = page["parent_slug"]
        if parent and parent in page_map:
            page_map[parent]["children"].append(page)
        else:
            roots.append(page)

    return roots

# ════════════════════════════════════════
# 🔘 Section 狀態切換 API
# ════════════════════════════════════════
class SectionStatusUpdate(BaseModel):
    is_active: bool

@router.patch("/sections/{section_id}/status", response_model=SectionOut, summary="切換區塊啟用狀態（需要登入）")
def update_section_status(
    section_id: int,
    status_data: SectionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """專門用來切換區塊的停用/啟用狀態（軟刪除）"""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail=f"找不到區塊 ID：{section_id}")

    section.is_active = status_data.is_active
    db.commit()
    db.refresh(section)
    return section