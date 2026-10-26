from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.user_mgr import super_admin_required
from db.sqlalchemy_define import get_db
from services.acquisition_analytics_service import (
    CANONICAL_CATEGORIES,
    build_acquisition_analysis,
    build_category_detail,
    build_order_drilldown,
)


router = APIRouter(prefix="/acquisition", tags=["获客机会分析"])


def _load_fact_rows(db: Session):
    return db.execute(
        text(
            """
            SELECT
                performance.id,
                performance.company_tracking_no,
                performance.shipping_date,
                performance.product_name,
                performance.shipping_channel,
                performance.salesman,
                performance.shipping_fee,
                performance.shipping_cost,
                performance.goods_weight,
                performance.goods_volume,
                performance.remark,
                trade.id AS trade_id,
                trade.shipping_customer,
                trade.receiving_address,
                trade.scheduling_status
            FROM t_performance_statement performance
            LEFT JOIN t_consignment_trade trade
              ON trade.order_no = performance.company_tracking_no
            ORDER BY performance.shipping_date, performance.company_tracking_no, performance.id
            """
        )
    ).mappings().all()


def _build(
    db: Session,
    start_date: Optional[date],
    end_date: Optional[date],
    category: Optional[str],
    channel: Optional[str],
    identifiable_only: bool,
    new_customers_only: bool,
    min_orders: int,
    min_new_customers: int,
    max_negative_rate_pct: float,
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "开始日期不能晚于结束日期")
    if category and category not in CANONICAL_CATEGORIES:
        raise HTTPException(422, "不支持的规范品类")
    rows = _load_fact_rows(db)
    return build_acquisition_analysis(
        rows,
        start_date=start_date,
        end_date=end_date,
        category=category,
        channel=channel,
        identifiable_only=identifiable_only,
        new_customers_only=new_customers_only,
        min_orders=min_orders,
        min_new_customers=min_new_customers,
        max_negative_rate=max_negative_rate_pct,
    ), rows


@router.get("/overview", summary="获客机会总览")
def acquisition_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    identifiable_only: bool = Query(False),
    new_customers_only: bool = Query(False),
    min_orders: int = Query(20, ge=1, le=10000),
    min_new_customers: int = Query(5, ge=1, le=1000),
    max_negative_rate_pct: float = Query(30, ge=0, le=100),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    analysis, _ = _build(
        db, start_date, end_date, category, channel, identifiable_only,
        new_customers_only, min_orders, min_new_customers, max_negative_rate_pct,
    )
    return {"code": 200, "message": "success", "data": analysis}


@router.get("/categories", summary="获客品类排行")
def acquisition_categories(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    channel: Optional[str] = Query(None),
    min_orders: int = Query(20, ge=1, le=10000),
    min_new_customers: int = Query(5, ge=1, le=1000),
    max_negative_rate_pct: float = Query(30, ge=0, le=100),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    analysis, _ = _build(
        db, start_date, end_date, None, channel, False, False,
        min_orders, min_new_customers, max_negative_rate_pct,
    )
    return {"code": 200, "message": "success", "data": analysis["categories"]}


@router.get("/orders", summary="获客指标订单明细")
def acquisition_order_drilldown(
    scope: str = Query("all"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    salesman: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "开始日期不能晚于结束日期")
    if category and category not in CANONICAL_CATEGORIES:
        raise HTTPException(422, "不支持的规范品类")
    try:
        rows = build_order_drilldown(
            _load_fact_rows(db), scope, start_date, end_date, category, channel, salesman, customer,
        )
    except ValueError as exc:
        raise HTTPException(422, "不支持的明细类型") from exc
    offset = (page - 1) * page_size
    return {
        "code": 200,
        "message": "success",
        "data": {
            "scope": scope,
            "total": len(rows),
            "page": page,
            "page_size": page_size,
            "items": rows[offset:offset + page_size],
        },
    }


@router.get("/categories/{category}", summary="获客品类详情")
def acquisition_category_detail(
    category: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    channel: Optional[str] = Query(None),
    salesman: Optional[str] = Query(None),
    min_orders: int = Query(20, ge=1, le=10000),
    min_new_customers: int = Query(5, ge=1, le=1000),
    max_negative_rate_pct: float = Query(30, ge=0, le=100),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    analysis, rows = _build(
        db, start_date, end_date, category, channel, False, False,
        min_orders, min_new_customers, max_negative_rate_pct,
    )
    detail = build_category_detail(analysis, rows, category, channel=channel, salesman=salesman)
    if not detail:
        raise HTTPException(404, "当前筛选范围没有该品类数据")
    return {"code": 200, "message": "success", "data": detail}


@router.get("/cohorts", summary="获客 cohort 指标")
def acquisition_cohorts(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    analysis, _ = _build(db, start_date, end_date, category, None, False, False, 20, 5, 30)
    data = [
        {"category": item["category"], "cohort_30": item["cohort_30"], "cohort_90": item["cohort_90"]}
        for item in analysis["categories"]
    ]
    return {"code": 200, "message": "success", "data": data}


@router.get("/data-quality", summary="获客分析数据质量")
def acquisition_data_quality(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    analysis, _ = _build(db, start_date, end_date, None, None, False, False, 20, 5, 30)
    return {"code": 200, "message": "success", "data": analysis["quality"]}
