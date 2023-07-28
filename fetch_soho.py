from bs4 import BeautifulSoup
import requests
import datetime as datetii
from datetime import datetime
import numpy as np 
from PIL import Image
import sys
import os

def get_urls_from_date(url,time_origin):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser').find_all('tr')[3:-1]
    urls = []
    times = []
    for s in soup:
        lnk = url+s.find_all("a")[0].get('href')
        if(lnk.endswith("_1024.jpg")):
            urls.append(lnk)
            times.append((time_origin-datetime.strptime(s.find_all("a")[0].get('href').split("_")[0]+" "+s.find_all("a")[0].get('href').split("_")[1], '%Y%m%d %H%M')).seconds)
    return urls, times


def get_cme_images(cme,nb_frames =204):
    date = "".join(cme[0].split("-"))
    time = "".join(cme[1].split(":")[:-1])
    datetime_object = datetime.strptime(cme[0]+" "+cme[1], '%Y-%m-%d %H:%M:%S')

    urls,times = get_urls_from_date("https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/2023/c3/" + date +"/",datetime_object)
    cme_idx  = np.array(times).argmin()
    img_list = []
    for id in range(cme_idx,len(urls)):
        img_list.append(Image.open(requests.get(urls[id], stream=True).raw))

    #if we dont have enough frame, lets get the one from next day
    not_reached_end = True
    if(len(img_list)<nb_frames):
        while(len(img_list)<nb_frames and not_reached_end):
            next_day_date = (datetime_object +datetii.timedelta(days=1)).date()
            datetime_object = datetime_object +datetii.timedelta(days=1)
            next_day_date = str(next_day_date.year)+str('%02d' % next_day_date.month)+str('%02d' % next_day_date.day)
            url_next = "https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/2023/c3/" +  next_day_date  +"/"
            print(url_next)
            response = requests.get(url_next)
            ##Check if there is a next day of data to fetch from
            if(response.status_code==200):
                urls,times = get_urls_from_date(url_next,datetime_object)
                for id in range(0,len(urls)):
                    img_list.append(Image.open(requests.get(urls[id], stream=True).raw))
                    if(len(img_list)>nb_frames):
                        break                            
            else:
                not_reached_end =False

    for i,im in enumerate(img_list):
        im.save("./temp_imgs/"+str(i)+".png")
    os.system("ffmpeg -framerate 30 -i temp_imgs/%d.png -c:v libx264 -pix_fmt yuv420p "+date+".mp4")
    os.system("rm -rf temp_imgs/*")
    # img_list[0].save(
    #         'animation.gif',
    #         save_all=True,
    #         append_images=img_list[1:], # append rest of the images
    #         duration=10, # in milliseconds
    #         loop=0)


def get_cme_dates_from_scoreboard():
    reqs = requests.get("https://kauai.ccmc.gsfc.nasa.gov/CMEscoreboard/")
    soup = BeautifulSoup(reqs.text, 'html.parser')
    cmes = []
    for tabl in soup.find_all('table'):
        date = tabl.find_all("b")
        if(len(date)>0):
            dt_t = date[0].text[5:].split("T")
            dt = dt_t[0]
            t  = dt_t[1].split("-")[0]
            cmes.append((dt,t))
    return cmes



def create_gif_from_scoreboard():
    cmes =  get_cme_dates_from_scoreboard()
    for cme in cmes:
        get_cme_images(cme,102)



def get_last_x_days(duration=7):
    now  = datetime.now()
    origin_now = now
    img_list = []
    for i in range(0,duration):
        next_date = str(now.year)+str('%02d' % now.month)+str('%02d' % now.day)
        url_next = "https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/2023/c3/" +  next_date  +"/"
        print(url_next)
        response = requests.get(url_next)
        ##Check if there is a next day of data to fetch from
        if(response.status_code==200):
            urls,times = get_urls_from_date(url_next,now)
        now = now - datetii.timedelta(days=1)
        list_im = []
        for id in range(0,len(urls)):
            list_im.append(Image.open(requests.get(urls[id], stream=True).raw))
        img_list = list_im + img_list
    # print(len(img_list))
    # img_list[0].save(
    #     'last_2_days.gif',
    #     save_all=True,
    #     append_images=img_list[1:], # append rest of the images
    #     duration=3, # in milliseconds
    #     loop=0)
    for i,im in enumerate(img_list):
        im.save("/export/home/aswo/jlelouedec/CME_toolkit/temp_imgs/"+str(i)+".png")
    os.system("ffmpeg -framerate 30 -i /export/home/aswo/jlelouedec/CME_toolkit/temp_imgs/%d.png -c:v libx264 -pix_fmt yuv420p /perm/aswo/ops/corona/"+str(origin_now.date())+".mp4")
    os.system('ffmpeg -framerate 20 -i /export/home/aswo/jlelouedec/CME_toolkit/temp_imgs/%d.png -vf scale=512:-1 /perm/aswo/ops/corona/'+str(origin_now.date())+'.gif')
    os.system("rm -rf /export/home/aswo/jlelouedec/CME_toolkit/temp_imgs/*")

if(len(sys.argv)>1):
    argument = sys.argv[1]
    if(argument=="scoreboard"):
        create_gif_from_scoreboard()
    elif(argument=="lastd"):
        get_last_x_days(2)
    else:
        print("UNRECOGNIZED ARGUMENT")
else:
    print("NO ARGUMENT PASSED, PLEASE PASS scoreboard or lastd values")