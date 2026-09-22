# Data Dictionary

## Raw source — `vendas.csv`

This is the only source dataset in the repository.

| Column | Description |
|---|---|
| sale_id | Transaction identifier |
| sale_date | Transaction date |
| customer_id | Customer identifier |
| customer_name | Customer display name |
| customer_segment | Customer business segment |
| city | Customer city |
| state | Brazilian state code |
| region | Brazilian macro-region |
| region_id | Geography business key |
| product_id | Product identifier |
| product_name | Product name |
| category | Product category |
| subcategory | Product subcategory |
| unit_price | Selling price per unit |
| quantity | Transaction quantity |
| discount_pct | Discount rate |
| unit_cost | Cost per unit |
| seller_id | Seller identifier |
| seller_name | Seller name |
| seller_team | Commercial team |
| channel | Sales channel |
| order_status | Transaction status |

## Generated — FactSales

Grain: one row per valid transaction after ETL.

| Column | Description |
|---|---|
| sale_id | Transaction key |
| date_id | Date dimension key |
| customer_id | Customer dimension key |
| product_id | Product dimension key |
| seller_id | Seller dimension key |
| region_id | Region dimension key |
| channel | Sales channel |
| order_status | Concluído or Devolvido |
| unit_price | Unit selling price |
| quantity | Original transaction quantity |
| net_quantity | Signed quantity after returns |
| discount_pct | Discount rate |
| gross_revenue | Revenue before discount |
| discount_amount | Discount value |
| net_revenue | Revenue after discount |
| unit_cost | Unit cost |
| total_cost | Signed transaction cost |
| gross_profit | Net revenue less total cost |
| margin_pct | Transaction gross-margin percentage |

## Generated dimensions

### DimCustomer
`customer_id`, `customer_name`, `segment`, `city`, `state`, `region_id`

### DimProduct
`product_id`, `product_name`, `category`, `subcategory`

### DimSeller
`seller_id`, `seller_name`, `team`

### DimRegion
`region_id`, `region`, `state`

### DimDate
`date_id`, `date`, `year`, `quarter`, `month_number`, `month_name`,
`year_month`, `day`, `weekday_number`, `weekday_name`, `is_weekend`
