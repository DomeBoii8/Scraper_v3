# Format of payload to be received by combining output of backend and LLM
"""
{
    product: "<Product Name>"
    columns: [<List of Columns>],
    records: [<Records as tuples/lists>],
    outputFormat: "<Output format>",
}
"""

import os
import pandas as pd

base_dir = './exports'

if not os.path.exists(base_dir):
    os.mkdir(base_dir)

def validatePayload(payload):
    reqCols = ['product', 'columns', 'records', 'outputFormat']

    for col in reqCols:
        if col not in payload:
            return False

    for rec in payload['records']:
        col_length = len(payload['columns'])
        if len(rec) != col_length:
            return False

    if payload['outputFormat'] not in ['csv', 'json', 'xlsx']:
        return False

    if payload['product'] is None:
        return False

    return True

def conversionToDataFrame(payload):
    columns = payload['columns']
    records = payload['records']
    df = pd.DataFrame(records, columns=columns)
    return df

def outputFile(outputFormat, product, df):
    opFormat = outputFormat.lower()

    if opFormat == "csv":
        file_path = f"{base_dir}/{product}.csv"
        df.to_csv(file_path, index=False)

    elif opFormat == "xlsx":
        file_path = f"{base_dir}/{product}.xlsx"
        df.to_excel(file_path, index=False)

    elif opFormat == "json":
        file_path = f"{base_dir}/{product}.json"
        df.to_json(file_path, orient="records", indent=2)

def dataFormatter(payload):
    if validatePayload(payload):
        outputFile(payload['outputFormat'], payload['product'], conversionToDataFrame(payload))

# Testing with example payload
"""
if __name__ == '__main__':
    payload = {
        'product': 'BTC',
        'columns': ['Value', 'Time'],
        'records': [[180, 2147], [190, 2247]],
        'outputFormat': 'json',
    }
    dataFormatter(payload)
"""