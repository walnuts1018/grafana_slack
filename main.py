#!/usr/bin/python3
import time
import datetime
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import datetime
import git
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv()
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def git_push():
    repo = git.Repo()

    #Commit(サブディレクトリ含めて全て)
    repo.git.add('.')
    repo.git.commit('.','-m','[add] Grafana images')

    #Push
    origin = repo.remote(name='origin')
    origin.push()

def capture_grafana(grafana_dict):
    print("start chrome")
    options = Options()
    options.add_argument('--hide-scrollbars')  #スクロールバーを消す
    options.add_argument('--incognito')        #シークレットモード
    options.add_argument('--headless')         #ヘッドレス
    driver = webdriver.Chrome(options=options) 

    WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
    driver.get(grafana_dict["url"])
    driver.set_window_size(grafana_dict["size"][0], grafana_dict["size"][1])
    driver.find_element(By.NAME, "user").click()
    driver.find_element(By.NAME, "user").send_keys(os.environ.get("user"))
    driver.find_element(By.ID, "current-password").send_keys(os.environ.get("password"))
    element = driver.find_element(By.CSS_SELECTOR, ".css-14g7ilz-button > .css-1mhnkuh")
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    driver.find_element(By.CSS_SELECTOR, ".css-14g7ilz-button > .css-1mhnkuh").click()
    #ファイル名用に現在時刻の取得
    now = datetime.datetime.now()
    time_jp = now.strftime('%Y%m%d_%H%M%S')
    filename = grafana_dict["name"] + "_"+ time_jp + ".png"
    #wait
    time.sleep(grafana_dict["sleep"])
    #キャプチャの取得
    driver.save_screenshot("./images/" + filename)
    driver.quit()

    #キャプチャファイルができているか最大5秒探す
    start=time.time()
    while time.time()-start<=5:
        if os.path.exists("./images/" + filename):
            return(str(filename), str(time_jp))       
        else:
            return(False)

grafana_dict={
    "long":
    {
        "url": "http://100.76.36.63:3000/d/xfpJB9FGz/1-node-exporter-for-prometheus-dashboard-en-20201010?orgId=1&kiosk",
        "name": "grafana_long",
        "size": (1920, 2300),
        "sleep": 20
    },
    "short": {
        "url": "http://100.76.36.63:3000/d/rYdddlPWsa/222?orgId=1&refresh=1m&kiosk",
        "name": "grafana_short",
        "size": (1075, 400),
        "sleep": 5
    },
    "cpu": {
        "url": "http://100.76.36.63:3000/d/xfpJB9FGz/1-node-exporter-for-prometheus-dashboard-en-20201010?orgId=1&from=now-1h&to=now&viewPanel=7",
        "name": "grafana_cpu",
        "size": (1075, 400),
        "sleep": 30
    },
    "mem": {
        "url": "http://100.76.36.63:3000/d/xfpJB9FGz/1-node-exporter-for-prometheus-dashboard-en-20201010?orgId=1&viewPanel=156&kiosk",
        "name": "grafana_mem",
        "size": (1075, 400),
        "sleep": 30
    },
    "load": {
        "url": "http://100.76.36.63:3000/d/xfpJB9FGz/1-node-exporter-for-prometheus-dashboard-en-20201010?orgId=1&viewPanel=13&from=now-1h&to=now",
        "name": "grafana_load",
        "size": (1075, 400),
        "sleep": 30
    }
    
}

@app.event("message")
def handle_message_events(message, say):
    if  (not ("attachments" in message)):
        return
    elif ("Resolved" in message["attachments"][0]["text"]):
        return
    elif ("cpu = high" in message["attachments"][0]["text"]):
        print("cpu")
        picpath = capture_grafana(grafana_dict["cpu"])
    elif "mem = high" in message["attachments"][0]["text"]:
        print("mem")
        picpath = capture_grafana(grafana_dict["mem"])
    elif "load = high" in message["attachments"][0]["text"]:
        print("load")
        picpath = capture_grafana(grafana_dict["load"])
    elif "alertname = TestAlert" in message["attachments"][0]["text"]:
        print("alert test")
        picpath = capture_grafana(grafana_dict["cpu"])
    else:
        return
    git_push()
    say({
            "attachments": [{
                "color": "#D63232",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⌚Capture Time: "+picpath[1][0:4]+"/"+picpath[1][4:6]+"/"+picpath[1][6:8]+" "+picpath[1][9:11]+":"+picpath[1][11:13]
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": picpath[0],
                            "emoji": True
                        },
                        "image_url": "https://github.com/walnuts1018/grafana_slack/raw/main/images/"+ picpath[0],
                        "alt_text": picpath[0]
                    }
                ]
            }]
        })

@app.command("/sys")
def grafana(ack, respond, command, say):
    ack()
    userInput = command['text'].split()
    #print(command)
    if (userInput[0]=="list"):
        respond("https://github.com/walnuts1018/grafana_slack/tree/main/images")
    else:
        user_name=f"👀User: <@{command['user_name']}>"
        say({
            "attachments": [{
                "color": "#7AE0FF",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "💪Generating the Grafana screen capture...\n　  Please wait... (up to 30 seconds)"
                        }
                    },
                ]
            }]
        })
        if (userInput[0]=="long"):
            picpath = capture_grafana(grafana_dict["long"])
            origin_url="Image from http://100.76.36.63:3000/d/xfpJB9FGz/1-node-exporter-for-prometheus-dashboard-en-20201010?orgId=1"
        elif(userInput[0]=="short"):
            picpath = capture_grafana(grafana_dict["short"])
            origin_url="Image from http://100.76.36.63:3000/d/rYdddlPWsa/222?orgId=1&refresh=1m"
        git_push()
        say({
            "attachments": [{
                "color": "#83DEAF",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⌚Capture Time: "+picpath[1][0:4]+"/"+picpath[1][4:6]+"/"+picpath[1][6:8]+" "+picpath[1][9:11]+":"+picpath[1][11:13]+"\n"+user_name
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": picpath[0],
                            "emoji": True
                        },
                        "image_url": "https://github.com/walnuts1018/grafana_slack/raw/main/images/"+ picpath[0],
                        "alt_text": picpath[0]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": origin_url
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "📷 List available images with `/sys list`\n📊 View simple graph with `/sys short`\n📊 View detailed graph with `/sys long`"
                            }
                        ]
                    },
                ]
            }]
        })

    

SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
