# Amazon-Comment-Crawler
An automated Amazon product review crawler developed with Python 3.13 + Playwright.
It automatically extracts product information, the latest reviews, ratings, etc,
then exports the collected data into an Excel file for easy analysis and organization.
 
*Before running the script, please update your AMAZON_EMAIL and AMAZON_PASSWORD in amazon_comment.py, and ensure your account has permission to view all product reviews.
 
## | **Features**<br>
 
1. Automatically opens each product page on Amazon<br>
2. Extracts product name<br>
3. Collects reviews sorted by **“Most recent”**, including:<br>
   · Reviewer name<br>
   · Rating (numeric only)<br>
   · Review date<br>
   · Style (if available)<br>
   · Size (if available)<br>
   · Review title<br>
   · Review content<br>
4. Automatically exports results to an **Excel (.xlsx)** file<br>
 
*Automatically stops at reviews older than one year to avoid duplicates and unnecessary data.*<br>
![example2](image/amazon_comment.png)<br>
## | **Package Installation**<br>
 
`pip install -r requirements.txt`<br>
 
## | **Target Business Configuration**<br>
 
Please paste the Amazon products link of the business you want to scrape reviews from into **product_url**.<br>
 
## | **Output File**<br>
![example4](image/output_file_excel.png)<br>
<br><br>
# | **Amazon 評論爬蟲**<br>
 
以 Python 3.13 + Playwright 開發的自動化 Amazon 評論爬蟲工具。<br>
可自動擷取產品資訊、最新評論、星等等資料，<br>
並將結果輸出為 Excel 檔案，方便後續分析與整理。<br>
 
*執行前請至 amazon_comment.py 更改您的 AMAZON_EMAIL & AMAZON_PASSWORD，確認您的帳號已被允許瀏覽商品所有評論
 
## | **功能特色**<br>
 
1. 自動開啟 Amazon 各產品頁面<br>
2. 擷取商品名稱<br>
3. 收集「最新排序」評論，包含：<br>
  · 評論者名稱<br>
  · 星等（純數字）<br>
  · 評論時間<br>
  · 產品規格 (若有)<br>
  · 產品尺寸 (若有)<br>
  · 評論標題<br>
  · 評論內容<br>
4. 結果自動輸出至 Excel (.xlsx)<br>
 
*自動停止在一年以前的評論，避免重複與冗長資料*<br>
![example2](image/amazon_comment.png)<br>
## | **套件安裝**<br>
 
`pip install -r requirements.txt`<br>
 
## | **目標商家設定**<br>
 
請至 product_url 貼上想要爬取評論的產品連結
 
## | **輸出檔案**<br>
 
![example4](image/output_file_excel.png)<br>
