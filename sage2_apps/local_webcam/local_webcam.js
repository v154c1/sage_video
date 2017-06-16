var local_webcam = SAGE2_App.extend( {
    init: function(data) {
        this.SAGE2Init('video', data);

		// application specific 'init'
		var t = this;
		
        t.resizeEvents = "continuous";
        
        
        navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia || navigator.oGetUserMedia;
		if (navigator.getUserMedia) {       
			navigator.getUserMedia({video: true}, handleVideo, videoError);
		}
 
		function handleVideo(stream) {
			t.element.src = window.URL.createObjectURL(stream);
			t.element.play();
		}
		
		function videoError() {
			t.log("Video error, sorry.")
		}

    },

    load: function(date) {
		this.log("Load");
    },

    draw: function(date) {
        this.log("Draw");
    },

    resize: function(date) {
        this.refresh(date); //redraw after resize
    },

    event: function(type, position, user, data, date) {
        this.refresh(date);
    },

    move: function(date) {
        this.refresh(date);
       },

    quit: function() {
        this.log("Done");
    }
});
