import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎸 코드 진행 기반 AI 자동 작곡 스튜디오",
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
    .chord-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 10px 18px;
        border-radius: 14px;
        font-weight: 800;
        margin: 6px;
        font-size: 1.1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        text-align: center;
        min-width: 90px;
    }
    .sequencer-box {
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

# --- 음계 및 코드 주파수 테이블 ---
NOTE_FREQS = {
    "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.00, "A2": 110.00, "B2": 123.47,
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77,
    "C6": 1046.50
}

CHORD_DB = {
    "C": {"notes": ["C4", "E4", "G4"], "root": "C2", "scale": ["C4", "D4", "E4", "G4", "A4"]},
    "G": {"notes": ["G3", "B3", "D4"], "root": "G2", "scale": ["G4", "A4", "B4", "D5", "E5"]},
    "Am": {"notes": ["A3", "C4", "E4"], "root": "A2", "scale": ["A4", "C5", "D5", "E5", "G5"]},
    "Em": {"notes": ["E3", "G3", "B3"], "root": "E2", "scale": ["E4", "G4", "A4", "B4", "D5"]},
    "F": {"notes": ["F3", "A3", "C4"], "root": "F2", "scale": ["F4", "A4", "C5", "D5", "F5"]},
    "Dm": {"notes": ["D3", "F3", "A3"], "root": "D2", "scale": ["D4", "F4", "G4", "A4", "C5"]},
    "FM7": {"notes": ["F3", "A3", "C4", "E4"], "root": "F2", "scale": ["F4", "A4", "C5", "E5"]},
    "E7": {"notes": ["E3", "G#3", "B3", "D4"], "root": "E2", "scale": ["E4", "G#4", "B4", "D5"]},
    "Am7": {"notes": ["A3", "C4", "E4", "G4"], "root": "A2", "scale": ["A4", "C5", "E5", "G5"]},
    "G7": {"notes": ["G3", "B3", "D4", "F4"], "root": "G2", "scale": ["G4", "B4", "D5", "F5"]}
}

CHORD_PRESETS = {
    "🎶 K-Pop 머니 코드 (C - G - Am - F)": ["C", "G", "Am", "F"],
    "☕ 감성 발라드/캐논 진행 (C - G - Am - Em - F - C - F - G)": ["C", "G", "Am", "Em", "F", "C", "F", "G"],
    "🌇 감성 시티팝/재즈 (FM7 - E7 - Am7 - C)": ["FM7", "E7", "Am7", "C"],
    "🎸 청춘 포크/록 기타 (C - Am - Dm - G7)": ["C", "Am", "Dm", "G7"],
    "🔥 감성 짝사랑 코드 (Am - F - C - G)": ["Am", "F", "C", "G"]
}

# --- 음원 합성 함수 ---
def synthesize_instrument(freq, duration, sample_rate, inst_type="piano"):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if freq <= 0 or len(t) == 0:
        return np.zeros_like(t)
    
    if inst_type == "🎸 어쿠스틱 기타":
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.35 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.18 * np.sin(2 * np.pi * freq * 3 * t))
        envelope = np.exp(-4.2 * t / duration)
        pluck = np.random.uniform(-0.1, 0.1, len(t)) * np.exp(-40.0 * t / duration)
        return (sound + pluck) * envelope
    elif inst_type == "🎹 그랜드 피아노":
        sound = (0.55 * np.sin(2 * np.pi * freq * t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.12 * np.sin(2 * np.pi * freq * 3 * t))
        envelope = np.exp(-3.0 * t / duration)
        return sound * envelope
    elif inst_type == "🎻 바이올린 / 현악기":
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.5 * t)
        sound = (0.5 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * vibrato * t))
        attack_len = int(0.1 * len(t))
        attack = np.ones_like(t)
        if attack_len > 0:
            attack[:attack_len] = np.linspace(0, 1, attack_len)
        release = np.exp(-1.2 * t / duration)
        return sound * attack * release
    elif inst_type == "🩵 80s 레트로 신디사이저":
        sound = np.zeros_like(t)
        for k in range(1, 6):
            sound += (0.35 / k) * np.sin(2 * np.pi * freq * k * t)
        envelope = np.exp(-2.2 * t / duration)
        return sound * envelope
    else:
        return np.sin(2 * np.pi * freq * t) * np.exp(-3.0 * t / duration)

def synthesize_drum(drum_type, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if len(t) == 0:
        return np.zeros(0)
    if drum_type == "kick":
        freq_sweep = np.linspace(130, 35, len(t))
        return 0.85 * np.sin(2 * np.pi * freq_sweep * t) * np.exp(-14 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-18 * t / duration)
        body = 0.4 * np.sin(2 * np.pi * 180 * t) * np.exp(-20 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-45 * t / duration)
    return np.zeros_like(t)

def add_sound_slice(target_arr, sound_data, start_idx):
    if len(sound_data) == 0 or start_idx >= len(target_arr):
        return
    end_idx = min(len(target_arr), start_idx + len(sound_data))
    copy_len = end_idx - start_idx
    if copy_len > 0:
        target_arr[start_idx:end_idx] += sound_data[:copy_len]

# --- 코드 기반 풀 오케스트레이션 생성 엔진 ---
def generate_chord_composition(chords, style, main_inst, bpm, sample_rate, generate_melody=True):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    bar_samples = int(sample_rate * bar_dur)
    
    total_samples = len(chords) * bar_samples
    if total_samples <= 0:
        return np.zeros(sample_rate), np.zeros(sample_rate), np.zeros(sample_rate), np.zeros(sample_rate), np.zeros(sample_rate)
        
    melody_track = np.zeros(total_samples)
    chord_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)
    
    sub_len_16th = bar_samples // 16
    dur_16th = sub_len_16th / sample_rate
    
    random.seed(42) # 재생성 일정함 유지
    
    for bar_idx, chord_name in enumerate(chords):
        c_info = CHORD_DB.get(chord_name, CHORD_DB["C"])
        c_notes = c_info["notes"]
        c_root_note = c_info["root"]
        c_scale = c_info["scale"]
        
        c_root_freq = NOTE_FREQS.get(c_root_note, 130.81)
        c_freqs = [NOTE_FREQS.get(n, 261.63) for n in c_notes]
        
        bar_start_idx = bar_idx * bar_samples
        
        # 16슬롯 마디 루프
        for slot in range(16):
            slot_start = bar_start_idx + (slot * sub_len_16th)
            
            # 1. 코드 반주 (Strumming / Arpeggio)
            if "기타" in main_inst or "록" in style or "포크" in style:
                # 기타 스트럼 리듬 (0, 4, 8, 10, 12, 14 슬롯)
                if slot in [0, 4, 8, 10, 12, 14]:
                    for f_idx, cf in enumerate(c_freqs):
                        strum_delay = int(f_idx * 0.015 * sample_rate)
                        strum_sound = 0.25 * synthesize_instrument(cf, dur_16th * 3, sample_rate, "🎸 어쿠스틱 기타")
                        add_sound_slice(chord_track, strum_sound, slot_start + strum_delay)
            else:
                # 피아노/신스 8분음표 아르페지오 (짝수 슬롯)
                if slot % 2 == 0:
                    cf = c_freqs[(slot // 2) % len(c_freqs)]
                    arp_sound = 0.3 * synthesize_instrument(cf, dur_16th * 2, sample_rate, "🎹 그랜드 피아노")
                    add_sound_slice(chord_track, arp_sound, slot_start)
                    
            # 2. 묵직한 베이스 라인 (Root Note)
            if slot in [0, 8] or ("댄스" in style and slot in [0, 6, 10]):
                bass_sound = 0.55 * synthesize_instrument(c_root_freq, dur_16th * 3, sample_rate, "🩵 80s 레트로 신디사이저")
                add_sound_slice(bass_track, bass_sound, slot_start)
                
            # 3. 드럼 리듬 비트
            if "댄스" in style:
                if slot % 4 == 0:
                    add_sound_slice(drum_track, synthesize_drum("kick", dur_16th * 2, sample_rate), slot_start)
                if slot in [4, 12]:
                    add_sound_slice(drum_track, synthesize_drum("snare", dur_16th * 2, sample_rate), slot_start)
                if slot % 2 == 1:
                    add_sound_slice(drum_track, 0.4 * synthesize_drum("hihat", dur_16th, sample_rate), slot_start)
            else: # 발라드 / 포크 / 록
                if slot in [0, 10]:
                    add_sound_slice(drum_track, 0.8 * synthesize_drum("kick", dur_16th * 2, sample_rate), slot_start)
                if slot in [4, 12]:
                    add_sound_slice(drum_track, 0.7 * synthesize_drum("snare", dur_16th * 2, sample_rate), slot_start)
                if slot % 2 == 0:
                    add_sound_slice(drum_track, 0.3 * synthesize_drum("hihat", dur_16th, sample_rate), slot_start)
                    
            # 4. 코드에 맞는 리드 멜로디 자동 창작 (AI Melody Gen)
            if generate_melody:
                # 8분음표/4분음표 단위로 싱코페이션 멜로디 생성
                if slot in [0, 3, 6, 8, 11, 14]:
                    m_note = random.choice(c_scale)
                    m_freq = NOTE_FREQS.get(m_note, 392.00)
                    m_dur = dur_16th * (3 if slot in [0, 8] else 2)
                    mel_sound = 0.85 * synthesize_instrument(m_freq, m_dur, sample_rate, main_inst)
                    add_sound_slice(melody_track, mel_sound, slot_start)

    mixed_full = melody_track + chord_track + bass_track + drum_track
    max_v = np.max(np.abs(mixed_full))
    if max_v > 0:
        mixed_full = (mixed_full / max_v) * 0.92
        
    return mixed_full, melody_track, chord_track, bass_track, drum_track

# --- 세션 상태 ---
if "chord_list" not in st.session_state:
    st.session_state.chord_list = ["C", "G", "Am", "F"]

# --- UI 레이아웃 ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.1rem;">🎸 마디별 기타/피아노 코드 작곡 스튜디오</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.02rem;">
        복잡한 악보 없이 <b>[마디별 코드]</b>만 입력해 보세요! 대중가요/팝송처럼 어울리는 <b>리드 멜로디, 화음 반주, 베이스, 드럼</b>이 완벽하게 만들어집니다.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.markdown("### 🎼 1. 마디별 코드 진행 구성하기")
    
    # 프리셋 선택
    preset_choice = st.selectbox("✨ 대중가요 인기 코드 진행 선택:", ["직접 구성하기"] + list(CHORD_PRESETS.keys()))
    if preset_choice != "직접 구성하기":
        if st.button("📥 선택한 코드 진행 적용하기"):
            st.session_state.chord_list = list(CHORD_PRESETS[preset_choice])
            st.rerun()
            
    st.markdown("#### 🎸 마디에 코드 추가하기")
    c_cols = st.columns(5)
    chord_keys = list(CHORD_DB.keys())
    for idx, c_name in enumerate(chord_keys):
        with c_cols[idx % 5]:
            if st.button(f"+ {c_name}", key=f"btn_chord_{c_name}"):
                st.session_state.chord_list.append(c_name)
                st.rerun()
                
    # 현재 코드 시퀀스
    st.markdown('<div class="sequencer-box">', unsafe_allow_html=True)
    st.markdown("##### 🎶 현재 마디별 코드 진행")
    if not st.session_state.chord_list:
        st.info("코드를 선택해 마디를 구성해 보세요!")
    else:
        html_chords = "".join([f'<span class="chord-badge">Bar {i+1}<br>{c}</span>' for i, c in enumerate(st.session_state.chord_list)])
        st.markdown(html_chords, unsafe_allow_html=True)
        
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("⬅️ 마지막 마디 지우기") and st.session_state.chord_list:
            st.session_state.chord_list.pop()
            st.rerun()
    with c_btn2:
        if st.button("🗑️ 전체 코드 초기화"):
            st.session_state.chord_list = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🎛️ 2. 악기 & 밴드 세팅")
    
    main_inst = st.selectbox(
        "🎸 메인 악기 선택:",
        ["🎸 어쿠스틱 기타", "🎹 그랜드 피아노", "🎻 바이올린 / 현악기", "🩵 80s 레트로 신디사이저"]
    )
    
    band_style = st.selectbox(
        "🎵 편곡 스타일 / 리듬:",
        ["🕺 K-Pop / 신나는 팝 댄스", "☕ 감성 포크 / 어쿠스틱 발라드", "🎸 파워풀 록 밴드"]
    )
    
    bpm = st.slider("⏱️ 템포 (BPM):", 60, 160, 115)
    
    gen_mel = st.checkbox("✨ 코드에 어울리는 리드 멜로디도 AI가 자동 창작하기", value=True)

st.markdown("---")
st.subheader("🎧 코드 기반 풀밴드 곡 생성하기")

if st.button("🚀 선택한 코드로 완성곡 연주하기!", type="primary", use_container_width=True):
    if not st.session_state.chord_list:
        st.warning("⚠️ 코드를 최소 1개 이상 추가해 주세요!")
    else:
        with st.spinner("🎸 입력하신 마디별 코드에 맞춰 멜로디, 화음, 베이스, 드럼을 합주하는 중입니다..."):
            sample_rate = 44100
            mixed_full, mel_t, cho_t, bas_t, dru_t = generate_chord_composition(
                st.session_state.chord_list, band_style, main_inst, bpm, sample_rate, gen_mel
            )
            
            def to_bytes(arr):
                arr_i16 = (arr * 32767).astype(np.int16)
                b = io.BytesIO()
                wavfile.write(b, sample_rate, arr_i16)
                return b.getvalue()
                
            full_wav = to_bytes(mixed_full)
            
            st.success(f"🎉 **[{' - '.join(st.session_state.chord_list)}]** 코드 진행으로 완성된 멋진 음악입니다!")
            
            st.markdown("#### 🌟 풀밴드 합주 들어보기")
            st.audio(full_wav, format="audio/wav")
            
            st.download_button(
                label="💾 완성곡 다운로드 (.wav)",
                data=full_wav,
                file_name="chord_based_song.wav",
                mime="audio/wav"
            )
            
            with st.expander("🔍 트랙별 개별 소리 들어보기"):
                t1, t2 = st.columns(2)
                with t1:
                    st.caption("1️⃣ 메인 멜로디")
                    st.audio(to_bytes(mel_t), format="audio/wav")
                    st.caption("2️⃣ 코드 반주")
                    st.audio(to_bytes(cho_t), format="audio/wav")
                with t2:
                    st.caption("3️⃣ 베이스 라인")
                    st.audio(to_bytes(bas_t), format="audio/wav")
                    st.caption("4️⃣ 드럼 비트")
                    st.audio(to_bytes(dru_t), format="audio/wav")
