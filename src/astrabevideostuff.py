import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
gi.require_version("GstVideo", "1.0")
from gi.repository import GstVideo

class VideoStuff():
    def play(self,rate):
        pass
    def pause(self):
        pass
    def stop(self):
        pass
    def skip(self,rate,amount):
        pass
    def frame_step(self,num):
        pass
    def seek_simple(self,pos_nano_sec):
        pass
    def set_file(self,uri):
        pass
    

class GstVideoStuff(VideoStuff):
    def __init__(self):
        self.playbin = Gst.ElementFactory.make("playbin", "playbin")
        
        #bin = Gst.Bin.new("my-bin")
        #timeoverlay = Gst.ElementFactory.make("timeoverlay")
        #bin.add(timeoverlay)
        #pad = timeoverlay.get_static_pad("video_sink")
        #ghostpad = Gst.GhostPad.new("sink", pad)
        #bin.add_pad(ghostpad)
        #videosink = Gst.ElementFactory.make("autovideosink")
        #bin.add(videosink)
        #timeoverlay.link(videosink)
        #self.playbin.set_property("video-sink", bin)        
        
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message::state-changed", self.on_state_changed__bus)
        bus.connect("message::eos", self.on_eos__bus)
        #bus.connect("message::error", self.on_error__bus)
        #bus.connect("message::application", self.on_application__bus)
        self.state = Gst.State.NULL
        self.duration = Gst.CLOCK_TIME_NONE
        self.handlers_on_state_changed__bus=[]
        self.seek_data=None
        self.target_position=-1

    def on_eos__bus(self,bus,message):
        videosink=self.playbin.get_property("video-sink")
        seek_event=Gst.Event.new_seek(1.0,
                                      Gst.Format.TIME,
                                      Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                      Gst.SeekType.SET,
                                      self.target_position,
                                      Gst.SeekType.SET,
                                      -1)
        self.target_position=-1
        self.seek_data=(1.0,-1)
        videosink.send_event(seek_event)
        self.playbin.set_state(Gst.State.PAUSED)
        pass

        
    def set_file(self,uri):
        if not self.playbin:
            print("ERROR: playbinを作成できませんでした。")
            return
        self.playbin.set_property("uri",uri)
        ret = self.playbin.set_state(Gst.State.PAUSED)
        self.analyze_stream()

    def attach_window(self,window_handle):
        if not self.playbin:
            print("ERROR: playbinを作成できませんでした。")
            return
        self.playbin.set_window_handle(window_handle)
        
    def play(self,rate):
        if self.seek_data != (rate,-1):
            videosink=self.playbin.get_property("video-sink")
            position=self.query_position(Gst.Format.TIME)
            if rate>0:
                seek_event=Gst.Event.new_seek(rate,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              position,
                                              Gst.SeekType.SET,
                                              -1)
                self.target_position=-1
            elif rate<0:
                seek_event=Gst.Event.new_seek(rate,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              0,
                                              Gst.SeekType.SET,
                                              position)
                self.target_position=0
            videosink.send_event(seek_event)
            self.seek_data = (rate,-1)
        ret = self.playbin.set_state(Gst.State.PLAYING)
        
    def pause(self):
        ret = self.playbin.set_state(Gst.State.PAUSED)
        
    def stop(self):
        ret = self.playbin.set_state(Gst.State.PAUSED)
        self.playbin.seek_simple(Gst.Format.TIME,Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,0)
        #ret = self.playbin.set_state(Gst.State.READY)

    def skip(self,rate,amount):
        videosink=self.playbin.get_property("video-sink")
        (f,s)=self.framerate
        if rate > 0:
            seek_data=(rate,amount)
            if self.seek_data != seek_data:
                position=self.query_position(Gst.Format.TIME)
                seek_event=Gst.Event.new_seek(rate,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              position,
                                              Gst.SeekType.SET,
                                              position+amount)
                self.target_position=position+amount
                self.seek_data=seek_data
                videosink.send_event(seek_event)
        else:
            seek_data=(rate,amount)
            if self.seek_data != seek_data:
                position=self.query_position(Gst.Format.TIME)
                seek_event=Gst.Event.new_seek(rate,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              position-amount,
                                              Gst.SeekType.SET,
                                              position)
                self.target_position=position-amount
                self.seek_data=seek_data
                videosink.send_event(seek_event)
        ret = self.playbin.set_state(Gst.State.PLAYING)
            
        return
        
    def seek_simple(self,pos_nano_sec):
        self.playbin.seek_simple(Gst.Format.TIME,
                                  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                  pos_nano_sec)
 
    def frame_step(self,diff_frame):
        ret = self.playbin.set_state(Gst.State.PAUSED)
        videosink=self.playbin.get_property("video-sink")
        (f,s)=self.framerate
        if diff_frame > 0:
            seek_data=(1.0,-1)
            if self.seek_data != seek_data:
                position=self.query_position(Gst.Format.TIME)
                seek_event=Gst.Event.new_seek(1.0,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              position,
                                              Gst.SeekType.SET,
                                              -1)
                self.target_position=-1
                self.seek_data=seek_data
                videosink.send_event(seek_event)
        else:
            seek_data=(-1.0,-1)
            if self.seek_data != seek_data:
                position=self.query_position(Gst.Format.TIME)
                seek_event=Gst.Event.new_seek(-1.0,
                                              Gst.Format.TIME,
                                              Gst.SeekFlags.FLUSH|Gst.SeekFlags.ACCURATE,
                                              Gst.SeekType.SET,
                                              0,
                                              Gst.SeekType.SET,
                                              position)
                self.target_position=0
                self.seek_data=seek_data
                videosink.send_event(seek_event)
            
        stepevent=Gst.Event.new_step(Gst.Format.BUFFERS,abs(diff_frame),1,True,False)

        videosink.send_event(stepevent)
        return

    def query_duration(self,format):
        (ret,self.duration)=self.playbin.query_duration(format)
        return self.duration

    def query_position(self,format):
        (ret,position) = self.playbin.query_position(format)
        return position
    
    def on_state_changed__bus(self,bus,msg):
        (old,new,pending) = msg.parse_state_changed()
        if msg.src != self.playbin:
            return
        self.state = new
        for f in self.handlers_on_state_changed__bus:
            f(bus,msg)
        self.analyze_stream()

    def analyze_stream(self):
        caps=None
        (ret, duration) = self.playbin.query_duration(Gst.Format.TIME)
        if ret:
            self.duration=duration
        else:
            self.duration=0
        sample = self.playbin.get_property("sample")
        if sample:
            caps=sample.get_caps()
        if caps:
            for i in range(caps.get_size()):
                structure=caps.get_structure(i)
                #print(structure.to_string())                
                (ret,numerator,denominator)=structure.get_fraction("framerate")
                if ret:
                    self.framerate=(numerator,denominator)

        nr_video = self.playbin.get_property("n-video")
        for i in range(nr_video):
            tags = self.playbin.emit("get-video-tags",i)
            if tags:
                #print("video stram {0}".format(i))
                (ret,s)=tags.get_string(Gst.TAG_VIDEO_CODEC)
                #print(" codec: {0}".format(s))
                (ret,a)=tags.get_uint(Gst.TAG_BITRATE)
                #print(" bitrate: {0}".format(a))
        nr_audio = self.playbin.get_property("n-audio")
        for i in range(nr_audio):
            tags = self.playbin.emit("get-audio-tags",i)
            if tags:
                #print("audio stram {0}".format(i))
                (ret,s)=tags.get_string(Gst.TAG_AUDIO_CODEC)
                #print(" codec: {0}".format(s))
                (ret,s)=tags.get_string(Gst.TAG_LANGUAGE_CODE)
                #print(" language: {0}".format(s))
                (ret,a)=tags.get_uint(Gst.TAG_BITRATE)
                #print(" bitrate: {0}".format(a))
        nr_text = self.playbin.get_property("n-text")
        for i in range(nr_text):
            tags = self.playbin.emit("get-text-tags",i)
            if tags:
                #print("subtitle stram {0}".format(i))
                (ret,s)=tags.get_string(Gst.TAG_LANGUAGE_CODE)
                #print(" language: {0}".format(s))
