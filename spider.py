import requests
import os
import shutil
import sys
import time
import argparse
from Log import Log
from bs4 import BeautifulSoup
from io import TextIOWrapper

ROOT_URL = "http://society.people.com.cn"
MAIN_DIR = "/GB"
MAIN_FILE  = "/index.html"
ARTICAL_PATH = "./article"
PICTURE_PATH = "./picture"

## 针对bs4对国内编码方式不兼容的办法。
def http_get(url : str) -> requests.Response:
    result = requests.get(url)
    result.encoding = "gbk"
    return result

def get_page_list_from_main_url(text: str) -> list:
    result = []
    soup = BeautifulSoup(text, 'lxml')
    page_tag = soup.find(name="div", attrs={"class": "page_n clearfix"})
    page_link_list = page_tag.find_all("a")
    for page_link in page_link_list:
        try:
            href = page_link['href']
            if href not in result:
                result.append(page_link['href'])
        # 无视掉所有异常.该tag能找到的就是连接
        except Exception as e:
            # print(e)
            continue
    return result

def get_insite_url_from_main_pages(text : str) -> list:
    result = []
    bs = BeautifulSoup(text,"lxml")
    tags = bs.find_all('a')
    for i in tags:
        try:
            href = i['href']
            if href not in result    and    \
                ("/n1/" in href)     and    \
                ('http' not in href) and    \
                ("#liuyan" not in href):
                result.append(href)
        # 无视掉所有异常.该tag能找到的就是连接
        except Exception as e:
            # print(e)
            continue
    return result

# 获取文章发表时间
def get_content_pub_time(soup : BeautifulSoup) -> str:
    div = soup.find(                  \
        name="div",                   \
        attrs={"class": "channel cf"} \
    ).find(                           \
        name="div",                   \
        attrs={"class": "col-1-1 fl"} \
    )
    return div.text.replace("\n", "").replace(" ", "").replace("\t", "")

# 获取文章标题
def get_content_title(soup : BeautifulSoup) ->str:
    div = soup.find(                        \
        name="div",                         \
        attrs={"class": "layout rm_txt cf"} \
    ).find(                                 \
        name="div",                         \
        attrs={"class": "col col-1 fl"}     \
    )
    return div.find(name="h1").text

#获取文章正文内容
def get_content_text(soup : BeautifulSoup) -> str:
    result = ""
    tag_list = soup.find_all(name="p", attrs={"style": "text-indent: 2em;"})
    for i in tag_list:
        try:
            result += i.text
        except Exception as e:
            Log.e("Exception while get_content_text()")
            Log.e("exception:{}".format(e))
    return result

# 获取并储存当前页面下的所有图片
def get_content_images(soup : BeautifulSoup,fd : TextIOWrapper) -> int:
    result = 0
    img_list = soup.find_all(name = "p",attrs={"style": "text-align: center;"})
    for i in img_list:
        try:
            name = i.find(name="img")['src']
            url = ROOT_URL + name
            name = PICTURE_PATH + "/" + name.replace("/","_").replace("_NMediaFile_","").replace("_mediafile_pic_","")
            res = requests.get(url).content
            fd.write("{}\n".format(name))
            img_fd = open(name,"wb")
            img_fd.write(res)
            img_fd.close()
        except Exception as e:
            continue
    return len(img_list)

def store_data_from_url(url : str) -> None:
    file_path = ARTICAL_PATH + "/" +url.replace(ROOT_URL,"").replace("/","_").replace(".html",".txt")
    fd = open(file_path,"w",encoding="gbk")
    req = http_get(url)
    soup = BeautifulSoup(req.text.replace("&nbsp;", " "),"lxml")

    title = get_content_title(soup)
    fd.write("标题: {}\n\n\n".format(title))

    pub_time = get_content_pub_time(soup)
    fd.write("发布时间：{}\n\n".format(pub_time))

    fd.write("链接：{}\n\n".format(url))

    text = get_content_text(soup)
    fd.write("文章正文:\n\n{}\n\n".format(text))

    fd.write("图片列表:\n")
    get_content_images(soup,fd)

    fd.close()
    return None

def main():
    if not os.path.exists(ARTICAL_PATH):
        os.mkdir(ARTICAL_PATH)
    if not os.path.exists(PICTURE_PATH):
        os.mkdir(PICTURE_PATH)
    req = http_get((ROOT_URL + MAIN_DIR + MAIN_FILE))

    # 获取有多少页面
    page_list = get_page_list_from_main_url(req.text)
    page_list.append(MAIN_FILE)
    Log.succ("GET MAIN PAGES URL SUCC!")

    # 从所有分页中提取所有站内连接
    insite_list = []
    for i in page_list:
        #速度稍微慢点，怕触发反D机制
        time.sleep(0.25)
        url = ROOT_URL + MAIN_DIR + "/" + i
        req = http_get(url)
        insite_list += get_insite_url_from_main_pages(req.text)

    insite_list = list(set(insite_list))
    Log.succ("Get all insite url success!,url count:{}".format(len(insite_list)))
    Log.v("Start.Geting data stream...")
    for i in range(len(insite_list)):
        time.sleep(0.1)
        url = ROOT_URL + insite_list[i]
        Log.v("current :{},{}".format(i,url))
        req = http_get(url)
        try:
            store_data_from_url(url)
        except Exception as e:
            print(e.args)
            continue
        

def clear() -> None:
    Log.v("clearing data...")
    if os.path.exists(ARTICAL_PATH):
        shutil.rmtree(ARTICAL_PATH)
    if os.path.exists(PICTURE_PATH):
        shutil.rmtree(PICTURE_PATH)
    Log.succ("All data has been cleared.")
    return None


if __name__ == "__main__":
    if "--clear" in sys.argv:
        clear()
        exit()
    main()


