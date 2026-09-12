"""Centralized visual system for the Apex Streamlit application."""


EDITORIAL_CSS = """
<style>
:root {
    --font-display: "Iowan Old Style", Charter, Georgia, "Times New Roman", serif;
    --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    --canvas: #f4f1ea;
    --paper: #fbfaf6;
    --paper-deep: #ebe6dc;
    --ink: #1c211e;
    --ink-soft: #4d514c;
    --muted: #74766f;
    --line: #d3cec3;
    --line-strong: #99978f;
    --accent: #a64529;
    --positive: #48624d;
    --negative: #865047;
}
html, body, [class*="css"] { font-family: var(--font-ui); }
.stApp { background: var(--canvas); color: var(--ink); }
[data-testid="stAppViewContainer"] > .main { background: var(--canvas); }
[data-testid="stHeader"] { background: transparent; }
.main .block-container { max-width: 1120px; padding: 2.7rem 3.5rem 5.5rem; }

[data-testid="stSidebar"] {
    background: var(--paper-deep);
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] > div:first-child { padding: 1.8rem 1.1rem; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] small { color: var(--ink-soft) !important; }
.brand-lockup { border-bottom: 1px solid var(--line); padding: .15rem .3rem 1.5rem; }
.brand-lockup strong {
    color: var(--ink);
    display: block;
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 600;
    letter-spacing: .14em;
}
.brand-lockup small {
    color: var(--muted);
    display: block;
    font-family: var(--font-mono);
    font-size: .62rem;
    letter-spacing: .04em;
    margin-top: .2rem;
}
.nav-caption,
.minor-heading,
.analysis-label,
.meta-label {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: .66rem;
    font-weight: 650;
    letter-spacing: .09em;
    text-transform: uppercase;
}
.nav-caption { color: var(--ink) !important; margin: 1.3rem .45rem .35rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-left: 2px solid transparent;
    color: var(--ink-soft) !important;
    margin: .05rem 0;
    padding: .52rem .65rem;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label span,
[data-testid="stSidebar"] [data-testid="stRadio"] label svg {
    color: var(--ink-soft) !important;
    fill: currentColor;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(255, 255, 255, .32);
    border-left-color: var(--accent);
    color: var(--ink) !important;
    font-weight: 650;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p,
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) span,
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) svg {
    color: var(--ink) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color: var(--accent); }
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child > div:first-child {
    background-color: var(--ink-soft) !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child > div:first-child > div {
    background-color: var(--paper-deep) !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div:first-child {
    background-color: var(--accent) !important;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div:first-child > div {
    background-color: var(--paper) !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: transparent;
    border-color: var(--line-strong);
    color: var(--ink) !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover,
[data-testid="stSidebar"] [data-testid="stButton"] button:focus-visible {
    background: var(--paper);
    border-color: var(--ink-soft);
    color: var(--ink) !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button * { color: inherit !important; }
.sidebar-status {
    border-top: 1px solid var(--line);
    margin: 1.8rem .35rem 0;
    padding-top: 1rem;
}
.sidebar-status span,
.sidebar-status small { color: var(--muted); display: block; font-size: .69rem; }
.sidebar-status strong {
    color: var(--ink);
    display: block;
    font-family: var(--font-mono);
    font-size: .73rem;
    margin: .35rem 0;
}

.editorial-header {
    border-top: 3px solid var(--ink);
    margin-bottom: 2rem;
    padding-top: .85rem;
}
.eyebrow {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: .67rem;
    letter-spacing: .1em;
    margin: 0 0 1.35rem;
    text-transform: uppercase;
}
.editorial-header h1 {
    font-family: var(--font-display);
    font-size: clamp(2.75rem, 5.5vw, 4.9rem);
    font-weight: 500;
    letter-spacing: -.045em;
    line-height: .96;
    margin: 0;
}
.editorial-header .dek {
    color: var(--ink-soft);
    font-family: var(--font-display);
    font-size: 1.18rem;
    line-height: 1.45;
    margin: .9rem 0 0;
    max-width: 680px;
}

.context-notice {
    align-items: baseline;
    border-bottom: 1px solid var(--line);
    border-top: 1px solid var(--line);
    display: flex;
    gap: .8rem;
    margin: -.4rem 0 2rem;
    padding: .7rem 0;
}
.context-notice strong {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: .65rem;
    letter-spacing: .07em;
    text-transform: uppercase;
}
.context-notice span { color: var(--muted); font-size: .78rem; }

.section-heading {
    align-items: start;
    border-top: 1px solid var(--ink);
    display: grid;
    gap: .9rem;
    grid-template-columns: 2.5rem 1fr;
    margin: 3.3rem 0 1.35rem;
    padding-top: .7rem;
}
.section-heading > span {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: .68rem;
    padding-top: .3rem;
}
.section-heading h2,
.record-masthead h2 {
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 3.5vw, 2.8rem);
    font-weight: 500;
    letter-spacing: -.035em;
    line-height: 1;
    margin: 0;
}
.section-description { color: var(--muted); font-size: .84rem; margin: .45rem 0 0; }
.subsection-title {
    border-top: 1px solid var(--line-strong);
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 600;
    margin: 2.1rem 0 .85rem;
    padding-top: .6rem;
}
.minor-heading { margin: 1.2rem 0 .4rem; }
.empty-state {
    color: var(--muted);
    font-family: var(--font-display);
    font-size: .95rem;
    font-style: italic;
    margin: .4rem 0;
}

.upload-flow {
    border-bottom: 1px solid var(--line-strong);
    border-top: 1px solid var(--line-strong);
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1fr;
    margin: 1.8rem 0 2.2rem;
    padding: .9rem 0;
}
.upload-step { padding: 0 .8rem; }
.upload-step:first-child { padding-left: 0; }
.upload-step span {
    color: var(--accent);
    display: block;
    font-family: var(--font-mono);
    font-size: .62rem;
    letter-spacing: .08em;
    margin-bottom: .22rem;
    text-transform: uppercase;
}
.upload-step strong { font-family: var(--font-display); font-size: 1rem; font-weight: 600; }
.upload-arrow { align-self: center; color: var(--line-strong); font-family: var(--font-mono); }
.upload-intro { border-top: 1px solid var(--line); margin-top: .35rem; padding-top: .75rem; }
.upload-intro strong {
    display: block;
    font-family: var(--font-display);
    font-size: 1.15rem;
    margin-bottom: .18rem;
}
.upload-intro span { color: var(--muted); font-size: .76rem; }
.file-status {
    border-bottom: 1px solid var(--line);
    color: var(--ink-soft);
    font-size: .76rem;
    margin: -.25rem 0 .8rem;
    min-height: 2rem;
    padding: .25rem 0 .65rem;
}
.file-status strong { color: var(--ink); font-family: var(--font-mono); font-size: .69rem; }
.helper-note {
    border-left: 2px solid var(--line-strong);
    color: var(--ink-soft);
    font-size: .78rem;
    line-height: 1.5;
    margin: 1.2rem 0;
    max-width: 760px;
    padding: .15rem 0 .15rem .8rem;
}
.helper-note strong { color: var(--ink); }
.analysis-ready {
    border-top: 1px solid var(--positive);
    color: var(--ink-soft);
    margin-top: 1.5rem;
    padding-top: .8rem;
}
.analysis-ready strong { color: var(--positive); font-family: var(--font-display); }
[data-testid="stFileUploaderDropzone"] {
    background: var(--paper);
    border: 1px dashed var(--line-strong);
    border-radius: 0;
    color: var(--ink-soft);
}
[data-testid="stFileUploader"],
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small {
    color: var(--ink-soft) !important;
}
[data-testid="stFileUploader"] svg {
    color: var(--ink-soft) !important;
    fill: currentColor;
}
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: var(--ink-soft) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--paper-deep) !important;
    border: 1px solid var(--line-strong) !important;
    color: var(--ink) !important;
}
[data-testid="stFileUploaderDropzone"] button * {
    color: var(--ink) !important;
    fill: currentColor;
}
[data-testid="stFileUploaderDropzone"] button:hover,
[data-testid="stFileUploaderDropzone"] button:focus-visible {
    background: var(--ink) !important;
    border-color: var(--ink) !important;
    color: var(--paper) !important;
}
[data-testid="stFileUploaderDropzone"] button:hover *,
[data-testid="stFileUploaderDropzone"] button:focus-visible * {
    color: var(--paper) !important;
    fill: currentColor;
}
[data-testid="stFileUploaderDropzone"] button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stButton"] button {
    border-radius: 0;
    box-shadow: none;
}
[data-testid="stButton"] button[kind="primary"] {
    background: var(--ink);
    border-color: var(--ink);
    color: var(--paper);
    font-weight: 650;
    letter-spacing: .01em;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: var(--accent);
    border-color: var(--accent);
}

.briefing-strip,
.difference-strip {
    border-bottom: 1px solid var(--line-strong);
    border-top: 1px solid var(--line-strong);
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    margin: 1.8rem 0;
}
.briefing-strip > div,
.difference-strip > div {
    border-right: 1px solid var(--line);
    padding: .85rem 1rem;
}
.briefing-strip > div:first-child,
.difference-strip > div:first-child { padding-left: 0; }
.briefing-strip > div:last-child,
.difference-strip > div:last-child { border-right: 0; }
.briefing-strip span,
.difference-strip span {
    color: var(--muted);
    display: block;
    font-size: .68rem;
    margin-bottom: .3rem;
}
.briefing-strip strong {
    font-family: var(--font-display);
    font-size: 1.45rem;
    font-weight: 500;
}
.difference-strip strong { font-family: var(--font-mono); font-size: .76rem; }

.candidate-entry {
    border-top: 2px solid var(--ink);
    margin: 0 0 .8rem;
    padding-top: .75rem;
}
.candidate-entry__head {
    align-items: end;
    display: grid;
    gap: 1rem;
    grid-template-columns: 3rem minmax(0, 1fr) auto;
    margin-bottom: .9rem;
}
.candidate-entry__rank {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 1rem;
    padding-bottom: .3rem;
}
.candidate-entry__identity h3 {
    font-family: var(--font-display);
    font-size: clamp(1.65rem, 3.1vw, 2.55rem);
    font-weight: 600;
    letter-spacing: -.035em;
    line-height: 1;
    margin: 0 0 .25rem;
    overflow-wrap: anywhere;
}
.candidate-entry__identity p {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: .66rem;
    margin: 0;
}
.candidate-entry__score {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: clamp(1.45rem, 2.6vw, 2.2rem);
    letter-spacing: -.04em;
    padding-bottom: .15rem;
    text-align: right;
}
.candidate-separator { margin: 2.2rem 0 3.1rem; }

.score-strip {
    border-bottom: 1px solid var(--line);
    border-top: 1px solid var(--line);
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
}
.score-item { border-right: 1px solid var(--line); padding: .65rem .75rem; }
.score-item:first-child { padding-left: 0; }
.score-item:last-child { border-right: 0; }
.score-item span { color: var(--muted); display: block; font-size: .64rem; margin-bottom: .2rem; }
.score-item strong { font-family: var(--font-mono); font-size: .78rem; }
.score-item--lead strong { color: var(--accent); font-size: .9rem; }

.skill-ledger,
.missing-ledger,
.plain-ledger {
    border-top: 1px solid var(--line);
    list-style: none;
    margin: 0;
    padding: 0;
}
.skill-ledger li {
    align-items: baseline;
    border-bottom: 1px solid var(--line);
    display: grid;
    gap: .7rem;
    grid-template-columns: minmax(10rem, 1fr) minmax(10rem, 1fr) auto;
    padding: .5rem 0;
}
.skill-name { font-family: var(--font-display); font-size: .98rem; font-weight: 600; }
.skill-found { color: var(--muted); font-size: .7rem; overflow-wrap: anywhere; }
.match-method {
    color: var(--positive);
    font-family: var(--font-mono);
    font-size: .6rem;
    text-transform: uppercase;
}
.skill-group-label {
    color: var(--ink-soft);
    font-family: var(--font-display);
    font-size: .94rem;
    font-weight: 600;
    margin: .85rem 0 .3rem;
}
.missing-ledger li {
    border-bottom: 1px solid var(--line);
    color: var(--negative);
    padding: .5rem 0;
}
.missing-ledger small { color: var(--muted); display: block; font-size: .68rem; margin-top: .18rem; }
.plain-ledger li {
    border-bottom: 1px solid var(--line);
    font-family: var(--font-display);
    padding: .48rem 0;
}

.analysis-note {
    border-left: 2px solid var(--accent);
    margin: 1.4rem 0 0;
    max-width: 900px;
    padding: .1rem 0 .1rem .9rem;
}
.analysis-note p:last-child {
    color: var(--ink-soft);
    font-family: var(--font-display);
    font-size: 1rem;
    line-height: 1.58;
    margin: .4rem 0 0;
}
.analysis-note--comparison { margin-top: 2.5rem; }
.signal-note {
    border-left: 2px solid var(--positive);
    color: var(--ink-soft);
    font-family: var(--font-display);
    font-size: .9rem;
    margin: .9rem 0;
    padding: .2rem 0 .2rem .75rem;
}

.match-records { border-top: 2px solid var(--ink); }
.match-record { border-bottom: 1px solid var(--line); padding: 1rem 0; }
.match-record h4 {
    font-family: var(--font-display);
    font-size: 1.12rem;
    font-weight: 650;
    margin: 0 0 .35rem;
}
.match-meta { display: flex; flex-wrap: wrap; gap: .35rem 1.1rem; }
.match-meta span {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: .62rem;
    text-transform: uppercase;
}
.match-record blockquote {
    border-left: 2px solid var(--line-strong);
    color: var(--ink-soft);
    font-family: var(--font-display);
    line-height: 1.5;
    margin: .75rem 0 0;
    max-width: 820px;
    padding-left: .8rem;
}
.match-record blockquote strong {
    color: var(--muted);
    display: block;
    font-family: var(--font-mono);
    font-size: .6rem;
    letter-spacing: .06em;
    margin-bottom: .25rem;
    text-transform: uppercase;
}

.table-shell { overflow-x: auto; width: 100%; }
.ranking-table {
    border-collapse: collapse;
    font-size: .84rem;
    width: 100%;
}
.ranking-table thead { border-bottom: 2px solid var(--ink); border-top: 1px solid var(--ink); }
.ranking-table th {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: .63rem;
    letter-spacing: .06em;
    padding: .65rem .7rem;
    text-align: left;
    text-transform: uppercase;
}
.ranking-table td { border-bottom: 1px solid var(--line); padding: .9rem .7rem; vertical-align: top; }
.ranking-table td:not(:nth-child(2)) { font-family: var(--font-mono); font-size: .76rem; }
.ranking-table td small {
    color: var(--muted);
    display: block;
    font-family: var(--font-mono);
    font-size: .62rem;
    margin-top: .2rem;
}
.rank-cell { color: var(--accent); }

.record-masthead {
    align-items: end;
    border-bottom: 1px solid var(--ink);
    display: grid;
    gap: .75rem 1.2rem;
    grid-template-columns: minmax(0, 1fr) auto;
    margin: 2rem 0 .8rem;
    padding-bottom: .8rem;
}
.record-masthead > span {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: .68rem;
    grid-column: 1 / -1;
}
.record-masthead h2 { margin: 0; overflow-wrap: anywhere; }
.record-masthead small { color: var(--muted); font-family: var(--font-mono); }
.record-score {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 1.7rem;
    text-align: right;
}

.comparison-person { border-top: 2px solid var(--ink); margin-top: 1.5rem; padding-top: .7rem; }
.comparison-person p {
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: .64rem;
    margin: 0;
    text-transform: uppercase;
}
.comparison-person h3 {
    font-family: var(--font-display);
    font-size: clamp(1.5rem, 2.5vw, 2.25rem);
    font-weight: 600;
    line-height: 1;
    margin: .55rem 0 1rem;
    overflow-wrap: anywhere;
}
.comparison-person > strong {
    color: var(--accent);
    display: block;
    font-family: var(--font-mono);
    font-size: 1.6rem;
}
.comparison-person > small { color: var(--muted); font-size: .68rem; }
.comparison-verdict {
    align-items: baseline;
    border-bottom: 1px solid var(--ink);
    border-top: 1px solid var(--ink);
    display: grid;
    gap: .8rem;
    grid-template-columns: auto 1fr auto;
    margin-top: 2.5rem;
    padding: .85rem 0;
}
.comparison-verdict span { color: var(--muted); font-size: .7rem; }
.comparison-verdict strong { font-family: var(--font-display); font-size: 1.4rem; font-weight: 600; }
.comparison-verdict small { font-family: var(--font-mono); font-size: .64rem; }

[data-testid="stSelectbox"] label {
    color: var(--muted);
    font-family: var(--font-mono);
    font-size: .66rem;
    letter-spacing: .04em;
    text-transform: uppercase;
}
[data-baseweb="select"] > div {
    background: var(--paper) !important;
    border-color: var(--line-strong) !important;
    border-radius: 0 !important;
}
[data-testid="stAlert"] { border-radius: 0; }
.empty-analysis {
    border-bottom: 1px solid var(--line-strong);
    border-top: 1px solid var(--line-strong);
    margin: 2rem 0 1.2rem;
    padding: 1.4rem 0;
}
.empty-analysis strong {
    display: block;
    font-family: var(--font-display);
    font-size: 1.25rem;
    margin-bottom: .35rem;
}
.empty-analysis p { color: var(--ink-soft); margin: 0; }

@media (max-width: 900px) {
    .main .block-container { padding: 2.3rem 1.5rem 4rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 320px !important;
        min-width: 0 !important;
        width: 100% !important;
    }
}
@media (max-width: 640px) {
    .editorial-header h1 { font-size: 2.7rem; }
    .context-notice { align-items: start; flex-direction: column; gap: .25rem; }
    .upload-flow { gap: .35rem; grid-template-columns: 1fr; }
    .upload-arrow { transform: rotate(90deg); }
    .candidate-entry__head { align-items: start; grid-template-columns: 2.2rem 1fr; }
    .candidate-entry__score { grid-column: 2; text-align: left; }
    .briefing-strip,
    .difference-strip,
    .score-strip { grid-template-columns: 1fr; }
    .briefing-strip > div,
    .difference-strip > div,
    .score-item {
        border-bottom: 1px solid var(--line);
        border-right: 0;
        padding-left: 0;
    }
    .briefing-strip > div:last-child,
    .difference-strip > div:last-child,
    .score-item:last-child { border-bottom: 0; }
    .skill-ledger li { grid-template-columns: 1fr auto; }
    .skill-found { grid-column: 1 / -1; grid-row: 2; }
    .record-masthead { align-items: start; grid-template-columns: 1fr; }
    .record-score { text-align: left; }
    .comparison-verdict { align-items: start; grid-template-columns: 1fr; }
    .section-heading { grid-template-columns: 2rem 1fr; }
}
</style>
"""
