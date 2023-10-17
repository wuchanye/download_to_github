from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import time
import os
import requests
import base64
from bs4 import BeautifulSoup
import hashlib


from flask import Flask
app = Flask(__name__)

line_bot_api=LineBotApi('h3KUlT/r7nBj0F1L7SiDJf4e809FD64XLazi5LGtx7ch3LhjtqiqA0Mx4RDHGPm/VUNOkNqqqNQO/TJnj/sx1OQU+j2KlmGsgAQG3R0GG00Z47xrW2kYla+V4wFrt5WZ9Ku612SwHFVtAnGMzkMeZgdB04t89/1O/w1cDnyilFU=')
handler=WebhookHandler('d433242811b1a47be485a3068a7318d1') 


@app.route("/callback" , methods = ['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

WAITING_FOR_FOOD_NAME = 1
WAITING_FOR_QUERY_NUM = 2
WAITING_FOR_IMG = 3
NORMAL = 0
current_state = None

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    global current_state
    global keyword
    
    if current_state == WAITING_FOR_FOOD_NAME:
        keyword = user_message  # 將用戶的回覆儲存在 keyword 變數中
        current_state = NORMAL  # 回復正常狀態
        img_content = download_images_with_beautifulsoup(1, keyword)
        
        if img_content:  # 不是空列表，即有搜尋結果
            github_token = os.environ.get('github_token')
            img_message = upload_image_to_github(img_content, keyword, github_token)
            line_bot_api.reply_message(event.reply_token, img_message)
    else:
        if user_message == ("@查詢"):
            current_state = WAITING_FOR_FOOD_NAME
            message = TextSendMessage(text='請輸入食物名稱：')
            line_bot_api.reply_message(event.reply_token, message)
                    
    
def download_images_with_beautifulsoup(round, img_keyword):
    # 獲取 html 內容
    url = f'https://www.google.com.hk/search?q={img_keyword}&tbm=isch'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    
    max_image_size = 1024 * 1024
    img_content = None  # 用于存储图像内容
    
    for i in range(round):
        try:
            # 分析網頁, 找圖片元素
            img_elements = soup.find_all('img') 
            
            for element in img_elements:
                # 遍歷元素, 鎖定屬性
                img_url = element.get('src')
                if isinstance(img_url, str) and img_url.startswith('https://'): # 留下https://開頭的url
                    if data_url_count == 0:
                        data_url_count += 1
                        continue
                    else:
                        r = requests.get(img_url)
                        if len(r.content) < max_image_size: 
                            img_content = r.content # 將二進制內容儲存在參數
                            break
        except Exception as e:
            print(f"出现错误：{str(e)}")
            continue
        
    print("爬取完成")
    time.sleep(0.5)
    return img_content


def upload_image_to_github(image_content, keyword, github_token):
    github_username = 'wuchanye'
    github_repo = 'download_to_github'
    github_folder = 'img2'
    filename = keyword + '.jpg'
    img_message = None
    
    
    sha1 = hashlib.sha1()
    sha1.update(image_content)
    sha1_hash = sha1.hexdigest()
    
    url = f'https://api.github.com/repos/{github_username}/{github_repo}/contents/{github_folder}/{filename}'
    headers = {
        'Authorization': f'Bearer {github_token}',
    }
    
    response = requests.get(url, headers=headers)
    existing_file_data = response.json()
    existing_sha = existing_file_data.get('sha', '')
    
    if existing_sha != sha1_hash:
        
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
        }

        data = {
            'message': 'Update image',
            'content': base64.b64encode(image_content).decode('utf-8'),
            'sha': existing_sha,
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200 or response.status_code == 201:
            image_url = response.json().get('content').get('download_url')
            img_message = ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
            print("文件已成功更新到GitHub存储库的文件夹。")
        else:
            print(f"上传文件失败，HTTP响应代码: {response.status_code}")
            print(f"响应内容: {response.text}")
            img_message = TextSendMessage(text="上傳圖片失敗。")
    return img_message

# 主程式
if __name__ == '__main__':
    current_state = NORMAL
    keyword = ""
    
    app.run()
