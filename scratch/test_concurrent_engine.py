import time
from concurrent.futures import ThreadPoolExecutor
from test_hybrid_engine import DirectPortalClient

user_codes = [
    ("511624", "Changodar (Og)"),
    ("511476", "Hathipura"),
    ("511635", "Huka"),
    ("511910", "Kothadiya"),
    ("511494", "Panar"),
    ("511919", "Parabdi"),
    ("511750", "Vejalka"),
    ("516997", "Bhurakui"),
    ("516890", "Gangapura"),
    ("516994", "Shahpur"),
    ("516979", "Shekhadi"),
    ("510916", "Chumfari"),
    ("510894", "Patyo"),
    ("510967", "Sardarkhantni Muvadi"),
    ("507435", "Bharadava"),
    ("507910", "Jalana"),
    ("508112", "Jorapura Bhakhar"),
    ("507962", "Kanagar"),
    ("507814", "Tadholi"),
    ("522275", "Debar"),
    ("522522", "Nikoli"),
    ("522190", "Prankad"),
    ("522073", "Thikaria"),
    ("516536", "Hathsani"),
    ("516102", "Nava Rampar"),
    ("520789", "Anandpura"),
    ("520103", "Dabherai"),
    ("520181", "Dharoliya Bhindol"),
    ("520791", "Gola Gamdi"),
    ("520113", "Nana Butiyapura")
]

# Create thread-local clients or one client per worker thread
clients = {}

def get_client(worker_id):
    if worker_id not in clients:
        c = DirectPortalClient("https://generate.snsies.com/", "admin@kmltodata.local", "Admin@12345")
        c.login()
        clients[worker_id] = c
    return clients[worker_id]

# Pre-authenticate 5 clients
print("Logging in 5 worker clients...")
for i in range(5):
    get_client(i)
print("5 worker clients ready.")

def process_item(args):
    idx, item = args
    worker_id = idx % 5
    client = get_client(worker_id)
    code, name = item
    return client.process_village(name, code)

print("\nStarting concurrent run with 5 workers on 30 villages...")
t_start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_item, enumerate(user_codes)))
total_time = time.time() - t_start

successes = sum(1 for r in results if r['status'] == 'SUCCESS')
avg_time = round(total_time / len(user_codes), 3)
throughput = round(len(user_codes) / (total_time / 60), 1)

print("\n" + "=" * 60)
print(f"BENCHMARK RESULTS (5 WORKERS):")
print(f"Total Villages: {len(user_codes)}")
print(f"Successes: {successes} | Failures: {len(user_codes) - successes}")
print(f"Total Execution Time: {round(total_time, 2)} seconds")
print(f"Average Time per Village: {avg_time} seconds ({round(avg_time * 1000, 1)} ms)")
print(f"Throughput: {throughput} villages / minute")
print("=" * 60)
