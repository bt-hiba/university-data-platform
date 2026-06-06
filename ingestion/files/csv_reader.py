import pandas as pd


def read_csv_file(file_path):

    df = pd.read_csv(file_path)

    return {
        "row_count": len(df),
        "columns": list(df.columns),
        "data": df.to_dict(orient="records")
    }