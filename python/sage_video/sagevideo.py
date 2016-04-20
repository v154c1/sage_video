'''
Created on 20. 4. 2016

@author: neneko
'''
import json
import subprocess

def get_video_info(filename):
    video_data = json.loads(subprocess.check_output(['ffprobe','-of','json','-show_streams','-select_streams','v',filename],stderr=subprocess.PIPE).decode('utf8'))
    return video_data

def compute(cfg):
    stripes_x = cfg['stripes_x']
    stripes_y = cfg['stripes_y']
    total_x = cfg['total_x']
    total_y = cfg['total_y']
    
    part_width = total_x/stripes_x
    part_height = total_y/stripes_y

    print('Preparing videos for %dx%d displays, %dx%d each'%(stripes_x, stripes_y, part_width, part_height))

    video_data = cfg['video']

    W = video_data["streams"][0]['coded_width']
    H = video_data["streams"][0]['coded_height']

    # find upscaled resolution
    if (total_x / W) < (total_y / H):
        display_width=total_x
        display_height=H * total_x / W
        virtual_width = W
        virtual_height = W * total_y / total_x
    else:
        display_width=W * total_y / H
        display_height=total_y
        virtual_width = H  * total_x / total_y
        virtual_height = H
    
    offset_x = (virtual_width - W) / 2
    offset_y = (virtual_height - H) / 2
    
    stripe_x=virtual_width/stripes_x
    stripe_y=virtual_height/stripes_y
    
    print('Displayed resolution will be %dx%d'%(display_width, display_height))
    print('Virtual resolution will be %dx%d, offset %dx%d'%(virtual_width, virtual_height, offset_x, offset_y))
    print('Stripes will have resolution %dx%d'%(stripe_x, stripe_y))
    
    
    vdx=-offset_x
    dx=0
    
    cfg['tiles']={}
    for part_x in range(0, stripes_x):
        w = min(vdx + stripe_x, W - dx)
        vdx = min(vdx+stripe_x,0)
        
        if w <= 0:
            print('ignoring column %d'%(part_x))
        
        vdy=-offset_y
        dy=0
        for part_y in range(0, stripes_y):
            h = min(vdy + stripe_y, H - dy)
            vdy = min(vdy+stripe_y,0)
            if h <= 0:
                print('ignoring row %d'%(part_y))
            print('Crop (%d,%d): %dx%d+%d+%d'%(part_x, part_y, w, h, dx, dy))
            x=stripe_x - w if dx == 0 else 0
            y=stripe_y - h if dy == 0 else 0
            
            cfg['tiles']['%d_%d'%(part_x, part_y)]={
                'w':w,
                'h':h,
                'dx':dx,
                'dy':dy,
                'x':x,
                'y':y
            }
            
            dy = dy + h
        dx = dx + w
    
    cfg['offset_x']=offset_x
    cfg['offset_y']=offset_y
    cfg['stripe_x']=stripe_x
    cfg['stripe_y']=stripe_y
    cfg['virtual_width']=virtual_width
    cfg['virtual_height']=virtual_height
    cfg['W']=W
    cfg['H']=H
    cfg['part_width']=part_width
    cfg['part_height']=part_height
    return cfg
