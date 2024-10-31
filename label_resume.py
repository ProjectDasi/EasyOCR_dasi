import easyocr
import re
import json
import os

def label_resume_data(extracted_text):
    """
    OCR로 추출된 텍스트에서 개인 정보를 라벨링합니다.
    """
    # 결과를 저장할 딕셔너리
    result_dict = {
        'resume': {
            'name': '',
            'birthDate': '',
            'address': '',
            'phone': '',
            'email': '',
            'emergencyRelationship': '',
            'emergencyContact': '',
            'updateDate': ''
        }
    }

    # 변수 설정: birthDate와 updateDate를 따로 관리
    birth_year = ''
    birth_month = ''
    birth_day = ''
    update_year = ''
    update_month = ''
    update_day = ''
    
    # 플래그 설정: 각 필드에 대한 플래그 설정
    is_name = False
    is_address = False
    is_email = False
    is_phone = False
    is_emergency_contact = False
    is_birth_date = False  # 생년월일 플래그
    is_update_section = False  # updateDate 관련 플래그

    # OCR로 추출된 텍스트에서 각 항목 식별
    for i, detection in enumerate(extracted_text):
        text = detection.strip()
        text = re.sub(r'\s+', ' ', text)

        print(f"현재 텍스트: {text}")  # 디버깅용 텍스트 출력

        # 각 항목 식별 및 추출

        # 이름 추출
        if '성명' in text or '이름' in text:
            is_name = True
            continue
        if is_name:
            result_dict['resume']['name'] = text.strip()
            print(f"name 처리 완료: {result_dict['resume']['name']}")  # 디버깅 출력
            is_name = False
            continue

        # 주소 추출
        if '주소' in text:
            is_address = True
            continue
        if is_address:
            result_dict['resume']['address'] = text.strip()
            print(f"address 처리 완료: {result_dict['resume']['address']}")  # 디버깅 출력
            is_address = False
            continue

        # 이메일 추출
        if '이메일' in text or '이데일' in text:
            is_email = True
            continue
        if is_email:
            email_match = re.search(r'\S+@\S+\.\S+', text)
            if email_match:
                result_dict['resume']['email'] = email_match.group(0)
            else:
                corrected_email = text.replace('examplecom', 'example.com')
                result_dict['resume']['email'] = corrected_email
            print(f"email 처리 완료: {result_dict['resume']['email']}")  # 디버깅 출력
            is_email = False
            continue

        # 휴대전화 추출
        if '휴대전화' in text or '전화번호' in text:
            is_phone = True
            continue
        if is_phone and '비상연락처' not in text:
            phone_match = re.search(r'\d{3}-\d{3,4}-\d{4}', text)
            if phone_match:
                result_dict['resume']['phone'] = phone_match.group(0)
            print(f"phone 처리 완료: {result_dict['resume']['phone']}")  # 디버깅 출력
            is_phone = False
            continue

        # 비상연락처 및 관계 추출
        if '비상연락처' in text or '긴급연락처' in text:
            is_emergency_contact = True
            continue
        if is_emergency_contact:
            relationship_match = re.search(r'관계:\s*([\S]+)', text)
            if relationship_match:
                result_dict['resume']['emergencyRelationship'] = relationship_match.group(1)
                print(f"emergencyRelationship 처리 완료: {result_dict['resume']['emergencyRelationship']}")  # 디버깅 출력
            else:
                phone_match = re.search(r'\d{3}-\d{3,4}-\d{4}', text)
                if phone_match:
                    result_dict['resume']['emergencyContact'] = phone_match.group(0)
                    print(f"emergencyContact 처리 완료: {result_dict['resume']['emergencyContact']}")  # 디버깅 출력
                    is_emergency_contact = False
            continue

        # 생년월일 추출 (년,월,일 또는 여러 줄에 걸친 경우도 처리)
        if re.search(r'생년\s*월일', text):  # 생년월일 또는 생년 월일 처리
            is_birth_date = True
            birth_year, birth_month, birth_day = '', '', ''  # 초기화
            continue

        if is_birth_date:
            # "1953년 8월 7일"과 같은 한 줄 형식 처리
            date_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
            if date_match:
                birth_year, birth_month, birth_day = date_match.groups()
                result_dict['resume']['birthDate'] = f"{birth_year}-{birth_month.zfill(2)}-{birth_day.zfill(2)}"
                print(f"birthDate 처리 완료: {result_dict['resume']['birthDate']}")  # 디버깅 출력
                is_birth_date = False
                continue
            
            # "1950년", "7월 20일"이 분리된 경우 처리
            year_match = re.search(r'(\d{4})년', text)
            month_day_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', text)
            if year_match:
                birth_year = year_match.group(1)
            elif month_day_match:
                birth_month, birth_day = month_day_match.groups()
            
            # 모든 날짜 정보가 채워지면 birthDate에 저장
            if birth_year and birth_month and birth_day:
                result_dict['resume']['birthDate'] = f"{birth_year}-{birth_month.zfill(2)}-{birth_day.zfill(2)}"
                print(f"birthDate 처리 완료: {result_dict['resume']['birthDate']}")  # 디버깅 출력
                is_birth_date = False  # 플래그 해제
                continue

        # 업데이트 날짜 추출 (이전 텍스트가 '위 내용은 틀림없음'일 경우 추출)
        if '위 내용은 틀림없음' in text:
            is_update_section = True  # 이 텍스트 이후에 날짜 데이터를 처리하도록 플래그 설정
            continue

        if is_update_section:
            # 년도, 월, 일 처리
            if '년' in text:
                update_year_match = re.search(r'(\d{4})\s*년', text)
                if update_year_match:
                    update_year = update_year_match.group(1)
                    print(f"update_year 처리 완료: {update_year}")  # 디버깅 출력
                continue
            if re.match(r'^\d{1,2}$', text) and update_year and not update_month:
                update_month = text.zfill(2)
                print(f"update_month 처리 완료: {update_month}")  # 디버깅 출력
                continue
            if re.match(r'^\d{1,2}$', text) and update_month and not update_day:
                update_day = text.zfill(2)
                print(f"update_day 처리 완료: {update_day}")  # 디버깅 출력

            # updateDate를 완성하고 플래그 초기화
            if update_year and update_month and update_day:
                result_dict['resume']['updateDate'] = f"{update_year}-{update_month}-{update_day}"
                print(f"updateDate 처리 완료: {result_dict['resume']['updateDate']}")  # 디버깅 출력
                update_year, update_month, update_day = '', '', ''
                is_update_section = False  # 플래그 초기화

    return result_dict

# 만약 이 파일을 직접 실행한다면
if __name__ == "__main__":
    # OCR 이미지 경로 설정
    image_path = 'C:/Users/SAMSUNG/Desktop/1022easyocr/img/sample1.jpg'

    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    result = reader.readtext(image_path)

    labeled_data = label_resume_data([detection[1] for detection in result])

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    folder_name = f"{base_name}_data"
    json_filename = f"{base_name}_resume_labeled.json"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"폴더 생성 완료: {folder_name}")

    json_filepath = os.path.join(folder_name, json_filename)

    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(labeled_data, json_file, ensure_ascii=False, indent=4)

    print(f"JSON 파일 저장 완료: {json_filepath}")
