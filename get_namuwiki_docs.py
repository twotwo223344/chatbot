from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def load_namuwiki_docs_selenium(topic):
    # Selenium 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 나무위키 페이지 열기
    url = f"https://namu.wiki/w/{topic}"
    driver.get(url)

    try:
        # '본문 내용을 포함한 특정 클래스' 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "UCfKg97Y"))  # 실제 본문 내용이 포함된 클래스 이름
        )
        
        # 본문 내용 추출
        content = driver.find_element(By.CLASS_NAME, "UCfKg97Y").text
        print("본문 내용:", content)
        
    except Exception as e:
        print("페이지에서 본문 내용을 찾을 수 없습니다.")
        print("에러:", e)
        content = ""
    
    driver.quit()
    return content

# # 테스트
topic = "흑백요리사" # "K-POP/역사" #"흑백요리사"
text = load_namuwiki_docs_selenium(topic)
