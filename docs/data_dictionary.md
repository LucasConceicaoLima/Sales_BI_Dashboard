# Dicionário de Dados

## Fonte de dados — `vendas.csv`

Este é o único conjunto de dados de origem do repositório.

| Coluna | Descrição |
|---|---|
| sale_id | Identificador da transação |
| sale_date | Data da transação |
| customer_id | Identificador do cliente |
| customer_name | Nome do cliente |
| customer_segment | Segmento do cliente |
| city | Cidade do cliente |
| state | Sigla do estado brasileiro |
| region | Macrorregião brasileira |
| region_id | Chave de identificação da região |
| product_id | Identificador do produto |
| product_name | Nome do produto |
| category | Categoria do produto |
| subcategory | Subcategoria do produto |
| unit_price | Preço de venda por unidade |
| quantity | Quantidade da transação |
| discount_pct | Percentual de desconto |
| unit_cost | Custo por unidade |
| seller_id | Identificador do vendedor |
| seller_name | Nome do vendedor |
| seller_team | Equipe comercial |
| channel | Canal de venda |
| order_status | Status da transação |

## Gerada — fato_vendas

**Grão:** uma linha por transação válida após o processo de ETL.

| Coluna | Descrição |
|---|---|
| sale_id | Chave da transação |
| date_id | Chave da dimensão de data |
| customer_id | Chave da dimensão de cliente |
| product_id | Chave da dimensão de produto |
| seller_id | Chave da dimensão de vendedor |
| region_id | Chave da dimensão de região |
| channel | Canal de venda |
| order_status | Status da transação: Concluído ou Devolvido |
| unit_price | Preço de venda por unidade |
| quantity | Quantidade original da transação |
| net_quantity | Quantidade líquida considerando devoluções |
| discount_pct | Percentual de desconto |
| gross_revenue | Receita antes dos descontos |
| discount_amount | Valor do desconto |
| net_revenue | Receita após os descontos |
| unit_cost | Custo por unidade |
| total_cost | Custo total da transação considerando devoluções |
| gross_profit | Receita líquida menos o custo total |
| margin_pct | Percentual de margem bruta da transação |

## Dimensões geradas

### dim_cliente

`customer_id`, `customer_name`, `segment`, `city`, `state`

### dim_produto

`product_id`, `product_name`, `category`, `subcategory`

### dim_vendedor

`seller_id`, `seller_name`, `seller_team`

### dim_regiao

`region_id`, `region`, `state`

### dim_data

`date_id`, `date`, `year`, `quarter`, `month_number`, `month_name`,
`year_month`, `day`, `weekday_number`, `weekday_name`, `is_weekend`