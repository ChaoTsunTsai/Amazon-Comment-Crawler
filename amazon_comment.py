from playwright.sync_api import sync_playwright
import time
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import json

# 設定與共用
base_dir = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(base_dir, "files")
os.makedirs(files_dir, exist_ok=True)
current_time = datetime.today().strftime("%Y%m%d_%H%M%S")

AMAZON_EMAIL = "AMAZON_EMAIL"
AMAZON_PASSWORD = "AMAZON_PASSWORD"

SELECTORS = {
    "login_entry_btn": "#nav-link-accountList",
    "email_input": "#ap_email_login",
    "continue_btn": "input[aria-labelledby='continue-announce']",
    "password_input": "#ap_password",
    "submit_btn": "input#signInSubmit",
    "phone_skip_link": "#ap-account-fixup-phone-skip-link",
    "see_all_reviews": "a[data-hook='see-all-reviews-link-foot']",
    "next_page_btn": "li.a-last a"
}

def log(idx: int | None, msg: str):
    prefix = f"[{idx}] " if idx is not None else ""
    print(prefix + msg)

def load_product_urls(path: str) -> list[str]:
    urls = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到 {path}，請在與此腳本同目錄放置 product_url.txt")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    if not urls:
        raise ValueError("product_url.txt 內沒有有效的 URL（空行或只有註解）。")
    return urls

def extract_product_name(url: str) -> str:
    """
    從 Amazon URL 中提取商品名稱
    範例: https://www.amazon.com/Name/dp/ID -> Name
    """
    # 針對標準 Amazon 商品頁網址結構提取
    match = re.search(r"amazon\.com/([^/]+)/dp", url)
    if match:
        return match.group(1)
    return "Unknown_Product"

def login_amazon(page, email, password):
    """
    執行 Amazon 登入流程
    """
    log(None, "正在前往 Amazon 首頁...")
    page.goto("https://www.amazon.com/", timeout=60000)
    
    # 點擊首頁的 "Hello, sign in"
    try:
        page.wait_for_selector(SELECTORS["login_entry_btn"], timeout=10000)
        page.click(SELECTORS["login_entry_btn"])
    except Exception as e:
        log(None, f"找不到登入按鈕，可能需要人工介入或 Selector 已變更: {e}")
        return

    # 輸入 Email
    log(None, "正在輸入 Email...")
    try:
        page.wait_for_selector(SELECTORS["email_input"], timeout=10000)
        page.fill(SELECTORS["email_input"], email)
        page.click(SELECTORS["continue_btn"])
    except Exception as e:
        log(None, f"輸入 Email 失敗: {e}")
        return

    # 輸入密碼
    log(None, "正在輸入密碼...")
    try:
        page.wait_for_selector(SELECTORS["password_input"], timeout=10000)
        page.fill(SELECTORS["password_input"], password)
        
        # 點擊登入 (Sign-In)
        page.click(SELECTORS["submit_btn"])
        log(None, "已送出帳號密碼資訊")
        
        # 稍微等待頁面跳轉
        time.sleep(3)

        try:
            # 設定 5 秒 timeout，若頁面出現則點擊跳過，沒出現則忽略
            page.wait_for_selector(SELECTORS["phone_skip_link"], timeout=5000)
            log(None, "偵測到「新增手機號碼」頁面，正在執行跳過...")
            page.click(SELECTORS["phone_skip_link"])
            # 點擊後稍微等待頁面反應
            time.sleep(2)
        except Exception:
            # 若無此元素 (Timeout) 或發生錯誤，視為無需跳過
            log(None, "未偵測到（或無需）跳過手機號碼頁面")
        
    except Exception as e:
        log(None, f"輸入密碼失敗: {e}")

def go_to_review_page(page, url):
    """
    前往商品頁面並點擊 'See all reviews'
    """
    log(None, f"正在前往商品頁面: {url}")
    try:
        page.goto(url, timeout=60000)
        
        # 等待並點擊 'See all reviews'
        try:
            log(None, "正在尋找 'See all reviews' 連結...")
            page.wait_for_selector(SELECTORS["see_all_reviews"], timeout=10000)
            page.click(SELECTORS["see_all_reviews"])
            log(None, "已點擊 'See all reviews'，等待評論頁面載入...")
            
            # 這裡可以加上簡單的等待，確保進入列表頁 (例如等待評論列表元素)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2) # 緩衝
            
        except Exception as e:
            log(None, f"找不到或無法點擊 'See all reviews' 連結: {e}")
            
    except Exception as e:
        log(None, f"前往商品頁面失敗: {e}")

def change_sort_to_most_recent(page):
    """
    透過修改 URL 參數將評論排序切換為 Most recent
    """
    log(None, "正在透過 URL 強制切換排序為 'Most recent'...")
    
    current_url = page.url
    
    # 檢查 URL 是否已經包含排序參數，避免重複刷新
    if "sortBy=recent" in current_url:
        log(None, "當前 URL 已包含 sortBy=recent，無需切換。")
        return

    # 構造新 URL
    # 判斷當前 URL 是否已有參數 (通常點擊 See all reviews 後會有 ?ie=UTF8...)
    separator = "&" if "?" in current_url else "?"
    
    # 強制加上 sortBy=recent 與 pageNumber=1
    new_url = f"{current_url}{separator}sortBy=recent&pageNumber=1"
    
    try:
        log(None, f"跳轉至新 URL: {new_url}")
        page.goto(new_url, timeout=60000)
        
        # 等待頁面載入
        page.wait_for_load_state("domcontentloaded")
        
        try:
            page.wait_for_selector("[data-hook='review']", timeout=10000)
            log(None, "成功載入 'Most recent' 排序的評論列表。")
        except Exception:
            log(None, "警告: 等待評論元素逾時，可能是沒有評論或頁面結構改變。")
            
        time.sleep(2)
        
    except Exception as e:
        log(None, f"切換 URL 失敗: {e}")

def get_reviews(page, cutoff_date=None):
    """
    抓取當前頁面的評論資訊 (目前僅實作 Poster)
    """
    log(None, "正在讀取評論區塊...")
    
    # 定位所有評論區塊    
    review_elements = page.locator("[data-hook='review']").all()
    
    log(None, f"本頁共偵測到 {len(review_elements)} 則評論")

    results = []
    stop_flag = False

    for idx, review in enumerate(review_elements):
        try:
            # Date
            post_date_el = review.locator("[data-hook='review-date']").first
            post_date_raw = post_date_el.inner_text().strip() if post_date_el.count() > 0 else "N/A"
            date_match = re.search(r"on\s+(.+)$", post_date_raw)
            date_str_part = date_match.group(1).strip()  # 取得 "September 15, 2025"
            dt_obj = datetime.strptime(date_str_part, "%B %d, %Y")

            if cutoff_date and dt_obj < cutoff_date:
                log(idx+1, f"偵測到舊評論 ({dt_obj.strftime('%Y-%m-%d')})，觸發停止條件。")
                stop_flag = True
                break

            formatted_date = dt_obj.strftime("%Y-%m-%d")

            # Poster
            poster_el = review.locator(".a-profile-name").first
            poster = poster_el.inner_text().strip() if poster_el.count() > 0 else "Unknown"

            # Rating
            rating_el = review.locator("[data-hook='review-star-rating'] span.a-icon-alt").first
            rating_raw = rating_el.inner_text().strip() if rating_el.count() > 0 else "N/A"
            rating_match = re.search(r"(\d+(\.\d+)?)", rating_raw)
            rating = int(float(rating_match.group(1))) if rating_match else 0

            # Title
            title_el = review.locator("[data-hook='review-title']").first
            title = "N/A"
            
            if title_el.count() > 0:
                title_text = title_el.inner_text().strip()
                
                # 如果有抓到評分文字，且標題是以該評分文字開頭，就將其移除
                if rating_raw != "N/A" and title_text.startswith(rating_raw):
                    # 移除 rating_raw 的長度，並再次 strip 去除留下的空白
                    title_text = title_text[len(rating_raw):].strip()
                
                # 處理換行 (取第一行作為標題)
                title = title_text.split('\n')[0].strip()

            # Format Strip (Style / Size)
            format_el = review.locator("[data-hook='format-strip']").first
            style_val = "N/A"
            size_val = "N/A"
            
            if format_el.count() > 0:
                format_text = format_el.inner_text().strip()
                
                # 解析 Style
                style_match = re.search(r"Style:\s*(.+?)(?=\s*Size:|$)", format_text)
                if style_match:
                    style_val = style_match.group(1).strip(" |")
                
                # 解析 Size
                size_match = re.search(r"Size:\s*(.+?)(?=\s*Style:|$)", format_text)
                if size_match:
                    size_val = size_match.group(1).strip(" |")

            # Content
            content_el = review.locator("[data-hook='review-body']").first
            content = content_el.inner_text().strip() if content_el.count() > 0 else "N/A"

            log(idx+1, f"Poster: {poster} | Rating: {rating} | Post Date: {formatted_date} | Title: {title} | Content: {content}")
            
            results.append({
                "Poster": poster,
                "Rating": rating,
                "Post Date": formatted_date,
                "Style": style_val,
                "Size": size_val,
                "Title": title,
                "Content": content
            })

        except Exception as e:
            log(idx+1, f"抓取單則評論失敗: {e}")
            continue
            
    return results, stop_flag

def scrape_all_reviews(page):
    """
    [新增函式] 負責翻頁並收集所有評論
    """
    all_reviews = []
    page_num = 1
    
    # target_date = datetime.now() - timedelta(days=365)
    target_date = None
    log(None, f"設定爬取截止日期為: {target_date.strftime('%Y-%m-%d') if target_date else '無限制'}")

    while True:
        log(None, f"--- 正在讀取第 {page_num} 頁評論 ---")
        
        # 抓取當前頁面資料
        reviews, stop_flag = get_reviews(page, cutoff_date=target_date)
        all_reviews.extend(reviews)

        if stop_flag:
            log(None, "已達到日期限制，停止翻頁。")
            break
        
        # 檢查是否有下一頁按鈕
        # Amazon 的下一頁按鈕通常在 li.a-last 裡面，如果是最後一頁，a 標籤通常會消失或 class 變更
        next_btn = page.locator(SELECTORS["next_page_btn"]).first
        
        if next_btn.is_visible():
            try:
                log(None, "偵測到下一頁，準備翻頁...")
                next_btn.click()
                
                # 等待頁面載入                
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3) 
                
                page_num += 1
            except Exception as e:
                log(None, f"翻頁失敗或已達最後一頁: {e}")
                break
        else:
            log(None, "未發現下一頁按鈕 (或已是最後一頁)，停止翻頁。")
            break
            
    return all_reviews

def main():
    url_list_path = os.path.join(base_dir, "product_url.txt")
    
    # 讀取 URL
    try:
        product_urls = load_product_urls(url_list_path)
        log(None, f"已讀取 {len(product_urls)} 個待處理 URL")
    except Exception as e:
        log(None, f"讀取 URL 失敗: {e}")
        return

    # 啟動瀏覽器
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 登入 Amazon
        login_amazon(page, AMAZON_EMAIL, AMAZON_PASSWORD)
        
        # 遍歷商品並進入評論頁
        for i, url in enumerate(product_urls):
            log(None, f"--- 開始處理第 {i+1} 個商品 ---")

            product_name = extract_product_name(url)

            go_to_review_page(page, url)

            change_sort_to_most_recent(page)

            all_reviews = scrape_all_reviews(page)

            for review in all_reviews:
                review["Product Name"] = product_name
            
            if all_reviews:
                log(None, f"準備匯出 {len(all_reviews)} 筆資料...")
                
                try:
                    # 建立 DataFrame
                    df = pd.DataFrame(all_reviews)
                    
                    # 處理檔名，移除非法字元並加上時間戳記
                    safe_product_name = re.sub(r'[\\/*?:"<>|]', "", product_name)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    filename = f"{safe_product_name}_{timestamp}.xlsx"
                    file_path = os.path.join(files_dir, filename)
                    
                    # 輸出 Excel
                    df.to_excel(file_path, index=False)
                    log(None, f"成功匯出 Excel: {file_path}")
                    
                except Exception as e:
                    log(None, f"匯出 Excel 失敗: {e}")
            else:
                log(None, "本商品無評論資料，跳過匯出。")

            # 若要一次跑完測試，可以註解下面這行 break
            # break

        input("請按 Enter 鍵結束本次測試 (瀏覽器將關閉)...")
        
        browser.close()

if __name__ == "__main__":
    main()