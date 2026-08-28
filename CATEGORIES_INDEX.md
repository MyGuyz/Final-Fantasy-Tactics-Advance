# FFTA — ดัชนีหมวดหมู่ข้อความที่แปลได้

อัปเดตรอบที่ 3: **พบและแก้ช่องโหว่สำคัญ** — ข้อความจำนวนมากถูกบีบอัดด้วย FFTA LZSS ฝังในสตริง (control code `0x32`) ซึ่งรอบก่อนหน้าถอดไม่ออก ทำให้ **บทสนทนาเนื้อเรื่องหลักหายไปเกือบทั้งหมด** รอบนี้ implement ตัวถอดแล้ว กู้คืนมาได้ **1,491 บรรทัดใหม่**

รวมทั้งหมด 5,361 บรรทัดไม่ซ้ำ จาก 55,960 สตริงที่สแกนได้

รูปแบบไฟล์: `[offset] ข้อความ` (มี `xN` ถ้าพบซ้ำ N ครั้ง)

| ไฟล์ | หมวดหมู่ | จำนวน |
|---|---|---|
| [story_dialogue.txt](categorized_text/story_dialogue.txt) | บทสนทนาเนื้อเรื่อง/คัตซีน/บทพูดตัวละคร (ส่วนใหญ่บีบอัด LZSS ฝังใน) | 1,839 |
| [crn_names.txt](categorized_text/crn_names.txt) | ชื่อเฉพาะอ้างอิงในบทสนทนา (ตัวละคร/มอนสเตอร์) | 100 |
| [skills.txt](categorized_text/skills.txt) | ชื่อทักษะ/สกิล/ความสามารถ | 612 |
| [rumor_titles.txt](categorized_text/rumor_titles.txt) | ชื่อบทความข่าวลือ Ivalice / หัวข้อภารกิจ | 421 |
| [system_ui.txt](categorized_text/system_ui.txt) | ข้อความระบบ เซฟ/โหลด/เมนู | 313 |
| [npc_pool.txt](categorized_text/npc_pool.txt) | ชื่อสุ่มสมาชิกแคลน/NPC | 571 |
| [items.txt](categorized_text/items.txt) | ชื่อไอเทม/อาวุธ/ชุดเกราะ | 721 |
| [status_labels.txt](categorized_text/status_labels.txt) | ป้ายสถานะ/ธาตุ UI สั้น | 13 |
| [battle_log.txt](categorized_text/battle_log.txt) | ข้อความระบบการต่อสู้ + คำอธิบายเอฟเฟกต์ | 298 |
| [rumor_body.txt](categorized_text/rumor_body.txt) | เนื้อหาข่าวลือ Ivalice + ข้อความภารกิจ (ปนกัน) | 392 |
| [unclassified.txt](categorized_text/unclassified.txt) | ยังไม่จัดหมวด — ต้องตรวจด้วยตา | 81 |
