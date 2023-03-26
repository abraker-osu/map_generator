import os
import shutil
import hashlib
import textwrap

from .Slider import Slider


class MapGenerator():

    AUDIO_OFFSET = -48  # ms
    BEAT_LENGTH  = 1000 # ms, bpm = 1 / BEAT_LENGTH * 1000 * 60
    SLIDER_VEL   = 1

    CIRCLE  = 1 << 0
    SLIDER  = 1 << 1
    NCOMBO  = 1 << 2
    SPINNER = 1 << 3

    def __init__(self):
        self.ar = None
        self.cs = None
        self.od = None
        self.hp = None
 
        self.sm = None  # slider multiplier; Base slider velocity in hundreds of osu! pixels per beat
        self.st = None  # slider tick rate; How many ticks per beat the slider is split into

        self.version = None
        self.creator = None

        self.data = None
        self.rate = 1.0
        self.t    = 0


    def start(self, ar, cs, od, hp, sm=1, st=1):
        self.ar = float(ar)
        self.cs = float(cs)
        self.od = float(od)
        self.hp = float(hp)

        self.sm = float(sm)
        self.st = int(st)

        if not (0.0 <= ar <= 11.0): raise ValueError('AR must be between 0.0 and 11.0.')
        if not (0.0 <= cs <= 10.0): raise ValueError('CS must be between 0.0 and 10.0.')
        if not (0.0 <= od <= 10.0): raise ValueError('OD must be between 0.0 and 10.0.')
        if not (0.0 <= hp <= 10.0): raise ValueError('HP must be between 0.0 and 10.0.')

        if not (0.0 <= sm): raise ValueError('SM must be more than 0.0')
        if not (0   <= st): raise ValueError('ST must be more than 0')

        if self.ar > 10.0:
            self.rate = 1.5
            self.ar   = MapGenerator.__ms_to_ar(MapGenerator.__ar_to_ms(ar)*self.rate)

        self.version = None
        self.data    = []
        self.t       = 0


    def set_meta(self, version, creator='unknown'):
        if len(version) > 16: raise ValueError('Version is too long.')
        if len(creator) > 32: raise ValueError('Creator is too long.')

        self.version = version
        self.creator = creator


    def add_sv(self, sv):
        # TODO
        pass


    def add_note(self, note_data, t_delta=True):
        IDX_T = 0  # time
        IDX_X = 1  # xpos
        IDX_Y = 2  # ypos
        IDX_C = 3  # split slider?

        if type(note_data) is not list:
            raise ValueError('Note data must be a list of int 3-tuples: [ t, x, y, c ]')

        for i, _ in enumerate(note_data):
            if len(note_data[i]) != 4:
                raise ValueError('Note data must be a list of int 3-tuples: [ t, x, y, c ]')

            if t_delta:
                note_t = self.t
                self.t += int(note_data[i][IDX_T] / self.rate)
            else:
                self.t = int(note_data[i][IDX_T] / self.rate)
                note_t = self.t
 
            note_data[i][IDX_T] = note_t
            note_data[i][IDX_X] = int(note_data[i][IDX_X])
            note_data[i][IDX_Y] = int(note_data[i][IDX_Y])
            note_data[i][IDX_C] = int(note_data[i][IDX_C])
        
        self.data += [ note_data ]


    def gen(self):
        if self.ar is None: raise ValueError('AR is not set. Use start() to set it.')
        if self.cs is None: raise ValueError('CS is not set. Use start() to set it.')
        if self.od is None: raise ValueError('OD is not set. Use start() to set it.')
        if self.hp is None: raise ValueError('HP is not set. Use start() to set it.')

        if self.sm is None: raise ValueError('SM is not set. Use start() to set it.')
        if self.st is None: raise ValueError('ST is not set. Use start() to set it.')

        if self.data is None:
            raise ValueError('Data is not set. Use set_data() to set it.')

        if self.version is None:
            self.version = 'gen'

        IDX_T = 0  # time
        IDX_X = 1  # xpos
        IDX_Y = 2  # ypos
        IDX_C = 3  # split slider?

        beatmap_data = textwrap.dedent(
            f"""\
            osu file format v14

            [General]
            AudioFilename: blank.mp3
            AudioLeadIn: 0
            PreviewTime: -1
            Countdown: 0
            SampleSet: Normal
            StackLeniency: 0
            Mode: 0
            LetterboxInBreaks: 1
            WidescreenStoryboard: 1

            [Editor]
            DistanceSpacing: 1.0
            BeatDivisor: 1
            GridSize: 32
            TimelineZoom: 1.0

            [Metadata]
            Title:unknown
            TitleUnicode:unknown
            Artist:{self.creator}
            ArtistUnicode:{self.creator}
            Creator:{self.creator}
            Version:{self.version}
            Source:
            Tags:
            BeatmapID:0
            BeatmapSetID:0

            [Difficulty]
            HPDrainRate:{self.hp}
            CircleSize:{self.cs}
            OverallDifficulty:{self.od}
            ApproachRate:{self.ar}
            SliderMultiplier:{self.sm}
            SliderTickRate:{self.st}

            [Events]\
            """
        )

        # Generate notes
        for note in self.data:
            beatmap_data += textwrap.dedent(
                f"""
                Sample,{int(note[0][IDX_T] + MapGenerator.AUDIO_OFFSET*self.rate)},3,"pluck.wav",100\
                """
            )

        # No uninherited timing points, so SLIDER_VEL is 1
        beatmap_data += textwrap.dedent(
            f"""

            [TimingPoints]
            0,{MapGenerator.BEAT_LENGTH},4,1,1,100,1,0

            [HitObjects]\
            """
        )

        for note in self.data:
            if len(note) == 1:
                # It's a single note
                beatmap_data += textwrap.dedent(
                    f"""
                    {int(note[0][IDX_X])},{int(note[0][IDX_Y])},{int(note[0][IDX_T] + MapGenerator.AUDIO_OFFSET*self.rate)},{MapGenerator.CIRCLE},0,0:0:0:0:\
                    """
                )
            else:
                # It's a slider, go through control points
                # Note: Only timings of first and last control point are used.
                #   as such only positions of control points matter for sliders.
                slider_data = ''
                for c in note[1:]:
                    slider_data += f'|{c[IDX_X]}:{c[IDX_Y]}'
                    
                    if c[IDX_C] == 1:
                        slider_data += f'|{c[IDX_X]}:{c[IDX_Y]}'

                repeats = 1
                px_len = Slider(note).length()

                beatmap_data += textwrap.dedent(
                    f"""
                    {int(note[0][IDX_X])},{int(note[0][IDX_Y])},{int(note[0][IDX_T] + MapGenerator.AUDIO_OFFSET*self.rate)},{MapGenerator.SLIDER},0,B{slider_data},{repeats},{px_len}\
                    """
                )

        # Remove leading whitespace
        beatmap_data = beatmap_data.split('\n')
        for i in range(len(beatmap_data)):
            beatmap_data[i] = beatmap_data[i].strip()
        beatmap_data = '\n'.join(beatmap_data)

        return beatmap_data


    def save(self, beatmap_data, filepath, res_path=''):
        # Write to beatmap file
        os.makedirs(filepath, exist_ok=True)

        if len(res_path) == 0:
            res_path = os.getcwd()

        if res_path[-1] != '/':
            res_path += '/'

        with open(f'{res_path}res/tmp.osu', 'wt', encoding='utf-8') as f:
            f.write(beatmap_data)

        map_md5 = hashlib.md5(open(f'{res_path}res/tmp.osu', 'rb').read()).hexdigest()

        if not os.path.isfile(f'{filepath}/{map_md5}.osu'):
            shutil.copy2(f'{res_path}res/tmp.osu', f'{filepath}/{map_md5}.osu')
        os.remove(f'{res_path}res/tmp.osu')

        if not os.path.isfile(f'{filepath}/pluck.wav'):
            shutil.copy2(f'{res_path}res/pluck.wav', f'{filepath}/pluck.wav')

        if not os.path.isfile(f'{filepath}/normal-hitnormal.wav'):
            shutil.copy2(f'{res_path}res/blank.wav', f'{filepath}/normal-hitnormal.wav')



    @staticmethod
    def __ar_to_ms(ar: 'float') -> float:
        if ar <= 5: return 1800 - 120*ar
        else:       return 1950 - 150*ar


    @staticmethod
    def __ms_to_ar(ms: 'float') -> float:
        if ms >= 1200: return (1800 - ms)/120
        else:          return (1950 - ms)/150
