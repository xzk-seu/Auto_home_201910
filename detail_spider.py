# coding:utf-8


import json
import os
import random
import time
import urllib
from urllib.request import Request
from urllib.request import urlopen

from bs4 import BeautifulSoup
from tqdm import tqdm

from Logger import logger
from settings import my_headers
from multiprocessing import Pool


def get_proxy():
    proxy_host = "http-proxy-t2.dobel.cn"
    proxy_port = "9180"
    proxy_user = "NJDNDX7AIHK3SM0"
    proxy_pass = "VYTirAXy"
    proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxy_host,
        "port": proxy_port,
        "user": proxy_user,
        "pass": proxy_pass,
    }
    proxy = {
        "http": proxy_meta,
        "https": proxy_meta,
    }
    return proxy


# 此函数用于得到html
def get_content(url, headers):
    """
    此函数用于抓取返回403禁止访问的网页
    """

    max_try = 0
    html = None
    while max_try < 5:
        max_try += 1
        try:
            random_header = random.choice(headers)

            """
            对于Request中的第二个参数headers，它是字典型参数，所以在传入时
            也可以直接将个字典传入，字典中就是下面元组的键值对应
            """
            req = Request(url)
            req.add_header("User-Agent", random_header)
            req.add_header("GET", url)
            req.add_header("Host", "club.autohome.com.cn")
            req.add_header("Referer", "https://club.autohome.com.cn/bbs/thread/cde6ae21bb64db83/82386958-2.html")

            proxy = get_proxy()
            # proxy = None
            proxy_support = urllib.request.ProxyHandler(proxy)
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)

            html = urlopen(req)
            break
        except Exception as e:
            if max_try < 5:
                logger.info("Try: %d | Error : %s" % (max_try, str(e)))
            else:
                logger.error("Try: %d | Error : %s" % (max_try, str(e)))
            time.sleep(max_try)
    return html


def get_page_info(html):  # 得到易读的html
    soup = None
    try:
        soup = BeautifulSoup(html, "html.parser")
    except AttributeError:
        logger.error('getJDInfo-getPageInfo:html is None!')
    return soup


def switch_ip():
    url = 'http://ip.dobel.cn/switch-ip'
    get_content(url, my_headers)
    logger.info('switch ip')


def get_result(url):  # 从美观的html中提取所需的信息

    post_info = dict()  # 存放帖子相关信息
    reply_info = dict()  # 存放回复相关信息
    html = get_content(url, my_headers)
    soup = get_page_info(html)
    total_page = soup.find('span', {"class": "fs"}).attrs['title'].strip()[1:3]

    # 得到所发布帖子主题，点击量，回复量
    top_div = soup.find('div', {"class": "consnav"})  # 帖子顶部div
    topic_prespan = top_div.find('span', {"class": "gt"})
    topic_span = topic_prespan.next_sibling.next_sibling
    number = top_div.findAll('font')
    post_info['topic'] = topic_span.string
    post_info['click_number'] = number[0].string
    post_info['reply_number'] = number[1].string

    # 得到所发布帖子的内容

    content_divs = soup.find('div', {"class": "w740"})
    post_div = content_divs.find('div', {"class": "tz-paragraph"})
    post_content = ''
    if post_div is not None:
        for child in post_div.children:
            if child.string is not None:
                post_content += child.string
        post_info['content'] = post_content
    else:
        post_info['content'] = ''
    # 得到本帖和所有回复的发表时间

    new_url = url
    all_person = []  # 存所有人的信息
    all_time = []  # 存所有发表的时间
    all_floor = []  # 存所有人的楼层
    all_content = []  # 存所有人的话
    index = 0
    for i in range(int(total_page)):
        new_url = url.replace('-1', '-' + str(i + 1))
        html = get_content(new_url, my_headers)
        soup = get_page_info(html)
        contents = soup.findAll('div', {"class": "w740"})
        for content in contents[1:]:
            temp = ''
            reply_cont = content.find('div', {"class": 'yy_reply_cont'})
            if reply_cont is not None:
                for child in reply_cont.children:
                    if child.string is not None:
                        temp += child.string.strip()
            else:
                for child in content.children:
                    if child.string is not None:
                        temp += child.string.strip()
            temp = temp.replace('\n', '')
            temp = temp.replace('\r', '')
            all_content.append(temp)
        floors = soup.findAll('button', {"class": "rightbutlz"})
        for floor in floors:
            all_floor.append(floor.string)
        time_span = soup.findAll('span', {"xname": "date"})
        if time_span is not None:
            for t in time_span:
                all_time.append(t.string)

        # 得到楼主及回复人的相关信息
        person_info_divs = soup.findAll('div', {"class": "conleft fl"})

        for person in person_info_divs:
            name = person.a.string.strip()
            ul = person.find('ul', {"class": "leftlist"})
            level_icons = ul.findAll('div', {"class": "imgcon"})
            level = '普通用户' if len(level_icons) == 0 else '解题答人'
            lis = ul.findAll('li')
            jinhua = '0帖' if lis[2].a is None else lis[2].a.string
            tiezi_a = lis[3].findAll('a')
            tiezi = tiezi_a[0].string + '|' + tiezi_a[1].string
            registe_time = lis[4].string.strip()[3:]
            address = lis[5].a.string
            person_info = {"name": name, "name_link": ul.a.attrs['href'],
                           'floor': all_floor[index], 'jinhua': jinhua, 'tiezi': tiezi,
                           'registe_time': registe_time, 'address': address, 'level': level}
            all_person.append(person_info)
            index += 1
    post_info['time'] = all_time[0] if len(all_time) > 0 else 0
    post_info['poster_info'] = all_person[0]
    reply_info = []
    for i in range(1, len(all_floor)):
        ti = all_time[i]
        content = all_content[i] if len(all_content) > i else ''
        reply = {'time': ti, 'content': content, 'replyer_info': all_person[i]}
        reply_info.append(reply)
    result = {'post_info': post_info, 'reply_info': reply_info}

    return result


def write_json(page, result, car_type):
    dir_path = os.path.join(os.getcwd(), 'content', car_type)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    path = os.path.join(dir_path, '%d.json' % page)
    with open(path, 'w', encoding='utf-8') as fw:
        json.dump(result, fw)


def task_process(i, car_type_str):
    """
    一个task读一个json，写一个json，可以作为一个线程
    :return:
    """
    result = []
    logger.info('task %d is start!' % i)
    path = os.path.join(os.getcwd(), 'index', car_type_str, str(i) + '.json')
    with open(path, 'r', encoding='utf-8') as fr:
        data = json.load(fr)
    for post in tqdm(data['result']['list']):
        try:
            result.append(get_result(post['url']))
        except ValueError:
            logger.error('ValueError')
        except Exception as e:
            switch_ip()
            logger.error(post['url'])
            logger.error(str(e))
    write_json(i, result, car_type_str)
    logger.info('task %d is end!' % i)


def safe_task_process(i, car_type_str):
    try:
        task_process(i, car_type_str)
    except Exception as e:
        logger.error(str(e))


def file_list2int_list(file_list):
    int_list = list()
    for f in file_list:
        int_list.append(int(f.split('.')[0]))
    return int_list


def get_task_list(car_type_str):
    """
    index-content,做差集，得到待爬的列表
    :return:
    """
    index_path = os.path.join(os.getcwd(), 'index', car_type_str)
    content_path = os.path.join(os.getcwd(), 'content', car_type_str)
    if not os.path.exists(content_path):
        file_list = os.listdir(index_path)
    else:
        file_list = [x for x in os.listdir(index_path) if x not in os.listdir(content_path)]
    return file_list2int_list(file_list)


def multi_run():
    path = os.path.join(os.getcwd(), 'index')
    car_type_list = os.listdir(path)
    for n, c in enumerate(car_type_list):
        print('%d for %s' % (n, c))
    car_type = int(input('input car type: '))
    car_type_str = car_type_list[car_type]
    task_list = get_task_list(car_type_str)
    print('there are %d task for car type %s' % (len(task_list), car_type_str))

    num_process = int(input('num of process:'))
    pool = Pool(num_process)

    for i in task_list:
        pool.apply_async(safe_task_process, args=(i, car_type_str))
    pool.close()
    pool.join()


def run():
    begin = int(input('begin:'))
    end = int(input('end:'))
    path = os.path.join(os.getcwd(), 'index')
    car_type_list = os.listdir(path)
    for n, c in enumerate(car_type_list):
        print('%d for %s' % (n, c))
    car_type = int(input('input car type: '))
    for i in range(begin, end):
        car_type_str = car_type_list[car_type]
        task_process(i, car_type_str)


if __name__ == "__main__":
    multi_run()
    # run()
