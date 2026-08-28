import json, re, collections, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

new = json.load(open(os.path.join(BASE,'data','FFTA_corpus_raw.json'), encoding='utf-8'))
NL = chr(10)
TEXT = [(0x390000, 0x3A0000), (0x490000, 0x4A0000), (0x4B0000, 0x4F0000),
        (0x520000, 0x530000), (0x550000, 0x570000), (0x9C0000, 0xA20000)]


def intext(o):
    return any(lo <= o < hi for lo, hi in TEXT)


def clean(t):
    return re.sub(r'\s+', ' ', re.sub(r'\{[^}]*\}', '', t)).strip()


def is_noise(c):
    L = re.sub(r'[^A-Za-z]', '', c)
    if len(L) < 2:
        return True
    if re.search(r'(.)\1{3,}', L):
        return True
    run = best = 1
    for i in range(1, len(L)):
        if ord(L[i]) - ord(L[i - 1]) in (1, -1):
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best >= 5


COMMON = re.compile(r'\b(the|you|and|that|this|have|with|for|are|not|but|your|will|can|its|our|all|from|they|what|when|there|been|were|his|her|him|she|has|had|was|out|who|how|any|one|now|get|got|about|would|could|them|then|than|some|more|just|like|into|over|after|only|know|make|take|come|here|want|need|see|say|good|much|very|well|back|down|even|also|because|before|through|should|these|those|where|which|while|other|first|last|most|many|such|being|does|did|too|off|why|way|day|man|new|old|own|use|two|may|part)\b', re.I)

broken = []
for d in new:
    o = int(d['offset'], 16)
    if not intext(o):
        continue
    c = clean(d['text'])
    if len(re.sub(r'[^A-Za-z]', '', c)) < 8:
        continue
    if is_noise(c) or not COMMON.search(c):
        continue
    junk = len(re.findall(r'\{u[0-9A-F]{2}\}', d['text'])) + len(re.findall(r'\{LZSS_FAIL\}', d['text']))
    if junk >= 3:
        broken.append((d['offset'], c, d['text']))

broken.sort(key=lambda x: int(x[0], 16))
path = os.path.join(BASE,'data','categorized_text','_INCOMPLETE_needs_work.txt')
with open(path, 'w', encoding='utf-8') as f:
    f.write('# ข้อความที่ถอดได้ไม่สมบูรณ์ (' + str(len(broken)) + ' รายการ)' + NL)
    f.write('# สาเหตุ: ยังมีรูปแบบบีบอัด/back-reference แบบฝังในสตริงที่ยังถอดไม่ออก (ไม่มี marker 0x32)' + NL)
    f.write('# บรรทัดแรก = ที่อ่านออกบางส่วน / บรรทัด RAW = ผลถอดดิบพร้อม placeholder' + NL + NL)
    for off, c, raw in broken:
        f.write('[' + off + ']' + chr(9) + c + NL)
        f.write('   RAW: ' + raw[:300].replace(NL, '\\n') + NL + NL)
print('wrote', len(broken), 'broken entries')
