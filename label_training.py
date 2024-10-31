import easyocr
import re
import json
import os

def label_training_data(extracted_text):
    # 결과를 저장할 딕셔너리
    result_dict = {
        'training': []
    }

    # 변수 설정: 현재 처리 중인 training 데이터
    training_data = {
        'trainingStart': '',
        'trainingEnd': '',
        'trainingName': '',
        'trainingInstitution': ''
    }

    # 정규식 패턴: 날짜, 기관 탐지용
    date_pattern = re.compile(r'(\d{4})[\.\,\-](\d{2})')  # 날짜 패턴 예: '1995.06' 또는 '2018,.12'
    institution_keywords = ['협회', '기관', '공단', '센터', '지원', '교육']  # 기관 관련 키워드

    # 플래그: 훈련 섹션인지 확인하는 플래그
    in_training_section = False
    expect_name = False  # 훈련명을 기대하는 플래그
    expect_institution = False  # 훈련 기관을 예상하는 플래그 (훈련명 뒤에 나오는 텍스트가 기관일 경우)

    # 잘못된 날짜 형식을 교정하는 함수
    def fix_date_format(text):
        # '2018,.12'와 같은 잘못된 형식의 텍스트를 올바르게 변환
        fixed_text = text.replace(',', '.').replace('..', '.')
        return fixed_text

    # OCR로 추출된 텍스트에서 각 항목 식별
    for i, detection in enumerate(extracted_text):
        text = detection.strip()
        text = re.sub(r'\s+', ' ', text)
        text = fix_date_format(text)  # 날짜 형식 교정
        print(f"현재 텍스트: {text}")  # 디버깅용 텍스트 출력

        # 다른 섹션이 나오면 훈련 라벨링 중지
        if any(keyword in text for keyword in ['경력', '자격', '수상', '학력']):
            print(f"다른 섹션을 만났습니다. ({text}), 훈련 라벨링 중지.")
            in_training_section = False
            continue

        # 훈련사항 섹션 시작을 감지
        if '훈련' in text or '교육' in text:
            in_training_section = True
            print(f"훈련 섹션 시작: {text}")
            continue

        # 훈련 섹션에 속하는 텍스트만 라벨링
        if in_training_section:
            # 날짜 패턴 탐지 (훈련 시작/종료)
            date_match = date_pattern.search(text)
            if date_match:
                # 시작일이 비어있으면 시작일로 저장
                if not training_data['trainingStart']:
                    training_data['trainingStart'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-01"
                    print(f"trainingStart 처리 완료: {training_data['trainingStart']}")
                # 종료일이 비어있으면 종료일로 저장
                elif not training_data['trainingEnd']:
                    training_data['trainingEnd'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-01"
                    print(f"trainingEnd 처리 완료: {training_data['trainingEnd']}")
                    expect_name = True  # 종료일이 처리된 후에는 훈련명을 기대
                continue

            # 훈련명 탐지: 기관 키워드가 포함되지 않으면 훈련명으로 처리
            if expect_name and not any(keyword in text for keyword in institution_keywords):
                training_data['trainingName'] = text.strip()
                print(f"trainingName 처리 완료: {training_data['trainingName']}")
                expect_name = False  # 훈련명을 처리한 후 플래그 초기화
                expect_institution = True  # 다음에 기관이 나올 것으로 예상
                continue

            # 훈련 기관 탐지: 특정 키워드를 포함한 경우 훈련 기관으로 처리
            if expect_institution or any(keyword in text for keyword in institution_keywords):
                training_data['trainingInstitution'] = text.strip()
                print(f"trainingInstitution 처리 완료: {training_data['trainingInstitution']}")
                expect_institution = False  # 플래그 초기화
                continue

            # 훈련사항이 모두 완료되면 저장하고 초기화
            if training_data['trainingStart'] and training_data['trainingEnd'] and training_data['trainingName'] and training_data['trainingInstitution']:
                result_dict['training'].append(training_data)
                print(f"training 저장 완료: {training_data}")
                # 새로운 훈련 데이터를 처리하기 위해 초기화
                training_data = {
                    'trainingStart': '',
                    'trainingEnd': '',
                    'trainingName': '',
                    'trainingInstitution': ''
                }

    # 마지막 남은 훈련 정보 저장 (필드가 채워졌으면)
    if training_data['trainingStart'] or training_data['trainingName'] or training_data['trainingInstitution']:
        result_dict['training'].append(training_data)
        print(f"마지막 training 저장 완료: {training_data}")

    return result_dict

if __name__ == "__main__":
    # OCR 이미지 경로 설정
    image_path = 'C:/Users/SAMSUNG/Desktop/1022easyocr/img/sample1.jpg'

    # OCR을 위한 EasyOCR reader 생성
    reader = easyocr.Reader(['ko', 'en'], gpu=False)

    # 이미지에서 텍스트 추출
    result = reader.readtext(image_path)

    # 라벨링된 데이터 가져오기
    labeled_data = label_training_data([detection[1] for detection in result])

    # 이미지 파일명을 기반으로 폴더명 및 파일명 생성
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    folder_name = f"{base_name}_data"
    json_filename = f"{base_name}_training_labeled.json"

    # 폴더가 존재하지 않으면 생성
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"폴더 생성 완료: {folder_name}")

    # 폴더 경로와 JSON 파일명을 결합
    json_filepath = os.path.join(folder_name, json_filename)

    # JSON 형식으로 파일로 저장
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(labeled_data, json_file, ensure_ascii=False, indent=4)

    print(f"JSON 파일 저장 완료: {json_filepath}")
