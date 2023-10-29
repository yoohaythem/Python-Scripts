# 赛区标签：LPL-0(二进制0)；LCK-1(二进制1)；NRG-2(二进制10)，方便后续比较同赛区，用字符串效率较低
# NRG 和 WBG 二进制第三位赋值 1（+4），方便后续比较

import random

loop = 10 ** 6  # 模拟100万次
# 初始化WBG_NRG相遇的次数，没有内战的次数
WBG_NRG_times = 0
NO_same_times = 0
ALL_happen = 0


# 模拟第一轮抽签
def main():
    global WBG_NRG_times, NO_same_times, ALL_happen
    # ----------------------第一轮开始----------------------

    # 3-0池子
    dict_3to0 = {"JDG": 0, "GENG": 1}
    # 3-2池子
    dict_3to2 = {"BLG": 0, "KT": 1, "WBG": 0 + 4}
    # 3-1池子
    dict_3to1 = {"LNG": 0, "NRG": 2 + 4, "T1": 1}
    # 比赛结果池子，0代表内战，1代表外战
    result = {0: [], 1: []}

    for _ in range(2):
        # 随机选择dict_3to0中的一支队伍
        _3to0 = random.choice(list(dict_3to0.keys()))
        # 随机选择dict_3to2中的一支队伍
        _3to2 = random.choice(list(dict_3to2.keys()))
        # 如果是外战的队伍放入result[1]，内战的队伍放入result[0]
        result[1 if ((dict_3to0[_3to0] & 3) - (dict_3to2[_3to2] & 3)) else 0].append({_3to0, _3to2})

        # 从字典中移除选择的队伍
        dict_3to0.pop(_3to0)
        dict_3to2.pop(_3to2)

    # 两轮抽签结束，合并3-2池子和3-1池子，返回
    dict_3to1.update(dict_3to2)

    # ----------------------第二轮开始----------------------

    temp = 0  # 存放 WBG_NRG 标志位
    for _ in range(2):
        # 随机选择dict_3to1中的两支队伍
        _3to1 = random.sample(list(dict_3to1.keys()), 2)
        # 如果是外战的队伍放入result[1]，内战的队伍放入result[0]
        result[1 if ((dict_3to1[_3to1[0]] & 3) - (dict_3to1[_3to1[1]] & 3)) else 0].append({_3to1[0], _3to1[1]})
        # 如果是 NRG 和 WBG，计数
        if dict_3to1[_3to1[0]] >> 2 == dict_3to1[_3to1[1]] >> 2 == 1:
            WBG_NRG_times += 1
            temp = 1
        # 从字典中移除选择的队伍
        dict_3to1.pop(_3to1[0])
        dict_3to1.pop(_3to1[1])

    # 如果全部外战，计数
    if len(result[1]) == 4:
        NO_same_times += 1
        if temp:
            ALL_happen += 1


if __name__ == '__main__':
    for i in range(loop):
        main()
    print(f"全部内战概率为: {NO_same_times / loop * 100:.2f}% \nWBG打NRG概率为: {WBG_NRG_times / loop * 100:.2f}% \n"
          f"二者全部发生概率为: {ALL_happen / loop * 100:.2f}%")


'''
全部内战概率为: 22.21% 
WBG打NRG概率为: 11.11% 
二者全部发生概率为: 5.54%
'''