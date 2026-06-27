const pptxgen = require("./node_modules/pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
p.author = "Team Redrob";
p.title = "Redrob Candidate Ranker — Approach";

// Palette: Ocean / deep-tech
const NAVY = "0B1F3A", DEEP = "0E2A47", TEAL = "1C7293", SEA = "00A896",
      MINT = "44E0C4", ICE = "CFE3F2", WHITE = "FFFFFF", MUT = "8AA6BF",
      CARD = "12233D", DARKCARD = "0A1830", RED = "E8615D", GOLD = "F2C14E";
const SANS = "Calibri", SERIF = "Cambria";
const W = 13.3, H = 7.5;

function dark(s){ s.background = { color: NAVY }; }
function light(s){ s.background = { color: "F4F8FB" }; }

function kicker(s, t, color){
  s.addText(t.toUpperCase(), { x:0.7, y:0.55, w:11.9, h:0.3, fontFace:SANS,
    fontSize:13, bold:true, color: color||SEA, charSpacing:3, margin:0 });
}
function title(s, t, color){
  s.addText(t, { x:0.7, y:0.9, w:11.9, h:0.95, fontFace:SERIF, fontSize:34,
    bold:true, color: color||WHITE, margin:0 });
}
function card(s, x,y,w,h, fill){
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x,y,w,h, rectRadius:0.08,
    fill:{color: fill||CARD}, line:{type:"none"},
    shadow:{type:"outer", color:"000000", blur:8, offset:3, angle:90, opacity:0.18} });
}
function dot(s, x, y, color){
  s.addShape(p.shapes.OVAL, { x, y, w:0.34, h:0.34, fill:{color:color}, line:{type:"none"} });
}

// ---------------------------------------------------------------- 1. TITLE
let s = p.addSlide(); dark(s);
s.addShape(p.shapes.OVAL, { x:9.6, y:-2.2, w:6.5, h:6.5, fill:{color:DEEP}, line:{type:"none"} });
s.addShape(p.shapes.OVAL, { x:11.3, y:3.8, w:4.2, h:4.2, fill:{color:"10314F"}, line:{type:"none"} });
s.addText("REDROB · DATA & AI CHALLENGE", { x:0.8, y:1.6, w:10, h:0.4, fontFace:SANS,
  fontSize:15, bold:true, color:MINT, charSpacing:3, margin:0 });
s.addText("Ranking candidates the way a\ngreat recruiter would", { x:0.8, y:2.2, w:11, h:2.0,
  fontFace:SERIF, fontSize:46, bold:true, color:WHITE, margin:0, lineSpacingMultiple:1.0 });
s.addText("A hybrid, fully-offline candidate ranker for the Senior AI Engineer role — built to read profiles, not keywords.",
  { x:0.8, y:4.5, w:10.8, h:0.8, fontFace:SANS, fontSize:18, color:ICE, margin:0 });
s.addText([
  {text:"100,000", options:{bold:true, color:MINT}},
  {text:"  candidate pool      ", options:{color:MUT}},
  {text:"Top 100", options:{bold:true, color:MINT}},
  {text:"  shortlist      ", options:{color:MUT}},
  {text:"~1 min", options:{bold:true, color:MINT}},
  {text:"  CPU · no network", options:{color:MUT}},
], { x:0.8, y:5.7, w:11.5, h:0.5, fontFace:SANS, fontSize:15, margin:0 });

// ---------------------------------------------------------------- 2. PROBLEM
s = p.addSlide(); light(s);
kicker(s, "The problem", TEAL); title(s, "Keyword filters can't see what matters", NAVY);
const traps = [
  ["Keyword-stuffers", "A “Marketing Manager” whose skills list is packed with RAG, Pinecone, embeddings. Perfect on keywords — wrong person.", RED],
  ["Plain-language strengths", "Built a recommendation system at a product company, but never wrote “vector DB.” Easy to miss, genuinely strong.", SEA],
  ["~80 honeypots", "Subtly impossible profiles: 8 years at a 3-year-old company; “expert” in 10 skills with 0 months used. Forced to tier 0.", GOLD],
  ["Behavioral twins", "Identical on paper — separated only by who actually responds to recruiters and is still active.", TEAL],
];
let x=0.7, y=2.1, cw=5.95, ch=2.2, gx=0.4, gy=0.35;
traps.forEach((t,i)=>{
  const cx = x + (i%2)*(cw+gx), cy = y + Math.floor(i/2)*(ch+gy);
  card(s, cx, cy, cw, ch, WHITE);
  dot(s, cx+0.4, cy+0.4, t[2]);
  s.addText(t[0], { x:cx+0.95, y:cy+0.34, w:cw-1.3, h:0.5, fontFace:SANS, fontSize:19, bold:true, color:NAVY, margin:0 });
  s.addText(t[1], { x:cx+0.45, y:cy+1.0, w:cw-0.9, h:1.0, fontFace:SANS, fontSize:14.5, color:"31506B", margin:0 });
});
s.addText("A pure embedding or keyword system falls for all four. The JD even says so explicitly.",
  { x:0.7, y:6.95, w:11.9, h:0.4, fontFace:SANS, fontSize:14, italic:true, color:TEAL, margin:0 });

// ---------------------------------------------------------------- 3. APPROACH / ARCH
s = p.addSlide(); dark(s);
kicker(s, "The approach", MINT); title(s, "An explainable hybrid, not a black box", WHITE);
// pipeline as 3 stages of cards + modifiers
function pcard(x,y,w,h,head,body,acc){
  card(s,x,y,w,h,CARD);
  s.addText(head, { x:x+0.35, y:y+0.28, w:w-0.6, h:0.5, fontFace:SANS, fontSize:16.5, bold:true, color:acc||MINT, margin:0 });
  s.addText(body, { x:x+0.35, y:y+0.85, w:w-0.6, h:h-1.0, fontFace:SANS, fontSize:13.5, color:ICE, margin:0, lineSpacingMultiple:1.02 });
}
pcard(0.7,2.05,3.95,2.35,"1 · Structured scoring",
  "Seven explainable features per candidate: title fit, trust-weighted skills, career evidence, semantic match, experience band, domain, location.", MINT);
pcard(4.85,2.05,3.95,2.35,"2 · Modifiers",
  "Two multipliers on the merit score: explicit JD disqualifiers (red flags) and behavioral availability (response rate, recency, open-to-work).", SEA);
pcard(9.0,2.05,3.6,2.35,"3 · Honeypot guard",
  "Internal-consistency checks collapse impossible profiles beneath every genuine candidate — no ID special-casing.", GOLD);
// flow line
s.addText("→", { x:4.55, y:2.9, w:0.4, h:0.5, fontSize:26, bold:true, color:MUT, align:"center", margin:0 });
s.addText("→", { x:8.7, y:2.9, w:0.4, h:0.5, fontSize:26, bold:true, color:MUT, align:"center", margin:0 });
card(s, 0.7, 4.75, 11.9, 1.95, DARKCARD);
s.addText("Final score  =  weighted merit  ×  red-flag penalty  ×  behavioral modifier", 
  { x:1.0, y:5.0, w:11.3, h:0.5, fontFace:SERIF, fontSize:21, bold:true, color:WHITE, margin:0 });
s.addText([
  {text:"Title fit + skill-trust ", options:{bold:true, color:MINT}},
  {text:"defeat keyword-stuffers.   ", options:{color:ICE}},
  {text:"Career-description text ", options:{bold:true, color:SEA}},
  {text:"surfaces plain-language strengths.   ", options:{color:ICE}},
  {text:"Behavioral signals ", options:{bold:true, color:GOLD}},
  {text:"encode who's actually hireable.", options:{color:ICE}},
], { x:1.0, y:5.7, w:11.3, h:0.9, fontFace:SANS, fontSize:14.5, margin:0, lineSpacingMultiple:1.1 });

// ---------------------------------------------------------------- 4. COMPONENTS TABLE
s = p.addSlide(); light(s);
kicker(s, "Scoring components", TEAL); title(s, "What each signal captures", NAVY);
const rows = [
  ["title_fit", "0.24", "Is the title actually an ML/AI/SW engineer?", "Decisive vs keyword-stuffers"],
  ["skills_fit", "0.18", "Skills × trust (endorsements + duration + assessment)", "Kills “expert, 0 months used”"],
  ["career_evidence", "0.18", "Product-company + shipped ranking / search / recsys", "Finds real builders"],
  ["semantic", "0.16", "TF-IDF cosine: profile ↔ JD-derived query", "Plain-language strengths"],
  ["experience_fit", "0.12", "Alignment with the 5–9y band (ideal 6–8)", "JD’s soft band"],
  ["domain_fit", "0.07", "NLP / IR vs CV / speech / robotics", "JD-named negative"],
  ["location_fit", "0.05", "Indian metros / willing to relocate", "No visa sponsorship"],
];
let ty=2.05, rh=0.62;
// header
s.addText([
  {text:"COMPONENT", options:{}},
], { x:0.7, y:ty, w:2.6, h:0.4, fontFace:SANS, fontSize:12, bold:true, color:TEAL, charSpacing:1, margin:0 });
s.addText("WEIGHT", { x:3.35, y:ty, w:1.0, h:0.4, fontFace:SANS, fontSize:12, bold:true, color:TEAL, charSpacing:1, margin:0 });
s.addText("WHAT IT CAPTURES", { x:4.5, y:ty, w:5.0, h:0.4, fontFace:SANS, fontSize:12, bold:true, color:TEAL, charSpacing:1, margin:0 });
s.addText("WHY IT MATTERS", { x:9.7, y:ty, w:2.9, h:0.4, fontFace:SANS, fontSize:12, bold:true, color:TEAL, charSpacing:1, margin:0 });
rows.forEach((r,i)=>{
  const cy = ty+0.5 + i*rh;
  if(i%2===0) s.addShape(p.shapes.RECTANGLE, {x:0.6,y:cy-0.06,w:12.1,h:rh-0.05, fill:{color:"E9F1F8"}, line:{type:"none"}});
  s.addText(r[0], { x:0.7, y:cy, w:2.6, h:0.45, fontFace:"Courier New", fontSize:13.5, bold:true, color:NAVY, margin:0, valign:"middle" });
  s.addText(r[1], { x:3.35, y:cy, w:1.0, h:0.45, fontFace:SANS, fontSize:14, bold:true, color:SEA, margin:0, valign:"middle" });
  s.addText(r[2], { x:4.5, y:cy, w:5.1, h:0.45, fontFace:SANS, fontSize:13, color:"32475C", margin:0, valign:"middle" });
  s.addText(r[3], { x:9.7, y:cy, w:2.9, h:0.45, fontFace:SANS, fontSize:13, italic:true, color:TEAL, margin:0, valign:"middle" });
});
s.addText("Weights live in config.yaml · the structured JD reading lives in role_spec.yaml",
  { x:0.7, y:6.95, w:11.9, h:0.4, fontFace:SANS, fontSize:13, italic:true, color:MUT, margin:0 });

// ---------------------------------------------------------------- 5. HONEYPOTS
s = p.addSlide(); dark(s);
kicker(s, "Defeating the traps", GOLD); title(s, "Reading profiles, not embeddings", WHITE);
card(s, 0.7, 2.05, 5.95, 4.55, CARD);
s.addText("Honeypot detection — internal consistency", { x:1.05, y:2.3, w:5.3, h:0.5, fontFace:SANS, fontSize:17, bold:true, color:GOLD, margin:0 });
s.addText([
  {text:"Duration vs date span — ", options:{bold:true,color:WHITE,breakLine:true}},
  {text:"a role can’t last 96 months across a 36-month window.", options:{color:ICE,breakLine:true}},
  {text:"Tenure vs experience — ", options:{bold:true,color:WHITE,breakLine:true}},
  {text:"can’t have worked more years than you’ve existed professionally.", options:{color:ICE,breakLine:true}},
  {text:"Proficiency vs usage — ", options:{bold:true,color:WHITE,breakLine:true}},
  {text:"“expert” in many skills with 0 months used is impossible.", options:{color:ICE,breakLine:true}},
  {text:"Skill vs career length — ", options:{bold:true,color:WHITE,breakLine:true}},
  {text:"a skill used longer than the whole career.", options:{color:ICE}},
], { x:1.05, y:2.95, w:5.3, h:3.4, fontFace:SANS, fontSize:14, margin:0, lineSpacingMultiple:1.05 });
card(s, 6.95, 2.05, 5.65, 4.55, DARKCARD);
s.addText("The keyword-stuffer test", { x:7.3, y:2.3, w:5.0, h:0.5, fontFace:SANS, fontSize:17, bold:true, color:MINT, margin:0 });
s.addText([
  {text:"“Marketing Manager” + 9 AI skills", options:{bold:true, color:WHITE, breakLine:true}},
  {text:"the bad baseline ranks this #1.", options:{italic:true, color:RED, breakLine:true}},
], { x:7.3, y:2.95, w:5.0, h:0.8, fontFace:SANS, fontSize:14.5, margin:0 });
s.addText([
  {text:"Our title_fit scores it ~0.05.  ", options:{color:ICE}},
  {text:"The skill-trust multiplier strips “expert” skills with no endorsements or usage. It lands near the bottom — where a recruiter would put it.", options:{color:ICE}},
], { x:7.3, y:3.95, w:5.0, h:1.6, fontFace:SANS, fontSize:14, margin:0, lineSpacingMultiple:1.05 });
s.addText("We never special-case IDs — detection generalizes and is defensible at interview.",
  { x:7.3, y:5.85, w:5.0, h:0.6, fontFace:SANS, fontSize:13, italic:true, color:GOLD, margin:0 });

// ---------------------------------------------------------------- 6. RESULTS (stats)
s = p.addSlide(); light(s);
kicker(s, "Results on the full pool", TEAL); title(s, "100,000 candidates → a shortlist you can trust", NAVY);
const stats = [
  ["0", "honeypots in the top 100", SEA],
  ["0", "keyword-stuffer roles in top 100", TEAL],
  ["92/100", "inside the 5–9y band (mean 6.6y)", NAVY],
  ["~1 min", "runtime · CPU · no network", GOLD],
];
stats.forEach((st,i)=>{
  const cx = 0.7 + i*3.05, cw2=2.85;
  card(s, cx, 2.2, cw2, 1.95, WHITE);
  s.addText(st[0], { x:cx+0.1, y:2.4, w:cw2-0.2, h:0.9, fontFace:SERIF, fontSize:40, bold:true, color:st[2], align:"center", margin:0 });
  s.addText(st[1], { x:cx+0.2, y:3.35, w:cw2-0.4, h:0.7, fontFace:SANS, fontSize:13, color:"32475C", align:"center", margin:0 });
});
card(s, 0.7, 4.5, 11.9, 2.1, WHITE);
s.addText("Top-100 title mix", { x:1.0, y:4.7, w:11, h:0.4, fontFace:SANS, fontSize:15, bold:true, color:NAVY, margin:0 });
const mix = [["AI Engineer",14],["ML Engineer",12],["Applied ML",10],["Recsys Eng.",8],["Senior DS",7],["Search Eng.",7],["NLP Eng.",6],["Applied Sci.",4]];
const maxv = 14;
mix.forEach((m,i)=>{
  const bx = 1.0 + i*1.46;
  const bh = 0.9 * (m[1]/maxv);
  s.addShape(p.shapes.RECTANGLE, { x:bx, y:5.55-bh, w:0.95, h:bh, fill:{color: TEAL}, line:{type:"none"} });
  s.addText(String(m[1]), { x:bx-0.05, y:5.55-bh-0.32, w:1.05, h:0.3, fontFace:SANS, fontSize:12, bold:true, color:NAVY, align:"center", margin:0 });
  s.addText(m[0], { x:bx-0.1, y:5.62, w:1.15, h:0.7, fontFace:SANS, fontSize:10.5, color:"32475C", align:"center", margin:0 });
});

// ---------------------------------------------------------------- 7. REASONING
s = p.addSlide(); dark(s);
kicker(s, "Every rank is explained", MINT); title(s, "Reasoning a human can audit", WHITE);
const ex = [
  ["#1", SEA, "Lead AI Engineer with 6.7 yrs; strong role and skills alignment; relevant skills: Information Retrieval, Learning to Rank, Elasticsearch; responsive to recruiters (73%)."],
  ["#10", GOLD, "Current role is Project Manager (14.5 yrs); core engineering-title fit is weak despite listed skills; not active in 218d."],
  ["bottom", RED, "Flagged as likely honeypot (role duration exceeds its date span — impossible tenure); ranked at the bottom despite surface keyword matches."],
];
let ey=2.1;
ex.forEach((e,i)=>{
  card(s, 0.7, ey, 11.9, 1.35, i===2?DARKCARD:CARD);
  s.addText(e[0], { x:1.0, y:ey+0.22, w:1.5, h:0.9, fontFace:SERIF, fontSize:24, bold:true, color:e[1], align:"center", valign:"middle", margin:0 });
  s.addText(e[2], { x:2.6, y:ey+0.2, w:9.8, h:0.95, fontFace:SANS, fontSize:14.5, color:ICE, valign:"middle", margin:0, lineSpacingMultiple:1.03 });
  ey += 1.55;
});
s.addText("Grounded only in facts in the profile · names honest concerns · tone tracks the rank — built for Stage-4 manual review.",
  { x:0.7, y:6.95, w:11.9, h:0.4, fontFace:SANS, fontSize:13.5, italic:true, color:MINT, margin:0 });

// ---------------------------------------------------------------- 8. COMPUTE / COMPLIANCE
s = p.addSlide(); light(s);
kicker(s, "Built for production constraints", TEAL); title(s, "Reproducible, offline, within budget", NAVY);
const comp = [
  ["CPU only","No GPU anywhere in the ranking path.", SEA],
  ["No network","Zero hosted-LLM / API calls during ranking.", TEAL],
  ["< 5 min · < 16 GB","~1 min for 100k on a laptop CPU.", NAVY],
  ["One command","python rank.py --candidates … --out …", GOLD],
];
comp.forEach((c,i)=>{
  const cx=0.7+(i%2)*6.05, cy=2.1+Math.floor(i/2)*1.75, cw2=5.7;
  card(s, cx, cy, cw2, 1.5, WHITE);
  dot(s, cx+0.4, cy+0.45, c[2]);
  s.addText(c[0], { x:cx+0.95, y:cy+0.32, w:cw2-1.2, h:0.45, fontFace:SANS, fontSize:18, bold:true, color:NAVY, margin:0 });
  s.addText(c[1], { x:cx+0.95, y:cy+0.82, w:cw2-1.2, h:0.5, fontFace:i===3?"Courier New":SANS, fontSize:i===3?12.5:14, color:"32475C", margin:0 });
});
s.addText("Default semantic backend is TF-IDF — deterministic, no model download. An optional dense-embedding precompute is available; ranking stays offline either way.",
  { x:0.7, y:5.85, w:11.9, h:0.8, fontFace:SANS, fontSize:14, italic:true, color:TEAL, margin:0, lineSpacingMultiple:1.05 });

// ---------------------------------------------------------------- 9. CLOSING
s = p.addSlide(); dark(s);
s.addShape(p.shapes.OVAL, { x:-2.2, y:3.6, w:6.5, h:6.5, fill:{color:DEEP}, line:{type:"none"} });
s.addText("WHAT WE BUILT", { x:0.8, y:1.7, w:10, h:0.4, fontFace:SANS, fontSize:14, bold:true, color:MINT, charSpacing:3, margin:0 });
s.addText("A ranker that reasons about fit", { x:0.8, y:2.25, w:11.5, h:1.0, fontFace:SERIF, fontSize:40, bold:true, color:WHITE, margin:0 });
s.addText([
  {text:"Explainable hybrid scoring", options:{bold:true,color:MINT,breakLine:true}},
  {text:"— title, skill-trust, career evidence, semantic, behavioral, honeypot guard.", options:{color:ICE,breakLine:true}},
  {text:"\n", options:{breakLine:true}},
  {text:"Defeats the dataset’s traps", options:{bold:true,color:SEA,breakLine:true}},
  {text:"— keyword-stuffers down, plain-language strengths up, honeypots out.", options:{color:ICE,breakLine:true}},
  {text:"\n", options:{breakLine:true}},
  {text:"Production-ready", options:{bold:true,color:GOLD,breakLine:true}},
  {text:"— offline, CPU, one command, ~1 min for 100k candidates.", options:{color:ICE}},
], { x:0.8, y:3.5, w:11.4, h:2.6, fontFace:SANS, fontSize:17, margin:0, lineSpacingMultiple:1.1 });
s.addText("Make hiring smarter.", { x:0.8, y:6.5, w:10, h:0.5, fontFace:SERIF, fontSize:20, italic:true, bold:true, color:MINT, margin:0 });

p.writeFile({ fileName: "approach_deck.pptx" }).then(()=>console.log("DECK WRITTEN"));
