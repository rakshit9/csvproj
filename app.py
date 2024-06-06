from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['IMAGE_FOLDER'] = 'static'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
            file.save(filepath)
            return redirect(url_for('view_data'))
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        name = request.form['name']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Name'].lower() == name.lower():
                    if row['Picture']:
                        image_path = os.path.join(app.config['IMAGE_FOLDER'], row['Picture'])
                        print(f"Checking if {image_path} exists: {os.path.exists(image_path)}")  # Debug
                        if os.path.exists(image_path):
                            image_url = url_for('static', filename=row['Picture'])
                            print(f"Image URL: {image_url}")  # Debug
                            return render_template('display_image.html', image_url=image_url)
                    return render_template('error.html', message="Image file is missing.")
            return render_template('error.html', message="No such name found.")
    return redirect(url_for('index'))

@app.route('/data')
def view_data():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
    data = []
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    print(data)
    return render_template('view_data.html', data=data)


@app.route('/display_low_salary_images')
def display_low_salary_images():
    salary_threshold = 99000
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
    images_info = []
    try:
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    if float(row['Salary']) < salary_threshold:
                        if row['Picture'].strip():
                            image_path = os.path.join(app.config['IMAGE_FOLDER'], row['Picture'])
                            images_info.append({'path': image_path, 'exists': True})
                        else:
                            images_info.append({'path': 'Image does not exist', 'exists': False})
                except ValueError:
                    continue  # Skip rows where salary is not a valid float
    except FileNotFoundError:
        return "The file does not exist", 404

    return render_template('display_images.html', images_info=images_info)



@app.route('/add_picture', methods=['POST'])
def add_picture():
    name = request.form['name']
    file = request.files['picture']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
        
        # Update the CSV file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_people.csv')
        with open(filepath, 'r', newline='') as csvfile, open(temp_file_path, 'w', newline='') as tempfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(tempfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                if row['Name'].lower() == name.lower():
                    row['Picture'] = filename
                writer.writerow(row)
        
        os.replace(temp_file_path, filepath)
        return 'Image uploaded and CSV updated successfully!'
    return 'Invalid file or file not provided'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}




@app.route('/remove_entry', methods=['POST'])
def remove_entry():
    name_to_remove = request.form['name'].strip().lower()  # Get name from form data and prepare it
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_people.csv')
    try:
        with open(filepath, 'r', newline='') as csvfile, open(temp_file_path, 'w', newline='') as tempfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(tempfile, fieldnames=fieldnames)
            writer.writeheader()
            removed = False
            for row in reader:
                if row['Name'].lower() != name_to_remove:
                    writer.writerow(row)
                else:
                    removed = True

        os.replace(temp_file_path, filepath)
        return f'{name_to_remove.title()} removed successfully!' if removed else f'No entry found for {name_to_remove.title()}.'
    except Exception as e:
        return str(e), 500



@app.route('/update_entry', methods=['POST'])
def update_entry():
    name_to_update = request.form['name'].strip().lower()  # Name from the form

    # Collect field updates from the form
    updates = {
        'State': request.form['state'].strip(),
        'Salary': request.form['salary'].strip(),
        'Grade': request.form['grade'].strip(),
        'Room': request.form['room'].strip(),
        'Telnum': request.form['telnum'].strip(),
        'Picture': request.form['picture'].strip(),
        'Keywords': request.form['keywords'].strip()
    }

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'people.csv')
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_people.csv')
    updated = False

    try:
        with open(filepath, 'r', newline='') as csvfile, open(temp_file_path, 'w', newline='') as tempfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(tempfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                if row['Name'].strip().lower() == name_to_update:
                    for field, value in updates.items():
                        if value:  # Only update fields that have a new value provided
                            row[field] = value
                    updated = True
                writer.writerow(row)

        os.replace(temp_file_path, filepath)
        return f'Entry updated successfully for {name_to_update.title()}!' if updated else f'No entry found for {name_to_update.title()}.'
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    app.run(debug=True)
