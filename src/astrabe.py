#!/usr/bin/env python3
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,GdkPixbuf,Gio,GLib,Gdk
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst,GstVideo

import enum
import math

import universalcolordesign

class RegularlyUpdatable:
    def init_timerid_and_interval(self,interval):
        self.update_interval=interval
        if not hasattr(self,"timerid"):
            self.timerid=None
        if not hasattr(self,"timerid"):
            self.timer_num_steps=0
        
    def set_video_stuff(self, video_stuff):
        self.video_stuff=video_stuff
        self.video_stuff.handlers_on_state_changed__bus.append(self.on_state_changed__bus)

    def on_state_changed__bus(self,buf,msg):
        (old,new,pending) = msg.parse_state_changed()
        if new == Gst.State.PLAYING:
            self.set_regular_update(-1)
        else:
            self.set_regular_update(10)

    def set_regular_update(self,lim_num):
        self.timer_num_steps=lim_num
        if lim_num==0:
            if self.timerid != None:
                GLib.source_remove(self.timerid)
            self.timerid = None
        else:
            if self.timerid == None:
                self.timerid=GLib.timeout_add(self.update_interval,self.regular_update_upto_num)
                
    def regular_update_upto_num(self):
        self.regular_update_step()
        if self.timer_num_steps>0:
            self.timer_num_steps=self.timer_num_steps-1
        if self.timer_num_steps == 0:
            self.timerid=None
            return False
        return True

    def regular_update_step(self):
        pass

class TrackDrawingArea(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.time_per_unit = 0.1*Gst.SECOND
        
    def to_x(self,time):
        return time/self.time_per_unit
    def to_time(self,x):
        return x*self.time_per_unit

class CursorTrack(TrackDrawingArea):
    def __init__(self):
        super().__init__()
        self.current_time=0
        self.marked_time=0
        
        self.connect("draw", self.on_draw__area)

        self.clicked_position=None
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-press-event",self.on_click__area)           
        self.connect("button-release-event",self.on_release__area)            


        
    def on_click__area(self,widget,eventbutton):
        self.clicked_position=(eventbutton.x,eventbutton.y)

    def on_release__area(self,widget,eventbutton):
        if (eventbutton.x,eventbutton.y)==self.clicked_position:
            self.set_marked_time(self.to_time(eventbutton.x))
            print("clicked")
        else:
            print("draged")
        self.clicked_position=None

    def set_marked_time(self,time):
        self.marked_time=time
        self.queue_draw()

    def get_marked_time(self):
        return self.marked_time

    def set_current_time(self,time):
        self.current_time=time
        self.queue_draw()
        
    def get_current_time(self):
        return self.current_time
    
    def on_draw__area(self, widget, cr):
        allocation = widget.get_allocation()
        y=allocation.height
        x=self.to_x(self.current_time)
        (r,g,b,a)=universalcolordesign.CUD_V4.B1A
        cr.set_source_rgba(r,g,b,a)
        cr.move_to(x,0)
        cr.line_to(x,y)
        cr.stroke()

        x=self.to_x(self.marked_time)
        (r,g,b,a)=universalcolordesign.CUD_V4.B4A
        cr.set_source_rgba(r,g,b,a)
        cr.move_to(x,0)
        cr.line_to(x,y)
        cr.stroke()
        
        return True

class RulerTrack(TrackDrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1,10)
        self.is_for_upper=False
        self.connect("draw", self.on_draw__area)
        
    def set_duration(self,duration):
        self.set_size_request(self.to_x(duration),10)
        
    def on_draw__area(self, widget, cr):
        allocation = widget.get_allocation()
        y=allocation.height
        (r,g,b)=universalcolordesign.CUD_V4.G3
        cr.set_source_rgba(r,g,b)
        n=allocation.width//5
        for (ni,ri) in [(1,4),(5,2),(10,1)]:
            yi=y//ri
            if self.is_for_upper:
                y0=0
                y1=yi
            else:
                y0=y
                y1=y-yi
            for i in range(n//ni):
                cr.move_to(i*5*ni,y0)
                cr.line_to(i*5*ni,y1)
                cr.stroke()        
        return True

class SegmentTrack(TrackDrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1,10)
        self.segment=[]
        self.maxzindex=-1
        self.maxterminal=-1
        self.connect("draw", self.on_draw__area)

    def append_segment(self,start,terminal,label):
        zz=[z for (s,t,z,l) in self.segment if (s<=start and start<=t) or  (s<=terminal and terminal<=t) or (start<=s and s<=terminal) or (start<=t and t<=terminal) ]
        for i in range(len(zz)+1):
            if i not in zz:
                zindex = i
                break

        self.segment.append((start,terminal,zindex,label))
        if zindex > self.maxzindex:
            self.maxzindex=zindex
            self.set_size_request(self.to_x(self.maxterminal),10*(self.maxzindex+1))
        if terminal > self.maxterminal:
            self.maxterminal=terminal
            self.set_size_request(self.to_x(self.maxterminal),10*(self.maxzindex+1))

        
    def on_draw__area(self, widget, cr):
        allocation = widget.get_allocation()
        y=allocation.height
        (r,g,b,a)=universalcolordesign.CUD_V4.B1A
        cr.set_source_rgba(r,g,b,a)
        for (s,t,z,l) in self.segment:
            x0=self.to_x(s)
            x1=self.to_x(t)
            cr.move_to(x0,0)
            cr.line_to(x0,y)
            cr.stroke()        
            cr.move_to(x1,0)
            cr.line_to(x1,y)
            cr.stroke()
        (r,g,b)=universalcolordesign.CUD_V4.A1
        cr.set_source_rgb(r,g,b)
        for (s,t,z,l) in self.segment:        
            x0=self.to_x(s)
            x1=self.to_x(t)
            cr.move_to(x0,z*10+5)
            cr.line_to(x1,z*10+5)
            cr.stroke()
            cr.arc(x0,z*10+5,2,-math.pi/2,math.pi/2)
            cr.fill()
            cr.arc(x1,z*10+5,2,math.pi/2,3*math.pi/2)
            cr.fill()
        return True


class LinechartTrack(TrackDrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1,110)
        self.series_of_data = {}
        self.min_max = []
        self.maxtime=-1
        self.connect("draw", self.on_draw__area)
        self.colors = {}
        self.color_pallet = [universalcolordesign.CUD_V4.A1,
                             universalcolordesign.CUD_V4.A2,
                             universalcolordesign.CUD_V4.A4,
                             universalcolordesign.CUD_V4.A5,
                             universalcolordesign.CUD_V4.A3,
                             universalcolordesign.CUD_V4.A7,
                             universalcolordesign.CUD_V4.A8,
                             universalcolordesign.CUD_V4.A9,
                             universalcolordesign.CUD_V4.A6]

    def append_data(self,time,s,data):
        if s not in self.series_of_data:
            self.series_of_data[s]=[]
        self.series_of_data[s].append((time,data))
        self.series_of_data[s].sort()

        if s not in self.colors:
            self.colors[s]=self.color_pallet[(len(self.series_of_data)-1)]

        if time > self.maxtime:
            self.maxtime=time
            self.set_size_request(self.to_x(self.maxtime),110)

        flag=True
        n=len(self.min_max)
        if n>0:
            if self.min_max[-1][0]>=time:
                for j in range(n):
                    i=n-j-1
                    if self.min_max[i][0]==time:
                        if self.min_max[i][2]>data:
                            self.min_max[i][1]=s
                            self.min_max[i][2]=data
                        if self.min_max[i][4]<data:
                            self.min_max[i][3]=s
                            self.min_max[i][4]=data
                        flag=False
        if flag:
            self.min_max.append([time,s,data,s,data])
            self.min_max.sort()
        

    def to_y(self,v):
        return 105-v*100
    
    def on_draw__area(self, widget, cr):
        allocation = widget.get_allocation()
        y=allocation.height

        n=len(self.series_of_data)
        for k in self.series_of_data.keys():
            (r,g,b)=self.colors[k]
            cr.set_source_rgb(r,g,b)
            cr.move_to(self.to_x(0),self.to_y(0))
            for (time,v) in self.series_of_data[k]:
                x0=self.to_x(time)
                y0=self.to_y(v)
                cr.line_to(x0,y0)
            cr.stroke()

        for (min_max_0,min_max_1) in zip(self.min_max,self.min_max[1:]):
            x0=self.to_x(min_max_0[0])
            x1=self.to_x(min_max_1[0])
            (r,g,b)=self.colors[min_max_0[1]]
            cr.set_source_rgb(r,g,b)
            cr.move_to(x0,self.to_y(0))
            cr.line_to(x1,self.to_y(0))
            cr.stroke()
            (r,g,b)=self.colors[min_max_0[3]]
            cr.set_source_rgb(r,g,b)
            cr.move_to(x0,self.to_y(1))
            cr.line_to(x1,self.to_y(1))
            cr.stroke()
        return True


class TrackArea(Gtk.ScrolledWindow,RegularlyUpdatable):
    def __init__(self):
        super().__init__()
        self.current_time=0
        #scw.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.NEVER)
        self.set_policy(Gtk.PolicyType.ALWAYS,Gtk.PolicyType.NEVER)
        overlay=Gtk.Overlay()
        self.add(overlay)
        self.cursorarea=CursorTrack()
        overlay.add_overlay(self.cursorarea)
        self.box=Gtk.Box()
        self.box.set_orientation(Gtk.Orientation.VERTICAL)
        overlay.add(self.box)

        self.ruler=RulerTrack()
        self.add_track(self.ruler)

        self.video_stuff=None
        self.init_timerid_and_interval(10)
        
    def get_marked_time(self):
        return self.cursorarea.get_marked_time()
    
    def set_marked_time(self,t):
        return self.cursorarea.set_marked_time(t)
    
    def get_current_time(self):
        return self.cursorarea.get_current_time()
    
    def regular_update_step(self):
        current=self.video_stuff.query_position(Gst.Format.TIME)
        if current < 0:
            return True
        self.cursorarea.set_current_time(current)
        cx=self.cursorarea.to_x(current)
        adj=self.get_hadjustment()
        px=adj.get_value()
        ps=adj.get_page_size()
        x1=adj.get_upper()
        if cx > self.current_time:
            if cx < px:
                x=cx
                adj.set_value(x)
            elif cx < px+ps/2:
                pass
            elif cx < x1-ps/2:
                x=cx-ps/2
                adj.set_value(x)
            else:
                x=x1-ps
                adj.set_value(x)
        elif cx < self.current_time:
            if cx > px+ps:
                x=cx-ps
                adj.set_value(x)
            elif cx > px+ps/2:
                pass
            elif cx > ps/2:
                x=cx-ps/2
                adj.set_value(x)
            else:
                x=0
                adj.set_value(x)
        self.current_time=cx
        duration=self.video_stuff.query_duration(Gst.Format.TIME)
        if duration > 0 :
            self.ruler.set_duration(duration)
        return True


    def add_track(self,area):
        #self.box.pack_start(area,True,True,2)
        self.box.pack_start(area,False,True,2)


class VideoPositionScale(Gtk.Scale,RegularlyUpdatable):
    def __init__(self):
        adj = Gtk.Adjustment(value=0,lower=0,upper=100)
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,adjustment=adj)
        self.slider_update_signal_id = self.connect("value-changed", self.on_value_changed)
        self.video_stuff=None
        self.init_timerid_and_interval(10)
        

    def regular_update_step(self):
        if self.video_stuff.duration ==  Gst.CLOCK_TIME_NONE:
            return
        duration=self.video_stuff.query_duration(Gst.Format.TIME)
        if duration < 0 :
            return
        self.set_range(0,duration)
        current=self.video_stuff.query_position(Gst.Format.TIME)
        if current < 0:
            return
        if current > duration:
            return 
        self.handler_block(self.slider_update_signal_id)
        self.set_value(current)
        self.handler_unblock(self.slider_update_signal_id)
        return True

    def on_value_changed(self,range):
        pos_nano_sec=self.get_value()
        self.video_stuff.seek_simple(pos_nano_sec)

class VideoControllerBox(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.build_ui()
        self.video_stuff=None
        
    def build_ui(self):
        pass

    def add_button(self,iconnames,label,iconsize,event_handlers={}):
        it=Gtk.IconTheme.get_default()
        #it.list_contexts()
        #it.list_icons(context)
        button = None
        for iconname in iconnames:
            if it.has_icon(iconname):
                button=Gtk.Button.new_from_icon_name(iconname,iconsize)
                break
        if button == None:
            button = Gtk.Button.new_with_label(label)
        for k in event_handlers.keys():
            button.connect(k,event_handlers[k])            
        self.pack_start(button,False,False,0)


    def set_video_stuff(self,video_stuff):
        self.video_stuff=video_stuff

class VideoFrameStepController(VideoControllerBox):
    def __init__(self):
        super().__init__()

    def build_ui(self):
        eh={"clicked":self.on_click_previous_frame}
        self.add_button([],"-1/fps",eh)
        eh={"clicked":self.on_click_next_frame}
        self.add_button([],"+1/fps",eh)

    def on_click_next_frame(self,button):
        self.video_stuff.frame_step(1)

    def on_click_previous_frame(self,button):
        self.video_stuff.frame_step(-1)

class VideoFFController(VideoControllerBox):
    def __init__(self):
        super().__init__()
        self.set_rate(1.0)
        
        
    def build_ui(self):
        eh={"clicked":self.on_click_rew}
        il=["gtk-media-forward-rtl"]
        self.add_button(il,"FF",Gtk.IconSize.MENU,eh)
        eh={"clicked":self.on_click_ff}
        il=["gtk-media-forward-ltr"]
        self.add_button(il,"RW",Gtk.IconSize.MENU,eh)

        spinbutton = Gtk.SpinButton.new_with_range(0.1,10,0.01)
        adjustment = Gtk.Adjustment()
        adjustment.set_lower(0.1)
        adjustment.set_upper(10)
        adjustment.set_page_increment(0.1)
        adjustment.set_step_increment(0.01)
        spinbutton.set_adjustment(adjustment)
        spinbutton.set_value(1.0)
        spinbutton.connect("value-changed", self.on_value_changed)
        self.pack_start(spinbutton, False, False, 0)
        self.rate_changer=spinbutton

    def on_click_ff(self,button):
        self.video_stuff.play(self.rate)

    def on_click_rew(self,button):
        self.video_stuff.play(-self.rate)

    def on_value_changed(self, scroll):
        self.rate=scroll.get_value()

    def set_rate(self,rate):
        if rate > 0:
            self.rate=rate
            self.rate_changer.set_value(rate)

class VideoSkipController(VideoControllerBox):
    def __init__(self):
        super().__init__()
        self.set_rate(1.0)
        self.seek_amount=10*Gst.SECOND
        
    def build_ui(self):
        eh={"clicked":self.on_click_rew}
        il=["gtk-media-next-rtl"]
        self.add_button(il,"Next",Gtk.IconSize.MENU,eh)
        eh={"clicked":self.on_click_ff}
        il=["gtk-media-next-ltr"]
        self.add_button(il,"Prev",Gtk.IconSize.MENU,eh)

        spinbutton = Gtk.SpinButton.new_with_range(0.1,10,0.01)
        adjustment = Gtk.Adjustment()
        adjustment.set_lower(0.1)
        adjustment.set_upper(10)
        adjustment.set_page_increment(0.1)
        adjustment.set_step_increment(0.01)
        spinbutton.set_adjustment(adjustment)
        spinbutton.set_value(1.0)
        spinbutton.connect("value-changed", self.on_value_changed)
        self.pack_start(spinbutton, False, False, 0)
        self.rate_changer=spinbutton

    def on_click_ff(self,button):
        self.video_stuff.skip(self.rate,self.seek_amount)

    def on_click_rew(self,button):
        self.video_stuff.skip(-self.rate,self.seek_amount)

    def on_value_changed(self, scroll):
        self.rate=scroll.get_value()

    def set_rate(self,rate):
        if rate > 0:
            self.rate=rate
            self.rate_changer.set_value(rate)

class VideoController(VideoControllerBox):
    def __init__(self):
        super().__init__()
        
    def build_ui(self):
        eh={"clicked":self.on_click_start}
        il=["gtk-media-play","media-playback-start"]
        lb="Play"
        self.add_button(il,lb,Gtk.IconSize.MENU,eh)
        eh={"clicked":self.on_click_pause}
        il=["gtk-media-pause"]
        lb="Pause"
        self.add_button(il,lb,Gtk.IconSize.MENU,eh)
        eh={"clicked":self.on_click_stop}
        il=["gtk-media-stop"]
        lb="Stop"
        self.add_button(il,lb,Gtk.IconSize.MENU,eh)
        

    def on_click_start(self,button):
        self.video_stuff.play(1.0)

    def on_click_pause(self,button):
        self.video_stuff.pause()

    def on_click_stop(self,button):
        self.video_stuff.stop()


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

class VideoDrawingArea(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.video_stuff=None
        self.connect("realize", self.on_realize__area)
        self.connect("draw", self.on_draw__area)

    def on_draw__area(self, widget, cr):
        if self.video_stuff:
            if self.video_stuff.state == Gst.State.PAUSED:
                return False
            if self.video_stuff.state == Gst.State.PLAYING:
                return False
        allocation = widget.get_allocation()
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, allocation.width, allocation.height)
        cr.fill()
        return True


    def on_realize__area(self,widget):
        if not self.video_stuff:
            print("ERROR: video stuffがありませんでした。")
            return
        window = widget.get_window()
        window_handle = window.get_xid()
        self.video_stuff.attach_window(window_handle)

    def set_video_stuff(self,video_stuff):
        self.video_stuff=video_stuff
        pass




class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        maximize_action = Gio.SimpleAction.new_stateful("miximize", None, GLib.Variant.new_boolean(False))
        maximize_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(maximize_action)
        self.connect("notify::is-maximized",lambda obj, pspec: maximize_action.set_state(GLib.Variant.new_boolean(obj.props.is_maximized)),)

        action = Gio.SimpleAction.new("import_segment_track", None)
        action.connect("activate", self.on_import_segment_track)
        self.add_action(action)
        
        action = Gio.SimpleAction.new("move_current_position_to_marked_position", None)
        action.connect("activate", self.on_move_current_position_to_marked_position)
        self.add_action(action)

        action = Gio.SimpleAction.new("move_marked_position_to_current_position", None)
        action.connect("activate", self.on_move_marked_position_to_current_position)
        self.add_action(action)

        self.build_ui()
        self.set_default_size(640, 480)


    def set_video(self,uri):
        self.video_stuff.set_file(uri)
        
        
    def build_ui(self):
        video_block=Gtk.Box()
        video_block.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(video_block)
        
        self.video_stuff=GstVideoStuff()
        
        
        video_drawing_area = VideoDrawingArea()
        video_drawing_area.set_video_stuff(self.video_stuff)
        video_block.pack_start(video_drawing_area,True,True,0)
        self.video_drawing_area=video_drawing_area

        track_area=TrackArea()
        video_block.pack_start(track_area,False,True,0)
        track_area.set_video_stuff(self.video_stuff)
        self.track_area=track_area
        
        video_controller_box=Gtk.Box()
        video_controller_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        video_block.pack_start(video_controller_box,False,False,0)

        video_controller=VideoController()
        video_controller.set_video_stuff(self.video_stuff)
        video_controller_box.pack_start(video_controller,False,False,0)
        self.video_controller=video_controller

        sep=Gtk.Separator.new(orientation=Gtk.Orientation.VERTICAL)
        video_controller_box.pack_start(sep,False,False,3)
        
        vs= VideoFrameStepController()
        vs.set_video_stuff(self.video_stuff)
        video_controller_box.pack_start(vs,False,False,0)


        video_controller_box=Gtk.Box()
        video_controller_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        video_block.pack_start(video_controller_box,False,False,0)
        flag=True
        for rt in [0.5,1.0,2.0]:
            if flag:
                flag=False
            else:
                sep=Gtk.Separator.new(orientation=Gtk.Orientation.VERTICAL)
                video_controller_box.pack_start(sep,False,False,3)
            vs=VideoFFController()
            vs.set_video_stuff(self.video_stuff)
            vs.set_rate(rt)
            video_controller_box.pack_start(vs,False,False,0)

        video_controller_box=Gtk.Box()
        video_controller_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        video_block.pack_start(video_controller_box,False,False,0)
        flag=True
        for rt in [0.5,1.0,2.0]:
            if flag:
                flag=False
            else:
                sep=Gtk.Separator.new(orientation=Gtk.Orientation.VERTICAL)
                video_controller_box.pack_start(sep,False,False,3)
            vs=VideoSkipController()
            vs.set_video_stuff(self.video_stuff)
            vs.set_rate(rt)
            video_controller_box.pack_start(vs,False,False,0)
        
        vps=VideoPositionScale()
        vps.set_video_stuff(self.video_stuff)
        video_block.pack_start(vps,False,False,0)

        

    def on_maximize_toggle(self, action, value):
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()
    def on_move_marked_position_to_current_position(self, action, value):
        t=self.track_area.get_current_time()
        self.track_area.set_marked_time(t)
        
    def on_move_current_position_to_marked_position(self, action, value):
        t=self.track_area.get_marked_time()
        self.video_stuff.seek_simple(t)
        
    def on_import_segment_track(self, action, value):
        dialog = Gtk.FileChooserDialog(action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name("CSV files")
        filter.add_pattern("*.csv")
        filter.add_mime_type("text/csv")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file=dialog.get_file()
            path=file.get_path()
            dialog.destroy()        
            self.import_segment_track_from_csv(path,1,2,1)
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()



    def import_segment_track_from_csv(self,filename,start_col,duration_col,skip):
        segment_track=SegmentTrack()
        with open(filename) as file:
            for fi in file:
                if skip >0 :
                    skip=skip-1
                    continue
                data=fi.strip().split(",")
                s=self.str2nanosec_hhmmss(data[start_col])
                d=self.str2nanosec_hhmmss(data[duration_col])
                t=s+d
                segment_track.append_segment(s,t,data)
        segment_track.show()
        self.track_area.add_track(segment_track)

    def str2nanosec_hhmmss(self,data_str):
        dd = [float(i) for i in data_str.split(":")]
        s=(dd[0]*60+dd[1])*60+dd[2]
        return s*Gst.SECOND

    def import_linechart_track_from_tsv(self,filename,skip):
        track=LinechartTrack()
        with open(filename) as file:
            for fi in file:
                if skip >0 :
                    skip=skip-1
                    continue
                data=[ float(s) for s in fi.strip().split("\t")]
                time=data[0]*Gst.SECOND
                for (s,data) in enumerate(data[1:]):
                    track.append_data(time,s,data)
        track.show()
        self.track_area.add_track(track)

class AstrabeApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN|Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.add_main_option("version",ord("v"),GLib.OptionFlags.IN_MAIN,GLib.OptionArg.NONE,"version info",None)

        self.APP_NAME="Astrabe"
        self.APP_VERSION="0.0.0"
        self.APP_DESCRIPTION="A media player designed to support analysis."
        self.APP_URL="https://github.com/a175/astrabe"
        self.APP_LOGO_FILE="./icon.png"
        self.MENUBAR_XML_FILENAME = "./ui.xml"

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.build_menubar()

    def do_activate(self):
        window=MainWindow(application=self)
        window.show_all()
        window.present()

    def do_open(self,files,n_files,hint):
        window=MainWindow(application=self)
        
        print(files[0].get_path())
        print(files[0].get_uri())
        uri=files[0].get_uri()        
        window.set_video(uri)
        window.show_all()
        window.present()

        for gfile in files[1:]:
            path=gfile.get_path()
            print(path)
            if path.endswith("csv"):
                window.import_segment_track_from_csv(path,1,2,1)
            if path.endswith("txt"):
                window.import_linechart_track_from_tsv(path,0)
            
        print(hint)

    def do_command_line(self,command_line):
        options_dict = command_line.get_options_dict()
        options = options_dict.end().unpack()
        if "version" in options:
            if options["version"]:
                print(self.APP_NAME,self.APP_VERSION)
                return 0
        args = command_line.get_arguments()
        if len(args)>1:
            files=[]
            for fi in args[1:]:
                files.append(command_line.create_file_for_arg(fi))
            self.open(files,"")
            pass
    
        else:
            self.activate()
        return 0

    def build_menubar(self):
        builder = Gtk.Builder.new_from_file(self.MENUBAR_XML_FILENAME)
        menubar = builder.get_object("menubar")
        self.set_menubar(menubar)
        #self.set_app_menu(menubar)
        
        action = Gio.SimpleAction.new("new", None)
        action.connect("activate", self.on_new)
        self.add_action(action)

        action = Gio.SimpleAction.new("open", None)
        action.connect("activate", self.on_open)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("help", None)
        action.connect("activate", self.on_help)
        self.add_action(action)

    def on_quit(self,action,param):
        self.quit()
        
    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name(self.APP_NAME)
        about_dialog.set_version(self.APP_VERSION)
        about_dialog.set_website(self.APP_URL)
        about_dialog.set_comments(self.APP_DESCRIPTION)
        pixbuf=GdkPixbuf.Pixbuf.new_from_file(self.APP_LOGO_FILE)
        about_dialog.set_logo(pixbuf)
        about_dialog.present()

    def on_help(self, action, param):
        help_dialog = Gtk.MessageDialog(flags=0,buttons=Gtk.ButtonsType.OK,text="Help")
        help_dialog.format_secondary_text("See the following for help")
        link=Gtk.LinkButton.new_with_label(self.APP_URL,"link to web page")
        link.show()
        contentarea=help_dialog.get_content_area()
        contentarea.add(link)
        help_dialog.run()
        help_dialog.destroy()

    def on_new(self,action,param):
        self.activate()

    def on_open(self,action,param):
        dialog = Gtk.FileChooserDialog(action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name("MP4 files")
        filter.add_pattern("*.mp4")
        filter.add_mime_type("video/mp4")
        filter.add_mime_type("application/mp4")
        #filter.add_mime_type("audio/mp4")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("Zip files")
        filter.add_pattern("*.zip")
        filter.add_mime_type("application/zip")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file=dialog.get_file()
            self.open([file],"")
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()




def main():
    Gst.init(sys.argv)
    app = AstrabeApp()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
