'''
中国证券投资基金业协会网站基金爬虫
https://gs.amac.org.cn/amac-infodisc/res/pof/fund/index.html
爬虫结果写入txt文本或Mysql数据库持久保存
'''

import math
import random
import pymysql
import requests
import json
from bs4 import BeautifulSoup


# 获取单个基金详细数据
def find_one(suburl):
    sub_response = requests.get(suburl)
    soup = BeautifulSoup(sub_response.content, 'html.parser')
    table = soup.select('div.table-response')[1]
    data = []
    for row in table.find_all('tr'):
        row_data = []
        for cell in row.find_all('td'):
            row_data.append(cell.text.strip())
        data.append(row_data)
    return data


# 从文件中读取公司名称
def read_from_txt(txt_name):
    with open(txt_name, 'r', encoding='UTF-8-sig') as file:
        all = file.read(-1)
    return all.split('\n')


# 把内存列表写入txt文件
def write_to_txt(data):
    with open('result.txt', 'a', encoding='UTF-8-sig') as file:
        for item in data:
            file.write(item[0] + item[1] + " | ")
        file.write("\n")


# 把内存列表写入sql数据库
def write_to_sql(data):
    # 根据数据库实际情况填写
    db = pymysql.connect(host="localhost", user="root", password="123456", port=5518, charset='utf8')
    cur = db.cursor()
    cur.execute("create database if not exists fund character set utf8")
    cur.execute("use fund")
    sql = """
      CREATE TABLE  if not exists t_fund
    (
    `基金名称` VARCHAR(255) PRIMARY KEY NOT NULL,
    `基金编号` VARCHAR(255),
    `成立时间` VARCHAR(255),
    `备案时间` VARCHAR(255),
    `基金备案阶段` VARCHAR(255),
    `基金类型` VARCHAR(255),
    `注册地` VARCHAR(255),
    `币种` VARCHAR(255),
    `基金管理人名称` VARCHAR(255),
    `管理类型` VARCHAR(255),
    `托管人名称` VARCHAR(255),
    `运作状态` VARCHAR(255),
    `基金信息最后更新时间` VARCHAR(255)
    )character set = utf8 
    """
    cur.execute(sql)
    field = ",".join("`" + item[0].split(":")[0] + "`" for item in data)
    value = ",".join("'" + item[1].split(":")[0] + "'" for item in data)
    cur.execute(f'replace into t_fund({field}) VALUES ({value});')
    db.commit()
    cur.close()
    db.close()


# 清除txt文件
def clear_txt():
    with open('result.txt', 'w', encoding='UTF-8-sig') as file:
        file.write("")


# 根据企业名称数据，将查询结果写入txt或sql
def find_by_list(list, all_num, size, type="txt"):
    if type == "txt":
        clear_txt()
    for name in list:
        headers = {"Content-Type": "application/json"}
        for page in range(math.ceil(all_num / size)):
            url = f"https://gs.amac.org.cn/amac-infodisc/api/pof/fund?rand={random.random()}&page={page}&size={size}"
            response = requests.post(url, headers=headers, data=json.dumps({"keyword": name}))
            res = response.json().get("content")
            if not res:  # 防止空跑
                break
            for i in range(len(res)):
                subid = res[i]["id"]
                suburl = f"https://gs.amac.org.cn/amac-infodisc/res/pof/fund/{subid}.html"
                sub_data = find_one(suburl)  # 获取界面数据，放在列表里
                if type == "sql":
                    write_to_sql(sub_data)  # 把内存列表写入sql数据库
                else:
                    write_to_txt(sub_data)  # 把内存列表写入txt文件
    print(f"运行结束，请检查{type}")


if __name__ == '__main__':
    all_num = 500  # 共 xxx 条记录
    size = 20  # 一页显示 xxx 条
    list = read_from_txt("私募基金管理人名称.txt")  # 读取文件数据，每一行一家企业
    find_by_list(list, all_num, size, "txt")  # 根据企业名称数据，将查询结果写入txt
