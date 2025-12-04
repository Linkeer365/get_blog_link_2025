import sys
import time

import psycopg2
from psycopg2.extras import RealDictCursor

from archivenow import archivenow

import wayback

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
                archive_link = archivenow.push(full_url, "ia")[0]
                if not archive_link.startswith('https://web.archive.org/web/'):
                    time.sleep(30)
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
        

    except Exception as e:
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
    cnt = 0
    while cnt<=200:
        get_notyet_archive_link(db_config,'wayback_link1','wayback_date1')
        cnt+=1