// SAGE2 is available for use under the SAGE2 Software License
//
// University of Illinois at Chicago's Electronic Visualization Laboratory (EVL)
// and University of Hawai'i at Manoa's Laboratory for Advanced Visualization and
// Applications (LAVA)
//
// See full text, terms and conditions in the LICENSE.txt included file
//
// Copyright (c) 2014



var webrtc_test = SAGE2_App.extend( {
	
	init: function(data) {
		// call super-class 'init'
		this.SAGE2Init("video", data);

		// application specific 'init'
		var t = this;

		t.maxFPS = 25.0;
		t.src_base = 'http://sapp.cesnet.cz:8800/';
//		t.signal_base = 'ws://sapp.cesnet.cz:3333';
		t.signal_base = 'ws://sapp.cesnet.cz:8800/';
		t.element.style.border = "none";
		t.element.style.background = "#fff";


		t.initializeWidgets();
		t.client_id = String(Math.floor(1000*Math.random()))+"::"+window.location;

		t.signaling = new WebSocket(t.signal_base);
		t.peer = null;
		t.remote_idx = -1;
		t.fcount = 0;
		t.ftime = 0;
		t.timer_id = -1;
		t.stats = function() {
			var video = t.element;
			var tt = new Date().getTime();
			var fc = video.webkitDecodedFrameCount;
			var fps = -1;
			if (t.ftime > 0) {
			        var dt = tt - t.ftime;
			        var df = fc - t.fcount;
			        if (dt > 0) {
			                fps = 1000.0 * df / dt;
					var msg = 'Displaying resolution: '+video.videoWidth +'x'+video.videoHeight+', fps: '+fps+', during ' +(dt/1000.0)+' seconds';
					console.log(msg);
					t.signaling.send(JSON.stringify({state:'status',index:t.remote_idx,message:msg,client_id:t.client_id}));
			        }
			}
			t.ftime = tt;
			t.fcount = fc;
			return fps;
		};


		t.signaling.onmessage = function (event) {
		//  console.log(event);
		  data = JSON.parse(event.data);
		  if (data.state=='to_client' && data.client_id == t.client_id) {
		    if (t.remote_idx < 0) {
		      t.remote_idx = data.index;  
		    } 
		    if (t.remote_idx == data.index) {
		      console.log('Processing event');
			if (t.peer) {
			      t.peer.signal(data.data);
			} else {
				console.log('Received message before creating a peer');		
			}
		    }
		  }
		}

		console.log('Creating peer');
		delay =  2 + Number(String(window.location).split('=')[1][0]);	
		if (isNaN(delay)) {
			delay = Math.random() * 4 + 2;
		}
			console.log(t);
		
		console.log(delay);	
		setTimeout(function() {t.signaling.send(JSON.stringify({state:'init',client_id:t.client_id}));}, delay * 1000);
		t.peer = new SimplePeer({ initiator: false, stream: false })
    
		t.peer.on('signal', function (data) {
		    t.signaling.send(JSON.stringify({state:'to_server',index:t.remote_idx,data:data,client_id:t.client_id}));
		})


  
		  t.peer.on('stream', function (stream) {
		    // got remote video stream, now let's show it in a video tag
		    console.log('Got video stream');
		    //var video = document.getElementById('video1');
		    var video = t.element;
		    video.src = window.URL.createObjectURL(stream);
		    video.play();
			t.stats();
			t.timer_id = window.setInterval(t.stats, 5000);
		  })
	},
	
	quit: function() {
		console.log('Quitting! timer id: '+this.timer_id);
		if (this.timer_id > -1) {
			window.clearInterval(this.timer_id);
		}
	},
	initializeWidgets: function() {
		this.controls.addTextInput({value: "", label: "URL", identifier: "URL"});
		this.controls.finishedAddingControls();		
	},

	load: function(state, date) {
	},
	

	draw: function(date) {
	},
	
	resize: function(date) {
		this.refresh(date);
	},
	
	event: function(eventType, position, user_id, data, date) {

		if (eventType === "pointerPress" && (data.button === "left") ) {		
		}
		if (eventType === "pointerMove") {
		}
		if (eventType === "pointerRelease" && (data.button === "left") ) {
		}
		if (eventType === "pointerScroll") {
		}

		if (eventType === "widgetEvent") {
			switch (data.identifier) {
				case "URL":
					text = data.text;
					this.element.src = "about:blank";
					if (!text.match(/^[a-zA-Z]+:\/\//))
					{
						text = 'http://' + text;
					}
					this.element.src = text;
					break;
				default:
					console.log("No handler for:", data.identifier);
			}
		}

		if (eventType == "specialKey" && data.code == 37 && data.state == "down") {
			// left
		}
		else if (eventType == "specialKey" && data.code == 38 && data.state == "down") {
			// up
		}
		else if (eventType == "specialKey" && data.code == 39 && data.state == "down") {
			// right
		}
		else if (eventType == "specialKey" && data.code == 40 && data.state == "down") {
			// down
		}
		
		this.refresh(date);
	}
});


