import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎼 AI 멜로디 이어주기 & 자유 길이 창작 스튜디오",
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
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 24px 28px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #6366f1;
    }
    .anchor-badge {
        display: inline-block;
        background: #6366f1;
        color: white;
        padding: 6px 14px;
        border-radius: 12px;
        font-weight: bold;
        margin: 4px;
        font-size: 0.9rem;
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

# --- 음계 주파수 및 스케일 테이블 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99,
    "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25, "F5": 698.46, "F#5": 739.99,
    "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77, "C6": 1046.50
}

SCALE_NOTES = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "G5", "A5", "C6"]

# --- 고품질 음원 합성 (ADSR 봉우리 + 부드러운 오버랩) ---
def synthesize_note(freq, duration, sample_rate, inst_type="piano"):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if freq <= 0:
        return np.zeros_like(t)

    if inst_type == "🎹 피아노":
        sound = (0.6 * np.sin(2 * np.pi * freq * t) +
                 0.25 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.1 * np.sin(2 * np.pi * freq * 3 * t) +
                 0.05 * np.sin(2 * np.pi * freq * 4 * t))
        envelope = np.exp(-3.0 * t / duration)
        
    elif inst_type == "🎸 어쿠스틱 기타":
        sound = (0.55 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t))
        pluck = np.random.uniform(-0.1, 0.1, len(t)) * np.exp(-30.0 * t / duration)
        envelope = np.exp(-4.0 * t / duration)
        sound = (sound + pluck)
        
    elif inst_type == "🎻 감성 바이올린":
        vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t)
        sound = (0.5 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * vibrato * t))
        attack_len = min(int(0.15 * len(t)), len(t))
        envelope = np.ones_like(t)
        if attack_len > 0:
            envelope[:attack_len] = np.linspace(0, 1, attack_len)
        envelope *= np.exp(-1.2 * t / duration)
        
    else: # 신디사이저
        sound = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
        envelope = np.exp(-2.2 * t / duration)

    # 페이드인/아웃으로 클릭음 제거
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
        f_sweep = np.linspace(120, 35, len(t))
        return 0.7 * np.sin(2 * np.pi * f_sweep * t) * np.exp(-12 * t / duration)
    elif drum_type == "snare":
        noise = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-16 * t / duration)
        body = 0.3 * np.sin(2 * np.pi * 170 * t) * np.exp(-18 * t / duration)
        return noise + body
    elif drum_type == "hihat":
        return 0.25 * np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-40 * t / duration)
    return np.zeros_like(t)

# --- 징검다리 음 기반 멜로디 창작 & 이음새 보정 엔진 ---
def generate_creative_song(user_anchors, total_bars, bpm, main_inst, sample_rate):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    total_duration = total_bars * bar_dur
    total_samples = int(sample_rate * total_duration)

    melody_track = np.zeros(total_samples)
    chord_track = np.zeros(total_samples)
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)

    # 1. 징검다리 음(Anchors)을 바탕으로 전체 마디별 타겟 음계 구성
    # user_anchors = {bar_idx: "C4", ...}
    bar_target_notes = []
    default_notes = ["C4", "E4", "G4", "A4", "F4", "G4", "C5", "B4"]
    
    for b in range(total_bars):
        if b in user_anchors:
            bar_target_notes.append(user_anchors[b])
        else:
            # 부드럽게 이어지도록 이전 음 근처의 스케일 음 자동 추정
            if len(bar_target_notes) > 0:
                prev_n = bar_target_notes[-1]
                p_idx = SCALE_NOTES.index(prev_n) if prev_n in SCALE_NOTES else 2
                # 근처 1~2음 내에서 자연스럽게 이동
                step = random.choice([-2, -1, 0, 1, 2])
                new_idx = max(0, min(len(SCALE_NOTES) - 1, p_idx + step))
                bar_target_notes.append(SCALE_NOTES[new_idx])
            else:
                bar_target_notes.append(default_notes[b % len(default_notes)])

    # 코드 진행 도출 (C Major 기본 4코드 순환 및 변형)
    chord_palette = [
        [261.63, 329.63, 392.00], # C Major
        [196.00, 246.94, 293.66], # G Major
        [220.00, 261.63, 329.63], # A Minor
        [174.61, 220.00, 261.63]  # F Major
    ]
    bass_palette = [130.81, 98.00, 110.00, 87.31] # C2, G2, A2, F2

    bar_samples = int(sample_rate * bar_dur)

    # 마디별 창작 연주 합성
    for b in range(total_bars):
        b_start = b * bar_samples
        b_end = min(total_samples, (b + 1) * bar_samples)
        b_len = b_end - b_start
        if b_len <= 0:
            break

        start_note = bar_target_notes[b]
        end_note = bar_target_notes[(b + 1) % total_bars]

        s_idx = SCALE_NOTES.index(start_note) if start_note in SCALE_NOTES else 2
        e_idx = SCALE_NOTES.index(end_note) if end_note in SCALE_NOTES else 4

        # 한 마디 안에서 4개~8개의 음을 부드럽게 창작하여 이어줌 (Melodic Infilling)
        # 리듬 패턴 다양화 (마디 고조감 연출)
        num_sub_notes = 4 if (b % 4 in [0, 1]) else 8
        sub_dur = bar_dur / num_sub_notes
        sub_samples = int(sample_rate * sub_dur)

        # 멜로디 생성
        for sub in range(num_sub_notes):
            m_s = b_start + int(sub * sub_samples)
            m_e = min(total_samples, m_s + sub_samples)
            curr_dur = (m_e - m_s) / sample_rate
            if curr_dur <= 0 or m_s >= total_samples:
                continue

            # start_note에서 end_note로 부드럽게 보간(Interpolation)되는 음 선택
            ratio = sub / float(num_sub_notes)
            curr_scale_idx = int(s_idx + (e_idx - s_idx) * ratio)
            # 약간의 멜로디적 변화 부여
            if sub % 2 == 1:
                curr_scale_idx += random.choice([-1, 0, 1])
            curr_scale_idx = max(0, min(len(SCALE_NOTES) - 1, curr_scale_idx))

            note_name = SCALE_NOTES[curr_scale_idx]
            freq = NOTE_FREQS.get(note_name, 261.63)

            mel_sound = synthesize_note(freq, curr_dur, sample_rate, main_inst)
            mel_len = min(len(mel_sound), m_e - m_s)
            if mel_len > 0:
                melody_track[m_s:m_s + mel_len] += mel_sound[:mel_len]

        # 코드 & 베이스 & 드럼 생성
        chord_freqs = chord_palette[b % len(chord_palette)]
        bass_freq = bass_palette[b % len(bass_palette)]

        # 16분음표 박자 단위 (마디당 16 슬롯)
        slot_samples = bar_samples // 16
        for slot in range(16):
            sl_s = b_start + slot * slot_samples
            sl_e = min(total_samples, sl_s + slot_samples)
            sl_dur = (sl_e - sl_s) / sample_rate
            if sl_dur <= 0 or sl_s >= total_samples:
                continue

            # 코드 반주 (아르페지오/스트럼)
            if slot % 4 == 0 or (b >= 4 and slot % 2 == 0):
                cf = chord_freqs[(slot // 4) % len(chord_freqs)]
                ch_sound = 0.25 * synthesize_note(cf, sl_dur * 2, sample_rate, "🎹 피아노")
                ch_len = min(len(ch_sound), sl_e - sl_s)
                if ch_len > 0:
                    chord_track[sl_s:sl_s + ch_len] += ch_sound[:ch_len]

            # 베이스
            if slot in [0, 8] or (b % 2 == 1 and slot in [0, 6, 10]):
                bs_sound = 0.45 * synthesize_note(bass_freq, sl_dur * 3, sample_rate, "신디사이저")
                bs_len = min(len(bs_sound), sl_e - sl_s)
                if bs_len > 0:
                    bass_track[sl_s:sl_s + bs_len] += bs_sound[:bs_len]

            # 드럼 리듬
            if slot % 4 == 0:
                dk = synthesize_drum_hit("kick", sl_dur, sample_rate)
                dk_len = min(len(dk), sl_e - sl_s)
                if dk_len > 0:
                    drum_track[sl_s:sl_s + dk_len] += dk[:dk_len]
            if slot in [4, 12]:
                ds = synthesize_drum_hit("snare", sl_dur, sample_rate)
                ds_len = min(len(ds), sl_e - sl_s)
                if ds_len > 0:
                    drum_track[sl_s:sl_s + ds_len] += ds[:ds_len]
            if slot % 2 == 1:
                dh = synthesize_drum_hit("hihat", sl_dur, sample_rate)
                dh_len = min(len(dh), sl_e - sl_s)
                if dh_len > 0:
                    drum_track[sl_s:sl_s + dh_len] += dh[:dh_len]

    # 트랙 믹싱 & 피크 노멀라이제이션
    full_audio = 0.85 * melody_track + 0.6 * chord_track + 0.7 * bass_track + 0.75 * drum_track
    max_val = np.max(np.abs(full_audio))
    if max_val > 0:
        full_audio = (full_audio / max_val) * 0.92

    return full_audio, total_duration

# --- 세션 상태 ---
if "user_anchors" not in st.session_state:
    st.session_state.user_anchors = {0: "C4", 2: "G4", 4: "A4", 6: "E4"}

# --- UI 레이아웃 ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.1rem;">🎼 AI 멜로디 이어주기 & 자유 길이 작곡 스튜디오</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.02rem;">
        중간중간 <b>원하는 포인트 음(징검다리 음)</b>을 찍어두시면, AI가 음과 음 사이를 부드럽고 자연스럽게 창작하여 이어줍니다.<br>
        원하시는 <b>연주 길이(마디/초)</b>도 마음대로 설정해 보세요! 100% 저작권 무료 자작곡입니다.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.markdown("### ⏱️ 1. 곡 연주 길이 & 악기 설정")
    
    total_bars = st.select_slider(
        "📏 연주 길이 선택 (마디 수 / 재생 시간):",
        options=[4, 8, 12, 16, 24, 32],
        value=8,
        format_func=lambda x: f"{x}마디 (약 {int(x * 2.0)}초 연주)"
    )
    
    main_inst = st.selectbox(
        "🎸 주 멜로디 악기 음색:",
        ["🎹 피아노", "🎸 어쿠스틱 기타", "🎻 감성 바이올린"]
    )
    
    bpm = st.slider("⏱️ 템포 (BPM):", min_value=70, max_value=140, value=115)

    st.markdown("---")
    st.markdown("### 📍 2. 중간 징검다리 음(포인트 음) 지정하기")
    st.caption("특정 마디에 내가 꼭 듣고 싶은 음표를 찍어두세요. AI가 그 음으로 향하도록 부드럽게 멜로디를 창작합니다!")

    c_bar, c_note, c_add = st.columns([1.2, 1.2, 1.0])
    with c_bar:
        target_bar = st.selectbox("마디 위치 선택:", [f"{i+1}번째 마디" for i in range(total_bars)])
        bar_idx = int(target_bar.replace("번째 마디", "")) - 1
    with c_note:
        chosen_note = st.selectbox("원하는 음표 선택:", SCALE_NOTES, index=0)
    with c_add:
        st.write("")
        st.write("")
        if st.button("➕ 음표 지정하기", type="secondary"):
            st.session_state.user_anchors[bar_idx] = chosen_note
            st.rerun()

    # 현재 지정된 음표 목록
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown("##### 📌 현재 지정된 징검다리 음표 현황:")
    if not st.session_state.user_anchors:
        st.info("지정된 포인트 음이 없습니다. AI가 자유롭게 창작합니다.")
    else:
        badge_list = []
        for b_i in sorted(st.session_state.user_anchors.keys()):
            if b_i < total_bars:
                badge_list.append(f'<span class="anchor-badge">{b_i + 1}마디: {st.session_state.user_anchors[b_i]}</span>')
        st.markdown("".join(badge_list), unsafe_allow_html=True)

    if st.button("🗑️ 지정 음표 전체 초기화"):
        st.session_state.user_anchors = {}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🪄 3. 나만의 창작 곡 생성")
    st.info("💡 **작곡 원리**: 지정하신 마디의 음표들을 거쳐가도록, AI가 사이사이에 부드러운 경과음과 화성을 자동으로 작곡해 드립니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 나만의 맞춤 창작곡 연주하기!", type="primary", use_container_width=True):
        with st.spinner("🎵 AI가 징검다리 음표를 연결하여 부드러운 가요풍 곡을 창작 중입니다..."):
            sample_rate = 44100
            generated_audio, act_dur = generate_creative_song(
                st.session_state.user_anchors, total_bars, bpm, main_inst, sample_rate
            )

            # WAV 변환
            audio_int16 = (generated_audio * 32767).astype(np.int16)
            buf = io.BytesIO()
            wavfile.write(buf, sample_rate, audio_int16)
            wav_bytes = buf.getvalue()

            st.success(f"🎉 **약 {int(act_dur)}초 분량 ({total_bars}마디)**의 나만의 창작 곡이 완성되었습니다!")
            st.audio(wav_bytes, format="audio/wav")

            st.download_button(
                label="💾 창작 음원 파일 다운로드 (.wav)",
                data=wav_bytes,
                file_name=f"my_custom_song_{total_bars}bars.wav",
                mime="audio/wav"
            )
