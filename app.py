import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎵 원클릭 저작권 무료 가요 작곡기",
    page_icon="📻",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 커스텀 CSS (왕초보 맞춤형 깔끔 디자인) ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 600px !important;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .main-title-box {
        background: linear-gradient(135deg, #1e1b4b 0%, #3b82f6 100%);
        padding: 24px 20px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
        text-align: center;
    }
    .card-box {
        background-color: #1e293b;
        border: 2px solid #334155;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    div.stButton > button {
        border-radius: 14px !important;
        font-size: 1.05rem !important;
        font-weight: bold !important;
        padding: 12px 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 음계 음고 주파수 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C6": 1046.50
}

# --- 부드러운 자연 음색 합성 엔진 (ADSR 오버랩 적용) ---
def synth_smooth_tone(freq, duration, sample_rate=44100, inst="piano"):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if freq <= 0 or len(t) == 0:
        return np.zeros_like(t)
    
    if inst == "piano": # 따뜻한 피아노
        sound = (0.6 * np.sin(2 * np.pi * freq * t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.12 * np.sin(2 * np.pi * freq * 3 * t) +
                 0.05 * np.sin(2 * np.pi * freq * 4 * t))
        env = np.exp(-2.5 * t / duration)
    elif inst == "guitar": # 부드러운 통기타
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        env = np.exp(-3.5 * t / duration)
    elif inst == "string": # 서정적 현악기
        vib = 1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * t)
        sound = (0.5 * np.sin(2 * np.pi * freq * vib * t) +
                 0.35 * np.sin(2 * np.pi * freq * 2 * vib * t))
        att = np.ones_like(t)
        att_len = int(0.15 * len(t))
        if att_len > 0:
            att[:att_len] = np.linspace(0, 1, att_len)
        env = att * np.exp(-1.0 * t / duration)
    else: # 베이스
        sound = (0.7 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t))
        env = np.exp(-2.0 * t / duration)
        
    return sound * env

# --- 부드러운 드럼 사운드 ---
def synth_soft_drum(drum_type, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if len(t) == 0:
        return np.array([])
    if drum_type == "kick":
        f = np.linspace(110, 35, len(t))
        return 0.7 * np.sin(2 * np.pi * f * t) * np.exp(-12 * t / duration)
    elif drum_type == "snare":
        n = np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-16 * t / duration)
        b = 0.3 * np.sin(2 * np.pi * 160 * t) * np.exp(-18 * t / duration)
        return n + b
    elif drum_type == "hihat":
        return 0.2 * np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-40 * t / duration)
    return np.zeros_like(t)

# --- 안전한 오디오 슬라이스 합성 함수 ---
def add_audio_clip(target_arr, clip_arr, start_idx):
    if len(clip_arr) == 0:
        return
    end_idx = min(len(target_arr), start_idx + len(clip_arr))
    add_len = end_idx - start_idx
    if add_len > 0:
        target_arr[start_idx:end_idx] += clip_arr[:add_len]

# --- 가요 패턴 자동 생성기 ---
def make_kpop_song(style_name, mood_name, sample_rate=44100):
    # 스타일에 따른 템포와 코드 진행 설정
    if "발라드" in style_name:
        bpm = 80
        progression = [("C4", "G3", "A3", "F3"), ("C4", "Am3", "Dm3", "G3")]
        inst = "piano"
    elif "댄스" in style_name:
        bpm = 124
        progression = [("Am3", "F3", "C4", "G3"), ("F3", "G3", "Em3", "Am3")]
        inst = "guitar"
    elif "시티팝" in style_name:
        bpm = 105
        progression = [("C4", "Em3", "F3", "G3"), ("Am3", "Em3", "F3", "G3")]
        inst = "string"
    else: # 포크 가요
        bpm = 92
        progression = [("C4", "G3", "Am3", "Em3"), ("F3", "C4", "Dm3", "G3")]
        inst = "guitar"

    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    bar_samples = int(sample_rate * bar_dur)
    total_bars = 4 # 4마디 가요 멜로디 테마
    total_samples = bar_samples * total_bars

    melody_track = np.zeros(total_samples)
    chord_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)

    # 마디별 코드 화음 정의
    chord_notes_map = {
        "C4": ([261.63, 329.63, 392.00], 130.81),
        "G3": ([196.00, 246.94, 293.66], 98.00),
        "A3": ([220.00, 261.63, 329.63], 110.00),
        "Am3": ([220.00, 261.63, 329.63], 110.00),
        "F3": ([174.61, 220.00, 261.63], 87.31),
        "Em3": ([164.81, 196.00, 246.94], 82.41),
        "Dm3": ([146.83, 174.61, 220.00], 73.42)
    }

    scale_notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 783.99]

    # 마디 생성
    prog_pair = progression[0] if "밝은" in mood_name or "설레는" in mood_name else progression[1]
    
    for bar_idx in range(total_bars):
        bar_start = bar_idx * bar_samples
        chord_name = prog_pair[bar_idx % len(prog_pair)]
        freqs, bass_f = chord_notes_map.get(chord_name, ([261.63, 329.63, 392.00], 130.81))

        # 1. 멜로디 생성 (자연스럽고 부드럽게 이어지는 가요풍)
        # 마디당 4개의 음표
        for n_i in range(4):
            note_time = bar_start + int(n_i * (bar_samples / 4))
            dur = beat_dur * 0.95
            
            # 화음 내 음표 또는 스케일 음표 선택하여 감성적 멜로디 구성
            if n_i % 2 == 0:
                mel_f = random.choice(freqs) * (2 if "댄스" in style_name else 1)
            else:
                mel_f = random.choice(scale_notes)
                
            mel_clip = synth_smooth_tone(mel_f, dur, sample_rate, inst)
            add_audio_clip(melody_track, mel_clip * 0.5, note_time)

        # 2. 반주 코드 & 베이스 생성
        for slot in range(8): # 8분음표 단위
            slot_time = bar_start + int(slot * (bar_samples / 8))
            slot_dur = (beat_dur / 2) * 1.8
            
            # 코드 반주
            if slot % 2 == 0 or "댄스" in style_name:
                for cf in freqs:
                    c_clip = synth_smooth_tone(cf, slot_dur, sample_rate, "piano")
                    add_audio_clip(chord_track, c_clip * 0.25, slot_time)
            
            # 베이스
            if slot in [0, 4] or ("댄스" in style_name and slot in [0, 3, 6]):
                b_clip = synth_smooth_tone(bass_f, slot_dur * 1.5, sample_rate, "bass")
                add_audio_clip(bass_track, b_clip * 0.45, slot_time)

            # 드럼
            if "댄스" in style_name:
                if slot % 2 == 0:
                    add_audio_clip(drum_track, synth_soft_drum("kick", beat_dur/2, sample_rate) * 0.6, slot_time)
                if slot in [2, 6]:
                    add_audio_clip(drum_track, synth_soft_drum("snare", beat_dur/2, sample_rate) * 0.5, slot_time)
                add_audio_clip(drum_track, synth_soft_drum("hihat", beat_dur/2, sample_rate) * 0.25, slot_time)
            else:
                if slot == 0:
                    add_audio_clip(drum_track, synth_soft_drum("kick", beat_dur/2, sample_rate) * 0.5, slot_time)
                if slot == 4:
                    add_audio_clip(drum_track, synth_soft_drum("snare", beat_dur/2, sample_rate) * 0.4, slot_time)

    # 전체 믹싱
    full_mix = melody_track + chord_track + bass_track + drum_track
    max_v = np.max(np.abs(full_mix))
    if max_v > 0:
        full_mix = (full_mix / max_v) * 0.9

    return full_mix

# --- 헤더 ---
st.markdown("""
<div class="main-title-box">
    <h1 style="margin:0; font-size: 1.8rem; color: #ffffff;">📻 초간단 원클릭 가요 작곡기</h1>
    <p style="margin-top: 10px; font-size: 1.02rem; color: #e2e8f0; opacity: 0.95;">
        음악을 전혀 몰라도 괜찮아요! 클릭 한 번으로 <b>100% 저작권 자유로운 평범하고 부드러운 가요</b>가 자동 완성됩니다.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="card-box">', unsafe_allow_html=True)
st.markdown("### 🎛️ 원하는 음악 느낌만 골라보세요")

col1, col2 = st.columns(2)
with col1:
    style_choice = st.selectbox(
        "🎵 가요 장르 스타일:",
        ["☕ 감성 팝 발라드", "💃 신나는 K-POP 댄스", "🌇 8090 낭만 시티팝", "🎸 따뜻한 어쿠스틱 포크"]
    )
with col2:
    mood_choice = st.selectbox(
        "✨ 곡의 분위기:",
        ["✨ 설레고 밝은 분위기", "🌧️ 아련하고 차분한 분위기"]
    )

st.markdown('</div>', unsafe_allow_html=True)

# 메인 작곡 버튼
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🎶 [클릭] 나만의 가요 한 곡 만들기!", type="primary", use_container_width=True):
    with st.spinner("🎧 부드러운 가요 멜로디와 반주를 정성껏 만들고 있습니다..."):
        sample_rate = 44100
        generated_audio = make_kpop_song(style_choice, mood_choice, sample_rate)
        
        # WAV 오디오 변환
        audio_int16 = (generated_audio * 32767).astype(np.int16)
        buf = io.BytesIO()
        wavfile.write(buf, sample_rate, audio_int16)
        wav_bytes = buf.getvalue()
        
        st.session_state["my_song_wav"] = wav_bytes
        st.session_state["my_song_info"] = f"{style_choice} ({mood_choice})"

if "my_song_wav" in st.session_state:
    st.success(f"🎉 **{st.session_state['my_song_info']}** 스타일의 자연스러운 가요가 완성되었습니다!")
    
    st.markdown("#### 🎧 완성된 가요 들어보기")
    st.audio(st.session_state["my_song_wav"], format="audio/wav")
    
    st.download_button(
        label="💾 완성된 가요 음원 저장하기 (.wav) - 저작권 100% 무료",
        data=st.session_state["my_song_wav"],
        file_name="my_kpop_music.wav",
        mime="audio/wav",
        use_container_width=True
    )
    
    st.info("💡 **저작권 안내**: 이 음원은 파이썬 순수 오디오 알고리즘으로 즉석 생성된 100% 자작 음원으로, 유튜브 배경음, 개인 소장 등 어디서나 저작권 제약 없이 자유롭게 사용하실 수 있습니다!")
