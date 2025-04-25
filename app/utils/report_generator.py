import pandas as pd
from flask import current_app
import os

def generate_full_report(file_path):
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    
    # Generate comprehensive report
    report = df.describe(include='all').T
    report['mode'] = df.mode().iloc[0]
    
    # Save to reports directory
    report_path = os.path.join(current_app.config['REPORT_FOLDER'], 'full_report.csv')
    report.to_csv(report_path)
    
    return report_path