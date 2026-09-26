from pathlib import Path

import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_BRUTO = RAIZ / "data" / "raw" / "vendas.csv"
DIRETORIO_SAIDA = RAIZ / "data" / "processed"


COLUNAS_ESPERADAS = [
    "sale_id",
    "sale_date",
    "customer_id",
    "customer_name",
    "customer_segment",
    "city",
    "state",
    "region",
    "region_id",
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "unit_price",
    "quantity",
    "discount_pct",
    "unit_cost",
    "seller_id",
    "seller_name",
    "seller_team",
    "channel",
    "order_status",
]


def _moda(series: pd.Series, valor_padrao="Unknown"):
    """
    Retorna o valor não nulo/não vazio mais frequente.
    """
    valores = series.dropna().astype(str).str.strip()
    valores = valores[valores != ""]

    if valores.empty:
        return valor_padrao

    return valores.mode().iloc[0]


def validar_dados_brutos(df: pd.DataFrame):
    """
    Valida a estrutura do conjunto de dados bruto e as chaves obrigatórias.
    """
    colunas_ausentes = [
        column for column in COLUNAS_ESPERADAS
        if column not in df.columns
    ]

    if colunas_ausentes:
        raise ValueError(
            f"Missing required colunas: {colunas_ausentes}"
        )

    chaves_obrigatorias = [
        "sale_id",
        "customer_id",
        "product_id",
        "seller_id",
    ]

    for column in chaves_obrigatorias:
        if df[column].isna().any():
            raise ValueError(
                f"Column '{column}' contains null valores."
            )


def limpar_dados_brutos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e enriquece o conjunto de dados transacional bruto.
    """

    df = df.copy()

    # ---------------------------------------------------------
    # Remover transações duplicadas
    # ---------------------------------------------------------

    df = df.drop_duplicates(
        subset=["sale_id"],
        keep="first"
    ).copy()

    # ---------------------------------------------------------
    # Datas
    # ---------------------------------------------------------

    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce"
    )

    if df["sale_date"].isna().any():
        raise ValueError(
            "Some sale_date valores could not be converted to datas."
        )

    # ---------------------------------------------------------
    # Integer colunas
    # ---------------------------------------------------------

    colunas_inteiras = [
        "customer_id",
        "region_id",
        "product_id",
        "quantity",
        "seller_id",
    ]

    for column in colunas_inteiras:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        ).astype("int64")

    # ---------------------------------------------------------
    # Numeric colunas
    # ---------------------------------------------------------

    colunas_numericas = [
        "unit_price",
        "discount_pct",
        "unit_cost",
    ]

    for column in colunas_numericas:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    # ---------------------------------------------------------
    # Normalização de texto
    # ---------------------------------------------------------

    colunas_texto = [
        "customer_name",
        "customer_segment",
        "city",
        "state",
        "region",
        "product_name",
        "category",
        "subcategory",
        "seller_name",
        "seller_team",
        "channel",
        "order_status",
    ]

    for column in colunas_texto:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # Normalização de estado
    df["state"] = df["state"].str.upper()

    # Normalização de região
    df["region"] = df["region"].str.title()

    # ---------------------------------------------------------
    # Segmento de cliente
    # ---------------------------------------------------------

    df["customer_segment"] = (
        df["customer_segment"]
        .replace("", pd.NA)
    )

    # Segmentos ausentes recebem o valor Unknown
    df["customer_segment"] = (
        df["customer_segment"]
        .fillna("Unknown")
    )

    # ---------------------------------------------------------
    # Remover transações canceladas
    # ---------------------------------------------------------

    df = df[
        df["order_status"].str.lower() != "cancelado"
    ].copy()

    # ---------------------------------------------------------
    # Devoluções
    # ---------------------------------------------------------
    # Venda normal = +1
    # Devolução    = -1
    # ---------------------------------------------------------

    df["movement_sign"] = np.where(
        df["order_status"].str.lower() == "devolvido",
        -1,
        1,
    )

    # ---------------------------------------------------------
    # Quantidades
    # ---------------------------------------------------------

    df["net_quantity"] = (
        df["quantity"] * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Receita
    # ---------------------------------------------------------

    df["gross_revenue"] = (
        df["unit_price"]
        * df["quantity"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Desconto
    # ---------------------------------------------------------

    df["discount_amount"] = (
        df["unit_price"]
        * df["quantity"]
        * df["discount_pct"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Receita líquida
    # ---------------------------------------------------------

    df["net_revenue"] = (
        df["gross_revenue"]
        - df["discount_amount"]
    )

    # ---------------------------------------------------------
    # Custo
    # ---------------------------------------------------------

    df["total_cost"] = (
        df["unit_cost"]
        * df["quantity"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Lucro bruto
    # ---------------------------------------------------------

    df["gross_profit"] = (
        df["net_revenue"]
        - df["total_cost"]
    )

    # ---------------------------------------------------------
    # Margem
    # ---------------------------------------------------------

    df["margin_pct"] = np.where(
        df["net_revenue"] != 0,
        df["gross_profit"] / df["net_revenue"],
        0,
    )

    # ---------------------------------------------------------
    # ID da data
    # ---------------------------------------------------------

    df["date_id"] = (
        df["sale_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    return df


def construir_dim_cliente(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the customer dimensao.

    A região intencionalmente NÃO é incluída aqui.
    Os atributos do cliente permanecem independentes da
    transactional region used by FactSales.
    """

    dim_cliente = (
        df.groupby("customer_id", as_index=False)
        .agg(
            customer_name=("customer_name", _moda),
            segment=("customer_segment", _moda),
            city=("city", _moda),
            state=("state", _moda),
        )
    )

    return dim_cliente


def construir_dim_produto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the product dimensao.
    """

    dim_produto = (
        df.groupby("product_id", as_index=False)
        .agg(
            product_name=("product_name", _moda),
            category=("category", _moda),
            subcategory=("subcategory", _moda),
        )
    )

    return dim_produto


def construir_dim_vendedor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the seller dimensao.
    """

    dim_vendedor = (
        df.groupby("seller_id", as_index=False)
        .agg(
            seller_name=("seller_name", _moda),
            seller_team=("seller_team", _moda),
        )
    )

    return dim_vendedor


def construir_dim_regiao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the region dimensao.
    """

    dim_regiao = (
        df.groupby("region_id", as_index=False)
        .agg(
            region=("region", _moda),
            state=("state", _moda),
        )
    )

    return dim_regiao


def construir_dim_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds a continuous date dimensao covering the
    todo o período das transações.
    """

    data_inicial = df["sale_date"].min().normalize()
    data_final = df["sale_date"].max().normalize()

    datas = pd.date_range(
        start=data_inicial,
        end=data_final,
        freq="D",
    )

    dim_data = pd.DataFrame({
        "date": datas
    })

    dim_data["date_id"] = (
        dim_data["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    dim_data["year"] = dim_data["date"].dt.year

    dim_data["quarter"] = (
        "Q"
        + dim_data["date"].dt.quarter.astype(str)
    )

    dim_data["month_number"] = (
        dim_data["date"].dt.month
    )

    dim_data["month_name"] = (
        dim_data["date"]
        .dt.month_name()
    )

    dim_data["year_month"] = (
        dim_data["date"]
        .dt.strftime("%Y-%m")
    )

    dim_data["day"] = (
        dim_data["date"].dt.day
    )

    dim_data["weekday_number"] = (
        dim_data["date"].dt.weekday + 1
    )

    dim_data["weekday_name"] = (
        dim_data["date"]
        .dt.day_name()
    )

    dim_data["is_weekend"] = (
        dim_data["date"]
        .dt.weekday >= 5
    )

    return dim_data[
        [
            "date_id",
            "date",
            "year",
            "quarter",
            "month_number",
            "month_name",
            "year_month",
            "day",
            "weekday_number",
            "weekday_name",
            "is_weekend",
        ]
    ]


def construir_fato_vendas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói a tabela fato de vendas.

    A região permanece na tabela fato porque representa
    a região associada à transação.
    """

    colunas = [
        "sale_id",
        "date_id",
        "customer_id",
        "product_id",
        "seller_id",
        "region_id",
        "channel",
        "order_status",
        "unit_price",
        "quantity",
        "net_quantity",
        "discount_pct",
        "gross_revenue",
        "discount_amount",
        "net_revenue",
        "unit_cost",
        "total_cost",
        "gross_profit",
        "margin_pct",
    ]

    return df[colunas].copy()


def validar_modelo(
    fato_vendas: pd.DataFrame,
    dim_cliente: pd.DataFrame,
    dim_produto: pd.DataFrame,
    dim_vendedor: pd.DataFrame,
    dim_regiao: pd.DataFrame,
    dim_data: pd.DataFrame,
):
    """
    Valida a integridade referencial entre a tabela fato
    table and dimensoes.
    """

    # ---------------------------------------------------------
    # Validate dimensao key uniqueness
    # ---------------------------------------------------------

    dimensoes = {
        "customer_id": dim_cliente,
        "product_id": dim_produto,
        "seller_id": dim_vendedor,
        "region_id": dim_regiao,
        "date_id": dim_data,
    }

    for key, dimensao in dimensoes.items():
        if dimensao[key].duplicated().any():
            raise ValueError(
                f"Duplicate keys found in dimensao '{key}'."
            )

    # ---------------------------------------------------------
    # Validar fato -> cliente
    # ---------------------------------------------------------

    clientes_invalidos = (
        ~fato_vendas["customer_id"]
        .isin(dim_cliente["customer_id"])
    )

    if clientes_invalidos.any():
        raise ValueError(
            "FactSales contains customer_id valores "
            "not present in DimCustomer."
        )

    # ---------------------------------------------------------
    # Validar fato -> produto
    # ---------------------------------------------------------

    produtos_invalidos = (
        ~fato_vendas["product_id"]
        .isin(dim_produto["product_id"])
    )

    if produtos_invalidos.any():
        raise ValueError(
            "FactSales contains product_id valores "
            "not present in DimProduct."
        )

    # ---------------------------------------------------------
    # Validar fato -> vendedor
    # ---------------------------------------------------------

    vendedores_invalidos = (
        ~fato_vendas["seller_id"]
        .isin(dim_vendedor["seller_id"])
    )

    if vendedores_invalidos.any():
        raise ValueError(
            "FactSales contains seller_id valores "
            "not present in DimSeller."
        )

    # ---------------------------------------------------------
    # Validar fato -> região
    # ---------------------------------------------------------

    regioes_invalidas = (
        ~fato_vendas["region_id"]
        .isin(dim_regiao["region_id"])
    )

    if regioes_invalidas.any():
        raise ValueError(
            "FactSales contains region_id valores "
            "not present in DimRegion."
        )

    # ---------------------------------------------------------
    # Validar fato -> data
    # ---------------------------------------------------------

    datas_invalidas = (
        ~fato_vendas["date_id"]
        .isin(dim_data["date_id"])
    )

    if datas_invalidas.any():
        raise ValueError(
            "FactSales contains date_id valores "
            "not present in DimDate."
        )


def exportar_modelo(
    fato_vendas: pd.DataFrame,
    dim_cliente: pd.DataFrame,
    dim_produto: pd.DataFrame,
    dim_vendedor: pd.DataFrame,
    dim_regiao: pd.DataFrame,
    dim_data: pd.DataFrame,
):
    """
    Limpa o diretório de dados processados e exporta
    o modelo dimensional como arquivos CSV.
    """

    DIRETORIO_SAIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    # Remover arquivos CSV gerados anteriormente
    for file in DIRETORIO_SAIDA.glob("*.csv"):
        file.unlink()

    # Exportar dimensoes
    dim_cliente.to_csv(
        DIRETORIO_SAIDA / "dim_cliente.csv",
        index=False
    )

    dim_produto.to_csv(
        DIRETORIO_SAIDA / "dim_produto.csv",
        index=False
    )

    dim_vendedor.to_csv(
        DIRETORIO_SAIDA / "dim_vendedor.csv",
        index=False
    )

    dim_regiao.to_csv(
        DIRETORIO_SAIDA / "dim_regiao.csv",
        index=False
    )

    dim_data.to_csv(
        DIRETORIO_SAIDA / "dim_data.csv",
        index=False
    )

    # Exportarar tabela fato
    fato_vendas.to_csv(
        DIRETORIO_SAIDA / "fato_vendas.csv",
        index=False
    )


def main():
    print("Iniciando ETL...")

    # ---------------------------------------------------------
    # Ler dados brutos
    # ---------------------------------------------------------

    if not ARQUIVO_BRUTO.exists():
        raise FileNotFoundError(
            f"Arquivo bruto não encontrado: {ARQUIVO_BRUTO}"
        )

    df_bruto = pd.read_csv(ARQUIVO_BRUTO)

    print(f"Linhas brutas: {len(df_bruto):,}")

    # ---------------------------------------------------------
    # Validar dados brutos
    # ---------------------------------------------------------

    validar_dados_brutos(df_bruto)

    # ---------------------------------------------------------
    # Limpar e transformar
    # ---------------------------------------------------------

    df_limpo = limpar_dados_brutos(df_bruto)

    print(
        f"Linhas após limpeza: {len(df_limpo):,}"
    )

    # ---------------------------------------------------------
    # Build dimensoes
    # ---------------------------------------------------------

    dim_cliente = construir_dim_cliente(df_limpo)
    dim_produto = construir_dim_produto(df_limpo)
    dim_vendedor = construir_dim_vendedor(df_limpo)
    dim_regiao = construir_dim_regiao(df_limpo)
    dim_data = construir_dim_data(df_limpo)

    # ---------------------------------------------------------
    # Construir tabela fato
    # ---------------------------------------------------------

    fato_vendas = construir_fato_vendas(df_limpo)

    # ---------------------------------------------------------
    # Validar modelo dimensional
    # ---------------------------------------------------------

    validar_modelo(
        fato_vendas=fato_vendas,
        dim_cliente=dim_cliente,
        dim_produto=dim_produto,
        dim_vendedor=dim_vendedor,
        dim_regiao=dim_regiao,
        dim_data=dim_data,
    )

    # ---------------------------------------------------------
    # Exportar
    # ---------------------------------------------------------

    exportar_modelo(
        fato_vendas=fato_vendas,
        dim_cliente=dim_cliente,
        dim_produto=dim_produto,
        dim_vendedor=dim_vendedor,
        dim_regiao=dim_regiao,
        dim_data=dim_data,
    )

    # ---------------------------------------------------------
    # Resumo
    # ---------------------------------------------------------

    print("\nETL concluído com sucesso.")
    print("\nTabelas geradas:")

    print(
        f"  dim_cliente: {len(dim_cliente):,} rows"
    )

    print(
        f"  dim_produto:  {len(dim_produto):,} rows"
    )

    print(
        f"  dim_vendedor:   {len(dim_vendedor):,} rows"
    )

    print(
        f"  dim_regiao:   {len(dim_regiao):,} rows"
    )

    print(
        f"  dim_data:     {len(dim_data):,} rows"
    )

    print(
        f"  fato_vendas:   {len(fato_vendas):,} rows"
    )

    print(
        f"\nDiretório de saída: {DIRETORIO_SAIDA}"
    )


if __name__ == "__main__":
    main()