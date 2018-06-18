# encoding: utf-8
import time
import markdown
import bbcode
from helper import ftime, htime, htime2, check_purequote, fixcontent_before, fixcontent_after, calc_howlongago, getportrait, noquote
def render_dispbbs(topic, simplify, posts, userinfos):
    """
    need: topic, simplify, posts, userinfos
    need modules: time, markdown, bbcode
    returns: floor2post, time2post, user2post, is_edited, is_deleted, posts, topic
    """
    
    floor2post = {}
    user2post = {}
    time2post = {}
    is_deleted = False
    is_edited = False
    
    elapsed_days = int((time.time()-ftime(topic["time"]))//(24*3600))
    if elapsed_days>30 and "水楼" not in topic["title"]:
        extra_message = "这是 {elapsed_days} 天前发表的主题，如无必要请勿回复".format(**locals())
    
    if simplify:
        i = 0
        for post in posts:
            post["purequote"] = False
            post["quotedinfo"] = []
            time2post[ftime(post["time"])] = post["floor"]
            floor2post[post["floor"]] = i
            u = post["userName"] if topic["boardId"]!=182 else "匿名"
            if u not in user2post:
                user2post[u] = [(i, ftime(post["time"]))]
            else:
                user2post[u].append((i, ftime(post["time"])))
            i += 1
    
    for post in posts:

        if post["content"] is None:
            is_deleted = True
            post["content"] = "===此回复已经被删==="

        if simplify: # 精简纯引用
            c = post["content"].strip()
            is_purequote = check_purequote(c)
            is_lastfloor = post["floor"]==posts[-1]["floor"]
            if is_purequote and not is_lastfloor:
                try:
                    try:
                        quotetarget = int(post["content"].split("以下是引用")[1].split("楼")[0])
                    except:
                        username_and_time = post["content"].split("以下是引用[i]")[1].split("[/i]")[0]
                        username = "在".join(username_and_time.split("在")[:-1]).strip()
                        timestr1 = username_and_time.split("在")[-1]
                        timestr2 = timestr1.replace(" AM","")
                        timestr3 = timestr1.replace(" PM","")
                        if timestr2!=timestr1:
                            thetime = htime2(timestr2)
                        elif timestr3!=timestr1:
                            thetime = htime2(timestr3) + 43200 # stupid fix for PM, add 12h
                        else:
                            thetime = htime(timestr1)
                        for diff in [0, -1, 1]:
                            if thetime+diff in [i[1] for i in user2post[username]]:
                                quotetarget = time2post[thetime+diff]
                                break
                        else:
                            raise
                    if quotetarget!=1:
                        posts[floor2post[quotetarget]]["quotedinfo"].append([post["floor"],post["userName"]])
                        post["purequote"] = True # 如果不能提取出引用目标就放弃
                except:
                    pass
        
        if post["awards"] is not None and len(post["awards"]):
            awardcontent = ""
            for award in post["awards"]:
                awardcontent += award["content"]+" reason:"+award["reason"]+" by:"+award["operatorName"]+"\n"
            if post["contentType"]:
                post["content"] += "\n----\n#### 评分记录\n\n" + awardcontent.replace("\n","\n\n")
            else:
                post["content"] += "\n[color=red][align=right]==========\n" + awardcontent + "[/align][/color]"
                
        post["content_orignal"] = post["content"]
        post["content"] = fixcontent_before(post["content"])
        if post["contentType"]:
            content = post["content"]
            post["content"] = markdown.markdown(content,extensions=['del_ins','markdown.extensions.extra', 'urlize'])
            if post["content"].count("klzzwxh:")>0:
                post["content"] = markdown.markdown(content,extensions=['del_ins','markdown.extensions.extra'])
        else:
            post["content"] = "<div class='ubbcode'>"+bbcode.render_html(post["content"])+"</div>"
        
        post["content"] = fixcontent_after(post["content"])
        
        oldtime = ftime(post["time"])
        nowtime = int(time.time())
        post["howlongago"] = calc_howlongago(nowtime, oldtime)
        post["portrait"] = getportrait(post["userId"], userinfos)
    
    
    if simplify:
        for post in posts:
            post["quoteddetail"] = ", ".join(["{}L <b>{}</b>".format(item[0],item[1]) for item in post["quotedinfo"]])
        
    topic["participantCount"] = len(set([post["userName"] for post in posts]))
    
    is_edited = any([i["lastUpdateTime"] for i in posts])
    
    return floor2post, time2post, user2post, is_edited, is_deleted, posts, topic

def render_onmouseover(lastposts, boardid):
    result = ""
    i = len(lastposts)-1
    c = 0
    lastPostUser = ""
    while i>=0:
        if not lastposts[i]["content"]:
            i -= 1
            continue # 跳过被删除的回复
        else:
            if lastPostUser=="":
                lastPostUser = lastposts[i]["userName"] if boardid!=182 else "匿名"
        content = noquote(lastposts[i]["content"])
        if i == len(lastposts)-1 and len(content)==0:
            try:
                target = "在".join(lastposts[i]["content"].split("以下是引用")[1].split("的发言：")[0].split("在")[:-1]).replace("楼：用户","L 用户 ")+" 的发言"
                if "L" not in target:
                    content = "[i]引用[/i]"
                else:
                    targetlc = int(target.split("L")[0].strip())
                    if targetlc<from_+1:
                        content = lastposts[i]["content"]
                    else:
                        content = "[i]引用[/i]"
            except:
                #traceback.print_exc()
                i -= 1
                continue
        if len(content):
            for left, right in [("[align=right]","[/align]"), ("[right]","[/right]")]:
                if left in content and content.strip().endswith(right):
                    content = left.join(content.split(left)[0:-1])
            content = content.replace("[/size]","").replace("[/font]","").strip()
            result += "<b>["+str(lastposts[i]["floor"])+"L "+lastposts[i]["userName"]+"]</b> "
            if lastposts[i]["contentType"]==0:
                result += bbcode.render_html(content)
            else:
                mdhtml = markdown.markdown(content,extensions=['del_ins','markdown.extensions.extra', 'urlize']).strip()
                result += mdhtml.replace("<p>","").replace("</p>","").strip()
            result += "<br>"
            c += 1
        i -= 1
    return result, lastPostUser

def render_topiclist(topics, userinfos):
    result = []
    for post in topics:
        post["portrait"] = getportrait(post["userId"], userinfos)
        if post["userId"] is None:
            post["userId"] = -1
            post["userName"] = "匿名"
        oldtime = ftime(post["time"])
        nowtime = int(time.time())
        post["howlongago"] = calc_howlongago(nowtime, oldtime)
        post["howlongago2"] = calc_howlongago(nowtime, ftime(post["lastPostTime"]))
        result.append(post)
    return result