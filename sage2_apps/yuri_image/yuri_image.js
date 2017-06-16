// SAGE2 is available for use under the SAGE2 Software License
//
// University of Illinois at Chicago's Electronic Visualization Laboratory (EVL)
// and University of Hawai'i at Manoa's Laboratory for Advanced Visualization and
// Applications (LAVA)
//
// See full text, terms and conditions in the LICENSE.txt included file
//
// Copyright (c) 2014


var yuri_image = SAGE2_App.extend( {
	
	init: function(data) {
		this.SAGE2Init("img", data);

		// application specific 'init'
		var t = this;

		t.maxFPS = 25.0;
		t.src_base = 'http://sapp.cesnet.cz:8890/image/';
		t.signal_base = 'ws://sapp.cesnet.cz:8800/';
		t.element.style.border = "none";
		t.element.style.background = "#fff";

//		t.element.innerHTML = templ;
		t.element.src = 'http://sapp.cesnet.cz:8880/image.jpg';
//		t.element.onload = function(){
		t.rr = function(){
			var data =t.element;
			data.src = data.src.split('?')[0] + '?id=' + new Date().getTime()+Math.random();
			t.fcount_curr = t.fcount_curr+1;
			console.log('Reload '+ t.fcount_curr);
		};

		t.initializeWidgets();
		t.client_id = String(Math.floor(1000*Math.random()))+"::"+window.location;
		t.remote_idx = -1;
		t.signaling = new WebSocket(t.signal_base);
		t.fcount = 0;
		t.fcount_curr = 0;
                t.ftime = 0;
                t.timer_id = -1;
                t.timer_id2 = -1;
                t.stats = function() {
                        var tt = new Date().getTime();
                        var fps = -1;
                        if (t.ftime > 0) {
                                var dt = tt - t.ftime;
                                var df = t.fcount_curr - t.fcount;
                                if (dt > 0) {
                                        fps = 1000.0 * df / dt;
                                        var msg = fps+' fps during ' +(dt/1000.0)+' seconds';
                                        console.log(msg);
                                        t.signaling.send(JSON.stringify({state:'status',index:t.remote_idx,message:msg,client_id:t.client_id}));
                                }
                        }
                        t.ftime = tt;
                        t.fcount = t.fcount_curr;
                        return fps;
                };
		console.log(t);
		t.remote_idx = Number(String(window.location).split('=')[1][0]);
		if (isNaN(t.remote_idx)) {
			t.remote_idx = 99;
		}
		console.log(t.remote_idx);
		t.stats();
                t.timer_id = window.setInterval(t.stats, 5000);
                t.timer_id2 = window.setInterval(t.rr, 40);
	},
	quit: function() {
                console.log('Quitting! timer id: '+this.timer_id);
                if (this.timer_id > -1) {
                        window.clearInterval(this.timer_id);
                        window.clearInterval(this.timer_id2);
                }
        },	
	initializeWidgets: function() {
		this.controls.addTextInput({value: "", label: "URL", identifier: "URL"});
		this.controls.finishedAddingControls();		
	},

	load: function(state, date) {
	},
	

	reload_img: function(id) {
		document.getElementById(id).src = document.getElementById(id).src.split('?')[0] + '?id=' + new Date().getTime();		
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


