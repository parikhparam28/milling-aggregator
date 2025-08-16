import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button.jsx";
import { Input } from "./components/ui/input.jsx";
import { Textarea } from "./components/ui/textarea.jsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select.jsx";
import { Checkbox } from "./components/ui/checkbox.jsx";
import { Card, CardContent } from "./components/ui/card.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs.jsx";
import { Toaster, toast } from "./components/ui/sonner.jsx";
import { Badge } from "./components/ui/badge.jsx";
import { cn } from "./lib/utils.js";
import { Download, FileUp, LogIn, LogOut, Package, Receipt, Settings, ShoppingCart, UserPlus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Axios instance
const api = axios.create({ baseURL: API });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function useAuth() {
  const [user, setUser] = useState(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  useEffect(() => {
    if (!token) return;
    api.get("/me")
      .then((res) => setUser(res.data))
      .catch(() => setUser(null));
  }, [token]);
  return { user, setUser };
}

function Navbar({ user, onLogout }) {
  return (
    <div className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <div className="brand-badge"><span>PP</span></div>
          <Link to="/">Part Aggregator</Link>
        </div>
        <div className="nav-links">
          <Link to="/rfq/new">Get a quote</Link>
          <Link to="/requests">Requests</Link>
          <Link to="/offers">Offers</Link>
          <Link to="/orders">Orders</Link>
          <Link to="/payments">Payments</Link>
          {user ? (
            <Button variant="outline" size="sm" onClick={onLogout}><LogOut size={16} /> Logout</Button>
          ) : (
            <>
              <Link to="/login"><Button size="sm" variant="outline"><LogIn size={16}/> Login</Button></Link>
              <Link to="/register"><Button size="sm"><UserPlus size={16}/> Register</Button></Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Home() {
  return (
    <div>
      <section className="hero">
        <div className="hero-inner">
          <div>
            <h1>Precision machining quotes in minutes, not days.</h1>
            <p>Upload your CAD, pick materials and specs, and instantly compare supplier offers. DXF, DWG, STEP, IGES, STL supported.</p>
            <div style={{ display: "flex", gap: 12 }}>
              <Link to="/rfq/new"><Button size="lg">Get a quote</Button></Link>
              <Link to="/offers"><Button size="lg" variant="outline">View offers</Button></Link>
            </div>
          </div>
          <div className="hero-card">
            <div style={{ display: "grid", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Badge>Request</Badge>
                <span>Upload and submit specs</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Badge variant="secondary">Quotes</Badge>
                <span>Suppliers auto-respond</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Badge variant="outline">Order</Badge>
                <span>Accept and track production</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Badge variant="outline">Payment</Badge>
                <span>Pay securely (mock for demo)</span>
              </div>
            </div>
          </div>
        </div>
      </section>
      <div className="section-title">Why teams choose us</div>
      <div className="grid">
        <div className="tile"><h3>Supplier network</h3><p>Qualified EU suppliers with ISO certifications.</p></div>
        <div className="tile"><h3>Transparent pricing</h3><p>Compare offers by price, lead time, and notes.</p></div>
        <div className="tile"><h3>Manufacturing fit</h3><p>Material, tolerance, roughness handled with care.</p></div>
      </div>
    </div>
  );
}

function Register() {
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const submit = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/auth/register", form);
      toast.success("Registered. Please login.");
      nav("/login");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Registration failed");
    }
  };
  return (
    <div className="section-title">Create account
      <div className="form" style={{ marginTop: 12 }}>
        <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <div className="form-actions">
            <Button type="submit">Register</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Login({ onLogin }) {
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const submit = async (e) => {
    e.preventDefault();
    try {
      const data = new URLSearchParams();
      data.append("username", form.email);
      data.append("password", form.password);
      const res = await api.post("/auth/login", data, { headers: { "Content-Type": "application/x-www-form-urlencoded" } });
      localStorage.setItem("token", res.data.access_token);
      toast.success("Logged in");
      onLogin && onLogin();
      nav("/rfq/new");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Login failed");
    }
  };
  return (
    <div className="section-title">Login
      <div className="form" style={{ marginTop: 12 }}>
        <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
          <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <div className="form-actions">
            <Button type="submit">Login</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RFQNew() {
  const nav = useNavigate();
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({ material: "Aluminum 6061", quantity: 1, tolerance: "", roughness: "", part_marking: false, certification: "None", notes: "" });
  const submit = async (e) => {
    e.preventDefault();
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      if (file) fd.append("cad_file", file);
      await api.post("/rfqs", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("RFQ submitted. Quotes incoming!");
      nav("/offers");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Submit failed");
    }
  };
  return (
    <div>
      <div className="section-title">New RFQ</div>
      <div className="form" style={{ marginTop: 12 }}>
        <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
          <div className="form-row">
            <div>
              <label>Material</label>
              <Select value={form.material} onValueChange={(v) => setForm({ ...form, material: v })}>
                <SelectTrigger><SelectValue placeholder="Select material" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Aluminum 6061">Aluminum 6061</SelectItem>
                  <SelectItem value="Aluminum 7075">Aluminum 7075</SelectItem>
                  <SelectItem value="Steel 304">Steel 304</SelectItem>
                  <SelectItem value="Steel 316">Steel 316</SelectItem>
                  <SelectItem value="Brass">Brass</SelectItem>
                  <SelectItem value="Titanium">Titanium</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label>Quantity</label>
              <Input type="number" min={1} value={form.quantity} onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label>Precision tolerance</label>
              <Input placeholder="e.g., ±0.05 mm" value={form.tolerance} onChange={(e) => setForm({ ...form, tolerance: e.target.value })} />
            </div>
            <div>
              <label>Surface roughness</label>
              <Input placeholder="e.g., Ra 1.6 μm" value={form.roughness} onChange={(e) => setForm({ ...form, roughness: e.target.value })} />
            </div>
          </div>
          <div className="form-row">
            <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 8 }}>
              <Checkbox checked={form.part_marking} onCheckedChange={(v) => setForm({ ...form, part_marking: Boolean(v) })} id="pm" />
              <label htmlFor="pm">Part marking required</label>
            </div>
            <div>
              <label>Certification</label>
              <Select value={form.certification} onValueChange={(v) => setForm({ ...form, certification: v })}>
                <SelectTrigger><SelectValue placeholder="Certification" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="None">None</SelectItem>
                  <SelectItem value="ISO 9001">ISO 9001</SelectItem>
                  <SelectItem value="AS9100">AS9100</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <label>Notes</label>
            <Textarea rows={4} placeholder="Any additional instructions" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </div>
          <div>
            <label>Upload CAD (dxf, dwg, step, stp, iges, igs, stl, zip)</label>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input type="file" accept=".dxf,.dwg,.step,.stp,.iges,.igs,.stl,.zip" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              {file && <span>{file.name}</span>}
            </div>
          </div>
          <div className="form-actions">
            <Button type="submit"><FileUp size={16}/> Submit RFQ</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Offers() {
  const [rfqs, setRfqs] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [activeRfq, setActiveRfq] = useState("all");
  const load = async () => {
    try {
      const rfqRes = await api.get("/rfqs");
      setRfqs(rfqRes.data);
      const q = await api.get("/quotes" + (activeRfq !== "all" ? `?rfq_id=${activeRfq}` : ""));
      setQuotes(q.data);
    } catch (e) {
      // ignore
    }
  };
  useEffect(() => { load(); }, [activeRfq]);

  const accept = async (id) => {
    try {
      const res = await api.post(`/quotes/${id}/accept`);
      toast.success("Order created and pending payment");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed");
    }
  };

  return (
    <div>
      <div className="section-title">Offers</div>
      <div className="form" style={{ marginTop: 12 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
          <span>Filter by RFQ:</span>
          <Select value={activeRfq} onValueChange={setActiveRfq}>
            <SelectTrigger style={{ width: 260 }}><SelectValue placeholder="All" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {rfqs.map((r) => (
                <SelectItem key={r.id} value={r.id}>{r.material} × {r.quantity}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={load}><Download size={16}/> Refresh</Button>
        </div>
        <table className="table">
          <thead>
            <tr className="tr">
              <th className="th td">Supplier</th>
              <th className="th td">RFQ</th>
              <th className="th td">Price</th>
              <th className="th td">Lead time</th>
              <th className="th td">Notes</th>
              <th className="th td"></th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((q) => {
              const rfq = rfqs.find(r => r.id === q.rfq_id);
              return (
                <tr className="tr" key={q.id}>
                  <td className="td">{q.supplier_name}</td>
                  <td className="td">{rfq ? `${rfq.material} × ${rfq.quantity}` : q.rfq_id}</td>
                  <td className="td">€ {q.price.toFixed(2)}</td>
                  <td className="td">{q.lead_time_days} days</td>
                  <td className="td">{q.notes}</td>
                  <td className="td"><Button size="sm" onClick={() => accept(q.id)}>Accept</Button></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Requests() {
  const [rfqs, setRfqs] = useState([]);
  const load = async () => {
    try { const res = await api.get("/rfqs"); setRfqs(res.data);} catch {}
  };
  useEffect(() => { load(); }, []);
  return (
    <div>
      <div className="section-title">Requests</div>
      <div className="form" style={{ marginTop: 12 }}>
        <table className="table">
          <thead>
            <tr className="tr">
              <th className="th td">Created</th>
              <th className="th td">Material</th>
              <th className="th td">Qty</th>
              <th className="th td">Tolerance</th>
              <th className="th td">Roughness</th>
              <th className="th td">File</th>
            </tr>
          </thead>
          <tbody>
            {rfqs.map(r => (
              <tr className="tr" key={r.id}>
                <td className="td">{new Date(r.created_at).toLocaleString()}</td>
                <td className="td">{r.material}</td>
                <td className="td">{r.quantity}</td>
                <td className="td">{r.tolerance || "-"}</td>
                <td className="td">{r.roughness || "-"}</td>
                <td className="td">{r.cad_filename || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Orders() {
  const [orders, setOrders] = useState([]);
  const [rfqs, setRfqs] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const load = async () => {
    try {
      const o = await api.get("/orders");
      setOrders(o.data);
      const r = await api.get("/rfqs");
      setRfqs(r.data);
      const q = await api.get("/quotes");
      setQuotes(q.data);
    } catch {}
  };
  useEffect(() => { load(); }, []);
  const pay = async (id) => {
    try { await api.post(`/orders/${id}/pay`); toast.success("Payment recorded"); load(); } catch (e) { toast.error("Payment failed"); }
  }
  return (
    <div>
      <div className="section-title">Orders</div>
      <div className="form" style={{ marginTop: 12 }}>
        <table className="table">
          <thead>
            <tr className="tr">
              <th className="th td">Order</th>
              <th className="th td">RFQ</th>
              <th className="th td">Supplier</th>
              <th className="th td">Price</th>
              <th className="th td">Status</th>
              <th className="th td"></th>
            </tr>
          </thead>
          <tbody>
            {orders.map(o => {
              const quote = quotes.find(q => q.id === o.quote_id);
              const rfq = rfqs.find(r => r.id === o.rfq_id);
              return (
                &lt;tr className="tr" key={o.id}&gt;
                  &lt;td className="td"&gt;{o.id.slice(0,8)}&lt;/td&gt;
                  &lt;td className="td"&gt;{rfq ? `${rfq.material} × ${rfq.quantity}` : o.rfq_id}&lt;/td&gt;
                  &lt;td className="td"&gt;{quote ? quote.supplier_name : o.quote_id}&lt;/td&gt;
                  &lt;td className="td"&gt;{quote ? `€ ${quote.price.toFixed(2)}` : "-"}&lt;/td&gt;
                  &lt;td className="td"&gt;{o.status}&lt;/td&gt;
                  &lt;td className="td"&gt;{o.status === 'pending_payment' ? &lt;Button size="sm" onClick={() => pay(o.id)}&gt;Pay now&lt;/Button&gt; : null}&lt;/td&gt;
                &lt;/tr&gt;
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Payments() {
  const [payments, setPayments] = useState([]);
  const load = async () => { try { const p = await api.get("/payments"); setPayments(p.data);} catch {} };
  useEffect(() => { load(); }, []);
  return (
    <div>
      <div className="section-title">Payments</div>
      <div className="form" style={{ marginTop: 12 }}>
        <table className="table">
          <thead>
            <tr className="tr">
              <th className="th td">Created</th>
              <th className="th td">Order</th>
              <th className="th td">Amount</th>
              <th className="th td">Status</th>
            </tr>
          </thead>
          <tbody>
            {payments.map(p => (
              &lt;tr className="tr" key={p.id}&gt;
                &lt;td className="td"&gt;{new Date(p.created_at).toLocaleString()}&lt;/td&gt;
                &lt;td className="td"&gt;{p.order_id.slice(0,8)}&lt;/td&gt;
                &lt;td className="td"&gt;€ {p.amount.toFixed(2)}&lt;/td&gt;
                &lt;td className="td"&gt;{p.status}&lt;/td&gt;
              &lt;/tr&gt;
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AppShell() {
  const { user, setUser } = useAuth();
  const onLogout = () => { localStorage.removeItem("token"); setUser(null); window.location.href = "/"; };

  return (
    <div className="app-shell">
      <Navbar user={user} onLogout={onLogout} />
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "16px 20px" }}>
        &lt;Routes&gt;
          &lt;Route path="/" element={&lt;Home /&gt;} /&gt;
          &lt;Route path="/register" element={&lt;Register /&gt;} /&gt;
          &lt;Route path="/login" element={&lt;Login onLogin={() => {}} /&gt;} /&gt;
          &lt;Route path="/rfq/new" element={&lt;RFQNew /&gt;} /&gt;
          &lt;Route path="/requests" element={&lt;Requests /&gt;} /&gt;
          &lt;Route path="/offers" element={&lt;Offers /&gt;} /&gt;
          &lt;Route path="/orders" element={&lt;Orders /&gt;} /&gt;
          &lt;Route path="/payments" element={&lt;Payments /&gt;} /&gt;
        &lt;/Routes&gt;
      </div>
      <footer className="footer"><div className="footer-inner"><span>© {new Date().getFullYear()} Part Aggregator</span><span>Made for milling RFQs</span></div></footer>
      <Toaster richColors position="top-right" />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;