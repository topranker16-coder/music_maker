import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎼 AI 멀티 악기 자동 편곡 스튜디오",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1000px !important;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .header-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 24px 28px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #6366f1;
    }
    .note-badge {
        display: inline-block;
        background: #3b82f6;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        margin: 4px;
        font-size: 0.9rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .sequencer-box {
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .track-card {
        background: #1e293b;
        border-left: 5px solid #6366f1;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 음계 주파수 테이블 (C3 ~ C6) ---
NOTE_FREQS = {
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77,
    "C6": 1046.50
}

# --- 샘플 코드/멜로디 템플릿 ---
SAMPLE_CHORD_PROGRESSIONS = {
    "🎶 K-Pop 머니 코드 (C - G - Am - F)": [("C4", 1.0), ("G3", 1.0), ("A3", 1.0), ("F3", 1.0)],
    "☕ 감성 발라드/캐논 (C - G - Am - Em - F - C - F - G)": [("C4", 1.0), ("G3", 1.0), ("A3", 1.0), ("E3", 1.0), ("F3", 1.0), ("C4", 1.0), ("F3", 1.0), ("G3", 1.0)],
    "🌇 감성 시티팝/재즈 (F - G - Em - Am)": [("F3", 1.0), ("G3", 1.0), ("E3", 1.0), ("A3", 1.0)],
    "🎸 청춘 포크/록 (C - Am - Dm - G)": [("C4", 1.0), ("A3", 1.0), ("D3", 1.0), ("G3", 1.0)]
}

# --- 안전 슬라이스 합성 보조 함수 ---
def add_sound_slice(target_array, start_idx, sound_data):
    end_idx = start_idx + len(sound_data)
    if start_idx >= len(target_array):
        return
    if end_idx > len(target_array):
        fit_len = len(target_array) - start_idx
        target_array[start_idx:len(target_array)] += sound_data[:fit_len]
    else:
        target_array[start_idx:end_idx] += sound_data

# --- 음원 합성 함수 (고품질 악기별 ADSR & 배음) ---
def synthesize_instrument(freq, duration, sample_rate, inst_type="piano"):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if freq <= 0 or len(t) == 0:
        return np.zeros_like(t)
    
    if inst_type == "🎹 그랜드 피아노":
        sound = (0.55 * np.sin(2 * np.pi * freq * t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.12 * np.sin(2 * np.pi * freq * 3 * t) +
                 0.08 * np.sin(2 * np.pi * freq * 4 * t))
        envelope = np.exp(-3.2 * t / duration)
        return sound * envelope

    elif inst_type == "🎸 어쿠스틱 기타":
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        envelope = np.exp(-4.5 * t / duration)
        pluck = np.random.uniform(-0.15, 0.15, len(t)) * np.exp(-35.0 * t / duration)
        return (sound + pluck) * envelope

    elif inst_type == "🎻 바이올린 / 현악기":
        vibrato = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t)
        sound = (0.5 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * vibrato * t))
        attack_len = int(0.12 * len(t))
        attack = np.ones_like(t)
        if attack_len > 0:
            attack[:attack_len] = np.linspace(0, 1, attack_len)
        release = np.exp(-1.2 * t / duration)
        return sound * attack * release

    elif inst_type == "🩵 80s 레트로 신디사이저":
        sound = np.zeros_like(t)
        for k in range(1, 7):
            sound += (0.35 / k) * np.sin(2 * np.pi * freq * k * t)
        envelope = np.exp(-2.0 * t / duration)
        return sound * envelope

    elif inst_type == "🎷 감성 플루트 / 목관":
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t)
        sound = np.sin(2 * np.pi * freq * vibrato * t) + 0.12 * np.sin(2 * np.pi * freq * 2 * t)
        breath = 0.03 * np.random.uniform(-1, 1, len(t))
        attack_len = int(0.08 * len(t))
        attack = np.ones_like(t)
        if attack_len > 0:
            attack[:attack_len] = np.linspace(0, 1, attack_len)
        release = np.exp(-1.8 * t / duration)
        return (sound + breath) * attack * release

    else:
        return np.sin(2 * np.pi * freq * t) * np.exp(-3.0 * t / duration)

# --- 드럼 합성 엔진 ---
def synthesize_drum(drum_type, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if len(t) == 0:
        return np.zeros(0)
    if drum_type == "kick":
        freq_sweep = np.linspace(130, 35, len(t))
        sound = 0.8 * np.sin(2 * np.pi * freq_sweep * t) * np.exp(-14 * t / duration)
        return sound
    elif drum_type == "snare":
        noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-18 * t / duration)
        body = 0.4 * np.sin(2 * np.pi * 180 * t) * np.exp(-20 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        noise = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-45 * t / duration)
        return noise
    elif drum_type == "rimshot":
        sound = 0.5 * np.sin(2 * np.pi * 400 * t) * np.exp(-30 * t / duration)
        return sound
    return np.zeros_like(t)

# --- 4트랙 원음(Unscaled Raw Tracks) 합성 엔진 ---
def generate_raw_tracks(melody_notes, style, main_inst, bpm, sample_rate, enable_harmony=True):
    beat_dur = 60.0 / bpm
    
    # 총 박자 수 및 샘플 수
    total_beats = sum([dur for _, dur in melody_notes]) if melody_notes else 4.0
    total_duration = total_beats * beat_dur
    total_samples = int(sample_rate * total_duration)
    
    raw_melody = np.zeros(total_samples)
    raw_chord = np.zeros(total_samples)
    raw_bass = np.zeros(total_samples)
    raw_drum = np.zeros(total_samples)
    
    # 1. 메인 멜로디 & 화음 앙상블 생성
    curr_sample_idx = 0
    for note, dur_multiplier in melody_notes:
        dur = dur_multiplier * beat_dur
        freq = NOTE_FREQS.get(note, 261.63)
        
        # 주 멜로디 음
        sound_main = synthesize_instrument(freq, dur, sample_rate, main_inst)
        add_sound_slice(raw_melody, curr_sample_idx, sound_main)
        
        # 자동 앙상블 화음 (3도 위 화음)
        if enable_harmony:
            harmony_freq = freq * 1.25 # 장3도 화음
            second_inst = "🎻 바이올린 / 현악기" if "피아노" in main_inst else "🎷 감성 플루트 / 목관"
            sound_harm = 0.4 * synthesize_instrument(harmony_freq, dur, sample_rate, second_inst)
            add_sound_slice(raw_melody, curr_sample_idx, sound_harm)
            
        curr_sample_idx += int(sample_rate * dur)
        
    # 2. 코드 및 베이스, 드럼 트랙 생성
    bar_dur = 4 * beat_dur
    bar_samples = int(sample_rate * bar_dur)
    total_bars = max(1, int(np.ceil(total_samples / bar_samples)))
    
    # 화성 코드 테이블 (C, G, Am, F 삼화음 및 베이스)
    chord_map = {
        "C": ([261.63, 329.63, 392.00], 130.81),
        "G": ([196.00, 246.94, 293.66], 98.00),
        "Am": ([220.00, 261.63, 329.63], 110.00),
        "F": ([174.61, 220.00, 261.63], 87.31)
    }
    prog_keys = ["C", "G", "Am", "F"]
    
    for b in range(total_bars):
        b_start = b * bar_samples
        b_end = min(total_samples, (b + 1) * bar_samples)
        b_len = b_end - b_start
        if b_len <= 0:
            break
            
        c_key = prog_keys[b % len(prog_keys)]
        chord_freqs, bass_freq = chord_map[c_key]
        
        # 16분음표 단위 슬롯 (1마디 = 16슬롯)
        sub_len = bar_samples // 16
        for slot in range(16):
            s_idx = b_start + slot * sub_len
            if s_idx >= total_samples:
                break
            s_dur = min(sub_len, total_samples - s_idx) / sample_rate
            if s_dur <= 0:
                continue
                
            # 코드 반주
            if "댄스" in style:
                if slot in [0, 3, 6, 8, 10, 12, 14]:
                    cf = chord_freqs[slot % len(chord_freqs)]
                    s_ch = 0.4 * synthesize_instrument(cf, s_dur, sample_rate, "🎹 그랜드 피아노")
                    add_sound_slice(raw_chord, s_idx, s_ch)
            elif "발라드" in style or "오케스트라" in style:
                if slot % 2 == 0:
                    cf = chord_freqs[(slot // 2) % len(chord_freqs)]
                    inst = "🎻 바이올린 / 현악기" if "오케스트라" in style else "🎹 그랜드 피아노"
                    s_ch = 0.45 * synthesize_instrument(cf, s_dur * 2, sample_rate, inst)
                    add_sound_slice(raw_chord, s_idx, s_ch)
            else: # 록 밴드
                if slot % 4 == 0:
                    for cf in chord_freqs:
                        s_ch = 0.25 * synthesize_instrument(cf, s_dur * 3, sample_rate, "🎸 어쿠스틱 기타")
                        add_sound_slice(raw_chord, s_idx, s_ch)
                        
            # 베이스 라인
            if slot in [0, 8] or ("댄스" in style and slot in [0, 6, 10]):
                s_ba = 0.6 * synthesize_instrument(bass_freq, s_dur * 2, sample_rate, "🩵 80s 레트로 신디사이저")
                add_sound_slice(raw_bass, s_idx, s_ba)
                
            # 드럼 비트
            if "댄스" in style:
                if slot % 4 == 0:
                    add_sound_slice(raw_drum, s_idx, synthesize_drum("kick", s_dur, sample_rate))
                if slot in [4, 12]:
                    add_sound_slice(raw_drum, s_idx, synthesize_drum("snare", s_dur, sample_rate))
                if slot % 2 == 1:
                    add_sound_slice(raw_drum, s_idx, synthesize_drum("hihat", s_dur, sample_rate))
            elif "발라드" in style:
                if slot == 0:
                    add_sound_slice(raw_drum, s_idx, 0.7 * synthesize_drum("kick", s_dur, sample_rate))
                if slot == 8:
                    add_sound_slice(raw_drum, s_idx, 0.6 * synthesize_drum("rimshot", s_dur, sample_rate))
                if slot % 4 == 2:
                    add_sound_slice(raw_drum, s_idx, 0.3 * synthesize_drum("hihat", s_dur, sample_rate))
            elif "록" in style:
                if slot in [0, 8, 10]:
                    add_sound_slice(raw_drum, s_idx, 0.8 * synthesize_drum("kick", s_dur, sample_rate))
                if slot in [4, 12]:
                    add_sound_slice(raw_drum, s_idx, 0.8 * synthesize_drum("snare", s_dur, sample_rate))
                if slot % 2 == 0:
                    add_sound_slice(raw_drum, s_idx, 0.4 * synthesize_drum("hihat", s_dur, sample_rate))
            else:
                if slot == 0:
                    add_sound_slice(raw_drum, s_idx, 0.6 * synthesize_drum("kick", s_dur, sample_rate))
                if slot == 8:
                    add_sound_slice(raw_drum, s_idx, 0.5 * synthesize_drum("rimshot", s_dur, sample_rate))

    return raw_melody, raw_chord, raw_bass, raw_drum, sample_rate

# --- 세션 상태 초기화 ---
if "melody_notes" not in st.session_state:
    st.session_state.melody_notes = [("C4", 1.0), ("G3", 1.0), ("A3", 1.0), ("F3", 1.0)]

# --- 헤더 UI ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.1rem;">🎼 AI 멀티 악기 마디별 코드 & 멜로디 작곡 스튜디오</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.02rem;">
        마디별 코드나 멜로디만 입력해 보세요! AI가 <b>실시간 멀티 악기 풀밴드</b>로 멋지게 완성해 드립니다.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 메인 레이아웃 (좌: 컨트롤 & 건반, 우: 세팅 & 트랙 믹서) ---
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("### 🎹 1. 마디별 코드 & 멜로디 구성하기")
    
    # 템플릿 샘플 선택
    st.caption("✨ 대표 대중가요 코드 진행 샘플:")
    selected_sample = st.selectbox("샘플 코드 진행 불러오기:", ["직접 구성하기"] + list(SAMPLE_CHORD_PROGRESSIONS.keys()))
    if selected_sample != "직접 구성하기":
        if st.button("📥 선택한 코드 진행 적용하기"):
            st.session_state.melody_notes = list(SAMPLE_CHORD_PROGRESSIONS[selected_sample])
            st.session_state.pop("generated_tracks", None)
            st.rerun()

    # 코드 / 음표 버튼 그리드
    st.markdown("#### 🎵 코드 / 음표 버튼 눌러서 추가하기")
    octave_choice = st.radio("옥타브 선택:", ["3옥타브 (낮음/베이스)", "4옥타브 (기본)", "5옥타브 (높음)"], index=1, horizontal=True)
    oct_num = "3" if "3" in octave_choice else ("5" if "5" in octave_choice else "4")
    
    dur_choice = st.select_slider("박자 길이 (음표/마디):", options=[0.25, 0.5, 1.0, 2.0], value=1.0,
                                  format_func=lambda x: "1/4마디 (0.25박)" if x==0.25 else ("1/2마디 (0.5박)" if x==0.5 else ("1마디 (1박)" if x==1.0 else "2마디 (2박)")))

    keys_natural = ["C", "D", "E", "F", "G", "A", "B"]
    keys_sharp = ["C#", "D#", "F#", "G#", "A#"]
    
    st.caption("⚪ 기본 코드 / 음표 (C, D, E, F, G, A, B)")
    cols_nat = st.columns(7)
    for idx, k in enumerate(keys_natural):
        note_name = f"{k}{oct_num}"
        with cols_nat[idx]:
            if st.button(note_name, key=f"btn_nat_{note_name}"):
                st.session_state.melody_notes.append((note_name, dur_choice))
                st.session_state.pop("generated_tracks", None)
                st.rerun()
                
    st.caption("⬛ 반음 코드 / 음표 (C#, D#, F#, G#, A#)")
    cols_sharp = st.columns(5)
    for idx, k in enumerate(keys_sharp):
        note_name = f"{k}{oct_num}"
        with cols_sharp[idx]:
            if st.button(note_name, key=f"btn_sharp_{note_name}"):
                st.session_state.melody_notes.append((note_name, dur_choice))
                st.session_state.pop("generated_tracks", None)
                st.rerun()

    # 시퀀서 박스
    st.markdown('<div class="sequencer-box">', unsafe_allow_html=True)
    st.markdown("##### 🎶 현재 구성된 마디별 코드 / 음표 시퀀스")
    if len(st.session_state.melody_notes) == 0:
        st.info("버튼을 눌러 코드나 음표를 추가해 보세요!")
    else:
        badge_html = "".join([f'<span class="note-badge">{n} ({d}마디)</span>' for n, d in st.session_state.melody_notes])
        st.markdown(badge_html, unsafe_allow_html=True)
        
    c_del1, c_del2 = st.columns(2)
    with c_del1:
        if st.button("⬅️ 마지막 마디 지우기") and len(st.session_state.melody_notes) > 0:
            st.session_state.melody_notes.pop()
            st.session_state.pop("generated_tracks", None)
            st.rerun()
    with c_del2:
        if st.button("🗑️ 전체 초기화"):
            st.session_state.melody_notes = []
            st.session_state.pop("generated_tracks", None)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### 🎛️ 2. 악기 & 편곡 스타일 세팅")
    
    main_inst = st.selectbox(
        "🎸 메인 악기 음색 선택:",
        ["🎹 그랜드 피아노", "🎸 어쿠스틱 기타", "🎻 바이올린 / 현악기", "🩵 80s 레트로 신디사이저", "🎷 감성 플루트 / 목관"]
    )
    
    band_style = st.selectbox(
        "🎵 AI 자동 편곡 스타일:",
        ["🕺 K-POP / 신나는 팝 댄스", "☕ 감성적인 로파이 발라드", "🎸 파워풀 록 밴드", "🎻 웅장한 오케스트라"]
    )
    
    enable_harmony = st.checkbox("🎻 2성부/3성부 앙상블 화음 레이어링 (자동 합주)", value=True)
    
    bpm = st.slider("⏱️ 연주 템포 (BPM):", min_value=60, max_value=160, value=120 if "댄스" in band_style else (85 if "발라드" in band_style else 115))
    
    st.markdown("---")
    st.markdown("### 🎚️ 3. 실시간 트랙별 볼륨 믹서")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_mel = st.slider("🎷 메인/앙상블 멜로디 볼륨", 0.0, 1.2, 0.9, 0.05)
        v_cho = st.slider("🎹 화성 코드 반주 볼륨", 0.0, 1.2, 0.75, 0.05)
    with col_v2:
        v_bas = st.slider("🎸 베이스 라인 볼륨", 0.0, 1.2, 0.8, 0.05)
        v_dru = st.slider("🥁 드럼 비트 볼륨", 0.0, 1.2, 0.85, 0.05)

# --- 자동 편곡 음원 생성 버튼 ---
st.markdown("---")
st.subheader("🎧 풀버전 자동 편곡 음원 완성하기")

if st.button("🚀 AI 풀밴드 앙상블 편곡 연주 생성하기!", type="primary", use_container_width=True):
    if len(st.session_state.melody_notes) == 0:
        st.warning("⚠️ 먼저 코드나 음표를 최소 1개 이상 추가해 주세요!")
    else:
        with st.spinner("🎵 AI가 코드 진행을 분석하여 트랙별 풀밴드 음원을 생성 중입니다..."):
            raw_mel, raw_cho, raw_bas, raw_dru, sr = generate_raw_tracks(
                st.session_state.melody_notes, band_style, main_inst, bpm, 44100, enable_harmony
            )
            # 세션 상태에 지속 저장 (Rerun 시에도 사라지지 않음)
            st.session_state["generated_tracks"] = {
                "raw_mel": raw_mel,
                "raw_cho": raw_cho,
                "raw_bas": raw_bas,
                "raw_dru": raw_dru,
                "sr": sr,
                "info": f"[{main_inst}] + [{band_style}] ({bpm} BPM)"
            }

# --- 음원 재생 및 트랙별 실시간 볼륨 적용 영역 ---
if "generated_tracks" in st.session_state:
    tr = st.session_state["generated_tracks"]
    sr = tr["sr"]
    
    # 실시간 볼륨 스케일링
    mix_mel = tr["raw_mel"] * v_mel
    mix_cho = tr["raw_cho"] * v_cho
    mix_bas = tr["raw_bas"] * v_bas
    mix_dru = tr["raw_dru"] * v_dru
    
    full_mix = mix_mel + mix_cho + mix_bas + mix_dru
    max_val = np.max(np.abs(full_mix))
    if max_val > 0:
        full_mix = (full_mix / max_val) * 0.92
        
    # WAV 오디오 바이너리 변환 함수
    def to_wav_bytes(audio_np):
        audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)
        buf = io.BytesIO()
        wavfile.write(buf, sr, audio_int16)
        return buf.getvalue()
        
    full_wav_bytes = to_wav_bytes(full_mix)
    
    st.success(f"🎉 **{tr['info']}** 편곡 음원 준비 완료! (볼륨 조절 시 실시간 반영됩니다)")
    
    # 1. 마스터링 완곡 플레이어
    st.markdown("#### 🌟 1. 마스터링 풀버전 앙상블 들어보기 (전체 합주)")
    st.audio(full_wav_bytes, format="audio/wav")
    
    st.download_button(
        label="💾 마스터링 완곡 음원 다운로드 (.wav)",
        data=full_wav_bytes,
        file_name="ai_ensemble_full_music.wav",
        mime="audio/wav"
    )
    
    # 2. 트랙별 개별 음원 실시간 들어보기
    st.markdown("#### 🔍 2. 트랙별 개별 음원 들어보기 (실시간 볼륨 반영)")
    st.caption("💡 각 트랙의 [▶] 버튼을 누르면 해당 악기만의 독주 소리를 들어보실 수 있습니다.")
    
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown('<div class="track-card"><b>1️⃣ 메인 & 앙상블 멜로디 트랙</b></div>', unsafe_allow_html=True)
        st.audio(to_wav_bytes(mix_mel), format="audio/wav")
        
        st.markdown('<div class="track-card"><b>2️⃣ 화성 코드 반주 트랙</b></div>', unsafe_allow_html=True)
        st.audio(to_wav_bytes(mix_cho), format="audio/wav")
        
    with t_col2:
        st.markdown('<div class="track-card"><b>3️⃣ 베이스 라인 트랙</b></div>', unsafe_allow_html=True)
        st.audio(to_wav_bytes(mix_bas), format="audio/wav")
        
        st.markdown('<div class="track-card"><b>4️⃣ 리듬 드럼 & 퍼커션 비트 트랙</b></div>', unsafe_allow_html=True)
        st.audio(to_wav_bytes(mix_dru), format="audio/wav")
