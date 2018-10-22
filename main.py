# encoding: utf-8
import sys
#reload(sys)  # Reload does the trick!
#sys.setdefaultencoding('UTF8')
import time
import datetime
from flask import Flask, render_template, Blueprint, request, redirect, Markup, g, session, abort, Response, jsonify
import msgpack
import random
import bbcode
import pickle
import gzip
import mdx_urlize
import markdown
import requests
import os
import traceback
import mimetypes
import string
import re
import hashlib
import functools
from requests.structures import CaseInsensitiveDict
_bytes = bytes
try:
    from urllib.parse import urlparse
except:
    from urllib2 import urlparse
    def bytes(i, encoding="utf-8"):
        return i
import base64
from flask.sessions import session_json_serializer
from itsdangerous import base64_decode
from helper import ftime, gtime, htime, htime2, check_purequote, fixcontent_before, fixcontent_after, calc_howlongago, getportrait, portrait_nocc98, memberlink, noquote
from render import render_dispbbs, render_onmouseover, render_topiclist
from data import aboutmd, HTTPS_LIST, boardInfo

DATA = pickle.loads(gzip.open("test.status","rb").read())
assert DATA["version"]>=20181023, "data file version mismatch"
DATA["topic"] = {}
for topic in DATA["topics"]+DATA["hot"]:
    DATA["topic"][topic["id"]] = topic

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def file_modifytime_hash(filepath):
    """
    输入文件路径，输出修改时间戳的hash
    用于修改css和js后自动刷新url
    """
    result = hashlib.md5(bytes(str(int(os.stat(os.path.join(APP_ROOT,filepath)).st_mtime)), encoding="utf-8")).hexdigest()
    return result

JSHASH = file_modifytime_hash("static/all.js")
CSSHASH = file_modifytime_hash("static/all.css")

str = str
len = len
int = int


BBSNAME = "CC98"


app = Flask(__name__)

@app.before_request
def before_request():
    g.starttime = time.time()
    g.redis_read = 0
    g.redis_write = 0
    g.apifetch = 0
    if request.cookies.get("rvpnstatus","unknown")=="true": # request.remote_addr.startswith("10.190") and
        g.rvpn = True
    else:
        g.rvpn = False
    if request.referrer is not None and request.path in request.referrer:
        g.refresh = True
    else:
        g.refresh = False

@app.after_request
def after_request(response):
    try:
        starttime = g.starttime
    except:
        return response
    diff = time.time() - starttime
    if response.response and hasattr(response.response, "__getitem__") and isinstance(response.response[0], _bytes):
        infostring = "ExecTime: %d ms"%(int(diff*1000))
        if os.name == "posix": #Linux
            infostring += ", System Load: %.2f" % (os.getloadavg()[0])
        response.response[0] = response.response[0].replace(b'__EXECUTION_INFO__', infostring.encode('utf-8'))
        response.response[0] = html_final_replace_b(response.response[0])
        response.headers["content-length"] = len(response.response[0])
    return response

@app.errorhandler(404)
def page_not_found(e):
    targs = globals()
    targs.update(locals())
    return render_template('404.html', **targs), 404

def html_final_replace_b(inputbytes):
    for domain in HTTPS_LIST:
        inputbytes = inputbytes.replace(b'http://'+bytes(domain, "utf-8"), b'//'+bytes(domain, "utf-8"))
    inputbytes = inputbytes.replace(b'<a href="http://www.cc98.org/',b'<a href="/')\
                           .replace(b'<a href="https://www.cc98.org/',b'<a href="/')\
                           .replace(b'<a href="http://www.cc98.tech/',b'<a href="/')\
                           .replace(b"//file.cc98.org/", b"//zjucdn.b0.upaiyun.com/file.cc98.org/")
    return inputbytes

def html_final_replace(html):
    return html_final_replace_b(bytes(html, "utf-8")).decode()

@app.route("/")
@app.route("/index.asp")
def hello():
    return redirect("/recent")

def get_topic_url(topicid, floor, src=False, end=False):
    if src:
        srcstring = "&src=reply"
    else:
        srcstring = ""
    floor = int(floor)
    if end:
        page = 666666
        reply_position = "end"
    else:
        page = (floor+9)//10
        reply_position = floor%10
        if reply_position==0:
            reply_position = 10
    return "/dispbbs.asp?id={topicid}&star={page}{srcstring}#{reply_position}".format(**locals())


def limit_param(param_name, default_value, minvalue, maxvalue):
    try:
        data = int(request.args.get(param_name, default_value))
    except:
        data = default_value
    if data<minvalue:
        data = minvalue
    elif data > maxvalue:
        data = maxvalue
    return data

def userinfo_one_fix(userid):
    try:
        result = DATA["userinfos"][userid]
        result["portraitUrl"] = portrait_nocc98(result["portraitUrl"])
        return result
    except:
        return {"portraitUrl":"/static/pic/block.png"}

def handletopics_userinfo(topics):
    userids = set([int(post["userId"]) for post in topics if post["userId"] is not None and post["userId"]>0])
    userinfos = {userid: userinfo_one_fix(userid) for userid in userids}
    userinfos[-1] = {"portraitUrl":"/static/pic/anonymous.gif?v"}
    return userids, userinfos

def handletopics(topics, ishot=False, filterboards=None):
    if filterboards is None:
        filterboards = []
    if ishot:
        for post in topics:
            topicdata = api.topic(str(post["id"])) # TODO: fix this
            post.update(topicdata)
    userids, userinfos = handletopics_userinfo(topics)
    tmp = []
    for post in topics:
        if getboardname(post["boardId"]) in filterboards:
            continue
        tmp.append(post)
    result = render_topiclist(tmp, userinfos)
    return result, userids, userinfos


@app.route("/recent")
@app.route("/newTopics")
def recent():
    extra_message = ""
    title = u"查看新帖"
    title_name = u"最近的主题"
    page_max = 1
    page = 1
    topics = copy.deepcopy(DATA["topics"])
    topics.sort(key=lambda item:item["lastPostTime"], reverse=True)
    topics, userids, userinfos = handletopics(topics)
    targs = globals()
    targs.update(locals())
    return render_template("topiclist.html", **targs)

def getboardname(boardid, _abort=True, _raise=False):
    global boardInfo
    boardid = int(boardid)
    try:
        boardname = boardInfo[boardid]
    except:
        boardname = "未知板块"
    return boardname

"""
@app.route("/list/<int:boardid>")
@app.route("/go/<int:boardid>")
def boardlist(boardid):
    title = title_name = getboardname(boardid)
    extra_message = ""
    topic_count = api.board(boardid)["topicCount"]
    page_size = 20
    page_max = (topic_count+page_size-1)//page_size
    page = limit_param("p", 1, 1, page_max)
    if g.refresh or page!=1:
        topics = api_wo.board_topic(boardid, from_=(page-1)*20, size=20)
    else:
        topics = api.board_topic(boardid, from_=(page-1)*20, size=20)
    topics, userids, userinfos = handletopics(topics)
    targs = globals()
    targs.update(locals())
    return render_template("topiclist.html", **targs)
"""
import copy
def dispbbs_real(id, page=None, src=None, orignal_star=None, _useapiwo = True):
    """
    _useapiwo 为了防止无限递归 
    如果发现当前redis得到的回复数量不够(与topic不一致) 那就发起api请求 即使失败也不应该继续递归
    """
    extra_message = ""
    if request.args.get('simplify', '1')=='0':
        simplify = False
    else:
        simplify = True
    if page is None:
        page = 1
    if src is None:
        src = ""
    if orignal_star is None:
        orignal_star = 1
    try:
        id = int(id)
        topic = DATA["topic"][id]
    except:
        abort(404)
    boardid = topic["boardId"]
    boardname = getboardname(boardid, _abort=False)
    page_count = (topic["replyCount"]+100)//100
    if page > page_count:
        page = page_count

    title = topic["title"]

    posts = copy.deepcopy(DATA["posts"][id])

    if page!=1:
        posts.insert(0, DATA["posts"][id][0])
    
    if posts[0]["title"] is None:
        posts[0]["title"] = topic["title"] #fix if posts[0] deleted
    
    if boardid!=182:
        userinfos = DATA["userinfos"]
    else:
        userinfos = {None: {"portraitUrl":"/static/pic/anonymous.gif"}}
    
    floor2post, time2post, user2post, is_edited, is_deleted, posts, topic = render_dispbbs(topic, simplify, posts, userinfos)
    targs = globals()
    targs.update(locals())
    return render_template("dispbbs.html", **targs)

@app.route("/topic/<id>")
@app.route("/topic/<id>/")
def dispbbs_topic_id(id):
    return dispbbs_real(id)

@app.route("/topic/<id>/<int:star>")
def dispbbs_topic_idpage(id, star):
    if star<1:
        star = 1
    page = (star+9)//10
    return dispbbs_real(id, page, orignal_star=star)

@app.route("/dispbbs.asp")
def dispbbs():
    request.args = CaseInsensitiveDict(request.args)
    id = request.args.get('id',request.args.get('id;',''))
    star = int(request.args.get('star',request.args.get('star;',1)))
    if star<1:
        star = 1
    page = (star+9)//10
    src = request.args.get('src',"")
    return dispbbs_real(id, page, src, orignal_star=star)

def topic_onmouseover_real(id):
    id = int(id)
    topic = DATA["topic"][id]
    boardid = topic["boardId"]
    from_ = topic["replyCount"]//20*20
    lastposts = DATA["posts"][id]
    result, lastPostUser = render_onmouseover(lastposts, boardid)
    return {"html":html_final_replace(result).replace("\t","    "), "replycount": topic["replyCount"], "lastPostUser": lastPostUser, "topic_lastPostUser": topic["lastPostUser"]}

@app.route("/topic/<id>/onmouseover")
def topic_onmouseover(id):
    return jsonify(topic_onmouseover_real(id))

@app.route("/topic/<id>/onmouseover.html")
def topic_onmouseoverhtml(id):
    return topic_onmouseover_real(id)["html"]

@app.route("/about")
def about():
    title = "About"
    abouthtml = markdown.markdown(aboutmd)
    targs = globals()
    targs.update(locals())
    return render_template("about.html", **targs)

@app.route("/hot")
def hot():
    title = "热门话题"
    topics = copy.deepcopy(DATA["hot"])
    topics,userids,userinfos = handletopics(topics)
    targs = globals()
    targs.update(locals())
    return render_template("hot.html", **targs)

if __name__=="__main__":
    app.run('0.0.0.0',port=6000, debug=True)