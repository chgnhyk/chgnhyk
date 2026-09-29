from csoundengine.offline import OfflineEngine
from .utils import get_asset_path
import math

PREDEFINED_INSTUMENTS = r'''
instr tone
    pset 0, 0, 0, 440, 1.0, 0.0, 0.5, 0.0
    kfreq = p4
    kamp = p5
    kphase = p6
    kpan = p7
    kwobble = p8
    aenv = linsegr(0, 0.05, 1.0, p3-0.1, 1.0, 0.05, 0)
    awobble = oscili(kwobble, kfreq*0.1)
    aout = oscili(kamp, kfreq + kphase + awobble) * aenv
    aout moogladder aout, 300, 0.6
    
    outch 1, aout * (1.0 - kpan) 
    outch 2, aout * (kpan)
endin
                    
instr EPiano
    ; p4 = freq, p5 = amp
    iFreq = p4
    iAmp  = p5
    kpan = p6

    ; envelopes
    kEnv madsr 0.01, 0.2, 0.7, 0.3

    ; FM
    kModEnv linseg 1, 0.3, 0.2
    aMod    poscil iFreq * 2 * kModEnv, iFreq * 2
    aCar    poscil iAmp * kEnv, iFreq + aMod

    ; tone shaping
    aCar moogladder aCar, 3000, 0.6

    ; light saturation
    aOut = tanh(aCar * 2)

    outs aOut * (1.0 - kpan), aOut * kpan
endin
                    
instr Bass
    ; p4 = freq, p5 = amp
    iFreq = p4
    iAmp  = p5
    kpan = p6

    ; pluck envelope
    kEnv linsegr 0, 0.01, 1, 0.25, 0

    ; subtle pitch drop
    kPitch linseg iFreq * 1.02, 0.03, iFreq

    aSig poscil iAmp * kEnv, kPitch

    ; low-pass for warmth
    aSig moogladder aSig, 400, 0.6

    ; saturation
    aOut = tanh(aSig * 2)

    outs aOut * (1.0 - kpan), aOut * kpan
endin
                     
instr Kick
    ; p5 = amp
    iAmp = p5
    kpan = p6

    kEnv  linseg 1, 0.08, 0
    kFreq expon 140, 0.08, 40

    aSig poscil iAmp * kEnv, kFreq
    aOut = tanh(aSig * 3)
    ; low-pass for warmth
    aOut moogladder aOut, 800, 0.6

    outs aOut * (1.0 - kpan), aOut * kpan
endin

instr Snare
    ; p5 = amp
    iAmp = p5
    kpan = p6

    kEnv linseg 1, 0.12, 0

    aNoise rand iAmp * 0.7
    aTone  poscil iAmp * 0.3, 180

    aSig = (aNoise + aTone) * kEnv
    aSig buthp aSig, 800

    outs aSig * (1.0 - kpan), aSig * kpan
endin

instr Hat
    ; p5 = amp
    iAmp = p5
    kpan = p6

    kEnv linseg 1, 0.04, 0

    aNoise rand iAmp
    aHat buthp aNoise, 6000

    outs aHat * kEnv * (1.0 - kpan), aHat * kEnv * kpan
endin                     
'''

def midi_to_freq(midi_note: float, a4: float = 440.0) -> float:
    return a4 * (2 ** ((midi_note - 69) / 12))

NOTE_TO_SEMITONE = {
    "C": 0,  "C#": 1,  "Db": 1,
    "D": 2,  "D#": 3,  "Eb": 3,
    "E": 4,
    "F": 5,  "F#": 6,  "Gb": 6,
    "G": 7,  "G#": 8,  "Ab": 8,
    "A": 9,  "A#": 10, "Bb": 10,
    "B": 11,
}

def note_to_freq(note: str, a4: float = 440.0) -> float:
    # split note and octave
    if len(note) == 2:
        name, octave = note[0], int(note[1])
    else:
        name, octave = note[:2], int(note[2])

    semitone = NOTE_TO_SEMITONE[name]
    midi_note = (octave + 1) * 12 + semitone
    return midi_to_freq(midi_note, a4)


class AudioManager:
    def __init__(self, path:str, instrument:str=""):
        self.engine = OfflineEngine(outfile=path)
        self.filepath = path
        if instrument != "":
            self.setInstruments(instrument)

    def setEvent(self, *args, **kwargs):
        return self.engine.sched(*args, **kwargs)

    def setEffect(self, *args, **kwargs):
        return self.engine.automatep(*args, **kwargs)

    def setInstruments(self, csound_code:str):
        csound_code = csound_code.replace(';;####PREDEFINED####', PREDEFINED_INSTUMENTS)
        #print(get_asset_path("chgnhyk.assets.csound", "hrtf-44100-left.dat"))
        csound_code = csound_code.replace(';;####HRTF_L####', f'''
            gS_HRTF_left = "{get_asset_path("chgnhyk.assets.csound", "hrtf-44100-left.dat")}"
        ''')
        csound_code = csound_code.replace(';;####HRTF_R####', f'''
            gS_HRTF_right = "{get_asset_path("chgnhyk.assets.csound", "hrtf-44100-right.dat")}"
        ''')
        #print(csound_code)
        self.engine.compile(csound_code)

    def renderAudio(self, extratime=0.05):
        self.engine.perform(extratime=extratime)
        self.engine.stop()