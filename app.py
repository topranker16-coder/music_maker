import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎼 프로 가요풍 풀밴드 협연 스튜디오",
    page_icon="🎶",
    layout="wide",
)

# --- CSS 스타일 ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
    }
    .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 24px 28px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
        border: 1px solid #6366f1;
    }
    .chord-badge {
        display: inline-block;
        background: #4f46e5;
        color: white;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: bold;
        margin: 4px;
        font-size: 0.95rem;
        border: 1px solid #818cf8;
    }
    .status-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 18px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 음계 주파수 테이블 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99, "A5": 880.00
}

# --- 다양한 악기 음색 합성 엔진 ---
def synthesize_instrument(freq, duration, sample_rate, inst_type="피아노"):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if freq <= 0:
        return np.zeros_like(t)

    if inst_type == "피아노":
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        envelope = np.exp(-3.0 * t / duration)
    elif inst_type == "어쿠스틱 기타":
        sound = (0.45 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        pluck = np.random.uniform(-0.1, 0.1, len(t)) * np.exp(-30.0 * t / duration)
        envelope = np.exp(-4.0 * t / duration)
        sound += pluck
    elif inst_type == "스트링(현악기)":
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t)
        sound = (0.4 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
                 0.2 * np.sin(2 * np.pi * freq * 3 * vibrato * t))
        attack = min(int(0.1 * len(t)), len(t))
        envelope = np.ones_like(t)
        if attack > 0:
            envelope[:attack] = np.linspace(0, 1, attack)
        envelope *= np.exp(-1.2 * t / duration)
    elif inst_type == "일렉 기타":
        sound = (0.5 * np.arcsin(np.sin(2 * np.pi * freq * t)) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t))
        envelope = np.exp(-2.5 * t / duration)
    else: # 신디사이저 패드
        sound = 0.6 * np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 1.5 * t)
        envelope = np.exp(-1.5 * t / duration)

    fade_len = min(int(0.01 * sample_rate), len(t) // 2)
    if fade_len > 0:
        envelope[:fade_len] *= np.linspace(0, 1, fade_len)
        envelope[-fade_len:] *= np.linspace(1, 0, fade_len)

    return sound * envelope

def synthesize_drum_hit(drum_type, duration, sample_rate):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if drum_type == "kick":
        f_sweep = np.linspace(130, 30, len(t))
        return 0.75 * np.sin(2 * np.pi * f_sweep * t) * np.exp(-14 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-18 * t / duration)
        body = 0.35 * np.sin(2 * np.pi * 180 * t) * np.exp(-20 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return 0.2 * np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-45 * t / duration)
    return np.zeros_like(t)

# --- 풀밴드 협연 곡 생성 엔진 ---
def generate_full_band_song(progression_name, lead_inst, total_bars, bpm, sample_rate):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    total_duration = total_bars * bar_dur
    total_samples = int(sample_rate * total_duration)

    melody_track = np.zeros(total_samples)       # 리드 멜로디 (보컬 라인)
    harmony_track = np.zeros(total_samples)     # 스트링 보조 화음
    piano_track = np.zeros(total_samples)       # 피아노 아르페지오
    guitar_track = np.zeros(total_samples)      # 리듬 기타 스트럼
    bass_track = np.zeros(total_samples)        # 베이스 기타
    drum_track = np.zeros(total_samples)        # 드럼 세트

    chord_library = {
        "C": [261.63, 329.63, 392.00, 523.25],
        "Am": [220.00, 261.63, 329.63, 440.00],
        "F": [174.61, 220.00, 261.63, 349.23],
        "G": [196.00, 246.94, 293.66, 392.00],
        "Dm": [146.83, 174.61, 220.00, 293.66],
        "Em": [164.81, 196.00, 246.94, 329.63],
        "Am7": [220.00, 261.63, 329.63, 392.00],
        "Fmaj7": [174.61, 220.00, 261.63, 329.63],
        "G7": [196.00, 246.94, 293.66, 349.23],
    }

    if "I - V - VIm - IV" in progression_name:
        bar_chords = ["C", "G", "Am", "F"]
        bass_roots = [130.81, 98.00, 110.00, 87.31]
        scale_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    elif "VIm - IV - I - V" in progression_name:
        bar_chords = ["Am", "F", "C", "G"]
        bass_roots = [110.00, 87.31, 130.81, 98.00]
        scale_notes = ["A3", "C4", "D4", "E4", "F4", "G4", "A4", "C5"]
    elif "I - VIm - IV - V" in progression_name:
        bar_chords = ["C", "Am", "F", "G"]
        bass_roots = [130.81, 110.00, 87.31, 98.00]
        scale_notes = ["C4", "E4", "G4", "A4", "C5", "B4", "A4", "G4"]
    else:
        bar_chords = ["Am7", "Fmaj7", "G7", "C"]
        bass_roots = [110.00, 87.31, 98.00, 130.81]
        scale_notes = ["A3", "C4", "E4", "G4", "B4", "C5", "D5", "E5"]

    bar_samples = int(sample_rate * bar_dur)

    for b in range(total_bars):
        b_start = b * bar_samples
        b_end = min(total_samples, (b + 1) * bar_samples)
        b_len = b_end - b_start
        if b_len <= 0:
            break

        c_name = bar_chords[b % len(bar_chords)]
        chord_freqs = chord_library[c_name]
        bass_freq = bass_roots[b % len(bass_roots)]

        # 마디별 멜로디 및 악기 협연 전개 (8분음표/16분음표 단위 밀도화)
        sub_notes = 8
        sub_dur = bar_dur / sub_notes
        sub_samples = int(sample_rate * sub_dur)

        for sub in range(sub_notes):
            m_s = b_start + sub * sub_samples
            m_e = min(total_samples, m_s + sub_samples)
            curr_dur = (m_e - m_s) / sample_rate
            if curr_dur <= 0 or m_s >= total_samples:
                continue

            # 1. 리드 멜로디 (보컬 라인
