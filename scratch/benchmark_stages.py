import time
import requests
import re

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

print("=" * 60)
print("BENCHMARKING PIPELINE STAGES ACROSS PORTAL & AUTOMATION")
print("=" * 60)

# Stage E: Network Latency (Ping / TCP Round Trip)
t0 = time.time()
res = s.get("https://generate.snsies.com/login")
stage_e_latency = round((time.time() - t0) * 1000, 1)
print(f"Stage E (Network Latency - HTTPS RTT): {stage_e_latency} ms")

# Stage F: Authentication / Session Setup
t0 = time.time()
csrf = re.search(r'name="_token"\s+value="([^"]+)"', res.text).group(1)
s.post("https://generate.snsies.com/login", data={
    '_token': csrf,
    'email': 'admin@kmltodata.local',
    'password': 'Admin@12345',
    'remember': '1'
})
stage_f_auth = round((time.time() - t0) * 1000, 1)
print(f"Stage F (Auth / Session Setup): {stage_f_auth} ms")

# Stage B: Search via Direct HTTP
t0 = time.time()
s_res = s.get("https://generate.snsies.com/?q=511489")
stage_b_http = round((time.time() - t0) * 1000, 1)
print(f"Stage B (Village Search via Direct HTTP): {stage_b_http} ms")

# Stage D: URL Detection via Direct Regex Parsing
t0 = time.time()
rev_match = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', s_res.text)
detected_url = rev_match.group(1) if rev_match else None
stage_d_regex = round((time.time() - t0) * 1000, 3)
print(f"Stage D (URL Detection via HTTP parse): {stage_d_regex} ms -> {detected_url}")

# Now let's benchmark 10 villages sequentially via Direct HTTP to measure throughput
test_samples = [
    ("511639", "Bharkunda"),
    ("511489", "Bhankoda"),
    ("511868", "Dhadhodar"),
    ("511854", "Shahpur"),
    ("516239", "Savainagar"),
    ("511852", "Pipariya"),
    ("511850", "Nabhoi"),
    ("511851", "Amipura"),
    ("511853", "Aniyali Bhimji"),
    ("511860", "Ashoknagar")
]

print("\n--- Benchmarking 10 Villages via Direct HTTP (Sequential) ---")
t_seq = time.time()
for code, name in test_samples:
    t_v = time.time()
    r = s.get(f"https://generate.snsies.com/?q={code}")
    m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', r.text)
    u = m.group(1) if m else "PENDING"
    print(f"  {name} ({code}) -> {u} in {round((time.time()-t_v)*1000, 1)} ms")
total_seq = round(time.time() - t_seq, 2)
avg_seq = round(total_seq / len(test_samples), 3)
print(f"Sequential Total: {total_seq}s | Avg: {avg_seq}s per village | Throughput: {round(60/avg_seq, 1)} villages/min")

# Now let's benchmark the SAME 10 villages via Concurrent HTTP Threads (10 workers)
from concurrent.futures import ThreadPoolExecutor

print("\n--- Benchmarking 10 Villages via Concurrent HTTP (10 Workers) ---")
def fetch_village(item):
    code, name = item
    t_item = time.time()
    r = s.get(f"https://generate.snsies.com/?q={code}")
    m = re.search(r'href="(https://generate\.snsies\.com/villages/\d+/review)"', r.text)
    u = m.group(1) if m else "PENDING"
    return code, name, u, round((time.time() - t_item) * 1000, 1)

t_par = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(fetch_village, test_samples))
total_par = round(time.time() - t_par, 2)
avg_par = round(total_par / len(test_samples), 3)
print(f"Parallel Total (10 workers): {total_par}s | Avg: {avg_par}s per village | Throughput: {round(60/avg_par, 1)} villages/min")
for c, n, u, d in results:
    print(f"  {n} ({c}) in {d} ms -> {u}")
