import easyocr
import re
import json
import os

def label_education_data(extracted_text):
    # 결과를 저장할 딕셔너리
    result_dict = {
        'education': []
    }

    # 변수 설정: 현재 처리 중인 education 데이터
    education_data = {
        'educationStart': '',
        'educationEnd': '',
        'school': '',
        'major': ''
    }

    # 플래그 설정: 학력 섹션인지 확인하는 플래그
    in_education_section = False
    expect_end_date = False

    # OCR로 추출된 텍스트에서 각 항목 식별
    for i, detection in enumerate(extracted_text):
        text = detection.strip()
        text = re.sub(r'\s+', ' ', text)  # 텍스트 내의 연속된 공백을 한 칸으로 치환

        # "사랑"이라는 단어를 "사항"으로 교정
        if '사랑' in text:
            text = text.replace('사랑', '사항')

        print(f"현재 텍스트: {text}")  # 디버깅용 텍스트 출력

        # **학력 섹션을 감지** (학력, 학교명, 전공분야 등의 키워드를 통해 시작 및 종료 감지)
        if '학력' in text or '학교명' in text or '전공분야' in text:
            in_education_section = True
            print(f"학력 섹션 시작: {text}")
            continue

        # 학력 섹션이 끝났을 때 플래그 해제
        if any(keyword in text for keyword in ['경력', '자격', '훈련', '수상']):
            if in_education_section:
                print(f"다른 섹션을 만났습니다: {text}, 학력 섹션 종료")
                in_education_section = False
                continue

        # 학력 섹션에 속하는 텍스트만 처리
        if in_education_section:
            # 첫 번째 줄에 시작 날짜가 있는지 확인
            if re.match(r'\d{4}\.\d{2}', text):
                if not expect_end_date:
                    # 첫 번째로 나오는 날짜는 educationStart로 처리
                    education_data['educationStart'] = f"{text[:4]}-{text[5:7]}-01"
                    print(f"educationStart 처리 완료: {education_data['educationStart']}")
                    expect_end_date = True
                else:
                    # 두 번째로 나오는 날짜는 educationEnd로 처리
                    education_data['educationEnd'] = f"{text[:4]}-{text[5:7]}-01"
                    print(f"educationEnd 처리 완료: {education_data['educationEnd']}")
                    expect_end_date = False
                continue

            # 학교명 추출
            if '대학교' in text or '대학원' in text:
                education_data['school'] = text.strip()
                print(f"school 처리 완료: {education_data['school']}")
                continue

            # 전공 분야 추출
            if '공학' in text or '학' in text:
                education_data['major'] = text.strip()
                print(f"major 처리 완료: {education_data['major']}")
                continue

            # 학력 정보가 완료되면 저장
            if education_data['school'] or education_data['major'] or education_data['educationStart'] or education_data['educationEnd']:
                result_dict['education'].append(education_data.copy())
                print(f"education 저장 완료: {education_data}")
                # 다음 학력을 위한 초기화
                education_data = {
                    'educationStart': '',
                    'educationEnd': '',
                    'school': '',
                    'major': ''
                }
                expect_end_date = False  # 다음 섹션을 위해 초기화

    return result_dict

# 만약 이 파일을 직접 실행한다면
if __name__ == "__main__":
    # OCR 이미지 경로 설정
    image_path = 'C:/Users/SAMSUNG/Desktop/1022easyocr/img/sample2.jpg'

    # OCR을 위한 EasyOCR reader 생성
    reader = easyocr.Reader(['ko', 'en'], gpu=False)

    # 이미지에서 텍스트 추출
    result = reader.readtext(image_path)

    # 라벨링된 데이터 가져오기
    labeled_data = label_education_data([detection[1] for detection in result])

    # 이미지 파일명을 기반으로 폴더명 및 파일명 생성
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    folder_name = f"{base_name}_data"
    json_filename = f"{base_name}_education_labeled.json"

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
