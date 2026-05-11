# Proposal artifacts

Materials for the O'Reilly live course "Production Voice AI Agents with LiveKit."

| File | What it is |
|---|---|
| [`course-proposal.md`](./course-proposal.md) | The O'Reilly proposal in Markdown. Source of truth. 2-hour course, locked schedule. |
| [`course-proposal.html`](./course-proposal.html) | Rendered HTML version for copy-paste into the O'Reilly Google Doc template. Regenerate from the `.md` with the command below whenever the markdown changes. |
| [`citation-audit.md`](./citation-audit.md) | Strict vendor-source citation audit of every factual claim in the proposal. Companion document to `course-proposal.md`. Open findings (legacy `WorkerOptions` entrypoint, unverified `lk agent create`) live at the top. |

## Regenerating the HTML

```bash
# from repo root, with markdown_py installed (`uv tool install markdown`)
python3 -c "
import sys
import markdown
src = 'proposal/course-proposal.md'
out = 'proposal/course-proposal.html'
with open(src) as f: body = markdown.markdown(f.read(), extensions=['extra', 'sane_lists', 'smarty', 'tables'])
with open(out, 'w') as f:
    f.write('<!doctype html><html><head><meta charset=\"utf-8\"><title>Proposal</title></head><body>')
    f.write(body)
    f.write('</body></html>')
"
```

## Discipline

- **No em-dashes or en-dashes** in `course-proposal.md`. Verify with `grep -c "—" proposal/course-proposal.md` and `grep -c "–" proposal/course-proposal.md` (both should return 0).
- Every factual claim added to the proposal needs a row in `citation-audit.md` with one of: ✅ VENDOR-VERIFIED, 📁 REPO-ONLY, ⚠ DRIFT, ❓ VENDOR-DOC NOT FOUND, ✗ UNSOURCED.
- Schedule timings, section count, and total duration are locked at 2 hours. Do not adjust without confirming.
