-- Category-wise revenue, quantity, and profit
SELECT
    [Product Category],
    SUM([Sales Amount]) AS total_revenue,
    SUM([Quantity Sold]) AS total_quantity,
    SUM([Profit]) AS total_profit,
    AVG([Sales Amount]) AS average_sale
FROM sales_data
GROUP BY [Product Category]
ORDER BY total_revenue DESC;

-- Monthly sales trend by category
SELECT
    FORMAT([Order Date], 'yyyy-MM') AS sales_month,
    [Product Category],
    SUM([Sales Amount]) AS monthly_revenue
FROM sales_data
GROUP BY FORMAT([Order Date], 'yyyy-MM'), [Product Category]
ORDER BY sales_month, monthly_revenue DESC;

-- Most profitable category
SELECT TOP 1
    [Product Category],
    SUM([Profit]) AS total_profit
FROM sales_data
GROUP BY [Product Category]
ORDER BY total_profit DESC;

-- Region-wise summary
SELECT
    [Region],
    SUM([Sales Amount]) AS total_revenue,
    SUM([Profit]) AS total_profit,
    SUM([Quantity Sold]) AS total_quantity
FROM sales_data
GROUP BY [Region]
ORDER BY total_revenue DESC;
