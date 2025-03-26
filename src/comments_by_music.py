"""
根据歌曲 ID 获得所有的歌曲所对应的热门评论和歌词
"""
import datetime
import json
import math
import random
import time
from concurrent.futures.process import ProcessPoolExecutor

import requests

from src import sql, redis_util
from src.util.user_agents import agents


class Comment(object):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': '_ntes_nnid=7eced19b27ffae35dad3f8f2bf5885cd,1476521011210; _ntes_nuid=7eced19b27ffae35dad3f8f2bf5885cd; usertrack=c+5+hlgB7TgnsAmACnXtAg==; Province=025; City=025; _ga=GA1.2.1405085820.1476521280; NTES_PASSPORT=6n9ihXhbWKPi8yAqG.i2kETSCRa.ug06Txh8EMrrRsliVQXFV_orx5HffqhQjuGHkNQrLOIRLLotGohL9s10wcYSPiQfI2wiPacKlJ3nYAXgM; P_INFO=hourui93@163.com|1476523293|1|study|11&12|jis&1476511733&mail163#jis&320100#10#0#0|151889&0|g37_client_check&mailsettings&mail163&study&blog|hourui93@163.com; JSESSIONID-WYYY=189f31767098c3bd9d03d9b968c065daf43cbd4c1596732e4dcb471beafe2bf0605b85e969f92600064a977e0b64a24f0af7894ca898b696bd58ad5f39c8fce821ec2f81f826ea967215de4d10469e9bd672e75d25f116a9d309d360582a79620b250625859bc039161c78ab125a1e9bf5d291f6d4e4da30574ccd6bbab70b710e3f358f%3A1476594130342; _iuqxldmzr_=25; __utma=94650624.1038096298.1476521011.1476588849.1476592408.6; __utmb=94650624.11.10.1476592408; __utmc=94650624; __utmz=94650624.1476521011.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
        'DNT': '1',
        'Host': 'music.163.com',
        'Pragma': 'no-cache',
        'Referer': 'http://music.163.com/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
    }

    def saveComment(self, music_id):
        params = {'limit': 1000, 'offset': 0}
        # 获取歌手个人主页
        agent = random.choice(agents)
        self.headers["User-Agent"] = agent
        url = 'http://music.163.com/api/v1/resource/comments/R_SO_4_' + str(music_id)
        # 去redis验证是否爬取过
        check = redis_util.checkIfRequest(redis_util.commentPrefix, str(music_id))
        if (check):
            print("url:", url, "has request. pass")
            return
        r = requests.get(url, headers=self.headers, params=params)
        # 结果解析
        commentsJson = json.loads(r.text)
        # 保存redis去重缓存
        if (commentsJson['code'] == 200):
            redis_util.saveUrl(redis_util.commentPrefix, str(music_id))
        else:
            print(url, " request error :", commentsJson)
            return
        # 热评
        for item in commentsJson['hotComments']:
            self.dbsave(item, music_id)

        # 普通评论
        for item in commentsJson['comments']:
            self.dbsave(item, music_id)
        # 请求完成后睡一秒 防作弊
        time.sleep(1)

    # 保存数据库
    def dbsave(self, item, music_id):
        user = item['user']
        # 用户id
        userId = user['userId']
        nickname = user['nickname']
        # 用户头像
        userImg = user['avatarUrl']
        # 评论内容
        content = item['content']
        # 点赞数
        likedCount = item['likedCount']
        # 时间
        remarkTime = item['time']
        # 评论id
        commentId = item['commentId']
        try:
            # 持久化
            sql.insert_comment(commentId, music_id, content, likedCount, remarkTime, userId, nickname, userImg)
        except Exception as e:
            # 打印错误日志
            print(str(item), ' insert error : ', str(e))
            time.sleep(1)


def saveCommentBatch(index):
    my_comment = Comment()
    offset = 1000 * index
    musics = sql.get_music_page(offset, 1000)
    print("index:", index, "offset:", offset, "artists :", len(musics), "start :", musics[0]['music_id'])
    for item in musics:
        try:
            my_comment.saveComment(item['music_id'])
        except Exception as e:
            # 打印错误日志
            print(' internal  error : ' + str(e))
            # traceback.print_exc()
            time.sleep(2)
    print("index:", index, "finished")


def commentSpider():
    print("======= 开始爬 评论 信息 ===========")
    startTime = datetime.datetime.now()
    print(startTime.strftime('%Y-%m-%d %H:%M:%S'))
    # 所有歌手数量
    musics_num = sql.get_all_music_num()
    # 批次
    batch = math.ceil(musics_num.get('num') / 1000.0)
    # 构建线程池
    # pool = ProcessPoolExecutor(1)
    for index in range(0, batch):
        saveCommentBatch(index)
        # pool.submit(saveCommentBatch, index)
    # pool.shutdown(wait=True)
    print("======= 结束爬 评论 信息 ===========")
    endTime = datetime.datetime.now()
    print(endTime.strftime('%Y-%m-%d %H:%M:%S'))
    print("耗时：", (endTime - startTime).seconds, "秒")

# if __name__ == '__main__':
#     commentSpider()
