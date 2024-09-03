import json 
from datetime import datetime
import pickle 
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS,utils
from bs4 import BeautifulSoup
from scipy.ndimage import shift
import cv2 
import matplotlib
import os 
from scipy.ndimage import shift



def get_links_data(date,instrument="hi_1"):
    r = requests.post("https://www.stereo.rl.ac.uk/cgi-bin/data.py",data={"source":"SECCHI","target" :"lz/L2/a/img/"+instrument+"/"+date})
    soup = BeautifulSoup(r.text, "html.parser")
    test_var = soup.findAll('li')
    links = []
    for t in test_var:
        link = t.find("input").get('value')
        if((instrument=="hi_1" and link[-14:] == "2th1A_br11.fts") or (instrument=="hi_2" and link[-14:] == "2th2A_br11.fts")):
            links.append(link)
    return links 

global_ral_links  = []

def multiprocessing_ral_DL(i):
    r = requests.post("https://www.stereo.rl.ac.uk/cgi-bin/data.py",data={"source":"SECCHI","target" :global_ral_links[i]})
    with open("tmp/"+global_ral_links[i].split("/")[-1], "wb") as binary_file:
        # Write bytes to file
        binary_file.write(r.content)

def rdif_list(datas,headers):
    differences = []
    headers_differences = []

    for i in range(1,len(datas)):
        time1 = datetime.strptime(headers[i-1]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')
        time2 = datetime.strptime(headers[i]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')
        if( ((time2-time1).total_seconds()/3600.0)<5.0):
            im1 = datas[i-1]
            im2 = datas[i]

            head1 = headers[i-1]
            head2 = headers[i]

            center = [head2['crpix1']-1,head2['crpix2']-1]
            wcs = WCS(head2,key='A')
            center_prev = wcs.all_world2pix(head1["crval1a"],head1["crval2a"], 0)
            shift_arr = np.array([center_prev[1]-center[1],center_prev[0]-center[0]])
            
            diff   = cv2.medianBlur(cv2.medianBlur(np.float32(im2-shift(im1,shift_arr, mode='nearest',prefilter=False)), 5),5)
            # diff = np.float32(im2-shift(im1,shift_arr, mode='nearest',prefilter=False))

           
            differences.append(diff.astype(np.float32))
            headers_differences.append(head2)

    return differences,headers_differences

def donwload_ral_links(links,folder="tmp/"):

    global global_ral_links 
    global_ral_links = links
    pool=mp.get_context('fork').Pool(processes=6)
    pool.map(multiprocessing_ral_DL, np.arange(0,len(links),1))
    pool.close()
    pool.join()



    datas, headers = [], []
    for l in links:  
        hdul_test = fits.open(folder+l.split("/")[-1])
        datas.append(hdul_test[0].data)
        headers.append(hdul_test[0].header)
        hdul_test.close()

    return datas,headers


def plot_data(dates):
    with open('ICMECAT.json') as json_file:
        ICMECAT = json.load(json_file)
    json_file.close()

    print(dates)
    data,headers = [], []
    data2,headers2 = [], []
    for d in dates:
        links1 = get_links_data(d,instrument="hi_1")
        links2 = get_links_data(d,instrument="hi_2")
        d1,h   = donwload_ral_links(links1)
        data = data + d1
        headers = headers + h


        d2,h2 = donwload_ral_links(links2)
        data2 = data2 + d2
        headers2 = headers2 +h2
    

   
    data,headers   = rdif_list(data,headers)
    data2,headers2 = rdif_list(data2,headers2)
    projected = False

    print(len(data2),len(data))

    ids = [0]
    idx = 0
    for i in range(1,len(headers)):
        time1 = datetime.strptime(headers[i]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')
        time2 = datetime.strptime(headers2[idx]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')
        if(np.abs((time1-time2).total_seconds()/60)<40):
            idx+=1
        
        if(idx>len(headers2)-1):
            print(i)
            break
        ids.append(idx)
    while(i<len(data)):
        ids.append(idx-1)
        i+=1
    print(len(ids),ids)
    
    halfrange = 1000
    [sc,header]=pickle.load(open('wind_1995_now_rtn.p', "rb" ) ) 
    ind1 = np.argmin(abs(datetime.strptime(headers[0]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')-sc.time))
    bmax = 10  #np.nanmax(sc.bt[ind1:ind1+50000])
    bmin = -10 #np.nanmin(sc.bt[ind1:ind1+50000])

    clahe2 = cv2.createCLAHE(20,(6,6))
    for i in tqdm.tqdm(range(0,len(data)-1)):
        # hi2map = Map(data2[i],headers2[i])
        # earth = get_body_heliographic_stonyhurst('earth', hi2map.date, observer=hi2map.observer_coordinate)
        
        data_hi1 = data[i]
        data_hi1 = np.nan_to_num(data_hi1,np.nanmedian(data_hi1))
        vmin = np.median(data_hi1) -  np.std(data_hi1)
        vmax = np.median(data_hi1) + 2.5* np.std(data_hi1)
        data_hi1[data_hi1>vmax] = vmax
        data_hi1[data_hi1<vmin] = vmin
        data_hi1 = (data_hi1-vmin)/(vmax-vmin)
        # data_hi1 =clahe2.apply((data_hi1*255.0).astype(np.uint8))/255.0
        

        data_hi2 = data2[ids[i]]
        data_hi2 = np.nan_to_num(data_hi2,np.nanmedian(data_hi2))
        vmin = np.median(data_hi2) - np.std(data_hi2)
        vmax = np.median(data_hi2) + 2.5* np.std(data_hi2)
        data_hi2[data_hi2>vmax] = vmax
        data_hi2[data_hi2<vmin] = vmin
        data_hi2 = (data_hi2-vmin)/(vmax-vmin)
        # data_hi2 =clahe2.apply((data_hi2*255.0).astype(np.uint8))/255.0
       

        wcoord = WCS(headers2[ids[i]])
        x = np.arange(0,1024)
        y = np.arange(0,1024)
        xx,yy = np.meshgrid(x,y)
        coord = utils.pixel_to_skycoord(xx,yy,wcoord).data
        lats2  = coord.lat.value
        longs2 = coord.lon.value 


        wcoord2 = WCS(headers[i])
        x = np.arange(0,1024)
        y = np.arange(0,1024)
        xx,yy = np.meshgrid(x,y)
        if(not projected):
            fig = plt.figure(figsize=(25,10))
            axs = fig.subplot_mosaic([['Left', 'TopRight'],['Left', 'MiddleRight'],['Left', 'BottomRight'],['Left', 'LastBottomRight']],
                          gridspec_kw={'width_ratios':[2, 1]})


            coord = wcoord2.all_pix2world(np.concatenate([xx.flatten()[:,None],yy.flatten()[:,None]],1),0)
            date =  datetime.strptime(headers[i]["DATE-END"],'%Y-%m-%dT%H:%M:%S.%f')

            pixels = wcoord.all_world2pix(coord,0) ## pixels 0 is horizontal, 1 is vertical 
            hi2map = Map(data2[ids[i]],headers2[ids[i]])
            earth = get_body_heliographic_stonyhurst('earth', hi2map.date, observer=hi2map.observer_coordinate)
            pixs_earth = utils.skycoord_to_pixel(earth,wcoord)
            
            if(date.year<2015 or date.year>=2024):## CME moves to the left so we put hi1 on the right 
                template = np.zeros((1024,int(pixels[:,0].max())+1))
                template[pixels[:,1].astype(np.int32),pixels[:,0].astype(np.int32)] = data_hi1.reshape((1024*1024))
                template[:,:1024] = data_hi2
                axs['Left'].imshow(template,cmap="gray")
                axs['Left'].scatter(pixs_earth[0].astype(np.int32),pixs_earth[1].astype(np.int32), s=80, facecolors='none', edgecolors='b')
            else:##CME moves to the right so hi1 goes left, a bit more tricky 
                template = np.zeros((1024,1024-int(pixels[:,0].min())))
                template[pixels[:,1].astype(np.int32),int(-pixels[:,0].min())+pixels[:,0].astype(np.int32)] = data_hi1.reshape((1024*1024))
                template[:,int(-pixels[:,0].min())+y.flatten()] = data_hi2
                axs['Left'].imshow(template,cmap="gray")
                axs['Left'].scatter(int(-pixels[:,0].min())+pixs_earth[0].astype(np.int32),pixs_earth[1].astype(np.int32), s=80, facecolors='none', edgecolors='b')
            
           
            
            ind = ind1+np.argmin(abs(date-sc.time[ind1:ind1+50000]))

            
           
            
            # print(pixs_earth,int(-pixels[:,0].min()))
            
            axs['Left'].title.set_text(headers[i]["DATE-END"])

            axs['TopRight'].plot(sc.time[ind-halfrange:ind+halfrange],
                                    sc.bx[ind-halfrange:ind+halfrange],
                                    label='Bx',
                                    c='red')
            axs['TopRight'].plot(sc.time[ind-halfrange:ind+halfrange],
                                    sc.by[ind-halfrange:ind+halfrange],
                                    label='By',
                                    c='green')
            
            axs['TopRight'].plot(sc.time[ind-halfrange:ind+halfrange],
                                    sc.bz[ind-halfrange:ind+halfrange],
                                    label='Bz',
                                    c='blue')
            
            axs['TopRight'].plot(sc.time[ind-halfrange:ind+halfrange],
                                    sc.bt[ind-halfrange:ind+halfrange],
                                    label='Bt',
                                    c='black')
            
            axs['TopRight'].vlines(sc.time[ind],
                                   0, 1, transform=axs['TopRight'].get_xaxis_transform(),
                                   linewidth=2,
                                   linestyles='--',
                                   
                                    colors='red')
            axs["TopRight"].set_xticklabels([])
            axs['TopRight'].set_ylabel("B(nT)")

            # axs["TopRight"].set_ylim(bmin,bmax)
            
            axs['MiddleRight'].plot(
                sc.time[ind-halfrange:ind+halfrange],
                sc.vt[ind-halfrange:ind+halfrange],
                label='vtotal',
                c='orange'
            )
            axs['MiddleRight'].vlines(sc.time[ind],
                                      0, 1, transform=axs['MiddleRight'].get_xaxis_transform(),
                                      linewidth=2,
                                      linestyles='--',
                                     
                                      colors='red')
            axs["MiddleRight"].set_xticklabels([])
            axs['MiddleRight'].set_ylabel("V(km^-1)")


            axs['BottomRight'].plot(
                sc.time[ind-halfrange:ind+halfrange],
                sc.np[ind-halfrange:ind+halfrange],
                label='density',
                c='pink'
            )
            axs['BottomRight'].vlines(sc.time[ind],
                                      0, 1, transform=axs['BottomRight'].get_xaxis_transform(),
                                      linewidth=2,
                                      linestyles='--',
                                     
                                      colors='red')
            axs["BottomRight"].set_xticklabels([])
            axs['BottomRight'].set_ylabel("N(cm^-3)")
        
            axs['LastBottomRight'].plot(
                sc.time[ind-halfrange:ind+halfrange],
                sc.tp[ind-halfrange:ind+halfrange]/1000,
                label='temperature',
                c='purple'
            )
            axs['LastBottomRight'].vlines(sc.time[ind],
                                      0, 1, transform=axs['LastBottomRight'].get_xaxis_transform(),
                                      linewidth=2,
                                      linestyles='--',
                                     
                                      colors='red')
            
            print(sc.time[ind-halfrange],sc.time[ind+halfrange])
            axs['LastBottomRight'].set_xlim(sc.time[ind-halfrange],sc.time[ind+halfrange])
            axs['LastBottomRight'].xaxis.set_major_formatter( matplotlib.dates.DateFormatter('%d-%H')) 
            axs['LastBottomRight'].xaxis.set_major_locator(plt.MaxNLocator(8))
            plt.setp(axs['LastBottomRight'].get_xticklabels(), rotation=45)
            axs['LastBottomRight'].set_xlabel("Day/Hour")
            axs['LastBottomRight'].set_ylabel("T(KK)")

            for id in ICMECAT["mo_start_time"]:
              tmp_date2 = datetime.strptime((ICMECAT["mo_start_time"][id]),'%Y-%m-%dT%H:%MZ')
            #   sc.time[ind-halfrange:ind+halfrange]
              if(tmp_date2>sc.time[ind-halfrange] and tmp_date2<sc.time[ind+halfrange] and ICMECAT["sc_insitu"][id]=="Wind"):
                    axs['TopRight'].vlines(tmp_date2,
                                   0, 1, transform=axs['TopRight'].get_xaxis_transform(),
                                   linewidth=2,
                                   linestyles='--',
                                   
                                    colors='green')



            
            plt.savefig("figs_video/"+str(i)+".png")
            plt.close("all")


        else:

            lats  = coord.lat.value
            longs = coord.lon.value 

            longs  = longs*30
            longs2 = longs2*30 
            
            lats  = lats*30
            lats2 = lats2*30 


            mini_lat = min(lats2.min(),lats.min())
            maxi_lat = max(lats2.max(),lats.max())

            mini_long = min(longs2.min(),longs.min())
            maxi_long = max(longs2.max(),longs.max())


            template = np.zeros((int(maxi_lat+10),int(maxi_long+10)))

            
            lats  = (lats - mini_lat)/(maxi_lat-mini_lat)
            lats2 = (lats2 - mini_lat)/(maxi_lat-mini_lat)

            longs  = (longs - mini_long)/(maxi_long-mini_long)
            longs2 = (longs2 - mini_long)/(maxi_long-mini_long)

            template[(lats2*(maxi_lat+9)).astype(np.uint32),(longs2*(maxi_long+9)).astype(np.uint32)] = data_hi2
            template[(lats*(maxi_lat+9)).astype(np.uint32),(longs*(maxi_long+9)).astype(np.uint32)] = data_hi1

    os.system("ffmpeg -y -framerate 30 -i figs_video/%d.png -c:v libx264 -pix_fmt yuv420p   "+dates[0]+".mp4")
    files = glob.glob('figs_video/*')
    for f in files:
        os.remove(f)
    
    files = glob.glob('tmp/*')
    for f in files:
        os.remove(f)
