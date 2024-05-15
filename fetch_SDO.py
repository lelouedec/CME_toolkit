from bs4 import BeautifulSoup
import requests
import datetime as datetii
from datetime import datetime
import numpy as np 
from PIL import Image
import sys
import os
import wget
import multiprocessing as mp


global_urls1 = None
global_start = 0
temp_path = "/lscratch/aswo/ops/sdo/"

def multi_processes_dl(i):
    img = Image.open(requests.get(global_urls1[i], stream=True).raw)
    img.save(temp_path+str(global_start+i)+".png")

def get_last_x_days_SDO(duration=7,path_to_save="/perm/aswo/ops/corona/"):
    now  = datetime.now()
    origin_now = now
    img_list = []
    cnt = 0
    for i in range(0,duration):
        next_date = str(now.year)+"/"+str('%02d' % now.month)+"/"+str('%02d' % now.day)

        url_next = "https://sdo.oma.be/data/aia_quicklook_image/"+next_date+"/"
        soup = BeautifulSoup(requests.get(url_next).text, 'html.parser').find_all('tr')[3:-1]
        urls = []
        for s in soup:
            time_H = s.find_all("a")[0].get('href')
            urls_next_hours = url_next + time_H
            
            soup = BeautifulSoup(requests.get(urls_next_hours).text, 'html.parser').find_all('tr')[3:-1]
            
            for s in soup:
                lnk = urls_next_hours+s.find_all("a")[0].get('href')
                if(lnk.endswith("0193.quicklook.png")):
                    print(lnk)
                    urls.append(lnk)
        now = now - datetii.timedelta(days=1)
        list_im = []
        print(len(urls))
        
        global global_urls1 
        global_urls1 = urls

        global global_start 
        global_start = cnt

        pool= mp.get_context('fork').Pool(processes=12)
        pool.map(multi_processes_dl, np.arange(0,len(urls),1))
        pool.close()
        pool.join()
        
        
           
        cnt = cnt + len(urls)


    #save the videos and gifs with only the day's date
    os.system("ffmpeg -y -framerate 30 -i "+temp_path+"%d.png -c:v libx264 -pix_fmt yuv420p "+path_to_save+"SDO_193_current.mp4")
    # os.system("ffmpeg -y -framerate 15 -r 16 -i  "+temp_path+"%d.png -vf scale=512:-1 "+path_to_save+"SDO_193_current.gif")
    os.system('ffmpeg -y -i '+path_to_save+'SDO_193_current.mp4 -filter_complex "fps=9,scale=300:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=20[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'SDO_193_current_lowres.gif')
    os.system('ffmpeg -y -i '+path_to_save+'SDO_193_current.mp4 -filter_complex "fps=9,scale=350:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=35[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'SDO_193_current_midres.gif')
    os.system('ffmpeg -y -i '+path_to_save+'SDO_193_current.mp4 -filter_complex "fps=9,scale=512:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=100[p];[s1][p]paletteuse=dither=bayer" '+path_to_save+'SDO_193_current_highres.gif')


    #save the videos with only the day and time
    os.system("cp "+path_to_save+"SDO_193_current.mp4  " +path_to_save+"SDO_193_"+datetime.today().date().strftime('%y-%m-%d')+".mp4")
    os.system("rm -rf "+temp_path+"*")




get_last_x_days_SDO(7)
