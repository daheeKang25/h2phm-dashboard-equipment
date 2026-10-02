import streamlit as st
import pandas as pd
import time

# 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="수소발전소 예지보전 시연시스템", layout="wide")

# ---------------------------------------------------------
# 1. 데이터 로드 함수 (캐싱하여 속도 최적화)
# ---------------------------------------------------------
@st.cache_data
def load_data(scenario):
    if scenario == "정상 운전 (FC1)":
        return pd.read_csv('./data/FC1_Cleaned_1Hz.csv')
    else:
        return pd.read_csv('./data/FC2_Cleaned_1Hz.csv')

# ---------------------------------------------------------
# 2. 세션 상태(Session State) 초기화
# ---------------------------------------------------------
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'scenario' not in st.session_state:
    st.session_state.scenario = "정상 운전 (FC1)"

# ---------------------------------------------------------
# 3. 사이드바 (통신 제어 및 상태 모니터링)
# ---------------------------------------------------------
st.sidebar.title("📡 데이터 전송 제어부")

# 시나리오 선택
selected_scenario = st.sidebar.selectbox(
    "시나리오 선택", 
    ["정상 운전 (FC1)", "가속 열화 (FC2)"],
    index=0 if st.session_state.scenario == "정상 운전 (FC1)" else 1
)

if selected_scenario != st.session_state.scenario:
    st.session_state.scenario = selected_scenario
    st.session_state.current_index = 0
    st.session_state.is_running = False

df = load_data(st.session_state.scenario)
total_rows = len(df)

# 시작/정지 토글 버튼
col1, col2 = st.sidebar.columns(2)
if col1.button("▶ 전송 시작"):
    st.session_state.is_running = True
if col2.button("⏸ 전송 정지"):
    st.session_state.is_running = False

# 시각화 옵션 토글 추가
st.sidebar.markdown("---")
st.sidebar.subheader("UI 옵션")
show_visuals = st.sidebar.toggle("📊 상세 시각화 차트 표시", value=False)

# 전송 상태 표시
st.sidebar.markdown("---")
st.sidebar.subheader("네트워크 상태")
if st.session_state.is_running:
    st.sidebar.success("🟢 연결 상태: 정상 (데이터 송신 중)")
else:
    st.sidebar.warning("🟡 연결 상태: 대기 (송신 중지)")

st.sidebar.metric("총 전송 건수", f"{st.session_state.current_index} / {total_rows} 건")

# 인덱스 슬라이더
st.session_state.current_index = st.sidebar.slider(
    "시점 이동 (Time Index)", 
    0, total_rows - 1, st.session_state.current_index
)

# ---------------------------------------------------------
# 4. 메인 대시보드 화면 구성
# ---------------------------------------------------------
st.title("🏭 수소발전소 연료전지(PEMFC) 실시간 모니터링")
st.markdown("설비부에서 전송되는 1Hz 주기의 센서 데이터를 실시간으로 표출합니다.")

if st.session_state.current_index < total_rows:
    latest_row = df.iloc[st.session_state.current_index]
    
    # 4-1. 상단 핵심 지표
    st.subheader("핵심 운전 지표")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("노화 진행 시간 (Time)", f"{latest_row['Time']:.1f} h")
    m2.metric("스택 총 전압 (Utot)", f"{latest_row['Utot']:.3f} V")
    m3.metric("출력 전류 (I)", f"{latest_row['I']:.2f} A")
    m4.metric("전류 밀도 (J)", f"{latest_row['J']:.3f} A/cm²")
    
    st.markdown("---")

    # 4-2. 중단 셀 전압 추세선
    st.subheader("개별 셀 전압 실시간 추세 (불균형 모니터링)")
    window_size = 100
    start_idx = max(0, st.session_state.current_index - window_size)
    chart_data = df.iloc[start_idx : st.session_state.current_index + 1]
    
    chart_df = chart_data[['Time', 'U1', 'U2', 'U3', 'U4', 'U5']].set_index('Time')
    st.line_chart(chart_df, height=250)

    # 4-3. 하단 환경 센서 탭
    st.subheader("환경 센서 상세")
    tab1, tab2, tab3 = st.tabs(["🌡️ 온도 센서", "💨 압력 센서", "🌊 유량 센서"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("수소 유입 온도 (TinH2)", f"{latest_row['TinH2']:.1f} °C")
        c1.metric("수소 유출 온도 (ToutH2)", f"{latest_row['ToutH2']:.1f} °C")
        c2.metric("공기 유입 온도 (TinAIR)", f"{latest_row['TinAIR']:.1f} °C")
        c2.metric("공기 유출 온도 (ToutAIR)", f"{latest_row['ToutAIR']:.1f} °C")
        c3.metric("냉각수 유입 온도 (TinWAT)", f"{latest_row['TinWAT']:.1f} °C")
        c3.metric("냉각수 유출 온도 (ToutWAT)", f"{latest_row['ToutWAT']:.1f} °C")
        
    with tab2:
        c1, c2 = st.columns(2)
        c1.metric("수소 유입 압력 (PinH2)", f"{latest_row.get('PinH2', 0):.0f} mbara")
        c1.metric("수소 유출 압력 (PoutH2)", f"{latest_row.get('PoutH2', 0):.0f} mbara")
        c2.metric("공기 유입 압력 (PinAIR)", f"{latest_row.get('PinAIR', 0):.0f} mbara")
        c2.metric("공기 유출 압력 (PoutAIR)", f"{latest_row.get('PoutAIR', 0):.0f} mbara")

    with tab3:
        c1, c2, c3 = st.columns(3)
        c1.metric("수소 유입 유량 (DinH2)", f"{latest_row.get('DinH2', 0):.1f} l/mn")
        c1.metric("수소 유출 유량 (DoutH2)", f"{latest_row.get('DoutH2', 0):.1f} l/mn")
        c2.metric("공기 유입 유량 (DinAIR)", f"{latest_row.get('DinAIR', 0):.1f} l/mn")
        c2.metric("공기 유출 유량 (DoutAIR)", f"{latest_row.get('DoutAIR', 0):.1f} l/mn")
        c3.metric("냉각수 배출 유량 (DWAT)", f"{latest_row.get('DWAT', 0):.1f} l/mn")

    # 4-4. [추가] 상세 시각화 옵션 활성화 시 표출 영역
    if show_visuals:
        st.markdown("---")
        st.subheader("📊 실시간 상세 시각화")
        
        v_col1, v_col2 = st.columns(2)
        
        with v_col1:
            st.markdown("**스택 총 전압(Utot) 장기 열화 추세**")
            # 시작부터 현재까지의 전체 누적 전압 강하 트렌드를 보여줌
            cumulative_data = df.iloc[:st.session_state.current_index + 1]
            st.line_chart(cumulative_data.set_index('Time')['Utot'], height=250)
            
        with v_col2:
            st.markdown("**주요 가스(수소/공기) 유출입 온도 변화 (최근 100초)**")
            # 윈도우 사이즈(100초) 내의 온도 변화 비교
            temp_cols = ['TinH2', 'ToutH2', 'TinAIR', 'ToutAIR']
            st.line_chart(chart_data.set_index('Time')[temp_cols], height=250)

# ---------------------------------------------------------
# 5. 실시간 업데이트 루프 (Data Pump)
# ---------------------------------------------------------
if st.session_state.is_running:
    if st.session_state.current_index < total_rows - 1:
        time.sleep(1)
        st.session_state.current_index += 1
        st.rerun()
    else:
        st.session_state.is_running = False
        st.sidebar.warning("데이터 재생이 완료되었습니다.")
        st.rerun()