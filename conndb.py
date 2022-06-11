from ast import And
import json
import os
from unicodedata import name
from flask import Flask, flash, redirect,render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, table
import sqlalchemy
from werkzeug.utils import secure_filename
import face_recognition
import cv2

app = Flask(__name__, template_folder='templates')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
 
DB_FOLDER = os.getenv('DB_FOLDER')
app.config['DB_FOLDER'] = DB_FOLDER

app.secret_key ='SECRET_KEY'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/criminal_record'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = create_engine("mysql://root:@localhost/criminal_record")
meta = MetaData(bind=engine)
MetaData.reflect(meta)

db = SQLAlchemy(app)
 
class Record_table(db.Model):
    Serial_ID = db.Column(db.Integer,primary_key=True)
    Name = db.Column(db.String(80),nullable=False)
    Description = db.Column(db.String(300),nullable=False)
    DOB = db.Column(db.String(8),nullable=False)
    gender = db.Column(db.String(6),nullable=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def index():
    for file_name in os.listdir(UPLOAD_FOLDER):
        if allowed_file(file_name):
            file = UPLOAD_FOLDER + file_name
            os.remove(file)
    return render_template('main.html')

@app.route('/', methods = ['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return render_template(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No Image selected')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER,filename))
        flash('Image Successfully Uploaded')
        return render_template('main.html',filename= filename)
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)    

@app.route('/display/<filename>')
def image_displayer(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/match_image/<filename>')
def match_image(filename):
    k = 0
    msg = ""
    name = ""
    dob = ""
    file = ""

    imgDiv = face_recognition.load_image_file(UPLOAD_FOLDER + filename)
    imgDiv = cv2.cvtColor(imgDiv, cv2.COLOR_BGR2RGB)

    try:
        encodeDiv = face_recognition.face_encodings(imgDiv)[0]
    except IndexError as e:
        k = 2
        pass

    path = DB_FOLDER
    myList = os.listdir(path)

    if k!=2:
        for cu_img in myList:
            imgTest = face_recognition.load_image_file(f'{path}/{cu_img}')
            imgTest = cv2.cvtColor(imgTest, cv2.COLOR_BGR2RGB)
            encodeTest = face_recognition.face_encodings(imgDiv)[0]
            result = face_recognition.compare_faces([encodeDiv],encodeTest)
            if result[0]:
                file = cu_img
                fullname = os.path.splitext(file)[0]
                name = fullname.split('_')[0]
                dob = fullname.split('_')[1]
                msg = "MATCH FOUND!"
                k=1
                break
            
    if k==0:
        msg ="NO MATCH FOUND!"
    if k==2:
        msg = "Couldn't recognise any face!"
    value = {"msg":msg,"name": name,"dob":dob,"file":file,"k": k}
    return json.dumps(value)    

@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/form',methods = ['POST'])
def upinfo():
    name = request.form.get('name')
    description = request.form.get('description')
    dob = request.form.get('dob')
    gen = request.form.get('gender')
    file = request.files['file']
    # image_path = "./imagedb/" + file.filename
    # file.save(image_path)
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    renamefilename = f"{name}_{dob}.{ext}"
    file.save(os.path.join(DB_FOLDER, filename))
    os.rename(f"{DB_FOLDER}{filename}",f"{DB_FOLDER}{renamefilename}")
        
    entry = Record_table(Name = name,Description = description,DOB = dob,gender = gen)
    
    db.session.add(entry)
    db.session.commit()
    return redirect('/')
@app.route('/face_rec',methods = ['GET'])
def details():
    file = request.args.get('file')
    fullname = file.split('.')[0]
    name = fullname.split('_')[0]
    dob = fullname.split('_')[1]
    
    CRIMINALS = meta.tables['record_table']
    query = sqlalchemy.select(CRIMINALS).where( CRIMINALS.c.Name == name ,CRIMINALS.c.DOB == dob)

    details = engine.execute(query).fetchone()
    return render_template('face_rec.html',details = details, file = file)


if __name__ == '__main__':
    app.debug = True
    app.run()

 