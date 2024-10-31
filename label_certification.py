import easyocr
import re
import json
import os

def label_certification_data(extracted_text):
    """
    OCR로 추출된 텍스트에서 자격증 정보를 라벨링합니다.
    """
    # 결과를 저장할 딕셔너리
    resultDict = {
        'certification': []
    }

    # 변수 설정: 현재 처리 중인 certification 데이터
    certificationData = {
        'certificationName': '',
        'acquisitionDate': '',
        'issuingAuthority': ''
    }

    # 플래그 설정: 각 필드에 대한 플래그 설정
    isName = False
    isAuthority = False
    isNewEntry = False

    # OCR로 추출된 텍스트에서 각 항목 식별
    for i, detection in enumerate(extracted_text):
        text = detection.strip()
        text = re.sub(r'\s+', ' ', text)

        print(f"현재 텍스트: {text}")  # 디버깅용 텍스트 출력

        # 자격증, 면허, 수상 라벨링 중 - '훈련' 또는 '학력'이 나오면 종료
        if any(keyword in text for keyword in ['훈련', '학력']):
            print(f"다른 섹션을 만났습니다. ({text}), 자격증 라벨링 종료.")
            break

        # 취득일(날짜) 패턴 탐지
        dateMatch = re.match(r'(\d{4})\.(\d{2})\.(\d{2})', text)
        if dateMatch:
            # 이전 자격증 데이터를 저장
            if certificationData['certificationName'] and certificationData['issuingAuthority']:
                resultDict['certification'].append(certificationData)
                print(f"certification 저장 완료: {certificationData}")
                # 새로운 자격증을 위해 초기화
                certificationData = {
                    'certificationName': '',
                    'acquisitionDate': '',
                    'issuingAuthority': ''
                }

            # 자격증 취득일 처리
            certificationData['acquisitionDate'] = f"{dateMatch.group(1)}-{dateMatch.group(2).zfill(2)}-{dateMatch.group(3).zfill(2)}"
            print(f"acquisitionDate 처리 완료: {certificationData['acquisitionDate']}")
            isNewEntry = True  # 새로운 자격증 항목 플래그 설정
            continue

        # 발급기관(issuingAuthority) 처리
        if any(keyword in text for keyword in ['공단', '협회', '발급', '협의회', '전자']):
            certificationData['issuingAuthority'] = text.strip()
            print(f"issuingAuthority 처리 완료: {certificationData['issuingAuthority']}")
            isAuthority = True
            continue

        # 자격증 이름 처리
        if isNewEntry and not certificationData['certificationName']:
            certificationData['certificationName'] = text.strip()
            print(f"certificationName 처리 완료: {certificationData['certificationName']}")
            continue

    # 마지막 자격증 정보가 저장되지 않았을 수 있으니 마지막으로 처리
    if certificationData['certificationName'] and certificationData['acquisitionDate'] and certificationData['issuingAuthority']:
        resultDict['certification'].append(certificationData)
        print(f"마지막 certification 저장 완료: {certificationData}")

    return resultDict

# 만약 이 파일을 직접 실행한다면
if __name__ == "__main__":
    # OCR 이미지 경로 설정
    imagePath = 'C:/Users/SAMSUNG/Desktop/1022easyocr/img/sample1.jpg'

    # OCR을 위한 EasyOCR reader 생성
    reader = easyocr.Reader(['ko', 'en'], gpu=False)

    # 이미지에서 텍스트 추출
    result = reader.readtext(imagePath)

    # 라벨링된 데이터 가져오기
    labeledData = label_certification_data([detection[1] for detection in result])

    # 이미지 파일명을 기반으로 폴더명 및 파일명 생성
    baseName = os.path.splitext(os.path.basename(imagePath))[0]  # 이미지 파일명에서 확장자 제거
    folderName = f"{baseName}_data"  # 이미지 파일명에 기반한 폴더명 생성
    jsonFilename = f"{baseName}_certificationLabeled.json"  # JSON 파일명 생성

    # 폴더가 존재하지 않으면 생성
    if not os.path.exists(folderName):
        os.makedirs(folderName)
        print(f"폴더 생성 완료: {folderName}")

    # 폴더 경로와 JSON 파일명을 결합
    jsonFilepath = os.path.join(folderName, jsonFilename)

    # JSON 형식으로 파일로 저장
    with open(jsonFilepath, 'w', encoding='utf-8') as jsonFile:
        json.dump(labeledData, jsonFile, ensure_ascii=False, indent=4)

    print(f"JSON 파일 저장 완료: {jsonFilepath}")
