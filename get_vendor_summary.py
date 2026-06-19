import sqlite3
import pandas as pd
import numpy as np
import logging
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

def ingest_db(df, table_name, engine):
    '''this function will ingest the dataframe into database table'''
    df.to_sql(table_name, con = engine, if_exists = 'replace', index = False)
    
def create_vendor_summary(conn):
    '''this function will merge the different tables to get the overall vendor summary and adding new columns in the resultant data'''
    vendor_sales_summary = pd.read_sql_query("""WITH FreightSummary AS (
        SELECT 
            VendorNumber, 
            SUM(Freight) AS FreightCost 
        FROM vendor_invoice 
        GROUP BY VendorNumber
    ), 
    PurchaseSummary AS (
        SELECT 
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            p.PurchasePrice,
            pp.Price AS ActualPrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
        WHERE p.PurchasePrice > 0
        GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
    ), 
    SalesSummary AS (
        SELECT 
            VendorNo,
            Brand,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(ExciseTax) AS TotalExciseTax
        FROM sales
        GROUP BY VendorNo, Brand
    ) 
    SELECT 
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss 
        ON ps.VendorNumber = ss.VendorNo 
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs 
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""",conn)
    return vendor_sales_summary

# Data cleaning .
def clean_data(df):
    '''this function will clean the data'''
    if 'Volume' in df.columns:
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0.0)

    # make sure numeric columns exist before arithmetic operations
    for col in ['TotalSalesDollars', 'TotalPurchaseDollars', 'TotalSalesQuantity', 'TotalPurchaseQuantity']:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # filling missing value with 0
    df.fillna(0, inplace=True)
    
    # removing spaces from categorical columns
    for col in ['VendorName', 'Description']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # creating new columns for better analysis
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = np.where(
        df['TotalSalesDollars'] != 0,
        (df['GrossProfit'] / df['TotalSalesDollars']) * 100,
        0.0
    )
    df['StockTurnover'] = np.where(
        df['TotalPurchaseQuantity'] != 0,
        df['TotalSalesQuantity'] / df['TotalPurchaseQuantity'],
        0.0
    )
    df['SalesToPurchaseRatio'] = np.where(
        df['TotalPurchaseDollars'] != 0,
        df['TotalSalesDollars'] / df['TotalPurchaseDollars'],
        0.0
    )

    return df

if __name__ == '__main__':
    # creating database connection
    conn = sqlite3.connect('inventory.db')
    
    logging.info('Creating Vendor Summary Table.....')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())
    
    logging.info('Cleaning Data.....')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())
    
    logging.info('Ingesting data.....')
    ingest_db(clean_df,'vendor_sales_summary',conn)
    logging.info('Completed')