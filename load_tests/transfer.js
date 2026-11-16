import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

export const errorRate = new Counter('transfer_errors');
export const transferLatency = new Trend('transfer_latency_ms');
export const options = {
  scenarios: { concorrencia: { executor: 'constant-vus', vus: 50, duration: '15s' } },
};
const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export function setup() {
  const ts = Date.now();
  const create = (owner, balance) => {
    const res = http.post(`${BASE}/accounts`, JSON.stringify({ owner, initial_balance: balance }),
      { headers: { 'Content-Type': 'application/json' } });
    if (res.status !== 201) throw new Error(`Falha ao criar conta: ${res.body}`);
    return res.json().id;
  };
  return { source: create(`Carga-origem-${ts}`, '1000000.00'), destination: create(`Carga-destino-${ts}`, '0') };
}

export default function (data) {
  const key = `${__VU}-${__ITER}-${Date.now()}`;
  const payload = JSON.stringify({ origin_id: data.source, destination_id: data.destination, amount: '0.01' });
  const response = http.post(`${BASE}/transfers`, payload,
    { headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key } });
  const ok = check(response, { 'transferência HTTP 201': r => r.status === 201 });
  if (!ok) errorRate.add(1);
  transferLatency.add(response.timings.duration);
  sleep(0.1);
}
