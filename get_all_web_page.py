import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_all_web_pages(base_dir, blog_root):
    pages = []

    base_url = "https://linkeer365.github.io/" + blog_root if blog_root != "linkeer365.github.io" else "https://linkeer365.github.io/"

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == 'index.html':
                # 获取相对路径
                relative_path = os.path.relpath(root, base_dir)
                if relative_path == '.':
                    url = '/index.html'
                    abbr_link = ''
                else:
                    url = f'/{relative_path}/index.html'
                    abbr_link = f'{relative_path}'

                full_path = os.path.join(root, file)
                pages.append({
                    'base_url': base_url,
                    'root': blog_root,
                    'abbr_link': abbr_link.replace('\\', '/'),
                    'full_url': base_url+'/'+abbr_link.replace('\\', '/'),
                })

    return pages

def get_all(all_pages, post_dir):
    titles = {}
    dates = {}
    contents = {}
    if not post_dir:
        return titles

    for each in os.listdir(post_dir):
        if each.endswith('.md'):
            with open(os.path.join(post_dir, each), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                title = None
                abbrlink = None
                date = None
                cnt=0
                content = None
                for line_cnt,line in enumerate(lines,1):
                    if line.startswith('title: '):
                        title = line.split(': ')[1].strip().replace('\'','')
                    elif line.startswith('abbrlink: '):
                        abbrlink = line.split(': ')[1].strip().replace('\'','')
                    elif line.startswith('date: '):
                        date = line.split(': ')[1].strip().replace('\'','')
                    elif line.startswith('---'):
                        cnt+=1
                        if cnt==2:
                            content = '\n'.join(lines[line_cnt:])
                    if title and abbrlink and date and content:
                        titles[abbrlink] = title
                        dates[abbrlink] = date
                        contents[abbrlink] = content
                        break

    for page in all_pages:
        abbr_link_key = page['abbr_link'].replace('/', '')
        if abbr_link_key in titles:
            page['title'] = titles[abbr_link_key]
            page['create_date'] = dates[abbr_link_key]
            page['content'] = contents[abbr_link_key]
        else:
            page['title'] = 'No-Title-Page'
            page['create_date'] = '1970-01-01 00:00:00'
            page['content'] = ' '

    return all_pages

def save_to_postgresql(pages, db_config):
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

        # 创建表（如果不存在）
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.blog_post (
            root text NOT NULL,
            abbr_link text NOT NULL,
            title text NULL,
            base_url text NOT NULL,
            full_url text NOT NULL,
            create_date varchar(30) NULL,
            "content" text NULL,
            wayback_link1 text NULL,
            wayback_date1 varchar(30) NULL,
            wayback_link2 text NULL,
            wayback_date2 varchar(30) NULL,
            wayback_link3 text NULL,
            wayback_date3 varchar(30) NULL,
            wayback_link4 text NULL,
            wayback_date4 varchar(30) NULL,
            wayback_link5 text NULL,
            wayback_date5 varchar(30) NULL,
            CONSTRAINT blog_post_pkey PRIMARY KEY (root,abbr_link)
        );
        """
        cursor.execute(create_table_query)

        # 清空现有数据（可选）
        # cursor.execute("DELETE FROM public.blog_post;")

        # 插入数据
        insert_query = """
        INSERT INTO public.blog_post (
            root,
            abbr_link, title, base_url, full_url, create_date, "content",
            wayback_link1, wayback_date1, wayback_link2, wayback_date2,
            wayback_link3, wayback_date3, wayback_link4, wayback_date4,
            wayback_link5, wayback_date5
        ) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (root,abbr_link) DO UPDATE SET
            title = EXCLUDED.title,
            base_url = EXCLUDED.base_url,
            full_url = EXCLUDED.full_url,
            create_date = EXCLUDED.create_date,
            "content" = EXCLUDED."content",
            wayback_link1 = EXCLUDED.wayback_link1,
            wayback_date1 = EXCLUDED.wayback_date1,
            wayback_link2 = EXCLUDED.wayback_link2,
            wayback_date2 = EXCLUDED.wayback_date2,
            wayback_link3 = EXCLUDED.wayback_link3,
            wayback_date3 = EXCLUDED.wayback_date3,
            wayback_link4 = EXCLUDED.wayback_link4,
            wayback_date4 = EXCLUDED.wayback_date4,
            wayback_link5 = EXCLUDED.wayback_link5,
            wayback_date5 = EXCLUDED.wayback_date5;
        """

        for page in pages:
            cursor.execute(insert_query, (
                page.get('root', ''),
                page.get('abbr_link', ''),
                page.get('title', ''),
                page.get('base_url', ''),
                page.get('full_url', ''),
                page.get('create_date', ''),
                page.get('content', ''),
                None, None, None, None,  # wayback_link1-2
                None, None, None, None,  # wayback_link3-4
                None, None               # wayback_link5
            ))

        # 提交事务
        conn.commit()
        print(f"成功将 {len(pages)} 条记录保存到 PostgreSQL 数据库")

    except Exception as e:
        print(f"保存到数据库时出错: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 使用示例
if __name__ == '__main__':

    # 根据具体情况修改 src等内容

    src = 'D:\workSpaces\Blogs\Linkeer365TinyMomentSource-master'
    public_dir = src+os.sep+'public'
    post_dir=src+os.sep+'source'+os.sep+'_posts'
    blog_root = 'Linkeer365Collection'
    db_config = {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres',
        'port': '5432'
    }

    # baseUrl 末尾不带斜杠
    all_pages = get_all_web_pages(base_dir=public_dir, blog_root=blog_root)
    all_pages = get_all(all_pages, post_dir=post_dir)

    for page in all_pages:
        print(f"简洁URL: {page['abbr_link']}")
        print(f"完整URL: {page['full_url']}")
        print(f"标题: {page['title']}")
        print(f"日期: {page['create_date']}")
        print(f'内容: {page["content"][:100]}...')  # 只打印前100个字符
        print("---")

    # 保存为 JSON 文件
    with open(src+os.sep+'pages.json', 'w', encoding='utf-8') as f:
        json.dump(all_pages, f, ensure_ascii=False, indent=2)

    # 保存到 PostgreSQL 数据库（新增功能）
    # 请根据实际情况修改数据库配置
    save_to_postgresql(all_pages, db_config)