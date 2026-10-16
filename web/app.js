"use strict";

const $ = (s, r = document) => r.querySelector(s);

/* ---------- tiny helpers ---------- */
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  kids.flat().forEach(k => n.append(k));
  return n;
}

async function api(action, body = {}) {
  try {
    const r = await fetch("/api/" + action, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    const data = await r.json();
    updateBadge(data.user);
    return data;
  } catch (e) {
    return { ok: false, error: "Cannot reach the server. Is server.py running?" };
  }
}

function updateBadge(user) {
  const b = $("#userBadge");
  if (user) { b.textContent = `Signed in: ${user.account_number} (${user.name})`; b.classList.add("on"); }
  else { b.textContent = "Not signed in"; b.classList.remove("on"); }
}

function show(box, data, okText) {
  box.replaceChildren(el("div", { class: "msg " + (data.ok ? "ok" : "err") },
    data.ok ? (data.message || okText || "Done.") : data.error));
}

function field(label, name, type = "text", extra = {}) {
  return el("label", {}, label, el("input", { name, type, required: "", ...extra }));
}

/* form that posts to an action and shows the reply */
function actionForm(action, fields, submitText, { onDone, reset = true } = {}) {
  const out = el("div");
  const form = el("form", {
    onsubmit: async e => {
      e.preventDefault();
      const body = Object.fromEntries(new FormData(form));
      const data = await api(action, body);
      show(out, data);
      if (data.ok && reset) form.reset();
      if (onDone) onDone(data);
    }
  }, fields, el("button", { class: "btn", type: "submit" }, submitText));
  return [form, out];
}

function table(headers, rows) {
  if (!rows.length) return el("p", { class: "empty" }, "Nothing to show.");
  return el("div", { class: "tablewrap" }, el("table", {},
    el("thead", {}, el("tr", {}, headers.map(h => el("th", {}, h)))),
    el("tbody", {}, rows.map(r => el("tr", {}, r.map(c => el("td", {}, c)))))));
}

const pill = s => el("span", { class: "pill " + s }, s);
const kv = obj => el("dl", { class: "kv" }, Object.entries(obj).flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, String(v))]));

const loanTable = (loans, withAccount) => table(
  [...(withAccount ? ["Loan ID", "Account"] : ["Loan ID"]), "Principal", "To be paid", "Remaining", "Due date", "Collateral", "Status"],
  loans.map(l => [l.loan_id, ...(withAccount ? [l.account] : []), l.principal, l.total_payable,
                  l.remaining, l.due_date, l.collateral, pill(l.status)]));

/* ---------- menu definition (mirrors main.py menus) ---------- */
const CUSTOMER = [
  { title: "Open Account", build: () => actionForm("open_account", [
      field("Full legal name", "name"),
      field("Date of birth", "dob", "date"),
      field("Aadhar card number (12 digits)", "aadhar", "text", { inputmode: "numeric", maxlength: 14 }),
      el("label", {}, "Account type", el("select", { name: "type" },
        el("option", { value: 1 }, "Savings"), el("option", { value: 2 }, "Salary"), el("option", { value: 3 }, "Current"))),
      field("Set a password (min 4 characters)", "password", "password"),
    ], "Create Account") },

  { title: "Sign In", build: () => actionForm("sign_in", [
      field("Account number", "account_number", "number"),
      field("Password", "password", "password"),
    ], "Sign In") },

  { title: "Deposit Money", build: () => actionForm("deposit", [
      field("Amount to deposit (Rs.)", "amount", "number", { step: "0.01", min: "0.01" })], "Deposit") },

  { title: "Withdraw Money", build: () => actionForm("withdraw", [
      field("Amount to withdraw (Rs.)", "amount", "number", { step: "0.01", min: "0.01" })], "Withdraw") },

  { title: "Check Account Status", build: () => {
      const box = el("div");
      const load = async () => {
        const d = await api("status");
        if (!d.ok) return show(box, d);
        box.replaceChildren(
          el("h4", {}, "Account"), kv(d.account),
          el("h4", {}, "Transaction history"),
          table(["Txn ID", "Type", "Sender", "Receiver", "Amount", "Role", "Loan", "Time"],
            d.transactions.map(t => [t.id, t.type, t.sender, t.receiver, t.amount, t.role, t.loan, t.time])),
          el("h4", {}, "Loans"), loanTable(d.loans, false),
          el("p", {}, el("button", { class: "btn alt", onclick: load }, "Refresh")));
      };
      return [box, load];
  } },

  { title: "Transfer Money", build: () => actionForm("transfer", [
      field("Receiver account number", "receiver", "number"),
      field("Amount to transfer (Rs.)", "amount", "number", { step: "0.01", min: "0.01" })], "Transfer") },

  { title: "Apply for Loan", build: () => {
      const box = el("div"), out = el("div");
      let last = null;
      const form = el("form", { onsubmit: async e => {
        e.preventDefault();
        last = Object.fromEntries(new FormData(form));
        const d = await api("loan_quote", last);
        if (!d.ok) { box.replaceChildren(); return show(out, d); }
        out.replaceChildren();
        box.replaceChildren(el("h4", {}, "Loan offer"), kv(d.quote),
          d.eligible
            ? el("div", { class: "row" },
                el("button", { class: "btn", onclick: async () => {
                  const r = await api("apply_loan", last); box.replaceChildren(); show(out, r); if (r.ok) form.reset();
                } }, "Accept Loan"),
                el("button", { class: "btn alt", onclick: () => { box.replaceChildren(); show(out, { ok: true, message: "Loan application cancelled." }); } }, "Cancel"))
            : el("div", { class: "msg err" }, d.reason));
      } },
        field("Loan amount (Rs.)", "amount", "number", { step: "0.01", min: "0.01" }),
        field("Repayment period in months", "months", "number", { min: "1", max: "36" }),
        el("button", { class: "btn", type: "submit" }, "Get Offer"));
      const tiers = el("p", { class: "hint" }, "Loading loan rates…");
      api("loan_info").then(d => {
        tiers.textContent = d.ok
          ? "Rates (simple interest, per year): " + (() => { let p = 0; return d.tiers.map(t => { const s = `${p + 1}–${t.max_months} months: ${t.rate}% interest, ${t.collateral}% collateral`; p = t.max_months; return s; }).join(" · "); })()
          : "Sign in to see loan rates.";
      });
      return [tiers, form, box, out];
  } },

  { title: "Repay Loan", build: () => {
      const box = el("div");
      const load = async () => {
        const d = await api("my_pending_loans");
        if (!d.ok) return show(box, d);
        if (!d.loans.length) return box.replaceChildren(el("p", { class: "empty" }, "You have no pending loans."));
        const out = el("div");
        const form = el("form", { onsubmit: async e => {
          e.preventDefault();
          const r = await api("repay_loan", Object.fromEntries(new FormData(form)));
          if (r.ok) { await load(); box.append(el("div", { class: "msg ok" }, r.message)); } else show(out, r);
        } },
          el("label", {}, "Loan to repay", el("select", { name: "loan_id" },
            d.loans.map(l => el("option", { value: l.loan_id }, `${l.loan_id} — remaining ${l.remaining} (${l.status})`)))),
          field("Amount to repay (Rs.)", "amount", "number", { step: "0.01", min: "0.01" }),
          el("button", { class: "btn", type: "submit" }, "Repay"));
        box.replaceChildren(el("p", { class: "hint" }, "Available balance: " + d.available),
          loanTable(d.loans, false), el("br"), form, out);
      };
      return [box, load];
  } },

  { title: "Log Out", build: () => {
      const out = el("div");
      return [el("p", {}, "Sign out of the current account?"),
        el("button", { class: "btn", onclick: async () => show(out, await api("logout")) }, "Log Out"), out];
  } },
];

const BANK = [
  { title: "Show Current Funds in Bank", build: () => {
      const box = el("div");
      const load = async () => {
        const d = await api("bank_funds");
        box.replaceChildren(kv(d.info), el("button", { class: "btn alt", onclick: load }, "Refresh"));
      };
      return [box, load];
  } },
  { title: "Show Pending Loans", build: () => {
      const box = el("div");
      const load = async () => {
        const d = await api("bank_pending");
        box.replaceChildren(
          d.loans.length ? loanTable(d.loans, true) : el("p", { class: "empty" }, "No pending loans."),
          el("p", {}, el("strong", {}, "Total outstanding: "), d.total), 
          el("button", { class: "btn alt", onclick: load }, "Refresh"));
      };
      return [box, load];
  } },
];

/* ---------- render ---------- */
function renderMenu(items) {
  const panel = $("#panel");
  panel.replaceChildren();
  const all = [];
  items.forEach(it => {
    const body = el("div", { class: "item-body" });
    const wrap = el("section", { class: "item" });
    let loader = null, built = false;

    const toggle = () => {
      const opening = !wrap.classList.contains("open");
      all.forEach(w => w.classList.remove("open"));        // one option open at a time
      if (!opening) return;
      if (!built) {                                          // build content lazily, once
        const res = it.build();
        const nodes = Array.isArray(res) && typeof res[res.length - 1] === "function" ? res.slice(0, -1) : res;
        loader = Array.isArray(res) && typeof res[res.length - 1] === "function" ? res[res.length - 1] : null;
        body.append(...nodes); built = true;
      }
      wrap.classList.add("open");
      if (loader) loader();                                  // data views refresh on every open
    };

    const head = el("div", { class: "item-head", onclick: toggle },
      el("button", { class: "plus", type: "button", "aria-label": "Expand " + it.title }, "+"),
      el("span", { class: "item-title" }, it.title));
    wrap.append(head, body);
    all.push(wrap);
    panel.append(wrap);
  });
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === name));
  $("#panel").className = "panel panel-" + name;
  renderMenu(name === "customer" ? CUSTOMER : BANK);
}

document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => switchTab(t.dataset.tab)));
switchTab("customer");
api("whoami");
