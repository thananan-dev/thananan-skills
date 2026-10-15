# pre-flight-check — flow.json schema

The only file you write. `build_flow.py` validates it and builds `FLOW.html` next to it. Inline `code` and **bold** render everywhere.

## flow.json (→ FLOW.html via build_flow.py)

```jsonc
{
  "title": "หัวข้อเต็ม", "short": "ชื่อแท็บเบราว์เซอร์",
  "scope": "<branch> @ <sha> · ยังไม่ commit · m ไฟล์แก้ + n ไฟล์ใหม่ · +a/−d",  // โหมด default (uncommitted only)
  // โหมด --branch: "<branch> @ <sha> · ทั้ง branch ตั้งแต่แยกจาก <base>@<base-sha> · m ไฟล์แก้ + n ไฟล์ใหม่ · +a/−d"
  "why": ["**เดิม:** ...", "**หลัง:** ...", "**คำศัพท์:** ..."],          // `code` และ **bold** ใช้ได้
  "impacts": [{"level": "red|orange|yellow", "node": "2.4", "text": "..."}], // node ว่างได้ถ้าอยู่นอก chain
  "lanes": [{"id": "ui", "name": "UI", "sub": "component / page"}, ...],  // ไม่บังคับ — ตั้งเลนเองให้ตรงกับสถาปัตยกรรมของ repo นี้ (2–6 เลน) ไม่ใส่ = ใช้ค่า default 5 เลน api|app|domain|infra|db
  "pages": [{"tab": "📄 เอกสารที่แก้", "title": "...", "sub": "...",
    "blocks": [{"h": "หัวข้อ", "text": "...", "items": ["..."], "ba": ["ก่อน", "หลัง"],
                "table": {"head": ["ไฟล์", "สาระ", "ตรงกับโค้ด?"], "rows": [["..", "..", "✅"]]}}]}],  // ทุก key ใน block ไม่บังคับ
  "chains": [{
    "tab": "② ประมวลผล ⭐", "title": "② ... — POST /v1/...", "sub": "หนึ่งบรรทัดบอกว่าเส้นนี้คืออะไร",
    "nodes": [{
      "id": "2.4", "name": "`lockEligibility`",
      "layer": "api|app|domain|infra|db",        // เลนในแผนภาพ — ต้องเป็น id หนึ่งใน "lanes" ด้านบน (หรือ 5 ค่า default ถ้าไม่ได้ใส่ "lanes")
      "status": "new|changed|same",
      "sub": false, "parent": "2.4",             // sub=true → แสดงเยื้อง ลูกศรประจาก parent
      "file": "src/orders/service/process.ts", "line": 570,  // ตัวอย่าง — ใช้ path ไฟล์จริงของ repo (ภาษา/นามสกุลอะไรก็ได้)
      "caller": "[2.2] :210",
      "short": "ข้อความบนกล่อง ≤ 40 ตัวอักษร",
      "why": "ทำไมต้องเรียก / ถ้าไม่มีจะพังอะไร",  // บังคับ
      "impact": {"level": "orange", "text": "..."},
      "inside": [[":571", "ทำอะไร", "ทำไม / ถ้าไม่ผ่านตอบอะไร"]],   // บังคับสำหรับทุก node ที่ไม่ใช่ pass-through — รวม ⚪
      "extra": [{"title": "ตารางเสริม", "head": ["ก", "ข"], "rows": [["..", ".."]]}],
      "changed": ["ก่อน", "หลัง"],               // บังคับเมื่อ status = changed
      "types": [["`Type`", "file:line", "ทำไมรูปร่างนี้"]]
    }]
  }]
}
```
