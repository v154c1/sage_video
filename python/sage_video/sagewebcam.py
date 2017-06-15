#!/usr/bin/python

'''
Created on 21. 3. 2017

@author: neneko
'''
import json
import subprocess
import argparse
import os.path
import sys
import time
import re
from string import Template


INSTALL_DIR = "/etc/sage_video"

# SERVER_CFG_FILE = 'unicast_stream_file_yuri.xml'
MAIN_XML_TEMPLATE = 'unicast_stream_file_yuri.template.xml'
MAIN_XML_DIRECT_TEMPLATE = 'unicast_stream_file_direct_yuri.template.xml'
MAIN_XML_DECKLINK_TEMPLATE = 'unicast_stream_decklink_yuri.template.xml'

INNER_XML_TEMPLATE = 'unicast_stream_yuri_rtp.template.xml'

DECKLINK_FORMATS={
    'pal': [720, 576],
    'palp': [720, 576],
    'ntsc': [720,486],
    'ntscp': [720,486],
    'ntsc2398': [720,486],
    
    #'720p24': [1280, 720],
#     '720p25': [1280, 720],
#     '720p30': [1280, 720],
    
    '720p50': [1280, 720],
    '720p60': [1280, 720],
    '720p5994': [1280, 720],
    
    '1080p2398': [1920, 1080],
    '1080p24': [1920, 1080],
    '1080p25': [1920, 1080],
    '1080p2997': [1920, 1080],
    '1080p30': [1920, 1080],
    '1080p50': [1920, 1080],
    '1080p5994': [1920, 1080],
    '1080p60': [1920, 1080],
    
    '1080i50': [1920, 1080],
    '1080i5994': [1920, 1080],
    '1080i60': [1920, 1080],
    
    '1080p24PsF': [1920, 1080],
    '1080p2398PsF': [1920, 1080],
    
    '2k2398': [2048, 1080],
    '2k24': [2048, 1080],
    '2k25': [2048, 1080],
    
    '4k2398': [3840, 2160],
    '4k24': [3840, 2160],
    '4k25': [3840, 2160],
    '4k2997': [3840, 2160],
    '4k30': [3840, 2160]
    }
    
                  

def get_video_info(filename):
    video_data = json.loads(subprocess.check_output(
        ['ffprobe', '-of', 'json', '-show_streams', '-select_streams', 'v', filename], stderr=subprocess.PIPE).decode('utf8'))
    return video_data

def vcctrl(node, cmds):
    dev_null = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(
        os.devnull, 'wb')
    vcctrl_path = os.path.join(node['webcam_root'], 'utils','vcctrl') if node['webcam_root'] else 'vcctrl'
    cmdline = ['ssh', '-t', node['address'], vcctrl_path] + cmds
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
        res = re.search('^(\d+)\. (vcfb\d+)\((\d+),(\d+),([a-z]+)\) -> (/dev.*)$', line)
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
    
def check_remote_webcam(node, w, h, fmt):
#     out = vcctrl(node, ['-l'])
#     
#     if not vcctrl_check_list(out):
#         return None
    
#     if len(out) < 2:
#         print('No devices, trying to create one')
#         out = vcctrl_create_dev(node, w, h, fmt)
    
    while True:
        out = vcctrl(node, ['-l'])
    
        if not vcctrl_check_list(out):
            return None
    
        devs = vcctrl_get_list(out)
        if len(devs) < 1:
            print('No devices, trying to create one')
            out = vcctrl_create_dev(node, w, h, fmt)
            if not out:
                print('Failed to create a new device')
                return None
            else:
                print('Device created')
                continue
        
        if len(devs) > 1:
            print('more than one device exists on target system. The first one will be used')
            
        dev = devs[0]
        if dev['width'] != w or dev['height'] != h:
            print('Virtual webcam exists on the remote system, but has wrong resolution (webcam is set to %dx%d, but we need %dx%d)!'%(dev['width'],dev['height'],w,h))
            print('Trying to remove device')
            try:
                out = vcctrl(node, ['-r', dev['index']])
                if 'Can\'t remove device' in out[0]:
                    print('Failed to remove device with bad resolution')
                    return None
                else:
                    print('Device removed')
                    continue
            except subprocess.CalledProcessError as e:
                print('Failed to remove device with bad resolution')
                return None
            
        
        return dev
    
    #print(out)
        

def get_node_ip(node, alt_ip):
    if alt_ip and 'alt_ip' in node:
        return node['alt_ip']
    r = re.search('[^@]@([0-9.]+)$', node['address'])
    return r.group(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sage video streamer to webcam')
    parser.add_argument('--config', '-c', help='configuration file',
                        dest='cfg_file', default=os.path.join(INSTALL_DIR, 'config.json'))
    
#     parser.add_argument('--prepare', '-p', help='Prepare the videos instead of playing',
#                         dest='prepare', action='store_true', default=False)
#     parser.add_argument('--sound', '-s', action='store_true',
#                         default=False, dest='use_sound', help='Enable sound')
#     parser.add_argument(
#         '--output', '-o', help='Output file prefix', dest='out_prefix')
#     parser.add_argument('--format', '-f', help='Specify format for display', dest='format', choices=[
#                         'original', 'rgb', 'bgr', 'yuv', 'uyvy', 'yuv444', 'yuv444p', 'yuv420p', 'yuv422p'], default='original')
    parser.add_argument('--mtu', '-m', help='Specify MTU for payload', dest='mtu', type=int, default=8000)
    parser.add_argument('--bps', '-b', help='Specify BPS for encoder', dest='bps', type=int, default=-1)
    parser.add_argument('--alternative', '-a', action='store_true',
                         default=False, dest='alt_ip', help='Use alternate IP')
    parser.add_argument('--encode', '-e', action='store_true',
                         default=False, dest='encode', help='Force reencoding of the video, even if not needed')
    parser.add_argument('--decklink', '-d', action='store_true',
                         default=False, dest='decklink', help='Use live input from decklink instead of a file.')
    parser.add_argument(
        '--info', '-i', help='Show info and quit', action='store_true', dest='show_info')
    parser.add_argument(
        '--dry-run', '-n', help='Dry run (display commends to be executed, but do not execute them', dest='dry_run', action='store_true')
    parser.add_argument(
        '--log', '-l', help='Write logs to /tmp', dest='use_log', default=False, action='store_true')
    parser.add_argument('--streamer', '-s', help='Streamer implementation (yuri or uv)',
                        dest='streamer', default='yuri')

    parser.add_argument('video_file', help='video file or decklink format')

    args = parser.parse_args()

    print ('Loading config from %s' % args.cfg_file)

    if not os.path.exists(args.cfg_file):
        print('Config file \'%s\' doesn\'t exist!' % args.cfg_file)
        sys.exit(1)
    
    cfg = json.load(open(args.cfg_file, 'rt'))
        
    template_name = u''
    dry = args.dry_run
    video_file = args.video_file
    mtu = args.mtu
    bps=args.bps
    alt_ip = args.alt_ip
    instances = []
    use_log = args.use_log
    use_uv = args.streamer == 'uv'
    force_encoding = args.encode
    
    if args.decklink:
        if not video_file in DECKLINK_FORMATS:
            print('Format %s not supported for decklink input! Supported formats are: %s'%(video_file, ', '.join(sorted(DECKLINK_FORMATS.keys()))))
            sys.exit(1)
        print ('Using input from decklink in format '+args.video_file)
        f = DECKLINK_FORMATS[video_file]
        stream={'width': f[0], 'height': f[1]}
        template_name = MAIN_XML_DECKLINK_TEMPLATE
    else:
        if not os.path.exists(args.video_file):
            print('Video file \'%s\' doesn\'t exist!' % args.video_file)
            sys.exit(1)
    
        
        cfg['video'] = get_video_info(args.video_file)
        stream = cfg['video']['streams'][0]    
        if (not stream['codec_name'] == 'h264') or force_encoding:
            template_name = MAIN_XML_TEMPLATE
            print('Input file is in format %s, reencoding'%stream['codec_name'])
        else:
            print('Streaming direcly the encoded content from input file in %s'%stream['codec_name'])
            template_name = MAIN_XML_DIRECT_TEMPLATE
        
         
    #print (json.dumps(cfg['video'], indent=2))
    

    devs = []
    nodes=u''
    
    main_tpl = Template(open(os.path.join(cfg['server']['dir'], template_name)).read())
    inner_tpl = Template(open(os.path.join(cfg['server']['dir'], INNER_XML_TEMPLATE)).read())
    
    print('Using %s streamer'%('ultragrid' if use_uv else 'YURI'))
    
#     idx = 0
    for idx, name in enumerate(cfg['renderers']):
        node = cfg['renderers'][name]
        dev = check_remote_webcam(node, stream['width'], stream['height'], 'yuyv')
        if not dev:
            print('Failed to setup webcam on node %s!'%name)
            sys.exit(1)
        print('Using %s through /proc/%s on node %s (%s)'%(dev['device'],dev['name'],name,node['address']))
        dev['node']=node
        dev['node_name']=name
        devs.append(dev)
        nodes = nodes + inner_tpl.substitute({'IDX':idx, 'IP':get_node_ip(node, alt_ip), 'STREAMER': 'uv_rtp_sender' if use_uv else 'simple_h264_sender'})+u'\n\n'
        
        
    oxml = main_tpl.substitute({'NODES':nodes})
        
    # This should use mkstemp or similar, keeping the same name only for debugging. 
    xml_name = '/tmp/ox.xml'
    open(xml_name,'wt+').write(oxml)
    
        
#     print ('Using MTU %d'%args.mtu)

    fps_stats = 100 if use_log else 0
    
    for dev in devs:
        node=dev['node']
        cmdline = ['ssh', '-t','-t',
                   node['address'], 
                   'DISPLAY=:0', 
                   '/usr/bin/yuri_simple',
                   '%s[address=0.0.0.0,fps_stats=%d]'%('uv_rtp_receiver' if use_uv else 'simple_h264_receiver', fps_stats),
                   '-punlimited',
                   'avdecoder[fps_stats=%d]'%fps_stats,
                   '-psingle',
                   'convert[format=%s,fps_stats=%d]'%(dev['format'],fps_stats),
                   'filedump[filename=/proc/%s]'%dev['name']
                   ]
        
        print (str(cmdline))
        if not dry:
            if use_log:
                log_file = open('/tmp/sagewebcam_%s.log'%dev['node_name'], 'wb')
            else:
                log_file = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(os.devnull, 'wb')
            sin = subprocess.PIPE#open(os.devnull, 'rb')
            p = subprocess.Popen(cmdline, stdout=log_file, stderr=subprocess.STDOUT, stdin=sin)
            instances.append(p)
            time.sleep(0.5)
            
    cmdline = ['/usr/bin/yuri2', 
               xml_name, 
               'file=' + video_file,
               'mtu=%d' %mtu,
               'bps=%s'%bps,
               'fps_stats=%d'%fps_stats,
               'resolution=%dx%d'% (stream['width'], stream['height'])
               ]
    print(cmdline)
    if not dry:
        if use_log:
            log_file = open('/tmp/sagewebcam_main.log', 'wb')
        else:
            log_file = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(os.devnull, 'wb')
        yuri_server = subprocess.Popen(cmdline, stdout=log_file, stderr=subprocess.STDOUT)

        try:
            yuri_server.wait()
            print('Yuri server exited normally')
            yuri_server = None
            # yuri_server = subprocess.call(cmdline)#, stdout=dev_null,
            # stderr=dev_null)
        except KeyboardInterrupt:
            pass
        if yuri_server:
            print('Killing yuri server')
            yuri_server.send_signal(subprocess.signal.SIGINT)
            try:
                yuri_server.wait(5)
            except:
                yuri_server.kill()

    for i in instances:
        print('Ending an instance')
        i.stdin.write(b'\x03')
        try:
            if sys.version_info.major >= 3:
                i.wait(5)
            else:
                counter = 50
                while counter > 0:
                    if i.poll() != None:
                        break
                    time.sleep(0.1)
                    counter -= 1
                else:
                    raise subprocess.TimeoutExpired
        except Exception as e:
            print('Instance didn\'t end voluntarily (%s), killing it'%(str(e)))
            i.kill()

    del instances

    
    
    
        
        
        