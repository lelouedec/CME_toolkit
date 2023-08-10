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

    urls,times = get_urls_from_date("https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/"+cme[0].split("_")[0]+"/c3/" + date +"/",datetime_object)
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
            url_next = "https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/"+cme[0].split("_")[0]+"/c3/" +  next_day_date  +"/"
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



def get_last_x_days(duration=7,path_to_save="/perm/aswo/ops/corona/",temp_path="/export/home/aswo/jlelouedec/CME_toolkit/temp_imgs/"):
    now  = datetime.now()
    origin_now = now
    img_list = []
    for i in range(0,duration):
        next_date = str(now.year)+str('%02d' % now.month)+str('%02d' % now.day)
        url_next = "https://soho.nascom.nasa.gov/data/REPROCESSING/Completed/"+str(datetime.today().year)+"/c3/" +  next_date  +"/"
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

    for i,im in enumerate(img_list):
        im.save(temp_path+str(i)+".png")


    #save the videos and gifs with only the day's date
    os.system("ffmpeg -y -framerate 30 -i "+temp_path+"%d.png -c:v libx264 -pix_fmt yuv420p "+path_to_save+"lasco_c3_current.mp4")
    # os.system("ffmpeg -y -framerate 15 -r 16 -i  "+temp_path+"%d.png -vf scale=512:-1 "+path_to_save+"lasco_c3_current.gif")
    os.system('ffmpeg -y -i '+path_to_save+'lasco_c3_current.mp4 -filter_complex "fps=9,scale=300:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=20[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'lasco_c3_current_lowres.gif')
    os.system('ffmpeg -y -i '+path_to_save+'lasco_c3_current.mp4 -filter_complex "fps=9,scale=400:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=60[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'lasco_c3_current_midres.gif')
    os.system('ffmpeg -y -i '+path_to_save+'lasco_c3_current.mp4 -filter_complex "fps=9,scale=512:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=100[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'lasco_c3_current_highres.gif')


    #save the videos with only the day and time
    os.system("cp "+path_to_save+"lasco_c3_current.mp4  " +path_to_save+"lasco_c3_"+str(datetime.today()).split(".")[0].replace(" ","_")+".mp4")


    os.system("rm -rf "+temp_path+"*")



if(len(sys.argv)>1):
    argument = sys.argv[1]
    if(argument=="scoreboard"):
        create_gif_from_scoreboard()
    elif(argument=="lastd"):
        get_last_x_days(7)
    else:
        print("UNRECOGNIZED ARGUMENT")
else:
    print("NO ARGUMENT PASSED, PLEASE PASS scoreboard or lastd values")