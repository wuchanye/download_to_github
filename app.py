from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from opencc import OpenCC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from io import BytesIO
from PIL import Image
import pyimgur
import urllib.request as urllib_request
import urllib.parse as parse
import json
import time
import os
import requests
import re
import base64

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

def handle_message(event):
    user_message = event.message.text
    keyword = user_message
    messages = []

    
    img_url, message_text = download_images_and_upload_to_github(1, img_keyword, github_token)
    messages_text = "\n".join(messages_text)
    #img_message = ImageSendMessage(original_content_url=f'{img_url}',  preview_image_url=f'{img_url}')
    #messages = [messages_text , img_message]
    
    line_bot_api.reply_message(event.reply_token, messages_text)
   



def download_images_and_upload_to_github(round, keyword, github_token):
    message_text = []
    # Initialize the browser
    browser = init_browser(img_keyword)
    local_folder = 'imgs2'
    
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
        
    data_url_count = 0
    max_image_size = 1024 * 1024
    github_repo = 'wuchanye/test'  # Replace with your GitHub repository
    github_path = 'imgs2/' + img_keyword + '.jpg'
    
    for i in range(round):
        try:
            parent_element = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.islrc')))
            
            img_elements = WebDriverWait(parent_element, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))
            
            for element in img_elements:
                img_url = element.get_attribute('src')
                
                img_attributes = element.get_attribute('outerHTML')
                
                if isinstance(img_url, str):
                    if img_url.startswith('data:image/jpeg'):
                        if 'data-sz' not in img_attributes:
                            if data_url_count == 0:
                                data_url_count += 1
                                continue
                            else:
                                img_data = re.search(r'base64,(.*)', img_url).group(1)
                                image_data = base64.b64decode(img_data)
                                
                                if len(image_data) < max_image_size:
                                    image = Image.open(BytesIO(image_data))
                                    image = image.convert("RGB")
                                    
                                    # Save the image locally
                                    local_filename = f'./{local_folder}/{img_keyword}.jpg'
                                    image.save(local_filename)
                                    message_text.append('save file done')
                                    
                                    # Upload the image to GitHub
                                    message_text = upload_image_to_github(local_filename, github_repo, github_path, github_token, message_text)
                                    img_url = f'https://raw.githubusercontent.com/{github_repo}/main/img2/{img_keyword}.jpg'
                                    return img_url, message_text
                                    break
                    else:
                        if len(img_url) <= 200:
                            if 'images' in img_url:
                                local_filename = f'./{local_folder}/{img_keyword}.jpg'
                                r = requests.get(img_url)
                                if len(r.content) < max_image_size:
                                    with open(local_filename, 'wb') as file:
                                        file.write(r.content)
                                        file.close()
                                        message_text = upload_image_to_github(local_filename, github_repo, github_path, github_token)
                                        img_url = f'https://raw.githubusercontent.com/{github_repo}/main/img2/{img_keyword}.jpg'
                                        return img_url, message_text
                                        break
        except StaleElementReferenceException:
            print("出現StaleElementReferenceException錯誤，重新定位元素")
            continue
        
    time.sleep(0.5)
    browser.close()
    print("爬取完成") 

def upload_image_to_github(local_filename, github_repo, github_path, github_token, message_text):
    with open(local_filename, 'rb') as file:
        content = file.read()

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }
    
    url = f"https://api.github.com/repos/{github_repo}/contents/{github_path}"
    data = {
        "message": "Add image",
        "content": base64.b64encode(content).decode('utf-8'),
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        message_text.append("Image uploaded to GitHub successfully.")
    else:
        message_text.append("Failed to upload image to GitHub.")
        message_text.append(response.text)
    return message_text

  # 主程式
if __name__ == '__main__':
    keyword = ""
    app.run()
