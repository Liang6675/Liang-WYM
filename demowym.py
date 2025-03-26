import requests
import re
import os
import csv

# 创建文件夹
Floderwym = 'YUNCUN\\'
if not os.path.exists(Floderwym):
    os.mkdir(Floderwym)

# 创建歌曲列表文件夹
songs_list_folder = 'YUNCUN\\歌曲列表\\'
if not os.path.exists(songs_list_folder):
    os.mkdir(songs_list_folder)

# 网页链接
url = 'https://music.163.com/discover/toplist?id=3778678'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
}

# 发送请求获取歌曲信息
response = requests.get(url=url, headers=headers)
y_return = re.findall('<li><a href="/song\?id=(\d+)">(.*?)</a></li>', response.text)

# 保存歌曲信息到CSV文件
csv_file = songs_list_folder + 'songs.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['ID', 'Name'])
    for music, topicyum in y_return:
        writer.writerow([music, topicyum])

# 下载歌曲并保存歌词
for music, topicyum in y_return:
    # 创建歌曲文件夹
    song_folder = os.path.join(Floderwym, topicyum)
    if not os.path.exists(song_folder):
        os.mkdir(song_folder)

    # 获取歌曲URL
    music_url = f'http://music.163.com/song/media/outer/url?id={music}.mp3'
    music_content = requests.get(url=music_url, headers=headers).content

    # 保存歌曲
    with open(os.path.join(song_folder, topicyum + '.mp3'), mode='wb') as f:
        f.write(music_content)
        print(f"下载歌曲: {topicyum}")

    # 获取歌词
    lyrics_url = f'https://music.163.com/api/song/lyric?id={music}&lv=1&kv=1&tv=-1'
    lyrics_response = requests.get(url=lyrics_url, headers=headers)
    lyrics_data = lyrics_response.json()

    if 'lrc' in lyrics_data and 'lyric' in lyrics_data['lrc']:
        lyrics = lyrics_data['lrc']['lyric']
        # 保存歌词
        with open(os.path.join(song_folder, topicyum + '.txt'), mode='w', encoding='utf-8') as f:
            f.write(lyrics)
            print(f"保存歌词: {topicyum}")
    else:
        print(f"未能获取到歌词: {topicyum}")
