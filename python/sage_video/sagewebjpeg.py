#!/usr/bin/python
import json
import subprocess
import argparse
import os.path
import sys

INSTALL_DIR = '/etc/sage_video'
YURIXML = 'webserver_jpeg.xml'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sage video streamer to webcam')
    parser.add_argument('--config', '-c', help='configuration file',
                        dest='cfg_file', default=os.path.join(INSTALL_DIR, 'config.json'))
    parser.add_argument('--quality', '-1', help='jpeg quality',
                        dest='quality', default=75, type=int)
    parser.add_argument('video_file', help='video file or decklink format')

    args = parser.parse_args()

    print ('Loading config from %s' % args.cfg_file)

    if not os.path.exists(args.cfg_file):
        print('Config file \'%s\' doesn\'t exist!' % args.cfg_file)
        sys.exit(1)

    if not os.path.exists(args.video_file):
        print('Video file \'%s\' doesn\'t exist!' % args.video_file)
        sys.exit(1)

    cfg = json.load(open(args.cfg_file, 'rt'))


    cmdline = ['yuri2', 
                os.path.join(cfg['server']['dir'], YURIXML),
                'filename=%s'%(args.video_file),
                'q=%d'%(args.quality)]
                
    cmdline = [c.encode('utf-8') for c in cmdline]
        
    dev_null = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(
        os.devnull, 'wb')
    # subprocess.check_call(cmdline, stderr=dev_null)
    subprocess.check_call(cmdline)