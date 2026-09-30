from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.login import jwt_auth
from api.user_mgr import super_admin_required
from db.sqlalchemy_define import get_db


router = APIRouter(
    prefix="/business_stats",
    tags=["经营统计"],
    dependencies=[Depends(jwt_auth)],
)


def _plain_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def _rows(result: Iterable[Any]) -> List[Dict[str, Any]]:
    return [
        {key: _plain_value(value) for key, value in row.items()}
        for row in result
    ]


def _row(result: Any) -> Dict[str, Any]:
    row = result.one()
    return {key: _plain_value(value) for key, value in row.items()}


def _validate_range(start_date: Optional[date], end_date: Optional[date]) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "开始日期不能晚于结束日期")


def _month_bounds(month: str) -> tuple[date, date]:
    try:
        start = datetime.strptime(f"{month}-01", "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(422, "月份格式必须为 YYYY-MM") from exc

    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)
    return start, end


def _previous_month(month_start: date) -> str:
    if month_start.month == 1:
        return f"{month_start.year - 1}-12"
    return f"{month_start.year}-{month_start.month - 1:02d}"


def _change_pct(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 2)


GROWTH_DIMENSIONS = {
    "products": {
        "label": "产品",
        "expression": "COALESCE(NULLIF(TRIM(product_name), ''), '未知产品')",
    },
    "channels": {
        "label": "渠道",
        "expression": "COALESCE(NULLIF(TRIM(shipping_channel), ''), '未知渠道')",
    },
    "salesmen": {
        "label": "业务员",
        "expression": "COALESCE(NULLIF(TRIM(salesman), ''), '未知业务员')",
    },
    "weights": {
        "label": "重量段",
        "expression": """
            CASE
                WHEN goods_weight <= 0 THEN '未知/0'
                WHEN goods_weight <= 20 THEN '0-20kg'
                WHEN goods_weight <= 50 THEN '20-50kg'
                WHEN goods_weight <= 100 THEN '50-100kg'
                WHEN goods_weight <= 300 THEN '100-300kg'
                WHEN goods_weight <= 500 THEN '300-500kg'
                WHEN goods_weight <= 1000 THEN '500-1000kg'
                WHEN goods_weight <= 3000 THEN '1000-3000kg'
                ELSE '3000kg以上'
            END
        """,
    },
}


@router.get("/overview", summary="经营统计总览")
def get_business_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    _validate_range(start_date, end_date)

    params = {"start_date": start_date, "end_date": end_date}
    performance_filter = """
        WHERE (:start_date IS NULL OR shipping_date >= :start_date)
          AND (:end_date IS NULL OR shipping_date <= :end_date)
    """
    trade_filter = """
        WHERE (:start_date IS NULL OR STR_TO_DATE(LEFT(shipping_date, 10), '%Y-%m-%d') >= :start_date)
          AND (:end_date IS NULL OR STR_TO_DATE(LEFT(shipping_date, 10), '%Y-%m-%d') <= :end_date)
    """

    summary = _row(
        db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS order_count,
                    ROUND(COALESCE(SUM(shipping_fee), 0), 2) AS total_shipping_fee,
                    ROUND(COALESCE(SUM(shipping_cost), 0), 2) AS total_shipping_cost,
                    ROUND(COALESCE(SUM(actual_performance), 0), 2) AS total_profit,
                    ROUND(COALESCE(AVG(actual_performance), 0), 2) AS avg_order_profit,
                    ROUND(
                        COALESCE(SUM(actual_performance) / NULLIF(SUM(shipping_fee), 0) * 100, 0),
                        2
                    ) AS profit_rate_pct,
                    ROUND(COALESCE(SUM(goods_weight), 0), 2) AS total_weight_kg,
                    ROUND(COALESCE(SUM(goods_volume), 0), 3) AS total_volume_cbm,
                    MIN(shipping_date) AS min_shipping_date,
                    MAX(shipping_date) AS max_shipping_date
                FROM t_performance_statement
                {performance_filter}
                """
            ),
            params,
        ).mappings()
    )

    customer_summary = _row(
        db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS trade_count,
                    COUNT(DISTINCT NULLIF(TRIM(shipping_customer), '')) AS customer_count
                FROM t_consignment_trade
                {trade_filter}
                """
            ),
            params,
        ).mappings()
    )
    summary.update(customer_summary)

    monthly = _rows(
        db.execute(
            text(
                f"""
                SELECT
                    DATE_FORMAT(shipping_date, '%Y-%m') AS month,
                    COUNT(*) AS order_count,
                    ROUND(SUM(shipping_fee), 2) AS total_shipping_fee,
                    ROUND(SUM(actual_performance), 2) AS total_profit,
                    ROUND(AVG(actual_performance), 2) AS avg_order_profit
                FROM t_performance_statement
                {performance_filter}
                GROUP BY DATE_FORMAT(shipping_date, '%Y-%m')
                ORDER BY month
                """
            ),
            params,
        ).mappings()
    )

    products = _rows(
        db.execute(
            text(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(product_name), ''), '未知产品') AS name,
                    COUNT(*) AS order_count,
                    ROUND(SUM(shipping_fee), 2) AS total_shipping_fee,
                    ROUND(SUM(actual_performance), 2) AS total_profit,
                    ROUND(AVG(actual_performance), 2) AS avg_order_profit,
                    ROUND(
                        COALESCE(SUM(actual_performance) / NULLIF(SUM(shipping_fee), 0) * 100, 0),
                        2
                    ) AS profit_rate_pct
                FROM t_performance_statement
                {performance_filter}
                GROUP BY COALESCE(NULLIF(TRIM(product_name), ''), '未知产品')
                ORDER BY total_profit DESC
                LIMIT 12
                """
            ),
            params,
        ).mappings()
    )

    channels = _rows(
        db.execute(
            text(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(shipping_channel), ''), '未知渠道') AS name,
                    COUNT(*) AS order_count,
                    ROUND(SUM(shipping_fee), 2) AS total_shipping_fee,
                    ROUND(SUM(actual_performance), 2) AS total_profit,
                    ROUND(AVG(actual_performance), 2) AS avg_order_profit,
                    ROUND(
                        COALESCE(SUM(actual_performance) / NULLIF(SUM(shipping_fee), 0) * 100, 0),
                        2
                    ) AS profit_rate_pct
                FROM t_performance_statement
                {performance_filter}
                GROUP BY COALESCE(NULLIF(TRIM(shipping_channel), ''), '未知渠道')
                ORDER BY total_profit DESC
                """
            ),
            params,
        ).mappings()
    )

    weights = _rows(
        db.execute(
            text(
                f"""
                SELECT
                    CASE
                        WHEN goods_weight <= 0 THEN '未知/0'
                        WHEN goods_weight <= 20 THEN '0-20kg'
                        WHEN goods_weight <= 50 THEN '20-50kg'
                        WHEN goods_weight <= 100 THEN '50-100kg'
                        WHEN goods_weight <= 300 THEN '100-300kg'
                        WHEN goods_weight <= 500 THEN '300-500kg'
                        WHEN goods_weight <= 1000 THEN '500-1000kg'
                        WHEN goods_weight <= 3000 THEN '1000-3000kg'
                        ELSE '3000kg以上'
                    END AS name,
                    MIN(
                        CASE
                            WHEN goods_weight <= 0 THEN 0
                            WHEN goods_weight <= 20 THEN 1
                            WHEN goods_weight <= 50 THEN 2
                            WHEN goods_weight <= 100 THEN 3
                            WHEN goods_weight <= 300 THEN 4
                            WHEN goods_weight <= 500 THEN 5
                            WHEN goods_weight <= 1000 THEN 6
                            WHEN goods_weight <= 3000 THEN 7
                            ELSE 8
                        END
                    ) AS sort_order,
                    COUNT(*) AS order_count,
                    ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 2) AS order_pct,
                    ROUND(SUM(actual_performance), 2) AS total_profit,
                    ROUND(AVG(actual_performance), 2) AS avg_order_profit,
                    ROUND(
                        COALESCE(SUM(actual_performance) / NULLIF(SUM(shipping_fee), 0) * 100, 0),
                        2
                    ) AS profit_rate_pct
                FROM t_performance_statement
                {performance_filter}
                GROUP BY name
                ORDER BY sort_order
                """
            ),
            params,
        ).mappings()
    )

    repurchase = _rows(
        db.execute(
            text(
                f"""
                WITH customer_orders AS (
                    SELECT TRIM(shipping_customer) AS customer, COUNT(*) AS order_count
                    FROM t_consignment_trade
                    {trade_filter}
                      AND NULLIF(TRIM(shipping_customer), '') IS NOT NULL
                    GROUP BY TRIM(shipping_customer)
                )
                SELECT
                    CASE
                        WHEN order_count = 1 THEN '1次'
                        WHEN order_count BETWEEN 2 AND 3 THEN '2-3次'
                        WHEN order_count BETWEEN 4 AND 10 THEN '4-10次'
                        WHEN order_count BETWEEN 11 AND 30 THEN '11-30次'
                        ELSE '30次以上'
                    END AS name,
                    MIN(order_count) AS sort_order,
                    COUNT(*) AS customer_count,
                    ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 2) AS customer_pct
                FROM customer_orders
                GROUP BY name
                ORDER BY sort_order
                """
            ),
            params,
        ).mappings()
    )

    join_quality = _row(
        db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS trade_total,
                    COUNT(performance_codes.shipping_no) AS matched_count,
                    ROUND(
                        COUNT(performance_codes.shipping_no) / NULLIF(COUNT(*), 0) * 100,
                        2
                    ) AS matched_pct
                FROM t_consignment_trade trade_rows
                LEFT JOIN (
                    SELECT DISTINCT shipping_no
                    FROM t_performance_statement
                    WHERE NULLIF(shipping_no, '') IS NOT NULL
                ) performance_codes
                    ON performance_codes.shipping_no = trade_rows.shipping_code
                WHERE NULLIF(trade_rows.shipping_code, '') IS NOT NULL
                """
            )
        ).mappings()
    )

    top_customers = _rows(
        db.execute(
            text(
                f"""
                WITH customer_by_code AS (
                    SELECT
                        shipping_code,
                        MAX(TRIM(shipping_customer)) AS customer
                    FROM t_consignment_trade
                    {trade_filter}
                      AND NULLIF(shipping_code, '') IS NOT NULL
                      AND NULLIF(TRIM(shipping_customer), '') IS NOT NULL
                    GROUP BY shipping_code
                    HAVING COUNT(DISTINCT TRIM(shipping_customer)) = 1
                )
                SELECT
                    customer_by_code.customer AS name,
                    COUNT(*) AS order_count,
                    COUNT(DISTINCT DATE_FORMAT(performance.shipping_date, '%Y-%m')) AS active_months,
                    ROUND(SUM(performance.shipping_fee), 2) AS total_shipping_fee,
                    ROUND(SUM(performance.actual_performance), 2) AS total_profit,
                    ROUND(AVG(performance.actual_performance), 2) AS avg_order_profit,
                    ROUND(
                        COALESCE(
                            SUM(performance.actual_performance)
                            / NULLIF(SUM(performance.shipping_fee), 0) * 100,
                            0
                        ),
                        2
                    ) AS profit_rate_pct
                FROM t_performance_statement performance
                JOIN customer_by_code
                    ON customer_by_code.shipping_code = performance.shipping_no
                {performance_filter.replace('shipping_date', 'performance.shipping_date')}
                GROUP BY customer_by_code.customer
                ORDER BY total_profit DESC
                LIMIT 12
                """
            ),
            params,
        ).mappings()
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "summary": summary,
            "monthly": monthly,
            "products": products,
            "channels": channels,
            "weights": weights,
            "repurchase": repurchase,
            "join_quality": join_quality,
            "top_customers": top_customers,
        },
    }


@router.get("/growth", summary="月度增长诊断")
def get_monthly_growth(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    compare_month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    current_start, current_end = _month_bounds(month)
    comparison_month = compare_month or _previous_month(current_start)
    previous_start, previous_end = _month_bounds(comparison_month)
    if comparison_month == month:
        raise HTTPException(422, "对比月份不能与目标月份相同")

    params = {
        "current_start": current_start,
        "current_end": current_end,
        "previous_start": previous_start,
        "previous_end": previous_end,
    }
    summary = _row(
        db.execute(
            text(
                """
                SELECT
                    SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN 1 ELSE 0 END) AS current_orders,
                    SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN 1 ELSE 0 END) AS previous_orders,
                    ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance ELSE 0 END), 0), 2) AS current_profit,
                    ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance ELSE 0 END), 0), 2) AS previous_profit,
                    ROUND(COALESCE(AVG(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance END), 0), 2) AS current_avg_profit,
                    ROUND(COALESCE(AVG(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance END), 0), 2) AS previous_avg_profit
                FROM t_performance_statement
                WHERE (shipping_date >= :current_start AND shipping_date < :current_end)
                   OR (shipping_date >= :previous_start AND shipping_date < :previous_end)
                """
            ),
            params,
        ).mappings()
    )

    current_orders = int(summary["current_orders"] or 0)
    previous_orders = int(summary["previous_orders"] or 0)
    current_profit = float(summary["current_profit"] or 0)
    previous_profit = float(summary["previous_profit"] or 0)
    current_avg = float(summary["current_avg_profit"] or 0)
    previous_avg = float(summary["previous_avg_profit"] or 0)
    profit_delta = round(current_profit - previous_profit, 2)
    order_delta = current_orders - previous_orders
    avg_delta = round(current_avg - previous_avg, 2)

    volume_effect = round(order_delta * previous_avg, 2)
    unit_effect = round(current_orders * avg_delta, 2)
    summary.update(
        {
            "profit_delta": profit_delta,
            "profit_change_pct": _change_pct(current_profit, previous_profit),
            "order_delta": order_delta,
            "order_change_pct": _change_pct(current_orders, previous_orders),
            "avg_profit_delta": avg_delta,
            "avg_profit_change_pct": _change_pct(current_avg, previous_avg),
            "volume_effect": volume_effect,
            "unit_effect": unit_effect,
            "volume_effect_pct": round(volume_effect / profit_delta * 100, 2) if profit_delta else 0,
            "unit_effect_pct": round(unit_effect / profit_delta * 100, 2) if profit_delta else 0,
        }
    )

    contributions: Dict[str, List[Dict[str, Any]]] = {}
    for key, dimension in GROWTH_DIMENSIONS.items():
        expression = dimension["expression"]
        contributions[key] = _rows(
            db.execute(
                text(
                    f"""
                    SELECT
                        {expression} AS name,
                        SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN 1 ELSE 0 END) AS current_orders,
                        SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN 1 ELSE 0 END) AS previous_orders,
                        ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance ELSE 0 END), 0), 2) AS current_profit,
                        ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance ELSE 0 END), 0), 2) AS previous_profit,
                        ROUND(
                            COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance ELSE 0 END), 0)
                            - COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance ELSE 0 END), 0),
                            2
                        ) AS delta_profit
                    FROM t_performance_statement
                    WHERE (shipping_date >= :current_start AND shipping_date < :current_end)
                       OR (shipping_date >= :previous_start AND shipping_date < :previous_end)
                    GROUP BY name
                    ORDER BY ABS(delta_profit) DESC
                    LIMIT 12
                    """
                ),
                params,
            ).mappings()
        )
        for item in contributions[key]:
            item["order_delta"] = int(item["current_orders"] or 0) - int(item["previous_orders"] or 0)

    customer_segments = _rows(
        db.execute(
            text(
                """
                WITH customer_by_code AS (
                    SELECT shipping_code, MAX(TRIM(shipping_customer)) AS customer
                    FROM t_consignment_trade
                    WHERE NULLIF(shipping_code, '') IS NOT NULL
                      AND NULLIF(TRIM(shipping_customer), '') IS NOT NULL
                    GROUP BY shipping_code
                    HAVING COUNT(DISTINCT TRIM(shipping_customer)) = 1
                ), customer_activity AS (
                    SELECT
                        customer_by_code.customer,
                        MIN(performance.shipping_date) AS first_shipping_date,
                        SUM(CASE WHEN performance.shipping_date >= :current_start AND performance.shipping_date < :current_end THEN 1 ELSE 0 END) AS current_orders,
                        SUM(CASE WHEN performance.shipping_date >= :previous_start AND performance.shipping_date < :previous_end THEN 1 ELSE 0 END) AS previous_orders,
                        COALESCE(SUM(CASE WHEN performance.shipping_date >= :current_start AND performance.shipping_date < :current_end THEN performance.actual_performance ELSE 0 END), 0) AS current_profit,
                        COALESCE(SUM(CASE WHEN performance.shipping_date >= :previous_start AND performance.shipping_date < :previous_end THEN performance.actual_performance ELSE 0 END), 0) AS previous_profit
                    FROM t_performance_statement performance
                    JOIN customer_by_code ON customer_by_code.shipping_code = performance.shipping_no
                    GROUP BY customer_by_code.customer
                ), labeled AS (
                    SELECT
                        CASE
                            WHEN current_orders > 0 AND first_shipping_date >= :current_start THEN 'new'
                            WHEN current_orders > 0 AND previous_orders = 0 THEN 'reactivated'
                            WHEN current_orders > 0 AND previous_orders > 0 THEN 'retained'
                            WHEN current_orders = 0 AND previous_orders > 0 THEN 'lost'
                        END AS segment,
                        current_orders,
                        previous_orders,
                        current_profit,
                        previous_profit
                    FROM customer_activity
                    WHERE current_orders > 0 OR previous_orders > 0
                )
                SELECT
                    segment AS name,
                    COUNT(*) AS customer_count,
                    SUM(current_orders) AS current_orders,
                    SUM(previous_orders) AS previous_orders,
                    ROUND(SUM(current_profit), 2) AS current_profit,
                    ROUND(SUM(previous_profit), 2) AS previous_profit,
                    ROUND(SUM(current_profit) - SUM(previous_profit), 2) AS delta_profit,
                    SUM(CASE WHEN current_profit > previous_profit THEN 1 ELSE 0 END) AS growing_customers
                FROM labeled
                WHERE segment IS NOT NULL
                GROUP BY segment
                """
            ),
            params,
        ).mappings()
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "month": month,
            "compare_month": comparison_month,
            "summary": summary,
            "contributions": contributions,
            "customer_segments": customer_segments,
        },
    }


@router.get("/growth/detail", summary="增长贡献明细")
def get_growth_detail(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    compare_month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    dimension: Literal["products", "channels", "weights", "salesmen"] = "products",
    keyword: Optional[str] = Query(None, max_length=100),
    sort_by: Literal["impact", "delta_profit", "current_profit", "order_delta", "current_orders", "name"] = "impact",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(super_admin_required),
):
    current_start, current_end = _month_bounds(month)
    comparison_month = compare_month or _previous_month(current_start)
    previous_start, previous_end = _month_bounds(comparison_month)
    if comparison_month == month:
        raise HTTPException(422, "对比月份不能与目标月份相同")

    dimension_config = GROWTH_DIMENSIONS[dimension]
    expression = dimension_config["expression"]
    grouped_sql = f"""
        SELECT
            {expression} AS name,
            SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN 1 ELSE 0 END) AS current_orders,
            SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN 1 ELSE 0 END) AS previous_orders,
            ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN shipping_fee ELSE 0 END), 0), 2) AS current_revenue,
            ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN shipping_fee ELSE 0 END), 0), 2) AS previous_revenue,
            ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance ELSE 0 END), 0), 2) AS current_profit,
            ROUND(COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance ELSE 0 END), 0), 2) AS previous_profit,
            ROUND(
                COALESCE(SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN actual_performance ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN actual_performance ELSE 0 END), 0),
                2
            ) AS delta_profit,
            SUM(CASE WHEN shipping_date >= :current_start AND shipping_date < :current_end THEN 1 ELSE 0 END)
                - SUM(CASE WHEN shipping_date >= :previous_start AND shipping_date < :previous_end THEN 1 ELSE 0 END) AS order_delta
        FROM t_performance_statement
        WHERE (shipping_date >= :current_start AND shipping_date < :current_end)
           OR (shipping_date >= :previous_start AND shipping_date < :previous_end)
        GROUP BY name
    """
    params = {
        "current_start": current_start,
        "current_end": current_end,
        "previous_start": previous_start,
        "previous_end": previous_end,
        "keyword": f"%{keyword.strip()}%" if keyword and keyword.strip() else None,
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    total = int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM ({grouped_sql}) grouped_rows
                WHERE (:keyword IS NULL OR name LIKE :keyword)
                """
            ),
            params,
        ).scalar()
        or 0
    )

    order_expressions = {
        "impact": "ABS(delta_profit)",
        "delta_profit": "delta_profit",
        "current_profit": "current_profit",
        "order_delta": "order_delta",
        "current_orders": "current_orders",
        "name": "name",
    }
    order_expression = order_expressions[sort_by]
    direction = "ASC" if sort_order == "asc" else "DESC"
    items = _rows(
        db.execute(
            text(
                f"""
                SELECT *
                FROM ({grouped_sql}) grouped_rows
                WHERE (:keyword IS NULL OR name LIKE :keyword)
                ORDER BY {order_expression} {direction}, name ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).mappings()
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "month": month,
            "compare_month": comparison_month,
            "dimension": dimension,
            "dimension_label": dimension_config["label"],
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
        },
    }
