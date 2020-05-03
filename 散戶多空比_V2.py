#!/usr/bin/env python
# coding: utf-8

# In[99]:


import requests
import pandas as pd
from io import StringIO
import time
import re
import datetime

#取得當天日期並轉換
today=datetime.date.today()

#將- 取代為/ 讓查詢日期格式正確
queryDate=str(today).replace("-","/")
#print(queryDate)

#測試用日期
#queryDate="2020/04/27"
#today -= datetime.timedelta(days=1)
#print(today)
print(queryDate)

data = {}
n_days = 30
fail_count = 0
allow_continuous_fail_count = 5

# In[100]:


def postfuncNew(url,Postpayload):
    session = requests.Session()
    paramsPost = Postpayload
    headers = {"Origin":"https://www.taifex.com.tw","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8","Upgrade-Insecure-Requests":"1","User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:72.0) Gecko/20100101 Firefox/72.0","Connection":"close","Referer":"https://www.taifex.com.tw/cht/3/futContractsDate","Accept-Language":"zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3","Accept-Encoding":"gzip, deflate","Content-Type":"application/x-www-form-urlencoded"}
    cookies = {"BIGipServerPOOL_WWW_TCP_80":"471208108.20480.0000","c":"8c936b59dc569b26b816019ca2cb19f01709a701350","BIGipServerPOOL_iRule_WWW_Group":"404099244.20480.0000","ROUTEID":".tomcat3","_gat":"1","_ga":"GA1.3.2004033134.1582683667","JSESSIONID":"B80A16FA099F41D49840B4C1B5937B5C.tomcat3","BIGipServerPOOL_iRule_WWW_ts50search":"420876460.20480.0000","_gid":"GA1.3.285759117.1583137315"}
    response = session.post(url, data=paramsPost, headers=headers, cookies=cookies)
    #print("Status code:   %i" % response.status_code)
    #print("Response body: %s" % response.content)
    response.encoding = 'UTF-8'
    dfs = pd.read_html(StringIO(response.text), encoding='UTF-8')
    return dfs


# In[101]:


def getfunc(url,Getpayload):
    session = requests.Session()
    paramsGet = Getpayload
    headers = {"Accept":"application/json, text/javascript, */*; q=0.01","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0","Connection":"close","Referer":"https://www.taifex.com.tw/cht/3/futDailyMarketReport","Accept-Language":"zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3","Accept-Encoding":"gzip, deflate, br"}
    cookies = {"BIGipServerPOOL_WWW_TCP_80":"471208108.20480.0000","BIGipServerPOOL_iRule_WWW_Group":"437653676.20480.0000","ROUTEID":".tomcat2","_ga":"GA1.3.208110716.1584094066","JSESSIONID":"5DAB171C35C3BEF93CCE237A03A1FDF8.tomcat2","BIGipServerPOOL_iRule_WWW_ts50search":"420876460.20480.0000"}
    response = session.get(url, params=paramsGet, headers=headers, cookies=cookies)
    response.encoding = 'UTF-8'
    #print("Status code:   %i" % response.status_code)
    #print("Response body: %s" % response.content)
    return response.text


# In[110]:


#查詢為交易日
def isTraddingDay(date):
    geturl="https://www.taifex.com.tw/cht/3/getFutTradingSessionList.do"
    paramsGet = {"queryDate":date}
    isTradday=getfunc(geturl,paramsGet)
    if "COMMODITY_MARKET_CODE" in isTradday:
        trading=1
        print("Trading day,continue plz!!")
    else:
        trading=0
        #print("No data today!!")
    return trading


while len(data) < n_days:
    queryDate=str(today).replace("-","/")
    print("parsing",queryDate)
    if isTraddingDay(queryDate):

        #查詢期貨每日交易行情查詢->小台
        posturl="https://www.taifex.com.tw/cht/3/futDailyMarketReport"
        PayloadPost = {"commodity_id":"MTX","queryDate":queryDate,"dateaddcnt":"","commodity_idt":"MTX","marketCode":"0","commodity_id2":"","commodity_id2t2":"","MarketCode":"0","queryType":"2","commodity_id2t":""}

        df=postfuncNew(posturl,PayloadPost)[2].drop([0,1,2])
        #df=dfs[2].drop([0,1,2])
        dff=df.iloc[:10,1:13]


        # In[104]:


        #	交易資訊 > 三大法人 > 查詢 > 區分各期貨契約 > 依日期
        #三大法人小台指期多空單
        posturl1="https://www.taifex.com.tw/cht/3/futContractsDate"
        PayloadPost1 = {"queryDate":queryDate,"dateaddcnt":"","doQuery":"1","goDay":"","commodityId":"MXF","queryType":"1"}

        df2=postfuncNew(posturl1,PayloadPost1)[2].drop([0,1])


        # In[105]:


        """
        散戶多單=全市場未平倉量-三大法人多單
        散戶空單=全市場未平倉量-三大法人空單
        散戶多空比=(散戶多單-散戶空單)/全市場未平倉*100%
        """

        totalpointer=3 #刪掉3列所以從第3列開始起算，找到小計所在的列數，決定當天的所有期貨"到期月份" 總數

        while True:
            #print(dff[7][totalpointer])
            totalpointer=totalpointer+1
            if dff[7][totalpointer] =="小計:" : break
        '''             
        print("小台指期當日未沖銷契約量=",int(dff[12][totalpointer]))
        print("未到期留倉量=",(int(dff[12][totalpointer])-int(dff[12][4])))
        print("==================")
        print("自營多單=",int(df2[9][5]))
        print("投信多單=",int(df2[9][6]))
        print("外資多單=",int(df2[9][7]))
        print("==================")
        print("自營空單=",int(df2[11][5]))
        print("投信空單=",int(df2[11][6]))
        print("外資空單=",int(df2[11][7]))
        print("==================")
        '''
        #print(dff[12][totalpointer])
        indiviualPlayer_long=int(dff[12][totalpointer])-int(dff[12][4])-(int(df2[9][5])+int(df2[9][6])+int(df2[9][7]))
        indiviualPlayer_short=int(dff[12][totalpointer])-int(dff[12][4])-(int(df2[11][5])+int(df2[11][6])+int(df2[11][7]))
        indiviualPlayer_ratio=(100*(indiviualPlayer_long-indiviualPlayer_short)/(int(dff[12][totalpointer])-int(dff[12][4])))
        '''
        print("散戶多單=",indiviualPlayer_long)
        print("散戶空單=",indiviualPlayer_short)
        print(queryDate+"散戶多空比="+'%.2f%%' %indiviualPlayer_ratio)
        '''

        # In[106]:


        #首頁 > 交易資訊 > 大額交易人未沖銷部位結構 > 查詢 > 期貨大額交易人未沖銷部位結構表
        posturl3="https://www.taifex.com.tw/cht/3/largeTraderFutQry"
        PayloadPost3 = {"contractId":"all","datecount":"","queryDate":queryDate,"contractId2":"all"}

        df3=postfuncNew(posturl3,PayloadPost3)[3].drop([0])


        # In[107]:


        #大戶指標
        """大戶指標 大戶多空比 ＝（多方十大交易人佔比 － 空方十大交易人佔比）－ 多空分界點"""
        #print(df3.columns)
        biglong=re.split('[()%]',df3[(       '買方', '前十大交易人合計 (特定法人合計)',       '百分比')][2])
        #biglong=re.split('[()%] ',df3[2][7])
        bigsell=re.split('[()%]',df3[(       '賣方', '前十大交易人合計 (特定法人合計)',       '百分比')][2])
        #bigsell=re.split('[()%] ',df3[8][7])
        major_trader_ratio=(float(biglong[0])-float(bigsell[0]))
        #print(queryDate+"大戶多空比="+'%.2f%%' %major_trader_ratio)


        # In[108]:


        #查詢外資期貨多單
        posturl4 = "https://www.taifex.com.tw/cht/3/futContractsDate"
        PayloadPost4 = {"queryDate":queryDate,"dateaddcnt":"","doQuery":"1","goDay":"","commodityId":"TXF","queryType":"1"}

        df4 = postfuncNew(posturl4,PayloadPost4)[3].drop([0])
        #print(df4.columns)
        foreign_investment_long = df4[ (             '未平倉餘額',               '多空淨額',   '口數')][5]

        #print(queryDate+"大台外資多單=",foreign_investment_long)


        # In[109]:

        print("==========================================================")
        print(queryDate+"小台散戶多單=",indiviualPlayer_long)
        print(queryDate+"小台散戶空單=",indiviualPlayer_short)
        print(queryDate+"小台散戶多空比="+'%.2f%%' %indiviualPlayer_ratio)
        print(queryDate+"大台外資多單=",foreign_investment_long)
        print(queryDate+"大戶多空比="+'%.2f%%' %major_trader_ratio)
        print("==========================================================")
    else:
        print("not trading day")


    today -= datetime.timedelta(days=1)
    time.sleep(10)




