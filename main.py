import os
import shutil
from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.properties import NumericProperty
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.core.text import LabelBase
from kivy.storage.jsonstore import JsonStore
from datetime import datetime, timedelta
from kivy.utils import platform
import requests
import pytz
from urllib.request import urlopen
import time
from kivy.core.image import Image as CoreImage
from io import BytesIO
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.resources import resource_find
import traceback

# android imports
if platform == "android":
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, PythonJavaClass, java_method
else:
    def run_on_ui_thread(func):
        return func

class Drag(Image):
    pass


class Drag_Text(Label):
    pass


class Drag_Image(Image):
    pass


class Drag_Number(Label):
    pass


class AppStore(JsonStore):
    pass


class My_Text1(Label):
    pass


class My_Number1(Label):
    pass


class My_Button1(Image):
    pass


class My_Arrow(Image):
    pass


class TimeHandler:

    def __init__(self):
        self.local_time = self.get_time()

    # Step 1: Retrieve UTC time from the online service
    def get_utc_time(self):
        try:
            with urlopen('http://just-the-time.appspot.com/') as response:
                utc_time_str = response.read().decode('utf-8').strip()
            return datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None  # If no internet, return None

    # Step 2: Get the user's time zone
    def get_android_timezone(self):
        try:
            # Access Android's TimeZone using pyjnius
            TimeZone = autoclass('java.util.TimeZone')
            tz_id = TimeZone.getDefault().getID()
            return pytz.timezone(tz_id)
        except:
            return None

    def get_timezone(self):
        try:
            import geocoder
            from timezonefinder import TimezoneFinder
            # Attempt GPS-based location
            g = geocoder.ip('me')  # Replace with actual GPS data if available
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=g.lng, lat=g.lat)
            if tz_name:
                return pytz.timezone(tz_name)
        except:
            try:
                # Fall back to IP-based timezone
                response = requests.get('http://ipinfo.io')
                data = response.json()
                return pytz.timezone(data['timezone'])
            except:
                # Fall back to Android timezone
                return self.get_android_timezone()

    # Step 3: Convert UTC time to local time
    def convert_to_local_time(self, utc_time, timezone):
        return utc_time.astimezone(timezone)

    # Step 4: Fallback to device settings if GPS and internet are unavailable
    def get_local_time_from_device(self):
        local_time = time.localtime()
        return datetime.fromtimestamp(time.mktime(local_time))

    # Step 5: Ensure the output is in the correct format and usable for arithmetic operations
    def get_time(self):
        utc_time = self.get_utc_time()
        user_timezone = self.get_timezone()

        if utc_time and user_timezone:
            # net time
            local_time = self.convert_to_local_time(utc_time, user_timezone)
            # + time zone
            parsed_time = local_time.strftime("%Y-%m-%d %H:%M:%S%z")
            distance = int(parsed_time[-4:-2])
            temp_time = local_time + timedelta(hours=distance)
            # and get rid of time zone format (time+timezone)
            temp_time_text = temp_time.strftime("%Y-%m-%d %H:%M:%S")
            temp_time_no_text = datetime.strptime(temp_time_text, "%Y-%m-%d %H:%M:%S")
            local_time = temp_time_no_text
            self.texts = ["Net idő", "Net time"]
        else:
            try:
                # Fallback to device settings
                local_time = self.get_local_time_from_device()
                self.texts = ["Készülék idő", "Device time"]
            except:
                local_time = None
                self.texts = ["Nincs idő", "No time"]

        # Return the local time in the desired format
        return local_time


class AirplaneModeManager:
    _initialized = False

    def __init__(self):
        if not AirplaneModeManager._initialized:
            try:
                AirplaneModeManager.Intent = autoclass('android.content.Intent')
                AirplaneModeManager.Settings = autoclass('android.provider.Settings')
                AirplaneModeManager.SettingsGlobal = autoclass('android.provider.Settings$Global')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                AirplaneModeManager.activity = PythonActivity.mActivity
                AirplaneModeManager._initialized = True
            except:
                pass

    # open android page of airplane mode settings
    def open_settings(self):
        try:
            intent = self.Intent(self.Settings.ACTION_AIRPLANE_MODE_SETTINGS)
            self.activity.startActivity(intent)
            self.texts = "Open android page"
        except:
            self.texts = "Not open settings"

    # state of airplane mode
    def is_enabled(self):
        try:
            mode = self.SettingsGlobal.getInt(
                self.activity.getContentResolver(),
                self.SettingsGlobal.AIRPLANE_MODE_ON
            )
            return mode == 1
        except:
            return None


class AudioManager:

    def __init__(self, filename="rozi_music.ogg"):
        self.filename = filename
        self.media_player = None
        self.MediaPlayer = None
        self.PythonActivity = None
        self.activity = None

        try:
            self.MediaPlayer = autoclass('android.media.MediaPlayer')
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.activity = self.PythonActivity.mActivity
        except Exception as e:
            self.show_error(f"[AudioManager Init Error] {e}")
            # Nem gond, ha desktopon fut, csak jelezzük

    def stop(self):
        # stop and initialize the play again
        try:
            # if we have Mediaplayer object, we try to stop
            if self.media_player:
                try:
                    self.media_player.stop()
                except Exception:
                    # if we do not have, it does not cause error, we ignore it
                    pass
                try:
                    self.media_player.release()
                except Exception:
                    # if we have already released or not initialized, we ignore
                    pass
                finally:
                    self.media_player = None
            else:
                # No object, nothing happens
                self.media_player = None
        except Exception as e:
            self.show_error(f"Stop error: {e}")

    def show_error(self, message):
        # Natíve Android Toast error message or print fallback.
        try:
            message = str(message)
            if platform == "android":
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                Toast = autoclass('android.widget.Toast')
                String = autoclass('java.lang.String')
                Toast.makeText(activity, String(message), Toast.LENGTH_LONG).show()
            else:
                print(message)
        except Exception as e:
            print(f"[Toast Error] {e} | Original: {message}")

    def init_player(self):
        # MediaPlayer initalize and copy file to user_data_dir
        if self.media_player:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        src = os.path.join(base_dir, "tracks", self.filename)

        if platform == "android":
            app = App.get_running_app()
            user_data_dir = app.user_data_dir
            os.makedirs(user_data_dir, exist_ok=True)
            dst = os.path.join(user_data_dir, self.filename)

            if not os.path.exists(dst):
                try:
                    if os.path.exists(src):
                        shutil.copy(src, dst)
                    else:
                        ins = self.activity.getAssets().open(f"tracks/{self.filename}")
                        with open(dst, 'wb') as out:
                            buf = bytearray(1024 * 64)
                            while True:
                                read = ins.read(buf)
                                if read <= 0:
                                    break
                                out.write(buf[:read])
                        ins.close()
                except Exception as e:
                    self.show_error(f"hiba másoláskor: {e}")
                    return
        else:
            dst = src

        try:
            self.media_player = self.MediaPlayer()
            self.media_player.setDataSource(dst)
            self.media_player.prepare()
        except Exception as e:
            self.show_error(f"Hiba ini: {e}")
            self.media_player = None

    def set_volume(self, l, r):
        # volume set up
        try:
            self.media_player.setVolume(l, r)
        except Exception as e:
            self.show_error(f"Set volume error: {e}")

    def set_loop(self):
        # loop set up
        try:
            self.media_player.setLooping(True)
        except Exception as e:
            self.show_error(f"Loop error: {e}")

    def play(self):
        # initialize and play
        try:
            self.init_player()
            if self.media_player:
                self.media_player.start()
        except Exception as e:
            self.show_error(f"Play error: {e}")

    def pause(self):
        # pause the play
        try:
            if self.media_player and self.media_player.isPlaying():
                self.media_player.pause()
        except Exception as e:
            self.show_error(f"Pause error: {e}")

    def get_length(self):
        # get back with length of the tarck
        if not self.media_player:
            return 10.0
        try:
            return self.media_player.getDuration() / 1000.0
        except Exception as e:
            self.show_error(f"Error get_length: {e}")
            return 0.0


class AndroidVideoController:

    def __init__(self, app):
        self.app = app
        # self.status_label = status_label

        self.video_path = None
        self.media_player = None
        self.surface_view = None
        self.callback = None

        self.prepare_video_safe()

    def prepare_video_safe(self):
        # prepare video
        try:
            self.video_path = self.prepare_video()
            # self.set_status(f"Video ready:\n{self.video_path}")
        except Exception as e:
            traceback.print_exc()

    def prepare_video(self):
        # put video file to proper place
        filename = "rozi_road.mp4"
        packaged_path = resource_find(filename)
        target = os.path.join(self.app.user_data_dir, filename)

        if platform == "android":
            if os.path.exists(target):
                return target

            if packaged_path:
                shutil.copy(packaged_path, target)
                return target

            raise RuntimeError("Video not found")

        if packaged_path:
            return packaged_path

        raise RuntimeError("Video not found on desktop")

    def start(self):
        # start command in the app
        if platform != "android":
            return
        self.start_android_video()

    def stop(self):
        # stop command in the app
        if platform != "android":
            return
        self.stop_android_video()

    # ---------------- ANDROID ----------------
    @run_on_ui_thread
    def mistake(self, e):
        # Natíve Android Toast error message or print fallback.
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Toast = autoclass("android.widget.Toast")
            String = autoclass("java.lang.String")

            context = PythonActivity.mActivity
            error_message = f"STOP ERROR: {str(e)}"

            Toast.makeText(
                context,
                String(error_message),
                Toast.LENGTH_LONG
            ).show()

        except Exception as toast_error:
            traceback.print_exc()

    @run_on_ui_thread
    def start_android_video(self):
        try:
            MediaPlayer = autoclass("android.media.MediaPlayer")
            SurfaceView = autoclass("android.view.SurfaceView")
            LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
            Gravity = autoclass("android.view.Gravity")
            PixelFormat = autoclass("android.graphics.PixelFormat")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity
            window = activity.getWindow()

            w, h = Window.size
            video_height = int(h * 4 / 14)
            center_y = int((h - video_height) / 1.1)

            # if it exists only we set position and start
            if self.surface_view:
                self.surface_view.setY(center_y)
                if self.media_player:
                    holder = self.surface_view.getHolder()
                    self.media_player.setDisplay(holder)  # EZ HIÁNYZOTT
                    try:
                        self.media_player.start()
                    except:
                        pass
                return

            self.surface_view = SurfaceView(activity)
            self_ctrl = self

            # callback, important: save in self.callback
            class MyCallback(PythonJavaClass):
                __javainterfaces__ = ["android/view/SurfaceHolder$Callback"]
                __javacontext__ = "app"

                @java_method("(Landroid/view/SurfaceHolder;)V")
                def surfaceCreated(self, holder):

                    def start_player(dt):
                        try:
                            # create MediaPlayer if it does not exist yet
                            if not self_ctrl.media_player:
                                mp = MediaPlayer()
                                self_ctrl.media_player = mp
                                mp.setDataSource(self_ctrl.video_path)
                                mp.setLooping(True)
                                mp.prepare()

                            # DISPLAY restart always
                            self_ctrl.media_player.setDisplay(holder)
                            self_ctrl.media_player.start()

                        except Exception:
                            traceback.print_exc()

                    Clock.schedule_once(start_player, 0)

                @java_method("(Landroid/view/SurfaceHolder;)V")
                def surfaceDestroyed(self, holder):
                    try:
                        if self_ctrl.media_player:
                            self_ctrl.media_player.pause()
                            self_ctrl.media_player.setDisplay(None)
                    except:
                        pass

                @java_method("(Landroid/view/SurfaceHolder;III)V")
                def surfaceChanged(self, holder, format, width, height):
                    pass

            self.callback = MyCallback()
            holder = self.surface_view.getHolder()
            holder.addCallback(self.callback)

            # layout parameters
            params = LayoutParams(
                w,
                video_height,
                LayoutParams.TYPE_APPLICATION_PANEL,
                LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
            )
            params.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL

            window.addContentView(self.surface_view, params)
            self.surface_view.setY(center_y)

        except Exception as e:
            traceback.print_exc()
            self.mistake(e)

    @run_on_ui_thread
    def stop_android_video(self):
        # stop the video
        w, h = Window.size

        try:
            if self.media_player:
                self.media_player.pause()
                self.media_player.setDisplay(None)
            if self.surface_view:
                self.surface_view.setY(h * 2)

        except Exception as e:
            traceback.print_exc()
            self.mistake(e)


class R0Window(Screen):
    # splash screen init
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # color ogf background
        self.color_of_bg = (219 / 255, 128 / 255, 23 / 255, 1)
        self.color_of_picture = 62 / 255, 196 / 255, 62 / 255, 1
        self.source_of_picture = "buddha2.jpg"
        self.text_of_picture1 = "The way of the hero"
        self.text_of_picture = "A hős útja"
        self.color_of_text = 0, 0, 0, 1
        self.opacity_of_text = 1
        self.timer = 0
        self.width = Window.width
        self.height = Window.height

        # background music
        self.sound100 = AudioManager(filename="rozi_music.ogg")

    def on_pre_leave(self, *args):
        # if you left with music before and this data is saved
        first_window = self.manager.get_screen("R1")
        if first_window.music_switcher == 1:
            # start music
            self.sound100.play()
            self.sound100.set_volume(0.95, 0.95)
            self.sound100.set_loop()

    def moving_the_text(self, dt):
        # stop anim
        if self.timer == 100:
            self.opacity_of_text = 1
            self.ids.picture.children[0].opacity = self.opacity_of_text
            self.timer = 0
            self.load_saved_data()
            # switch page
            Clock.schedule_once(self.go_to_next_page, 2)
            return False

        # text anim
        if 20 <= self.timer < 40:
            self.opacity_of_text -= 0.1
            self.ids.picture.children[0].opacity = self.opacity_of_text
        elif 40 <= self.timer < 60:
            self.ids.picture.children[0].text = self.text_of_picture1
            self.ids.picture.children[0].size_hint_y -= 0.0001
        elif 60 <= self.timer < 80:
            self.opacity_of_text += 0.1
            self.ids.picture.children[0].opacity = self.opacity_of_text
        # line anim
        if 10 <= self.timer <= 90:
            self.ids.line.children[0].size_hint_x = (self.timer - 10) * 0.01
        # this number spins the definition
        self.timer += 1

    def on_enter(self, *args):
        # when we enter the app, lets start moving
        Clock.schedule_interval(self.moving_the_text, 0.025)

    def go_to_next_page(self, dt):
        # step to the other page (screen)
        self.parent.transition = FadeTransition()
        self.manager.transition.duration = 0.5
        self.parent.current = "R2"

    def load_saved_data(self):

        # call the second window
        second_window = self.manager.get_screen("R2")
        first_window = self.manager.get_screen("R1")
        # load colors
        first_window.color_of_top_text = first_window.store.get("colors")["color_of_top_text"]
        first_window.color_of_top_picto = first_window.store.get("colors")["color_of_top_picto"]
        first_window.color_of_arrows = first_window.store.get("colors")["color_of_arrows"]
        first_window.color_of_bottom_button = first_window.store.get("colors")["color_of_bottom_button"]
        # COLORS
        second_window.color_of_top_text = first_window.color_of_top_text
        second_window.ids.top.children[8].color = second_window.color_of_top_text
        first_window.ids.top.children[8].color = second_window.color_of_top_text
        second_window.color_of_top_picto = first_window.color_of_top_picto
        second_window.ids.top.children[0].color = second_window.color_of_top_picto
        first_window.ids.top.children[0].color = second_window.color_of_top_picto
        second_window.ids.top.children[1].color = second_window.color_of_top_picto
        first_window.ids.top.children[1].color = second_window.color_of_top_picto
        second_window.ids.top.children[3].color = second_window.color_of_top_picto
        first_window.ids.top.children[3].color = second_window.color_of_top_picto
        second_window.ids.top.children[4].color = second_window.color_of_top_picto
        first_window.ids.top.children[4].color = second_window.color_of_top_picto
        second_window.ids.top.children[5].color = second_window.color_of_top_picto
        first_window.ids.top.children[5].color = second_window.color_of_top_picto
        second_window.ids.top.children[6].color = second_window.color_of_top_picto
        first_window.ids.top.children[6].color = second_window.color_of_top_picto
        # load gender
        first_window.voice_switcher = first_window.store.get("gender")["gender"]
        # the gender of next page to create voice
        second_window.gender = first_window.voice_switcher
        first_window.gender = first_window.voice_switcher
        # load language
        first_window.language = first_window.store.get("language")["language"]
        second_window.language = first_window.store.get("language")["language"]
        # color of numbers on second screen
        second_window.color_of_text = first_window.color_of_arrows
        for i in range(len(second_window.ids.numbers.children)):
            second_window.ids.numbers.children[i].color = second_window.color_of_text
        # arrows color of second screen
        second_window.color_of_arrows = first_window.color_of_arrows
        for i in range(0, len(second_window.ids.buttons.children) - 1, 3):
            second_window.ids.buttons.children[i].color = second_window.color_of_arrows
        # arrows color of first screen
        for i in range(0, len(first_window.ids.rows.children) - 1, 3):
            if i == 6:
                first_window.ids.rows.children[i].color = first_window.color_of_arrow
            else:
                first_window.ids.rows.children[i].color = first_window.color_of_arrows
        # color of bottom button of first and second screen
        second_window.color_of_bottom_button = first_window.color_of_bottom_button
        second_window.ids.bottom.children[-1].color = second_window.color_of_bottom_button
        first_window.ids.bottom.children[-1].color = second_window.color_of_bottom_button
        # load picto
        first_window.ids.top.children[0].source = first_window.store.get("picto")["top0"]
        first_window.ids.top.children[1].source = first_window.store.get("picto")["top1"]
        first_window.ids.top.children[2].source = first_window.store.get("picto")["top2"]
        first_window.ids.top.children[3].source = first_window.store.get("picto")["top3"]
        first_window.ids.top.children[4].opacity = first_window.store.get("picto")["top4"]
        first_window.ids.top.children[5].opacity = first_window.store.get("picto")["top5"]
        # copy pictos status
        second_window.ids.top.children[0].source = first_window.ids.top.children[0].source
        second_window.ids.top.children[1].source = first_window.ids.top.children[1].source
        second_window.ids.top.children[2].source = first_window.ids.top.children[2].source
        second_window.ids.top.children[3].source = first_window.ids.top.children[3].source
        # copy picto status of music
        second_window.ids.top.children[4].opacity = first_window.ids.top.children[4].opacity
        second_window.ids.top.children[5].opacity = first_window.ids.top.children[5].opacity
        # ends and first row text
        if first_window.language == 1:
            # english specials - ends of number and first row text
            second_window.ends_of_numbers = ['st', 'nd', 'rd', 'th']
        else:
            # hungarian specials - ends of number and first row text
            second_window.ends_of_numbers = ['. ', '. ', '. ', '. ']
        # load small_number
        first_window.small_number = first_window.store.get("small_number")["small_number"]
        # load tap_counter
        second_window.tap_counter = first_window.store.get("tap_counter")["tap_counter"]
        # small number changes according to number of selecting row
        second_window.small_number = first_window.small_number
        second_window.all_numbers_refresh_counter = int(first_window.small_number) - 1
        second_window.ids.bottom_line.children[0].text = f'{second_window.tap_counter}'
        # load first grey row
        s = len(second_window.ids.all_none.children)
        if second_window.tap_counter == 0:
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][0][first_window.language]
        elif second_window.tap_counter == len(second_window.ids.numbers.children):
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][1][first_window.language]
        else:
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][0][first_window.language]
        # load elements
        elements = first_window.store.get("elements")["elements"]
        # write it out
        for i in range(1, 110, 3):
            k = int((i - 1) / 3)
            second_window.ids.buttons.children[i].text = elements[k][1]
            second_window.ids.numbers.children[k].text = elements[k][0]
            f = second_window.text_minus_two(second_window.ids.numbers.children[k].text)
            e = int(f)
            if e > 0:
                second_window.ids.numbers.children[k].opacity = 1
            p = second_window.ids.buttons.children[i].pos_hint["center_y"]
            q = second_window.order_text_left(second_window.ids.numbers.children[k])
            second_window.ids.buttons.children[i].pos_hint = {"x": q, "center_y": p}
        # determine the text on top
        second_window.ids.top.children[-2].text = second_window.buttons[950][first_window.language][0]
        first_window.ids.top.children[-2].text = first_window.texts[200][first_window.language * 2]
        # load switchers
        self.parent.touch_sound_allow = first_window.store.get("switchers")["touch_sound_allow"]
        # first_window.airplane_switcher = first_window.store.get("switchers")["airplane_switcher"]
        first_window.music_switcher = first_window.store.get("switchers")["music_switcher"]
        first_window.color_number = first_window.store.get("switchers")["color_number"]
        # language row is setting
        first_window.ids.rows.children[8 - 1].text = first_window.texts[8][first_window.language * 2]
        # change other texts (buttons) according to language in first page
        for k in range(len(first_window.ids.rows.children) - 1, -1, -3):
            if first_window.language == 0:
                if k == 2 and self.parent.touch_sound_allow == True:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 2 and self.parent.touch_sound_allow == False:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][1]

                elif k == 11 and first_window.voice_switcher == 1:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][1]
                elif k == 11 and first_window.voice_switcher == 0:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 14 and first_window.music_switcher == 1:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][1]
                elif k == 14 and first_window.music_switcher == 0:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 17:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 20:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 23:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 26:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]
                elif k == 5:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][0]

            else:
                if k == 2 and self.parent.touch_sound_allow == True:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 2 and self.parent.touch_sound_allow == False:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][3]

                elif k == 11 and first_window.voice_switcher == 1:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][3]
                elif k == 11 and first_window.voice_switcher == 0:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 14 and first_window.music_switcher == 1:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][3]
                elif k == 14 and first_window.music_switcher == 0:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 17:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 20:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 23:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 26:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]
                elif k == 5:
                    first_window.ids.rows.children[k - 1].text = first_window.texts[k][2]

    def on_touch_down(self, touch):
        # some function on mouse are banned
        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right':
            return False


class R1Window(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # intialize the option screen
        self.bg_color = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.arrow = "r_right.png"
        self.color_of_arrow_b = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.opacity_of_arrow_b = 0.3
        # first row arrows
        self.color_of_arrow = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.opacity_of_arrow = 0.3
        # other arrows
        self.color_of_arrows = 41 / 255, 145 / 255, 43 / 255, 1
        self.opacity_of_arrows = 0.3
        # top colors
        self.color_of_top = 255 / 255, 255 / 255, 255 / 255, 255 / 255
        self.color_of_top_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_top_text = 41 / 255, 145 / 255, 43 / 255, 1
        # pictos source
        self.pictos = {11: ("r_female.png", "r_male.png"),
                       8: ('r_hun_flag.png', "r_eng_flag.png"),
                       5: ("r_plane_not.png", "r_plane.png"),
                       2: ("r_sound.png", "r_mute.png"),
                       17: ("r_music_96.png", "r_not_128.png", 'r_circle_100.png'),
                       }

        # color of top pictos
        self.color_of_top_picto = 41 / 255, 145 / 255, 43 / 255, 1

        # pos of scrolled area
        self.position_of_row = 0.42
        # position of all none button
        self.position_of_first_row = 0.993
        self.rate = 0.065
        self.label_plus = 0.005
        # used texts
        self.texts = {
            11: ("Női hang", "Férfi hang", "Female voice", "Male Voice"),
            8: ("MAGYAR (HUN)", "MAGYAR (HUN)", "ENGLISH (ANG)", "ENGLISH (ANG)"),
            5: ("Video ki", "Video be", "Video off", "Video on"),
            2: ("Érintés hangok be", "Érintés hangok ki", "Touch sound on", "Touch sound off"),
            14: ("Zene ki", "Zene be", "Music off", "Music on"),
            17: ("Rólunk", "Rólunk", "About us", "About us"),
            20: ("Repülő mód kapcs.", "Repülő mód kapcs.", "Airplane mode switch", "Airplane mode switch"),
            23: ("Net ell. idő által", "Net ell. idő által", "Net by time", "Net by time"),
            26: ("Hogyan használd", "Hogyan használd", "How to use", "How to use"),
            200: ("BEÁLLÍTÁSOK", "BEÁLLÍTÁSOK", "SETTINGS", "SETTINGS")
        }
        # color of rows text
        self.color_of_button_text = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        # color of rows button
        self.color_of_button = 255 / 255, 255 / 255, 255 / 255, 255 / 255
        # color of line below
        self.color_of_bottom_button_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        # color of bottom picto
        self.color_of_bottom_button_picto = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        # color of bottom button
        self.color_of_bottom_button = 41 / 255, 145 / 255, 43 / 255, 1
        # language button color
        self.color_of_first_button = 101 / 255, 94 / 255, 94 / 255, 255 / 255
        self.color_of_first_button_text = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.language = 0  # hun
        # they are for moving on_touch
        self.first_pos = 0
        self.previous_touch_pos = None
        # slide touch right
        self.k = -10
        self.i = -11
        self.refresh_number = 0

        # sound of button
        self.sound = SoundLoader.load('rozi_toggle_button_pixabay.wav')

        # sound of attention
        self.sound1 = SoundLoader.load('attention.wav')

        # kind of voice
        self.voice_switcher = 0
        # music switch
        self.music_switcher = 0
        # allow to press for safe only on touch definitions
        self.pressing = 0
        # color of small number
        self.color_of_small_number = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        # themes of number on the bottom
        self.small_number = "37"
        # kind of color
        self.color_number = 0
        self.colors = [(41 / 255, 145 / 255, 43 / 255, 1),
                       (198 / 255, 56 / 255, 56 / 255, 1),
                       (156 / 255, 161 / 255, 53 / 255, 1),
                       (92 / 255, 126 / 255, 206 / 255, 1)]

        # Load json store file ????!!!!!!
        self.store = AppStore("ROZI_STORE_10.json")

        # new - the loop
        self.duration = "10"
        # self.music_checker_mover = 0

        # video switch
        self.video_switcher = 0

        # video calling
        app = App.get_running_app()
        self.video = AndroidVideoController(app)

    def data_disappear(self, dt):
        # delete the widget
        self.ids.other.clear_widgets()

    def on_enter(self, *args):
        # start to check the status of airplane mode
        Clock.schedule_once(self.airplane_status_command, 1)

    def on_leave(self, *args):

        # the video is off because we leave the page
        if platform == "android":
            # change of video button text according to language (because no video anymore)
            i = 5  # self.i
            # if status on/be
            if self.video_switcher == 1:
                # change button text according to language
                if self.language == 0:
                    self.ids.rows.children[i - 1].text = self.texts[i][0]
                else:
                    self.ids.rows.children[i - 1].text = self.texts[i][2]
                # change status
                self.video_switcher = 0
                # stop the video
                self.video.stop()
        else:
            # change of video button text according to language (because no video anymore)
            i = 5  # self.i
            if self.language == 0:
                self.ids.rows.children[i - 1].text = self.texts[i][0]
            else:
                self.ids.rows.children[i - 1].text = self.texts[i][2]
            # video status on/off
            self.video_switcher = 0

        # sound pause in safety
        Clock.schedule_once(self.data_disappear, 0.1)

    def music_command(self):
        # call page 0
        _window = self.manager.get_screen("R0")
        # row arrow glittering
        self.ids.rows.children[self.i - 2].opacity = 1
        if self.music_switcher == 0:
            # change picto
            self.ids.top.children[self.i // 3 + 1].opacity = 1
            self.ids.top.children[self.i // 3].opacity = 0

            # start music
            _window.sound100.play()
            _window.sound100.set_volume(0.95, 0.95)
            _window.sound100.set_loop()

            # change music off on text
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][1]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][3]
            self.music_switcher = 1
        else:
            # change picto
            self.ids.top.children[self.i // 3 + 1].opacity = 0
            self.ids.top.children[self.i // 3].opacity = 1

            # pause music
            _window.sound100.pause()

            # change music off on text
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][0]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][2]
            self.music_switcher = 0
        # row arrow fading back and button parameters back
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def voice_command(self):
        # arrow is up
        self.ids.rows.children[self.i - 2].opacity = 1
        # voice type
        if self.voice_switcher == 0:
            self.ids.top.children[self.i // 3].source = self.pictos[self.i][1]
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][1]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][3]
            self.voice_switcher = 1
        else:
            self.ids.top.children[self.i // 3].source = self.pictos[self.i][0]
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][0]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][2]
            self.voice_switcher = 0
        # arrow is down
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def language_command(self):
        # arrow is up
        self.ids.rows.children[self.i - 2].opacity = 1
        # if no additional widget on screen
        if len(self.ids.other.children) == 0:

            # change flag picto, language button text and bottom text
            if self.language == 0:
                self.ids.top.children[-2].text = self.texts[200][2]

                self.ids.top.children[self.i // 3].source = self.pictos[self.i][1]
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][2]
                self.language = 1
            else:
                self.ids.top.children[-2].text = self.texts[200][0]
                self.ids.top.children[self.i // 3].source = self.pictos[self.i][0]
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][0]
                self.language = 0
            # change other texts (buttons)
            for k in range(len(self.ids.rows.children) - 1, -1, -3):
                if self.language == 0:
                    if k == 2 and self.parent.touch_sound_allow == True:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 2 and self.parent.touch_sound_allow == False:
                        self.ids.rows.children[k - 1].text = self.texts[k][1]
                    elif k == 5 and self.video_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][1]
                    elif k == 5 and self.video_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 11 and self.voice_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][1]
                    elif k == 11 and self.voice_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 14 and self.music_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][1]
                    elif k == 14 and self.music_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 17:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 20:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 23:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]
                    elif k == 26:
                        self.ids.rows.children[k - 1].text = self.texts[k][0]

                else:
                    if k == 2 and self.parent.touch_sound_allow == True:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 2 and self.parent.touch_sound_allow == False:
                        self.ids.rows.children[k - 1].text = self.texts[k][3]
                    elif k == 5 and self.video_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][3]
                    elif k == 5 and self.video_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 11 and self.voice_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][3]
                    elif k == 11 and self.voice_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 14 and self.music_switcher == 1:
                        self.ids.rows.children[k - 1].text = self.texts[k][3]
                    elif k == 14 and self.music_switcher == 0:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 17:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 20:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 23:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
                    elif k == 26:
                        self.ids.rows.children[k - 1].text = self.texts[k][2]
        # arrow is down
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def about_command_delay(self, dt):
        # if no additional widget and no video play
        if len(self.ids.other.children) == 0 and self.video_switcher == 0:

            try:
                # URL of the image
                img_url = "https://picsum.photos/200/300"
                # Download the image
                response = requests.get(img_url)
                img_data = response.content

                # Load the image into a CoreImage object
                image = CoreImage(BytesIO(img_data), ext="png")

                # Create an Image widget and set the texture
                img_widget = Image()
                img_widget.texture = image.texture

                # size of picture
                img_widget.size_hint = (None, None)
                img_widget.size = (Window.width * 0.35, Window.height * 0.35)

                # Add the Image widget to the layout
                self.ids.other.add_widget(img_widget)

                # Image position
                self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}
                # the widget disappears in 5 seconds
                Clock.schedule_once(self.data_disappear, 5)

            except:
                if self.language == 0:
                    text = "Ez egy meditációs program vázlata."
                else:
                    text = "It's a concept for a meditation app."
                if len(self.ids.other.children) == 0:
                    self.ids.other.add_widget(Label(text=text,
                                                    font_name="Sony",
                                                    font_size=0.04 * Window.height,
                                                    color=self.color_of_top_picto,
                                                    halign="center",
                                                    valign="middle",
                                                    text_size=(self.width * 0.9, None),
                                                    size_hint_y=None,
                                                    ))
                self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}
                Clock.schedule_once(self.data_disappear, 5)

    def about_command(self):
        # about command start
        self.ids.rows.children[self.i - 2].opacity = 1
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)
        Clock.schedule_once(self.about_command_delay, 0.5)

    def net_and_time_check_command_delay(self, dt):

        # datas
        a = TimeHandler()
        b = a.local_time
        c = b.strftime("%Y.%m.%d. %H:%M:%S")
        d = a.texts[self.language]
        text = d + "\n" + c

        # write to the screen the datas
        if len(self.ids.other.children) == 0 and self.video_switcher == 0:
            self.ids.other.add_widget(Label(text=text,
                                            font_name="Sony",
                                            font_size=0.04 * Window.height,
                                            color=self.color_of_top_picto,
                                            halign="center",
                                            valign="middle",
                                            text_size=(self.width * 0.9, None),
                                            size_hint_y=None,
                                            ))

            self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}
            Clock.schedule_once(self.data_disappear, 5)

    def net_and_time_check_command(self):
        # start to check net and time
        self.ids.rows.children[self.i - 2].opacity = 1
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)
        Clock.schedule_once(self.net_and_time_check_command_delay, 0.5)

    def use_command(self):
        # how to use command
        self.ids.rows.children[self.i - 2].opacity = 1
        if len(self.ids.other.children) == 0 and self.video_switcher == 0:
            if self.language == 0:
                self.ids.other.add_widget(Label(
                    text="A rendszer gondoskodik az utolsó beállítások mentéséről minden oldalváltáskor. Kövesd a nyilakat és húzd helyükre az elemeket a TÉMÁK oldalon.",
                    font_name="Sony",
                    font_size=0.037 * Window.height,
                    color=self.color_of_top_picto,
                    halign="center",
                    valign="middle",
                    text_size=(self.width * 0.9, None),
                    size_hint_y=None,
                    ))

            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][3]
                self.ids.other.add_widget(Label(
                    text="The system ensures your latest settings are saved on every page change. Follow the arrows and drag & drop on the THEMES page.",
                    font_name="Sony",
                    font_size=0.037 * Window.height,
                    color=self.color_of_top_picto,
                    halign="center",
                    valign="middle",
                    text_size=(self.width * 0.9, None),
                    size_hint_y=None,
                    ))

            self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}
            Clock.schedule_once(self.data_disappear, 5)
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def airplane_switch_command(self):
        # go to the android page of airplane mode
        self.ids.rows.children[self.i - 2].opacity = 1

        if len(self.ids.other.children) == 0 and self.video_switcher == 0:

            k = AirplaneModeManager()
            k.open_settings()

            self.ids.other.add_widget(
                Label(text=k.texts,
                      font_name="Sony",
                      font_size=0.04 * Window.height,
                      color=self.color_of_top_picto,
                      halign="center",
                      valign="middle",
                      text_size=(self.width * 0.9, None),
                      size_hint_y=None,
                      ))
            self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)
        Clock.schedule_once(self.data_disappear, 5)

    def airplane_status_command(self, dt):
        # airplane status checking
        k = AirplaneModeManager()
        if k.is_enabled():
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][0]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][1]
        else:
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][1]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][0]

    def touch_sound_command(self):
        # whether the touch sound is on or off
        self.ids.rows.children[self.i - 2].opacity = 1
        if self.parent.touch_sound_allow:
            self.parent.touch_sound_allow = False
            self.ids.top.children[self.i // 3].source = self.pictos[self.i][1]
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][1]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][3]
        else:
            self.parent.touch_sound_allow = True
            self.ids.top.children[self.i // 3].source = self.pictos[self.i][0]
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][0]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][2]

        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def video_command(self):
        # starting video
        self.ids.rows.children[self.i - 2].opacity = 1
        # if status off and if no additional widget on screen
        if self.video_switcher == 0 and len(self.ids.other.children) == 0:
            # change button text according to language
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][1]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][3]
            # change status
            self.video_switcher = 1

            if platform == "android":
                self.video.start()
            else:
                # now only add a label
                label = Label(
                        text="VIDEO",
                        font_name="Sony",
                        font_size=0.037 * Window.height,
                        color= (0,0,0,1),
                        halign="center",
                        valign="middle",
                        text_size=(self.width * 0.9, None),
                        size_hint_y=None,
                        height=0.25 * Window.height
                    )

                with label.canvas.before:
                    Color(*self.color_of_top_picto)
                    label.bg = Rectangle(pos=label.pos, size=label.size)

                label.bind(
                    pos=lambda *_: setattr(label.bg, "pos", label.pos),
                    size=lambda *_: setattr(label.bg, "size", label.size)
                )
                # put the label on screen
                self.ids.other.add_widget(label)
                # place of label on screen
                self.ids.other.children[0].pos_hint = {"center_x": 0.5, "center_y": 0.22}

        # if status on
        elif self.video_switcher == 1:
            # change button text according to language
            if self.language == 0:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][0]
            else:
                self.ids.rows.children[self.i - 1].text = self.texts[self.i][2]
            # change status
            self.video_switcher = 0

            if platform == "android":
                self.video.stop()
            else:
                # delete text
                Clock.schedule_once(self.data_disappear, 0)

        # arrows opacity goes back down
        Clock.schedule_once(self.rows_buttons_arrows_back, 0.25)

    def go_to_the_next_page(self, dt):
        # change page
        self.parent.transition = self.parent.style_of_transition
        self.manager.transition.duration = 0.5
        self.manager.transition.direction = "left"
        self.parent.current = "R2"

    def bottom_command_back(self):
        self.ids.bottom.children[1].opacity = 1
        # collect first screen data for second window
        self.data_collector()
        Clock.schedule_once(self.bottom_buttons_right_arrow_back, 0.25)
        Clock.schedule_once(self.go_to_the_next_page, 0.75)

    def rows_buttons_arrows_back(self, dt):
        # row arrow fading back
        self.ids.rows.children[self.i - 2].opacity = 0.3
        # button parameters back
        self.i = -10
        self.k = -11
        self.pressing = 0

    def bottom_buttons_right_arrow_back(self, dt):
        # bottom button right arrow fading back
        self.ids.bottom.children[1].opacity = 0.3
        self.pressing = 0
        self.i = -10
        self.k = -11

    def bottom_buttons_left_arrow_back(self, dt):
        # bottom button left arrow fading back
        self.ids.bottom.children[0].opacity = 0.3
        self.pressing = 0
        self.i = -10
        self.k = -11

    def bottom_command_color(self):
        # change color start
        self.ids.bottom.children[0].opacity = 1
        # collect first screen data for second window
        Clock.schedule_once(self.bottom_buttons_left_arrow_back, 0.25)

        # if no additional widget on screen
        if len(self.ids.other.children) == 0:
            Clock.schedule_once(self.change_color, 1)

    def change_color(self, dt):
        # other arrows
        self.color_number += 1
        color = self.colors[self.color_number % 4]
        # pictos color
        self.color_of_top_text = color
        self.ids.top.children[8].color = self.color_of_top_text
        self.color_of_top_picto = color
        self.ids.top.children[0].color = self.color_of_top_picto
        self.ids.top.children[1].color = self.color_of_top_picto
        self.ids.top.children[3].color = self.color_of_top_picto
        self.ids.top.children[4].color = self.color_of_top_picto
        self.ids.top.children[5].color = self.color_of_top_picto
        self.ids.top.children[6].color = self.color_of_top_picto
        self.color_of_arrows = color
        for i in range(0, len(self.ids.rows.children) - 1, 3):
            if i == 6:
                self.ids.rows.children[i].color = self.color_of_arrow
            else:
                self.ids.rows.children[i].color = self.color_of_arrows
        self.color_of_bottom_button = color
        self.ids.bottom.children[-1].color = self.color_of_bottom_button

        Clock.schedule_once(self.bottom_buttons_right_arrow_back, 0.25)

    def data_collector(self):
        # call the second window
        second_window = self.manager.get_screen("R2")
        # COLORS
        second_window.color_of_top_text = self.color_of_top_text
        second_window.ids.top.children[8].color = second_window.color_of_top_text
        second_window.color_of_top_picto = self.color_of_top_picto
        second_window.ids.top.children[0].color = second_window.color_of_top_picto
        second_window.ids.top.children[1].color = second_window.color_of_top_picto
        second_window.ids.top.children[3].color = second_window.color_of_top_picto
        second_window.ids.top.children[4].color = second_window.color_of_top_picto
        second_window.ids.top.children[5].color = second_window.color_of_top_picto
        second_window.ids.top.children[6].color = second_window.color_of_top_picto
        second_window.color_of_text = self.color_of_arrows
        for i in range(len(second_window.ids.numbers.children)):
            second_window.ids.numbers.children[i].color = second_window.color_of_text
        second_window.color_of_arrows = self.color_of_arrows
        for i in range(0, len(second_window.ids.buttons.children) - 1, 3):
            second_window.ids.buttons.children[i].color = second_window.color_of_arrows
        second_window.color_of_bottom_button = self.color_of_bottom_button
        second_window.ids.bottom.children[-1].color = second_window.color_of_bottom_button

        # save colors
        self.store.put("colors", color_of_top_text=self.color_of_top_text,
                       color_of_top_picto=self.color_of_top_picto,
                       color_of_arrows=self.color_of_arrows,
                       color_of_bottom_button=self.color_of_bottom_button)

        # copy pictos status
        second_window.ids.top.children[0].source = self.ids.top.children[0].source
        second_window.ids.top.children[1].source = self.ids.top.children[1].source
        second_window.ids.top.children[2].source = self.ids.top.children[2].source
        second_window.ids.top.children[3].source = self.ids.top.children[3].source
        # copy picto status of music
        second_window.ids.top.children[4].opacity = self.ids.top.children[4].opacity
        second_window.ids.top.children[5].opacity = self.ids.top.children[5].opacity

        # save picto
        self.store.put("picto", top0=self.ids.top.children[0].source,
                       top1=self.ids.top.children[1].source,
                       top2=self.ids.top.children[2].source,
                       top3=self.ids.top.children[3].source,
                       top4=self.ids.top.children[4].opacity,
                       top5=self.ids.top.children[5].opacity)

        # the gender of next page to create voice
        second_window.gender = self.voice_switcher

        # save gender
        self.store.put("gender", gender=self.voice_switcher)

        # language continues next page
        second_window.language = self.language

        # save language
        self.store.put("language", language=self.language)

        # ends and first row text
        if self.language == 1:
            # english specials - ends of number and first row text
            second_window.ends_of_numbers = ['st', 'nd', 'rd', 'th']
        else:
            # hungarian specials - ends of number and first row text
            second_window.ends_of_numbers = ['. ', '. ', '. ', '. ']

        # small number changes according to number of selecting row
        second_window.small_number = self.small_number
        second_window.all_numbers_refresh_counter = int(self.small_number) - 1
        second_window.ids.bottom_line.children[0].text = f'{second_window.tap_counter}'

        # save small number
        self.store.put("small_number", small_number=self.small_number)

        # save tap number
        self.store.put("tap_counter", tap_counter=second_window.tap_counter)

        # first row text collecting
        s = len(second_window.ids.all_none.children)
        if second_window.tap_counter == 0:
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][0][self.language]
        elif second_window.tap_counter == len(second_window.ids.numbers.children):
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][1][self.language]
        else:
            second_window.ids.all_none.children[s - 2].text = second_window.buttons[940][0][self.language]
        # change the texts according to language
        elements = []
        for i in range(1, 110, 3):
            text = second_window.ids.buttons.children[i].text
            for key in second_window.buttons.keys():
                if second_window.buttons[key][0] == text or \
                        second_window.buttons[key][1] == text:
                    text = second_window.buttons[key][self.language]
            k = int((i - 1) / 3)
            e = second_window.ids.numbers.children[k].text
            f = second_window.text_minus_two(e)
            g = second_window.ends_ac_lang(f)
            number = str(f) + str(g)
            elements.append((number, text))

        # save small number
        self.store.put("elements", elements=elements)

        # write it out
        for i in range(1, 110, 3):
            k = int((i - 1) / 3)
            second_window.ids.buttons.children[i].text = elements[k][1]
            second_window.ids.numbers.children[k].text = elements[k][0]
            p = second_window.ids.buttons.children[i].pos_hint["center_y"]
            q = second_window.order_text_left(second_window.ids.numbers.children[k])
            second_window.ids.buttons.children[i].pos_hint = {"x": q, "center_y": p}

        # determine the text on top
        second_window.ids.top.children[-2].text = second_window.buttons[950][self.language][0]

        # save switchers
        self.store.put("switchers", touch_sound_allow=self.parent.touch_sound_allow,
                       # airplane_switcher=self.airplane_switcher,
                       music_switcher=self.music_switcher,
                       color_number=self.color_number % 4)

    def on_touch_down(self, touch):

        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right' or self.pressing == 1:
            return False
        # put the touch pos the first
        self.previous_touch_pos = touch.pos
        # no touch the button - default
        self.i = -11
        # get a value to touching in order to check it on_touch_up - swipe
        for k in range(len(self.ids.rows.children) - 1, -1, -3):
            if self.ids.rows.children[k].collide_point(*touch.pos):
                self.first_pos = touch.pos[0]
                self.k = k
        # get a value to touching in order to check it on_touch_up - swipe
        for k in range(len(self.ids.bottom.children) - 1, -1, -3):
            if self.ids.bottom.children[k].collide_point(*touch.pos):
                self.first_pos = touch.pos[0]
                self.k = k

    def on_touch_up(self, touch):

        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right' or self.pressing == 1:
            return False

        # check what button of options is released
        for i in range(len(self.ids.rows.children) - 1, -1, -3):
            if self.ids.rows.children[i].collide_point(*touch.pos):
                self.i = i
                if self.i == self.k:
                    if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                        self.pressing = 1
                        if i == 14:
                            self.music_command()
                        elif i == 11:
                            self.voice_command()
                        elif i == 8:
                            self.language_command()
                        elif i == 5:
                            pass
                            # self.airplane_status_command()
                            self.video_command()
                        elif i == 2:
                            self.touch_sound_command()
                        elif i == 17:
                            self.about_command()
                        elif i == 20:
                            self.airplane_switch_command()
                        elif i == 23:
                            self.net_and_time_check_command()
                        elif i == 26:
                            self.use_command()
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()

        # check what bottom button is released
        for i in range(len(self.ids.bottom.children) - 1, -1, -3):
            if self.ids.bottom.children[i].collide_point(*touch.pos):
                self.i = i
                if self.i == self.k:
                    if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                        self.pressing = 1
                        # change self.i earlier because it could be confused in rows_buttons_arrows_back
                        self.i = 1
                        self.data_collector()
                        self.bottom_command_back()
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()

                    elif self.first_pos - Window.width * 0.05 > touch.pos[0]:
                        self.bottom_command_color()
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()

    def on_touch_move(self, touch):
        # some function on mouse are banned
        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right' or self.pressing == 1:
            return False


class R2Window(Screen):
    # the page of track list (open page)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # number of theme
        self.tap_counter = 0
        # first number pos on the first button
        self.position_of_first_number = 0.929
        # numbers color
        self.color_of_text = 41 / 255, 145 / 255, 43 / 255, 1
        # pos of scrolled area
        self.position_of_row = 0.42
        # position of all none button
        self.position_of_first_row = 0.993  # 0.982
        # rate between themes buttons
        self.rate = 0.065
        # all / none button color
        self.color_of_first_button = 101 / 255, 94 / 255, 94 / 255, 255 / 255
        self.color_of_first_button_text = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        # themes button color
        self.color_of_button = 255 / 255, 255 / 255, 255 / 255, 255 / 255
        self.color_of_button_text = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        # button texts
        self.buttons = {
            1: ['Életcél        ', 'Purpose of life'],
            4: ['Elvonás        ', 'Withdraw       '],
            7: ['Fú             ', 'Weed           '],
            10: ['Alkohol        ', 'Alcohol        '],
            13: ['Dohányzás      ', 'Smoke          '],
            16: ['Intimitás      ', 'Intimacy       '],
            19: ['Mohóság        ', 'Greed          '],
            22: ['Perfekcionizmus', 'Perfectionism  '],
            25: ['Álmodozás      ', 'Dreaming       '],
            28: ['Unalom         ', 'Bore           '],
            31: ['Erő            ', "Power          "],
            34: ['Pénz           ', 'Money          '],
            37: ['Siker          ', 'Success        '],
            40: ['Lehetőségek    ', 'Opportunities  '],
            43: ['Egyedüllét     ', 'Boring         '],
            46: ['Alázat         ', 'Humble         '],
            49: ['Elégedettség   ', 'Satisfaction   '],
            52: ['Derű           ', 'Serenity       '],
            55: ['Rend           ', 'Order          '],
            58: ['Bosszankodás   ', 'Annoyance      '],
            61: ['Külvilág       ', 'Outside        '],
            64: ['Kommunikáció   ', 'Communication  '],
            67: ['Megbocsátás    ', 'Forgive        '],
            70: ['Harag          ', 'Rage           '],
            73: ['Ítélkezés      ', 'Judgement      '],
            76: ['Elengedés      ', 'Release        '],
            79: ['Munka          ', 'Job            '],
            82: ['Cselekvés      ', 'Action         '],
            85: ['Határok        ', 'Limits         '],
            88: ['Szükségletek   ', 'Needs          '],
            91: ['Félelem        ', 'Fear           '],
            94: ['Szégyen        ', 'Shame          '],
            97: ["Bűntudat       ", "Remorse        "],
            100: ['Érzések        ', 'Feelings       '],
            103: ['Jövőkép        ', 'Future vision  '],
            106: ['Önszeretet     ', 'Self-love      '],
            109: ['Meditáció      ', 'Meditation     '],
            940: [["MIND           ", "ALL            "],
                  ["EGYSEM         ", "NONE           "]],
            950: [["TÉMÁK", "TÉMÁK"], ["THEMES", "THEMES"]]}
        # background color of bg label
        self.bg_color = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        # arrows source
        self.arrow = "r_right.png"
        # bottom button
        self.color_of_arrow_b = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.opacity_of_arrow_b = 0.3
        # first row arrows
        self.color_of_arrow = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.opacity_of_arrow = 0.3
        # other arrows
        self.color_of_arrows = 41 / 255, 145 / 255, 43 / 255, 1
        self.opacity_of_arrows = 0.3
        # color of top picto lone
        self.color_of_top = 255 / 255, 255 / 255, 255 / 255, 255 / 255
        self.color_of_top_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_top_text = 41 / 255, 145 / 255, 43 / 255, 1
        # pictos source
        self.pictos = {11: ("r_female.png", "r_male.png"),
                       8: ('r_hun_flag.png', "r_eng_flag.png"),
                       5: ("r_plane_not.png", "r_plane.png"),
                       2: ("r_sound.png", "r_mute.png"),
                       17: ("r_music_96.png", "r_not_128.png", 'r_circle_100.png'),
                       }

        # pictos color
        self.color_of_top_picto = 41 / 255, 145 / 255, 43 / 255, 1
        # color of bottom line
        self.color_of_bottom_button_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_bottom_button_text = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_bottom_button = 41 / 255, 145 / 255, 43 / 255, 1
        self.color_of_bottom_picto = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        # female 0 or male 1
        self.gender = 0
        # language type
        self.language = 0
        # slide touch right
        self.first_pos = None
        self.previous_touch_pos = None
        self.first_touch_pos = None
        # slide touch right
        self.k = -10
        self.i = -11

        # sound
        self.sound = SoundLoader.load('rozi_toggle_button_pixabay.wav')
        # sound of attention
        self.sound1 = SoundLoader.load('attention.wav')

        # allowing buttons press
        self.pressing = 0
        # small writes on bottom button
        self.color_of_small_number = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.small_number = f'{self.tap_counter}'
        # the ends of the numbers according to language
        self.ends_of_numbers = ['. ', '. ', '. ', '. ']
        # heritage self_i because self_i is changing meanwhile we handle with the price of self_i
        self.heritage_of_self_i = -1
        # number in numbers manager and numbers_manager_order_changing
        self.border_of_number = 0
        # make the text flashing
        self.text_flash_number = 0
        # change_and_refresh_all_numbers
        self.all_numbers_refresh_counter = int(self.small_number) - 1
        self.pressing = 0
        self.row = []
        # drag and drop attributes
        self.dragged = True
        self.drag_counter = 0
        self.dragging = False
        self.drag_first_position = None
        self.selected_button_color = 0, 1, 1, 1
        self.z = 0
        self.drag_and_drop_scroll = True

    def on_leave(self, *args):

        # call first screen because the store is found there
        first_window = self.manager.get_screen("R1")
        # change the texts according to language
        elements = []
        for i in range(1, 110, 3):
            text = self.ids.buttons.children[i].text
            for key in self.buttons.keys():
                if self.buttons[key][0] == text or \
                        self.buttons[key][1] == text:
                    text = self.buttons[key][self.language]
            k = int((i - 1) / 3)
            e = self.ids.numbers.children[k].text
            f = self.text_minus_two(e)
            g = self.ends_ac_lang(f)
            number = str(f) + str(g)
            elements.append((number, text))

        # save small number
        first_window.store.put("elements", elements=elements)

        # save tap number
        first_window.store.put("tap_counter", tap_counter=self.tap_counter)

    def airplane_status_command(self, dt):

        # it is needed if there was no save at the previous quit (e.g. quit from the first page)
        first_window = self.manager.get_screen("R1")

        # airplane status checker
        k = AirplaneModeManager()
        # whether airplane mode is on/off
        if k.is_enabled():
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][0]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][1]
            first_window.ids.top.children[1].source = self.pictos[5][1]
        else:
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][1]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][0]
            first_window.ids.top.children[1].source = self.pictos[5][0]

    def on_enter(self, *args):
        # when the screen is open, check the status
        Clock.schedule_once(self.airplane_status_command, 1)

    def order_text_left(self, label):
        # fix the text with a label simulation
        x = 0.05
        text = label.text
        AdaptiveLabel = Label(
            text=text,
            font_size=0.04 * Window.height,
            font_name="Sony",
            size_hint=(None, None)
        )
        AdaptiveLabel.texture_update()
        AdaptiveLabel.width = AdaptiveLabel.texture_size[0]
        # And then, AdaptiveLabel.size is the size of text in pixel
        y = round(AdaptiveLabel.size[0] / Window.width, 3)
        if label.opacity == 0:
            x = 0.05
        else:
            if text[-1] == " ":
                x = 0.05 + y + 0.016
            else:
                x = 0.05 + y + 0.018
        return x

    def text_minus_two(self, text):
        # cut the end of the text
        return text[:-2]

    def ends_ac_lang(self, n):
        # st, nd, rd, etc...
        if str(n)[-1] == '1' and str(n) != '11':
            k = self.ends_of_numbers[0]
        elif str(n)[-1] == '2' and str(n) != '12':
            k = self.ends_of_numbers[1]
        elif str(n)[-1] == '3' and str(n) != '13':
            k = self.ends_of_numbers[2]
        else:
            k = self.ends_of_numbers[3]
        return k

    def text_flashing(self, dt):
        # if no track selected, the number of 0 is flashing
        if self.text_flash_number == 10:
            self.text_flash_number = 0
            return False
        if self.text_flash_number % 2 == 0:
            self.ids.bottom_line.children[0].opacity = 0
        else:
            self.ids.bottom_line.children[0].opacity = 1
        self.text_flash_number += 1

    def flash_up(self):
        # arrow bright
        if self.heritage_of_self_i == 200:
            self.ids.bottom.children[0].opacity = 1
        elif self.heritage_of_self_i == 100:
            self.ids.bottom.children[1].opacity = 1
        elif self.heritage_of_self_i == 300:
            self.ids.all_none.children[0].opacity = 1
        else:
            self.ids.buttons.children[self.heritage_of_self_i - 2].opacity = 1
        Clock.schedule_once(self.flash_down, 0.25)

    def flash_down(self, dt):
        # arrow fade
        if self.heritage_of_self_i == 200:
            self.ids.bottom.children[0].opacity = 0.3
        elif self.heritage_of_self_i == 100:
            self.ids.bottom.children[1].opacity = 0.3
        elif self.heritage_of_self_i == 300:
            self.ids.all_none.children[0].opacity = 0.3
        else:
            self.ids.buttons.children[self.heritage_of_self_i - 2].opacity = 0.3

    def data_collector(self):
        # all needed data written to next (3) player screen -
        # call the third window
        third_window = self.manager.get_screen("R3")
        # color
        third_window.color_of_top_text = self.color_of_top_text
        third_window.ids.top.children[8].color = third_window.color_of_top_text
        third_window.color_of_top_picto = self.color_of_top_picto
        third_window.ids.top.children[0].color = third_window.color_of_top_picto
        third_window.ids.top.children[1].color = third_window.color_of_top_picto
        third_window.ids.top.children[3].color = third_window.color_of_top_picto
        third_window.ids.top.children[4].color = third_window.color_of_top_picto
        third_window.ids.top.children[5].color = third_window.color_of_top_picto
        third_window.ids.top.children[6].color = third_window.color_of_top_picto
        third_window.color_of_bottom_button = self.color_of_bottom_button
        third_window.ids.bottom.children[-1].color = third_window.color_of_bottom_button

        # copy pictos status
        third_window.ids.top.children[0].source = self.ids.top.children[0].source
        third_window.ids.top.children[1].source = self.ids.top.children[1].source
        third_window.ids.top.children[2].source = self.ids.top.children[2].source
        third_window.ids.top.children[3].source = self.ids.top.children[3].source
        # copy picto status of music
        third_window.ids.top.children[4].opacity = self.ids.top.children[4].opacity
        third_window.ids.top.children[5].opacity = self.ids.top.children[5].opacity
        # female 0 or male 1
        third_window.gender = self.gender
        # language clone
        third_window.language = self.language
        # pos of scrolled area
        third_window.position_of_row = 0.42
        third_window.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": third_window.position_of_row}
        third_window.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": third_window.position_of_row}
        third_window.ids.signs.pos_hint = {"center_x": 0.5, "center_y": third_window.position_of_row}
        third_window.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": third_window.position_of_row}
        third_window.ids.times.pos_hint = {"center_x": 0.5, "center_y": third_window.position_of_row}
        # tap counter
        third_window.tap_counter = self.tap_counter
        third_window.small_number = self.small_number
        third_window.ids.bottom_line.children[0].text = f"{third_window.tap_counter}"
        # collect the selected rows for second screen
        e = {}
        for i in range(0, len(self.ids.numbers.children)):
            a = self.ids.numbers.children[i].text
            b = self.text_minus_two(a)
            d = self.ids.numbers.children[i].text[len(self.ids.numbers.children[i].text) - 2:]
            c = int(b)
            if c != 0:
                e[c] = d, self.ids.buttons.children[i * 3 + 1].text
        # selected rows appear on the second screen in order
        pos = third_window.position_of_first_row - self.rate
        for i in range(1, len(e) + 1):
            third_window_button = My_Button1()
            third_window_button.pos_hint = {"center_x": 0.5, "center_y": pos}
            third_window.ids.buttons.add_widget(third_window_button)

            # in case of Label we need this mode to add the parameters else it will not be appeared
            third_window_number = My_Number1(font_name="Sony",
                                             opacity=1,
                                             text=str(i) + str(e[i][0]),
                                             font_size=0.04 * Window.height,
                                             color=self.color_of_text,
                                             pos_hint={"x": 0.05, "center_y": pos + 0.005})
            third_window.ids.numbers.add_widget(third_window_number)
            # and in case of using ttf  we need this mode to add the parameters else it will not be appeared
            cs = self.order_text_left(third_window_number)

            third_window_text = My_Text1(opacity=1,
                                         font_name="Sony",
                                         text=str(e[i][1]),
                                         font_size=0.04 * Window.height,
                                         pos_hint={"x": cs, "center_y": pos + 0.005},
                                         color=(0 / 255, 0 / 255, 0 / 255, 255 / 255))
            third_window.ids.buttons.add_widget(third_window_text)

            third_window_arrow = My_Arrow()
            third_window.ids.signs.add_widget(third_window_arrow)
            third_window.ids.signs.children[0].pos_hint = {"center_x": 0.95, "center_y": pos}
            third_window.ids.signs.children[0].color = self.color_of_arrows

            pos -= self.rate

        # change the first button color
        third_window.ids.buttons.children[-1].color = 219 / 255, 128 / 255, 23 / 255, 1
        # change the first button arrow color
        third_window.ids.signs.children[-1].color = third_window.color_of_arrow_b
        # change first row text
        third_window.ids.shuffle_row.children[-2].text = third_window.buttons[940][0][self.language]
        # switcher always start 0
        third_window.play_or_stop_switcher = 0
        # change top row text
        third_window.ids.top.children[-2].text = third_window.buttons[950][0][self.language]

    def back_to_the_previous_page(self, dt):
        # go back to page 1
        self.parent.transition = self.parent.style_of_transition
        self.manager.transition.duration = 0.5
        self.manager.transition.direction = "right"
        self.parent.current = "R1"

    def go_to_the_next_page(self, dt):
        # go to the page 3 (player)
        self.parent.transition = self.parent.style_of_transition
        self.manager.transition.duration = 0.5
        self.manager.transition.direction = "left"
        self.parent.current = "R3"

    def bottom_command(self):
        # bottom button possibilities - back screen or next screen if number of tracks is not 0
        self.parent.transition = self.parent.style_of_transition
        self.manager.transition.duration = 1
        if self.heritage_of_self_i == 200:
            Clock.schedule_once(self.back_to_the_previous_page, 0.75)
        else:
            if self.tap_counter == 0:
                Clock.schedule_interval(self.text_flashing, 0.2)
            else:
                self.data_collector()
                Clock.schedule_once(self.go_to_the_next_page, 1)

    def change_and_refresh_numbers(self, dt):
        # refresh all rows
        if self.all_numbers_refresh_counter == - 1:
            # counter max again
            self.all_numbers_refresh_counter = int(self.small_number) - 1
            # refresh small number
            self.ids.bottom_line.children[0].text = f'{self.tap_counter}'
            # self.ids.bottom_line.children[0].size_hint_y += 0.0001
            # allow touch screen
            self.pressing = 0
            # stop def
            self.heritage_of_self_i = -1
            return False
        i = self.all_numbers_refresh_counter * 3 + 1
        pair = self.row[self.all_numbers_refresh_counter]
        g1 = pair[0]
        if g1 != 0:
            self.ids.numbers.children[self.all_numbers_refresh_counter].opacity = 1
        else:
            self.ids.numbers.children[self.all_numbers_refresh_counter].opacity = 0
        g = self.ends_ac_lang(g1)
        f = pair[1]
        self.ids.numbers.children[self.all_numbers_refresh_counter].text = str(g1) + g
        self.ids.buttons.children[i].text = str(f)
        p = self.ids.buttons.children[i].pos_hint["center_y"]
        q = self.order_text_left(self.ids.numbers.children[self.all_numbers_refresh_counter])
        self.ids.buttons.children[i].pos_hint = {"x": q, "center_y": p}
        self.all_numbers_refresh_counter -= 1

    def ordering_rows(self):
        # rows are put in proper order
        temporary_row_00 = []
        temporary_row_num = []
        for k in range(len(self.ids.numbers.children) - 1, -1, -1):
            i = k * 3 + 1
            e = int(self.text_minus_two(self.ids.numbers.children[k].text))
            if e == 0:
                temporary_row_00.append(self.ids.buttons.children[i].text)
            else:
                temporary_row_num.append([e, self.ids.buttons.children[i].text])
        temporary_row_num.sort(key=lambda x: x[0])
        temporary_row_0 = []
        for key in self.buttons.keys():
            if self.buttons[key][self.language] in temporary_row_00:
                temporary_row_0.insert(0, [0, self.buttons[key][self.language]])
        self.row = []
        self.row = temporary_row_num + temporary_row_0
        self.row.reverse()
        Clock.schedule_interval(self.change_and_refresh_numbers, 0.01)

    def numbers_manager(self):
        # no tap while processing
        self.pressing = 1
        # place of the number in numbers
        k = int(((self.heritage_of_self_i - 2) / 3))
        e = int(self.text_minus_two(self.ids.numbers.children[k].text))
        # one number + 1
        if e == 0:
            self.tap_counter += 1
            self.ids.numbers.children[k].opacity = 0
            self.ids.numbers.children[k].text = \
                str(self.tap_counter) + self.ends_ac_lang(self.tap_counter)
        # one number becomes 0
        elif e != 0:
            selected_number = e
            self.tap_counter -= 1
            self.ids.numbers.children[k].opacity = 0
            self.ids.numbers.children[k].text = \
                str(0) + self.ends_ac_lang(str(0))
            # numbers without 0 withdraw by - 1
            for t in range(len(self.ids.numbers.children) - 1, -1, -1):
                f = int(self.text_minus_two(self.ids.numbers.children[t].text))
                if f != 0:
                    if f > selected_number:
                        new_num = f
                        new_num = new_num - 1
                        self.ids.numbers.children[t].text = \
                            str(new_num) + self.ends_ac_lang(str(new_num))
        # first row text is changing
        s = len(self.ids.all_none.children)
        if self.tap_counter == int(self.small_number):
            self.ids.all_none.children[s - 2].text = self.buttons[940][1][self.language]
        else:
            self.ids.all_none.children[s - 2].text = self.buttons[940][0][self.language]
        # order the rows
        self.ordering_rows()

    def change_all_numbers(self):
        # in case of 0 the number plus 1 and +1 and +1 .....
        for k in range(len(self.ids.numbers.children) - 1, -1, -1):
            i = k * 3 + 1
            e = int(self.text_minus_two(self.ids.numbers.children[k].text))
            if e == 0:
                self.tap_counter += 1
                self.ids.numbers.children[k].text = \
                    str(self.tap_counter) + self.ends_ac_lang(self.tap_counter)
                p = self.ids.buttons.children[i].pos_hint["center_y"]
                self.ids.numbers.children[k].opacity = 1
                q = self.order_text_left(self.ids.numbers.children[k])
                self.ids.buttons.children[i].pos_hint = {"x": q, "center_y": p}
        # order the rows
        self.ordering_rows()

    def change_none_numbers(self):
        # no numbers only 0's
        self.tap_counter = 0
        new_num = self.tap_counter
        for k in range(len(self.ids.numbers.children) - 1, -1, - 1):
            i = k * 3 + 1
            e = int(self.text_minus_two(self.ids.numbers.children[k].text))
            if e != 0:
                self.ids.numbers.children[k].opacity = 0
                self.ids.numbers.children[k].text = \
                    str(0) + self.ends_ac_lang(new_num)
                p = self.ids.buttons.children[i].pos_hint["center_y"]
                self.ids.numbers.children[k].opacity = 1
                q = self.order_text_left(self.ids.numbers.children[k])
                self.ids.buttons.children[i].pos_hint = {"x": q, "center_y": p}
        # order the rows
        self.ordering_rows()

    def all_none_numbers_command(self):
        # no tap while processing
        self.pressing = 1

        # change first row text
        if self.tap_counter != len(self.ids.numbers.children):
            # refresh first row text
            s = len(self.ids.all_none.children)
            self.ids.all_none.children[s - 2].text = self.buttons[940][1][self.language]
            # change elements
            self.change_all_numbers()
        else:
            s = len(self.ids.all_none.children)
            # refresh first row
            self.ids.all_none.children[s - 2].text = self.buttons[940][0][self.language]
            # change elements
            self.change_none_numbers()

    def able_to_drag(self, dt):
        # we are doing the drag process
        if self.drag_counter == 15:
            self.dragging = True
            self.drag_counter = 0
            Clock.schedule_once(self.create_or_not_clone, 0.1)
            return False
        # we are interrupting the drag process
        if self.dragged:
            self.drag_counter = 0
            Clock.schedule_once(self.create_or_not_clone, 0.1)
            return False

        # changing the color of button as we approch the drag process
        if self.drag_counter > 7:
            k = [0.9, 0.75, 0.60, 0.45, 0.30, 0.15, 0]
            n = k[self.drag_counter - 8]
            self.ids.buttons.children[self.k].color = n, 1, 1, 1

        self.drag_counter += 1

    def create_or_not_clone(self, dt):
        # create clone and dragging
        if self.dragging:
            a = self.ids.buttons.children[self.k].pos_hint["center_x"]
            b = self.ids.buttons.children[self.k - 1].pos_hint["x"]
            c = self.ids.buttons.children[self.k - 2].pos_hint["center_x"]
            d = self.ids.numbers.children[(self.k // 3)].pos_hint["x"]

            self.ids.temporary.add_widget(Drag(size_hint_y=0.07))
            self.ids.temporary.add_widget(Drag_Text(text=self.ids.buttons.children[self.k - 1].text,
                                                    font_size=0.04 * Window.height))
            self.ids.temporary.add_widget(Drag_Image(color=self.color_of_top_picto,
                                                     opacity=0))
            self.ids.temporary.add_widget(Drag_Number(text=self.ids.numbers.children[(self.k // 3)].text,
                                                      font_size=0.04 * Window.height,
                                                      color=self.color_of_top_picto))

            self.ids.temporary.children[3].pos_hint = {"center_x": a, "center_y": self.drag_first_position}
            self.ids.temporary.children[2].pos_hint = {"x": b, "center_y": self.drag_first_position}
            self.ids.temporary.children[1].pos_hint = {"center_x": c, "center_y": self.drag_first_position}
            self.ids.temporary.children[0].pos_hint = {"x": d, "center_y": self.drag_first_position}

            self.ids.buttons.remove_widget(self.ids.buttons.children[self.k])
            self.ids.buttons.remove_widget(self.ids.buttons.children[self.k - 1])
            self.ids.buttons.remove_widget(self.ids.buttons.children[self.k - 2])
            self.ids.numbers.remove_widget(self.ids.numbers.children[(self.k // 3)])
        # no clone and the color changing back to default in all case
        elif not self.dragging:
            self.ids.buttons.children[self.heritage_of_self_i].color = self.color_of_button

    def selected_button_color_back(self, dt):
        # when button is released the color changes back
        self.ids.buttons.children[self.z].color = self.color_of_button

    def drop_the_drag(self, places, a, b, c, d):
        #  if no two touches go back to default place
        z = 0
        if len(places) == 1 or len(places) == 2:

            if places[0] == len(self.ids.buttons.children) + 2:
                temp = places[0] - 3
                e = self.ids.buttons.children[temp].pos_hint["center_y"] + self.rate
            else:
                temp = places[0]
                e = self.ids.buttons.children[temp].pos_hint["center_y"] - self.rate

            self.ids.temporary.children[3].pos_hint = {"center_x": a, "center_y": e}
            self.ids.temporary.children[2].pos_hint = {"x": b, "center_y": e}
            self.ids.temporary.children[1].pos_hint = {"center_x": c, "center_y": e}
            self.ids.temporary.children[0].pos_hint = {"x": d, "center_y": e}

            # temporary texts to clone back
            text1 = self.ids.temporary.children[2].text
            text2 = self.ids.temporary.children[0].text

            # create clones back
            first_drag = Drag(color=self.selected_button_color,
                              size_hint_y=0.06,
                              pos_hint={"center_x": a, "center_y": e})
            second_drag = Drag_Text(text=text1, font_size=0.04 * Window.height,
                                    pos_hint={"x": b, "center_y": e})
            third_drag = Drag_Image(opacity=0.3, pos_hint={"center_x": c, "center_y": e},
                                    color=self.color_of_top_picto)
            fourth_drag = Drag_Number(text=text2, font_size=0.04 * Window.height,
                                      pos_hint={"x": d, "center_y": e},
                                      color=self.color_of_top_picto)
            # appear and pos the clones in kivy file
            z = places[0] - 2
            zizi = places[0] // 3
            self.ids.buttons.add_widget(first_drag, index=z)
            self.ids.buttons.add_widget(second_drag, index=z)
            self.ids.buttons.add_widget(third_drag, index=z)
            self.ids.numbers.add_widget(fourth_drag, index=zizi)

        # if we come with the clone from up to down
        elif places[0] > places[2]:

            e = self.ids.buttons.children[places[2]].pos_hint["center_y"]

            # the buttons go up
            for n in range(places[2], places[0], 3):
                e += self.rate
                self.ids.buttons.children[n].pos_hint = {"center_x": a, "center_y": e}
                self.ids.buttons.children[n - 1].pos_hint = {"x": b, "center_y": e}
                self.ids.buttons.children[n - 2].pos_hint = {"center_x": c, "center_y": e}
                self.ids.numbers.children[n // 3].pos_hint = {"x": d, "center_y": e}

                g = int(self.text_minus_two(self.ids.numbers.children[n // 3].text))
                g -= 1
                self.ids.numbers.children[n // 3].text = str(g) + str(self.ends_ac_lang(g))

            # change the number of temporary
            j = int(self.text_minus_two(self.ids.temporary.children[0].text))
            j += ((places[0] - places[1]) // 3) - 1
            self.ids.temporary.children[0].text = str(j) + str(self.ends_ac_lang(j))

            # temporary goes to the proper place
            e = self.ids.buttons.children[places[1]].pos_hint["center_y"] - self.rate / 4
            self.ids.temporary.children[3].pos_hint = {"center_x": a, "center_y": e}
            self.ids.temporary.children[2].pos_hint = {"x": b, "center_y": e}
            self.ids.temporary.children[1].pos_hint = {"center_x": c, "center_y": e}
            self.ids.temporary.children[0].pos_hint = {"x": d, "center_y": e}

            # temporary texts to clone back
            text1 = self.ids.temporary.children[2].text
            text2 = self.ids.temporary.children[0].text

            e = self.ids.temporary.children[3].pos_hint["center_y"] + self.rate * 1.25
            # create clones back
            first_drag = Drag(color=self.selected_button_color,
                              size_hint_y=0.06,
                              pos_hint={"center_x": a, "center_y": e})
            second_drag = Drag_Text(text=text1, font_size=0.04 * Window.height,
                                    pos_hint={"x": b, "center_y": e})
            third_drag = Drag_Image(opacity=0.3, pos_hint={"center_x": c, "center_y": e},
                                    color=self.color_of_top_picto)
            fourth_drag = Drag_Number(text=text2, font_size=0.04 * Window.height,
                                      pos_hint={"x": d, "center_y": e},
                                      color=self.color_of_top_picto)
            # appear and pos the clones back in kivy file
            z = places[2] - 2
            zizi = places[2] // 3
            self.ids.buttons.add_widget(first_drag, index=z)
            self.ids.buttons.add_widget(second_drag, index=z)
            self.ids.buttons.add_widget(third_drag, index=z)
            self.ids.numbers.add_widget(fourth_drag, index=zizi)

        # if we come with the clone from down to up
        elif places[0] < places[2]:

            e = self.ids.buttons.children[places[0] - 3].pos_hint["center_y"]
            g = int(self.text_minus_two(self.ids.temporary.children[0].text))
            # the buttons go up
            for n in range(places[0], places[2], 3):
                e += self.rate

                self.ids.buttons.children[n].pos_hint = {"center_x": a, "center_y": e}
                self.ids.buttons.children[n - 1].pos_hint = {"x": b, "center_y": e}
                self.ids.buttons.children[n - 2].pos_hint = {"center_x": c, "center_y": e}
                self.ids.numbers.children[n // 3].pos_hint = {"x": d, "center_y": e}

                self.ids.numbers.children[n // 3].text = str(g) + str(self.ends_ac_lang(g))
                g -= 1

            # change the number of temporary
            j = int(self.text_minus_two(self.ids.temporary.children[0].text))
            j -= ((places[1] - places[0]) // 3) + 1
            self.ids.temporary.children[0].text = str(j) + str(self.ends_ac_lang(j))
            # temporary goes to the proper place
            e = self.ids.buttons.children[places[1]].pos_hint["center_y"] - self.rate / 4
            self.ids.temporary.children[3].pos_hint = {"center_x": a, "center_y": e}
            self.ids.temporary.children[2].pos_hint = {"x": b, "center_y": e}
            self.ids.temporary.children[1].pos_hint = {"center_x": c, "center_y": e}
            self.ids.temporary.children[0].pos_hint = {"x": d, "center_y": e}

            # temporary texts to clone back
            text1 = self.ids.temporary.children[2].text
            text2 = self.ids.temporary.children[0].text
            # data of temporary widgets to clone back

            e = self.ids.temporary.children[3].pos_hint["center_y"] + self.rate * 1.25
            # create clones back
            first_drag = Drag(color=self.selected_button_color,
                              size_hint_y=0.06,
                              pos_hint={"center_x": a, "center_y": e})
            second_drag = Drag_Text(text=text1, font_size=0.04 * Window.height,
                                    pos_hint={"x": b, "center_y": e})
            third_drag = Drag_Image(opacity=0.3, pos_hint={"center_x": c, "center_y": e},
                                    color=self.color_of_top_picto)
            fourth_drag = Drag_Number(text=text2, font_size=0.04 * Window.height,
                                      pos_hint={"x": d, "center_y": e},
                                      color=self.color_of_top_picto)

            # appear and pos the clones back in kivy file
            z = places[2] - 2
            zizi = places[2] // 3
            self.ids.buttons.add_widget(first_drag, index=z)
            self.ids.buttons.add_widget(second_drag, index=z)
            self.ids.buttons.add_widget(third_drag, index=z)
            self.ids.numbers.add_widget(fourth_drag, index=zizi)

        # the procedure of dragging ends
        self.dragging = False
        # slide opportunity as soon as it is possible in touch_up
        self.pressing = 0

        self.drag_and_drop_scroll = False

        # texts ordering as every change / self.pressing = 0 also in it because of other changes
        self.ordering_rows()

        # colored back
        self.z = z + 2
        Clock.schedule_once(self.selected_button_color_back, 1)

        # delete all temporary widgets
        self.ids.temporary.clear_widgets()

    def drag_and_drop_scroll_up(self, dt):
        # when you drag the row and go up on the screen
        if self.drag_and_drop_scroll is False:
            return False
        self.position_of_row -= 0.01
        if self.position_of_row <= 0.42:
            self.position_of_row = 0.42

        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

    def drag_and_drop_scroll_down(self, dt):
        # when you drag the row and go down on the screen
        if self.drag_and_drop_scroll is False:
            return False

        self.position_of_row += 0.01
        if self.position_of_row >= 2.022:
            self.position_of_row = 2.022
        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

    def on_touch_down(self, touch):

        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right' or self.pressing == 1:
            return False

        self.previous_touch_pos = touch.pos
        self.first_touch_pos = touch.pos

        s = len(self.ids.all_none.children)
        if self.ids.all_none.children[s - 1].collide_point(*touch.pos) and \
                self.ids.basic.children[0].collide_point(*touch.pos):
            self.first_pos = touch.pos[0]
            k = s - 2
            self.k = k

        elif self.ids.bottom.children[-1].collide_point(*touch.pos):
            self.first_pos = touch.pos[0]
            k = 3
            self.k = k

        else:
            for k in range(2, len(self.ids.buttons.children), 3):
                if self.ids.buttons.children[k].collide_point(*touch.pos) and \
                        self.ids.basic.children[0].collide_point(*touch.pos):
                    self.first_pos = touch.pos[0]
                    self.k = k
                    # the dragging process is tarting in def able to drag
                    n = int(self.text_minus_two(self.ids.numbers.children[self.k // 3].text))
                    # if we are not in dragging method and the widget is selected (has a number)
                    if self.dragged and n != 0:
                        self.drag_first_position = touch.spos[1]
                        self.dragged = False
                        self.heritage_of_self_i = self.k
                        Clock.schedule_interval(self.able_to_drag, 0.1)
                        break

    def on_touch_up(self, touch):

        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right':
            return False

        # no dragging process
        if not self.dragging and self.pressing == 0:

            # the first row button parameters (grey)
            s = len(self.ids.all_none.children)
            if self.ids.all_none.children[s - 1].collide_point(*touch.pos) and \
                    self.ids.basic.children[0].collide_point(*touch.pos):
                i = s - 2
                self.i = i
                if self.i == self.k:
                    # self.heritage_of_self_i = self.i
                    if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()
                            # self.sound.play()
                        self.heritage_of_self_i = 300
                        self.flash_up()

                        self.all_none_numbers_command()

            # bottom button things
            elif self.ids.bottom.children[-1].collide_point(*touch.pos):
                i = 3
                self.i = i
                if self.i == self.k:
                    if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                        self.heritage_of_self_i = 100
                        self.bottom_command()
                        self.flash_up()
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()

                    elif self.first_pos - Window.width * 0.05 > touch.pos[0]:
                        self.heritage_of_self_i = 200
                        self.bottom_command()
                        self.flash_up()
                        if self.sound and self.parent.touch_sound_allow:
                            self.sound.play()

            # other buttons in row
            else:
                for i in range(2, len(self.ids.buttons.children), 3):
                    if self.ids.buttons.children[i].collide_point(*touch.pos) and \
                            self.ids.basic.children[0].collide_point(*touch.pos):
                        self.i = i
                        if self.i == self.k:
                            if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                                self.heritage_of_self_i = self.i
                                self.numbers_manager()
                                self.flash_up()
                                if self.sound and self.parent.touch_sound_allow:
                                    self.sound.play()

            # for move and down and up - scroll
            self.previous_touch_pos = None
            # in on_move, on_up - scroll
            self.first_touch_pos = None
            # in on_down, on_up - slide
            self.first_pos = None
            # for on_down, on_up - slide
            self.i = -11
            self.k = -10

        # dragging processing
        elif self.dragging:

            # we should drop the drag here?!
            places = [self.k]
            for i in range(2, len(self.ids.buttons.children), 3):
                if self.ids.buttons.children[i].collide_widget(self.ids.temporary.children[3]) and \
                        self.ids.basic.children[0].collide_point(*touch.pos) and \
                        self.ids.numbers.children[(i - 2) // 3].opacity == 1:
                    places.append(i)

            a = self.ids.temporary.children[3].pos_hint["center_x"]
            b = self.ids.temporary.children[2].pos_hint["x"]
            c = self.ids.temporary.children[1].pos_hint["center_x"]
            d = self.ids.temporary.children[0].pos_hint["x"]

            self.drop_the_drag(places, a, b, c, d)

        # we stop dragging process
        self.dragged = True

        self.drag_and_drop_scroll = False

    def on_touch_move(self, touch):
        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right':
            return False

        # no dragging process
        if not self.dragging:

            if self.previous_touch_pos is None:
                self.previous_touch_pos = touch.pos
            if self.first_touch_pos is None:
                self.first_touch_pos = touch.pos

            # if we leave the selected button area the drag process stop
            if not self.ids.buttons.children[self.k].collide_point(*touch.pos):
                self.dragged = True

            # move up and down
            if self.ids.basic.children[0].collide_point(*touch.pos):
                if self.first_touch_pos[1] + Window.height * 0.05 < touch.pos[1] or \
                        self.first_touch_pos[1] - Window.height * 0.05 > touch.pos[1]:
                    # up edge
                    if self.position_of_row <= 0.42:
                        self.position_of_row = 0.42
                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        # to start the moving only up
                        if self.previous_touch_pos[1] > touch.pos[1]:
                            self.position_of_row += 0.075
                            self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                            self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                            self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    # down edge
                    elif self.position_of_row >= 2.022:
                        self.position_of_row = 2.022

                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        # to start the moving only up
                        if self.previous_touch_pos[1] < touch.pos[1]:
                            self.position_of_row -= 0.075
                            self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                            self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                            self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    # just moving up
                    elif self.previous_touch_pos[1] > touch.pos[1]:
                        self.position_of_row += 0.075
                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    # just moving down
                    elif self.previous_touch_pos[1] < touch.pos[1]:
                        self.position_of_row -= 0.075
                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

            # determine the last touch pos as a previous pos
            self.previous_touch_pos = touch.pos

        # if we are in dragging method and the temporary widgets (the clone) are ready
        if self.dragging and len(self.ids.temporary.children) >= 4:
            self.dragged = True
            if self.ids.basic.children[0].collide_point(*touch.pos):
                self.drag_and_drop_scroll = False

                a = self.ids.temporary.children[3].pos_hint["center_x"]
                b = self.ids.temporary.children[2].pos_hint["x"]
                c = self.ids.temporary.children[1].pos_hint["center_x"]
                d = self.ids.temporary.children[0].pos_hint["x"]

                self.ids.temporary.children[3].pos_hint = {"center_x": a, "center_y": touch.spos[1]}
                self.ids.temporary.children[2].pos_hint = {"x": b, "center_y": touch.spos[1]}
                self.ids.temporary.children[1].pos_hint = {"center_x": c, "center_y": touch.spos[1]}
                self.ids.temporary.children[0].pos_hint = {"x": d, "center_y": touch.spos[1]}

            elif self.ids.top.children[-1].collide_point(*touch.pos):
                self.drag_and_drop_scroll = True
                Clock.schedule_interval(self.drag_and_drop_scroll_up, 0.05)

            elif self.ids.bottom.children[-1].collide_point(*touch.pos):
                self.drag_and_drop_scroll = True
                Clock.schedule_interval(self.drag_and_drop_scroll_down, 0.05)

        # not to run over the area at all
        # up edge
        if self.position_of_row < 0.42:
            self.position_of_row = 0.42
        # down edge
        elif self.position_of_row > 2.022:
            self.position_of_row = 2.022
        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.all_none.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}


class R3Window(Screen):
    # sounds player
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # number of theme
        self.tap_counter = 0
        # pos of scrolled area
        self.position_of_row = 0.42
        # position of all none button
        self.position_of_first_row = 0.993
        # rate between themes buttons
        self.rate = 0.065
        # when buttons are coming up we need to change the scroll edge down
        self.position_of_row_of_border = 0
        # shuffle_row button color
        self.color_of_first_button = 101 / 255, 94 / 255, 94 / 255, 255 / 255
        self.color_of_first_button_text = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        # button texts
        self.buttons = {
            940: [["LEJÁTSZÁS", "PLAY"], ["MEGÁLLÍTÁS", "STOP"]],
            950: [["LEJÁTSZO", "PLAYER"], ["LEJÁTSZÓ", "PLAYER"]]}

        # background color of bg label
        self.bg_color = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        # arrows source
        self.arrow = "r_right.png"
        # bottom button
        self.color_of_arrow_b = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.opacity_of_arrow_b = 0.3
        # first row arrows
        self.color_of_arrow = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.opacity_of_arrow = 0.3
        # color of top picto lone
        self.color_of_top = 255 / 255, 255 / 255, 255 / 255, 255 / 255
        self.color_of_top_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_top_text = 41 / 255, 145 / 255, 43 / 255, 1
        # pictos source
        self.pictos = {11: ("r_female.png", "r_male.png"),
                       8: ('r_hun_flag.png', "r_eng_flag.png"),
                       5: ("r_plane_not.png", "r_plane.png"),
                       2: ("r_sound.png", "r_mute.png"),
                       17: ("r_music_96.png", "r_not_128.png", 'r_circle_100.png'),
                       }
        # pictos color
        self.color_of_top_picto = 41 / 255, 145 / 255, 43 / 255, 1
        # color of bottom line
        self.color_of_bottom_button_line = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_bottom_button_picto = 0 / 255, 0 / 255, 0 / 255, 255 / 255
        self.color_of_bottom_button = 41 / 255, 145 / 255, 43 / 255, 1
        # female 0 or male 1 from first - second - page
        self.gender = 0
        # language type
        self.language = 0
        # slide touch right
        self.first_pos = None
        self.previous_touch_pos = None
        self.first_touch_pos = None
        # slide touch right
        self.k = -10
        self.i = -11

        # sound
        self.sound = SoundLoader.load('rozi_toggle_button_pixabay.wav')
        # sound of attention
        self.sound1 = SoundLoader.load('attention.wav')

        # small writes on bottom button
        self.color_of_small_number = 200 / 255, 203 / 255, 202 / 255, 255 / 255
        self.small_number = f'{self.tap_counter}'
        # shuffle row switcher
        self.play_or_stop_switcher = 0
        # heritage self_i because self_i is changing meanwhile we handle with the price of self_i
        self.heritage_of_self_i = -1
        # list of sounds that will be played
        self.list_of_sounds = []
        # the sound that is played
        self.number_of_sound = 0
        # tracks  media player
        self.player = AudioManager(filename="rozi_music.ogg")
        # playing the track
        self.checker_number = 1
        # playing the list
        self.checker_all_number = 0
        # pause
        self.pause = 0
        # make the label color flashing
        self.label_flashing_number = 0
        # allow for pressing rows
        self.no_rows_buttons = 0
        # loop
        self.loop = 0
        # times

        seconds = 0  # example number of seconds
        seconds1 = 0  # # example the counting number of seconds

        self.all_time = f"{divmod(seconds1, 60)[0]}:{divmod(seconds1, 60)[1]:02d} /" \
                        f" {divmod(seconds, 60)[0]}:{divmod(seconds, 60)[1]:02d}"
        self.track_time = f"{divmod(seconds1, 60)[0]}:{divmod(seconds1, 60)[1]:02d} /" \
                          f" {divmod(seconds, 60)[0]}:{divmod(seconds, 60)[1]:02d}"

        self.length_of_tracks = []
        self.length_of_all_tracks = 0

    def on_pre_enter(self, *args):
        # scroll allowed and position is determined according to numbers of buttons
        if len(self.ids.buttons.children) >= 26:
            self.position_of_row_of_border = 0.4 + self.rate * ((self.tap_counter - 13) + 1)
        else:
            self.position_of_row_of_border = 0.42  # 0.415

    def on_enter(self, *args):
        # loading the selected tracks
        self.load_tracks()
        # check airplane mode
        Clock.schedule_once(self.airplane_status_command, 1)

    def on_leave(self, *args):

        # delete all sound buttons to start it again from second screen
        self.ids.buttons.clear_widgets()
        self.ids.numbers.clear_widgets()
        self.ids.signs.clear_widgets()
        # music volume up
        _window = self.manager.get_screen("R0")
        _window.sound100.set_volume(0.95, 0.95)

    def airplane_status_command(self, dt):
        # airplane checker
        k = AirplaneModeManager()
        if k.is_enabled():
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][0]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][1]
        else:
            # if the sign is changing give sound
            if self.sound1 and self.parent.touch_sound_allow and \
                    self.ids.top.children[1].source == self.pictos[5][1]:
                self.sound1.play()

            self.ids.top.children[1].source = self.pictos[5][0]

    def flash_up(self):
        # arrow bright
        if self.heritage_of_self_i == 300:
            self.ids.bottom.children[0].opacity = 1
        elif self.heritage_of_self_i == 100:
            self.ids.shuffle_row.children[0].opacity = 1
        elif self.heritage_of_self_i == 400:
            self.ids.bottom.children[1].opacity = 1
        else:
            self.ids.signs.children[self.heritage_of_self_i // 2].opacity = 1
        Clock.schedule_once(self.flash_down, 0.25)

    def flash_down(self, dt):
        # arrow fade
        if self.heritage_of_self_i == 300:
            self.ids.bottom.children[0].opacity = 0.3
        elif self.heritage_of_self_i == 100:
            self.ids.shuffle_row.children[0].opacity = 0.3
        elif self.heritage_of_self_i == 400:
            self.ids.bottom.children[1].opacity = 0.3
        else:
            self.ids.signs.children[self.heritage_of_self_i // 2].opacity = 0.3

    def before_go_to_the_previous_page(self):
        # no flash if we leave this page
        self.label_flashing_number = -1

        # the sound stop
        self.player.stop()

        # change the last button color
        self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
            255 / 255, 255 / 255, 255 / 255, 1  # 219 / 255, 128 / 255, 23 / 255, 1
        # change the first button arrow color
        self.ids.signs.children[(len(self.ids.signs.children) - 1) - self.number_of_sound].color = \
            self.color_of_top_picto
        # every each time data is 0
        self.number_of_sound = 0
        self.checker_number = 0
        self.checker_all_number = 0
        self.length_of_tracks = [0]
        self.length_of_all_tracks = 0

        # track timer
        self.ids.times.children[1].text = \
            f"{divmod(self.checker_all_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_all_number, 60)[1]:02d} / " \
            f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
            f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"

        b = self.length_of_tracks[self.number_of_sound]
        self.ids.times.children[0].text = \
            f"{divmod(self.checker_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_number, 60)[1]:02d} / " \
            f"{divmod(b, 60)[0]:02d}:" \
            f"{divmod(b, 60)[1]:02d}"
        a = self.position_of_first_row - ((self.number_of_sound + 1) * self.rate) + 0.0025
        self.ids.times.children[0].pos_hint = \
            {"right": 0.9, "center_y": a}

        self.length_of_tracks = []

        Clock.schedule_once(self.back_to_the_previous_page, 2)

    def back_to_the_previous_page(self, dt):
        # sound checker can be starting next time
        self.pause = 0
        # you can touch row buttons next time
        self.no_rows_buttons = 0
        # swap screen
        self.parent.transition = self.parent.style_of_transition
        self.manager.transition.duration = 0.5
        self.manager.transition.direction = "right"
        self.parent.current = "R2"

    def load_tracks(self):
        # load selected tracks
        self.list_of_sounds = []
        my_sound = ""
        for t in range(len(self.ids.signs.children) - 1, -1, -1):
            e = self.ids.buttons.children[t * 2].text
            f = e.strip()
            # female 0 or male 1 and hun 0 or eng 1
            if self.gender == 0 and self.language == 0:
                my_sound = f"hungarian_female.ogg"
            elif self.gender == 0 and self.language == 1:
                my_sound = f"english_female.ogg"
            elif self.gender == 1 and self.language == 1:
                my_sound = f"english_male.ogg"
            elif self.gender == 1 and self.language == 0:
                # my_sound = f"{f}.ogg"
                my_sound = f'hungarian_male.ogg'
            self.list_of_sounds.append(my_sound)
        # count tracks length and all length
        self.length_of_tracks = list(map(self.get_track_length, self.list_of_sounds))
        self.length_of_all_tracks = sum(map(self.get_track_length, self.list_of_sounds))
        # display first data if tracks
        seconds = 0
        self.ids.times.children[1].text = \
            f"{divmod(seconds, 60)[0]:02d}:" \
            f"{divmod(seconds, 60)[1]:02d} / " \
            f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
            f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"
        self.ids.times.children[0].text = \
            f"{divmod(seconds, 60)[0]:02d}:" \
            f"{divmod(seconds, 60)[1]:02d} / " \
            f"{divmod(self.length_of_tracks[0], 60)[0]:02d}:" \
            f"{divmod(self.length_of_tracks[0], 60)[1]:02d}"

    def get_track_length(self, file):
        # we determine the length of a track
        k = AudioManager(filename=file)
        k.play()
        k.set_volume(0.0, 0.0)
        import time
        time.sleep(0.1)
        duration = k.get_length()
        k.pause()
        k.set_volume(1.0, 1.0)
        k.stop()
        return int(duration)

    def play_track(self):
        # stop the label flashing
        self.label_flashing_number = -1
        # the arrows disappear during the play
        for t in range(len(self.ids.signs.children)):
            self.ids.signs.children[t].opacity = 0

        # row buttons touching is not allowed
        self.no_rows_buttons = 1

        # change the next button color
        self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
            219 / 255, 128 / 255, 23 / 255, 1
        # change the first button arrow color
        self.ids.signs.children[len(self.ids.signs.children) - 1 - self.number_of_sound].color = \
            self.color_of_arrow_b

        # media object - the track
        # load track
        if self.pause == 0:
            self.player = AudioManager(filename=self.list_of_sounds[self.number_of_sound])
        # continue track
        else:
            self.pause = 0
        # start the track
        self.player.play()

        # start sound checker
        Clock.schedule_interval(self.sound_checker, 1)

    def pause_label_flashing(self, dt):
        # when track is paused, the button is flashing
        if self.label_flashing_number == - 1:
            self.label_flashing_number = 0
            return False

        if self.label_flashing_number % 2 == 0:
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                255 / 255, 255 / 255, 255 / 255, 1
        else:
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                219 / 255, 128 / 255, 23 / 255, 1

        self.label_flashing_number += 1

    def no_loop(self):
        # in case when there is no loop
        # first row has to be change
        self.ids.shuffle_row.children[-2].text = self.buttons[940][0][self.language]
        self.play_or_stop_switcher = 0
        # the music volume go back to default
        _window = self.manager.get_screen("R0")
        _window.sound100.set_volume(0.9, 0.9)

        for t in range(len(self.ids.signs.children)):
            self.ids.signs.children[t].opacity = 0.3
        self.no_rows_buttons = 0

    def sound_checker(self, dt):
        # running/playing the tracks one after the other
        if self.pause == 1:
            return False

        # going around
        self.ids.times.children[1].text = \
            f"{divmod(self.checker_all_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_all_number, 60)[1]:02d} / " \
            f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
            f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"

        b = self.length_of_tracks[self.number_of_sound]
        self.ids.times.children[0].text = \
            f"{divmod(self.checker_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_number, 60)[1]:02d} / " \
            f"{divmod(b, 60)[0]:02d}:" \
            f"{divmod(b, 60)[1]:02d}"

        # question of loop at the end of last track
        if self.checker_all_number >= self.length_of_all_tracks + 1:

            # end the track
            self.player.stop()

            # self.position_of_sound = 0.0
            self.checker_number = 0
            self.checker_all_number = 0

            # change the last button color
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                255 / 255, 255 / 255, 255 / 255, 1  # 219 / 255, 128 / 255, 23 / 255, 1
            # change the first button arrow color
            self.ids.signs.children[(len(self.ids.signs.children) - 1) - self.number_of_sound].color = \
                self.color_of_top_picto

            # get first sound
            self.number_of_sound = 0

            # change the next button color
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                219 / 255, 128 / 255, 23 / 255, 1
            # change the first button arrow color
            self.ids.signs.children[len(self.ids.signs.children) - 1 - self.number_of_sound].color = \
                self.color_of_arrow_b

            # small number changing
            self.tap_counter = len(self.ids.signs.children)
            self.ids.bottom_line.children[0].text = f"{self.tap_counter}"

            # track timer
            self.ids.times.children[1].text = \
                f"{divmod(self.checker_all_number, 60)[0]:02d}:" \
                f"{divmod(self.checker_all_number, 60)[1]:02d} / " \
                f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
                f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"

            b = self.length_of_tracks[self.number_of_sound]
            self.ids.times.children[0].text = \
                f"{divmod(self.checker_number, 60)[0]:02d}:" \
                f"{divmod(self.checker_number, 60)[1]:02d} / " \
                f"{divmod(b, 60)[0]:02d}:" \
                f"{divmod(b, 60)[1]:02d}"
            a = self.position_of_first_row - ((self.number_of_sound + 1) * self.rate) + 0.0025
            self.ids.times.children[0].pos_hint = \
                {"right": 0.9, "center_y": a}

            # load first sound
            self.player = AudioManager(filename=self.list_of_sounds[self.number_of_sound])

            # loop
            if self.loop % 2 == 1:

                # start track
                self.player.play()

            # no loop
            else:
                # first row text change
                self.ids.shuffle_row.children[-2].text = self.buttons[940][0][self.language]

                # stop track
                self.player.stop()

                # stop time checker self
                self.pause = 1
                # stop/start switcher change
                self.play_or_stop_switcher = 0
                # allow for pressing rows
                self.no_rows_buttons = 0
                # change all button arrow opacity
                for t in range(len(self.ids.signs.children)):
                    self.ids.signs.children[t].opacity = 0.3
                # sound volume up back
                _window = self.manager.get_screen("R0")
                _window.sound100.set_volume(0.9, 0.9)

            # back up to the top of list
            self.position_of_row = 0.42
            self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
            self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
            self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
            self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
            self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

        # step next sound
        elif self.checker_number >= self.length_of_tracks[self.number_of_sound] + 1:

            # stop track
            self.player.stop()

            # self.position_of_sound = 0.0
            self.checker_number = 0

            # change the last button color
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                255 / 255, 255 / 255, 255 / 255, 1  # 219 / 255, 128 / 255, 23 / 255, 1
            # change the first button arrow color
            self.ids.signs.children[len(self.ids.signs.children) - 1 - self.number_of_sound].color = \
                self.color_of_top_picto

            # number of sound steps forward
            self.number_of_sound += 1

            # change the next button color
            self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
                219 / 255, 128 / 255, 23 / 255, 1
            # change the next button arrow color
            self.ids.signs.children[len(self.ids.signs.children) - 1 - self.number_of_sound].color = \
                self.color_of_arrow_b

            # small number changing
            self.tap_counter -= 1
            self.ids.bottom_line.children[0].text = f"{self.tap_counter}"

            # track timer
            self.ids.times.children[1].text = \
                f"{divmod(self.checker_all_number, 60)[0]:02d}:" \
                f"{divmod(self.checker_all_number, 60)[1]:02d} / " \
                f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
                f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"

            b = self.length_of_tracks[self.number_of_sound]
            self.ids.times.children[0].text = \
                f"{divmod(self.checker_number, 60)[0]:02d}:" \
                f"{divmod(self.checker_number, 60)[1]:02d} / " \
                f"{divmod(b, 60)[0]:02d}:" \
                f"{divmod(b, 60)[1]:02d}"
            a = self.position_of_first_row - ((self.number_of_sound + 1) * self.rate) + 0.0025
            self.ids.times.children[0].pos_hint = \
                {"right": 0.9, "center_y": a}

            # load the next song and play
            self.player = AudioManager(filename=self.list_of_sounds[self.number_of_sound])
            self.player.play()

        # counter strike
        self.checker_number += 1
        self.checker_all_number += 1

    def pause_track(self):

        # pause track
        self.player.pause()

        # prepare for label flashing
        self.label_flashing_number = 0
        # pause sound checker
        self.pause = 1
        # allow to touch row/track buttons
        self.no_rows_buttons = 0
        # the arrows of track/row buttons appear
        for t in range(len(self.ids.signs.children)):
            self.ids.signs.children[t].opacity = 0.3
        # start flashing the paused row/track button
        Clock.schedule_interval(self.pause_label_flashing, 0.25)

    def stop_track(self):

        # stop track
        self.player.stop()

        self.label_flashing_number = -1
        # allow to restart the track again
        self.pause = 0

        # change the last button color
        self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
            255 / 255, 255 / 255, 255 / 255, 1  # 219 / 255, 128 / 255, 23 / 255, 1
        # change the first button arrow color
        self.ids.signs.children[(len(self.ids.signs.children) - 1) - self.number_of_sound].color = \
            self.color_of_top_picto

        self.number_of_sound = (len(self.ids.signs.children) - 1) - self.heritage_of_self_i // 2

        # change the next button color
        self.ids.buttons.children[(len(self.ids.buttons.children) - 1) - (self.number_of_sound * 2)].color = \
            219 / 255, 128 / 255, 23 / 255, 1
        # change the first button arrow color
        self.ids.signs.children[len(self.ids.signs.children) - 1 - self.number_of_sound].color = \
            self.color_of_arrow_b

        # track timer
        self.checker_all_number = sum(self.length_of_tracks[:self.number_of_sound])

        self.ids.times.children[1].text = \
            f"{divmod(self.checker_all_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_all_number, 60)[1]:02d} / " \
            f"{divmod(self.length_of_all_tracks, 60)[0]:02d}:" \
            f"{divmod(self.length_of_all_tracks, 60)[1]:02d}"

        self.checker_number = 0

        b = self.length_of_tracks[self.number_of_sound]
        self.ids.times.children[0].text = \
            f"{divmod(self.checker_number, 60)[0]:02d}:" \
            f"{divmod(self.checker_number, 60)[1]:02d} / " \
            f"{divmod(b, 60)[0]:02d}:" \
            f"{divmod(b, 60)[1]:02d}"
        c = self.ids.numbers.children[self.heritage_of_self_i // 2].pos_hint["center_y"] - 0.0025
        self.ids.times.children[0].pos_hint = \
            {"right": 0.9, "center_y": c}

        # small number changing
        self.tap_counter = len(self.ids.signs.children) - self.number_of_sound
        self.ids.bottom_line.children[0].text = f"{self.tap_counter}"

    def play_or_stop_command(self):

        # call page 0
        _window = self.manager.get_screen("R0")

        # track on
        if self.play_or_stop_switcher == 0:

            # the music volume go back to default
            _window.sound100.set_volume(0.05, 0.05)

            # text change
            self.ids.shuffle_row.children[-2].text = self.buttons[940][1][self.language]
            # variable change
            self.play_or_stop_switcher = 1
            # play track
            self.play_track()

        # track off
        else:
            # text change
            self.ids.shuffle_row.children[-2].text = self.buttons[940][0][self.language]
            # variable change
            self.play_or_stop_switcher = 0
            # happening on in sound checker
            self.pause = 1

            # the music volume go back to default
            _window.sound100.set_volume(0.95, 0.95)

            # pause track
            self.pause_track()

    def loop_allow(self):
        # it is moving the loop contexts in sound checker with no loop and rotate the picto
        self.angle += 45
        self.ids.bottom.children[2].angle = self.angle
        self.loop += 1
        if self.loop % 2 == 0:
            self.ids.bottom.children[2].opacity = 0.3
        else:
            self.ids.bottom.children[2].opacity = 1

    def on_touch_down(self, touch):
        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right':
            return False

        # collect data
        self.previous_touch_pos = touch.pos
        self.first_touch_pos = touch.pos
        # shuffle first touch
        if self.ids.shuffle_row.children[-1].collide_point(*touch.pos) and \
                self.ids.basic.children[0].collide_point(*touch.pos):
            self.first_pos = touch.pos[0]
            k = 100
            self.k = k
        # bottom button first touch
        elif self.ids.bottom.children[-1].collide_point(*touch.pos):
            self.first_pos = touch.pos[0]
            k = 300
            self.k = k
        # other buttons first touch
        else:
            for k in range(len(self.ids.buttons.children) - 1, -1, -2):
                if self.ids.buttons.children[k].collide_point(*touch.pos) and \
                        self.ids.basic.children[0].collide_point(*touch.pos) and self.no_rows_buttons == 0:
                    self.first_pos = touch.pos[0]
                    self.k = k

    def on_touch_up(self, touch):

        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right':
            return False

        # the first row button parameters (grey)
        if self.ids.shuffle_row.children[-1].collide_point(*touch.pos) and \
                self.ids.basic.children[0].collide_point(*touch.pos):
            i = 100
            self.i = 100
            if self.i == self.k:
                self.heritage_of_self_i = self.i
                if self.first_pos + Window.width * 0.05 < touch.pos[0]:
                    if self.sound and self.parent.touch_sound_allow:
                        self.sound.play()

                    self.heritage_of_self_i = self.i
                    self.flash_up()
                    self.play_or_stop_command()

        # bottom button things
        elif self.ids.bottom.children[-1].collide_point(*touch.pos):
            i = 300
            self.i = i
            if self.i == self.k:

                if self.first_pos - Window.width * 0.05 > touch.pos[0]:
                    self.heritage_of_self_i = 300
                    self.flash_up()
                    if self.sound and self.parent.touch_sound_allow:
                        self.sound.play()

                    # stop sound checker
                    self.pause = 1

                    self.before_go_to_the_previous_page()
                elif self.first_pos + Window.width * 0.05 < touch.pos[0]:
                    self.heritage_of_self_i = 400
                    self.flash_up()
                    if self.sound and self.parent.touch_sound_allow:
                        self.sound.play()

                    self.loop_allow()
                    # BACK AND STOP happen at the end of flash down / bottom_command

        # other buttons in row
        else:
            for i in range(len(self.ids.buttons.children) - 1, -1, -2):
                if self.ids.buttons.children[i].collide_point(*touch.pos) and \
                        self.ids.basic.children[0].collide_point(*touch.pos) \
                        and self.no_rows_buttons == 0:
                    self.i = i
                    if self.i == self.k:
                        if self.first_pos + Window.width * 0.05 < touch.pos[0]:

                            self.heritage_of_self_i = self.i
                            self.flash_up()

                            # stop the track and change to another
                            self.stop_track()

                            if self.sound and self.parent.touch_sound_allow:
                                self.sound.play()


        # for move and down and up - scroll
        self.previous_touch_pos = None
        # in on_move, on_up - scroll
        self.first_touch_pos = None
        # in on_down, on_up - slide
        self.first_pos = None
        # for on_down, on_up - slide
        self.i = -11
        self.k = -10

    def on_touch_move(self, touch):
        if touch.button == "scrollup" or touch.button == "scrolldown" or touch.button == 'middle' \
                or touch.button == 'right' or self.position_of_row_of_border == 0.42:
            return False
        # when we play more tracks than it can be appeared on one screen
        if self.previous_touch_pos is None:
            self.previous_touch_pos = touch.pos
        if self.first_touch_pos is None:
            self.first_touch_pos = touch.pos

        if self.ids.basic.children[0].collide_point(*touch.pos):

            if self.first_touch_pos[1] + Window.height * 0.05 < touch.pos[1] or \
                    self.first_touch_pos[1] - Window.height * 0.05 > touch.pos[1]:
                # up edge
                if self.position_of_row <= 0.42:
                    self.position_of_row = 0.42
                    self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

                    # to start the moving only up
                    if self.previous_touch_pos[1] > touch.pos[1]:
                        self.position_of_row += 0.075
                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

                # down edge
                elif self.position_of_row >= self.position_of_row_of_border:
                    self.position_of_row = self.position_of_row_of_border
                    self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

                    # to start the moving only up
                    if self.previous_touch_pos[1] < touch.pos[1]:
                        self.position_of_row -= 0.075
                        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                        self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

                # just moving up
                elif self.previous_touch_pos[1] > touch.pos[1]:
                    self.position_of_row += 0.075
                    self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

                # just moving down
                elif self.previous_touch_pos[1] < touch.pos[1]:
                    self.position_of_row -= 0.075
                    self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
                    self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}

        # determine the last touch pos as a previous pos
        self.previous_touch_pos = touch.pos

        # not to run over the area at all
        # up edge
        if self.position_of_row <= 0.42:
            self.position_of_row = 0.42
        # down edge
        elif self.position_of_row >= self.position_of_row_of_border:
            self.position_of_row = self.position_of_row_of_border
        self.ids.buttons.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.numbers.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.shuffle_row.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.signs.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}
        self.ids.times.pos_hint = {"center_x": 0.5, "center_y": self.position_of_row}


class WindowManager(ScreenManager):
    # how to change screen
    style_of_transition = SlideTransition()
    # it is needed to handle the screens/pages

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # about the sound
        self.touch_sound_allow = True


class RoziApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # load everything we need - text style, windowmanager and screens
        LabelBase.register(name='Sony', fn_regular='Sony Sketch EF Regular.ttf')
        self.sm = WindowManager()
        self.sm.add_widget(Builder.load_file("MED0.kv"))
        self.sm.add_widget(Builder.load_file("MED1.kv"))
        self.sm.add_widget(Builder.load_file("MED2.kv"))
        self.sm.add_widget(Builder.load_file("MED3.kv"))

        # self.named = "ROZI"

    def build(self):
        self.icon = "new_icon1.png"
        # the app starts with splash screen
        self.sm.current = "R0"
        return self.sm

    def on_resume(self):
        try:
            first_window = self.sm.get_screen("R1")

            # we handle the video if the video screen is active
            if self.sm.current == "R1":
                video = getattr(first_window, "video", None)
                if video and video.surface_view and video.media_player:
                    holder = video.surface_view.getHolder()
                    video.media_player.setDisplay(holder)
                    # NE start()-ot hívjunk itt

            # Refresh the screen
            Clock.schedule_once(lambda dt: Window.canvas.ask_update(), 0.1)

            # airplane status check again
            Clock.schedule_once(first_window.airplane_status_command, 1)

        except Exception:
            # No need crash
            traceback.print_exc()

        return True

    def on_pause(self):

        first_window = self.sm.get_screen("R1")

        # we handle the video if the video screen is active
        if self.sm.current != "R1":
            if first_window.media_player:
                first_window.video.media_player.setDisplay(None)
                first_window.video.media_player.release()
                first_window.video_media_player = None
                first_window.video.surface_view = None

        return True

    def on_stop(self):
        # if we leave the app the sound is off
        settings_screen = self.sm.get_screen('R0')
        settings_screen.sound100.stop()


if __name__ == '__main__':
    RoziApp().run()