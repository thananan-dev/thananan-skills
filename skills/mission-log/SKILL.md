---
name: mission-log
description: >
  Draft a Merge Request (MR) or Pull Request (PR) description in a clear, consistent Summary/Changes/Test-plan format. Use this skill whenever the user says "เขียน MR", "สร้าง MR", "draft MR", "เขียน PR", "ช่วย MR", "MR description", "PR description", "write merge request", "write pull request", or asks to summarize / format changes for a git merge or pull request — even if they just say "ช่วยเขียน description ให้หน่อย" or paste a list of commits and ask for a write-up. Always invoke this skill before writing any MR/PR description.
---

# mission-log

A mission log for a branch — a concise report of what happened, for reviewers to read before touching the diff.

## Output format

Always use this exact structure as a raw Markdown code block so the user can copy-paste directly:

````markdown
## Summary

{1–2 sentences: อธิบายตรง ๆ ว่า MR นี้ทำอะไรโดยรวม — ไม่ต้องขึ้นต้นด้วยการอ้าง ticket}

Related: {ticket/issue ID ทั้งหมดที่เกี่ยวข้อง รวมถึงตัวหลักที่ MR นี้แก้ด้วย คั่นด้วยจุลภาคถ้ามีหลายอัน — ตัดบรรทัดนี้ทิ้งทั้งหมดถ้าไม่มี}

### Changes

**{Group name}**
- {bullet — สั้น กระชับ, ใช้ inline code สำหรับ field/route/value}
- ...

**{Another group}**
- ...

## Test plan

- [ ] {scenario — format: action → expected result}
- [ ] ...
````

## Rules

### Summary
- 1–2 ประโยค อธิบายตรง ๆ ว่า MR นี้ทำอะไรโดยรวม — ห้ามขึ้นต้นด้วย "ต่อจาก ticket X —" หรือรูปแบบอ้าง ticket ใด ๆ ในประโยค ticket ทั้งหมดอยู่ในบรรทัด Related แทน
- ไม่ต้องพูดถึงทุก change — แค่ให้ภาพรวมที่ reviewer เข้าใจทันที
- บรรทัด **Related** คือที่เดียวที่ใส่ ticket/issue — รวมทั้งตัวหลักที่ MR นี้แก้ และตัวอื่นที่เกี่ยวข้อง (parent epic, related bug, ticket อื่นที่ MR นี้แตะ) ถ้าไม่มีเลยให้ตัดบรรทัดนี้ออก อย่าใส่ "Related: -" หรือค่าว่าง

### Changes
- จัดกลุ่ม changes เป็น **bold header** ตามหัวข้อ เช่น feature name, ticket/issue, หรือ category (API, UI fixes, Docs)
- แต่ละ bullet = หนึ่ง logical change; ใช้ inline code สำหรับ field names, routes, values
- เรียงกลุ่มจาก user-facing / สำคัญที่สุด → housekeeping / docs ท้ายสุด
- ถ้าโปรเจกต์มี ticket/issue ID convention (Jira key, GitHub issue #, Linear ID, ฯลฯ) ให้ใส่ใน group header หรือ bullet ตามที่เหมาะ — อย่าสมมติ format เอง ถ้าไม่เห็นร่องรอยจาก commit message/branch name ให้ถามหรือข้ามไปเลย

### Test plan
- ใช้ checkbox `- [ ]` ทุก item
- แต่ละ item = หนึ่ง scenario; format: `{สิ่งที่ทำ} → {ผลที่คาดหวัง}`
- ครอบคลุม: happy path, edge case จาก bug/feature, permission boundary (ถ้ามี)
- เขียนให้คนที่ไม่รู้ code ก็ทำ manual test ตามได้

### Tone
- Thai/English mixed ได้ตามธรรมชาติของ codebase
- Technical terms เป็น English เสมอ (เช่น `modal`, ชื่อ component, HTTP status code)
- กระชับ — ไม่มีคำฟุ่มเฟือย

## Gathering information

**Summary — ถามก่อนเสมอ ด้วย 2 คำถามแยกกัน** (ใช้ structured multiple-choice question ถ้ามี เช่น `AskUserQuestion` — รวมสองเรื่องนี้เป็นประโยคเดียวแล้วมักได้คำตอบแค่ข้อเดียว จึงต้องแยกให้ชัดเป็นคนละข้อ)

1. **Summary ให้เขียนเกี่ยวกับอะไร** — ให้ตัวเลือก: (ก) สรุปเอาจาก commit message/diff ที่ทำจริง (เร็ว แต่จะไม่มี "ทำไม" ที่ไม่ได้เขียนไว้ใน commit) หรือ (ข) custom — user พิมพ์เนื้อหาเอง (ใช้เมื่อมี context อย่าง sprint goal ที่ไม่มีใน git history)
2. **เกี่ยวข้องกับ ticket/issue ใดบ้าง** — ตัวหลักที่แก้, parent epic, related bug ฯลฯ สำหรับใส่ในบรรทัด Related

ห้ามข้ามข้อไหนไปแม้ user จะตอบแค่ข้อเดียว ให้ถามย้ำข้อที่ขาดจนกว่าจะได้คำตอบครบทั้งสองข้อ — ถ้าเลือก (ก) ในข้อ 1 ค่อยไปดึง commit/diff มาสรุปหลังจากขั้นตอน gathering ด้านล่าง

เมื่อได้ context แล้วค่อยไปดึงข้อมูล Changes และ Test plan จาก git — หา base branch จริงของ repo ก่อน (`main`, `master`, `develop`, ฯลฯ — เช็คจาก default branch ของ remote หรือถามถ้าไม่ชัวร์) แล้วรัน:
1. `git log <base>...HEAD --oneline` — commit list และ ticket IDs (ถ้ามี)
2. `git diff <base>...HEAD --stat` — ไฟล์ที่เปลี่ยน
3. `git diff <base>...HEAD` — รายละเอียด change สำหรับ grouping และ test steps

## Example

```markdown
## Summary

เพิ่ม bulk export ให้หน้า reports พร้อมแก้ปัญหา filter ค้าง

Related: PROJ-408 (ticket หลัก), PROJ-401 (parent epic), PROJ-455 (bug report ต้นเรื่อง filter ค้าง)

### Changes

**Bulk export (PROJ-408)**
- เพิ่มปุ่ม "Export selected" บนหน้า reports list พร้อม checkbox เลือกหลายแถว
- Endpoint ใหม่ `POST /api/reports/export` รับ `report_ids[]` คืนไฟล์ CSV
- แสดง progress toast ระหว่าง export ไฟล์ใหญ่

**Filter fixes**
- แก้ bug `StatusFilter` กด clear แล้วค่าเก่ายังค้างใน URL query
- Debounce search input จาก 0ms เป็น 300ms ลด request ถี่เกินไป

**Docs**
- อัปเดต `REPORTS.md` ให้ตรงกับ endpoint ใหม่

## Test plan

- [ ] เลือก 3 แถวในหน้า reports → กด "Export selected" → ได้ไฟล์ CSV มี 3 แถวตรงกับที่เลือก
- [ ] Export รายการ >1000 แถว → progress toast ขึ้นระหว่างรอ ไม่ freeze หน้าจอ
- [ ] ตั้งค่า StatusFilter แล้วกด clear → query param หายจาก URL ด้วย
- [ ] พิมพ์ค้นหาเร็ว ๆ ใน search input → request ยิงแค่ครั้งเดียวหลังหยุดพิมพ์ 300ms
```
