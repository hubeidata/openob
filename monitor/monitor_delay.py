import redis
import time
import sys
import argparse

def monitor(redis_host, link_name):
    print(f"Connecting to Redis at {redis_host} for link '{link_name}'...")
    try:
        r = redis.Redis(host=redis_host, decode_responses=True)
        r.ping()
        print("Connected.")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return

    stats_key = f"openob:{link_name}:stats"
    vu_key = f"openob:{link_name}:vu:tx"

    print(f"Monitoring keys: {stats_key} (stats) and {vu_key} (audio)...")
    print("-" * 50)
    print(f"{'Time':<10} | {'RTT (ms)':<10} | {'Loss':<6} | {'Jitter':<8} | {'Audio (L/R)'}")
    print("-" * 50)

    try:
        while True:
            # Fetch stats
            stats = r.hgetall(stats_key)
            # Fetch VU (just to show activity)
            vu = r.hgetall(vu_key)

            if not stats:
                rtt = "N/A"
                loss = "-"
                jitter = "-"
            else:
                try:
                    rtt_val = float(stats.get('rtt_ms', 0))
                    rtt = f"{rtt_val:.2f}"
                except:
                    rtt = str(stats.get('rtt_ms', '?'))
                loss = stats.get('loss', '-')
                jitter = stats.get('jitter', '-')

            if not vu:
                audio = "No Signal"
            else:
                l = vu.get('left_db', '-inf')
                r_lvl = vu.get('right_db', '-inf')
                audio = f"{l} / {r_lvl}"

            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp:<10} | {rtt:<10} | {loss:<6} | {jitter:<8} | {audio}")

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nStopping monitor.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor OpenOB Link Delay/Stats")
    parser.add_argument("link_name", help="Name of the OpenOB link to monitor")
    parser.add_argument("--host", default="localhost", help="Redis host (default: localhost)")
    
    args = parser.parse_args()
    
    monitor(args.host, args.link_name)
