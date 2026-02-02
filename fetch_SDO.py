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
from natsort import natsorted
import glob
import matplotlib.pyplot as plt 
import sunpy.visualization.colormaps as cm
import matplotlib 
import sunpy
import sunpy.map
import astropy.units as u


global_urls1 = None
global_start = 0
temp_path = "/lscratch/aswo/ops/sdo/"
# temp_path = "./tmp/"

def multi_processes_dl(i):
    # img = Image.open(requests.get(global_urls1[i], stream=True).raw)
    # img.save(temp_path+str(global_start+i)+".fts")
    f = temp_path+global_urls1[i].split("/")[-1]
    wget.download(global_urls1[i],out = f)

    aiamap = sunpy.map.Map(f)
    fig = plt.figure(frameon=False)
    ax = plt.axes([0, 0, 1, 1])
    # Disable the axis
    ax.set_axis_off()
    
    norm = aiamap.plot_settings['norm']
    norm.vmin, norm.vmax = np.percentile(aiamap.data, [5, 99.9])
    ax.imshow(aiamap.data,
            norm=norm,
            cmap=aiamap.plot_settings['cmap'],
            origin="lower")
    plt.text(10, 24, aiamap.fits_header["DATE-OBS"], dict(size=7,color="white"))
    plt.savefig(temp_path+str(global_start+i)+".png")
    # plt.show()
    plt.close("all")
    os.system("rm "+f)

def get_last_x_days_SDO(duration=7,path_to_save="/perm/aswo/ops/corona/"):
    now  = datetime.now() - datetii.timedelta(days=duration)
    origin_now = now
    img_list = []
    cnt = 0
    for i in range(0,duration):
        next_date = str(now.year)+"/"+str('%02d' % now.month)+"/"+str('%02d' % now.day)
        # https://sdo.oma.be/data/aia_quicklook/0193/2026/01/20/
        url_next = "https://sdo.oma.be/data/aia_quicklook/0193/"+next_date+"/"
        soup = BeautifulSoup(requests.get(url_next).text, 'html.parser').find_all('a')
        urls = []
        for s in soup:
            lnk = s.get('href')
            if(lnk.endswith(".fits")):
                urls.append(url_next+lnk)

        now = now + datetii.timedelta(days=1)
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
        cnt =  + len(urls)

    # files = natsorted(glob.glob(temp_path+"/*.fits"))
    # for f in files:
    #     print(f)
        


        
        
           
        


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
