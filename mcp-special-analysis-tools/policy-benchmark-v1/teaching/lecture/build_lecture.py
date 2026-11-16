from __future__ import annotations

import argparse
import importlib.util
import json
import re
from html import escape
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(
    description='Build the unchanged four-page Korean policy-data lecture PDF.')
parser.add_argument('--output', type=Path,
                    default=ROOT / 'output' / 'pdf' / 'policy-data-lecture-ko.pdf',
                    help='Destination PDF path (default: lecture/output/pdf/).')
parser.add_argument('--tmp', '--tmpdir', dest='tmp', type=Path,
                    default=ROOT / 'tmp' / 'pdfs',
                    help='Directory for font subsets, plot and layout checks.')
parser.add_argument('--font-regular', type=Path,
                    default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
parser.add_argument('--font-bold', type=Path,
                    default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'))
parser.add_argument('--font-index', type=int, default=1,
                    help='Collection index; index 1 is Korean in Noto Sans CJK TTC.')
args = parser.parse_args()
TARGET = args.output.expanduser().resolve()
TARGET.parent.mkdir(parents=True, exist_ok=True)
TMP = args.tmp.expanduser().resolve()
TMP.mkdir(parents=True, exist_ok=True)
FONT_CACHE = TMP / 'fonts'
FONT_CACHE.mkdir(exist_ok=True)

INK = colors.HexColor('#12313C')
TEAL = colors.HexColor('#147D76')
MUTED = colors.HexColor('#52656C')
RULE = colors.HexColor('#CCD8D9')
PALE = colors.HexColor('#EEF5F3')
OCHRE = '#C7822D'
W,H = A4
M = 39
CW = W - 2*M

ORDER = ['chetty2020','kontokosta2021','tapio2003','kleinberg2018','itf2015',
         'dembski2020','hiltunen2008','perdomo2020','card1994','dehejia2002',
         'jacob2004','imai2011','imai2019']
ALL_SOURCES = {s['id']:s for s in json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))}
SOURCES = [ALL_SOURCES[k] for k in ORDER]

# Text remains separate from the empirical papers and student exercise package.
CONTENT = {
 'p1_lead':'정책 데이터 분석은 <b>어디가 문제인가 → 앞으로 어떻게 될까 → 왜 발생하며 무엇이 효과가 있는가</b>를 묻는다. 문제 발견의 출발점은 비교다. 차이를 찾은 뒤, 목표·권리·형평성 등의 기준으로 정책적 의미를 판단한다.',
 'p1_rows':[
  ['비교할 것','간단한 기법','정책에서 묻는 질문'],
  ['사람·집단·지역','평균·비율 비교, 박스플롯','어느 집단의 대기시간이 더 길고 불안정한가?'],
  ['시간','추세·증감률·변곡점 살펴보기','청년의 구직 중단 비율이 계속 높아지는가?'],
  ['비슷한 특성의 유형','교차분류, 군집분석','주거비 부담형·이동 불편형·복합 취약형으로 나뉘는가?'],
  ['목표·기준','목표 대비 격차, 기준 초과 비율','서비스 처리기한을 넘긴 사람은 얼마나 되는가?'],
 ],
 'p1_type':'<b>유형화</b>는 비슷한 대상을 묶어 집단의 차이를 잘 보이게 한다. 군집은 선택한 변수·척도·집단 수에 따라 달라지며, 그 자체가 원인이나 객관적으로 정해진 계층은 아니다. 위 유형명은 설명용 가상 예시다.',
 'p1_plot_title':'평균이 같아도 경험은 다르다',
 'p1_plot_note':'<b>수업용 가상자료.</b> 두 지역 모두 평균 11일이지만, 중앙값은 A 11일·B 7일이다. B에는 매우 오래 기다린 사례가 있다. 상자는 가운데 50%, 굵은 선은 중앙값, 별도 점은 긴 처리시간 사례를 보여준다.',
 'p1_paper1':'<b>경제적 기회의 격차 [1]</b> Chetty 외(2020)는 부모의 소득 수준에 따른 자녀의 성인 소득을 인종·성별·지역별로 비교했다. 이 연구에서 수업에 가져올 부분은 <b>비교 조건과 집단을 나누면 가려진 격차가 드러난다</b>는 점이다. 격차의 발견과 원인 규명은 구별한다.',
 'p1_paper2':'<b>민원이 적으면 문제가 적은가? [2]</b> Kontokosta·Hong(2021)은 캔자스시티의 311 민원과 주민 설문·지역 상태를 함께 살폈다. 일부 취약지역의 신고가 필요를 충분히 반영하지 못했다. <b>민원 건수는 문제의 크기와 동일하지 않다.</b>',
 'p1_close':'읽는 순서: 비교 기준 → 평균과 분포 → 시간 변화 → 자료에서 빠진 사람. 건수와 비율을 구분하고, 같은 정의·대상·기간으로 비교한다.',
 'p2_lead':'예측은 <b>“어떤 조건에서 무엇이 일어날 가능성이 있는가”</b>를 따진다. 아래 접근은 함께 사용할 수 있다. 특히 디지털 트윈은 하나의 예측 기법이라기보다 현실 자료와 여러 모형을 연결하는 체계다.',
 'p2_delphi':'<b>전문가에게 반복해서 묻고, 응답과 근거를 피드백한다.</b> Tapio(2003)는 핀란드 교통정책에서 경제·교통량·배출의 가능한 미래와 바람직한 미래를 물어 여러 시나리오를 구성했다. 이 방식은 의견 차이도 보존했다. 전문가 선정·질문 방식에 영향을 받으며, 합의가 정확성을 보장하지 않는다. [3]',
 'p2_ml':'<b>과거 자료에서 이후 결과와 연결되는 패턴을 학습한다.</b> 회귀·시계열 모형, 랜덤포리스트·부스팅 등이 쓰인다. Kleinberg 외(2018)는 재판 전 석방 판단과 위험 예측을 연구했다. 석방된 사람의 결과만 관찰되는 선택 문제를 함께 다뤘다. 과거와 미래의 조건이 달라지면 성능도 달라진다. [4]',
 'p2_sim':'<b>사람·자원·제도의 작동 규칙을 정하고 대안을 계산한다.</b> 미시모의실험·행위자 기반 모형·시스템다이내믹스 등이 있다. ITF(2015)는 리스본에서 공유 자율주행차 시나리오를 모의실험했다. 필요한 차량 수가 줄어도 공차 이동 등으로 총 주행거리는 늘 수 있다. 이는 가정 아래의 계산이다. [5]',
 'p2_twin':'<b>도시·시설의 자료를 모형과 연결해 상태와 대안을 살핀다.</b> Dembski 외(2020)는 독일 헤렌베르크의 3차원 도시·교통·바람·시민 자료를 연결한 프로토타입을 제시했다. 현실과의 연결·보정·검증이 중요하며, 정교한 화면이 사람의 미래 행동까지 보장하지는 않는다. [6]',
 'p2_signal':'“나뭇잎 하나가 떨어졌다”는 것은 계절 변화의 단서일 수 있지만 바람이나 손상 때문일 수도 있다. <b>약한 신호 탐색</b>은 작은 변화·현장 관찰·뉴스·전문가 판단을 모아 추가 확인할 대상을 찾는 일이다. 드문 단서를 놓치거나 잡음을 신호로 오인할 수 있다. Hiltunen(2008)은 신호·현상·해석의 구별을 제안했다. [7]',
 'p2_human':'예측이 의사결정에 쓰이면 사람의 행동과 다음 자료가 달라질 수 있다. Perdomo 외(2020)의 <b>수행적 예측</b>은 이 문제를 다룬다. 따라서 예측은 조건·오차·갱신 시점을 함께 제시한다. <b>확정적 예언의 어려움이 조건부 예측의 무용함을 뜻하지는 않는다.</b> [8]',
 'p2_close':'같은 청년고용 문제라도 “실업률 전망”, “지원제도 변경 시나리오”, “새로운 구직행태의 조짐”은 서로 다른 질문이다.',
 'p3_lead':'원인진단은 <b>무엇이 결과를 바꾸는가</b>, 효과분석은 <b>정책을 했을 때와 하지 않았을 때 얼마나 달라지는가</b>를 묻는다. 공통 과제는 관찰되지 않은 다른 상태, 즉 <b>반사실</b>에 설득력 있는 비교 근거를 만드는 것이다.',
 'p3_rows':[
  ['방법','비교하는 방식','해석을 위한 핵심 조건'],
  ['회귀·ANCOVA','관측한 공변량을 조정한 집단 차이','적절한 모형·비교 가능성, 관련 교란의 조정'],
  ['매칭·PSM','처치 전 특성이 비슷한 대상을 비교','겹치는 대상이 있어야 함; 미관측 교란은 남을 수 있음'],
  ['고정효과(FE)','같은 대상의 여러 시점을 비교','일정한 모형 조건에서 시간 불변 요인 제거; 시간 가변 교란은 남음 [13]'],
  ['DID','처치·비교집단의 전후 변화 차이','정책이 없었으면 추세가 평행했을 것이라는 가정'],
  ['RD','정책 배정 기준선 바로 양옆을 비교','경계 부근의 비교 가능성; 효과는 경계 주변에 해당'],
 ],
 'p3_note':'연구설계와 계산 방법은 결합할 수 있다. 예컨대 무작위실험에서도 회귀로 사전 차이를 조정할 수 있다. DID는 여러 시점과 반복횡단면에도 가능하며, 자료 구조에 맞는 비교 조건을 확인한다.',
 'p3_cases':'<b>DID [9]</b> Card·Krueger(1994): 뉴저지·펜실베이니아 패스트푸드점의 최저임금 인상 전후 고용 비교.<br/><b>PSM [10]</b> Dehejia·Wahba(2002): 취업훈련 자료에서 관측 특성이 비슷한 비실험 비교대상을 구성.<br/><b>RD [11]</b> Jacob·Lefgren(2004): 시카고의 성적 기준과 여름학교·진급 규칙 주변에서 교육 성과 비교.',
 'p3_med':'<b>매개: 어떤 경로로?</b><br/>가상 예: 취업상담 → 구직 자신감 → 취업.<br/>Imai 외(2011)는 뉴스 메시지·불안·이민 태도의 매개 경로 등을 재분석했다. 처치의 무작위배정만으로 매개 경로까지 입증되지는 않는다. [12]',
 'p3_mod':'<b>조절: 누구에게·언제 더 큰가?</b><br/>가상 예: 취업상담의 효과가 기존 경력에 따라 다른가?<br/>집단별 효과의 차이를 직접 비교한다. 한 집단에서만 유의하다는 이유로 집단 간 효과가 다르다고 단정하지 않는다.',
 'p3_close':'“영향요인 연구”에서 회귀계수나 변수 중요도가 크다는 것만으로 원인을 찾았다고 할 수 없다. 또한 통계의 “요인분석”은 여러 문항의 구조를 요약하는 방법으로, 인과적 원인을 찾는 것과 다르다.',
}

def norm(s):
    return s.translate(str.maketrans({'\u2010':'-','\u2011':'-','\u2012':'-','\u2013':'-','\u2014':'-','\u2212':'-'}))

font_module = ROOT.parent / 'build_handbook.py'
if not font_module.is_file():
    raise FileNotFoundError('Expected shared font helper at ../build_handbook.py; keep the teaching/lecture repository layout.')
spec=importlib.util.spec_from_file_location('handbook_font_helper',font_module)
fm=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)
chars=set(norm(json.dumps(CONTENT,ensure_ascii=False)+json.dumps(SOURCES,ensure_ascii=False)+Path(__file__).read_text(encoding='utf-8')))
# Include fixed label glyphs, not unsupported markup characters or code escapes.
reg=fm.embedded_font(args.font_regular,chars,FONT_CACHE,'Regular',args.font_index)
bold=fm.embedded_font(args.font_bold,chars,FONT_CACHE,'Bold',args.font_index)
pdfmetrics.registerFont(TTFont('Lecture',str(reg)))
pdfmetrics.registerFont(TTFont('Lecture-Bold',str(bold)))
pdfmetrics.registerFontFamily('Lecture',normal='Lecture',bold='Lecture-Bold',italic='Lecture',boldItalic='Lecture-Bold')

def style(size=10.1,leading=15.3,color=INK,bold=False):
    return ParagraphStyle('x',fontName='Lecture-Bold' if bold else 'Lecture',fontSize=size,
                          leading=leading,textColor=color,wordWrap='CJK',splitLongWords=True,
                          allowWidows=0,allowOrphans=0)

c=canvas.Canvas(str(TARGET),pagesize=A4,pageCompression=1)
c.setTitle('정책 데이터 분석: 문제 발견·예측·원인과 효과')
c.setAuthor('정책 데이터 분석 강의자료')
c.setSubject('비교와 유형화, 예측과 시뮬레이션, 반사실과 매개·조절을 소개하는 간결한 강의자료')
log=[]

def para(text,y,x=M,width=CW,size=10.1,leading=15.3,color=INK,bold=False,gap=7):
    p=Paragraph(norm(text),style(size,leading,color,bold))
    _,height=p.wrap(width,900)
    if y-height<48:
        raise ValueError(f'Content exceeds footer: y={y:.1f}, h={height:.1f}, {text[:45]}')
    p.drawOn(c,x,y-height)
    log.append({'page':c.getPageNumber(),'y_top':round(y,2),'y_bottom':round(y-height,2),'text':re.sub('<[^>]*>','',text)})
    return y-height-gap

def head(n,title,sub):
    c.setFillColor(TEAL); c.setFont('Lecture-Bold',9)
    c.drawString(M,H-37,'정책 데이터 분석 | 강의용 요약')
    c.setFillColor(MUTED); c.setFont('Lecture',8)
    c.drawRightString(W-M,H-37,f'{n} / 4')
    c.setStrokeColor(RULE);c.setLineWidth(.6);c.line(M,H-47,W-M,H-47)
    y=para(title,H-60,size=21.5,leading=30,bold=True,gap=6)
    y=para(sub,y,size=9.4,leading=14,color=MUTED,gap=16)
    c.setStrokeColor(RULE);c.line(M,38,W-M,38)
    c.setFillColor(MUTED);c.setFont('Lecture',7.5)
    c.drawString(M,25,'핵심 개념과 사례논문 | 별도 실습자료와 독립적으로 읽는 강의자료')
    c.drawRightString(W-M,25,str(n))
    return y

def section(title,y):
    return para(title,y,size=12.3,leading=18,bold=True,color=TEAL,gap=5)

def table(rows,y,widths):
    flow=[]
    for i,row in enumerate(rows):
        flow.append([Paragraph(norm(v),style(9.0 if i else 9.1,13.1,
                     colors.white if i==0 else INK,bold=(i==0 or j==0))) for j,v in enumerate(row)])
    t=Table(flow,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
      ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
      ('LINEBELOW',(0,1),(-1,-1),.4,RULE),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8F7')]),
    ]))
    _,h=t.wrap(CW,900)
    assert y-h>48
    t.drawOn(c,M,y-h)
    return y-h-9

def rule(y):
    c.setStrokeColor(RULE);c.setLineWidth(.55);c.line(M,y,W-M,y)
    return y-12

def arrow(x1,y1,x2,y2,color=TEAL):
    c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(1)
    c.line(x1,y1,x2,y2)
    dx=x2-x1;dy=y2-y1;ang=np.arctan2(dy,dx);a=4
    p=c.beginPath();p.moveTo(x2,y2)
    p.lineTo(x2-a*np.cos(ang-.5),y2-a*np.sin(ang-.5));p.lineTo(x2-a*np.cos(ang+.5),y2-a*np.sin(ang+.5));p.close()
    c.drawPath(p,stroke=0,fill=1)

# Accurate vector boxplot, with explicitly synthetic observations.
A=np.array([8,9,10,10,11,11,12,12,13,14])
B=np.array([1,2,3,5,6,8,10,15,20,40])
assert float(A.mean())==float(B.mean())==11
assert float(np.median(A))==11 and float(np.median(B))==7
font_prop=FontProperties(fname=str(reg))
plt.rcParams.update({'svg.fonttype':'path','axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(7.05,1.6),dpi=160)
bp=ax.boxplot([A,B],orientation='horizontal',positions=[2,1],widths=.43,
 patch_artist=True,whis=1.5,showfliers=True,
 medianprops={'color':'#12313C','linewidth':1.6},
 whiskerprops={'color':'#52656C','linewidth':1},capprops={'color':'#52656C','linewidth':1},
 flierprops={'marker':'o','markersize':4,'markerfacecolor':OCHRE,'markeredgecolor':OCHRE})
for box,col in zip(bp['boxes'],['#92C5BC','#E7BE89']):box.set_facecolor(col);box.set_edgecolor('#52656C')
ax.set_yticks([2,1],['지역 A (10건)','지역 B (10건)'],fontproperties=font_prop,fontsize=9)
ax.set_xlim(0,45);ax.set_xticks([0,10,20,30,40]);ax.tick_params(axis='both',length=0,labelsize=8,colors='#52656C')
ax.set_xlabel('민원 처리 일수',fontproperties=font_prop,fontsize=9,color='#52656C',labelpad=3)
ax.grid(axis='x',color='#DBE3E1',linewidth=.5);ax.set_axisbelow(True)
for sp in ax.spines.values():sp.set_visible(False)
fig.subplots_adjust(left=.15,right=.98,bottom=.31,top=.96)
plot_png=TMP/'synthetic_boxplot.png';fig.savefig(plot_png,transparent=True,dpi=400);plt.close(fig)

# 1. Discovery.
y=head(1,'문제 발견: 비교로 차이를 드러낸다','누가, 어디서, 언제 다른가? 평균 뒤의 분포와 자료의 빈틈까지 본다.')
y=para(CONTENT['p1_lead'],y)
y=table(CONTENT['p1_rows'],y,[92,153,CW-245])
y=para(CONTENT['p1_type'],y,size=9.5,leading=14.2,gap=12)
y=section(CONTENT['p1_plot_title'],y)
plot_h=CW*1.6/7.05;c.drawImage(ImageReader(str(plot_png)),M,y-plot_h,width=CW,height=plot_h,mask='auto');y-=plot_h+3
y=para(CONTENT['p1_plot_note'],y,size=9.2,leading=13.5,gap=13)
y=section('사례논문: 차이와 사각지대를 발견하기',y)
y=para(CONTENT['p1_paper1'],y,size=9.65,leading=14.5,gap=8)
y=para(CONTENT['p1_paper2'],y,size=9.65,leading=14.5,gap=9)
y=rule(y)
y=para(CONTENT['p1_close'],y,size=9.3,leading=14,color=TEAL,gap=0)
c.showPage()

# 2. Prediction and foresight.
y=head(2,'예측: 근거와 조건을 함께 말한다','미래를 한 숫자로 확정하기보다, 전망·시나리오·조짐을 구분한다.')
y=para(CONTENT['p2_lead'],y,gap=12)
for title,key in [('델파이: 전문가의 판단과 근거','p2_delphi'),
                  ('통계·기계학습: 관찰된 패턴','p2_ml'),
                  ('시뮬레이션: 작동 규칙과 가정','p2_sim'),
                  ('디지털 트윈: 현실 자료와 모형의 연결','p2_twin')]:
    y=section(title,y)
    y=para(CONTENT[key],y,size=10,leading=15,gap=12)
y=rule(y)
y=section('잡음 속의 조짐, 그리고 달라지는 사람',y)
y=para(CONTENT['p2_signal'],y,size=9.8,leading=14.8,gap=9)
y=para(CONTENT['p2_human'],y,size=9.8,leading=14.8,gap=9)
y=para(CONTENT['p2_close'],y,size=9.5,leading=14.3,color=TEAL,gap=0)
c.showPage()

# 3. Causal questions, mediation and moderation.
y=head(3,'원인과 효과: 설득력 있는 비교를 만든다','상관관계의 발견에서 한 걸음 더 나아가, 다른 설명을 얼마나 배제했는지 묻는다.')
y=para(CONTENT['p3_lead'],y,gap=10)
y=table(CONTENT['p3_rows'],y,[86,177,CW-263])
y=para(CONTENT['p3_note'],y,size=9.1,leading=13.5,gap=10)
y=section('사례논문: 무엇을 누구와 비교했는가?',y)
y=para(CONTENT['p3_cases'],y,size=9.3,leading=15,gap=11)
y=section('매개와 조절: 경로와 조건은 다르다',y)
col=(CW-20)/2
y_start=y
ya=para(CONTENT['p3_med'],y,x=M,width=col,size=9.3,leading=14,gap=2)
yb=para(CONTENT['p3_mod'],y,x=M+col+20,width=col,size=9.3,leading=14,gap=2)
y=min(ya,yb)-8
c.setStrokeColor(RULE);c.line(M+col+10,y+5,M+col+10,y_start)
y=rule(y)
y=para(CONTENT['p3_close'],y,size=9.3,leading=14,color=TEAL,gap=0)
c.showPage()

# 4. Compact, linked scholarly reading list.
y=head(4,'참고문헌과 원문 링크','본문의 대괄호 번호와 대응한다. 제목을 누르면 논문 또는 원저자·기관 페이지가 열린다.')
y=para('처음 읽을 자료: <b>[2] 민원 자료의 편향</b>, <b>[3] 델파이 시나리오</b>, <b>[5] 교통 시뮬레이션</b>, <b>[9] DID 비교 논리</b>. 논문 전체를 가르치기보다 질문·자료·비교 방식·해석의 한계를 읽는다.',y,size=9.5,leading=14.2,gap=15)
for i,src in enumerate(SOURCES,1):
    # Bibliographic text is retained; the visible title is linked without raw long URLs.
    citation=re.sub(r' https://doi\.org/\S+\.?$','',src['citation'])
    citation=citation.replace('Proceedings of the 37th International Conference on Machine Learning, Proceedings of Machine Learning Research','ICML, Proceedings of Machine Learning Research')
    linked=f'<b>[{i}]</b> <link href="{escape(src["url"],quote=True)}" color="#147D76">{escape(norm(citation))}</link>'
    y=para(linked,y,size=8.8,leading=12.3,gap=8)
y=rule(y+1)
y=para('<b>읽을 때 구분할 것</b> [1][2][4][9][10][11]은 실증자료를 다룬 연구, [3]은 델파이 방법·정책 사례, [5]는 조건부 시뮬레이션 보고서, [6]은 디지털 트윈 구현 사례, [7][8][12][13]은 개념·방법론 및 적용 연구다. 본문의 박스플롯과 별도 표시된 정책 예시는 수업용 가상 사례이며, 논문의 수치를 재현한 그림이 아니다.',y,size=8.8,leading=13,color=MUTED,gap=0)
c.save()

reader=PdfReader(TARGET)
assert len(reader.pages)==4, len(reader.pages)
pages=[p.extract_text() for p in reader.pages]
assert all(len(p)>600 for p in pages)
assert '중앙값' in pages[0] and '델파이' in pages[1] and '매개' in pages[2]
urls=[]
for p in reader.pages:
    for a in p.get('/Annots',[]):
        obj=a.get_object()
        if obj.get('/A',{}).get('/URI'):urls.append(str(obj['/A']['/URI']))
assert all(s['url'] in urls for s in SOURCES)
(TMP/'layout-record.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
(TMP/'extracted.txt').write_text('\n\n'.join(pages),encoding='utf-8')
print(json.dumps({'file':str(TARGET),'pages':len(reader.pages),'bytes':TARGET.stat().st_size,
                  'links':len(urls),'min_body_y':round(min(x['y_bottom'] for x in log),1)},ensure_ascii=False))
