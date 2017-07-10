# High resolution video playback and streaming for LCD walls
This document describes scripts for preparing, playing and network streaming of videos on hi-res LCD walls using various methods with and without the SAGE2 software.

Currently, we support the following methods:
1. Local playback of hi-res video (tested up to 8k) on an LCD wall (without SAGE2)
2. Network streaming of video to SAGE2 using virtual web cameras and external streaming software
3. Network streaming of video to SAGE2 using WebRTC
4. Network streaming of video to SAGE2 using JPEG

Method 2 is the most powerful network streaming. Methods 3 and 4 are alternatives with simpler setup.

## Common dependencies and setup
- [python](https://www.python.org/) (version 3.4 or newer)
- [libyuri](https://github.com/v154c1/libyuri)
- [virtual camera](https://github.com/v154c1/virtual_camera)
- [ffmpeg](http://ffmpeg.org/) - Tested with original FFMPEG. It may work with libav, but it's not supported in any way.
- [ultragrid](http://www.ultragrid.cz) – for method 2
- [nodejs](https://nodejs.org/) - for method 3.

### Gentoo linux
An ebuild for these scripts and dependencies (mainly libyuri and virtual webcamera) is also provided as ebuild for **Gentoo Linux** in [cave_overlay](https://github.com/iimcz/cave_overlay) and there;s an overlay list XML on https://iim.cz/cave.xml.

If you have layman installed, the you can (as root):
```bash
cd /etc/layman/overlays
wget https://iim.cz/cave.xml
layman -a cave_overlay
emerge -atv sage_video virtual_camera
```

### Other linux distributions

When installing withou an ebuild, you should:
1. Install dependencies (ffmpeg, libyuri, virtual webcamera, ...)
2. install the script:
  - Put the scripts anywhere in your PATH
  - create configuration file in **/etc/sage_video/config.json** (based on example python/config.json.sample)
  - Dont't forget to specify path to *configs* directory in config.json


## Configuration file
The sample configuration file looks like this:
```json
{
    "total_x": 9600, 
    "total_y": 4320, 
    "stripes_x": 5, 
    "stripes_y": 1,

    "renderers": {
	    "0_0": {
	        "dir": "/usr/share/sage_video/configs", 
	        "address": "sage@xxxx",
	        "webcam_root": "/XXXX/XXX/virtual_webcam",
	        "alt_ip": "xxxxx"
	    }
    },
    "server": {
	    "dir": "/usr/share/sage_video/configs"
    }
}
```

- total\_x, total\_y - Resolution the the whole wall in pixels
- stripes\_x, stripes\_y - How are the PC nodes organized (not displays). For example, in our case, we have 20 displays - 4 rows and 5 columns. There are 5 PC nodes, each of them driving a single column of 4 displays. So there are 5 stripes in X axis, and only one stripe in Y axis.
- server.dir - Directory with XML configuration files from the repository. 
- renderers - The **nodes**. 
  - name of each renderer is "X_Y" -  where X is the number of stripe in X axis and Y is the number of stripe in Y axis.
  - dir - directory with XML's (like server.dir)
  - address - user and address of the node. e.g. cave@192.168.2.10
  - alt_ip - alternative IP address (if you have multiple network interfaces on nodes and you want to use non-default interfaces, such as local interconnection over private IP addresses)
  - webcam\_root - root directory of the virtual webcam installation.

Make sure that the user running the script on the **server** has rights to access all the nodes using ssh without password (authenticated by a key).

The nodes should have the module **vcmod** (for virtual camera) loaded, preferably set to load automatically during boot.

## 1. Local playback of hi-res video on an LCD wall (without SAGE2)

This solution works as a distributed player. Video is divided into stripes. Each stripe is played out on a separate node and presented on a vertical column of LCD monitors.

#### Setup:
- Server - master PC controlling the playback
- Nodes - PCs for playout of individual stripes
- Storage - common disk storage accessible from all nodes

#### How it works:
User starts a script on the **server** and the file is then played synchronously on all the **nodes**.
. The script also starts a webserver for controlling the playback (pause/play).

Internally, it can work in two modes:
- Direct playback - The **server** and all **nodes** accept the video file in its full resolution. The **server** sends messages to the nodes to maintain synchronization. The server can also play sound.
- Prepared videos - The video file is first cut into stripes, one for each node. The server then plays the original video (or a scaled down version) and each node plays just its own stripe. This mode is more effective and allows to play higher resolution videos (8K).

##### Direct playback:
Assuming that all PCs (server and nodes) have shared storage mounted on /storage:

```bash
sagevideo /storage/VIDEO.mp4
```

This plays a video file /storage/VIDEO.mp4 on all nodes, which have to process the full resolution video file.

```bash
sagevideo -s /storage/VIDEO.mp4
```
The same with sound (using JACK) enabled.

##### Prepared videos:
```bash
sagevideo -p /storage/VIDEO.mp4 -o /storage/VIDEO
```

This takes the input video file, calculates the required cropping/padding and creates video files for all the stripes and one down scaled video file for the server.

```bash
sagevideo /storage/VIDEO_small.mp4 -o /storage/VIDEO
```

This plays the small video file on the server and the pre-encoded stripes on nodes.

#### Performance:
On our system with 5 nodes, each driving four 1080p displays, it is possible to use the direct method for formats up to 4K30p. For higher resolutions, it is needed to prepare the video into stripes.


## 2. Network streaming of video to SAGE2 using a virtual web camera and external streaming software
#### Setup:
The setup consists of a server that sends the video (either from a video file or from a capture card), receivers on nodes with virtual web cameras and the SAGE2 application displaying the video.

The actual network streaming is implemented using external streaming software, such as Ultragrid, with H.264 compression and streaming in RTP packets. The PC nodes decode the received video streams and put them into virtual web cameras. The SAGE2 application then displays the output of the web cameras inside web browsers.


### Usage:
- Load the **vcmod** module for the virtual web camera on all nodes
- Run the sagewebcam script 
- Run the SAGE2 application **local_webcam** to show the web camera output


Running the sagewebcam script:

```bash
sagewebcam /storage/VIDEO.mp4
```

This script configures the virtual cameras on all nodes, starts receivers, opens a video source and streams it to all nodes.

There are several parameters that change the behaviour:
- -s/--streamer -  Sets the external streaming software. The values can be 'uv' for Ultragrid and ‘yuri’ as an alternative using libyuri internal streaming routines.
- -a/--alternative - Use alternative addresses (in case of networking problems on the main network interface)
- -d/--decklink - Use a Decklink capture card. The filename should be set to a valid Decklink format (eg., 1080p25)
- -l/--log - Saves the output to log files (/tmp/sagewebcam*)
- -m/--mtu - Specifies mtu
- -e/--encode – If the input video is stored in a H.264 encoded file, stream it as it is, without decoding and encoding it again

The virtual web cameras are automatically created by the **sagewebcam** script exactly for the resolution of the input video. The same virtual web cameras can be used repeatedly for streaming of multiple video sources, as long as the resolution does not change. If you change resolution of the input video, it is necessary to stop all Chrome/Electron web browsers of the SAGE2 before running the **sagewebcam** script and start all Chrome/Electron web browsers afterwards. Otherwise the web browsers hold the virtual web cameras open and they cannot be re-created by the **sagewebcam** script.

## 3. Network streaming of video to SAGE2 software using WebRTC

#### Setup:
The sender side uses a virtual web camera and a web browser (Chrome), which takes video from the virtual web camera and streams it to all web browsers of SAGE2. The sender side PC must have the **vcmod** module loaded.

#### Installation:
Set the address of the sender in the sage_webrtc.js script. 

On the sender, in the *webrtc* directory, run:

```bash
npm install
```

#### Usage:
On the sender, in the *webrtc* directory run:
```bash
npm run start
```

On the sender, run the **sagewebrtc** script:


```bash
sagewebrtc /storage/video.mp4
```

On the sender, start a Chrome web browser and point it to the URL http://localhost:8800

Now you can start the SAGE2 application**webrtc_test**, which should receive the streamed video. You can see statistics on the web page opened by the web browser on the sender.

## 4. Network streaming of video to SAGE2 software using JPEGs

#### Setup:
The sender opens a file, encodes frames to JPEG images and starts a webserver providing them over the network. The SAGE2 application then periodically requests images from the web server and displays them.

#### Installation:
Set the address of the sender in the **sage_jpeg.js** script.

#### Usage:
On the sender, start the **sagewebjpeg** script:

```bash
sagewebjpeg /storage/VIDEO.mp4
```

Now you can start the SAGE2 application **yuri_image**, which should receive the streamed video.





