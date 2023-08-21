import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


'''
大麦网登录
'''
def login():
    # 设置ChromeDriver路径为你下载的匹配版本的路径
    chrome_driver_path = 'C:/Program Files/Google/Chrome/Application/chromedriver'  # 更新为实际路径
    # 创建ChromeDriver的Service对象
    chrome_service = Service(chrome_driver_path)
    # 创建Chrome浏览器选项对象
    chrome_options = Options()
    #隐藏Chrome 正受到自动测试软件的控制
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    # 设置Chrome浏览器的启动路径
    chrome_binary_path = 'C:/Program Files/Google/Chrome/Application/114.0.5734.0/chrome-win/chrome.exe'  # 更新为实际路径
    chrome_options.binary_location = chrome_binary_path
    # 在选项中添加其他设置（如果需要的话）
    # chrome_options.add_argument('--some-option')
    # 创建WebDriver并传入选项对象
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # 打开大麦网页面
    driver.get('https://www.damai.cn/')
    # 最大化浏览器窗口并置顶
    driver.maximize_window()
    # 设置最大等待时间为5秒
    wait = WebDriverWait(driver, 5)
    # 等待特定元素加载完成
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'i-logo')))
    print("ok")

    # 登录模块
    driver.find_element(By.XPATH, '//span[contains(text(), "登录")]').click()
    # 切换到指定的 iframe
    iframe_element1 = driver.find_element(By.XPATH, '//iframe[@id="alibaba-login-box"]')
    driver.switch_to.frame(iframe_element1)
    wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="fm-login-id"]'))).send_keys('13645191362')
    wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="fm-login-password"]'))).send_keys('!Cgsl@123')
    # 切回到默认上下文（主页面）
    # driver.switch_to.default_content()
    # 切换到指定的 iframe
    time.sleep(2)
    iframe_element2 = driver.find_element(By.XPATH, '//iframe[@id="baxia-dialog-content"]')
    driver.switch_to.frame(iframe_element2)
    # 等待滑块元素加载完成
    wait = WebDriverWait(driver, 5)
    slider_element = wait.until(EC.presence_of_element_located((By.XPATH, '//center//span[@class="nc_iconfont btn_slide"]')))
    # 创建 ActionChains 对象
    actions = ActionChains(driver)
    # 模拟滑动操作
    actions.click_and_hold(slider_element).move_by_offset(260, 0).release().perform()
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()

    time.sleep(10000)

    # 关闭浏览器窗口
    driver.quit()




