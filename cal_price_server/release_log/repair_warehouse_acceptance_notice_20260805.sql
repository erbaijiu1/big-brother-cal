SET NAMES utf8mb4;

UPDATE t_goods_classification SET acceptance_notice = ''
WHERE category_id IN (1, 2, 3, 4, 8, 9, 11, 14, 18);

UPDATE t_goods_classification
SET acceptance_notice = CASE category_id
    WHEN 5 THEN '危险品申报，需确认MSDS及危包资料'
    WHEN 6 THEN '需确认酒精度及申报资料'
    WHEN 7 THEN '危险化学品需确认MSDS、危包及运输条件'
    WHEN 10 THEN '高价值货物需确认包装、保险及安保条件'
    WHEN 12 THEN '液体货物需确认成分、酒精含量及防泄漏包装'
    WHEN 15 THEN '水生动物需确认活体包装及运输条件'
    WHEN 16 THEN '鲜活货物需确认检疫或许可资料'
    WHEN 17 THEN '植物需确认检疫及原产地资料'
    ELSE '入仓前需人工确认'
END
WHERE category_id IN (5, 6, 7, 10, 12, 15, 16, 17);

UPDATE t_goods_classification
SET acceptance_notice = '禁运或限运品，暂不承运'
WHERE category_id = 13;
