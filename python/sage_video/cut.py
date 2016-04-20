#!/usr/bin/python3
import sys
import json
import subprocess
import os
import sagevideo
def usage():
	print('Usage cut_video.py FILENAME OUTFILENAME [cfg]')






if __name__ =='__main__':
	if len(sys.argv) < 3:
		usage()
		sys.exit(1)
	
	filename = sys.argv[1]
	outfilename = sys.argv[2]
	cfgfile=sys.argv[3] if len(sys.argv) > 3 else 'config.json'
	cfg = json.load(open(cfgfile,'rt'))
	
	#stripes_x, stripes_y, total_x, total_y = [int(x) for x in sys.argv[3:7]]
	
	cfg['video']=sagevideo.get_video_info(filename)
	cfg=sagevideo.compute(cfg)
	
# 	stripes_x = cfg['stripes_x']
# 	stripes_y = cfg['stripes_y']
# 	total_x = cfg['total_x']
# 	total_y = cfg['total_y']
# 	offset_x=cfg['offset_x']
# 	offset_y=cfg['offset_y']
	stripe_x=cfg['stripe_x']
	stripe_y=cfg['stripe_y']
# 	virtual_width=cfg['virtual_width']
# 	virtual_height=cfg['virtual_height']
# 	W=cfg['W']
# 	H=cfg['H']
    
	for tile_id in cfg['tiles']:
		tile=cfg['tiles'][tile_id]
		x=tile['x']
		y=tile['y']
		w=tile['w']
		h=tile['h']
		dx=tile['dx']
		dy=tile['dy']
		
		print('Crop (%s): %dx%d+%d+%d'%(tile_id, w, h, dx, dy))

		filter = 'crop=%d:%d:%d:%d [v0];[v0] pad=%d:%d:%d:%d:black'%(w, h, dx, dy, stripe_x, stripe_y, x, y)
		ofn = '%s_%s.mp4'%(outfilename,tile_id)
		if os.path.exists(ofn):
			print('File %s already exists'%(ofn))
		else:
			cmdline=['ffmpeg','-i',filename,'-filter:v',filter,'-an','-c:v','libx264','-preset','slower',ofn]
			print('cmdlineL %s'%str(cmdline))
			subprocess.call(cmdline)#,stderr=subprocess.PIPE)
		

