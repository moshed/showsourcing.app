// Excel template for the vendor quote form (2026-10-23). Loaded only when the
// vendor taps Download or Upload. One row per item; one column per form field
// (the team's custom fields included), dropdowns for choice fields, and photo
// columns. Reading back finds photos three ways:
//   1. pictures floating OVER the cells (drawing anchors, matched by row),
//   2. pictures placed IN a cell (Excel 365 "Place in Cell": richData),
//   3. WPS Office in-cell pictures (=DISPIMG("ID_..."), xl/cellimages.xml).
(function () {
  const LIBS = [
    "/lib/jszip.min.js",
    "/lib/exceljs.min.js",
  ];
  const PHOTO_COLS = 3;
  const FIRST_DATA_ROW = 3; // row 1 = field keys (hidden), row 2 = labels
  const ROWS = 60;

  function load(src) {
    return new Promise((ok, bad) => {
      if ([...document.scripts].some((s) => s.src === src)) return ok();
      const s = document.createElement("script");
      s.src = src; s.onload = ok; s.onerror = () => bad(new Error("Could not load " + src));
      document.head.appendChild(s);
    });
  }
  async function libs() { for (const s of LIBS) await load(s); }

  function colName(n) { // 1 -> A
    let s = "";
    while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
    return s;
  }

  // Price by quantity: one price column per quantity ("pb:1000").
  // The vendor sets the quantities: one text column, "1000: 4.20; 5000: 3.95".
  function sheetFields(form) {
    return form.fields.flatMap((f) => f.kind !== "ladder" ? [f]
      : !(f.qtys || []).length ? [{ key: "pb:text", label: "Price by quantity (e.g. 1000: 4.20; 5000: 3.95)", kind: "longtext" }]
      : f.qtys.map((q) => ({ key: `pb:${q}`, label: `Price for ${Number(q).toLocaleString("en-US")} pcs`, kind: "currency" })));
  }
  function pairs(text) { // "1,000 pcs: 4.20; 5k = 3.95" -> [{qty, price}]
    const out = [];
    for (const m of String(text).matchAll(/([\d][\d,.]*\s*[kK]?)\s*(?:pcs|pc|units?)?\s*[:=@]\s*[^\d;\n]*([\d][\d,.]*)/g)) out.push({ qty: m[1].trim(), price: m[2] });
    return out;
  }

  // ---------- Template ----------
  async function download(form) {
    await libs();
    const wb = new ExcelJS.Workbook();
    wb.creator = "Show Sourcing";
    const ws = wb.addWorksheet("Items", { views: [{ state: "frozen", ySplit: 2 }] });
    const lists = wb.addWorksheet("Lists", { state: "hidden" });
    const how = wb.addWorksheet("How to fill in");

    const fields = sheetFields(form);
    const keys = [...fields.map((f) => f.key), ...Array.from({ length: PHOTO_COLS }, (_, i) => `photo${i + 1}`)];
    const labels = [...fields.map((f) => f.label + (f.required ? " *" : "")), ...Array.from({ length: PHOTO_COLS }, (_, i) => `Photo ${i + 1}`)];
    ws.addRow(keys);
    ws.addRow(labels);
    ws.getRow(1).hidden = true;
    const head = ws.getRow(2);
    head.font = { bold: true, color: { argb: "FFFFFFFF" } };
    head.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFF97316" } };
    head.height = 30;
    head.alignment = { vertical: "middle", wrapText: true };

    // Dropdown lists live on the hidden Lists sheet (Excel caps inline lists at 255 characters).
    let listCol = 1;
    function listRange(values) {
      const c = colName(listCol++);
      values.forEach((v, i) => { lists.getCell(`${c}${i + 1}`).value = v; });
      return `Lists!$${c}$1:$${c}$${Math.max(values.length, 1)}`;
    }
    fields.forEach((f, i) => {
      const col = ws.getColumn(i + 1);
      col.width = f.kind === "longtext" ? 40 : f.key === "name" ? 30 : 18;
      let range = null;
      if (f.kind === "category" && form.categories?.length) range = listRange(form.categories);
      if (f.kind === "choice" && f.options?.length) range = listRange(f.options);
      if (f.kind === "toggle") range = listRange(["Yes", "No"]);
      for (let r = FIRST_DATA_ROW; r < FIRST_DATA_ROW + ROWS; r++) {
        const cell = ws.getCell(r, i + 1);
        cell.alignment = { vertical: "top", wrapText: true };
        if (range) {
          cell.dataValidation = { type: "list", allowBlank: true, formulae: [range],
            showErrorMessage: f.kind !== "category", errorTitle: f.label, error: "Pick a value from the list." };
        }
        if (f.kind === "number" || f.kind === "currency") cell.numFmt = f.kind === "currency" ? "0.00" : "0";
      }
    });
    for (let p = 0; p < PHOTO_COLS; p++) ws.getColumn(fields.length + 1 + p).width = 22;
    for (let r = FIRST_DATA_ROW; r < FIRST_DATA_ROW + ROWS; r++) ws.getRow(r).height = 90;

    how.getColumn(1).width = 100;
    [
      `${form.rfq?.name || form.title || "Quote"} — ${form.team || ""}`,
      "",
      "1. Fill in one row per item on the Items sheet. Fields marked * are required.",
      "2. Pick from the dropdown where a cell has one.",
      "3. Add up to 3 pictures per item in the Photo columns, on the item's row.",
      "   You can place a picture IN the cell or put it OVER the cell. Both work.",
      "4. Save the file and upload it on the same page. Check the items, then press Send quote.",
    ].forEach((t, i) => { how.getCell(i + 1, 1).value = t; if (i === 0) how.getCell(1, 1).font = { bold: true, size: 14 }; });

    const buf = await wb.xlsx.writeBuffer();
    const blob = new Blob([buf], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${(form.rfq?.name || form.title || "Quote").replace(/[^\w -]+/g, "").trim() || "Quote"} - template.xlsx`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }

  // ---------- Reading ----------
  const parseXML = (s) => new DOMParser().parseFromString(s, "application/xml");
  const byLocal = (doc, name) => [...doc.getElementsByTagName("*")].filter((e) => e.localName === name);
  const attr = (e, local) => { for (const a of e.attributes) if (a.localName === local) return a.value; return null; };
  function resolve(base, target) { // base "xl/worksheets/sheet1.xml", target "../drawings/drawing1.xml"
    if (target.startsWith("/")) return target.slice(1);
    const parts = base.split("/"); parts.pop();
    for (const t of target.split("/")) { if (t === "..") parts.pop(); else if (t !== ".") parts.push(t); }
    return parts.join("/");
  }
  async function rels(zip, path) {
    const p = resolve(path, "_rels/" + path.split("/").pop() + ".rels");
    const f = zip.file(p); if (!f) return {};
    const doc = parseXML(await f.async("string"));
    const out = {};
    for (const r of byLocal(doc, "Relationship")) out[r.getAttribute("Id")] = resolve(path, r.getAttribute("Target"));
    return out;
  }
  function cellRef(ref) { // "E12" -> {col: 5, row: 12}
    const m = /^([A-Z]+)(\d+)$/.exec(ref || ""); if (!m) return null;
    let col = 0; for (const ch of m[1]) col = col * 26 + (ch.charCodeAt(0) - 64);
    return { col, row: +m[2] };
  }

  // Every picture on the sheet as {row (1-based), bytes, ext}.
  async function pictures(zip, sheetPath, sheetXML) {
    const out = [];
    const media = async (path) => { const f = zip.file(path); return f ? { bytes: await f.async("uint8array"), ext: path.split(".").pop().toLowerCase() } : null; };
    const sheetRels = await rels(zip, sheetPath);

    // 1. Floating pictures, anchored to the cell under their top-left corner.
    for (const d of byLocal(sheetXML, "drawing")) {
      const drawingPath = sheetRels[attr(d, "id")]; if (!drawingPath || !zip.file(drawingPath)) continue;
      const ddoc = parseXML(await zip.file(drawingPath).async("string"));
      const drels = await rels(zip, drawingPath);
      for (const anchor of [...byLocal(ddoc, "twoCellAnchor"), ...byLocal(ddoc, "oneCellAnchor")]) {
        const from = byLocal(anchor, "from")[0]; const blip = byLocal(anchor, "blip")[0];
        if (!from || !blip) continue;
        const row0 = +byLocal(from, "row")[0].textContent;
        const m = await media(drels[attr(blip, "embed")]);
        if (m) out.push({ row: row0 + 1, ...m });
      }
    }

    // 2. Excel "Place in Cell": <c r="E3" vm="1"> -> metadata -> rich value -> image.
    const vmCells = byLocal(sheetXML, "c").filter((c) => c.getAttribute("vm"));
    if (vmCells.length && zip.file("xl/metadata.xml") && zip.file("xl/richData/rdrichvalue.xml")) {
      const meta = parseXML(await zip.file("xl/metadata.xml").async("string"));
      const valueBk = byLocal(meta, "valueMetadata")[0] ? byLocal(byLocal(meta, "valueMetadata")[0], "bk") : [];
      const futureBk = byLocal(meta, "futureMetadata")[0] ? byLocal(byLocal(meta, "futureMetadata")[0], "bk") : [];
      const rv = byLocal(parseXML(await zip.file("xl/richData/rdrichvalue.xml").async("string")), "rv");
      const relDoc = zip.file("xl/richData/richValueRel.xml") ? parseXML(await zip.file("xl/richData/richValueRel.xml").async("string")) : null;
      const relList = relDoc ? byLocal(relDoc, "rel").map((r) => attr(r, "id")) : [];
      const relTargets = await rels(zip, "xl/richData/richValueRel.xml");
      for (const c of vmCells) {
        try {
          const vm = +c.getAttribute("vm"); // 1-based
          const rc = byLocal(valueBk[vm - 1], "rc")[0];
          const fIndex = +rc.getAttribute("v"); // 0-based into futureMetadata
          const rvb = byLocal(futureBk[fIndex], "rvb")[0];
          const rvIndex = +rvb.getAttribute("i");
          const relIndex = +byLocal(rv[rvIndex], "v")[0].textContent; // _rvRel:LocalImageIdentifier comes first
          const m = await media(relTargets[relList[relIndex]]);
          const ref = cellRef(c.getAttribute("r"));
          if (m && ref) out.push({ row: ref.row, ...m });
        } catch { /* one odd cell is skipped */ }
      }
    }

    // 3. WPS Office: =DISPIMG("ID_...",1), pictures in xl/cellimages.xml.
    if (zip.file("xl/cellimages.xml")) {
      const cdoc = parseXML(await zip.file("xl/cellimages.xml").async("string"));
      const crels = await rels(zip, "xl/cellimages.xml");
      const byName = {};
      for (const pic of byLocal(cdoc, "pic")) {
        const name = byLocal(pic, "cNvPr")[0]?.getAttribute("name");
        const blip = byLocal(pic, "blip")[0];
        if (name && blip) byName[name] = crels[attr(blip, "embed")];
      }
      for (const c of byLocal(sheetXML, "c")) {
        const f = byLocal(c, "f")[0]?.textContent || "";
        const m = /DISPIMG\(\s*"([^"]+)"/i.exec(f); if (!m) continue;
        const img = await media(byName[m[1]]); const ref = cellRef(c.getAttribute("r"));
        if (img && ref) out.push({ row: ref.row, ...img });
      }
    }
    return out.filter((p) => ["png", "jpg", "jpeg", "gif", "webp", "bmp"].includes(p.ext));
  }

  async function sheetPathFor(zip, wanted) {
    const wbDoc = parseXML(await zip.file("xl/workbook.xml").async("string"));
    const wbRels = await rels(zip, "xl/workbook.xml");
    const sheets = byLocal(wbDoc, "sheet").map((s) => ({ name: s.getAttribute("name"), path: wbRels[attr(s, "id")] }));
    return (sheets.find((s) => s.name === wanted) || sheets[0]).path;
  }

  function toJPEG(bytes, ext) {
    return new Promise((ok, bad) => {
      const url = URL.createObjectURL(new Blob([bytes], { type: `image/${ext === "jpg" ? "jpeg" : ext}` }));
      const img = new Image();
      img.onload = () => {
        const s = Math.min(1, 1600 / Math.max(img.width, img.height));
        const c = document.createElement("canvas");
        c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
        const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height);
        g.drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url); ok(c.toDataURL("image/jpeg", 0.82));
      };
      img.onerror = () => { URL.revokeObjectURL(url); bad(new Error("bad image")); };
      img.src = url;
    });
  }

  // Every cell's text, read straight from the XML (ExcelJS crashed on some
  // files with floating pictures). Returns Map(row -> Map(col -> text)).
  async function cells(zip, sheetXML) {
    const shared = [];
    if (zip.file("xl/sharedStrings.xml")) {
      const sdoc = parseXML(await zip.file("xl/sharedStrings.xml").async("string"));
      for (const si of byLocal(sdoc, "si")) shared.push(byLocal(si, "t").map((t) => t.textContent).join(""));
    }
    const out = new Map();
    for (const c of byLocal(sheetXML, "c")) {
      const ref = cellRef(c.getAttribute("r")); if (!ref) continue;
      const t = c.getAttribute("t");
      const v = byLocal(c, "v")[0]?.textContent ?? "";
      let text = "";
      if (t === "s") text = shared[+v] ?? "";
      else if (t === "inlineStr") text = byLocal(c, "t").map((x) => x.textContent).join("");
      else if (t === "e") text = "";
      else if (t === "b") text = v === "1" ? "Yes" : v === "0" ? "No" : "";
      else text = /^-?\d+\.\d{6,}$/.test(v) ? String(+parseFloat(v).toPrecision(12)) : v; // 9.800000000000001 -> 9.8
      if (/^=?DISPIMG\(/i.test(text)) text = ""; // a WPS picture, not a value
      if (!out.has(ref.row)) out.set(ref.row, new Map());
      out.get(ref.row).set(ref.col, text.trim());
    }
    return out;
  }

  // Returns [{fields, category, photos[]}] in sheet order.
  async function read(file, form) {
    await load(LIBS[0]);
    const data = await file.arrayBuffer();
    const zip = await JSZip.loadAsync(data);
    const sheetPath = await sheetPathFor(zip, "Items");
    const sheetXML = parseXML(await zip.file(sheetPath).async("string"));
    const grid = await cells(zip, sheetXML);

    const fields = sheetFields(form);
    const known = new Set(fields.map((f) => f.key));
    const norm = (t) => t.toLowerCase().replace(/\s*\*$/, "").trim();
    const labelToKey = Object.fromEntries(fields.map((f) => [norm(f.label), f.key]));

    // Header: our hidden keys row, else a row of labels. The best match wins.
    let headerRow = 1, colKey = {};
    for (let r = 1; r <= 5; r++) {
      const map = {};
      for (const [c, t] of grid.get(r) ?? []) {
        const k = known.has(t) ? t : labelToKey[norm(t)];
        if (k) map[c] = k;
      }
      if (Object.keys(map).length > Object.keys(colKey).length) { colKey = map; headerRow = r; }
    }
    let firstData = headerRow + 1;
    const firstCol = +Object.keys(colKey)[0] || 1;
    if (labelToKey[norm(grid.get(firstData)?.get(firstCol) ?? "")]) firstData++; // the labels row under the keys row

    const byRow = new Map();
    const lastRow = Math.max(0, ...grid.keys());
    for (let r = firstData; r <= lastRow; r++) {
      const fields = {}; let any = false;
      for (const [c, k] of Object.entries(colKey)) {
        const t = grid.get(r)?.get(+c) ?? "";
        if (t) { fields[k] = t; any = true; }
      }
      if (!any) continue;
      // The price columns become the item's price by quantity.
      const breaks = Object.keys(fields).filter((k) => k.startsWith("pb:")).flatMap((k) => {
        const v = fields[k]; delete fields[k];
        return k === "pb:text" ? pairs(v) : [{ qty: k.slice(3), price: v }];
      });
      const qtys = (form.fields.find((f) => f.kind === "ladder")?.qtys || []).map(String);
      for (const q of qtys) if (!breaks.some((b) => b.qty === q)) breaks.push({ qty: q, price: "" });
      breaks.sort((a, b) => qtys.indexOf(a.qty) - qtys.indexOf(b.qty));
      const ladder = form.fields.some((f) => f.kind === "ladder");
      byRow.set(r, { fields, category: fields.category || "", photos: [], ...(ladder && (qtys.length || breaks.length) ? { breaks } : {}) });
    }

    for (const p of await pictures(zip, sheetPath, sheetXML)) {
      const item = byRow.get(p.row); if (!item || item.photos.length >= 6) continue;
      try { item.photos.push(await toJPEG(p.bytes, p.ext)); } catch { /* skip */ }
    }
    return [...byRow.values()];
  }

  window.QuoteSheet = { download, read };
})();
