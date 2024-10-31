import easyocr
import re
import json
import os

def label_work_experience_data(extracted_text):
    # 결과를 저장할 딕셔너리
    result_dict = {
        'workExperience': []
    }

    # 변수 설정: 현재 처리 중인 work_experience 데이터
    work_experience_data = {
        'workStart': '',
        'workEnd': '',
        'company': '',
        'workDescription': ''
    }

    # 플래그 설정: 각 필드에 대한 플래그 설정
    is_company = False
    is_description = False
    in_work_section = False  # 경력 섹션 감지 플래그

    # 텍스트 교정 함수 ('사랑'->'사항', '취1일'->'취득일', '면히'->'면허')
    def clean_text(text):
        corrections = {
            '사랑': '사항',
            '취1일': '취득일',
            '면히': '면허'
        }
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        return text

    # 정규식 패턴
    work_period_pattern = re.compile(r'\d{4}(\.\d{1,2})?\s*~\s*\d{4}(\.\d{1,2})?')  # 예: 2018~2019, 2018.3~2019.12
    date_pattern = re.compile(r'\d{4}(\.\d{1,2})?')  # 예: 2018.3, 2018

    # OCR로 추출된 텍스트에서 각 항목 식별
    for i, text in enumerate(extracted_text):
        text = clean_text(re.sub(r'\s+', ' ', text.strip()))
        print(f"현재 텍스트: {text}")  # 디버깅용 텍스트 출력

        # 경력 섹션 시작 확인
        if '경력' in text or '근무기간' in text:
            in_work_section = True
            print(f"경력 섹션 시작: {text}")
            continue

        # 경력 섹션 종료 조건 (자격, 학력 등의 다른 섹션을 만날 때)
        if any(keyword in text for keyword in ['자격', '학력', '수상', '훈련']):
            if in_work_section:
                print(f"경력 섹션 종료: {text}")
            in_work_section = False
            continue

        # 경력 섹션이 아닌 경우 라벨링 무시
        if not in_work_section:
            continue

        # 근무 기간 추출
        if work_period_pattern.search(text):
            dates = work_period_pattern.search(text).group()
            start_date, end_date = dates.split("~")
            work_experience_data['workStart'] = start_date.strip()
            work_experience_data['workEnd'] = end_date.strip()
            print(f"근무 기간 처리 완료: {work_experience_data['workStart']} ~ {work_experience_data['workEnd']}")
            is_company = True  # 근무처 탐색으로 플래그 설정
            continue

        # 근무 시작 또는 종료 날짜만 있는 경우 처리
        if date_pattern.match(text):
            date_match = date_pattern.search(text)
            if date_match:
                if not work_experience_data['workStart']:
                    work_experience_data['workStart'] = f"{date_match.group()}"
                    print(f"workStart 처리 완료: {work_experience_data['workStart']}")
                else:
                    work_experience_data['workEnd'] = f"{date_match.group()}"
                    print(f"workEnd 처리 완료: {work_experience_data['workEnd']}")
                    is_company = True  # 다음에는 근무처를 처리
            continue

        # "근무처" 키워드를 만나면 회사 이름을 다음 텍스트에서 찾도록 설정
        if '근무처' in text:
            is_company = True
            continue

        # 근무처 추출
        if is_company:
            work_experience_data['company'] = text
            print(f"company 처리 완료: {work_experience_data['company']}")
            is_company = False
            is_description = True  # 다음에는 업무 내용을 처리
            continue

        # "업무내용" 키워드를 만나면 업무 내용을 다음 텍스트에서 찾도록 설정
        if '업무내용' in text:
            is_description = True
            continue

        # 업무 내용 추출
        if is_description:
            work_experience_data['workDescription'] = text
            print(f"workDescription 처리 완료: {work_experience_data['workDescription']}")

            # 경력사항이 모두 완료되면 저장하고 초기화
            result_dict['workExperience'].append(work_experience_data)
            print(f"workExperience 저장 완료: {work_experience_data}")

            work_experience_data = {
                'workStart': '',
                'workEnd': '',
                'company': '',
                'workDescription': ''
            }

            is_description = False  # 플래그 초기화
            continue

    # 마지막 남은 경력 정보 저장
    if work_experience_data['workStart'] or work_experience_data['company'] or work_experience_data['workDescription']:
        result_dict['workExperience'].append(work_experience_data)
        print(f"마지막 workExperience 저장 완료: {work_experience_data}")

    return result_dict

if __name__ == "__main__":
    image_path = 'C:/Users/SAMSUNG/Desktop/1022easyocr/img/sample1.jpg'

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    result = reader.readtext(image_path)

    labeled_data = label_work_experience_data([detection[1] for detection in result])

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    folder_name = f"{base_name}_data"
    json_filename = f"{base_name}_workExperience_labeled.json"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"폴더 생성 완료: {folder_name}")

    json_filepath = os.path.join(folder_name, json_filename)

    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(labeled_data, json_file, ensure_ascii=False, indent=4)

    print(f"JSON 파일 저장 완료: {json_filepath}")