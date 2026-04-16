path = r'C:\Users\t-bmathieu\railassist-demo\railassist-ui\src\App.jsx'
content = open(path, 'r', encoding='utf-8').read()

old = '''  const run = async (text) => {
    if (busy) return;
    setBusy(true);
    setPipelineSteps([]);
    setVisibleSteps(0);

    setMessages(prev => [...prev, { role: "user", text }]);

    const demo = DEMOS[demoIdx % DEMOS.length];
    setDemoIdx(p => p + 1);

    setPipelineSteps(demo.steps);
    for (let i = 0; i < demo.steps.length; i++) {
      await new Promise(r => setTimeout(r, 500));
      setVisibleSteps(i + 1);
    }

    await new Promise(r => setTimeout(r, 600));

    setMessages(prev => [...prev, {
      role: "assistant", text: demo.text, agent: demo.agent,
    }]);
    setBusy(false);
  };'''

new = '''  const run = async (text) => {
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
  };'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print('OK - App.jsx updated')
else:
    print('ERROR - old text not found, checking...')
    if 'DEMOS[demoIdx' in content:
        print('Found demoIdx reference - trying broader replace')
        # Find and replace just the key line
        content = content.replace('const demo = DEMOS[demoIdx % DEMOS.length];\n    setDemoIdx(p => p + 1);\n\n    setPipelineSteps(demo.steps);\n    for (let i = 0; i < demo.steps.length; i++) {\n      await new Promise(r => setTimeout(r, 500));\n      setVisibleSteps(i + 1);\n    }\n\n    await new Promise(r => setTimeout(r, 600));\n\n    setMessages(prev => [...prev, {\n      role: "assistant", text: demo.text, agent: demo.agent,\n    }]);\n    setBusy(false);', '''try {
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
    setBusy(false);''')
        open(path, 'w', encoding='utf-8').write(content)
        print('OK - fixed with broader replace')
    else:
        print('Content not found at all')