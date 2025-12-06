import sys
import time

import psycopg2
from psycopg2.extras import RealDictCursor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from archivenow import archivenow

import wayback

def archive_by_selenium(full_url):

    driver.get("https://web.archive.org/save")
    wait = WebDriverWait(driver, 10)
    
    try:
        input_box = wait.until(EC.presence_of_element_located((By.ID, "web-save-url-input")))
        input_box.send_keys(full_url)
    except Exception as e:
        print(f"填写输入框时出错: {e}")
    
    try:
        checkbox = wait.until(EC.presence_of_element_located((By.ID, "capture_all")))
        if (checkbox.get_attribute("checked")):
            checkbox.click()
    except Exception as e:
        print(f"操作checkbox时出错: {e}")
    
    try:
        upload_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"input[type='submit'][value='SAVE PAGE']")))[0]
        upload_btn.click()
    except Exception as e:
        print(f"上传btn获取出错: {e}")

    try:
        # 1. 显式等待“保存成功”的结果区域出现
        # 等待id为‘spn-result’的div元素出现在DOM中，最多等待300秒
        link_element = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#spn-result a"))
        )
        generated_link = link_element.get_attribute("href")

    except Exception as e:
        print(f"保存出错: {e}")
    
    return generated_link

def get_already_page(full_url,fresh_date='201701'):
    client = wayback.WaybackClient()
    results = list(client.search(full_url))
    date_start_idx = len("https://web.archive.org/web/")
    date_end_idx = len("https://web.archive.org/web/20220313143510")
    # 能取就取最新的
    for each in results[::-1]:
        if each.view_url and each.view_url[date_start_idx:date_end_idx]>fresh_date:
            # print('already:',each.view_url)
            return each.view_url
    return None

def get_notyet_archive_link(db_config,field,field_date):
    """
    将页面数据保存到PostgreSQL数据库
    """
    try:
        # 建立数据库连接
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )
        
        cursor = conn.cursor()
        
        retrieve_table_query = f"""
        SELECT root,abbr_link,full_url 
        FROM public.blog_post
        WHERE {field} is null
        """
        
        cursor.execute(retrieve_table_query)
        
        date_start_idx = len("https://web.archive.org/web/")
        date_end_idx = len("https://web.archive.org/web/20220313143510")
        
        for root,abbr_link,full_url in cursor.fetchall():
            archive_link = get_already_page(full_url)
            
            if archive_link == None:
                # archive_link = archivenow.push(full_url, "ia")[0]
                if archive_link == None or not archive_link.startswith('https://web.archive.org/web/'):
                    time.sleep(10)
                    archive_link = archive_by_selenium(full_url)
                    print(archive_link)
                    if not archive_link.startswith('https://web.archive.org/web/'):
                        time.sleep(10)
                        continue
            archive_date = archive_link[date_start_idx:date_end_idx]
            cursor2 = conn.cursor()
            update_table_query = f"""
            UPDATE public.blog_post
            SET {field} = '{archive_link}',
            {field_date} = '{archive_date}'
            WHERE root = '{root}'
            AND abbr_link = '{abbr_link}'
            """
            cursor2.execute(update_table_query)
            # 提交事务
            conn.commit()
            with open("u2a.log",'a',encoding="utf-8") as f:
                f.write(f"{root} : {abbr_link}\n")
                f.write(archive_link+'\n\n')
            time.sleep(10)

    except Exception as e:
        print(root,abbr_link,'\t',archive_link)
        print(f"更新到数据库时出错: {e}")
        if conn:
            conn.rollback()
        

if __name__ == '__main__':

    db_config = {
        'host': 'localhost',
        'database': 'lsyhome',
        'user': 'postgres',
        'password': 'postgres',
        'port': '5432'
    }
    
    driver = webdriver.Chrome()
    cnt = 0
    while cnt<=200:
        get_notyet_archive_link(db_config,'wayback_link1','wayback_date1')
        cnt+=1