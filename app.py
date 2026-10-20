import io
import random
import numpy as np
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="🎼 프로 가요풍 AI 작곡 스튜디오",
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

# --- 가요풍 음계 및 주파수 테이블 ---
NOTE_FREQS = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99,
    "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25, "F5": 698.46, "F#5": 739.99,
    "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77, "C6": 1046.50
}

SCALE_NOTES = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "G5", "A5", "C6"]

# --- 악기별 고품질 신디사이징 (풍성한 배음 구조) ---
def synthesize_note(freq, duration, sample_rate, inst_type="🎹 그랜드 피아노"):
    num_samples = int(sample_rate * duration)
    if num_samples <= 0:
        return np.array([])
    t = np.linspace(0, duration, num_samples, endpoint=False)
    if freq <= 0:
        return np.zeros_like(t)

    if "피아노" in inst_type:
        sound = (0.5 * np.sin(2 * np.pi * freq * t) +
                 0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.15 * np.sin(2 * np.pi * freq * 3 * t) +
                 0.08 * np.sin(2 * np.pi * freq * 4 * t))
        envelope = np.exp(-2.5 * t / duration)
        
    elif "기타" in inst_type:
        sound = (0.45 * np.sin(2 * np.pi * freq * t) +
                 0.35 * np.sin(2 * np.pi * freq * 2 * t) +
                 0.2 * np.sin(2 * np.pi * freq * 3 * t))
        pluck = np.random.uniform(-0.12, 0.12, len(t)) * np.exp(-35.0 * t / duration)
        envelope = np.exp(-3.8 * t / duration)
        sound = (sound + pluck)
        
    elif "바이올린" in inst_type or "스트링" in inst_type:
        vibrato = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t)
        sound = (0.45 * np.sin(2 * np.pi * freq * vibrato * t) +
                 0.35 * np.sin(2 * np.pi * freq * 2 * vibrato * t) +
                 0.2 * np.sin(2 * np.pi * freq * 3 * vibrato * t))
        attack_len = min(int(0.12 * len(t)), len(t))
        envelope = np.ones_like(t)
        if attack_len > 0:
            envelope[:attack_len] = np.linspace(0, 1, attack_len)
        envelope *= np.exp(-1.0 * t / duration)
        
    else: # 감성 신디사이저 패드
        sound = 0.6 * np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 1.5 * t)
        envelope = np.exp(-1.8 * t / duration)

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

# --- 프로 가요풍 편곡 및 화성학 엔진 ---
def generate_kpop_song(user_anchors, total_bars, bpm, main_inst, mood_style, sample_rate):
    beat_dur = 60.0 / bpm
    bar_dur = 4 * beat_dur
    total_duration = total_bars * bar_dur
    total_samples = int(sample_rate * total_duration)

    melody_track = np.zeros(total_samples)
    chord_track = np.zeros(total_samples)
    sub_melody_track = np.zeros(total_samples) # 대위법적 화음 라인
    bass_track = np.zeros(total_samples)
    drum_track = np.zeros(total_samples)

    # 징검다리 음 구성
    bar_target_notes = []
    default_notes = ["C4", "E4", "G4", "A4", "F4", "G4", "C5", "B4"]
    for b in range(total_bars):
        if b in user_anchors:
            bar_target_notes.append(user_anchors[b])
        else:
            if len(bar_target_notes) > 0:
                prev_n = bar_target_notes[-1]
                p_idx = SCALE_NOTES.index(prev_n) if prev_n in SCALE_NOTES else 2
                step = random.choice([-2, -1, 0, 1, 2])
                new_idx = max(0, min(len(SCALE_NOTES) - 1, p_idx + step))
                bar_target_notes.append(SCALE_NOTES[new_idx])
            else:
                bar_target_notes.append(default_notes[b % len(default_notes)])

    # 무드별 프로 가요 코드 팔레트 (발라드/미디엄 템포 순환 코드)
    if "감성 발라드" in mood_style:
        # I - V - VIm - IV (가요 단골 4코드 진행)
        chord_progressions = [
            [261.63, 329.63, 392.00], # C (I)
            [196.00, 246.94, 293.66], # G (V)
            [220.00, 261.63, 329.63], # Am (VIm)
            [174.61, 220.00, 261.63]  # F (IV)
        ]
        bass_palette = [130.81, 98.00, 110.00, 87.31]
    elif "신나는 댄스/팝" in mood_style:
        # VIm - IV - I - V 진행
        chord_progressions = [
            [220.00, 261.63, 329.63], # Am
            [174.61, 220.00, 261.63], # F
            [261.63, 329.63, 392.00], # C
            [196.00, 246.94, 293.66]  # G
        ]
        bass_palette = [110.00, 87.31, 130.81, 98.00]
    else: # 몽환적인 R&B / 인디
        chord_progressions = [
            [220.00, 261.63, 329.63, 392.00], # Am7
            [174.61, 220.00, 261.63, 329.63], # Fmaj7
            [261.63, 329.63, 392.00, 493.88], # Cmaj7
            [196.00, 246.94, 329.63, 392.00]  # G7
        ]
        bass_palette = [110.00, 87.31, 130.81, 98.00]

    bar_samples = int(sample_rate * bar_dur)

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

        # 한 마디 안에 8개의 멜로디 음표를 풍성하게 배치 (가요풍 리듬 밀도 강화)
        num_sub_notes = 8
        sub_dur = bar_dur / num_sub_notes
        sub_samples = int(sample_rate * sub_dur)

        for sub in range(num_sub_notes):
            m_s = b_start + int(sub * sub_samples)
            m_e = min(total_samples, m_s + sub_samples)
            curr_dur = (m_e - m_s) / sample_rate
            if curr_dur <= 0 or m_s >= total_samples:
                continue

            ratio = sub / float(num_sub_notes)
            curr_scale_idx = int(s_idx + (e_idx - s_idx) * ratio)
            if sub in [2, 5, 7]:
                curr_scale_idx += random.choice([-1, 0, 1, 2])
            curr_scale_idx = max(0, min(len(SCALE_NOTES) - 1, curr_scale_idx))

            note_name = SCALE_NOTES[curr_scale_idx]
            freq = NOTE_FREQS.get(note_name, 261.63)

            # 주 멜로디
            mel_sound = synthesize_note(freq, curr_dur * 1.1, sample_rate, main_inst)
            mel_len = min(len(mel_sound), m_e - m_s)
            if mel_len > 0:
                melody_track[m_s:m_s + mel_len] += mel_sound[:mel_len]

            # 보조 화음 멜로디 (3도 위 하모니 라인 자동 생성으로 꽉 찬 사운드 연출)
            if sub % 2 == 0:
                harmony_idx = min(len(SCALE_NOTES) - 1, curr_scale_idx + 2)
                harm_freq = NOTE_FREQS.get(SCALE_NOTES[harmony_idx], 329.63)
                harm_sound = 0.35 * synthesize_note(harm_freq, curr_dur, sample_rate, "🎻 감성 바이올린/스트링")
                h_len = min(len(harm_sound), m_e - m_s)
                if h_len > 0:
                    sub_melody_track[m_s:m_s + h_len] += harm_sound[:h_len]

        # 코드, 베이스, 드럼 (16분음표 정밀 편곡)
        chord_freqs = chord_progressions[b % len(chord_progressions)]
        bass_freq = bass_palette[b % len(bass_palette)]
        slot_samples = bar_samples // 16

        for slot in range(16):
            sl_s = b_start + slot * slot_samples
            sl_e = min(total_samples, sl_s + slot_samples)
            sl_dur = (sl_e - sl_s) / sample_rate
            if sl_dur <= 0 or sl_s >= total_samples:
                continue

            # 피아노 아르페지오/코드 반주 (가요풍 리듬 패턴)
            if slot in [0, 4, 8, 12]:
                cf = chord_freqs[(slot // 4) % len(chord_freqs)]
                ch_sound = 0.3 * synthesize_note(cf, sl_dur * 3.5, sample_rate, "🎹 그랜드 피아노")
                ch_len = min(len(ch_sound), sl_e - sl_s)
                if ch_len > 0:
                    chord_track[sl_s:sl_s + ch_len] += ch_sound[:ch_len]

            # 베이스 기타 (풍성한 저음역대 그루브)
            if slot in [0, 6, 10]:
                bs_sound = 0.5 * synthesize_note(bass_freq, sl_dur * 2.5, sample_rate, "🎹 그랜드 피아노")
                bs_len = min(len(bs_sound), sl_e - sl_s)
                if bs_len > 0:
                    bass_track[sl_s:sl_s + bs_len] += bs_sound[:bs_len]

            # 찰진 드럼 리듬 (킥, 스네어, 하이햇)
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
            if slot % 2 == 1 or slot % 2 == 0:
                dh = synthesize_drum_hit("hihat", sl_dur, sample_rate)
                dh_len = min(len(dh), sl_e - sl_s)
                if dh_len > 0:
                    drum_track[sl_s:sl_s + dh_len] += dh[:dh_len]

    # 최종 믹싱 (보조 화음과 피아노 코드를 꽉 채워 빈약함 제거)
    full_audio = (0.75 * melody_track + 
                  0.45 * sub_melody_track + 
                  0.55 * chord_track + 
                  0.65 * bass_track + 
                  0.7 * drum_track)
                  
    max_val = np.max(np.abs(full_audio))
    if max_val > 0:
        full_audio = (full_audio / max_val) * 0.95

    return full_audio, total_duration

# --- 세션 상태 ---
if "user_anchors" not in st.session_state:
    st.session_state.user_anchors = {0: "C4", 2: "G4", 4: "A4", 6: "F4"}

# --- UI 레이아웃 ---
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size: 2.1rem;">🎼 프로 가요풍 AI 작곡 & 입체 편곡 스튜디오</h1>
    <p style="margin-top: 8px; opacity: 0.9; font-size: 1.02rem;">
        동요 같은 빈약함을 없애고, <b>가요풍 4코드 진행 + 3도 하모니 보조 화음 + 찰진 드럼 그루브</b>로 꽉 찬 사운드를 선사합니다!<br>
        원하시는 분위기와 징검다리 음을 설정하여 나만의 고품격 자작곡을 만들어 보세요.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.markdown("### 🎛️ 1. 가요 장르 및 곡 스타일 설정")
    
    mood_style = st.selectbox(
        "🎵 곡의 무드 및 화성 진행 스타일:",
        ["감성 발라드 (I-V-VIm-IV 진행)", "신나는 댄스/팝 (VIm-IV-I-V 진행)", "몽환적인 R&B / 인디팝"]
    )

    total_bars = st.select_slider(
        "📏 연주 길이 선택 (마디 수):",
        options=[4, 8, 12, 16, 24, 32],
        value=8,
        format_func=lambda x: f"{x}마디 (약 {int(x * 2.0)}초 연주)"
    )
    
    main_inst = st.selectbox(
        "🎸 주 멜로디 악기 음색:",
        ["🎹 그랜드 피아노", "🎸 어쿠스틱 기타", "🎻 감성 바이올린/스트링", "✨ 신디사이저 패드"]
    )
    
    bpm = st.slider("⏱️ 템포 (BPM):", min_value=70, max_value=135, value=108)

    st.markdown("---")
    st.markdown("### 📍 2. 핵심 징검다리 음(Anchor) 지정")
    st.caption("원하는 마디에 꼭 들어가야 할 음표를 지정하면, AI가 가요풍의 화성과 멜로디로 유기적으로 연결합니다.")

    c_bar, c_note, c_add = st.columns([1.2, 1.2, 1.0])
    with c_bar:
        target_bar = st.selectbox("마디 선택:", [f"{i+1}번째 마디" for i in range(total_bars)])
        bar_idx = int(target_bar.replace("번째 마디", "")) - 1
    with c_note:
        chosen_note = st.selectbox("음표 선택:", SCALE_NOTES, index=0)
    with c_add:
        st.write("")
        st.write("")
        if st.button("➕ 음표 추가", type="secondary"):
            st.session_state.user_anchors[bar_idx] = chosen_note
            st.rerun()

    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown("##### 📌 현재 지정된 징검다리 음표 현황:")
    if not st.session_state.user_anchors:
        st.info("지정된 포인트 음이 없습니다. AI가 가요 스케일에 맞춰 자동 작곡합니다.")
    else:
        badge_list = []
        for b_i in sorted(st.session_state.user_anchors.keys()):
            if b_i < total_bars:
                badge_list.append(f'<span class="anchor-badge">{b_i + 1}마디: {st.session_state.user_anchors[b_i]}</span>')
        st.markdown("".join(badge_list), unsafe_allow_html=True)

    if st.button("🗑️ 전체 초기화"):
        st.session_state.user_anchors = {}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 🪄 3. 프로 가요풍 명곡 생성하기")
    st.info("💡 **업그레이드 포인트**: 주 멜로디 외에 **3도 화음 대위법 라인**과 **풍성한 피아노 아르페지오 코드**가 함께 연주되어 절대 빈약하지 않은 풀 프레임 사운드를 들려줍니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 프로 가요풍 자작곡 연주하기!", type="primary", use_container_width=True):
        with st.spinner("🎵 가요풍 화성 진행과 풍성한 악기 세션을 믹싱 중입니다..."):
            sample_rate = 44100
            generated_audio, act_dur = generate_kpop_song(
                st.session_state.user_anchors, total_bars, bpm, main_inst, mood_style, sample_rate
            )

            audio_int16 = (generated_audio * 32767).astype(np.int16)
            buf = io.BytesIO()
            wavfile.write(buf, sample_rate, audio_int16)
            wav_bytes = buf.getvalue()

            st.success(f"🎉 **약 {int(act_dur)}초 분량 ({total_bars}마디)**의 풍성한 가요풍 자작곡이 완성되었습니다!")
            st.audio(wav_bytes, format="audio/wav")

            st.download_button(
                label="💾 고품질 가요풍 음원 다운로드 (.wav)",
                data=wav_bytes,
                file_name=f"kpop_style_song_{total_bars}bars.wav",
                mime="audio/wav"
            )
