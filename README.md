# sage_video
Scripts for preparing and playing videos on sage using various methods.

Currently, we support following methods:
1. Play hi-res videos (tested up to 8k) on sage-like system, without using any sage library.
2. Play videos using streaming and virtual webcameras
3. Stream video from virtual webcamera to sage2 using WebRTC
4. Stream video from local webserver using JPEG

## Common dependencies and setup
- [python](https://www.python.org/) (version 3.4 or newer)
- [libyuri](https://github.com/v154c1/libyuri)
- [virtual camera](https://github.com/v154c1/virtual_camera)
- [ffmpeg](http://ffmpeg.org/) - Tested with original FFMPEG. It may work with libav, but it's not supported in any way.
- [nodejs](https://nodejs.org/) - Only for method 3.

### Gentoo linux
An ebuild for these scripts and dependencies (mainly libyuri and virtual webcamera) is also provided as ebuild for **Gentoo Linux** in [cave_overlay](https://github.com/iimcz/cave_overlay) and there;s an overlay list XML on https://iim.cz/cave.xml.

If you have layman installed, the you can (as root):
```bash
cd /etc/layman/overlays
wget https://iim.cz/cave.xml
layman -a cave_overlay
emerge -atv sage_video virtual_camera
```

### Different linux distributions

When installing without ebuild, you should:
1. Install dependencies (ffmpeg, libyuri, virtual webcamera)
2. install the script:
  - Put the scripts anywhere in your path
  - create configuration file in **/etc/sage_video/config.json** (based on example python/config.json.sample)
  - Dont't forget to specify path to *configs* directory in config.json


## Config file
The sample cofig looks like:
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

- total\_x, total\_y - Resolution the the whole wall
- stripes\_x, stripes\_y - How are the nodes organized (nodes, not monitors). In our case, we have 20 displays - 4 rows and 5 columns. There are 5 nodes, each of then having a single column of 4 displays. So there are 5 stripes in X axis, and only single one in Y.
- server.dir - Directory with XML configuration files from the repository. 
- renderers - The **nodes**. 
  - name of each renderer is "X_Y" - where X is number of stripe in X axis, Y number in Y axis.
  - dir - directory with XML's (like server.dir)
  - address - user and address of the node. e.g. cave@192.168.2.10
  - alt_ip - alternative IP address (needed only when there are problems with main network)
  - webcam\_root - root darectory of virtual\_webcam installation. Set this only, when it's not installed in the system.

Make sure, that user running the script on **server** has rights to access all the nodes using ssh without password (authenticated by a key).

The nodes should have the module **vcmod** (for virtual camera) loaded, preferably set to load automatically on start.

## 1. Distributed player

#### Expected setup:
- Server - Master PC controlling the playback
- Nodes - sage nodes
- Storage - common storage accessible from all the nodes

#### How it works
User starts a script on the **server** and the file is then played synchronously on all ot sage nodes.
The script also starts a webserver for controlling the playback (pause/play).

Internally, it can work in two modes:
- direct playback - The **server** and all the **nodes** play the video in full resolution. The **server** send messages to the nodes to maintain synchronization. It can also playback a sound. 
- Prepared videos - The video to be played is firstly cut into stripes, one for each node. When the video is to be played, the server plays the original video (or scaled down version) and each node plays it's own stripe.

##### Direct playback:
Assuming that all machines (nodes and server) ha shared storage mounted on /storage

```bash
sagevideo /storage/VIDEO.mp4
```

This plays a video /storage/VIDEO.mp4 on all nodes. All nodes have to play the whole video.

```bash
sagevideo -s /storage/VIDEO.mp4
```
The same with sound (using JACK) enabled.

##### Prepared videos
```bash
sagevideo -p /storage/VIDEO.mp4 -o /storage/VIDEO
```

This takes the input video, calculates required cropping/padding and creates video for all the stripes and one small video for server.

```bash
sagevideo /storage/VIDEO_small.mp4 -o /storage/VIDEO
```

Now (without the parameter -p/--prepare), the script plays the small video on server and the preencoded stripes on nodes.

#### Performance
On our system with 5 sage nodes, all driving 4 fullHD displays, we're able to use the direct method for resolutions up to 4k. For higher resolutions, it's usually needed to prepare them.


## 2. using virtual webcamera
#### Expected setup
Server playing the video (either from a video file or from a decklink capture card), receivers with virtual camera on nodes and sage2 application displaying the video.


This setup a slightly more complicated. It take the input file (or output of decklink capture card) and streams it to sage nodes using RTP in h.264.
The nodes then decode the video a puts it into the virtual webcamera. Then, simple sage2 application displaying output of the webcamera can be used to show the video, as a SAGE2 application.



### Usage
- Firstly, make sure the vcmod module is loaded on all nodes
- Run the sagewebcam script 
- Run SAGE2 application showing the webcam output


```bash
sagewebcam /storage/VIDEO.mp4
```

Configures virtual cameras on all ndoes, starts receivers, opens video and streams it to all nodes. 
If the video is in h264, then it's simply streamed as is (this can be disabled by parameter -e/--encode). Otherwise it's decoded, encoded into h264 and streamed. Note: not every h264 file is encoded for streaming. In a case of problems, add the -e and try it again with reencoded stream.

There are several parameters that change the bahaviour:
- -s/--streamer - Sets the underlying streaming implementation. Default value is 'yuri'. If you have libyuri compiled with ultragrid support, you can also try 'uv' as an alternative.
- -a/--alternative - Use alternative addresses (in a case main interface has bad properties)
- -d/--decklink - Use decklink capture card. The filename should be se to a valid decklink format (eg 1080p25)
- -l/--log - Saves output to log files (/tmp/sgewebcam*)
- -m/--mtu - Specifies mtu


## 3. WebRTC

#### Expected setup
Server with virtual webcamera and browser (chrome). The server has to have **vcmod** module loaded.

#### Installing
Before installing sage2 application, change the address of websocket server in the sage_webrtc.js to address of **server**.
On the server side, run 
```bash
npm install
```
in the *webrtc* directory.

#### Usage
On the **server**, firstly start the server (in webrtc directory):
```bash
npm run start
```

Then run *sagewebrtc* script and access http://localhost:8800/. This should connect to virtual webcam. Now you can start the application on sage.

```bash
sagewebrtc /storage/video.mp4
```

## 4. Local webserver and JPEGs

#### Expected setup
**Server** opens a file, encodes frames to JPEG and starts a webserver providing these images.
**sage2** application then periodically takes images from the webserver.


#### Installing
Before deploying the sage2 application, change the address of **server** in sage_jpeg.js

#### Usage
```bash
sagewebjpeg /storage/VIDEO.mp4
```




