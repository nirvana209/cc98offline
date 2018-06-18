# encoding: utf-8
import time, datetime
ftime = lambda i:int(time.mktime(time.strptime(i.split(".")[0].split("+")[0],"%Y-%m-%dT%H:%M:%S")))
gtime = lambda i:datetime.datetime.fromtimestamp(int(i)).strftime("%Y-%m-%d %H:%M:%S")
htime = lambda i:int(time.mktime(time.strptime(i,"%Y/%m/%d %H:%M:%S")))
htime2 = lambda i:int(time.mktime(time.strptime(i,"%m/%d/%Y %H:%M:%S")))

def check_purequote(c):
    c = c.strip()
    return c.startswith("[quote") and (c.endswith("[/quote]") or c.endswith("[/quotex]"))

def fixcontent_before(content):
    content = content.replace("\n[align=right][size=3][color=gray]——来自微信小程序「[b][color=black]CC98[/color][/b]」[/color][/size][/align]","")
    return content

def fixcontent_after(html):
    result = html.replace("&amp;#", "&#")
    return result

def calc_howlongago(nowtime, oldtime, ago=True):
    if ago:
        agotext = "前"
        rightnowtext = "刚刚"
    else:
        agotext = "后"
        rightnowtext = "即将"
    timediff = nowtime - oldtime
    if timediff < 0:
        return rightnowtext
    years, rest = divmod(timediff,365*24*3600)
    months, rest = divmod(rest,30*24*3600)
    days, rest = divmod(rest,24*3600)
    hours, rest = divmod(rest,3600)
    minutes, seconds = divmod(rest, 60)
    if years > 0:
        return "{years} 年 {months} 月".format(**locals())+agotext
    elif months>0:
        return "{months} 月 {days} 天".format(**locals())+agotext
    elif days>0:
        return "{days} 天 {hours} 小时".format(**locals())+agotext
    elif hours>0:
        return "{hours} 小时 {minutes} 分".format(**locals())+agotext
    elif minutes>0 :
        return "{minutes} 分前".format(**locals())
    else:
        return rightnowtext

def portrait_nocc98(url):
    return url.replace("http://www.cc98.org/","/").replace("https://www.cc98.org/","/")


def getportrait(userid, userinfos):
    default = "/static/pic/block.png"
    try:
        return portrait_nocc98(userinfos[userid]["portraitUrl"])
    except:
        return default

def memberlink(userid):
    if userid is None or userid < 0:
        return ""
    else:
        return ' href="/user/id/{userid}" '.format(**locals())

def noquote(content):
    content = content.strip()
    if content.startswith("[quote"):
        return content.split("[/quote]")[-1].split("[/quotex]")[-1].strip()
    else:
        return content
