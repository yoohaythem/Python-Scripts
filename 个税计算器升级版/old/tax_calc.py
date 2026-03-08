from scipy.optimize import minimize
import numpy as np


# 一次性奖金额
def one_time_tax_rate(奖金账户):
    if 奖金账户 <= 0:
        return 0
    elif 奖金账户 <= 3000 * 12:
        value = 0.03 * 奖金账户
    elif 奖金账户 <= 12000 * 12:
        value = 0.1 * 奖金账户 - 210
    elif 奖金账户 <= 25000 * 12:
        value = 0.2 * 奖金账户 - 1410
    elif 奖金账户 <= 35000 * 12:
        value = 0.25 * 奖金账户 - 2660
    elif 奖金账户 <= 55000 * 12:
        value = 0.3 * 奖金账户 - 4410
    elif 奖金账户 <= 80000 * 12:
        value = 0.35 * 奖金账户 - 7160
    else:
        value = 0.45 * 奖金账户 - 15160
    return value


# 按月扣税
def salary_tax_rate(月薪, 月公积金, 月社保, 月退税额, 年额外增加):
    base = 月薪 * 12 + 年额外增加 - 60000 - (月公积金 + 月社保 + 月退税额) * 12
    if base <= 0:
        return 0
    elif base <= 3000 * 12:
        value = 0.03 * base
    elif base <= 12000 * 12:
        value = 0.1 * base - 2520
    elif base <= 25000 * 12:
        value = 0.2 * base - 16920
    elif base <= 35000 * 12:
        value = 0.25 * base - 31920
    elif base <= 55000 * 12:
        value = 0.3 * base - 52920
    elif base <= 80000 * 12:
        value = 0.35 * base - 85920
    else:
        value = 0.45 * base - 181920
    return value


# 主函数
def main(年奖金账户, 月薪, 月公积金, 月社保, 月退税额):
    # 定义目标函数（两个函数的和）
    def objective_function(x):
        return one_time_tax_rate(奖金账户=x) + salary_tax_rate(月薪=月薪, 月公积金=月公积金, 月社保=月社保, 月退税额=月退税额, 年额外增加=年奖金账户 - x)

    # 指定 x 的范围
    x_range = (0, 年奖金账户)

    # 初始值
    result = minimize(objective_function, 年奖金账户, bounds=[x_range])

    # 初始猜测值
    for initial_guess in range(0, 年奖金账户, 500):
        temp = minimize(objective_function, np.array([initial_guess]), bounds=[x_range])
        # print(initial_guess, temp.fun)
        if temp.fun < result.fun:
            result = temp

    print(f"一次性提取数额为:{result.x[0]:.2f}时，年纳税额最小为：{result.fun:.2f}")
    return result


if __name__ == '__main__':
    main(年奖金账户=200000, 月薪=50000, 月公积金=15000, 月社保=18000, 月退税额=6000)
