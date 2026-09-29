#!/usr/bin/env python3
"""Local Web UI & Interactive Dashboard for Agentic AI Research Agent.

Run:
    python web_ui.py
Then open http://localhost:5050 in your browser.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import AgentOrchestrator
from report.builder import ReportBuilder


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agentic AI Research Agent — Autonomous Intelligence System</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0a0f1d;
      --bg-secondary: #0f172a;
      --bg-card: rgba(15, 23, 42, 0.75);
      --bg-glass: rgba(30, 41, 59, 0.45);
      --border-color: rgba(148, 163, 184, 0.15);
      --border-highlight: rgba(56, 189, 248, 0.4);
      --accent-cyan: #38bdf8;
      --accent-blue: #3b82f6;
      --accent-purple: #818cf8;
      --accent-green: #34d399;
      --accent-amber: #fbbf24;
      --accent-red: #f87171;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-glow: 0 0 25px rgba(56, 189, 248, 0.15);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
      line-height: 1.5;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 35%, rgba(129, 140, 248, 0.07) 0%, transparent 45%),
        radial-gradient(circle at 50% 90%, rgba(52, 211, 153, 0.05) 0%, transparent 40%);
    }

    /* Container */
    .container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 24px 64px;
    }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 32px;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .brand-icon {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(56, 189, 248, 0.3);
    }

    .brand-icon svg {
      width: 26px;
      height: 26px;
      fill: #fff;
    }

    .brand-title {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, #fff 30%, var(--accent-cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-tag {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 500;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(52, 211, 153, 0.1);
      border: 1px solid rgba(52, 211, 153, 0.3);
      color: var(--accent-green);
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 10px var(--accent-green);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.85); }
    }

    /* Tabs */
    .tab-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 28px;
    }

    .tab-btn {
      background: var(--bg-glass);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 10px 20px;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tab-btn:hover {
      color: #fff;
      border-color: rgba(148, 163, 184, 0.3);
    }

    .tab-btn.active {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(59, 130, 246, 0.1));
      border-color: var(--accent-cyan);
      color: #fff;
      box-shadow: var(--shadow-glow);
    }

    /* Input Card */
    .glass-card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 28px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      margin-bottom: 28px;
      transition: border-color 0.3s ease;
    }

    .glass-card:hover {
      border-color: var(--border-highlight);
    }

    .card-title {
      font-size: 17px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #fff;
    }

    /* Quick Presets */
    .presets-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }

    .preset-pill {
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 7px 14px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .preset-pill:hover {
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
      transform: translateY(-1px);
    }

    /* Goal Input Group */
    .input-group {
      display: flex;
      gap: 12px;
    }

    .goal-input {
      flex: 1;
      background: rgba(15, 23, 42, 0.85);
      border: 1.5px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      font-family: inherit;
      font-size: 15px;
      color: #fff;
      outline: none;
      transition: all 0.2s ease;
    }

    .goal-input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }

    .btn-run {
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      border: none;
      border-radius: var(--radius-md);
      padding: 0 28px;
      font-family: inherit;
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
      transition: all 0.2s ease;
    }

    .btn-run:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(56, 189, 248, 0.4);
    }

    .btn-run:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }

    /* Grid Layout for Output */
    .output-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 28px;
    }

    @media (max-width: 900px) {
      .output-grid { grid-template-columns: 1fr; }
    }

    /* Metrics Summary Strip */
    .metrics-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }

    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .metric-label {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    .metric-value {
      font-size: 26px;
      font-weight: 800;
      color: #fff;
    }

    .metric-value.green { color: var(--accent-green); }
    .metric-value.cyan { color: var(--accent-cyan); }
    .metric-value.amber { color: var(--accent-amber); }

    /* Step Timeline Cards */
    .step-card {
      background: rgba(30, 41, 59, 0.4);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 12px;
      transition: all 0.2s ease;
    }

    .step-card:hover {
      background: rgba(30, 41, 59, 0.6);
      border-color: rgba(148, 163, 184, 0.3);
    }

    .step-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .step-num {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 700;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-cyan);
      padding: 3px 8px;
      border-radius: 6px;
    }

    .tool-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(52, 211, 153, 0.15);
      color: var(--accent-green);
    }

    .tool-badge.calculator {
      background: rgba(129, 140, 248, 0.15);
      color: var(--accent-purple);
    }

    .tool-badge.summarizer {
      background: rgba(251, 191, 36, 0.15);
      color: var(--accent-amber);
    }

    .step-desc {
      font-size: 13.5px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 6px;
    }

    .step-meta {
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
    }

    /* Error recovery callout */
    .recovery-callout {
      background: rgba(251, 191, 36, 0.08);
      border: 1px solid rgba(251, 191, 36, 0.3);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      margin-top: 12px;
      margin-bottom: 12px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }

    .recovery-icon {
      color: var(--accent-amber);
      font-size: 18px;
      line-height: 1;
    }

    .recovery-text {
      font-size: 12.5px;
      color: #fef3c7;
    }

    .recovery-text strong {
      color: #fff;
    }

    /* Report Box */
    .report-content {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 20px;
      font-size: 13.5px;
      color: var(--text-secondary);
      max-height: 480px;
      overflow-y: auto;
      white-space: pre-wrap;
      line-height: 1.6;
    }

    .report-content h1, .report-content h2, .report-content h3 {
      color: #fff;
      margin-top: 16px;
      margin-bottom: 8px;
    }

    /* Code View */
    pre.raw-json {
      background: #020617;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 18px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #38bdf8;
      max-height: 480px;
      overflow: auto;
    }

    /* Architecture View Tab */
    #archView svg {
      width: 100%;
      height: auto;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-color);
    }

    /* Spinner */
    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.2);
      border-top: 3px solid #fff;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Footer */
    footer {
      text-align: center;
      padding-top: 32px;
      border-top: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 13px;
    }

    footer a {
      color: var(--accent-cyan);
      text-decoration: none;
    }

    footer a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>

  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand-wrap">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
        </div>
        <div>
          <h1 class="brand-title">Agentic AI Research Agent</h1>
          <p class="brand-tag">Autonomous Planning &bull; Multi-Tool Pipeline &bull; 3-Tier Self-Correction</p>
        </div>
      </div>
      <div>
        <span class="status-badge">
          <span class="status-dot"></span>
          System Online &bull; v1.0
        </span>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('agentView')">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1010 10A10 10 0 0012 2zm1 15h-2v-6h2zm0-8h-2V7h2z"/></svg>
        Live Agent Console
      </button>
      <button class="tab-btn" onclick="switchTab('archView')">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M4 6h16V4H4zm0 5h16v-2H4zm0 5h16v-2H4zm0 5h16v-2H4z"/></svg>
        System Architecture
      </button>
      <button class="tab-btn" onclick="switchTab('telemetryView')">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-7 14H7v-4h5zm5 0h-4V7h4z"/></svg>
        Evaluation Dashboard (40 Traces)
      </button>
    </div>

    <!-- TAB 1: Live Agent Console -->
    <div id="agentView" class="tab-content">
      <!-- Input Section -->
      <div class="glass-card">
        <div class="card-title">
          <span>Target Research Goal</span>
        </div>

        <!-- Quick preset goals -->
        <div class="presets-row">
          <span style="font-size:12px; color:var(--text-muted); align-self:center; font-weight:600;">PRESETS:</span>
          <button class="preset-pill" onclick="setGoal('Research and summarize the top 3 developments in artificial intelligence from the last week.')">🔬 AI Research</button>
          <button class="preset-pill" onclick="setGoal('Given a company name Tesla, produce a short competitive-landscape brief using public web data.')">🚗 Tesla Competitive Brief</button>
          <button class="preset-pill" onclick="setGoal('Plan a 3-day itinerary for Tokyo, respecting a budget of $500 and interests in food and culture.')">🗼 Tokyo Travel & Budget</button>
        </div>

        <div class="input-group">
          <input type="text" id="goalInput" class="goal-input" placeholder="Enter high-level goal in natural language..." value="Research and summarize the top 3 developments in artificial intelligence from the last week.">
          <button id="runBtn" class="btn-run" onclick="runAgent()">
            <span id="btnText">Execute Goal</span>
            <div id="btnSpinner" class="spinner" style="display:none;"></div>
          </button>
        </div>
      </div>

      <!-- Live Execution Telemetry Strip -->
      <div id="metricsStrip" class="metrics-strip" style="display:none;">
        <div class="metric-card">
          <span class="metric-label">Execution Status</span>
          <span id="metricStatus" class="metric-value green">SUCCESS</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Total Steps</span>
          <span id="metricSteps" class="metric-value cyan">4</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Retries / Recovery</span>
          <span id="metricRetries" class="metric-value amber">1</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Total Runtime</span>
          <span id="metricDuration" class="metric-value">4.2s</span>
        </div>
      </div>

      <!-- Execution Grid -->
      <div id="resultsGrid" class="output-grid" style="display:none;">
        <!-- Left Column: Steps Timeline -->
        <div class="glass-card">
          <div class="card-title">
            <span>Decomposed Plan & Execution Flow</span>
          </div>
          <div id="stepsList"></div>

          <!-- Recovery Callout -->
          <div id="recoveryBox" class="recovery-callout" style="display:none;">
            <div class="recovery-icon">⚡</div>
            <div class="recovery-text">
              <strong>Self-Correction Triggered:</strong>
              <div id="recoveryDetails">Simulated timeout detected on Step 1 &bull; Auto-retried and recovered successfully.</div>
            </div>
          </div>
        </div>

        <!-- Right Column: Final Report & Synthesis -->
        <div class="glass-card">
          <div class="card-title">
            <span>Synthesized Intelligence Report</span>
          </div>
          <div id="reportBox" class="report-content">Generating report...</div>
        </div>
      </div>

      <!-- Raw Audit Drawer -->
      <div id="jsonDrawer" class="glass-card" style="display:none;">
        <div class="card-title">
          <span>Machine-Readable Audit Trace (JSON)</span>
        </div>
        <pre id="jsonOutput" class="raw-json"></pre>
      </div>
    </div>

    <!-- TAB 2: Architecture View -->
    <div id="archView" class="tab-content" style="display:none;">
      <div class="glass-card">
        <div class="card-title">
          <span>Agent Architecture Diagram</span>
        </div>
        <div id="svgContainer" style="overflow:auto; max-height:850px;">
          <!-- SVG loaded here -->
        </div>
      </div>
    </div>

    <!-- TAB 3: Telemetry Dashboard -->
    <div id="telemetryView" class="tab-content" style="display:none;">
      <div class="glass-card">
        <div class="card-title">
          <span>40-Trace Benchmark & Monitoring Evaluation</span>
        </div>
        <p style="color:var(--text-secondary); margin-bottom:20px; font-size:14px;">
          Evaluated across 40 labeled traces covering Research, Competitive Intelligence, Travel Budgeting, and Fault Injection scenarios.
        </p>

        <div class="metrics-strip">
          <div class="metric-card">
            <span class="metric-label">Macro Precision</span>
            <span class="metric-value green">97.7%</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Macro Recall</span>
            <span class="metric-value green">100.0%</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Macro F1 Score</span>
            <span class="metric-value green">98.8%</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Fault Recovery Rate</span>
            <span class="metric-value cyan">100.0%</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Zero-Crash Integrity</span>
            <span class="metric-value green">100.0%</span>
          </div>
        </div>

        <div style="margin-top:24px; overflow-x:auto;">
          <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
            <thead>
              <tr style="border-bottom:1.5px solid var(--border-color); color:var(--text-muted);">
                <th style="padding:10px;">Domain Intent</th>
                <th style="padding:10px;">Support</th>
                <th style="padding:10px;">Precision</th>
                <th style="padding:10px;">Recall</th>
                <th style="padding:10px;">F1-Score</th>
                <th style="padding:10px;">Evaluation Outcome</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom:1px solid rgba(148,163,184,0.1);">
                <td style="padding:12px; font-weight:600; color:#fff;">Research Summarization</td>
                <td style="padding:12px;">13</td>
                <td style="padding:12px; color:var(--accent-cyan);">92.9%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">96.3%</td>
                <td style="padding:12px; color:var(--accent-green);">&#10003; PASS (Safe default fallback)</td>
              </tr>
              <tr style="border-bottom:1px solid rgba(148,163,184,0.1);">
                <td style="padding:12px; font-weight:600; color:#fff;">Competitive Intelligence</td>
                <td style="padding:12px;">11</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">&#10003; PASS (Exact entity classification)</td>
              </tr>
              <tr style="border-bottom:1px solid rgba(148,163,184,0.1);">
                <td style="padding:12px; font-weight:600; color:#fff;">Travel & Budgeting</td>
                <td style="padding:12px;">11</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">&#10003; PASS (Exact duration & budget parsing)</td>
              </tr>
              <tr>
                <td style="padding:12px; font-weight:600; color:#fff;">Adversarial / Code Injection</td>
                <td style="padding:12px;">5</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">100.0%</td>
                <td style="padding:12px; color:var(--accent-green);">&#10003; PASS (AST-safe parser blocked code exec)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer>
      <p>Built with Python, DuckDuckGo API, MediaWiki REST, AST Evaluator &amp; Extractive Summarization.</p>
      <p style="margin-top:4px;">
        Developer: <strong>Kallal Mukherjee</strong> &bull; 
        <a href="https://github.com/kallal79/agentic-ai-research-agent" target="_blank">GitHub Repository</a> &bull; 
        <a href="https://www.linkedin.com/in/kallalum/" target="_blank">LinkedIn Profile</a>
      </p>
    </footer>
  </div>

  <script>
    function setGoal(text) {
      document.getElementById('goalInput').value = text;
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      
      event.currentTarget.classList.add('active');
      document.getElementById(tabId).style.display = 'block';

      if (tabId === 'archView') {
        loadSvg();
      }
    }

    async function loadSvg() {
      const container = document.getElementById('svgContainer');
      if (container.children.length === 0) {
        try {
          const res = await fetch('/api/architecture');
          const svgText = await res.text();
          container.innerHTML = svgText;
        } catch (e) {
          container.innerHTML = '<p style="color:red;">Failed to load architecture diagram.</p>';
        }
      }
    }

    async function runAgent() {
      const goal = document.getElementById('goalInput').value.trim();
      if (!goal) return;

      const runBtn = document.getElementById('runBtn');
      const btnText = document.getElementById('btnText');
      const btnSpinner = document.getElementById('btnSpinner');

      runBtn.disabled = true;
      btnText.textContent = 'Agent Running...';
      btnSpinner.style.display = 'block';

      // Clear previous outputs
      document.getElementById('metricsStrip').style.display = 'none';
      document.getElementById('resultsGrid').style.display = 'none';
      document.getElementById('jsonDrawer').style.display = 'none';
      document.getElementById('recoveryBox').style.display = 'none';

      try {
        const res = await fetch('/api/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal: goal })
        });
        const data = await res.json();
        renderResults(data);
      } catch (err) {
        alert('Error executing agent: ' + err);
      } finally {
        runBtn.disabled = false;
        btnText.textContent = 'Execute Goal';
        btnSpinner.style.display = 'none';
      }
    }

    function renderResults(data) {
      const stats = data.statistics || {};
      const timing = data.timing || {};
      const steps = data.steps || [];
      const recovery = data.recovery_events || [];

      // Update metrics
      document.getElementById('metricStatus').textContent = stats.failed === 0 ? 'SUCCESS' : (stats.succeeded > 0 ? 'PARTIAL' : 'FAILED');
      document.getElementById('metricSteps').textContent = stats.total_steps || steps.length;
      document.getElementById('metricRetries').textContent = stats.total_retries || recovery.length;
      document.getElementById('metricDuration').textContent = (timing.duration_seconds || 0) + 's';
      document.getElementById('metricsStrip').style.display = 'grid';

      // Render steps
      const stepsContainer = document.getElementById('stepsList');
      stepsContainer.innerHTML = '';
      steps.forEach(step => {
        let badgeClass = 'tool-badge';
        if (step.tool === 'calculator') badgeClass += ' calculator';
        if (step.tool === 'text_summarizer') badgeClass += ' summarizer';

        const card = document.createElement('div');
        card.className = 'step-card';
        card.innerHTML = `
          <div class="step-card-header">
            <span class="step-num">STEP ${step.step_id}</span>
            <span class="${badgeClass}">${step.tool}</span>
          </div>
          <div class="step-desc">${step.description}</div>
          <div class="step-meta">
            <span>Status: <strong style="color:${step.status === 'SUCCESS' ? 'var(--accent-green)' : 'var(--accent-amber)'}">${step.status}</strong> (${step.attempts || 1} attempt${(step.attempts || 1) > 1 ? 's' : ''})</span>
            <span>Latency: ${step.duration_ms} ms</span>
          </div>
        `;
        stepsContainer.appendChild(card);
      });

      // Show recovery box if any recovery events
      if (recovery.length > 0) {
        const recBox = document.getElementById('recoveryBox');
        const recDetails = document.getElementById('recoveryDetails');
        recDetails.innerHTML = recovery.map(r => `<strong>Step ${r.step_id} [${r.action.toUpperCase()}]:</strong> ${r.reason}`).join('<br>');
        recBox.style.display = 'flex';
      }

      // Render report
      document.getElementById('reportBox').textContent = data.summary_markdown || JSON.stringify(data.final_output, null, 2);
      document.getElementById('resultsGrid').style.display = 'grid';

      // Render JSON Drawer
      document.getElementById('jsonOutput').textContent = JSON.stringify(data, null, 2);
      document.getElementById('jsonDrawer').style.display = 'block';
    }
  </script>
</body>
</html>
"""


class AgentWebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/architecture":
            svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "submission_files", "2_architecture_diagram.svg")
            if not os.path.exists(svg_path):
                svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "architecture_diagram.svg")
            if os.path.exists(svg_path):
                with open(svg_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            else:
                self.send_error(404, "Architecture SVG not found")
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            goal = data.get("goal", "Research recent advancements in AI")

            # Run the agent orchestrator
            agent = AgentOrchestrator(simulate_failure=True)
            report_data = agent.run(goal)

            # Generate markdown summary
            builder = ReportBuilder()
            md_text = builder.build_markdown(report_data)
            report_data["summary_markdown"] = md_text

            # Send JSON response
            resp_bytes = json.dumps(report_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
        else:
            self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        # Clean terminal logging
        sys.stderr.write(f"[WebUI] {args[0]} - {args[1]}\n")


def start_server(port: int = 5050):
    server = HTTPServer(("0.0.0.0", port), AgentWebHandler)
    print("=" * 65)
    print(f"  Agentic AI Research Agent — Web UI Online")
    print(f"  URL: http://localhost:{port}")
    print(f"  Local Network: http://127.0.0.1:{port}")
    print("=" * 65)
    server.serve_forever()


if __name__ == "__main__":
    port = 5050
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port)
