"""Centralized visual system for the Apex Streamlit application."""


EDITORIAL_CSS = """
<style>
:root {
    --font-display: "Anthropic Serif", "Source Serif 4", Georgia, "Times New Roman", serif;
    --font-ui: "Anthropic Sans", "Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono: "Anthropic Mono", "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
    --canvas: #f3efe7; --paper: #faf8f2; --paper-deep: #ebe5da;
    --ink: #201f1b; --ink-soft: #504d46; --muted: #777167;
    --line: #d1c9bc; --line-dark: #aaa194; --accent: #b84f2f;
    --positive: #506853; --negative: #875149;
}
html, body, [class*="css"] { font-family: var(--font-ui); }
.stApp { background: var(--canvas); color: var(--ink); }
[data-testid="stAppViewContainer"] > .main { background: var(--canvas); }
.main .block-container { max-width: 1240px; padding: 3.4rem 4rem 6rem; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--paper-deep); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.25rem; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] strong, [data-testid="stSidebar"] small { color: var(--ink-soft); }
.brand-lockup { display: flex; align-items: center; padding: .2rem .35rem 2.6rem; }
.brand-lockup strong { color: var(--ink); display: block; font-family: var(--font-display); font-size: 1.55rem; font-weight: 500; letter-spacing: .12em; }
.brand-lockup small { color: var(--muted); display: block; font-size: .72rem; margin-top: .08rem; }
.nav-caption, .minor-heading, .analysis-label { color: var(--muted); font-family: var(--font-mono); font-size: .68rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { border-bottom: 1px solid transparent; color: var(--ink-soft); padding: .65rem .55rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { border-bottom-color: var(--accent); color: var(--ink); font-weight: 650; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { color: var(--ink-soft) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { color: var(--ink) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color: var(--accent); }
.sidebar-status { border-top: 1px solid var(--line); margin: 2.4rem .35rem 0; padding-top: 1.15rem; }
.sidebar-status span, .sidebar-status small { color: var(--muted); display: block; font-size: .72rem; }
.sidebar-status strong { color: var(--ink); display: block; font-family: var(--font-mono); font-size: .76rem; margin: .42rem 0; }
.editorial-header { border-top: 3px solid var(--ink); margin-bottom: 2.4rem; padding-top: 1.1rem; }
.eyebrow { color: var(--accent); font-family: var(--font-mono); font-size: .72rem; letter-spacing: .1em; margin: 0 0 2.2rem; text-transform: uppercase; }
.editorial-header h1 { font-family: var(--font-display); font-size: clamp(3.4rem, 8vw, 7.4rem); font-weight: 400; letter-spacing: -.055em; line-height: .85; margin: 0; }
.editorial-header .dek { color: var(--ink-soft); font-family: var(--font-display); font-size: 1.35rem; line-height: 1.45; margin: 1.3rem 0 0; max-width: 720px; }
.section-heading { align-items: start; border-top: 1px solid var(--ink); display: grid; gap: 1.1rem; grid-template-columns: 3rem 1fr; margin: 4rem 0 1.7rem; padding-top: .8rem; }
.section-heading > span { color: var(--accent); font-family: var(--font-mono); font-size: .72rem; padding-top: .45rem; }
.section-heading h2, .record-masthead h2 { font-family: var(--font-display); font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 400; letter-spacing: -.035em; line-height: 1; margin: 0; }
.section-description { color: var(--muted); font-size: .9rem; margin: .55rem 0 0; }
.subsection-title { border-top: 1px solid var(--line-dark); font-family: var(--font-display); font-size: 1.45rem; font-weight: 500; margin: 2.2rem 0 1rem; padding-top: .65rem; }
.minor-heading { margin: 1.35rem 0 .45rem; }
.empty-state { color: var(--muted); font-family: var(--font-display); font-size: 1rem; font-style: italic; margin: .45rem 0; }
.briefing-strip, .difference-strip { border-bottom: 1px solid var(--line-dark); border-top: 1px solid var(--line-dark); display: grid; grid-template-columns: repeat(3, 1fr); margin: 2.2rem 0; }
.briefing-strip > div, .difference-strip > div { border-right: 1px solid var(--line); padding: 1rem 1.25rem; }
.briefing-strip > div:first-child, .difference-strip > div:first-child { padding-left: 0; }
.briefing-strip > div:last-child, .difference-strip > div:last-child { border-right: 0; }
.briefing-strip span, .difference-strip span { color: var(--muted); display: block; font-size: .72rem; margin-bottom: .4rem; }
.briefing-strip strong { font-family: var(--font-display); font-size: 1.8rem; font-weight: 400; }
.difference-strip strong { font-family: var(--font-mono); font-size: .82rem; }
.candidate-feature { border-top: 2px solid var(--ink); margin-bottom: 2.8rem; padding-top: .75rem; }
.candidate-feature--primary { border-top-width: 4px; }
.candidate-kicker { color: var(--accent); font-family: var(--font-mono); font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; }
.candidate-feature h3 { font-family: var(--font-display); font-size: clamp(1.9rem, 3vw, 3rem); font-weight: 400; letter-spacing: -.035em; line-height: 1; margin: .65rem 0; overflow-wrap: anywhere; }
.candidate-feature--primary h3 { font-size: clamp(2.8rem, 5vw, 5rem); }
.candidate-score { color: var(--accent); font-family: var(--font-mono); font-size: clamp(2rem, 4vw, 4rem); letter-spacing: -.06em; }
.candidate-id { color: var(--muted); font-family: var(--font-mono); font-size: .7rem; margin: .2rem 0 1.2rem; }
.score-strip { border-bottom: 1px solid var(--line); border-top: 1px solid var(--line); display: grid; grid-template-columns: 1.35fr 1fr 1fr; }
.score-item { border-right: 1px solid var(--line); padding: .75rem .8rem; }
.score-item:last-child { border-right: 0; }
.score-item span { color: var(--muted); display: block; font-size: .66rem; margin-bottom: .25rem; }
.score-item strong { font-family: var(--font-mono); font-size: .82rem; }
.score-item--lead strong { color: var(--accent); font-size: 1rem; }
.skill-ledger, .missing-ledger, .plain-ledger { border-top: 1px solid var(--line); list-style: none; margin: 0; padding: 0; }
.skill-ledger li { align-items: baseline; border-bottom: 1px solid var(--line); display: grid; gap: .75rem; grid-template-columns: 1fr 1fr auto; padding: .55rem 0; }
.skill-name { font-family: var(--font-display); font-size: 1rem; }
.skill-found { color: var(--muted); font-size: .72rem; overflow-wrap: anywhere; }
.match-method { color: var(--positive); font-family: var(--font-mono); font-size: .62rem; text-transform: uppercase; }
.skill-group-label { color: var(--ink-soft); font-family: var(--font-display); font-size: 1rem; margin: 1rem 0 .35rem; }
.missing-ledger li { border-bottom: 1px solid var(--line); color: var(--negative); padding: .55rem 0; }
.missing-ledger small { color: var(--muted); display: block; font-size: .7rem; margin-top: .2rem; }
.plain-ledger li { border-bottom: 1px solid var(--line); font-family: var(--font-display); padding: .5rem 0; }
.analysis-note { border-left: 2px solid var(--accent); margin: 1.6rem 0 0; padding: .15rem 0 .15rem 1rem; }
.analysis-note p:last-child { color: var(--ink-soft); font-family: var(--font-display); font-size: 1.03rem; line-height: 1.55; margin: .45rem 0 0; }
.analysis-note--comparison { margin-top: 3rem; }
.signal-note { border-left: 2px solid var(--positive); color: var(--ink-soft); font-family: var(--font-display); font-size: .95rem; margin: 1rem 0; padding: .25rem 0 .25rem .8rem; }
.match-records { border-top: 2px solid var(--ink); }
.match-record { border-bottom: 1px solid var(--line); padding: 1.2rem 0; }
.match-record h4 { font-family: var(--font-display); font-size: 1.25rem; font-weight: 500; margin: 0 0 .35rem; }
.match-record > p { color: var(--ink-soft); font-size: .82rem; margin: 0; }
.match-meta { display: flex; flex-wrap: wrap; gap: .4rem 1.25rem; margin-top: .65rem; }
.match-meta span { color: var(--muted); font-family: var(--font-mono); font-size: .66rem; text-transform: uppercase; }
.match-record blockquote { border-left: 2px solid var(--accent); color: var(--ink-soft); font-family: var(--font-display); line-height: 1.5; margin: .9rem 0 0; max-width: 760px; padding-left: .9rem; }
.match-record blockquote strong { color: var(--muted); display: block; font-family: var(--font-mono); font-size: .62rem; letter-spacing: .06em; margin-bottom: .3rem; text-transform: uppercase; }
.table-shell { overflow-x: auto; width: 100%; }
.ranking-table, .evidence-table { border-collapse: collapse; font-size: .88rem; width: 100%; }
.ranking-table thead, .evidence-table thead { border-bottom: 2px solid var(--ink); border-top: 1px solid var(--ink); }
.ranking-table th, .evidence-table th { color: var(--muted); font-family: var(--font-mono); font-size: .66rem; letter-spacing: .06em; padding: .7rem .8rem; text-align: left; text-transform: uppercase; }
.ranking-table td, .evidence-table td { border-bottom: 1px solid var(--line); padding: 1.05rem .8rem; vertical-align: top; }
.ranking-table td:not(:nth-child(2)), .evidence-table td:last-child { font-family: var(--font-mono); font-size: .8rem; }
.ranking-table td small { color: var(--muted); display: block; font-family: var(--font-mono); font-size: .65rem; margin-top: .25rem; }
.rank-cell { color: var(--accent); }
.record-masthead { border-bottom: 1px solid var(--ink); margin: 2.6rem 0 1rem; padding-bottom: 1rem; }
.record-masthead > span { color: var(--accent); font-family: var(--font-mono); font-size: .7rem; }
.record-masthead h2 { margin: .5rem 0 .35rem; }
.record-masthead small { color: var(--muted); font-family: var(--font-mono); }
.comparison-person { border-top: 3px solid var(--ink); margin-top: 2rem; padding-top: .8rem; }
.comparison-person p { color: var(--accent); font-family: var(--font-mono); font-size: .68rem; margin: 0; text-transform: uppercase; }
.comparison-person h3 { font-family: var(--font-display); font-size: clamp(1.8rem, 3vw, 3rem); font-weight: 400; line-height: 1; margin: .7rem 0 1.4rem; overflow-wrap: anywhere; }
.comparison-person > strong { color: var(--accent); display: block; font-family: var(--font-mono); font-size: 2.2rem; }
.comparison-person > small { color: var(--muted); }
.comparison-verdict { align-items: baseline; border-bottom: 1px solid var(--ink); border-top: 1px solid var(--ink); display: grid; gap: 1rem; grid-template-columns: auto 1fr auto; margin-top: 3rem; padding: 1rem 0; }
.comparison-verdict span { color: var(--muted); font-size: .75rem; }
.comparison-verdict strong { font-family: var(--font-display); font-size: 1.6rem; font-weight: 400; }
.comparison-verdict small { font-family: var(--font-mono); font-size: .68rem; }
[data-testid="stSelectbox"] label { color: var(--muted); font-family: var(--font-mono); font-size: .7rem; letter-spacing: .04em; text-transform: uppercase; }
[data-baseweb="select"] > div { background: var(--paper) !important; border-color: var(--line-dark) !important; border-radius: 0 !important; }
[data-testid="stAlert"] { border-radius: 0; }
@media (max-width: 900px) {
    .main .block-container { padding: 2.6rem 1.4rem 4rem; }
    .editorial-header h1 { font-size: 4rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 340px !important; min-width: 0 !important; width: 100% !important; }
}
@media (max-width: 620px) {
    .briefing-strip, .difference-strip { grid-template-columns: 1fr; }
    .briefing-strip > div, .difference-strip > div { border-bottom: 1px solid var(--line); border-right: 0; padding-left: 0; }
    .briefing-strip > div:last-child, .difference-strip > div:last-child { border-bottom: 0; }
    .score-strip { grid-template-columns: 1fr; }
    .score-item { border-bottom: 1px solid var(--line); border-right: 0; }
    .score-item:last-child { border-bottom: 0; }
    .skill-ledger li { grid-template-columns: 1fr auto; }
    .skill-found { grid-column: 1 / -1; grid-row: 2; }
    .comparison-verdict { align-items: start; grid-template-columns: 1fr; }
    .section-heading { grid-template-columns: 2rem 1fr; }
}
</style>
"""
