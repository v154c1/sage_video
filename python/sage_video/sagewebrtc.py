#!/usr/bin/python
import json
import subprocess
import argparse
import os.path
import sys
import time
import re
from string import Template

def get_video_info(filename):
    video_data = json.loads(subprocess.check_output(
        ['ffprobe', '-of', 'json', '-show_streams', '-select_streams', 'v', filename], stderr=subprocess.PIPE).decode('utf8'))
    return video_data

def vcctrl(cmds):
    dev_null = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(
        os.devnull, 'wb')
    cmdline = [ 'vcctrl' ] + cmds
    return subprocess.check_output(cmdline, stderr=dev_null).decode('utf-8').splitlines()

def vcctrl_check_list(out):
    if 'Failed to open' in out[0]:
        print('Failed to access webcam control. Do you have the module loaded and does the current user have rights to access it?')
        return False
    
    if not 'Virtual V4L2 devices' in out[0]:
        print('Unsupported output of vcctrl. Do you have the correct version?')
        return False
    
    return True
    
def vcctrl_get_list(out):
    devs = []
    for line in out[1:]:
        print('LINE: '+line)
        res = re.search('^(\d+)\. (vcfb\d+)\((\d+),(\d+),([a-z0-9]+)\) -> (/dev.*)$', line)
        devs.append({
            'index':res.group(1),
            'name':res.group(2),
            'width':int(res.group(3)),
            'height':int(res.group(4)),
            'format':res.group(5),
            'device':res.group(6),
            })
    return devs

def vcctrl_create_dev(node, w,h,fmt):
    out = vcctrl(node, ['-c', '-s','%dx%d'%(w,h), '-p',fmt])
    if not 'A new device will be created' in out[0]:
        print('Creating a new device probably failed')
        return None
    out = vcctrl(node, ['-l'])
    if not vcctrl_check_list(out):
        return None
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sage video streamer to webcam')

    parser.add_argument('video_file', help='video file or decklink format')

    args = parser.parse_args()
    
    cfg = {}

    cfg['video'] = get_video_info(args.video_file)

    # print(json.dumps(cfg, indent=2))

    out = vcctrl(['-l'])

    if not vcctrl_check_list(out):
        sys.exit(1)

    devs = vcctrl_get_list(out)
    if len(devs) < 1:
        print('No device found, creating new one')
    
        devs = vcctrl_create_dev( cfg['video']['width'], cfg['video']['height'], 'yuyv')
        if not devs:
            print('Failed to create a device!')
            sys.exit(1)
        dev = devs[0]
    else:
        # find usable device...
        dev = devs[0]

    cmdline = ['yuri_simple', 
                'rawavsource[filename=%s]'%(args.video_file),
                'convert[format=%s]'%(dev['format']),
                'scale[resolution=%dx%d]'%(dev['width'], dev['height']),
                'filedump[filename=/proc/%s]'%(dev['name'])]
    
    cmdline = [c.encode('utf-8') for c in cmdline]
        
    dev_null = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(
        os.devnull, 'wb')
    # subprocess.check_call(cmdline, stderr=dev_null)
    subprocess.check_call(cmdline)
