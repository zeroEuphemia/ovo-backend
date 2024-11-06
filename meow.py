from flask import Flask, render_template, request, send_file, jsonify, make_response
from flask_cors import CORS
import secrets
import os
from werkzeug.utils import secure_filename
import json
import xlwt

app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['UPLOAD_FOLDER'] = 'upload/'
app.config['DOWNLOAD_FOLDER'] = 'download/'
app.config['OUTPUT_FOLDER'] = 'output/'
app.config['INPUT_FOLDER'] = 'input/'
app.config['EXAMPLE_FOLDER'] = 'Examples/'

@app.route("/api/test", methods = ['GET','POST'])
def test():
    data = request.get_json()
    code = data["code"]
    # print(type(code), code)
    return "Test Meow !"

@app.route("/api/generate", methods = ['GET','POST'])
def generate():
    data = request.get_json()
    random_hex = secrets.token_hex(16)
    random_urlsafe = secrets.token_urlsafe(32)
    input_cnf_path = os.path.join(app.config['INPUT_FOLDER'], secure_filename(random_urlsafe + ".cnf"))
    input_cnf_file = open(input_cnf_path, "w")
    input_cnf_file.write(data["code"])
    input_cnf_file.close()

    # print(data['k'])
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], secure_filename(random_urlsafe + ".out"))
    command = f"nohup ./LS-Sampling-Plus/LS-Sampling-Plus -input_cnf_path {input_cnf_path} -output_testcase_path {output_path} -k {data['k']}"
    # print(command)
    os.system(command)

    ret, columns = [], []
    with open(output_path, "r") as output_file:
        lines = output_file.readlines()
    idx = 0
    for line in lines:
        tc = list(map(int, line.split()))
        # ret.append(tc)
        nvar = len(tc)
        if idx == 0:
            columns.append( { "title" : '编号', "width" : 130, "dataIndex" : 'index', "key" : 'index', "fixed" : 'left' } )
            for i in range(nvar):
                tmp_obj = {"title": f"x{i + 1}", "dataIndex" : f"value{i}", "key" : str(i), "width" : 100}
                columns.append(tmp_obj)
        
        tmp_obj = {"key" : str(idx), "index" : "TestCase " + str(idx + 1)}
        for i in range(nvar):
            tmp_obj[f"value{i}"] = tc[i]
        # print(tmp_obj)
        ret.append(tmp_obj)
        idx += 1
    feedback = {
        "columns": columns,
        "data": ret
    }
    return json.dumps(feedback)

@app.route("/api/loadexample", methods = ['GET','POST'])
def loadexample():
    data = request.get_json()
    example_name = data["example_name"]
    print(data, example_name)
    example_cnf_path = os.path.join(app.config['EXAMPLE_FOLDER'], example_name + ".cnf")
    print(example_cnf_path)
    with open(example_cnf_path, "r") as example_cnf_file:
        ret = example_cnf_file.read()
    return ret

@app.route("/api/uploadcnf", methods = ['GET','POST'])
def uploadcnf():
    if request.method != 'POST':
        return "QAQ"
    f = request.files['file']
    random_hex = secrets.token_hex(16)
    random_urlsafe = secrets.token_urlsafe(32)
    upload_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(random_urlsafe + f.filename))
    f.save(upload_file_path)
    with open(upload_file_path, "r") as file:
        return file.read()
    return "Error"

@app.route("/api/downloadcnf", methods = ['GET','POST'])
def downloadcnf():
    data = request.get_json()
    random_hex = secrets.token_hex(16)
    random_urlsafe = secrets.token_urlsafe(32)
    download_file_name = secure_filename(random_urlsafe + ".txt")
    download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], download_file_name)
    file = open(download_path, "w")
    file.write(data["code"])
    file.close()
    return send_file(download_path, as_attachment=True, download_name = download_file_name)

@app.route("/api/download_tc_csv", methods = ['GET','POST'])
def download_tc_csv():
    data = request.get_json()
    tc_data = data["data"]
    random_hex = secrets.token_hex(16)
    random_urlsafe = secrets.token_urlsafe(32)
    download_file_name = secure_filename(random_urlsafe + ".")
    download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], download_file_name)
    download_file = open(download_path, "w")
    for item in tc_data:
        nvar = len(item) - 2
        # print(item, nvar)
        for i in range(nvar):
            if i > 0:
                download_file.write(",")
            download_file.write(f"{item['value' + str(i)]}")
        download_file.write("\n")
    download_file.close()
    return send_file(download_path, as_attachment=True, download_name = download_file_name)

@app.route("/api/download_tc_xls", methods = ['GET','POST'])
def download_tc_xls():
    data = request.get_json()
    tc_data = data["data"]
    random_hex = secrets.token_hex(16)
    random_urlsafe = secrets.token_urlsafe(32)
    download_file_name = secure_filename(random_urlsafe + ".xls")
    download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], download_file_name)

    workBook = xlwt.Workbook(encoding = 'utf-8')
    sheet = workBook.add_sheet("sheetName")
    head, xls_data = [], []
    for item in tc_data:
        nvar, tc = len(item) - 2, []
        for i in range(nvar):
            tc.append(item['value' + str(i)])
        xls_data.append(tc)
    
    for i in range(nvar):
        head.append(f"x{i + 1}")
    for i in head:
	    sheet.write(0, head.index(i), i)
    length = len(xls_data)
    for i in range(length):
        line_len = len(xls_data[i])
        for j in range(line_len):
            sheet.write(i + 1, j, xls_data[i][j])
    workBook.save(download_path)
    return send_file(download_path, as_attachment = True, download_name = download_file_name, mimetype='application/vnd.ms-excel')
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)