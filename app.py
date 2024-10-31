import os
from flask import Flask, request, jsonify, make_response
import easyocr
import json
from label_resume import label_resume_data
from label_work_experience import label_work_experience_data
from label_certification import label_certification_data
from label_training import label_training_data
from label_education import label_education_data

# Flask 앱 초기화
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

# 업로드된 파일을 저장할 폴더 설정
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# EasyOCR 모델 로드
reader = easyocr.Reader(['ko', 'en'], gpu=False)

# 이력서 이미지 처리 함수
def process_resume_image(image_path):
    # 이미지에서 텍스트 추출
    result = reader.readtext(image_path)

    # 추출된 텍스트 라벨링
    resume_data = label_resume_data([detection[1] for detection in result])
    work_experience_data = label_work_experience_data([detection[1] for detection in result])
    certification_data = label_certification_data([detection[1] for detection in result])
    training_data = label_training_data([detection[1] for detection in result])
    education_data = label_education_data([detection[1] for detection in result])

    # 모든 데이터를 통합
    full_data = {
        "resume": resume_data['resume'],
        "workExperience": work_experience_data['workExperience'],
        "certification": certification_data['certification'],
        "training": training_data['training'],
        "education": education_data['education']
    }

    # 라벨링된 데이터를 JSON 파일로 저장
    json_filename = os.path.splitext(os.path.basename(image_path))[0] + "Labeled.json"
    json_filepath = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)

    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(full_data, json_file, ensure_ascii=False, indent=4)

    print(f"라벨링된 데이터가 {json_filepath}에 저장되었습니다.")

    return full_data, json_filepath  # 라벨링된 데이터와 저장 경로 반환

# 한글 인코딩 문제 해결을 위한 JSON 응답 생성 함수
def create_json_response(labeled_data, json_filepath):
    response_data = {
        "message": "File processed successfully.",
        "data": labeled_data,  # 라벨링 데이터를 직접 반환
        "jsonFilepath": json_filepath  # 저장된 JSON 파일 경로도 반환
    }

    # 한글이 포함된 데이터를 ensure_ascii=False로 처리
    json_response = json.dumps(response_data, ensure_ascii=False, indent=4)

    # make_response로 Flask 응답 생성
    response = make_response(json_response)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# 파일 업로드 엔드포인트
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 파일 저장
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # 이력서 이미지 처리 및 라벨링
        labeled_data, json_filepath = process_resume_image(file_path)

        # 한글 인코딩을 처리한 JSON 응답 생성
        return create_json_response(labeled_data, json_filepath)
    
# Flask 앱 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
