import pytest
import asyncio
import random
import time

# Adjust these imports to match your folder structure
from harmony.tests.utils import AppClient, SimConfig, SimState, SafeMetrics, ACTION_REGISTRY

# ==========================================
# CONFIGURATION
# ==========================================
# class StressConfig:
#     SIM_CONFIG = SimConfig(
#         MAX_USERS=50,  # Max users *per worker*
#     )
#     DURATION_SECONDS: int = 30
#     CONCURRENT_WORKERS: int = 50
#     VERBOSE_ERRORS: bool = True
#     MONITOR_INTERVAL: int = 2 

class StressConfig:
    SIM_CONFIG = SimConfig(
        MAX_USERS=1,  # Max users *per worker*
    )
    DURATION_SECONDS: int = 30
    CONCURRENT_WORKERS: int = 1
    VERBOSE_ERRORS: bool = True
    MONITOR_INTERVAL: int = 2 

# ==========================================
# WORKER & MONITOR
# ==========================================
async def periodic_monitor(metrics: SafeMetrics, stop_event: asyncio.Event):
    """Prints metrics to console every few seconds."""
    start_time = time.time()
    while not stop_event.is_set():
        await asyncio.sleep(StressConfig.MONITOR_INTERVAL)
        elapsed = time.time() - start_time
        summary = await metrics.get_summary_str()
        print(f"[{elapsed:.1f}s] {summary}")

async def independent_worker(
    worker_id: int, 
    stop_event: asyncio.Event, 
    client: AppClient, 
    metrics: SafeMetrics
):
    """
    Runs an isolated simulation scenario.
    Owns its own SimState, so no locking with other workers needed.
    """
    # 1. Setup Local State
    local_state = SimState(config=StressConfig.SIM_CONFIG)
    
    # 2. Pre-seed: Ensure we have at least one user to start so we don't spin empty loops
    #    (Calling the action function directly requires bypassing the decorator wrapper if strictly typed, 
    #     but usually calling registry func is safer)
    await ACTION_REGISTRY["create_user"]["func"](client, local_state)

    # 3. Prepare Weights (optimization)
    action_names = list(ACTION_REGISTRY.keys())
    action_weights = [ACTION_REGISTRY[k]['weight'] for k in action_names]

    # 4. Loop
    while not stop_event.is_set():
        # Pick Action
        chosen_name = random.choices(action_names, weights=action_weights, k=1)[0]
        action_def = ACTION_REGISTRY[chosen_name]
        
        start = time.time()
        try:
            await action_def['func'](client, local_state)
            latency = time.time() - start
            await metrics.record(chosen_name, latency, error=False)
            
        except Exception as e:
            latency = time.time() - start
            await metrics.record(chosen_name, latency, error=True)
            
            if StressConfig.VERBOSE_ERRORS:
                print(f"[Worker-{worker_id}] [{chosen_name}] Failed: {e}")

        # Slight yield to let other tasks breathe
        await asyncio.sleep(0)

# ==========================================
# MAIN TEST
# ==========================================
@pytest.mark.stress
@pytest.mark.asyncio
async def test_stress_simulation(app_client: AppClient):
    print(f"\n--- Starting Stress Test ({StressConfig.CONCURRENT_WORKERS} Workers) ---")
    
    stop_event = asyncio.Event()
    metrics = SafeMetrics()
    
    # 1. Create Workers
    workers = [
        asyncio.create_task(independent_worker(i, stop_event, app_client, metrics))
        for i in range(StressConfig.CONCURRENT_WORKERS)
    ]
    
    # 2. Create Monitor
    monitor = asyncio.create_task(periodic_monitor(metrics, stop_event))

    # 3. Run for Duration
    print(f"Running for {StressConfig.DURATION_SECONDS} seconds...")
    await asyncio.sleep(StressConfig.DURATION_SECONDS)
    
    # 4. Shutdown
    print("Stopping...")
    stop_event.set()
    
    # Wait for workers to finish current task
    await asyncio.gather(*workers)
    
    # Stop monitor
    await monitor
    
    # 5. Report
    await metrics.final_report()