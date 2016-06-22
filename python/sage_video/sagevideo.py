#!/usr/bin/python

'''
Created on 20. 4. 2016

@author: neneko
'''
import json
import subprocess
import argparse
import os.path
import sys
import time

INSTALL_DIR = "/etc/sage_video"

SERVER_CFG_FILE = 'sync_server.xml'
SERVER_CFG_FILE_SOUND = 'sync_server_sound.xml'
CLIENT_CFG_FILE = 'sync_client_no_pad.xml'
CLIENT_CFG_FILE_PAD = 'sync_client.xml'


def get_video_info(filename):
    video_data = json.loads(subprocess.check_output(
        ['ffprobe', '-of', 'json', '-show_streams', '-select_streams', 'v', filename], stderr=subprocess.PIPE).decode('utf8'))
    return video_data


def compute(cfg):
    stripes_x = cfg['stripes_x']
    stripes_y = cfg['stripes_y']
    total_x = cfg['total_x']
    total_y = cfg['total_y']

    part_width = total_x / stripes_x
    part_height = total_y / stripes_y

    print('Preparing videos for %dx%d displays, %dx%d each' %
          (stripes_x, stripes_y, part_width, part_height))

    video_data = cfg['video']

    W = video_data["streams"][0]['width']
    H = video_data["streams"][0]['height']

    # find upscaled resolution
    if (total_x / W) < (total_y / H):
        display_width = total_x
        display_height = H * total_x / W
        virtual_width = W
        virtual_height = W * total_y / total_x
    else:
        display_width = W * total_y / H
        display_height = total_y
        virtual_width = H * total_x / total_y
        virtual_height = H

    offset_x = (virtual_width - W) / 2
    offset_y = (virtual_height - H) / 2

    stripe_x = virtual_width / stripes_x
    stripe_y = virtual_height / stripes_y

    print('Displayed resolution will be %dx%d' %
          (display_width, display_height))
    print('Virtual resolution will be %dx%d, offset %dx%d' %
          (virtual_width, virtual_height, offset_x, offset_y))
    print('Stripes will have resolution %dx%d' % (stripe_x, stripe_y))

    vdx = -offset_x
    dx = 0

    cfg['tiles'] = {}
    for part_x in range(0, stripes_x):
        w = min(vdx + stripe_x, W - dx)
        vdx = min(vdx + stripe_x, 0)

        if w <= 0:
            print('ignoring column %d' % (part_x))

        vdy = -offset_y
        dy = 0
        for part_y in range(0, stripes_y):
            h = min(vdy + stripe_y, H - dy)
            vdy = min(vdy + stripe_y, 0)
            if h <= 0:
                print('ignoring row %d' % (part_y))
            print('Crop (%d,%d): %dx%d+%d+%d' % (part_x, part_y, w, h, dx, dy))
            x = stripe_x - w if dx == 0 else 0
            y = stripe_y - h if dy == 0 else 0

            cfg['tiles']['%d_%d' % (part_x, part_y)] = {
                'w': w,
                'h': h,
                'dx': dx,
                'dy': dy,
                'x': x,
                'y': y
            }

            dy = dy + h
        dx = dx + w

    cfg['offset_x'] = offset_x
    cfg['offset_y'] = offset_y
    cfg['stripe_x'] = stripe_x
    cfg['stripe_y'] = stripe_y
    cfg['virtual_width'] = virtual_width
    cfg['virtual_height'] = virtual_height
    cfg['W'] = W
    cfg['H'] = H
    cfg['part_width'] = part_width
    cfg['part_height'] = part_height
    return cfg


def cut(cfg, filename, out_prefix, dry):
    stripe_x = cfg['stripe_x']
    stripe_y = cfg['stripe_y']

    for tile_id in cfg['tiles']:
        tile = cfg['tiles'][tile_id]
        x = tile['x']
        y = tile['y']
        w = tile['w']
        h = tile['h']
        dx = tile['dx']
        dy = tile['dy']

        print('Crop (%s): %dx%d+%d+%d' % (tile_id, w, h, dx, dy))

        filter = 'crop=%d:%d:%d:%d [v0];[v0] pad=%d:%d:%d:%d:black' % (
            w, h, dx, dy, stripe_x, stripe_y, x, y)
        ofn = '%s_%s.mp4' % (out_prefix, tile_id)
        if os.path.exists(ofn):
            print('File %s already exists' % (ofn))
        else:
            cmdline = ['ffmpeg', '-i', filename, '-filter:v', filter,
                       '-an', '-c:v', 'libx264', '-preset', 'slower', ofn]
            print('cmdline: %s' % str(cmdline))
            if not dry:
                subprocess.call(cmdline)


def play(cfg, video_file, out_prefix, sound, format, dry):
    client_cfg = CLIENT_CFG_FILE if out_prefix else CLIENT_CFG_FILE_PAD
    server_cfg = SERVER_CFG_FILE_SOUND if sound else SERVER_CFG_FILE

    stripes_x = cfg['stripes_x']
    stripes_y = cfg['stripes_y']
    total_x = cfg['total_x']
    total_y = cfg['total_y']
    offset_x = cfg['offset_x']
    offset_y = cfg['offset_y']
    stripe_x = cfg['stripe_x']
    stripe_y = cfg['stripe_y']
    virtual_width = cfg['virtual_width']
    virtual_height = cfg['virtual_height']
    W = cfg['W']
    H = cfg['H']
    part_width = cfg['part_width']
    part_height = cfg['part_height']

    instances = []

    dev_null = subprocess.DEVNULL if 'DEVNULL' in subprocess.__all__ else open(
        os.devnull, 'wb')
    print(dev_null)
    for tile_id in cfg['tiles']:
        tile = cfg['tiles'][tile_id]
        x = tile['x']
        y = tile['y']
        w = tile['w']
        h = tile['h']
        dx = tile['dx']
        dy = tile['dy']

        if not tile_id in cfg['renderers']:
            print('Unspecified tile %s' % tile_id)
            continue

        filename = out_prefix + \
            '_%s.mp4' % tile_id if out_prefix else video_file

        renderer = cfg['renderers'][tile_id]

        cmdline = ['ssh', '-t',
                   renderer['address'], '/usr/bin/yuri2',
                   os.path.join(renderer['dir'], client_cfg),
                   '-o', '/tmp/sage_video.log',
                   'resolution=%dx%d' % (part_width, part_height),
                   'file=' + filename,
                   'format=' + format]
        if not out_prefix:
            cmdline = cmdline + [
                'crop=%dx%d+%d+%d' % (w, h, dx, dy),
                'pad=%dx%d' % (stripe_x, stripe_y),
                'halign=%s' % ('left' if x == 0 else 'right')]

        print (str(cmdline))
        if not dry:
            p = subprocess.Popen(cmdline, stdout=dev_null, stderr=dev_null)
            instances.append(p)
            time.sleep(0.5)

    sdir = cfg['server']['dir']
    cmdline = ['/usr/bin/yuri2', os.path.join(
        sdir, server_cfg), 'file=' + video_file, 'webdir=' + os.path.join(sdir, 'webcontroller'), 'format=%s' % format]
    print('Server cmdline: %s' % str(cmdline))
    if not dry:
        yuri_server = subprocess.Popen(cmdline)

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
        i.send_signal(subprocess.signal.SIGINT)
        try:
            i.wait(5)
        except:
            i.kill()

    del instances


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sage video player')
    parser.add_argument('--config', '-c', help='configuration file',
                        dest='cfg_file', default=os.path.join(INSTALL_DIR, 'config.json'))
    parser.add_argument('--prepare', '-p', help='Prepare the videos instead of playing',
                        dest='prepare', action='store_true', default=False)
    parser.add_argument('--sound', '-s', action='store_true',
                        default=False, dest='use_sound', help='Enable sound')
    parser.add_argument(
        '--output', '-o', help='Output file prefix', dest='out_prefix')
    parser.add_argument('--format', '-f', help='Specify format for display', dest='format', choices=[
                        'original', 'rgb', 'bgr', 'yuv', 'uyvy', 'yuv444', 'yuv444p', 'yuv420p', 'yuv422p'], default='original')
    parser.add_argument(
        '--info', '-i', help='Show info and quit', action='store_true', dest='show_info')
    parser.add_argument(
        '--dry-run', '-n', help='Dry run (display commends to be executed, but do not execute them', dest='dry_run', action='store_true')
    parser.add_argument('video_file', help='video file')

    args = parser.parse_args()

    print ('Loading config from %s' % args.cfg_file)

    if not os.path.exists(args.cfg_file):
        print('Config file \'%s\' doesn\'t exist!' % args.cfg_file)
        sys.exit(1)

    if not os.path.exists(args.video_file):
        print('Video file \'%s\' doesn\'t exist!' % args.video_file)
        sys.exit(1)

    cfg = json.load(open(args.cfg_file, 'rt'))
    cfg['video'] = get_video_info(args.video_file)
    cfg = compute(cfg)

    if args.show_info:
        pass
    elif args.prepare:
        if not args.out_prefix:
            print(
                'You need to provide output prefix (--output) for preparation!')
            sys.exit(1)
        cut(cfg, args.video_file, args.out_prefix, args.dry_run)
    else:
        print ('Playing video %s sound, using conversion to %s' %
               ('with' if args.use_sound else 'without', args.format))
        play(cfg, args.video_file, args.out_prefix,
             args.use_sound, args.format, args.dry_run)
