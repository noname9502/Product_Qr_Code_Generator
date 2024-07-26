from flask import Flask, render_template_string, request, redirect, url_for, send_file
import qrcode
import io
import os

app = Flask(__name__)

# Mahsulot ma'lumotlari uchun xotirada saqlash
product_data = []

# Mahsulot ma'lumotlarini saqlash/yuklash yo'li
DATA_FILE = 'products.txt'

#O'rnatilgan CSS bilan # HTML shabloni
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mahsulot QR kodi generatori</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 80%;
            margin: auto;
            overflow: hidden;
        }
        form {
            background: #fff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }
        label {
            display: block;
            margin: 10px 0 5px;
        }
        input {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
        }
        button {
            background: #5cb85c;
            border: none;
            color: #fff;
            padding: 10px 20px;
            cursor: pointer;
        }
        button:hover {
            background: #4cae4c;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            background: #fff;
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
        }
        #editProduct {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mahsulot QR kodi generatori</h1>
        <form action="{{ url_for('add_product') }}" method="post">
            <label for="name">Mahsulot nomi:</label>
            <input type="text" id="name" name="name" required>
            <label for="price">Narxi:</label>
            <input type="text" id="price" name="price" required>
            <label for="size">Hajmi:</label>
            <input type="text" id="size" name="size" required>
            <label for="total">Jami:</label>
            <input type="text" id="total" name="total" required>
            <label for="produced_country">Ishlab chiqarilgan mamlakat:</label>
            <input type="text" id="produced_country" name="produced_country" required>
            <label for="prod_date">Ishlab chiqarish sanasi (MM/DD/YYYY):</label>
            <input type="text" id="prod_date" name="prod_date" required>
            <label for="materials">Materiallar:</label>
            <input type="text" id="materials" name="materials" required>
            <button type="submit">Mahsulot qo'shish</button>
        </form>
        <form action="{{ url_for('load_product_data') }}" method="post" enctype="multipart/form-data">
            <label for="file">Mahsulot ma'lumotlarini yuklash</label>
            <input type="file" id="file" name="file" required>
            <button type="submit">Mahsulot ma'lumotlarini yuklash</button>
        </form>
        <button onclick="window.location.href='{{ url_for('save_product_data') }}'">Mahsulot ma'lumotlarini saqlang</button>
        <button onclick="window.location.href='{{ url_for('view_products') }}'">Mahsulotlarni ko'rish</button>
        <h2>Mahsulotlar roʻyxati</h2>
        <ul>
            {% for product in products %}
                <li>
                    {{ product[0] }} - 
                    <a href="{{ url_for('generate_qr_code', index=loop.index0) }}">QR Code yarating </a> - 
                    <a href="#" onclick="showEditForm({{ loop.index0 }}); return false;">Tahrirlash</a> - 
                    <a href="{{ url_for('delete_product', index=loop.index0) }}">Oʻchirish</a>
                </li>
            {% endfor %}
        </ul>
        <div id="editProduct">
            <h2>Edit Product</h2>
            <form id="editForm" action="" method="post">
                <input type="hidden" id="editIndex" name="index">
                <label for="edit_name">Mahsulot nomi:</label>
                <input type="text" id="edit_name" name="name" required>
                <label for="edit_price">Narxi:</label>
                <input type="text" id="edit_price" name="price" required>
                <label for="edit_size">Hajmi:</label>
                <input type="text" id="edit_size" name="size" required>
                <label for="edit_total">Jami:</label>
                <input type="text" id="edit_total" name="total" required>
                <label for="edit_produced_country">Ishlab chiqarilgan mamlakat:</label>
                <input type="text" id="edit_produced_country" name="produced_country" required>
                <label for="edit_prod_date">Ishlab chiqarish sanasi (MM/DD/YYYY):</label>
                <input type="text" id="edit_prod_date" name="prod_date" required>
                <label for="edit_materials">Materiallar:</label>
                <input type="text" id="edit_materials" name="materials" required>
                <button type="submit">Mahsulotni yangilash</button>
            </form>
        </div>
    </div>
    <script>
        function showEditForm(index) {
            var product = {{ products | tojson }};
            var selectedProduct = product[index];
            document.getElementById('editProduct').style.display = 'block';
            document.getElementById('editForm').action = '/update/' + index;
            document.getElementById('editIndex').value = index;
            document.getElementById('edit_name').value = selectedProduct[0];
            document.getElementById('edit_price').value = selectedProduct[1];
            document.getElementById('edit_size').value = selectedProduct[2];
            document.getElementById('edit_total').value = selectedProduct[3];
            document.getElementById('edit_produced_country').value = selectedProduct[4];
            document.getElementById('edit_prod_date').value = selectedProduct[5];
            document.getElementById('edit_materials').value = selectedProduct[6];
        }
    </script>
</body>
</html>
'''

# Jadvaldagi barcha mahsulotlarni ko'rish uchun marshrut
@app.route('/view')
def view_products():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mahsulotlarni ko'rish</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 80%;
            margin: auto;
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f4f4f4;
        }
        a {
            color: #5cb85c;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .back-button {
            background: #5cb85c;
            border: none;
            color: #fff;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .back-button:hover {
            background: #4cae4c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Mahsulotlarni ko'rish</h1>
        <table>
            <thead>
                <tr>
                    <th>Ism</th>
                    <th>Narxi</th>
                    <th>Hajmi</th>
                    <th>Jami</th>
                    <th>Ishlab chiqarilgan mamlakat</th>
                    <th>Ishlab chiqarish sanasi</th>
                    <th>Materiallar</th>
                </tr>
            </thead>
            <tbody>
                {% for product in products %}
                <tr>
                    <td>{{ product[0] }}</td>
                    <td>{{ product[1] }}</td>
                    <td>{{ product[2] }}</td>
                    <td>{{ product[3] }}</td>
                    <td>{{ product[4] }}</td>
                    <td>{{ product[5] }}</td>
                    <td>{{ product[6] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <a class="back-button" href="{{ url_for('index') }}">Uyga qaytish</a>
    </div>
</body>
</html>
''', products=product_data)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, products=product_data)

@app.route('/add', methods=['POST'])
def add_product():
    product = [
        request.form.get('name'),
        request.form.get('price'),
        request.form.get('size'),
        request.form.get('total'),
        request.form.get('produced_country'),
        request.form.get('prod_date'),
        request.form.get('materials')
    ]
    product_data.append(product)
    return redirect(url_for('index'))

@app.route('/update/<int:index>', methods=['POST'])
def update_product(index):
    if 0 <= index < len(product_data):
        product_data[index] = [
            request.form.get('name'),
            request.form.get('price'),
            request.form.get('size'),
            request.form.get('total'),
            request.form.get('produced_country'),
            request.form.get('prod_date'),
            request.form.get('materials')
        ]
    return redirect(url_for('index'))

@app.route('/generate_qr_code/<int:index>')
def generate_qr_code(index):
    if 0 <= index < len(product_data):
        product = product_data[index]
        qr_data = f"Name: {product[0]}\nPrice: {product[1]}\nSize: {product[2]}\nTotal: {product[3]}\nProduced Country: {product[4]}\nProduction Date: {product[5]}\nMaterials: {product[6]}"
        qr = qrcode.make(qr_data)
        img = io.BytesIO()
        qr.save(img, 'PNG')
        img.seek(0)
        return send_file(img, mimetype='image/png', as_attachment=True, download_name='qrcode.png')
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete_product(index):
    if 0 <= index < len(product_data):
        product_data.pop(index)
    return redirect(url_for('index'))

@app.route('/load_product_data', methods=['POST'])
def load_product_data():
    file = request.files['file']
    if file:
        file_content = file.stream.read().decode('utf-8')
        global product_data
        product_data = [line.strip().split(',') for line in file_content.splitlines()]
    return redirect(url_for('index'))

@app.route('/save_product_data')
def save_product_data():
    with open(DATA_FILE, 'w') as f:
        for product in product_data:
            f.write(",".join(product) + "\n")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
