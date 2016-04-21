#!/usr/bin/python3
'''
Created on 21. 4. 2016

@author: neneko
'''
import subprocess
import os
import sagevideo
import sys
import json

CFG_FILE='sync_client.xml'
SERVER_CFG_FILE='sync_server.xml'

def usage():
    print('Usage play_original.py FILENAME [cfg]')


if __name__ =='__main__':
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    
    filename = sys.argv[1]
    
    cfgfile=sys.argv[2] if len(sys.argv) > 3 else 'config.json'
    cfg = json.load(open(cfgfile,'rt'))
    
    #stripes_x, stripes_y, total_x, total_y = [int(x) for x in sys.argv[3:7]]
    
    cfg['video']=sagevideo.get_video_info(filename)
    cfg=sagevideo.compute(cfg)
    
    stripes_x = cfg['stripes_x']
    stripes_y = cfg['stripes_y']
    total_x = cfg['total_x']
    total_y = cfg['total_y']
    offset_x=cfg['offset_x']
    offset_y=cfg['offset_y']
    stripe_x=cfg['stripe_x']
    stripe_y=cfg['stripe_y']
    virtual_width=cfg['virtual_width']
    virtual_height=cfg['virtual_height']
    W=cfg['W']
    H=cfg['H']
    part_width=cfg['part_width']
    part_height=cfg['part_height']
    
    instances=[]
    for tile_id in cfg['tiles']:
        tile=cfg['tiles'][tile_id]
        x=tile['x']
        y=tile['y']
        w=tile['w']
        h=tile['h']
        dx=tile['dx']
        dy=tile['dy']
        
        if not tile_id in cfg['renderers']:
            print('Unspecified tile %s'%tile_id)
            continue
        
        renderer=cfg['renderers'][tile_id]
        
        cmdline=['ssh','-t',
                 renderer['address'],'/usr/bin/yuri2',
                 os.path.join(renderer['dir'],CFG_FILE),
                 'resolution=%dx%d'%(part_width,part_height),
                 'file='+filename,
                 'crop=%dx%d+%d+%d'%(w, h, dx, dy),
                 'pad=%dx%d'%(stripe_x, stripe_y),
                 'halign=%s'%('left' if x == 0 else 'right')]
        
        print (str(cmdline))
        instances.append(subprocess.Popen(cmdline))
        
    sdir = cfg['server']['dir']        
    cmdline=['/usr/bin/yuri2',os.path.join(sdir,SERVER_CFG_FILE),'file='+filename,'webdir='+os.path.join(sdir,'webcontroller')]
    print('Server cmdline: %s'%str(cmdline))
    subprocess.call(cmdline)
        
    for i in instances:
        i.send_signal(subprocess.signal.SIGINT)
        try:
            i.wait(5)
        except:
            i.kill()
            
    del instances
        
            