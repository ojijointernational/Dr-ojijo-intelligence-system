from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_monthly_sales(df, month, year):
    try:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        monthly_data = df[(df['Timestamp'].dt.month == month) & (df['Timestamp'].dt.year == year)]
        total_sales = (monthly_data['Price'] * monthly_data['Quantity']).sum()
        return total_sales
    except Exception as e:
        return f"Error calculating monthly sales: {e}"

def get_top_products(df, n=3):
    try:
        product_sales = df.groupby('Product')['Price', 'Quantity'].sum()
        product_sales['TotalRevenue'] = product_sales['Price'] * product_sales['Quantity']
        top_products = product_sales.sort_values(by='TotalRevenue', ascending=False).head(n).index.tolist()
        return top_products
    except Exception as e:
        return f"Error getting top products: {e}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            # Store the DataFrame temporarily (we'll need a better way to manage state later)
            request.app.sales_data = df
            return jsonify({'message': 'File uploaded successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Error reading file: {e}'}), 500
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analyze/monthly_sales', methods=['POST'])
def get_monthly_sales_route():
    data = request.get_json()
    month = data.get('month')
    year = data.get('year')
    if not hasattr(request.app, 'sales_data'):
        return jsonify({'error': 'No data uploaded yet'}), 400
    if month is None or year is None:
        return jsonify({'error': 'Month and year are required'}), 400
    sales = calculate_monthly_sales(request.app.sales_data.copy(), int(month), int(year))
    return jsonify({'monthly_sales': sales}), 200

@app.route('/analyze/top_products', methods=['GET'])
def get_top_products_route():
    if not hasattr(request.app, 'sales_data'):
        return jsonify({'error': 'No data uploaded yet'}), 400
    top_products = get_top_products(request.app.sales_data.copy())
    return jsonify({'top_products': top_products}), 200

if __name__ == '__main__':
    app.run(debug=True)
