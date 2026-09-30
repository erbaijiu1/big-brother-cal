from datetime import date
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

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
