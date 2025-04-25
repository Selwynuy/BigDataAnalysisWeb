import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO


def analyze_dataset(file_path):
    try:
        df = pd.read_csv(file_path) if file_path.endswith(
            '.csv') else pd.read_excel(file_path)

        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric': {},
            'categorical': {}
        }

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                analysis['numeric'][col] = {
                    'mean': round(df[col].mean(), 2),
                    'median': round(df[col].median(), 2),
                    'mode': df[col].mode().tolist(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'std': round(df[col].std(), 2),
                    'histogram': df[col].value_counts().to_dict()
                }
            else:
                analysis['categorical'][col] = {
                    'unique_values': df[col].nunique(),
                    'top_values': df[col].value_counts().head(5).to_dict()
                }

        return analysis
    except Exception as e:
        raise ValueError(f"Analysis failed: {str(e)}")


def generate_plot(series):
    plt.figure(figsize=(10, 5))
    series.hist()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')