import sqlite3
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def init_database():
    """初始化資料庫，建立 quotes 資料表"""
    conn = sqlite3.connect('quotes.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            author TEXT NOT NULL,
            tags TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("資料庫初始化完成")


def save_to_database(quotes_list):
    """將爬取的名言資料存入資料庫"""
    conn = sqlite3.connect('quotes.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quotes")
    
    for quote in quotes_list:
        cursor.execute(
            "INSERT INTO quotes (text, author, tags) VALUES (?, ?, ?)",
            (quote['text'], quote['author'], quote['tags'])
        )
    
    conn.commit()
    print(f"成功儲存 {len(quotes_list)} 筆資料到資料庫")
    conn.close()


def scrape_quotes():
    """使用 Selenium 爬取名言佳句（前 5 頁）"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    browser = webdriver.Chrome(options=chrome_options)
    
    all_quotes = []
    target_url = "http://quotes.toscrape.com/js/"
    
    try:
        browser.get(target_url)
        print(f"開始爬取: {target_url}")
        
        for page in range(1, 6):
            print(f"\n正在爬取第 {page} 頁...")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "quote"))
            )
            
            quote_elements = browser.find_elements(By.CLASS_NAME, "quote")
            
            for quote_elem in quote_elements:
                try:
                    text = quote_elem.find_element(By.CLASS_NAME, "text").text
                    text = text.strip('\u201c\u201d"')
                    author = quote_elem.find_element(By.CLASS_NAME, "author").text
                    tag_elements = quote_elem.find_elements(By.CLASS_NAME, "tag")
                    tags = ",".join([tag.text for tag in tag_elements])
                    
                    all_quotes.append({
                        'text': text,
                        'author': author,
                        'tags': tags
                    })
                    
                except NoSuchElementException as e:
                    print(f"擷取資料時發生錯誤: {e}")
                    continue
            
            print(f"第 {page} 頁爬取完成，共 {len(quote_elements)} 則名言")
            
            # 如果不是最後一頁，點擊 Next 按鈕換頁
            if page < 5:
                try:
                    next_button = WebDriverWait(browser, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.next > a"))
                    )
                    next_button.click()
                    sleep(1)  # 等待頁面載入
                except TimeoutException:
                    print("找不到 Next 按鈕或已到最後一頁")
                    break
                    
    except Exception as e:
        print(f"爬蟲執行時發生錯誤: {e}")
        
    finally:
        browser.quit()
        print("\n瀏覽器已關閉")
    
    return all_quotes


def main():
    """主程式"""
    print("=" * 50)
    print("動態名言爬蟲程式 - pacho.py")
    print("=" * 50)
    
    init_database()
    quotes = scrape_quotes()
    
    if quotes:
        save_to_database(quotes)
        print(f"\n爬取完成！共取得 {len(quotes)} 則名言")
    else:
        print("\n未取得任何資料")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
