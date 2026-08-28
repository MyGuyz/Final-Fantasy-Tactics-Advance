import json, re, os, collections
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data = json.load(open(os.path.join(BASE,'data','FFTA_corpus_raw.json'), encoding='utf-8'))
NL = chr(10)

PUNCT = {'E4': '.', 'EC': ',', 'FC': ':', 'EB': '!', 'FE': '-',
         'F6': chr(34), 'F4': chr(39), 'EA': '?', 'EE': chr(0x2014)}


def prettify(text):
    t = re.sub(r'\{80([0-9A-F]{2})\}', lambda m: PUNCT.get(m.group(1), ''), text)
    t = t.replace('{40:70}{40:63}', NL + NL).replace('{40:61}{40:63}', NL + NL)
    t = t.replace('{PAGE}{CLEAR}', NL + NL)
    t = re.sub(r'\{NAME:[0-9A-F]{2}\}', '<NAME>', t)
    t = re.sub(r'\{[^}]*\}', '', t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r' ' + NL, NL, t)
    t = re.sub(NL + '{3,}', NL + NL, t)
    return t.strip()


def is_noise(text):
    letters = re.sub(r'[^A-Za-z]', '', text)
    if len(letters) < 2:
        return True
    if re.search(r'(.)\1{3,}', letters):
        return True
    run = best = 1
    for i in range(1, len(letters)):
        if ord(letters[i]) - ord(letters[i - 1]) == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best >= 5


def quality(text):
    c = re.sub(r'\{[^}]*\}', '', text)
    return len(c) / max(len(text), 1)


REGIONS = [
    (0x9C0000, 0xA20000, 'story_dialogue', 'บทสนทนาเนื้อเรื่อง/คัตซีน/บทพูดตัวละคร (ส่วนใหญ่บีบอัด LZSS ฝังใน)'),
    (0x550800, 0x552500, 'crn_names', 'ชื่อเฉพาะอ้างอิงในบทสนทนา (ตัวละคร/มอนสเตอร์)'),
    (0x552500, 0x557000, 'skills', 'ชื่อทักษะ/สกิล/ความสามารถ'),
    (0x557000, 0x560000, 'rumor_titles', 'ชื่อบทความข่าวลือ Ivalice / หัวข้อภารกิจ'),
    (0x563000, 0x567000, 'system_ui', 'ข้อความระบบ เซฟ/โหลด/เมนู'),
    (0x567000, 0x570000, 'npc_pool', 'ชื่อสุ่มสมาชิกแคลน/NPC'),
    (0x520000, 0x530000, 'items', 'ชื่อไอเทม/อาวุธ/ชุดเกราะ'),
    (0x390000, 0x3A0000, 'status_labels', 'ป้ายสถานะ/ธาตุ UI สั้น'),
    (0x490000, 0x4A0000, 'battle_log', 'ข้อความระบบการต่อสู้ + คำอธิบายเอฟเฟกต์'),
    (0x4B0000, 0x4F0000, 'rumor_body', 'เนื้อหาข่าวลือ Ivalice + ข้อความภารกิจ (ปนกัน)'),
]

# The remaining 4+ letter "unclassified" hits (outside every known text REGION)
# audited individually and confirmed non-text: raw ROM bytes decode to smooth
# gradient/graphics-style curves (low byte-to-byte delta), not real words. See
# data/categorized_text/unclassified.txt header for the full writeup.
CONFIRMED_NOISE_OFFSETS = {
    '0x18fc3c', '0x1bd4db', '0x1d59f6', '0x1f1150', '0x1f4c58', '0x2e2f73',
    '0x31b5a3', '0x3230c6', '0x576df9', '0x5dffca', '0x8fdc31', '0x902bb4',
    '0x914cb8', '0x91e006', '0x92bfd9', '0x92f401', '0x932f52', '0x940a39',
}

buckets = collections.defaultdict(dict)
noise_n = 0
for d in data:
    off = int(d['offset'], 16)
    text = prettify(d['text'])
    if is_noise(text) or quality(d['text']) < 0.45:
        noise_n += 1
        continue
    key = 'unclassified'
    for lo, hi, k, _ in REGIONS:
        if lo <= off < hi:
            key = k
            break
    # Anything outside every known text REGION and shorter than 4 letters is
    # almost certainly a scanner false-positive, not real text: audited all 81
    # such hits once (see data/categorized_text/unclassified.txt header) and
    # found none were real words — mostly coincidental byte runs from smooth
    # gradient/graphics data landing in the charmap's letter range. The loose
    # single-byte-mode start condition (`0x01` then any `0x80-0xFF` byte) makes
    # this kind of short false start common outside the curated text regions.
    if key == 'unclassified':
        letters = re.sub(r'[^A-Za-z]', '', text)
        if len(letters) < 4 or d['offset'] in CONFIRMED_NOISE_OFFSETS:
            noise_n += 1
            continue
    if text not in buckets[key]:
        buckets[key][text] = {'offset': d['offset'], 'count': 0}
    buckets[key][text]['count'] += 1

LABELS = {k: lab for _, _, k, lab in REGIONS}
LABELS['unclassified'] = 'ยังไม่จัดหมวด — ต้องตรวจด้วยตา'

outdir = os.path.join(BASE,'data','categorized_text')
os.makedirs(outdir, exist_ok=True)
# unclassified.txt is hand-maintained (documents the noise audit) and
# _INCOMPLETE_needs_work.txt is produced by gapreport.py, not this script —
# never auto-delete either. Only genuinely new unclassified hits (not seen
# before) would need a human to look at and fold into that writeup.
KEEP_FILES = {'unclassified.txt', '_INCOMPLETE_needs_work.txt'}
for f in os.listdir(outdir):
    if f in KEEP_FILES:
        continue
    os.remove(os.path.join(outdir, f))

order = [k for _, _, k, _ in REGIONS]
rows = []
total = 0
unclassified_new = buckets.get('unclassified') or {}
if unclassified_new:
    print(f'WARNING: {len(unclassified_new)} NEW unclassified hits not covered by the noise audit — review by hand:')
    for text, meta in sorted(unclassified_new.items(), key=lambda x: int(x[1]['offset'], 16)):
        print('  ', meta['offset'], repr(text))
for key in order:
    items = buckets.get(key) or {}
    if not items:
        continue
    total += len(items)
    with open(os.path.join(outdir, key + '.txt'), 'w', encoding='utf-8') as f:
        f.write('# ' + LABELS[key] + '  (' + str(len(items)) + ' รายการไม่ซ้ำ)' + NL + NL)
        for text, meta in sorted(items.items(), key=lambda x: int(x[1]['offset'], 16)):
            cnt = ' x' + str(meta['count']) if meta['count'] > 1 else ''
            f.write('[' + meta['offset'] + ']' + cnt + chr(9) + text + NL)
            if NL in text:
                f.write('---' + NL)
    rows.append((key, LABELS[key], len(items)))

incomplete_path = os.path.join(outdir, '_INCOMPLETE_needs_work.txt')
incomplete_n = 0
if os.path.exists(incomplete_path):
    with open(incomplete_path, encoding='utf-8') as f:
        incomplete_n = sum(1 for line in f if line.startswith('['))

with open(os.path.join(BASE,'CATEGORIES_INDEX.md'), 'w', encoding='utf-8') as f:
    f.write('# FFTA — ดัชนีหมวดหมู่ข้อความที่แปลได้' + NL + NL)
    f.write('อัปเดตรอบที่ 4: ตรวจสอบ 81 รายการที่เคย "ยังไม่จัดหมวด" แล้วสรุปว่าเป็น false positive จากการสแกนทั้งหมด (ดู `data/categorized_text/unclassified.txt`) — ไม่ใช่ backlog ที่ต้องแปล จึงตัดออกจากตารางนี้' + NL + NL)
    f.write('รวมทั้งหมด ' + format(total, ',') + ' บรรทัดไม่ซ้ำ (จัดหมวดสมบูรณ์แล้ว) + ' + format(incomplete_n, ',') + ' บรรทัดถอดไม่สมบูรณ์ (`_INCOMPLETE_needs_work.txt`) จาก ' + format(len(data), ',') + ' สตริงที่สแกนได้' + NL + NL)
    f.write('รูปแบบไฟล์: `[offset] ข้อความ` (มี `xN` ถ้าพบซ้ำ N ครั้ง)' + NL + NL)
    f.write('| ไฟล์ | หมวดหมู่ | จำนวน |' + NL + '|---|---|---|' + NL)
    for key, lab, cnt in rows:
        f.write('| [' + key + '.txt](categorized_text/' + key + '.txt) | ' + lab + ' | ' + format(cnt, ',') + ' |' + NL)
    f.write('| [_INCOMPLETE_needs_work.txt](categorized_text/_INCOMPLETE_needs_work.txt) | ถอดได้ไม่สมบูรณ์ — รอไข compression scheme อีกแบบ (ดู README.md "ปัญหา 1") | ' + format(incomplete_n, ',') + ' |' + NL)

print('total unique:', total, 'noise filtered:', noise_n)
for key, lab, cnt in rows:
    print(' ', key, cnt)
