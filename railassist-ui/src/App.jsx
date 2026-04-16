import { useState, useRef, useEffect } from "react";

const C = {
  blue: "#003B8E", blueDark: "#00275E", blueLight: "#EDF2F9",
  gold: "#C9991A", white: "#FFFFFF", bg: "#F7F8FA",
  text: "#1A1D26", textMid: "#4B5060", textLight: "#8B919F",
  border: "#E4E7EC", green: "#15803D", amber: "#B45309",
  red: "#B91C1C", purple: "#6D28D9", cyan: "#0891B2",
};

const AGENTS = {
  railassist: { name: "RailAssist", color: C.blue },
  schedule: { name: "ScheduleAgent", color: C.cyan },
  passenger: { name: "PassengerAgent", color: C.gold },
  incident: { name: "IncidentAgent", color: C.amber },
  knowledge: { name: "KnowledgeAgent", color: C.purple },
  fabric: { name: "FabricAgent", color: C.green },
};

const DEMOS = [
  {
    q: "Next departures from Brussels-Midi?",
    steps: [
      { t: "route", from: "railassist", to: "schedule", msg: "Timetable query detected" },
      { t: "tool", agent: "schedule", tool: "code_interpreter", msg: "generate_departures('Bruxelles-Midi')" },
      { t: "ok", tool: "code_interpreter", msg: "8 departures generated" },
    ],
    agent: "schedule",
    text: "Here are the next departures from Brussels-Midi:\n\nIC 1523 → Li\u00e8ge-Guillemins \u00b7 14:22 \u00b7 Pl. 3 \u00b7 On time\nS1 4087 → Antwerp-Central \u00b7 14:28 \u00b7 Pl. 7 \u00b7 +5 min\nIC 2841 → Namur \u00b7 14:35 \u00b7 Pl. 12 \u00b7 On time\nThalys 9284 → Amsterdam \u00b7 14:52 \u00b7 Pl. 4 \u00b7 On time\nICE 18 → Cologne \u00b7 15:01 \u00b7 Pl. 2 \u00b7 +3 min\nL 910 → Ottignies \u00b7 15:08 \u00b7 Pl. 1 \u00b7 On time\nS2 5190 → Leuven \u00b7 15:15 \u00b7 Pl. 9 \u00b7 On time\nIC 3052 → Bruges \u00b7 15:22 \u00b7 Pl. 11 \u00b7 On time",
  },
  {
    q: "What are the rules for bikes on trains?",
    steps: [
      { t: "route", from: "railassist", to: "knowledge", msg: "Policy query detected" },
      { t: "tool", agent: "knowledge", tool: "azure_ai_search", msg: 'query: "bikes trains rules"' },
      { t: "ok", tool: "azure_ai_search", msg: "Found: Conditions g\u00e9n\u00e9rales de transport (score: 0.89)" },
    ],
    agent: "knowledge",
    text: "According to the SNCB General Transport Conditions:\n\n- Bikes are allowed on trains with a supplement of \u20ac4\n- A valid transport ticket is required in addition\n- Peak hours (7\u20139h, 17\u201319h): access may be restricted\n- Folding bikes travel free when stored in a bag\n- Bike spaces are located in designated areas of each train\n\nSource: Conditions g\u00e9n\u00e9rales de transport SNCB",
  },
  {
    q: "Any disruptions right now?",
    steps: [
      { t: "route", from: "railassist", to: "incident", msg: "Disruption query detected" },
      { t: "tool", agent: "incident", tool: "code_interpreter", msg: "get_active_disruptions()" },
      { t: "ok", tool: "code_interpreter", msg: "2 active incidents found" },
    ],
    agent: "incident",
    text: "Current disruptions:\n\nCRITICAL \u2014 L25 Brussels\u2013Li\u00e8ge\nSignal failure near Leuven since 11:30\nResolution expected: 16:00\nReplacement buses operating Leuven \u2194 Li\u00e8ge\n23 trains affected\n\nMEDIUM \u2014 L130 Namur\u2013Charleroi\nTrack maintenance at Jemeppe\nSingle track operation, delays 10\u201315 min\nReduced frequency maintained",
  },
  {
    q: "My train IC1832 was 45 min late, compensation?",
    steps: [
      { t: "route", from: "railassist", to: "passenger", msg: "Compensation query detected" },
      { t: "tool", agent: "passenger", tool: "code_interpreter", msg: "calculate_compensation(delay=45)" },
      { t: "ok", tool: "code_interpreter", msg: "50% refund \u2014 EC 1371/2007 bracket 30\u201359 min" },
    ],
    agent: "passenger",
    text: "Compensation for IC1832 (45 min delay):\n\nRegulation: EU EC 1371/2007\nDelay bracket: 30\u201359 min → 50% refund\nYou are entitled to 50% of your ticket price\nClaim reference: CLM-20260415-4827\nProcessing: 5\u201310 business days\n\nSubmit at belgiantrain.be or any Customer Service desk.",
  },
  {
    q: "Punctuality rate by line?",
    steps: [
      { t: "route", from: "railassist", to: "fabric", msg: "Analytics query detected" },
      { t: "tool", agent: "fabric", tool: "fabric_lakehouse", msg: "SELECT line, punctuality FROM rail_operations" },
      { t: "ok", tool: "fabric_lakehouse", msg: "6 rows returned from lakehouse" },
    ],
    agent: "fabric",
    text: "Punctuality by line (operational data):\n\nL96 Brussels\u2013Namur: 66.7%\nL1 Brussels\u2013Antwerp: 55.6%\nL25 Brussels\u2013Li\u00e8ge: 50.0%\nL51 Brussels\u2013Bruges: 50.0%\nL50A Brussels\u2013Ghent: 33.3%\nL130 Namur\u2013Charleroi: 33.3%\n\nTop delay causes: mechanical issues, weather, signal failures\n\nSource: Microsoft Fabric \u2014 rail_operations lakehouse",
  },
  {
    q: "Train delayed \u2014 alternatives from Namur + compensation?",
    steps: [
      { t: "route", from: "railassist", to: "incident", msg: "Multi-domain → checking disruptions" },
      { t: "tool", agent: "incident", tool: "code_interpreter", msg: "check_disruptions('Namur')" },
      { t: "ok", tool: "code_interpreter", msg: "1 disruption on L96" },
      { t: "route", from: "railassist", to: "schedule", msg: "Finding alternative connections" },
      { t: "tool", agent: "schedule", tool: "code_interpreter", msg: "search_alternatives('Namur')" },
      { t: "ok", tool: "code_interpreter", msg: "2 routes found" },
      { t: "route", from: "railassist", to: "passenger", msg: "Processing compensation" },
      { t: "tool", agent: "passenger", tool: "code_interpreter", msg: "calculate_compensation(delay=40)" },
      { t: "ok", tool: "code_interpreter", msg: "50% refund eligible" },
    ],
    agent: "railassist",
    text: "I coordinated with three specialist agents:\n\nDISRUPTION\nL96 Brussels\u2013Namur: signal issue near Gembloux\n\nALTERNATIVES FROM NAMUR\n1. IC via Charleroi → Brussels \u00b7 Dep 15:10 \u00b7 +20 min detour\n2. L-train Namur → Ottignies → Brussels \u00b7 Dep 15:25\n\nCOMPENSATION\n40 min delay → 50% refund (EC 1371/2007)\nClaim ref: CLM-20260415-5031\n\nWould you like help with anything else?",
  },
];

const QUICK_LABELS = ["Departures", "Bike rules", "Disruptions", "Compensation", "Analytics", "Multi-agent"];

function PipelineStep({ step, show }) {
  const isRoute = step.t === "route";
  const isOk = step.t === "ok";
  const color = isRoute ? C.blue : isOk ? C.green : C.amber;
  const label = isRoute ? "ROUTE" : isOk ? "DONE" : "TOOL";

  return (
    <div style={{
      opacity: show ? 1 : 0, transform: show ? "translateX(0)" : "translateX(12px)",
      transition: "all 0.35s ease", padding: "5px 0",
      display: "flex", alignItems: "flex-start", gap: 8,
    }}>
      <div style={{
        width: 44, fontSize: 9, fontWeight: 700, color, flexShrink: 0,
        fontFamily: "'JetBrains Mono', monospace", paddingTop: 2,
      }}>{label}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {isRoute && (
          <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, color: C.textLight }}>{AGENTS[step.from]?.name}</span>
            <span style={{ fontSize: 11, color: C.textLight }}>→</span>
            <span style={{
              fontSize: 11, fontWeight: 600, color: AGENTS[step.to]?.color,
              background: `${AGENTS[step.to]?.color}10`, padding: "1px 6px", borderRadius: 3,
            }}>{AGENTS[step.to]?.name}</span>
          </div>
        )}
        {!isRoute && step.tool && (
          <span style={{
            fontSize: 10, fontFamily: "'JetBrains Mono', monospace",
            color: isOk ? C.green : C.textMid,
            background: isOk ? "#F0FDF4" : `${C.border}60`, padding: "1px 6px", borderRadius: 3,
          }}>
            {isOk ? "✓" : "⚡"} {step.tool}
          </span>
        )}
        <div style={{
          fontSize: 10, color: C.textLight, marginTop: 2,
          fontFamily: isRoute ? "inherit" : "'JetBrains Mono', monospace",
          fontStyle: isRoute ? "italic" : "normal",
        }}>
          {step.msg}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPipeline, setShowPipeline] = useState(true);
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [demoIdx, setDemoIdx] = useState(0);
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  const run = async (text) => {
    if (busy) return;
    setBusy(true);
    setPipelineSteps([]);
    setVisibleSteps(0);
    setMessages(prev => [...prev, { role: "user", text }]);
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: "demo" }),
      });
      const data = await res.json();
      if (data.steps && data.steps.length > 0) {
        setPipelineSteps(data.steps);
        for (let i = 0; i < data.steps.length; i++) {
          await new Promise(r => setTimeout(r, 300));
          setVisibleSteps(i + 1);
        }
      }
      let agentKey = "railassist";
      if (data.steps) {
        const lastRoute = [...data.steps].reverse().find(s => s.t === "route");
        if (lastRoute) {
          const nm = lastRoute.to.toLowerCase();
          if (nm.includes("schedule")) agentKey = "schedule";
          else if (nm.includes("passenger")) agentKey = "passenger";
          else if (nm.includes("incident")) agentKey = "incident";
          else if (nm.includes("knowledge")) agentKey = "knowledge";
        }
      }
      setMessages(prev => [...prev, { role: "assistant", text: data.response || "No response", agent: agentKey }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", text: "Connection error: " + err.message, agent: "railassist" }]);
    }
    setBusy(false);
  };

  const send = () => { const t = input.trim(); if (t) { setInput(""); run(t); } };

  return (
    <div style={{ height: "100vh", display: "flex", fontFamily: "'Source Sans 3', 'Segoe UI', sans-serif", background: C.bg }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
        * { margin:0; padding:0; box-sizing:border-box; }
        input:focus { outline: none; }
        ::-webkit-scrollbar { width:4px } ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:2px }
      `}</style>

      {/* Main chat */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

        <div style={{
          background: C.blue, height: 54, padding: "0 24px",
          display: "flex", alignItems: "center", gap: 12, flexShrink: 0,
        }}>
          <div style={{
            width: 34, height: 22, borderRadius: 11, border: "2px solid white",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 800, fontSize: 13, color: "white", fontFamily: "Georgia",
          }}>B</div>
          <span style={{ color: "white", fontSize: 17, fontWeight: 700 }}>RailAssist</span>
          <span style={{ color: "white", fontSize: 13, opacity: 0.55, fontWeight: 400 }}>NMBS / SNCB</span>
          <div style={{ marginLeft: "auto" }}>
            <button onClick={() => setShowPipeline(p => !p)} style={{
              background: showPipeline ? "rgba(255,255,255,0.18)" : "transparent",
              border: "1px solid rgba(255,255,255,0.25)", borderRadius: 6,
              color: "white", fontSize: 11, padding: "4px 10px", cursor: "pointer",
              fontFamily: "'JetBrains Mono', monospace", fontWeight: 500,
            }}>
              {showPipeline ? "Pipeline ON" : "Pipeline OFF"}
            </button>
          </div>
        </div>

        <div ref={chatRef} style={{
          flex: 1, overflowY: "auto", padding: "20px 24px",
          display: "flex", flexDirection: "column", gap: 14,
        }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "60px 20px", animation: "fadeUp 0.5s ease" }}>
              <h2 style={{ fontSize: 24, fontWeight: 700, color: C.blue, marginBottom: 8 }}>
                How can I help you today?
              </h2>
              <p style={{ color: C.textLight, fontSize: 14, maxWidth: 400, margin: "0 auto", lineHeight: 1.6 }}>
                Ask about train schedules, fares, disruptions, regulations, or compensation claims.
              </p>
            </div>
          )}

          {messages.map((msg, i) => {
            if (msg.role === "user") {
              return (
                <div key={i} style={{
                  alignSelf: "flex-end", maxWidth: "65%",
                  padding: "10px 16px", borderRadius: "16px 16px 4px 16px",
                  background: C.blue, color: "white", fontSize: 14, lineHeight: 1.5,
                  animation: "fadeUp 0.25s ease",
                }}>{msg.text}</div>
              );
            }
            const ag = AGENTS[msg.agent];
            return (
              <div key={i} style={{ alignSelf: "flex-start", maxWidth: "72%", animation: "fadeUp 0.3s ease" }}>
                {ag && (
                  <div style={{
                    display: "inline-flex", alignItems: "center", gap: 5,
                    marginBottom: 5, padding: "2px 8px", borderRadius: 5,
                    background: `${ag.color}0D`, fontSize: 11, fontWeight: 600, color: ag.color,
                  }}>
                    {ag.name}
                  </div>
                )}
                <div style={{
                  padding: "12px 16px", borderRadius: "4px 16px 16px 16px",
                  background: "white", border: `1px solid ${C.border}`,
                  fontSize: 14, lineHeight: 1.65, color: C.text,
                  whiteSpace: "pre-wrap", boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
                }}>{msg.text}</div>
              </div>
            );
          })}

          {busy && messages[messages.length - 1]?.role === "user" && (
            <div style={{
              alignSelf: "flex-start", padding: "12px 18px",
              background: "white", border: `1px solid ${C.border}`, borderRadius: 14,
              display: "flex", gap: 5,
            }}>
              {[0,1,2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: "50%", background: C.blue,
                  animation: `blink 1s ease ${i*0.15}s infinite`,
                }}/>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: "4px 24px 6px", display: "flex", gap: 6, flexWrap: "wrap", flexShrink: 0 }}>
          {DEMOS.map((d, i) => (
            <button key={i} disabled={busy}
              onClick={() => run(d.q)}
              style={{
                padding: "5px 12px", borderRadius: 20, fontSize: 12, fontWeight: 500,
                background: "white", border: `1px solid ${C.border}`, color: C.text,
                cursor: busy ? "not-allowed" : "pointer", opacity: busy ? 0.4 : 1,
                transition: "all 0.15s",
              }}
              onMouseEnter={e => { if(!busy){ e.target.style.borderColor=C.blue; e.target.style.color=C.blue; }}}
              onMouseLeave={e => { e.target.style.borderColor=C.border; e.target.style.color=C.text; }}
            >{QUICK_LABELS[i]}</button>
          ))}
        </div>

        <div style={{
          background: "white", borderTop: `1px solid ${C.border}`,
          padding: "10px 24px", display: "flex", gap: 10, flexShrink: 0,
        }}>
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Type your question..."
            disabled={busy}
            style={{
              flex: 1, padding: "10px 14px", borderRadius: 10,
              border: `1px solid ${C.border}`, fontSize: 14,
              fontFamily: "inherit", color: C.text, transition: "border 0.2s",
            }}
            onFocus={e => e.target.style.borderColor = C.blue}
            onBlur={e => e.target.style.borderColor = C.border}
          />
          <button onClick={send} disabled={busy || !input.trim()}
            style={{
              width: 42, height: 42, borderRadius: 10, border: "none",
              background: busy || !input.trim() ? C.border : C.blue,
              color: "white", fontSize: 18, cursor: busy ? "not-allowed" : "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>→</button>
        </div>
      </div>

      {/* Side pipeline */}
      {showPipeline && (
        <div style={{
          width: 320, borderLeft: `1px solid ${C.border}`, background: "white",
          display: "flex", flexDirection: "column", flexShrink: 0,
        }}>
          <div style={{
            height: 54, padding: "0 16px", background: "#FAFBFC",
            borderBottom: `1px solid ${C.border}`,
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Agent Pipeline</span>
            <div style={{
              marginLeft: "auto", fontSize: 9, fontWeight: 600,
              padding: "2px 7px", borderRadius: 4,
              background: busy ? "#FEF3C7" : pipelineSteps.length > 0 ? "#F0FDF4" : C.blueLight,
              color: busy ? C.amber : pipelineSteps.length > 0 ? C.green : C.blue,
              fontFamily: "'JetBrains Mono', monospace",
              animation: busy ? "blink 1s infinite" : "none",
            }}>
              {busy ? "PROCESSING" : pipelineSteps.length > 0 ? "COMPLETED" : "IDLE"}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px" }}>
            {pipelineSteps.length === 0 && !busy && (
              <div style={{ textAlign: "center", padding: "40px 10px", color: C.textLight, fontSize: 12 }}>
                Ask a question to see the<br/>agent orchestration pipeline
              </div>
            )}
            {pipelineSteps.map((step, i) => (
              <PipelineStep key={i} step={step} show={i < visibleSteps} />
            ))}
            {busy && visibleSteps >= pipelineSteps.length && pipelineSteps.length > 0 && (
              <div style={{
                marginTop: 8, padding: "6px 10px", borderRadius: 6,
                background: "#FEF3C7", fontSize: 11, color: C.amber,
                fontFamily: "'JetBrains Mono', monospace",
                animation: "blink 1.2s infinite",
              }}>
                Composing response...
              </div>
            )}
          </div>

          <div style={{
            borderTop: `1px solid ${C.border}`, padding: "10px 14px", background: "#FAFBFC",
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.textLight, marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5 }}>
              Connected Agents
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {Object.entries(AGENTS).map(([k, ag]) => (
                <span key={k} style={{
                  fontSize: 10, padding: "2px 7px", borderRadius: 4,
                  background: `${ag.color}0A`, color: ag.color,
                  border: `1px solid ${ag.color}18`,
                }}>{ag.name}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
