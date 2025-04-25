from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from io import BytesIO
import tempfile
from datetime import datetime


bp = Blueprint('main', __name__)

# Configuration
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def read_dataframe(file_path):
    """Helper function to read files consistently"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        return pd.read_excel(file_path)
    except Exception as e:
        raise Exception(f"Could not read file: {str(e)}")

def get_file_info(df):
    """Get file information including preview, shape, and column types"""
    preview = df.head(5).to_dict(orient='records')
    shape = f"{df.shape[0]} rows × {df.shape[1]} columns"
    column_types = {col: str(df[col].dtype) for col in df.columns}
    return {
        'preview': preview,
        'shape': shape,
        'column_types': column_types
    }

def ensure_upload_folder():
    """Ensure upload folder exists"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)


@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('error.html', message="No file selected"), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('error.html', message="No file selected"), 400
        
        if not allowed_file(file.filename):
            return render_template('error.html', 
                                message=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"), 400
        
        try:
            # Ensure upload directory exists
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Verify file was saved
            if not os.path.exists(file_path):
                return render_template('error.html', 
                                    message="File failed to save. Please try again."), 500
            
            # Immediately read the file to verify it's valid
            try:
                df = pd.read_csv(file_path) if filename.endswith('.csv') else pd.read_excel(file_path)
                file_info = get_file_info(df)
            except Exception as e:
                os.remove(file_path)  # Clean up invalid file
                return render_template('error.html', 
                                    message=f"Invalid file content: {str(e)}"), 400
            
            # Store file info in session for the results page
            session['file_info'] = {
                'filename': filename,
                'columns': list(df.columns),
                'preview': file_info['preview'],
                'shape': file_info['shape'],
                'column_types': file_info['column_types']
            }
            
            return redirect(url_for('main.results', filename=filename))
            
        except Exception as e:
            return render_template('error.html', 
                                message=f"Error processing file: {str(e)}"), 500
    
    return render_template('index.html')


@bp.route('/results/<filename>')
def results(filename):
    # Get file info from session
    file_info = session.get('file_info')
    
    if not file_info or file_info['filename'] != filename:
        return redirect(url_for('main.index'))
    
    return render_template('results.html',
                         filename=filename,
                         columns=file_info['columns'],
                         preview=file_info['preview'],
                         shape=file_info['shape'],
                         column_types=file_info['column_types'])


@bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        filename = data['filename']
        command = data.get('command', '').strip().lower()
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        df = read_dataframe(file_path)

        result = {}
        if command:
            parts = command.split()
            if len(parts) >= 3 and parts[1] == 'of':
                operation = parts[0]
                column = ' '.join(parts[2:])

                if column not in df.columns:
                    return jsonify({
                        'success': False,
                        'error': f"Column '{column}' not found in the dataset. Available columns: {', '.join(df.columns)}"
                    })

                if operation in ['mean', 'median', 'min', 'max', 'std']:
                    if not pd.api.types.is_numeric_dtype(df[column]):
                        return jsonify({
                            'success': False,
                            'error': f"Cannot calculate {operation} for '{column}' - it's not a numeric column"
                        })
                    try:
                        if operation == 'mean':
                            result[column] = {'mean': float(df[column].mean())}
                        elif operation == 'median':
                            result[column] = {
                                'median': float(df[column].median())}
                        elif operation == 'min':
                            result[column] = {'min': float(df[column].min())}
                        elif operation == 'max':
                            result[column] = {'max': float(df[column].max())}
                        elif operation == 'std':
                            result[column] = {'std': float(df[column].std())}
                    except Exception as e:
                        return jsonify({
                            'success': False,
                            'error': f"Couldn't calculate {operation} for '{column}': {str(e)}"
                        })
                elif operation == 'mode':
                    try:
                        modes = df[column].mode().tolist()
                        # Convert all modes to strings
                        result[column] = {'mode': [str(m) for m in modes]}
                    except Exception as e:
                        return jsonify({
                            'success': False,
                            'error': f"Couldn't calculate mode for '{column}': {str(e)}"
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': f"Unknown operation '{operation}'. Try: mean, median, mode, min, max, or std"
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': "Invalid command format. Try: '[operation] of [column]' like 'mean of age'"
                })
        else:
            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    try:
                        result[column] = {
                            'mean': float(df[column].mean()),
                            'median': float(df[column].median()),
                            'min': float(df[column].min()),
                            'max': float(df[column].max()),
                            'std': float(df[column].std())
                        }
                    except Exception as e:
                        result[column] = {
                            'error': f"Couldn't analyze column '{column}': {str(e)}"
                        }

        return jsonify({
            'success': True,
            'result': result,
            'command': command
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Analysis failed: {str(e)}"
        }), 400


@bp.route('/download/original/<filename>')
def download_original(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return render_template('error.html', message="File not found"), 404
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


@bp.route('/download/analysis/<filename>')
def download_analysis(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return render_template('error.html', message="File not found"), 404

    try:
        df = read_dataframe(file_path)
        analysis_df = df.describe(include='all').T
        analysis_df['mode'] = df.mode().iloc[0]
        analysis_df['missing_values'] = df.isnull().sum()

        output = BytesIO()
        analysis_df.to_csv(output, index=True)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f"analysis_{filename}",
            mimetype='text/csv'
        )
    except Exception as e:
        return render_template('error.html', message=f"Analysis error: {str(e)}"), 500


@bp.route('/download/report/<filename>')
def download_report(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return render_template('error.html', message="File not found"), 404

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        df = read_dataframe(file_path)
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        pdf_path = temp_pdf.name
        temp_pdf.close()

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Data Analysis Report", styles['Title']))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"File: {filename}", styles['Normal']))

        stats_df = df.describe(include='all').T
        stats_data = [stats_df.columns.tolist()] + stats_df.values.tolist()
        t = Table(stats_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)

        missing_df = pd.DataFrame(
            df.isnull().sum(), columns=['Missing Values'])
        missing_data = [missing_df.columns.tolist()] + \
            missing_df.values.tolist()
        t = Table(missing_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)

        doc.build(elements)

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"report_{filename.replace('.csv', '.pdf').replace('.xlsx', '.pdf')}",
            mimetype='application/pdf'
        )
    except ImportError:
        return render_template('error.html', message="Please install reportlab: pip install reportlab"), 400
    except Exception as e:
        return render_template('error.html', message=f"Report error: {str(e)}"), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}
