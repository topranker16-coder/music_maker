import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎹 AI 멀티 악기 자동 합주 & 편곡 스튜디오",
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

# --- 정갈한 12음계 순서 ---
SCALE_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def get_transposed_freq(base_freq, semitones):
    return base_freq * (2 ** (semitones / 12.0))

# --- 샘플 멜로디 템플릿 ---
SAMPLE_MELODIES = {
    "✨ K-POP 댄스 훅 (신나는 멜로디)": [
        ("E5", 0.5), ("G5", 0.5), ("A5", 0.5), ("A5", 0.5), ("G5", 0.5), ("E5", 0.5), ("D5", 0.5), ("E5", 1.0),
        ("G5", 0.5), ("A5", 0.5), ("C6", 1.0), ("B5", 0.5), ("A5", 0.5), ("G5", 1.0)
    ],
    "☕ 감성 발라드 테마 (서정적)": [
        ("C4", 1.0), ("E4", 1.0), ("G4", 1.0), ("B4", 1.0), ("A4", 1.0), ("G4", 0.5), ("F4", 0.5), ("E4", 2.0),
        ("F4", 1.0), ("E4", 1.0), ("D4", 1.0), ("C4", 2.0)
    ],
    "🎻 캐논 변주곡풍 (클래식 앙상블)": [
        ("E5", 1.0), ("D5", 1.0), ("C5", 1.0), ("B4", 1.0), ("A4", 1.0), ("G4", 1.0), ("A4", 1.0), ("B4", 1.0),
        ("C5", 1.0), ("B4", 1.0), ("A4", 1.0), ("G4", 1.0), ("F4", 1.0), ("E4", 1.0), ("F4", 1.0), ("G4", 1.0)
    ],
    "🔔 학교종이 땡땡땡": [
        ("G4", 0.5), ("G4", 0.5), ("A4", 0.5), ("A4", 0.5), ("G4", 0.5), ("G4", 0.5), ("E4", 1.0),
        ("G4", 0.5), ("G4", 0.5), ("E4", 0.5), ("E4", 0.5), ("D4", 2.0)
    ]
}

# --- 음원 합성 함수 (고품질 악기별 ADSR & 배음) ---
def synthesize_instrument(freq, duration, sample_rate, inst_type="🎹 그랜드 피아노"):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if freq <= 0 or len(t) == 0:
        return np.zeros(max(1, int(sample_rate * duration)))
    
    if "피아노" in inst_type:
        sound = (0.55 * np.sin(2 * np.pi * freq * t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.12 * np.sin(2 * np.pi * freq * 3 * t) +
                 0.08 * np.sin(2 * np.pi * freq * 4 * t))
        envelope = np.exp(-3.2 * t / max(0.01, duration))
        return sound * envelope

    elif "기타" in inst_type:
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        envelope = np.exp(-4.5 * t / max(0.01, duration))
        pluck = np.random.uniform(-0.15, 0.15, len(t)) * np.exp(-35.0 * t / max(0.01, duration))
        return (sound + pluck) * envelope

    elif "바이올린" in inst_type or "현악기" in inst_type or "첼로" in inst_type:
        vibrato = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t)
        sound = (0.5 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * vibrato * t))
        attack_len = int(0.12 * len(t))
        attack = np.ones_like(t)
        if attack_len > 0:
            attack[:attack_len] = np.linspace(0, 1, attack_len)
        release = np.exp(-1.2 * t / max(0.01, duration))
        return sound * attack * release

    elif "신디사이저" in inst_type or "신스" in inst_type:
        sound = np.zeros_like(t)
        for k in range(1, 7):
            sound += (0.35 / k) * np.sin(2 * np.pi * freq * k * t)
        envelope = np.exp(-2.0 * t / max(0.01, duration))
        return sound * envelope

    elif "플루트" in inst_type or "관악기" in inst_type:
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t)
        sound = np.sin(2 * np.pi * freq * vibrato * t) + 0.12 * np.sin(2 * np.pi * freq * 2 * t)
        breath = 0.03 * np.random.uniform(-1, 1, len(t))
        attack_len = int(0.08 * len(t))
        attack = np.ones_like(t)
        if attack_len > 0:
            attack[:attack_len] = np.linspace(0, 1, attack_len)
        release = np.exp(-1.8 * t / max(0.01, duration))
        return (sound + breath) * attack * release

    else: # 기본 피아노
        return np.sin(2 * np.pi * freq * t) * np.exp(-3.0 * t / max(0.01, duration))

# --- 드럼 합성 엔진 ---
def synthesize_drum(drum_type, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if len(t) == 0:
        return np.zeros(1)
    if drum_type == "kick":
        freq_sweep = np.linspace(130, 35, len(t))
        sound = 0.8 * np.sin(2 * np.pi * freq_sweep * t) * np.exp(-14 * t / max(0.01, duration))
        return sound
    elif drum_type == "snare":
        noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-18 * t / max(0.01, duration))
        body = 0.4 * np.sin(2 * np.pi * 180 * t) * np.exp(-20 * t / max(0.01, duration))
        return noise + body
    elif drum_type == "hihat":
        noise = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-45 * t / max(0.01, duration))
        return noise
    elif drum_type == "rimshot":
        sound = 0.5 * np.sin(2 * np.pi * 400 * t) * np.exp(-30 * t / max(0.01, duration))
        return sound
    return np.zeros_like(t)

# --- 안전 슬라이스 도우미 함수 ---
def add_sound_slice(target_array, sound_slice, start_idx):
    if len(sound_slice) == 0:
        return
    end_idx = min(len(target_array), start_idx + len(sound_slice))
    valid_len = end_idx - start_idx
    if valid_len > 0:
        target_array[start_idx:end_idx] += sound_slice[:valid_len]

# --- 화성학 코드 및 앙상블 합주 자동 편곡 생성 엔진 ---
def generate_auto_arrangement(melody_notes, style, main_inst, enable_harmony_ensemble, bpm, sample_rate, mix_vols):
    beat_dur = 60.0 / bpm
    
    # 1. 멜로디의 으뜸음(Root Key) 자동 감지 및 화성 이조(Transposition)
    first_note = melody_notes[0][0] if melody_notes else "C4"
    root_note = first_note[:-1] # "C", "G", "E" 등
    
    # Root Key 음계 인덱스 계산 (C=0, C#=1, D=2, ..., B=11)
    root_idx = SCALE_NOTES.index(root_note) if root_note in SCALE_NOTES else 0
    semi_shift = root_idx # C 기준으로 몇 반음 차이나는지
    
    # 2. 메인 멜로디 트랙 생성 (옵션: 2성부/3성부 앙상블 화음 덧붙이기)
    melody_audio_list = []
    
    # 세컨드 앙상블 보조 악기 선정 (주 악기와 어울리는 듀엣 악기)
    second_inst = "🎻 바이올린 / 현악기" if "피아노" in main_inst else ("🎷 감성 플루트 / 목관" if "바이올린" in main_inst else "🎹 그랜드 피아노")
    
    for note, dur_multiplier in melody_notes:
        dur = dur_multiplier * beat_dur
        freq = NOTE_FREQS.get(note, 261.63)
        
        # 주 멜로디 연주
        m_sound = synthesize_instrument(freq, dur, sample_rate, main_inst)
        
        # [앙상블 모드] 3도 위 화음 + 보조 악기 합주 레이어링!
        if enable_harmony_ensemble:
            harmony_freq_3rd = get_transposed_freq(freq, 4) # 3도(4반음) 위 화음
            harmony_sound = 0.4 * synthesize_instrument(harmony_freq_3rd, dur, sample_rate, second_inst)
            m_sound = m_sound + harmony_sound
            
        melody_audio_list.append(m_sound)
        
    melody_track = np.concatenate(melody_audio_list) if melody_audio_list else np.zeros(sample_rate)
    total_samples = len(melody_track)
    
    # 3. 멜로디 조성에 맞춰 자동 이조된 4코드 진행 (I - V - vi - IV 명곡 화성)
    # C Major 기본 화성을 root_idx 만큼 반음 이동
    c_base_chords = [
        [261.63, 329.63, 392.00], # C Major (C4, E4, G4)
        [196.00, 246.94, 293.66], # G Major (G3, B3, D4)
        [220.00, 261.63, 329.63], # A Minor (A3, C4, E4)
        [174.61, 220.00, 261.63]  # F Major (F3, A3, C4)
    ]
    c_base_bass = [130.81, 98.00, 110.00, 87.31] # C2, G2, A2, F2
    
    # 이조된 코드 및 베이스 주파수 세트
    chord_progression = [[get_transposed_freq(f, semi_shift) for f in chord] for chord in c_base_chords]
    bass_progression = [get_transposed_freq(f, semi_shift) for f in c_base_bass]
    
    chord_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)
    
    # 4. 주 악기에 어울리는 코드 및 베이스 세션 악기 맞춤 할당
    if "바이올린" in main_inst or "오케스트라" in style:
        chord_inst_type = "🎻 바이올린 / 현악기"
        bass_inst_type = "🎻 바이올린 / 현악기" # 첼로/더블베이스 톤
    elif "기타" in main_inst or "록" in style:
        chord_inst_type = "🎸 어쿠스틱 기타"
        bass_inst_type = "🩵 80s 레트로 신디사이저"
    elif "신디사이저" in main_inst or "댄스" in style:
        chord_inst_type = "🩵 80s 레트로 신디사이저"
        bass_inst_type = "🩵 80s 레트로 신디사이저"
    else: # 피아노, 플루트 등
        chord_inst_type = "🎹 그랜드 피아노"
        bass_inst_type = "🎹 그랜드 피아노"
        
    # 마디(Bar) 단위 분할 (1마디 = 4박)
    bar_dur = 4 * beat_dur
    bar_samples = int(sample_rate * bar_dur)
    total_bars = int(np.ceil(total_samples / bar_samples))
    
    for b in range(total_bars):
        start_s = b * bar_samples
        end_s = min(total_samples, (b + 1) * bar_samples)
        curr_len = end_s - start_s
        if curr_len <= 0:
            break
            
        chord_freqs = chord_progression[b % len(chord_progression)]
        bass_freq = bass_progression[b % len(bass_progression)]
        
        chord_bar = np.zeros(curr_len)
        bass_bar = np.zeros(curr_len)
        drum_bar = np.zeros(curr_len)
        
        # 16분음표 단위 슬롯 (1마디 = 16슬롯)
        sub_len = max(1, bar_samples // 16)
        for slot in range(16):
            s_idx = slot * sub_len
            if s_idx >= curr_len:
                break
            e_idx = min(curr_len, (slot + 1) * sub_len)
            s_dur = (e_idx - s_idx) / sample_rate
            if s_dur <= 0:
                continue
                
            # A) 코드 반주 리듬 연주
            if "댄스" in style:
                if slot in [0, 3, 6, 8, 10, 12, 14]:
                    cf = chord_freqs[slot % len(chord_freqs)]
                    c_snd = 0.35 * synthesize_instrument(cf, s_dur * 1.5, sample_rate, chord_inst_type)
                    add_sound_slice(chord_bar, c_snd, s_idx)
            elif "발라드" in style or "오케스트라" in style:
                if slot % 2 == 0:
                    cf = chord_freqs[(slot // 2) % len(chord_freqs)]
                    c_snd = 0.4 * synthesize_instrument(cf, s_dur * 2.5, sample_rate, chord_inst_type)
                    add_sound_slice(chord_bar, c_snd, s_idx)
            else: # 록 밴드
                if slot % 4 == 0:
                    for cf in chord_freqs:
                        c_snd = 0.22 * synthesize_instrument(cf, s_dur * 3.5, sample_rate, chord_inst_type)
                        add_sound_slice(chord_bar, c_snd, s_idx)
                        
            # B) 베이스 트랙 연주
            if slot in [0, 8] or ("댄스" in style and slot in [0, 6, 10]):
                b_snd = 0.55 * synthesize_instrument(bass_freq, s_dur * 2.5, sample_rate, bass_inst_type)
                add_sound_slice(bass_bar, b_snd, s_idx)
                
            # C) 드럼 비트 패턴
            if "댄스" in style:
                if slot % 4 == 0:
                    add_sound_slice(drum_bar, synthesize_drum("kick", s_dur, sample_rate), s_idx)
                if slot in [4, 12]:
                    add_sound_slice(drum_bar, synthesize_drum("snare", s_dur, sample_rate), s_idx)
                if slot % 2 == 1:
                    add_sound_slice(drum_bar, synthesize_drum("hihat", s_dur, sample_rate), s_idx)
            elif "발라드" in style:
                if slot == 0:
                    add_sound_slice(drum_bar, 0.7 * synthesize_drum("kick", s_dur, sample_rate), s_idx)
                if slot == 8:
                    add_sound_slice(drum_bar, 0.6 * synthesize_drum("rimshot", s_dur, sample_rate), s_idx)
                if slot % 4 == 2:
                    add_sound_slice(drum_bar, 0.3 * synthesize_drum("hihat", s_dur, sample_rate), s_idx)
            elif "록" in style:
                if slot in [0, 8, 10]:
                    add_sound_slice(drum_bar, 0.8 * synthesize_drum("kick", s_dur, sample_rate), s_idx)
                if slot in [4, 12]:
                    add_sound_slice(drum_bar, 0.8 * synthesize_drum("snare", s_dur, sample_rate), s_idx)
                if slot % 2 == 0:
                    add_sound_slice(drum_bar, 0.4 * synthesize_drum("hihat", s_dur, sample_rate), s_idx)
            else: # 오케스트라
                if slot == 0:
                    add_sound_slice(drum_bar, 0.6 * synthesize_drum("kick", s_dur, sample_rate), s_idx)
                if slot == 8:
                    add_sound_slice(drum_bar, 0.5 * synthesize_drum("rimshot", s_dur, sample_rate), s_idx)

        add_sound_slice(chord_track, chord_bar, start_s)
        add_sound_slice(bass_track, bass_bar, start_s)
        add_sound_slice(drum_track, drum_bar, start_s)
        
    # 5. 트랙별 볼륨 믹싱 적용
    v_mel, v_cho, v_bas, v_dru = mix_vols
    mix_melody = melody_track * v_mel
    mix_chord = chord_track * v_cho
    mix_bass = bass_track * v_bas
    mix_drum = drum_track * v_dru
    
    mixed_full = mix_melody + mix_chord + mix_bass + mix_drum
    
    # 피크 노멀라이제이션
    max_val = np.max(np.abs(mixed_full))
    if max_val > 0:
        mixed_full = (mixed_full / max_val) * 0.92
        
    return mixed_full, mix_melody, mix_chord, mix_bass, mix_drum

# --- 세션 상태 초기화 ---
if "melody_notes" not in st.session_state:
    st.session_state.melody_notes = [("C4", 1.0), ("E4", 1.0), ("G4", 1.0), ("C5", 1.0)]

# --- 헤더 UI ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.1rem;">🎼 AI 멀티 악기 자동 합주 & 편곡 스튜디오</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.02rem;">
        찍어주신 멜로디에 맞춰 <b>자동 3도 화음 앙상블 합주</b>와 <b>멜로디 조성(Key) 자동 이조 반주</b>가 완벽하게 어우러집니다!
    </p>
</div>
""", unsafe_allow_html=True)

# --- 메인 레이아웃 (좌: 컨트롤 & 건반, 우: 세팅 & 트랙 믹서) ---
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("### 🎹 1. 멜로디 음표 찍기")
    
    # 템플릿 샘플 선택
    st.caption("✨ 빠른 합주 체험을 위한 대표 멜로디 샘플:")
    selected_sample = st.selectbox("샘플 멜로디 불러오기:", ["직접 작성하기"] + list(SAMPLE_MELODIES.keys()))
    if selected_sample != "직접 작성하기":
        if st.button("📥 선택한 샘플 멜로디 적용하기"):
            st.session_state.melody_notes = list(SAMPLE_MELODIES[selected_sample])
            st.rerun()

    # 건반 패드 입력
    st.markdown("#### 🎵 피아노 건반 눌러서 음 추가하기")
    octave_choice = st.radio("옥타브 선택:", ["3옥타브 (낮음)", "4옥타브 (기본)", "5옥타브 (높음)"], index=1, horizontal=True)
    oct_num = "3" if "3" in octave_choice else ("5" if "5" in octave_choice else "4")
    
    dur_choice = st.select_slider("박자 길이 (음표):", options=[0.25, 0.5, 1.0, 2.0], value=0.5,
                                  format_func=lambda x: "16분음표 (0.25박)" if x==0.25 else ("8분음표 (0.5박)" if x==0.5 else ("4분음표 (1박)" if x==1.0 else "2분음표 (2박)")))

    # 건반 버튼 그리드
    keys_natural = ["C", "D", "E", "F", "G", "A", "B"]
    keys_sharp = ["C#", "D#", "F#", "G#", "A#"]
    
    st.caption("⚪ 흰 건반 (기본음)")
    cols_nat = st.columns(7)
    for idx, k in enumerate(keys_natural):
        note_name = f"{k}{oct_num}"
        with cols_nat[idx]:
            if st.button(note_name, key=f"btn_nat_{note_name}"):
                st.session_state.melody_notes.append((note_name, dur_choice))
                st.rerun()
                
    st.caption("⬛ 검은 건반 (반음)")
    cols_sharp = st.columns(5)
    for idx, k in enumerate(keys_sharp):
        note_name = f"{k}{oct_num}"
        with cols_sharp[idx]:
            if st.button(note_name, key=f"btn_sharp_{note_name}"):
                st.session_state.melody_notes.append((note_name, dur_choice))
                st.rerun()

    # 현재 찍힌 음표 시퀀서 표시
    st.markdown('<div class="sequencer-box">', unsafe_allow_html=True)
    st.markdown("##### 🎶 현재 입력된 멜로디 시퀀스")
    if len(st.session_state.melody_notes) == 0:
        st.info("건반을 눌러 음표를 추가해 보세요!")
    else:
        badge_html = "".join([f'<span class="note-badge">{n} ({d}박)</span>' for n, d in st.session_state.melody_notes])
        st.markdown(badge_html, unsafe_allow_html=True)
        
    c_del1, c_del2 = st.columns(2)
    with c_del1:
        if st.button("⬅️ 마지막 음 지우기") and len(st.session_state.melody_notes) > 0:
            st.session_state.melody_notes.pop()
            st.rerun()
    with c_del2:
        if st.button("🗑️ 전체 음표 초기화"):
            st.session_state.melody_notes = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### 🎛️ 2. 악기 & 앙상블 합주 세팅")
    
    main_inst = st.selectbox(
        "🎸 메인 멜로디 악기 선택:",
        ["🎹 그랜드 피아노", "🎸 어쿠스틱 기타", "🎻 바이올린 / 현악기", "🩵 80s 레트로 신디사이저", "🎷 감성 플루트 / 목관"]
    )
    
    # ★ 핵심 신기능: 2성부/3성부 앙상블 합주 모드 스위치
    enable_harmony_ensemble = st.toggle(
        "🎻 2성부/3성부 앙상블 화음 레이어링 (자동 합주)",
        value=True,
        help="켜면 멜로디에 어울리는 보조 악기(바이올린/플루트 등)가 3도 화음을 동시에 연주하여 웅장한 합주 효과를 만들어냅니다!"
    )
    
    band_style = st.selectbox(
        "🎵 AI 자동 편곡 장르 스타일:",
        ["🕺 K-POP / 신나는 팝 댄스", "☕ 감성적인 로파이 발라드", "🎸 파워풀 록 밴드", "🎻 웅장한 오케스트라"]
    )
    
    bpm = st.slider("⏱️ 연주 템포 (BPM):", min_value=60, max_value=160, value=120 if "댄스" in band_style else (85 if "발라드" in band_style else 115))
    
    st.markdown("---")
    st.markdown("### 🎚️ 3. 트랙별 볼륨 믹서")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_mel = st.slider("🎷 메인 멜로디/합주 볼륨", 0.0, 1.2, 0.9, 0.1)
        v_cho = st.slider("🎹 화성 코드 볼륨", 0.0, 1.2, 0.7, 0.1)
    with col_v2:
        v_bas = st.slider("🎸 베이스 라인 볼륨", 0.0, 1.2, 0.8, 0.1)
        v_dru = st.slider("🥁 드럼 비트 볼륨", 0.0, 1.2, 0.85, 0.1)

# --- 자동 편곡 음원 생성 버튼 및 오디오 플레이어 ---
st.markdown("---")
st.subheader("🎧 풀버전 자동 편곡 앙상블 완성하기")

if st.button("🚀 AI 풀밴드 앙상블 합주 시작하기!", type="primary", use_container_width=True):
    if len(st.session_state.melody_notes) == 0:
        st.warning("⚠️ 먼저 피아노 건반을 눌러 최소 1개 이상의 음표를 추가해 주세요!")
    else:
        with st.spinner("🎵 AI가 멜로디의 조성을 분석하여 3도 화음 합주와 맞춤형 화성 세션을 조율 중입니다..."):
            sample_rate = 44100
            mix_vols = (v_mel, v_cho, v_bas, v_dru)
            
            full_audio, track_mel, track_cho, track_bas, track_dru = generate_auto_arrangement(
                st.session_state.melody_notes, band_style, main_inst, enable_harmony_ensemble, bpm, sample_rate, mix_vols
            )
            
            # WAV 변환 함수
            def to_wav_bytes(audio_np):
                audio_int16 = (audio_np * 32767).astype(np.int16)
                buf = io.BytesIO()
                wavfile.write(buf, sample_rate, audio_int16)
                return buf.getvalue()
                
            full_wav_bytes = to_wav_bytes(full_audio)
            
            st.success(f"🎉 **[{main_inst}]**와 **[{band_style}]** 스타일에 맞춘 화려한 앙상블 합주곡이 완성되었습니다!")
            
            # 메인 풀버전 플레이어
            st.markdown("#### 🌟 마스터링 풀버전 앙상블 들어보기")
            st.audio(full_wav_bytes, format="audio/wav")
            
            st.download_button(
                label="💾 마스터링 음원 다운로드 (.wav)",
                data=full_wav_bytes,
                file_name="ai_ensemble_music.wav",
                mime="audio/wav"
            )
            
            # 트랙별 분리 듣기 익스팬더
            with st.expander("🔍 트랙별 개별 음원 들어보기 (멀티 스템)"):
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.caption("1️⃣ 메인 멜로디 & 3도 화음 앙상블 트랙")
                    st.audio(to_wav_bytes(track_mel), format="audio/wav")
                    st.caption("2️⃣ 조성 맞춤형 화성 코드 트랙")
                    st.audio(to_wav_bytes(track_cho), format="audio/wav")
                with t_col2:
                    st.caption("3️⃣ 세션 베이스 라인 트랙")
                    st.audio(to_wav_bytes(track_bas), format="audio/wav")
                    st.caption("4️⃣ 리듬 드럼 & 퍼커션 비트 트랙")
                    st.audio(to_wav_bytes(track_dru), format="audio/wav")
