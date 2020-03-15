import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
fig = plt.figure()
ax = fig.add_subplot(111, projection = '3d')
x = y = z = [1, 2, 3]
sc = ax.scatter(x,y,z)

#####################
x2, y2, _ = proj3d.proj_transform(1, 1, 1, ax.get_proj())
print(x2, y2)   # project 3d data space to 2d data space
print(ax.transData.transform((x2, y2)))  # convert 2d space to screen space
#####################
def on_motion(e):
    # move your mouse to (1,1,1), and e.xdata, e.ydata will be the same as x2, y2
    print(e.x, e.y, e.xdata, e.ydata)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
plt.show()