/* =========================
   Scheduling algorithms
========================= */

function finish(d, g) {
    d.forEach(x => {
        x.tat = x.ct - x.at;
        x.wt = x.tat - x.bt;
        x.rt = x.st - x.at;
    });

    d.sort((a, b) => a.idx - b.idx);
    return { procs: d, gantt: g };
}

const fresh = ps => ps.map(x => ({ ...x, rem: x.bt, st: null }));

function nonPre(ps, key) {
    const left = fresh(ps), done = [], g = [];
    let t = 0;

    while (left.length) {
        const ready = left.filter(x => x.at <= t);

        if (!ready.length) {
            t = Math.min(...left.map(x => x.at));
            continue;
        }

        ready.sort((a, b) =>
            key(a) - key(b) || a.at - b.at || a.idx - b.idx
        );

        const x = ready[0];
        left.splice(left.indexOf(x), 1);
        x.st = t;
        t += x.bt;
        x.ct = t;

        g.push({ pid: x.pid, start: x.st, end: t });
        done.push(x);
    }

    return finish(done, g);
}

function rr(ps, q) {
    const p = fresh(ps).sort((a, b) => a.at - b.at || a.idx - b.idx);
    const queue = [], g = [], done = [];
    let t = 0, i = 0;

    const admit = () => {
        while (i < p.length && p[i].at <= t) queue.push(p[i++]);
    };

    admit();

    while (done.length < p.length) {
        if (!queue.length) {
            t = p[i].at;
            admit();
            continue;
        }

        const x = queue.shift();
        if (x.st === null) x.st = t;

        const runTime = Math.min(q, x.rem);
        g.push({ pid: x.pid, start: t, end: t + runTime });

        t += runTime;
        x.rem -= runTime;
        admit();

        if (x.rem > 0) {
            queue.push(x);
        } else {
            x.ct = t;
            done.push(x);
        }
    }

    return finish(done, g);
}

const QS = [2, 4, 8];

function mlfq(ps) {
    const p = fresh(ps).sort((a, b) => a.at - b.at || a.idx - b.idx);
    const Q = QS.map(() => []), g = [], done = [];
    let t = 0, i = 0;

    const admit = () => {
        while (i < p.length && p[i].at <= t) Q[0].push(p[i++]);
    };

    admit();

    while (done.length < p.length) {
        const lv = Q.findIndex(z => z.length);

        if (lv < 0) {
            t = p[i].at;
            admit();
            continue;
        }

        const x = Q[lv].shift();
        if (x.st === null) x.st = t;

        const runTime = Math.min(QS[lv], x.rem);
        g.push({ pid: x.pid, start: t, end: t + runTime, q: lv });

        t += runTime;
        x.rem -= runTime;
        admit();

        if (x.rem > 0) {
            Q[Math.min(lv + 1, QS.length - 1)].push(x);
        } else {
            x.ct = t;
            done.push(x);
        }
    }

    return finish(done, g);
}

const ALGOS = {
    fcfs: { n: 'FCFS', f: p => nonPre(p, x => x.at) },
    sjf: { n: 'SJF', f: p => nonPre(p, x => x.bt) },
    rr: { n: 'Round Robin', f: (p, q) => rr(p, q) },
    pri: { n: 'Priority', f: p => nonPre(p, x => x.pr) },
    mlfq: { n: 'MLFQ', f: p => mlfq(p) }
};

/* =========================
   Deadlock helpers
========================= */

const need = (mx, al) =>
    mx.map((r, i) => r.map((v, j) => v - al[i][j]));

function order(avail, needs, alloc, fin0) {
    const n = alloc.length;
    const w = [...avail];
    const f = fin0 ? [...fin0] : Array(n).fill(false);
    const seq = [];
    let go = true;

    while (go) {
        go = false;

        for (let i = 0; i < n; i++) {
            if (!f[i] && needs[i].every((v, j) => v <= w[j])) {
                alloc[i].forEach((v, j) => {
                    w[j] += v;
                });

                f[i] = true;
                seq.push(i);
                go = true;
            }
        }
    }

    return { seq, f };
}

function tryRequest(p, req, av, mx, al) {
    const nd = need(mx, al)[p];

    if (req.some((v, j) => v > nd[j])) {
        return {
            ok: false,
            why: `P${p} is asking for more than its remaining need.`
        };
    }

    if (req.some((v, j) => v > av[j])) {
        return {
            ok: false,
            why: `Not enough resources are free right now, so P${p} must wait.`
        };
    }

    const av2 = av.map((v, j) => v - req[j]);

    const al2 = al.map((r, i) =>
        i === p ? r.map((v, j) => v + req[j]) : r
    );

    const s = order(av2, need(mx, al2), al2);

    if (!s.f.every(Boolean)) {
        return {
            ok: false,
            why: 'Granting this request would leave the system in an unsafe state, so the process must wait.'
        };
    }

    return { ok: true, seq: s.seq, av: av2 };
}

function detect(av, al, rq) {
    const hold = al.map(r => r.every(v => v === 0));
    const { f } = order(av, rq, al, hold);

    return f.map((x, i) => x ? null : 'P' + i).filter(Boolean);
}

/* =========================
   Memory allocation
========================= */


function allocate(parts, reqs, strat) {
    const seg = parts.map((size, index) => ({
        size,
        owner: null,
        block: size,
        blockId: index + 1
    }));

    const res = [];
    const usedBlocks = new Set();

    reqs.forEach((size, i) => {
        const name = 'P' + (i + 1);

        // Only consider original blocks that have not been used.
        const candidates = seg.filter(
            s => !s.owner &&
                 !usedBlocks.has(s.blockId) &&
                 s.size >= size
        );

        if (!candidates.length) {
            const free = seg
                .filter(s => !s.owner && !usedBlocks.has(s.blockId))
                .reduce((sum, s) => sum + s.size, 0);

            res.push({
                name,
                size,
                ok: false,
                why: free >= size
                    ? `Enough memory is free (${free}), but no single unused block is large enough`
                    : `Not enough allocatable memory (${free})`
            });

            return;
        }

        let pick = candidates[0];

        if (strat === 'best') {
            pick = candidates.reduce(
                (a, b) => a.size <= b.size ? a : b
            );
        }

        if (strat === 'worst') {
            pick = candidates.reduce(
                (a, b) => a.size >= b.size ? a : b
            );
        }

        const index = seg.indexOf(pick);
        const originalSize = pick.size;
        const remaining = originalSize - size;

        // Allocate the process to this original block.
        pick.size = size;
        pick.owner = name;

        // Mark the entire original block as used.
        usedBlocks.add(pick.blockId);

        res.push({
            name,
            size,
            ok: true,
            block: pick.block,
            blockId: pick.blockId
        });

        // Preserve the unused portion for display only.
        if (remaining > 0) {
            seg.splice(index + 1, 0, {
                size: remaining,
                owner: null,
                block: pick.block,
                blockId: pick.blockId
            });
        }
    });

    return { seg, res };
}


/* =========================
   Shared UI helpers
========================= */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const esc = s => String(s).replace(/[&<>"]/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;'
}[c]));

const num = v =>
    /^\d+$/.test(String(v).trim()) ? Number(v) : NaN;

const PAL = [
    '#2563EB',
    '#0F766E',
    '#B45309',
    '#7C3AED',
    '#BE123C',
    '#4D7C0F',
    '#0369A1',
    '#A21CAF'
];

$$('nav button').forEach(b => {
    b.onclick = () => {
        $$('nav button').forEach(x =>
            x.setAttribute('aria-selected', x === b)
        );

        $$('.panel').forEach(p => {
            p.hidden = p.id !== b.dataset.tab;
        });
    };
});

/* =========================
   CPU scheduling UI
========================= */

const SAMPLE = [
    ['P1', 0, 5, 2],
    ['P2', 1, 3, 1],
    ['P3', 2, 8, 3],
    ['P4', 3, 6, 2]
];

let rows = [];

const LBL = {
    at: 'Arrival time',
    bt: 'Burst time',
    pr: 'Priority'
};

function resetRows() {
    rows = SAMPLE.map(r => ({
        pid: r[0],
        at: String(r[1]),
        bt: String(r[2]),
        pr: String(r[3])
    }));
}

function drawRows() {
    $('#wl').innerHTML =
        '<thead><tr><th>Process</th><th>Arrival</th><th>Burst</th><th>Priority</th><th></th></tr></thead><tbody>' +
        rows.map((r, i) =>
            `<tr><td><input aria-label="Process name" data-i="${i}" data-f="pid" value="${esc(r.pid)}"></td>` +
            ['at', 'bt', 'pr'].map(f =>
                `<td><input aria-label="${LBL[f]} of ${esc(r.pid)}" inputmode="numeric" data-i="${i}" data-f="${f}" value="${esc(r[f])}"></td>`
            ).join('') +
            `<td><button class="ghost sm" data-del="${i}" aria-label="Remove ${esc(r.pid)}">Remove</button></td></tr>`
        ).join('') + '</tbody>';
}

function readWorkload() {
    const procs = [];
    const seen = new Set();

    if (!rows.length) {
        return { error: 'Add at least one process.' };
    }

    for (let i = 0; i < rows.length; i++) {
        const r = rows[i];
        const pid = r.pid.trim();
        const at = num(r.at);
        const bt = num(r.bt);
        const pr = num(r.pr);
        const w = 'Row ' + (i + 1) + ': ';

        if (!pid) {
            return { error: w + 'the process needs a name.' };
        }

        if (seen.has(pid)) {
            return { error: w + 'the name "' + pid + '" is used twice.' };
        }

        seen.add(pid);

        if (isNaN(at)) {
            return { error: w + 'arrival time must be a whole number of 0 or more.' };
        }

        if (isNaN(bt) || bt < 1) {
            return { error: w + 'burst time must be a whole number of 1 or more.' };
        }

        if (isNaN(pr)) {
            return { error: w + 'priority must be a whole number of 0 or more.' };
        }

        procs.push({ pid, at, bt, pr, idx: i });
    }

    return { procs };
}

const avg = (a, k) =>
    (a.reduce((s, x) => s + x[k], 0) / a.length).toFixed(2);

function ganttHTML(g, procs) {
    const col = {};

    procs.forEach((p, i) => {
        col[p.pid] = PAL[i % PAL.length];
    });

    const segs = [];
    let pos = 0;

    g.forEach(s => {
        if (s.start > pos) {
            segs.push({ idle: true, start: pos, end: s.start });
        }

        segs.push(s);
        pos = s.end;
    });

    const u = Math.max(
        16,
        Math.min(40, Math.floor(900 / Math.max(1, pos)))
    );

    return '<div class="gantt" role="img" aria-label="Gantt chart">' +
        segs.map((s, i) => {
            const w = (s.end - s.start) * u;

            const end = i === segs.length - 1
                ? `<span class="tick end">${s.end}</span>`
                : '';

            return `<div class="seg${s.idle ? ' idle' : ''}" style="width:${w}px;${s.idle ? '' : 'background:' + col[s.pid]}">` +
                `<span class="tick">${s.start}</span>` +
                `${s.idle ? 'idle' : esc(s.pid) + (s.q !== undefined ? '<small>Q' + s.q + '</small>' : '')}` +
                end + '</div>';
        }).join('') + '</div>';
}

function renderSchedule(r) {
    $('#out').innerHTML =
        ganttHTML(r.gantt, r.procs) +
        '<div class="scroll"><table><thead><tr>' +
        '<th>Process</th><th class="n">Arrival</th><th class="n">Burst</th>' +
        '<th class="n">Priority</th><th class="n">Start</th><th class="n">Finish</th>' +
        '<th class="n">Waiting</th><th class="n">Turnaround</th><th class="n">Response</th>' +
        '</tr></thead><tbody>' +
        r.procs.map(x =>
            `<tr><td>${esc(x.pid)}</td><td class="n">${x.at}</td>` +
            `<td class="n">${x.bt}</td><td class="n">${x.pr}</td>` +
            `<td class="n">${x.st}</td><td class="n">${x.ct}</td>` +
            `<td class="n">${x.wt}</td><td class="n">${x.tat}</td><td class="n">${x.rt}</td></tr>`
        ).join('') +
        `<tr class="foot"><td colspan="6">Average</td>` +
        `<td class="n">${avg(r.procs, 'wt')}</td>` +
        `<td class="n">${avg(r.procs, 'tat')}</td>` +
        `<td class="n">${avg(r.procs, 'rt')}</td></tr></tbody></table></div>`;
}

async function postJSON(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || `Request failed (${response.status}).`);
    }

    return data;
}

function backendProcesses(procs) {
    return procs.map(p => ({
        pid: p.pid,
        arrival_time: p.at,
        burst_time: p.bt,
        priority: p.pr
    }));
}

function normalizeSchedule(data, algo) {
    const procs = (data.processes || []).map((p, i) => ({
        pid: p.pid,
        at: p.arrival_time,
        bt: p.burst_time,
        pr: p.priority ?? 0,
        st: p.start_time,
        ct: p.completion_time,
        wt: p.waiting_time,
        tat: p.turnaround_time,
        rt: p.response_time,
        idx: i
    }));

    const gantt = (data.gantt_chart || []).map(s => {
        const match = algo === 'mlfq' && typeof s.pid === 'string'
            ? s.pid.match(/^(.*)\(Q(\d+)\)$/)
            : null;

        return match
            ? { pid: match[1], q: Number(match[2]), start: s.start, end: s.end }
            : { pid: s.pid, start: s.start, end: s.end };
    });

    return { procs, gantt };
}

async function renderComparison(procs) {
    const goalSelect = document.querySelector('#comparison-goal');
    const goal = goalSelect ? goalSelect.value : 'waiting';

    const data = await postJSON('/api/scheduling/compare', {
        processes: backendProcesses(procs),
        goal: goal
    });

    const metricLabels = {
        waiting: 'Average waiting time',
        turnaround: 'Average turnaround time',
        response: 'Average response time'
    };

    const metricKeys = {
        waiting: 'avg_waiting_time',
        turnaround: 'avg_turnaround_time',
        response: 'avg_response_time'
    };

    const metric = metricKeys[goal];

    const all = (data.comparison || []).map(item => ({
        name: item.algorithm,
        waiting: Number(item.avg_waiting_time),
        turnaround: Number(item.avg_turnaround_time),
        response: Number(item.avg_response_time),
        isBest: item.is_best === true
    }));

    if (!all.length) {
        document.querySelector('#cmp').innerHTML =
            '<p class="hint">No comparison results returned.</p>';
        return;
    }

    document.querySelector('#cmp').innerHTML =
        `<p class="hint">Algorithms are ranked by ${metricLabels[goal].toLowerCase()}. ` +
        'Lower values are better. All tied best results are highlighted.</p>' +
        '<div class="scroll"><table><thead><tr>' +
        '<th>Algorithm</th>' +
        '<th class="n">Average waiting</th>' +
        '<th class="n">Average turnaround</th>' +
        '<th class="n">Average response</th>' +
        '</tr></thead><tbody>' +
        all.map(item =>
            `<tr class="${item.isBest ? 'best' : ''}">` +
            `<td>${esc(item.name)}${item.isBest ? ' ★ Best' : ''}</td>` +
            `<td class="n">${item.waiting.toFixed(2)}</td>` +
            `<td class="n">${item.turnaround.toFixed(2)}</td>` +
            `<td class="n">${item.response.toFixed(2)}</td>` +
            '</tr>'
        ).join('') +
        '</tbody></table></div>';
}

/* All selected scheduling results and comparison come from Flask. */

async function run() {
    const algo = $('#algo').value;
    const q = num($('#q').value);
    const err = $('#err');
    const out = $('#out');
    const cmp = $('#cmp');

    const w = readWorkload();
    let msg = w.error;

    if (!msg && !(Number.isInteger(q) && q >= 1)) {
        msg = 'The time quantum must be a whole number of 1 or more.';
    }

    if (msg) {
        err.textContent = msg;
        out.innerHTML = '';
        cmp.innerHTML = '';
        return;
    }

    err.textContent = '';
    out.innerHTML = '<p class="hint">Calculating schedule...</p>';
    cmp.innerHTML = '<p class="hint">Comparing algorithms...</p>';

    try {
        const payload = { processes: backendProcesses(w.procs) };
        let endpoint = '/api/scheduling/fcfs';

        if (algo === 'sjf') {
            endpoint = '/api/scheduling/sjf';
        } else if (algo === 'rr') {
            endpoint = '/api/scheduling/round-robin';
            payload.time_quantum = q;
        } else if (algo === 'pri') {
            endpoint = '/api/scheduling/priority';
            payload.aging_interval = 4;
            payload.aging_boost = 1;
        } else if (algo === 'mlfq') {
            endpoint = '/api/scheduling/mlfq';
            payload.quantums = [2, 4, 8];
        }

        const data = await postJSON(endpoint, payload);
        const result = normalizeSchedule(data, algo);

        renderSchedule(result);

        try {
            await renderComparison(w.procs);
        } catch (comparisonError) {
            cmp.innerHTML =
                `<p class="err">Schedule calculated, but comparison failed: ${esc(comparisonError.message)}</p>`;
        }
    } catch (error) {
        err.textContent = error.message || 'An unexpected error occurred.';
        out.innerHTML = '';
        cmp.innerHTML = '';
    }
}

/* Workload event listeners */

$('#wl').addEventListener('input', e => {
    const i = e.target.dataset.i;
    if (i === undefined) return;

    rows[i][e.target.dataset.f] = e.target.value;
    run();
});

$('#wl').addEventListener('click', e => {
    const d = e.target.dataset.del;
    if (d === undefined) return;

    rows.splice(+d, 1);
    drawRows();
    run();
});

$('#add').onclick = () => {
    let k = rows.length + 1;

    while (rows.some(r => r.pid === 'P' + k)) k++;

    rows.push({ pid: 'P' + k, at: '0', bt: '1', pr: '1' });
    drawRows();
    run();
};

$('#reset').onclick = () => {
    resetRows();
    drawRows();
    run();
};

$('#algo').onchange = run;
$('#q').oninput = run;

$('#comparison-goal').addEventListener('change', async () => {
    const workload = readWorkload();

    if (workload.error) return;

    try {
        await renderComparison(workload.procs);
    } catch (error) {
        $('#cmp').innerHTML =
            `<p class="err">${esc(error.message)}</p>`;
    }
});

/* =========================
   Deadlock UI
========================= */

const L = i => String.fromCharCode(65 + i);

const D = {
    bk: {
        n: 5,
        m: 3,
        t: {
            alloc: [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]],
            max: [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]],
            avail: [[3,3,2]]
        }
    },
    dt: {
        n: 5,
        m: 3,
        t: {
            alloc: [[0,1,0],[2,0,0],[3,0,3],[2,1,1],[0,0,2]],
            req: [[0,0,0],[2,0,2],[0,0,1],[1,0,0],[0,0,2]],
            avail: [[0,0,0]]
        }
    }
};

const TITLES = {
    alloc: 'Allocation (held now)',
    max: 'Maximum demand',
    req: 'Request (waiting for)',
    avail: 'Available (free now)'
};

function resize(s) {
    const S = D[s];

    for (const k in S.t) {
        const rowsCount = k === 'avail' ? 1 : S.n;

        S.t[k] = Array.from({ length: rowsCount }, (_, i) =>
            Array.from({ length: S.m }, (_, j) =>
                S.t[k][i] && S.t[k][i][j] !== undefined
                    ? S.t[k][i][j]
                    : 0
            )
        );
    }
}

function drawGrid(s) {
    const S = D[s];

    $('#' + s + '-grid').innerHTML = Object.keys(S.t).map(k =>
        `<div class="mat"><h3>${TITLES[k]}</h3><table><thead><tr><th></th>` +
        Array.from({ length: S.m }, (_, j) => `<th>${L(j)}</th>`).join('') +
        '</tr></thead><tbody>' +
        S.t[k].map((r, i) =>
            `<tr><th>${k === 'avail' ? 'Free' : 'P' + i}</th>` +
            r.map((v, j) =>
                `<td><input type="number" min="0" step="1" value="${v}" data-s="${s}" data-k="${k}" data-r="${i}" data-c="${j}" aria-label="${TITLES[k]}, resource ${L(j)}"></td>`
            ).join('') + '</tr>'
        ).join('') + '</tbody></table></div>'
    ).join('');
}

const valid = t =>
    Object.values(t).flat(2).every(v => Number.isInteger(v) && v >= 0);

const seqText = a => a.map(i => 'P' + i).join(' → ');

const matTable = (m, cols) =>
    '<table><thead><tr><th></th>' +
    cols.map(c => `<th class="n">${c}</th>`).join('') +
    '</tr></thead><tbody>' +
    m.map((r, i) =>
        `<tr><th>P${i}</th>` +
        r.map(v => `<td class="n">${v}</td>`).join('') +
        '</tr>'
    ).join('') + '</tbody></table>';

function calcBk() {
    const S = D.bk, out = $('#bk-out');
    $('#bk-res').innerHTML = '';

    if (!valid(S.t)) {
        out.innerHTML =
            '<p class="err">Every cell must be a whole number of 0 or more.</p>';
        return;
    }

    const nd = need(S.t.max, S.t.alloc);

    if (nd.some(r => r.some(v => v < 0))) {
        out.innerHTML =
            '<p class="err">A process holds more than its maximum demand.</p>';
        return;
    }

    const o = order(S.t.avail[0], nd, S.t.alloc);
    const safe = o.f.every(Boolean);

    out.innerHTML =
        (safe
            ? `<div class="msg"><span class="ok">Safe state.</span> Safe sequence: ${seqText(o.seq)}</div>`
            : '<div class="msg bad-box"><span class="bad">Unsafe state.</span> No order exists in which every process can finish.</div>') +
        '<h3>Remaining need (maximum minus allocation)</h3><div class="scroll">' +
        matTable(nd, Array.from({ length: S.m }, (_, j) => L(j))) +
        '</div>';
}

function drawReq() {
    const S = D.bk;

    $('#bk-req').innerHTML =
        '<label>Process<select id="rq-p">' +
        Array.from({ length: S.n }, (_, i) =>
            `<option value="${i}">P${i}</option>`
        ).join('') +
        '</select></label>' +
        Array.from({ length: S.m }, (_, j) =>
            `<label>Units of ${L(j)}<input class="rq" type="number" min="0" step="1" value="0" style="width:90px"></label>`
        ).join('') +
        '<button id="rq-go">Check request</button>';
}

$('#bk-req').addEventListener('click', e => {
    if (e.target.id !== 'rq-go') return;

    const S = D.bk, res = $('#bk-res');

    if (!valid(S.t) || need(S.t.max, S.t.alloc).some(r => r.some(v => v < 0))) {
        res.innerHTML = '<p class="err">Fix the tables above first.</p>';
        return;
    }

    const req = $$('.rq').map(i => num(i.value));

    if (req.some(isNaN)) {
        res.innerHTML =
            '<p class="err">Each request must be a whole number of 0 or more.</p>';
        return;
    }

    const r = tryRequest(
        +$('#rq-p').value,
        req,
        S.t.avail[0],
        S.t.max,
        S.t.alloc
    );

    res.innerHTML = r.ok
        ? `<div class="msg"><span class="ok">Request can be granted.</span> Safe sequence afterwards: ${seqText(r.seq)}. Free resources afterwards: ${r.av.map((v,j) => L(j) + ' = ' + v).join(', ')}.</div>`
        : `<div class="msg bad-box"><span class="bad">Request refused.</span> ${r.why}</div>`;
});

function calcDt() {
    const S = D.dt, out = $('#dt-out');

    if (!valid(S.t)) {
        out.innerHTML =
            '<p class="err">Every cell must be a whole number of 0 or more.</p>';
        return;
    }

    const d = detect(S.t.avail[0], S.t.alloc, S.t.req);

    out.innerHTML = d.length
        ? `<div class="msg bad-box"><span class="bad">Deadlock.</span> ${d.join(', ')} can never continue.</div>`
        : '<div class="msg"><span class="ok">No deadlock.</span> Every process can eventually finish.</div>';
}

['bk', 'dt'].forEach(s => {
    $('#' + s + '-grid').addEventListener('input', e => {
        const d = e.target.dataset;
        if (d.k === undefined) return;

        D[s].t[d.k][+d.r][+d.c] = num(e.target.value);
        s === 'bk' ? calcBk() : calcDt();
    });

    ['n', 'm'].forEach(f => {
        $('#' + s + '-' + f).addEventListener('input', e => {
            const v = num(e.target.value);
            const max = f === 'n' ? 8 : 6;

            if (isNaN(v) || v < 1 || v > max) return;

            D[s][f] = v;
            resize(s);
            drawGrid(s);

            if (s === 'bk') {
                drawReq();
                calcBk();
            } else {
                calcDt();
            }
        });
    });
});

/* =========================
   Memory UI
========================= */

const list = t => t.split(/[\s,]+/).filter(Boolean);

function runMem() {
    const err = $('#mem-err');
    const out = $('#mem-out');

    const b = list($('#blocks').value);
    const r = list($('#reqs').value);

    if (!b.length || !r.length) {
        err.textContent =
            'Enter at least one free block and one process request.';
        out.innerHTML = '';
        return;
    }

    if (b.concat(r).some(v => !/^\d+$/.test(v) || Number(v) < 1)) {
        err.textContent =
            'Use positive whole numbers separated by commas.';
        out.innerHTML = '';
        return;
    }

    err.textContent = '';

    const parts = b.map(Number);
    const reqs = r.map(Number);

    const strategies = [
        ['first', 'First Fit'],
        ['best', 'Best Fit'],
        ['worst', 'Worst Fit']
    ];

    out.innerHTML = strategies.map(([strategy, title]) => {
        const allocation = allocate(parts, reqs, strategy);

        const freeSegments = allocation.seg.filter(s => !s.owner);

        const freeMemory = freeSegments.reduce(
            (sum, s) => sum + s.size,
            0
        );

        const largestFree = freeSegments.length
            ? Math.max(...freeSegments.map(s => s.size))
            : 0;

        const placed = allocation.res.filter(p => p.ok).length;

        const fragmentation = freeMemory
            ? Math.round((1 - largestFree / freeMemory) * 1000) / 10
            : 0;

        // Show each original block separately.
        // Any leftover memory remains visible inside its original block.
        const blockRows = parts.map((originalSize, blockIndex) => {
            const blockId = blockIndex + 1;

            const segments = allocation.seg.filter(
                s => s.blockId === blockId
            );

            const segmentTotal = segments.reduce(
                (sum, s) => sum + s.size,
                0
            );

            const segmentHTML = segments.map(segment => {
                const processIndex = segment.owner
                    ? Number(segment.owner.slice(1)) - 1
                    : 0;

                const color = segment.owner
                    ? PAL[processIndex % PAL.length]
                    : '#E5E7EB';

                const label = segment.owner || 'FREE MEMORY';

                return `
                    <div style="
                        flex: ${segment.size} 1 0;
                        min-width: 0;
                        padding: 12px 6px;
                        background: ${color};
                        color: ${segment.owner ? '#FFFFFF' : '#374151'};
                        text-align: center;
                        font-weight: 600;
                        overflow-wrap: anywhere;
                        border-radius: 5px;
                    " title="${esc(label)}: ${segment.size} units">
                        ${esc(label)}<br>
                        <small>${segment.size} units</small>
                    </div>`;
            }).join('');

            return `
                <div style="margin: 14px 0;">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        gap: 12px;
                        margin-bottom: 6px;
                    ">
                        <strong>Free block: ${originalSize}</strong>
                        <span class="hint">${segmentTotal} units</span>
                    </div>

                    <div style="
                        display: flex;
                        gap: 6px;
                        align-items: stretch;
                        min-height: 52px;
                    ">
                        ${segmentHTML}
                    </div>
                </div>`;
        }).join('');

        const tableRows = allocation.res.map(process => {
            if (process.ok) {
                return `
                    <tr>
                        <td><strong>${esc(process.name)}</strong></td>
                        <td class="n">${process.size} units</td>
                        <td>${process.block}</td>
                        <td><span class="ok">Allocated</span></td>
                    </tr>`;
            }

            return `
                <tr>
                    <td><strong>${esc(process.name)}</strong></td>
                    <td class="n">${process.size} units</td>
                    <td>—</td>
                    <td>
                        <span class="bad">Not allocated.</span>
                        ${esc(process.why)}
                    </td>
                </tr>`;
        }).join('');

        return `
            <section class="card">
                <h2>${title}</h2>

                <p class="stat">
                    Allocated ${placed} of ${reqs.length} processes.
                    Total free memory: ${freeMemory} units.
                    Largest free block: ${largestFree} units.
                    External fragmentation indicator: ${fragmentation}%.
                </p>

                <h3>Memory segments</h3>

                <p class="hint">
                    Each row represents one original free block.
                    Leftover space remains visible as FREE MEMORY.
                </p>

                ${blockRows}

                <div class="scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Process</th>
                                <th class="n">Requested size</th>
                                <th>Original block</th>
                                <th>Allocation status</th>
                            </tr>
                        </thead>
                        <tbody>${tableRows}</tbody>
                    </table>
                </div>
            </section>`;
    }).join('');
}

$('#blocks').oninput = runMem;
$('#reqs').oninput = runMem;

/* =========================
   Initialize the UI
========================= */

resetRows();
drawRows();
run();

['bk', 'dt'].forEach(s => {
    $('#' + s + '-n').value = D[s].n;
    $('#' + s + '-m').value = D[s].m;
    drawGrid(s);
});

drawReq();
calcBk();
calcDt();
runMem();

/* =========================
   ML Algorithm Recommendation
========================= */

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("recommend-button");
    const goalSelect = document.getElementById("recommendation-goal");
    const resultDiv = document.getElementById("recommendation-result");

    if (!button || !goalSelect || !resultDiv) return;

    button.addEventListener("click", async () => {
        resultDiv.textContent = "Generating recommendation...";
        button.disabled = true;

        try {
            const workload = readWorkload();

            if (workload.error) {
                throw new Error(workload.error);
            }

            const processes = backendProcesses(workload.procs);

            if (!processes || processes.length === 0) {
                throw new Error("Please enter at least one process.");
            }

            const response = await postJSON("/api/recommend", {
                processes: processes,
                goal: goalSelect.value
            });

            resultDiv.replaceChildren();

            const heading = document.createElement("h3");
            heading.textContent =
                "Recommended Algorithm: " +
                response.recommended_algorithm;

            resultDiv.appendChild(heading);

            const explanation = document.createElement("p");
            explanation.textContent =
                response.explanation || "No explanation provided.";

            resultDiv.appendChild(explanation);

            if (response.workload_stats) {
                const stats = document.createElement("pre");

                stats.textContent = JSON.stringify(
                    response.workload_stats,
                    null,
                    2
                );

                resultDiv.appendChild(stats);
            }
        } catch (error) {
            resultDiv.textContent =
                "Recommendation failed: " + error.message;
        } finally {
            button.disabled = false;
        }
    });
});