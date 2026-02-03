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
    print(f"{'Time':<10} | {'RTCP':<5} | {'RTT (ms)':<10} | {'Loss':<6} | {'Jitter':<8} | {'Audio (L/R)'}")
    print("-" * 80)

    try:
        while True:
            # Fetch stats and TTL (stats expire quickly)
            stats = r.hgetall(stats_key)
            stats_ttl = r.ttl(stats_key)
            # Fetch VU (just to show activity)
            vu = r.hgetall(vu_key)

            if stats and stats_ttl and stats_ttl > 0:
                # Parse numbers safely
                try:
                    rtt_val = float(stats.get('rtt_ms', 0))
                    rtt = f"{rtt_val:.2f}"
                except Exception:
                    rtt = str(stats.get('rtt_ms', '?'))

                loss_val = stats.get('loss')
                loss = str(loss_val) if loss_val is not None and str(loss_val) != "-1" else '-'

                jitter_val = stats.get('jitter')
                try:
                    jitter = f"{float(jitter_val):.2f}" if jitter_val is not None and str(jitter_val) != "-1" else '-'
                except Exception:
                    jitter = str(jitter_val) if jitter_val is not None else '-'

                rtcp = 'YES'
            else:
                rtt = "N/A"
                loss = "-"
                jitter = "-"
                rtcp = 'NO'

            if not vu:
                audio = "No Signal"
            else:
                try:
                    l = float(vu.get('left_db', 'nan'))
                    r_lvl = float(vu.get('right_db', 'nan'))
                    audio = f"{l:.2f} / {r_lvl:.2f}"
                except Exception:
                    audio = f"{vu.get('left_db', '-')} / {vu.get('right_db', '-') }"

            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp:<10} | {rtcp:<5} | {rtt:<10} | {loss:<6} | {jitter:<8} | {audio}")

            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nStopping monitor.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor OpenOB Link Delay/Stats")
    parser.add_argument("link_name", help="Name of the OpenOB link to monitor")
    parser.add_argument("--host", default="localhost", help="Redis host (default: localhost)")
    
    args = parser.parse_args()
    
    monitor(args.host, args.link_name)
