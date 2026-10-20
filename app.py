import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎸 기타 코드 반주 AI 작곡 스튜디오",
    page_icon="🎶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일 ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1050px !important;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%);
        padding: 24px 28px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #60a5fa;
    }
    .chord-badge {
        display: inline-block;
        background: #2563eb;
        color: white;
        padding: 8px 16px;
        border-radius: 12px;
        font-weight: bold;
        margin: 6px;
        font-size: 1.05rem;
        border: 1px solid #93c5fd;
    }
    .status-card {
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 음계 및 주파수 테이블 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99,
    "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00
}

# --- 기타 스트럼(Strumming) 및 악기 합성 엔진 ---
def synthesize_guitar_strum(chord_freqs, duration, sample_rate, strum_type="어쿠스틱 스트럼"):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    
    t = np.linspace(0, duration, num_samples, endpoint=False)
    strum_signal = np.zeros_like(t)
    
    # 기타 스트럼 특유의 미세한 시간차(Arpeggio-like strumming) 구현
    num_strings = len(chord_freqs)
    string_delay = int(sample_rate * 0.025) # 현을 튕기는 미세한 간격 (25ms)
    
    for i, freq in enumerate(chord_freqs):
        offset = i * string_delay
        if offset >= num_samples:
            continue
        sub_t = t[:num_samples - offset]
        
        # 기타 배음 구조 (밝고 청량한 어쿠스틱/일렉 기타 질감)
        string_sound = (0.4 * np.sin(2 * np.pi * freq * sub_t) +
                        0.25 * np.sin(2 * np.pi * freq * 2 * sub_t) +
                        0.12 * np.sin(2 * np.pi * freq * 3 * sub_t))
        
        # 피크 및 서스틴 엔벨로프
        if "스트럼" in strum_type:
            pluck_decay = np.exp(-4.5 * sub_t / duration)
        else: # 아르페지오 (부드럽게 튕기는 핑거스타일)
            pluck_decay = np.exp(-3.0 * sub_t / duration)
            
        string_sound *= pluck_decay
        
        # 페이드 아웃
        fade_len = min(int(0.01 * sample_rate), len(sub_t) // 2)
        if fade_len > 0:
            string_sound[:fade_len] *= np.linspace(0, 1, fade_len)
            string_sound[-fade_len:] *= np.linspace(1, 0, fade_len)
            
        strum_signal[offset:offset + len(string_sound)] += string_sound
        
    return strum_signal

def synthesize_drum_hit(drum_type, duration, sample_rate):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if drum_type == "kick":
        f_sweep = np.linspace(120, 30, len(t))
        return 0.7 * np.sin(2 * np.pi * f_sweep * t) * np.exp(-12 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-15 * t / duration)
        body = 0.3 * np.sin(2 * np.pi * 180 * t) * np.exp(-18 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return 0.2 * np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-35 * t / duration)
    return np.zeros_like(t)

# --- 프로 가요풍 기타 코드 곡 생성 엔진 ---
def generate_guitar_band_song(progression_name, strum_type, total_bars, bpm, sample_rate):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    total_duration = total_bars * bar_dur
    total_samples = int(sample_rate * total_duration)

    guitar_track = np.zeros(total_samples)
    piano_pad_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)

    # 가요풍 대표 코드 사전 (주파수 세트: 루트, 3도, 5도, 7도 등)
    # C Major / A Minor 스케일 기준 대표 코드들
    chord_library = {
        "C": [261.63, 329.63, 392.00, 523.25],       # C Major
        "Am": [220.00, 261.63, 329.63, 440.00],     # A Minor
        "F": [174.61, 220.00, 261.63, 349.23],      # F Major
        "G": [196.00, 246.94, 293.66, 392.00],      # G Major
        "Dm": [146.83, 174.61, 220.00, 293.66],     # D Minor
        "Em": [164.81, 196.00, 246.94, 329.63],     # E Minor
        "Am7": [220.00, 261.63, 329.63, 392.00],    # A minor 7
        "Fmaj7": [174.61, 220.00, 261.63, 329.63],  # F major 7
        "G7": [196.00, 246.94, 293.66, 349.23],     # G dominant 7
    }

    # 선택한 진행 방식에 따른 마디별 코드 매핑
    if "I - V - VIm - IV (발라드 국민 진행: C - G - Am - F)" in progression_name:
        bar_chords = ["C", "G", "Am", "F"]
        bass_roots = [130.81, 98.00, 110.00, 87.31] # C2, G2, A2, F2
    elif "VIm - IV - I - V (감성 팝 진행: Am - F - C - G)" in progression_name:
        bar_chords = ["Am", "F", "C", "G"]
        bass_roots
