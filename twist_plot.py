import plotly.graph_objs as go
import plotly.express as px
import numpy as np 


North_to_south = True
left_handed    = False
def direction_from_pts(x1,x2):
    if(not North_to_south):
        direction = np.array([
                    x1[0]-x2[0],
                    x1[1]-x2[1],
                    x1[2]-x2[2],
        ])
    else:
        direction = np.array([
                    x2[0]-x1[0],
                    x2[1]-x1[1],
                    x2[2]-x1[2],
        ])
    direction = direction / np.linalg.norm(direction)
    return direction


resolution = 1000
turns = 10
line_thickness_red = 20.0
red_arrow_thickness = 0.6
if(not North_to_south):
    start = 0
else:
    start = 0.5*np.pi

if(not left_handed):
    if(turns%2==0):
        if((turns * 270 + 90.0)%360==90.0):
            theta  = np.linspace(start,  np.deg2rad(turns * 270 + 90.0 ), resolution)
        else:
            theta  = np.linspace(start,  np.deg2rad(turns * 270 - 90.0 ), resolution)
    else:
        theta  = np.linspace(start,  np.deg2rad(turns *360 +  90.0 ), resolution)
else:
    if(turns%2==0):
        # print("good 4: ",(4 * 270.0)//180.0,"bad 6: ",(6 * 270.0)//180.0,"good 8: ",(8 * 270.0)//180.0,"bad 10: ",(10 * 270.0)//180.0)
        if(((turns * 270.0)//180.0)%2==0):
            theta  = np.linspace(start,  np.deg2rad(turns * 270  ), resolution)
        else:
            theta  = np.linspace(start,  np.deg2rad(turns * 270 - 180 ), resolution)
    else:
        theta  = np.linspace(start,  np.deg2rad(turns *360), resolution)


Z = np.linspace(0,turns, resolution) #here
if(left_handed):
    X =  2.0*np.sin(theta)
    Y =  2.0*np.cos(theta)
else:
    X =  2.0*np.cos(theta)
    Y =  2.0*np.sin(theta)

previous = 0
added = False
for i in range(1,len(Z)):
    if(Y[i]<0 and Y[i-1]>=0):
        if(added==False):
            fig = go.Figure(data=go.Scatter3d(x=X[previous:i], 
                            y=Y[previous:i],
                            z=Z[previous:i],
                            mode='lines',
                            line=dict(color='rgba(255 ,0 ,0 ,1.0)',width=line_thickness_red)
                            )
                    )
            added = True
        else:
            fig.add_trace(go.Scatter3d(x=X[previous:i], 
                            y=Y[previous:i],
                            z=Z[previous:i],
                            mode='lines',
                            line=dict(color='rgba(255 ,0 ,0 ,1.0)',width=line_thickness_red)
                            )
            )
        previous = i
    elif(Y[i]>=0 and Y[i-1]<0):
        if(added==False):
            fig = go.Figure(data=go.Scatter3d(x=X[previous:i], 
                            y=Y[previous:i],
                            z=Z[previous:i],
                            mode='lines',
                            line=dict(color='rgba(255 ,0 ,0 ,0.6)',width=line_thickness_red,dash='dash')
                            )
                    )
        else:
            fig.add_trace(go.Scatter3d(x=X[previous:i], 
                            y=Y[previous:i],
                            z=Z[previous:i],
                            mode='lines',
                            line=dict(color='rgba(255 ,0 ,0 ,0.6)',width=line_thickness_red,dash='dash')
                            )
            )
        previous = i


if(Y[-1]>=0):
   fig.add_trace(go.Scatter3d(x=X[previous:i], 
                            y=Y[previous:i],
                            z=Z[previous:i],
                            mode='lines',
                            line=dict(color='rgba(255 ,0 ,0 ,1.0)',width=line_thickness_red)
                            )
            )       

else:
    fig.add_trace(go.Scatter3d(x=X[previous:i], 
                    y=Y[previous:i],
                    z=Z[previous:i],
                    mode='lines',
                    line=dict(color='rgba(255 ,0 ,0 ,0.6)',width=line_thickness_red,dash='dash')
                    )
    )



########FIND BETTER WAY TO PUT THE ARROWS MID WAY 
    

arrows = [10.75,19.65,28.55,37.45,46.35,55.25,64.15,73.05,81.95,90.85]

for a in arrows:
    dir0= direction_from_pts([X[int(a*(resolution/100))+1:int(a*(resolution/100))+2],Y[int(a*(resolution/100))+1:int(a*(resolution/100))+2],Z[int(a*(resolution/100))+1:int(a*(resolution/100))+2]],
                         [X[int(a*(resolution/100)):int(a*(resolution/100))+1],Y[int(a*(resolution/100)):int(a*(resolution/100))+1],Z[int(a*(resolution/100)):int(a*(resolution/100))+1]])
    fig.add_trace( go.Cone(x=X[int(a*(resolution/100)):int(a*(resolution/100))+1], 
                        y=Y[int(a*(resolution/100)):int(a*(resolution/100))+1],
                        z=Z[int(a*(resolution/100)):int(a*(resolution/100))+1], 
                        u=dir0[0], 
                        v=dir0[1], 
                        w=dir0[2],
                        sizemode="absolute",
                        sizeref=red_arrow_thickness,
                        colorscale=[[0, 'red'],[1, 'red']],
                        showscale=False))



if(not North_to_south):
    direction = direction_from_pts([X[-1],Y[-1],Z[-1]],[X[-2],Y[-2],Z[-2]])
    fig.add_trace( go.Cone(x=X[-1:], y=Y[-1:],z=Z[-1:], u=[direction[0]], v=[direction[1]], w=[direction[2]],sizemode="absolute",sizeref=red_arrow_thickness,colorscale=[[0, 'red'],[1, 'red']],showscale=False))
    fig.add_trace( go.Scatter3d(x=[0,0], 
                 y=[0,0],
                 z=[-1,turns+2],
                 mode='lines',
                 line=dict(color='black',width=15)
                )
            )
    fig.add_trace( go.Cone(x=[0], y=[0],z=[turns+2], u=[0],v=[0], w=[1],sizemode="absolute",sizeref=0.55,colorscale=[[0, 'black'],[1, 'black']],showscale=False))

else:
    direction = direction_from_pts([X[1],Y[1],Z[1]],[X[0],Y[0],Z[0]])
    fig.add_trace( go.Cone(x=[X[0]], y=[Y[0]],z=[Z[0]], u=[direction[0]], v=[direction[1]], w=[direction[2]],sizemode="absolute",sizeref=red_arrow_thickness,colorscale=[[0, 'red'],[1, 'red']],showscale=False))
    fig.add_trace( go.Scatter3d(x=[0,0], 
                 y=[0,0],
                 z=[-2,turns+2],
                 mode='lines',
                 line=dict(color='black',width=15)
                )
            )
    fig.add_trace( go.Cone(x=[0], y=[0],z=[-2], u=[0],v=[0], w=[-1],sizemode="absolute",sizeref=0.55,colorscale=[[0, 'black'],[1, 'black']],showscale=False))


# fig2 =
camera = dict(
    up=dict(x=1, y=0, z=0),
    center=dict(x=0, y=0, z=0),
    eye=dict(x=0, y=1.5, z=0)
)
fig.update_layout(scene_camera=camera, title="prout",scene = dict(  xaxis = dict(showgrid = False,showticklabels = False,backgroundcolor ="white"),
                                                                    yaxis = dict(showgrid = False,showticklabels = False,backgroundcolor ="white"),
                                                                    zaxis = dict(showgrid = False,showticklabels = False,backgroundcolor ="white")
                                                                     )
             )

fig.show() 