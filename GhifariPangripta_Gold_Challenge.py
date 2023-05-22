import re # Memanggil Regex
import sqlite3 # Memanggil SQLite3 untuk pengolahan database
import pandas as pd # Memanggil Pandas untuk pengolahan dataframe
from flask import Flask, jsonify, request # Memanggil flask
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from ##Memanggil Swagger

# kata Alay
dict_alay = pd.read_csv("new_kamusalay.csv", encoding='latin1',header=None)
dict_alay = dict_alay.rename(columns={0:'Alay', 1:'Benar'})

# Membuat kata Alay menjadi sebuah kamus baru dan menjadi variabel yang berkaitan satu sama lain
dict_alay_map = dict(zip(dict_alay['Alay'], dict_alay['Benar']))

# kata Abusive
dict_abusive = pd.read_csv("abusive.csv",encoding='latin1')

# melakukan filter kata Abusive dengan cara membuat list baru dan menggantinya dengan
# kata Tidak Baik
dict_abusive['Kata_Tidakbaik'] = "Tidak Baik"

# Memetakan kata-kata ABUSIVE menjadi key dan kata "cencored" menjadi value yang berkaitan satu sama lain
dict_abusive_map = dict(zip(dict_abusive['ABUSIVE'], dict_abusive['Kata_Tidakbaik']))

def normal_alay(text):
    return ' '.join([dict_alay_map[word]
    if
        word in dict_alay_map 
    
    else
        word for word in text.split(' ')])

def normal_abusive(text):
    return ' '.join([dict_abusive_map[word]
    if
        word in dict_abusive_map 

    else
        word for word in text.split(' ')])

# merubah karakter dalam sebuah tweet menjadi lowercase (huruf kecil) agar menjadi seragam
def lowercase(text):
    return text.lower()

# Melakukan cleansing dalam sebuah tweet
def cleansed_text(text):    
    text = re.sub(r"[^0-9a-zA-Z]+", "", text) #Menghilangkan non alpha numeric character
    text = re.sub(r"\n", ' ', text) #Menghilangkan new line (enter)
    text = re.sub(r"rt", "", text) #Menghilangkan kata rt (retweet)
    text = re.sub(r"user", "", text) # Menghilangkan kata user
    text = re.sub(r"#\w+", "", text) #Menghilangkan kata dengan hashtag (#)
    text = re.sub(r"http\S+|www\S+|https\S+", "", text) #Menghilangkan URL
    text = re.sub(r"\s+", " ", text) #Menghilangkan spasi berlebih
    return text

# Menjalankan function cleansing
def cleansing_data(text):
    text = lowercase(text)
    text = cleansed_text(text)
    text = normal_alay(text)
    text = normal_abusive(text)
    return text

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder

# Memberikan judul antarmuka dari Swagger yang digunakan
swagger_template = dict(
    info = {
        'title': LazyString(lambda: 'API Cleasning Text Binar Gold Challenge'),
        'version': LazyString(lambda: '1.0.0 // BETA'),
        'description': LazyString(lambda: 'API Documentation for Text Processing'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'docs',
            'route': '/docs.json',
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route':'/'
}

swagger = Swagger(app, template=swagger_template,
                  config=swagger_config)

# Mebuat endpoint
@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/hello-world', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "Menyapa Hello World",
        'data': "Hello World",
    }

    response_data = jsonify(json_response)
    return response_data

    
@swag_from("docs/text_process.yml", methods=['POST'])
@app.route('/text_process', methods=['POST'])
def text_processing():

    #sebelum
    text = request.form.get('text')

    #sesudah
    text_clean = cleansing_data(text)

    # membuat database 
    with sqlite3.connect("Database_Gold_Challenge.db") as DB:
        DB.execute('create table if not exists cleansing (text_ori varchar(255), text_clean varchar(255))')
        query_txt = 'insert into cleansing (text_ori , text_clean) values (?,?)'
        val = (text, text_clean)
        DB.execute(query_txt, val)
        DB.commit()


    response_data = { "input" :text, "output" :text_clean}
    return response_data


@swag_from("docs/text_process_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():

    # Upladed file
    file = request.files.getlist('file')[0]

    # Import file csv ke Pandas
    df = pd.read_csv(file, encoding='latin-1')

    # Ambil teks yang akan diproses dalam format list

    # Sebelum Cleansing
    texts_kotor = df['Tweet']
    texts_kotor = texts_kotor.to_list()

    # Sesudah Cleansing
    df['Tweet'] = df['Tweet'].apply(cleansing_data)
    texts = df.text.to_list()

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'text_before_cleansing': texts_kotor,
        'text_after_cleansing' : texts
    }

    kata_kata = list(zip(texts_kotor,texts))

    conn=sqlite3.connect('Database_Gold_Challange.db')
    cursor=conn.cursor()
    cursor.executemany("INSERT INTO Kata_Kata (id, text_ori, text_clean) VALUES (NULL,?, ?)", kata_kata)
    
    conn.commit()
    conn.close()

    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
	app.run()