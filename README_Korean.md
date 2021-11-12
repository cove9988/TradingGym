# Trading Gym (>Python 3.7)
Trading Gym은 외한 거래의 맥락에서 심층 강화 학습 알고리즘 개발을 위한 오픈 소스 프로젝트입니다.
## 프로젝트의 핵심
1. 외화 거래를 위한 맞춤형 gym은 3가지 동작을 합니다(매수, 매도, 아무 작업을 하지 않음). 보상은 손실 방지(SL) 와 이익 실현(PT)에 의해 기반 및 실현되는 외한 포인트입니다. 손실 방지(SL)는 매개변수를 통과함으로써 고정되고 이익 실현(PT)은 보상을 극대화하기 위한 AI 학습입니다.
2. 같은 시간대의 멀티플라이 페어들은 1분 5분 30분 1시간 4시간으로 시간을 설정할 수 있습니다. 야간 현금 위약금, 거래 수수료, 거래 야간 위약금(SWAP)를 두 개 다 구성할 수 있습니다.
3. 데이터 프로세스는 일련 시간을 기반으로 한 하루, 주 또는 달로 데이터를 나눌 것입니다. 그리고 Isaac 혹은 Ray를 병행으로 사용하여 훈련할 것입니다.
4. 파일 로그, 콘솔 출력 과 실시간 그래프를 이용하여 주요 렌더링에 사용할 수 있습니다.

##  주요 기능
1. 외환 기능
    
    1.1.  보상 및 잔액 계산에서 포인트(5개의 십진수 외환)를 사용합니다. 
    ### 기준점
    보통 특정 환율이 인용되는 마지막 소수 자릿수를 점(a point)이라고 합니다.	
       
2. 데이터 처리: (./data/data_process.py)
    
    2.1. csv(시간, 시가, 고가, 저가, 종가)를 처리할 때, 사용한 소스는 MetaTrader입니다.
    
    2.2. 기호, 요일 등과 같은 몇 가지 필수 기능을 추가하였습니다.
    
    2.3. finta를 사용하여 TA 기능을 추가하였습니다.
    
    2.4. 연속적인 시간 데이터를 주간 또는 월간으로 분할하였습니다.
    
    2.5 벡터 프로세스하기 위해 서로 다른 거래 쌍(GBPUSD, EURUSD 등)을 CSV에 결합하였습니다. (현재까지는 수동으로)
3. 환경:
    
    3.1. action_space = spaces.Box(low=0, high=3, shape=(len(assets), ))
    
    3.2. _action = floor(action) {0:매수, 1:매도, 2:n 아무것도 하지 않음}
    
    3.3. action_price는 현재 봉(candlestick)의 근접한 가격입니다.
    
    3.4. observation_space는 현재 잔액을 포함합니다, .. (draw down) * assets + (TA features)*assets
    
    3.5. 수행의 일부로 고정된 stop_loss(SL) 매개변수와 profit_taken(PT)에 대한 분수 계산을 사용합니다. 
    
    3.6. 야간 현금 과태료, 거래 수수료, 야간거래 과태료 보유 
    
    3.7. 보상은 다음단계에서 손실 방지(SL)와 이익 실현(PT)이 촉발되면 실현됩니다.
    
    3.8. 최대 유지(max holding)
    
    3.9. balance <= x  or step == len(df)  [reach the weekend]
        if step == len(df) close 인 경우에 근접가(close price)에서 모든 유지 상태(holding position)를 끝냅니다.

## 거래 환경:

`Candle Trading`은 ohlc(시가, 고가, 저가, 종가에 대한 봉/바) data가 입력되어 있는 거래 환경이며, 외화(통화) 거래에서 매우 유용합니다. 우리는 이익 실현(머신 러닝)과 고정된 손실매를 이용합니다. 

## 당신의 고유한 `data_process` 생성

당신의 고유한 data를 생성하기 위해, 'data/data_process.py' 파일에 있는  `data_process` base class를 사용할 수 있습니다.

## OpenAI gym과의 호환성

Tgym(거래환경)은 OpenAI Gym으로부터 상속됩니다. 우리는 완전히 OpenAI Gym architecture를 기반으로 하고 이 기반을 통해 Trading Gym를 추가적인 OpenAI 환경으로 제안하는 것을 목적으로 합니다.

## 예시
ppo_test.ipynb
