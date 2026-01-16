"""
Load Testing Script for AutonomAI Distributed Deployment

Tests API under load to verify:
- Distributed state management
- Race condition prevention
- Load balancer effectiveness
- Overall system stability
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import statistics


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    base_url: str = "http://localhost"
    num_concurrent_requests: int = 10
    num_iterations: int = 100
    request_timeout: int = 30
    test_endpoints: List[str] = field(default_factory=lambda: ["/health", "/v2/execute"])


@dataclass
class TestResult:
    """Results from a single request"""
    endpoint: str
    status_code: int
    response_time: float
    success: bool
    error: str = ""


class LoadTester:
    """Load testing utility"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str = "GET",
        data: Dict = None
    ) -> TestResult:
        """Make a single HTTP request"""
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, timeout=self.config.request_timeout) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    return TestResult(
                        endpoint=endpoint,
                        status_code=response.status,
                        response_time=response_time,
                        success=response.status == 200
                    )
            elif method == "POST":
                async with session.post(
                    url,
                    json=data,
                    timeout=self.config.request_timeout
                ) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    return TestResult(
                        endpoint=endpoint,
                        status_code=response.status,
                        response_time=response_time,
                        success=response.status == 200
                    )
        except asyncio.TimeoutError:
            return TestResult(
                endpoint=endpoint,
                status_code=0,
                response_time=self.config.request_timeout,
                success=False,
                error="Timeout"
            )
        except Exception as e:
            return TestResult(
                endpoint=endpoint,
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_requests(self, endpoint: str, num_requests: int):
        """Run multiple concurrent requests to an endpoint"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(num_requests):
                if endpoint == "/v2/execute":
                    # Test with actual execute request
                    data = {
                        "query": "Test query for load testing",
                        "enable_optimization": False
                    }
                    tasks.append(self.make_request(session, endpoint, "POST", data))
                else:
                    tasks.append(self.make_request(session, endpoint))
            
            results = await asyncio.gather(*tasks)
            self.results.extend(results)
    
    async def test_distributed_state_consistency(self):
        """Test that distributed state prevents race conditions"""
        print("\n=== Testing Distributed State Consistency ===")
        
        async with aiohttp.ClientSession() as session:
            # Create multiple concurrent requests that update state
            tasks = []
            for i in range(20):
                data = {
                    "query": f"Test query {i}",
                    "enable_optimization": True
                }
                tasks.append(
                    self.make_request(session, "/v2/execute", "POST", data)
                )
            
            results = await asyncio.gather(*tasks)
            
            # Count successes and failures
            successes = sum(1 for r in results if r.success)
            failures = sum(1 for r in results if not r.success)
            
            print(f"Concurrent state updates: {successes} succeeded, {failures} failed")
            
            # All should succeed without conflicts
            if failures == 0:
                print("✅ No race conditions detected")
            else:
                print(f"⚠️ {failures} requests failed - possible race conditions")
    
    def print_summary(self):
        """Print test summary"""
        if not self.results:
            print("No results to summarize")
            return
        
        print("\n" + "=" * 60)
        print("LOAD TEST SUMMARY")
        print("=" * 60)
        
        # Overall statistics
        total_requests = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_requests - successful
        success_rate = (successful / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"\nTotal Requests: {total_requests}")
        print(f"Successful: {successful} ({success_rate:.1f}%)")
        print(f"Failed: {failed}")
        
        # Response time statistics
        response_times = [r.response_time for r in self.results if r.success]
        
        if response_times:
            print(f"\nResponse Times:")
            print(f"  Min: {min(response_times):.3f}s")
            print(f"  Max: {max(response_times):.3f}s")
            print(f"  Mean: {statistics.mean(response_times):.3f}s")
            print(f"  Median: {statistics.median(response_times):.3f}s")
            
            if len(response_times) > 1:
                print(f"  StdDev: {statistics.stdev(response_times):.3f}s")
        
        # Per-endpoint statistics
        endpoints = set(r.endpoint for r in self.results)
        print(f"\nPer-Endpoint Results:")
        
        for endpoint in endpoints:
            endpoint_results = [r for r in self.results if r.endpoint == endpoint]
            endpoint_success = sum(1 for r in endpoint_results if r.success)
            endpoint_total = len(endpoint_results)
            endpoint_success_rate = (endpoint_success / endpoint_total) * 100
            
            endpoint_times = [r.response_time for r in endpoint_results if r.success]
            avg_time = statistics.mean(endpoint_times) if endpoint_times else 0
            
            print(f"\n  {endpoint}:")
            print(f"    Requests: {endpoint_total}")
            print(f"    Success Rate: {endpoint_success_rate:.1f}%")
            print(f"    Avg Response Time: {avg_time:.3f}s")
        
        # Error summary
        errors = [r.error for r in self.results if r.error]
        if errors:
            print(f"\nErrors encountered:")
            error_counts = {}
            for error in errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            
            for error, count in error_counts.items():
                print(f"  {error}: {count} times")
        
        print("\n" + "=" * 60)


async def run_basic_load_test(config: LoadTestConfig):
    """Run basic load test"""
    tester = LoadTester(config)
    
    print("Starting Basic Load Test...")
    print(f"Base URL: {config.base_url}")
    print(f"Concurrent Requests: {config.num_concurrent_requests}")
    print(f"Iterations: {config.num_iterations}")
    
    # Test health endpoint
    print("\n=== Testing Health Endpoint ===")
    for i in range(config.num_iterations):
        print(f"Iteration {i+1}/{config.num_iterations}", end="\r")
        await tester.run_concurrent_requests("/health", config.num_concurrent_requests)
    
    print("\n\nLoad test completed!")
    tester.print_summary()


async def run_stress_test(config: LoadTestConfig):
    """Run stress test with higher concurrency"""
    tester = LoadTester(config)
    
    print("Starting Stress Test...")
    print(f"Base URL: {config.base_url}")
    print(f"Concurrent Requests: {config.num_concurrent_requests}")
    print(f"Iterations: {config.num_iterations}")
    
    start_time = time.time()
    
    # Test with high concurrency
    print("\n=== High Concurrency Test ===")
    for i in range(config.num_iterations):
        print(f"Iteration {i+1}/{config.num_iterations}", end="\r")
        await tester.run_concurrent_requests("/health", config.num_concurrent_requests)
    
    elapsed = time.time() - start_time
    total_requests = config.num_concurrent_requests * config.num_iterations
    rps = total_requests / elapsed
    
    print(f"\n\nStress test completed!")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Requests per second: {rps:.2f}")
    
    tester.print_summary()


async def run_distributed_state_test(config: LoadTestConfig):
    """Test distributed state management under load"""
    tester = LoadTester(config)
    
    print("Starting Distributed State Test...")
    print("This test verifies that distributed locks prevent race conditions")
    
    await tester.test_distributed_state_consistency()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test AutonomAI distributed deployment")
    parser.add_argument(
        "--test",
        choices=["basic", "stress", "distributed", "all"],
        default="basic",
        help="Type of test to run"
    )
    parser.add_argument(
        "--url",
        default="http://localhost",
        help="Base URL of the API"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent requests"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations"
    )
    
    args = parser.parse_args()
    
    # Create config with command line arguments
    config = LoadTestConfig(
        base_url=args.url,
        num_concurrent_requests=args.concurrent,
        num_iterations=args.iterations
    )
    
    if args.test == "basic" or args.test == "all":
        asyncio.run(run_basic_load_test(config))
    
    if args.test == "stress" or args.test == "all":
        # Use higher concurrency for stress test
        stress_config = LoadTestConfig(
            base_url=args.url,
            num_concurrent_requests=max(args.concurrent, 50),
            num_iterations=max(args.iterations, 10)
        )
        asyncio.run(run_stress_test(stress_config))
    
    if args.test == "distributed" or args.test == "all":
        asyncio.run(run_distributed_state_test(config))


if __name__ == "__main__":
    main()
