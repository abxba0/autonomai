"""
Integration Test for Batch Processing API

Tests the batch processing API endpoints integrated into API v2.
"""

import sys
import os
import time
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_api_health():
    """Test API health endpoint"""
    print("\nTesting API health endpoint...")
    
    response = requests.get("http://localhost:8000/v2/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API is healthy: {data['status']}")
        print(f"  Version: {data['version']}")
        return True
    else:
        print(f"✗ API health check failed: {response.status_code}")
        return False


def test_batch_submit():
    """Test batch job submission"""
    print("\nTesting batch job submission...")
    
    # Submit a simple batch job
    job_data = {
        "job_type": "failure_optimization",
        "tasks": [
            {
                "failure_description": "Test failure 1",
                "severity": "low",
            },
            {
                "failure_description": "Test failure 2",
                "severity": "moderate",
            },
        ],
        "max_workers": 2,
        "priority": 1,
    }
    
    response = requests.post(
        "http://localhost:8000/v2/batch/submit",
        json=job_data,
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Job submitted successfully: {data['job_id']}")
        print(f"  Status: {data['status']}")
        print(f"  Tasks: {data['tasks_count']}")
        return data['job_id']
    else:
        print(f"✗ Job submission failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def test_batch_status(job_id):
    """Test getting batch job status"""
    print(f"\nTesting batch job status for {job_id}...")
    
    response = requests.get(f"http://localhost:8000/v2/batch/{job_id}/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Job status retrieved: {data['status']}")
        if data.get('progress'):
            progress = data['progress']
            print(f"  Progress: {progress['progress_percent']:.1f}%")
            print(f"  Completed: {progress['completed_tasks']}/{progress['total_tasks']}")
        return True
    else:
        print(f"✗ Status retrieval failed: {response.status_code}")
        return False


def test_batch_list():
    """Test listing batch jobs"""
    print("\nTesting batch job listing...")
    
    response = requests.get("http://localhost:8000/v2/batch/jobs?limit=10")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Jobs listed successfully: {data['total']} jobs")
        
        for job in data['jobs'][:3]:  # Show first 3
            print(f"  - {job['job_id']}: {job['status']} ({job['job_type']})")
        
        return True
    else:
        print(f"✗ Job listing failed: {response.status_code}")
        return False


def test_batch_stats():
    """Test batch statistics"""
    print("\nTesting batch statistics...")
    
    response = requests.get("http://localhost:8000/v2/batch/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Statistics retrieved: {data['total_jobs']} total jobs")
        
        if data.get('by_status'):
            print("  By status:")
            for status, count in data['by_status'].items():
                print(f"    {status}: {count}")
        
        return True
    else:
        print(f"✗ Statistics retrieval failed: {response.status_code}")
        return False


def main():
    """Run integration tests"""
    print("=" * 60)
    print("Batch Processing API Integration Tests")
    print("=" * 60)
    print("\nNOTE: API server must be running on http://localhost:8000")
    print("Start with: python web/api_v2.py")
    
    try:
        # Test API health
        if not test_api_health():
            print("\n✗ API is not running. Please start it with: python web/api_v2.py")
            return False
        
        # Test batch endpoints
        job_id = test_batch_submit()
        
        if job_id:
            time.sleep(1)  # Brief pause
            test_batch_status(job_id)
        
        test_batch_list()
        test_batch_stats()
        
        print("\n" + "=" * 60)
        print("✓ All integration tests passed!")
        print("=" * 60)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to API server.")
        print("Please start the API with: python web/api_v2.py")
        return False
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
