> **Archived draft, not a specification.** IML draft 0.1 was filed on 2026-09-12 and is kept here unchanged as the dated record. It was reviewed on 2026-09-18. As written, axiom A1 (lossless conversion to and from I-Lang v4.x) does not hold: the value abbreviation table is not injective, the dot/space and plus/comma substitutions are lossy, values carry no delimiting or escaping, and the conditional, loop and parallel forms have no I-Lang v4.x operation syntax to decompile to. A2 (identical parsing by any model) is not testable as stated, and the figures under A3 count characters, not bytes, and change with the tokenizer. The verb roots and modifier keys below are not the I-Lang canon's (22 of 41 roots and 12 of 29 core keys differ). The scope that replaces this draft is in [ROADMAP.md](../ROADMAP.md).
>
> 存档草案，不是规范。0.1 于 2026-09-12 提出，2026-09-18 复审：A1 无损往返在现有写法下不成立，A2 不可检验，A3 的数字是字符数且随分词器变化；词根表与键表未对齐正典。替代它的 0.2 范围见 [ROADMAP.md](../ROADMAP.md)。

---

::ILANG::v5.0
[TYPE:spec_draft]
[PROJECT:I-Lang Machine Layer (IML)]
[VERSION:draft_0.1]
[DATE:2026-09-12]
[FROM:@MOTHER]
[AUTHORITY:@SUN]
[CONSTRAINT:此层不需要人类可读|人类审计通过反编译到v4.x完成]

---

# I-Lang Machine Layer (IML) — 纯 AI 原生通信语法

## 设计公理

```
A1  可逆      IML ↔ I-Lang v4.x 无损双向转换 任何时候可反编译回人类可读
A2  确定性    同一条 IML 指令在任何模型上解析结果相同 零歧义
A3  最小熵    同等语义下 token 数最少的表达胜出
A4  自描述    语法规则本身可用 IML 编码 新模型读一遍规则即可解析
```

## 层级关系

```
Layer 3   人类层     自然语言（中/英）           给人看
Layer 2   协议层     I-Lang v4.x                 人和 AI 都看得懂
Layer 1   机器层     IML                         只给 AI 看
Layer 0   判断层     I-Lang v5.0 向量            判断函数（跨层）

压缩方向   L3 → L2 → L1    （人话→协议→机器码）
审计方向   L1 → L2 → L3    （机器码→协议→人话）
```

---

## §1 词根表 (Verb Roots)

88 个 v4.x 动词压缩为 2 字节词根。规则：取辅音骨架 + 首元音。

```
v4.x 动词     IML 词根    字节
────────      ────────    ────
READ          RD          2
WRITE         WR          2
GEN           GN          2
EVAL          EV          2
DIFF          DF          2
SAVE          SV          2
LOAD          LD          2
EXEC          EX          2
FIND          FN          2
SCAN          SC          2
SORT          SR          2
FILT          FL          2
SEND          SN          2
RECV          RC          2
AUTH          AU          2
CREA          CR          2
WRIT          WT          2
EDIT          ED          2
DELE          DL          2
FILL          FI          2
COMP          CM          2
CONV          CV          2
SUMM          SM          2
TRAN          TR          2
PARA          PR          2
EXPL          XP          2
LIST          LS          2
RANK          RK          2
SCOR          SK          2
ANSW          AN          2
UPDT          UP          2
MERG          MG          2
ARCH          AR          2
LINK          LK          2
VALI          VL          2
TEST          TS          2
DEBU          DB          2
DEPL          DP          2
MONI          MN          2
ALER          AL          2
RETR          RT          2
```

完整 88 词根映射表见附录 A。冲突解决规则：
第一个注册的词根拥有 2 字节权。后来冲突的加第三字节（首元音）。
词根表冻结在 release 里，新增词根走 PR 流程。

---

## §2 实体压缩 (Entity Shorthand)

v4.x 实体 `@XXX` 压缩为 1 字节前缀 `Φ` + 单字母。

```
v4.x          IML       含义
────          ───       ────
@IMG          ΦI        图像
@VID          ΦV        视频
@AUD          ΦA        音频
@SRC          ΦS        源
@DST          ΦD        目标
@PREV         ΦP        上一步输出
@LOCAL        ΦL        本地
@SCREEN       ΦN        屏幕
@LOG          ΦG        日志
@NULL         Φ0        空
@STDIN        ΦX        标准输入
@GH           ΦH        GitHub
@R2           ΦR        R2 存储
@CANVAS       ΦC        画布
```

Core entities: Φ + 大写字母
Media entities: Φ + 大写字母（已含在上表）
Custom entities: Φ + 小写字母 + 定义块

---

## §3 修饰符压缩 (Modifier Keys)

29 核心键 + 20 媒体键 = 49 键。压缩为 1-2 字节。

```
规则: 取首字母。冲突时取前两字母。

核心 29 键
v4.x    IML    v4.x    IML    v4.x    IML
fmt=    f=     lng=    l=     len=    n=
ton=    t=     sty=    y=     path=   p=
whr=    w=     mch=    m=     src=    s=
dst=    d=     frm=    fr=    to=     to=
by=     b=     via=    v=     if=     i=
on=     o=     at=     a=     lim=    li=
exc=    x=     inc=    ic=    tag=    tg=
pri=    pr=    grp=    g=     ord=    or=
dep=    dp=    ttl=    tt=    mode=   md=
conf=   cf=    gate=   gt=

媒体 20 键
sbj=    sj=    act=    ac=    plc=    pc=
txt=    tx=    pov=    pv=    fcl=    fc=
mvt=    mv=    lgt=    lg=    pal=    pa=
mdm=    mm=    asp=    as=    rsl=    rs=
qly=    q=     dur=    du=    fps=    fp=
sed=    se=    adh=    ah=    ref=    rf=
dlg=    dl=    sfx=    sf=
```

---

## §4 语法规则

### 4.1 基本句式

```
v4.x:   [READ:@SRC|path=/data|fmt=json]=>[EVAL|whr=quality]=>[WRITE:@DST]
IML:    RDΦSp=/data,f=j→EVw=quality→WRΦD

压缩比: 63 bytes → 31 bytes = 51%
```

### 4.2 语法结构

```
指令       = 词根 + 实体? + 修饰符组? 
修饰符组   = 修饰符 (, 修饰符)*
修饰符     = 键 = 值
管道       = →
终止       = Ω
并行       = ‖
条件       = ?条件:真分支;假分支
循环       = ×次数 或 ×条件
```

### 4.3 完整示例

```
=== 文生图 ===
v4.x:   [GEN:@IMG|subj=a fox reading a book|light=golden_hour|medium=watercolor|ratio=16:9]=>[Ω]
IML:    GNΦIsj=fox.reading.book,lg=gh,mm=wc,as=16:9→Ω

=== 文生视频链 ===
v4.x:   [GEN:@IMG|subj=city|medium=3d]=>[GEN:@VID|src=@PREV|motion=pan_left|dur=5s]=>[Ω]
IML:    GNΦIsj=city,mm=3d→GNΦVs=ΦP,mv=pl,du=5→Ω

=== 多步工作流 ===
v4.x:   [READ:@SRC|path=data.csv]=>[FILT|whr=score>80]=>[SORT|by=date|ord=desc]=>[WRITE:@DST|fmt=json]
IML:    RDΦSp=data.csv→FLw=score>80→SRb=date,or=desc→WRΦDf=j

=== 并行 ===
v4.x:   [SCAN:@SRC|path=/a]=>[Ω] || [SCAN:@SRC|path=/b]=>[Ω]
IML:    SCΦSp=/a→Ω‖SCΦSp=/b→Ω

=== 条件 ===
v4.x:   [EVAL:@PREV|whr=safe]=>IF(true)[EXEC]=>IF(false)[ALER]
IML:    EVΦPw=safe?EX;AL

=== 循环 ===
v4.x:   LOOP(3)[READ:@SRC]=>[EVAL]=>[NEXT]
IML:    ×3{RDΦS→EV}
```

---

## §5 值压缩规则

### 5.1 常用值缩写表

```
全称              缩写     适用键
json              j        f=
csv               c        f=
markdown          m        f=
english           en       l=
chinese           zh       l=
golden_hour       gh       lg=
watercolor        wc       mm=
photograph        ph       mm=
oil_painting      op       mm=
3d_render         3d       mm=
pan_left          pl       mv=
zoom_in           zi       mv=
wide_angle        wa       pv=
rule_of_thirds    r3       (构图)
close_up          cu       pv=
shallow           sw       (景深)
ascending         asc      or=
descending        desc     or=
```

### 5.2 数值直传

数值不压缩，直传：`du=5` `fp=30` `as=16:9` `rs=1024`

### 5.3 字符串值

空格替换为 `.`：`sj=fox.reading.book`
逗号替换为 `+`：`x=text+watermark+blur`

---

## §6 反编译规则 (IML → v4.x)

```
任何 IML 指令都可以通过以下规则无损还原为 v4.x：

1. 词根 → 查词根表 → 还原动词
2. Φ + 字母 → 查实体表 → 还原 @XXX
3. 单字母键 → 查修饰符表 → 还原全名
4. 值缩写 → 查值缩写表 → 还原全称
5. → 还原为 =>[ ]
6. Ω 保持
7. . 还原为空格（在字符串值中）
8. + 还原为逗号（在排除列表中）

反编译器是确定性函数 输入同一条 IML 任何实现输出同一条 v4.x
反编译器代码随 spec 一起发布（Python 参考实现）
```

---

## §7 与 Astra machineslop 的本质区别

```
Astra machineslop                    IML
────────────────                     ───
模型自发产生 无规范                    有 spec 有字典 有版本号
不可逆 无法还原为可读形式              可逆 确定性反编译到 v4.x
模型决定什么时候压缩                   操作者决定（三档开关）
每次压缩方式不同                       同一语义永远同一编码
没有字典 后来者无法学习                 字典公开 新模型读一遍即可
不可审计                              通过反编译可审计
```

---

## §8 release 计划

```
此 spec 作为 I-Lang Machine Layer v0.1 draft
不合并进 v4.x 或 v5.0 → 独立 spec 文件
独立 Zenodo DOI
时间戳: 2026-09-12 = 比 Astra machineslop 讨论早... 不，同一天

release 路径:
  draft 0.1  → CC 审 + 三模型实测（IML 指令能否被 DS/GPT/Claude 正确执行）
  draft 0.2  → 词根冲突解决 + 反编译器 Python 实现
  v1.0.0     → 冻结词根表 + 切 GitHub release + Zenodo DOI
```

---

## 附录 B: token 对比实测模板

```python
# 对同一条指令的三个层级计算 tiktoken 数
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")

l3 = "Read the file at /data/input.csv, filter rows where score is above 80, sort by date descending, and write the result as JSON to the output destination."
l2 = "[READ:@SRC|path=/data/input.csv]=>[FILT|whr=score>80]=>[SORT|by=date|ord=desc]=>[WRITE:@DST|fmt=json]"
l1 = "RDΦSp=/data/input.csv→FLw=score>80→SRb=date,or=desc→WRΦDf=j"

for label, text in [("L3 human", l3), ("L2 v4.x", l2), ("L1 IML", l1)]:
    tokens = len(enc.encode(text))
    print(f"{label:12s}  {tokens:3d} tokens  {len(text):3d} chars")
```

---

::FACT{timestamp|conf:2026-09-12|note:same_day_as_Astra_machineslop_discussion|DOI:pending_release}
::RULE{审计方式⇒反编译到 L2 然后人类审 L2|人类永远不需要直接读 L1}
::RULE{此 spec 是标准不是应用|应用层怎么用是产品决定}

=>[Ω]
