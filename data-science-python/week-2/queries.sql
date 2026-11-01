-- Week 2: SQL for data analysis. Table: orders(order_id, customer_name, order_date, category,
-- sub_category, product_name, quantity, unit_price, total_price, region)

-- 1. Top 5 customers by total spend
SELECT customer_name, COUNT(*) AS orders, SUM(total_price) AS total_spent
FROM orders
GROUP BY customer_name
ORDER BY total_spent DESC
LIMIT 5;

-- 2. Overall average order value, and by region
SELECT 'All regions' AS region, ROUND(AVG(total_price), 2) AS avg_order_value, COUNT(*) AS orders FROM orders
UNION ALL
SELECT region, ROUND(AVG(total_price), 2), COUNT(*) FROM orders GROUP BY region
ORDER BY avg_order_value DESC;

-- 3. Revenue and units by category and sub-category (aggregation with GROUP BY and ORDER BY)
SELECT category, sub_category, SUM(quantity) AS units, SUM(total_price) AS revenue
FROM orders
GROUP BY category, sub_category
ORDER BY revenue DESC;

-- 4. Customers whose total spend is above the average customer's total spend (subquery)
SELECT customer_name, SUM(total_price) AS total_spent
FROM orders
GROUP BY customer_name
HAVING SUM(total_price) > (SELECT AVG(spent) FROM (SELECT SUM(total_price) AS spent FROM orders GROUP BY customer_name))
ORDER BY total_spent DESC
LIMIT 10;

-- 5. Order size bands with CASE
SELECT CASE WHEN total_price >= 40000 THEN 'Large (40k+)'
            WHEN total_price >= 15000 THEN 'Medium (15k-40k)'
            ELSE 'Small (<15k)' END AS order_band,
       COUNT(*) AS orders, ROUND(AVG(total_price), 2) AS avg_value
FROM orders
GROUP BY order_band
ORDER BY avg_value DESC;

-- 6. Join each order to its region's average, and keep the biggest orders above that average
SELECT o.order_id, o.customer_name, o.region, o.total_price, ROUND(r.avg_value, 2) AS region_avg,
       ROUND(o.total_price / r.avg_value, 1) AS times_region_avg
FROM orders AS o
JOIN (SELECT region, AVG(total_price) AS avg_value FROM orders GROUP BY region) AS r ON r.region = o.region
WHERE o.total_price > r.avg_value
ORDER BY times_region_avg DESC
LIMIT 5;

-- 7. Monthly revenue
SELECT substr(order_date, 1, 7) AS month, SUM(total_price) AS revenue
FROM orders
GROUP BY month
ORDER BY month;
