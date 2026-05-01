#!/usr/bin/env python3
"""
Simulation script for RDBMS outage cascade scenario
Run with: python backend/scripts/simulate_failure.py
"""

import asyncio
import httpx
import time
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_color(text, color=Colors.RESET):
    print(f"{color}{text}{Colors.RESET}")

async def send_signal(client, component_id, error_type, severity):
    """Send a single signal"""
    try:
        response = await client.post(
            f"{API_BASE}/signals",
            json={
                "component_id": component_id,
                "error_type": error_type,
                "severity": severity,
                "timestamp": time.time()
            },
            timeout=5.0
        )
        return response.status_code == 202
    except Exception as e:
        print_color(f"   Error sending signal: {e}", Colors.RED)
        return False

async def check_health():
    """Check if backend is healthy before starting"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health", timeout=5.0)
            if response.status_code == 200:
                return True
    except:
        pass
    return False

async def get_metrics():
    """Get current metrics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/signals/metrics", timeout=5.0)
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

async def simulate_rdbms_cascade():
    """Simulate RDBMS outage causing downstream cascade"""
    print_color("=" * 70, Colors.CYAN)
    print_color("🚨 RDBMS OUTAGE CASCADE SIMULATION", Colors.BOLD + Colors.RED)
    print_color("=" * 70, Colors.CYAN)
    
    # Check health first
    print_color("\n📡 Checking backend health...", Colors.BLUE)
    if not await check_health():
        print_color("❌ Backend is not healthy. Make sure docker-compose up is running.", Colors.RED)
        print("   Run: docker-compose up -d")
        sys.exit(1)
    print_color("✅ Backend is healthy!", Colors.GREEN)
    
    # Get initial metrics
    initial_metrics = await get_metrics()
    if initial_metrics:
        print_color(f"\n📊 Initial metrics:", Colors.BLUE)
        print(f"   Total signals: {initial_metrics.get('total_signals_received', 0)}")
        print(f"   Work items: {initial_metrics.get('work_items_created', 0)}")
    
    async with httpx.AsyncClient() as client:
        
        # Phase 1: RDBMS fails - send 120 signals over 8 seconds
        print_color("\n" + "=" * 70, Colors.YELLOW)
        print_color("📡 PHASE 1: RDBMS_PRIMARY Failure", Colors.BOLD + Colors.YELLOW)
        print_color("   Sending 120 signals over 8 seconds", Colors.YELLOW)
        print_color("   Expected: 1 work item (debounced)", Colors.YELLOW)
        print_color("=" * 70, Colors.YELLOW)
        
        signals_sent = 0
        start_time = time.time()
        
        for i in range(120):
            success = await send_signal(client, "RDBMS_PRIMARY", "CONNECTION_REFUSED", "P0")
            if success:
                signals_sent += 1
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print_color(f"   📨 Sent {i + 1}/120 signals...", Colors.CYAN)
            
            # Spread over 8 seconds (120 signals / 8 seconds = 15 signals/sec)
            await asyncio.sleep(0.066)
        
        elapsed = time.time() - start_time
        print_color(f"\n   ✅ Phase 1 complete: {signals_sent} signals sent in {elapsed:.1f} seconds", Colors.GREEN)
        
        # Wait for processing
        print_color("\n⏳ Waiting 3 seconds for debounce processing...", Colors.BLUE)
        await asyncio.sleep(3)
        
        # Show metrics after phase 1
        metrics = await get_metrics()
        if metrics:
            print_color(f"\n📊 After Phase 1:", Colors.BLUE)
            print(f"   Work items created: {metrics.get('work_items_created', 0)}")
            print(f"   Signals debounced: {metrics.get('signals_debounced', 0)}")
        
        # Phase 2: MCP hosts start failing
        print_color("\n" + "=" * 70, Colors.YELLOW)
        print_color("📡 PHASE 2: MCP_HOST_01 Cascade Failure", Colors.BOLD + Colors.YELLOW)
        print_color("   Sending 50 signals (simulating upstream timeout)", Colors.YELLOW)
        print_color("=" * 70, Colors.YELLOW)
        
        signals_sent = 0
        for i in range(50):
            success = await send_signal(client, "MCP_HOST_01", "UPSTREAM_TIMEOUT", "P1")
            if success:
                signals_sent += 1
            
            if (i + 1) % 10 == 0:
                print_color(f"   📨 Sent {i + 1}/50 signals...", Colors.CYAN)
            
            await asyncio.sleep(0.1)
        
        print_color(f"\n   ✅ Phase 2 complete: {signals_sent} signals sent", Colors.GREEN)
        await asyncio.sleep(2)
        
        # Phase 3: Cache cluster degradation
        print_color("\n" + "=" * 70, Colors.YELLOW)
        print_color("📡 PHASE 3: CACHE_CLUSTER Degradation", Colors.BOLD + Colors.YELLOW)
        print_color("   Sending 20 signals (simulating slow responses)", Colors.YELLOW)
        print_color("=" * 70, Colors.YELLOW)
        
        signals_sent = 0
        for i in range(20):
            success = await send_signal(client, "CACHE_CLUSTER", "SLOW_RESPONSE", "P2")
            if success:
                signals_sent += 1
            
            if (i + 1) % 5 == 0:
                print_color(f"   📨 Sent {i + 1}/20 signals...", Colors.CYAN)
            
            await asyncio.sleep(0.2)
        
        print_color(f"\n   ✅ Phase 3 complete: {signals_sent} signals sent", Colors.GREEN)
        
        # Final metrics
        await asyncio.sleep(3)
        final_metrics = await get_metrics()
        
        # Final summary
        print_color("\n" + "=" * 70, Colors.CYAN)
        print_color("📊 SIMULATION COMPLETE - FINAL METRICS", Colors.BOLD + Colors.GREEN)
        print_color("=" * 70, Colors.CYAN)
        
        if final_metrics:
            print(f"\n  📈 Total Signals Received: {final_metrics.get('total_signals_received', 0)}")
            print(f"  🏗️  Work Items Created: {final_metrics.get('work_items_created', 0)}")
            print(f"  🔄 Signals Debounced: {final_metrics.get('signals_debounced', 0)}")
            print(f"  📊 Queue Depth: {final_metrics.get('queue_depth', 0)}")
            print(f"  💾 Dropped Signals: {final_metrics.get('dropped_signals', 0)}")
        
        print_color("\n" + "=" * 70, Colors.GREEN)
        print_color("✅ VERIFICATION CHECKLIST:", Colors.BOLD)
        print_color("=" * 70, Colors.GREEN)
        print("  □ RDBMS_PRIMARY: 120 signals → 1 work item (debounced)")
        print("  □ MCP_HOST_01: 50 signals → work item created")
        print("  □ CACHE_CLUSTER: 20 signals → work item created")
        print("  □ P0 Alert triggered for RDBMS (should see WAR ROOM message)")
        print("  □ P1 Alert triggered for MCP (on-call paged)")
        print("  □ P2 Alert triggered for Cache (Slack only)")
        
        print_color("\n🌐 Open the dashboard: http://localhost:3000", Colors.CYAN)
        print_color("   Check Active Incidents to see created work items\n", Colors.CYAN)

async def main():
    try:
        await simulate_rdbms_cascade()
    except KeyboardInterrupt:
        print_color("\n\n⚠️ Simulation interrupted by user", Colors.YELLOW)
    except Exception as e:
        print_color(f"\n❌ Simulation failed: {e}", Colors.RED)

if __name__ == "__main__":
    asyncio.run(main())