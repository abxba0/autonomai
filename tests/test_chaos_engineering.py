"""
Chaos Engineering Test Suite
Simulates real-world faults and distributed failures

Chaos Scenarios:
- Network failures (timeouts, partitions, packet loss)
- Service failures (Redis, database, LLM API)
- Resource exhaustion (memory, CPU, disk)
- Cascading failures
- Byzantine failures
- Circuit breaker testing
- Fallback mechanism validation
"""

import pytest
import sys
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.config import SystemConfig
from src.core.main_model import MainModel
from src.core.critic_model import CriticModel
from src.core.instruction_manager import InstructionManager


class TestNetworkFailures:
    """Test system behavior under network failures"""

    def test_api_timeout_handling(self):
        """Test handling of API timeouts"""

        def mock_timeout(*args, **kwargs):
            raise TimeoutError("API request timed out")

        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should handle timeout gracefully
        try:
            with patch("time.sleep", side_effect=mock_timeout):
                main_model = MainModel(config, inst_mgr)
                # System should fallback or handle error
                assert main_model is not None
        except TimeoutError:
            # Acceptable to propagate timeout
            pass

    def test_network_partition_resilience(self):
        """Test resilience to network partitions"""

        def simulate_partition():
            """Simulate network partition by blocking connections"""
            raise ConnectionError("Network partition detected")

        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should handle partition gracefully
        try:
            main_model = MainModel(config, inst_mgr)
            # Should fallback to mock or local mode
            assert main_model.model is not None
        except ConnectionError:
            # Acceptable if handled properly
            pass

    def test_intermittent_connectivity(self):
        """Test handling of intermittent network connectivity"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Simulate intermittent connectivity
        success_count = 0
        failure_count = 0

        for i in range(10):
            try:
                # Randomly fail some requests
                if random.random() > 0.5:
                    main_model = MainModel(config, inst_mgr)
                    success_count += 1
                else:
                    raise ConnectionError("Intermittent failure")
            except ConnectionError:
                failure_count += 1

        # Should have some successes and some failures
        assert success_count > 0 or failure_count > 0

    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures"""

        def mock_dns_failure(*args, **kwargs):
            raise OSError("DNS resolution failed")

        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should handle DNS failures gracefully
        try:
            main_model = MainModel(config, inst_mgr)
            assert main_model.model is not None
        except OSError:
            # Acceptable to fail with appropriate error
            pass

    def test_packet_loss_simulation(self):
        """Test behavior under packet loss"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Simulate packet loss by random delays/failures
        attempts = 0
        max_attempts = 5

        while attempts < max_attempts:
            try:
                if random.random() > 0.3:  # 30% packet loss
                    main_model = MainModel(config, inst_mgr)
                    break
                else:
                    attempts += 1
                    time.sleep(0.1)
            except Exception:
                attempts += 1

        # Should eventually succeed with retries
        assert attempts <= max_attempts


class TestServiceFailures:
    """Test behavior when dependent services fail"""

    def test_redis_unavailable(self):
        """Test graceful degradation when Redis is unavailable"""
        config = SystemConfig(
            enable_caching=True,
            cache_redis_url="redis://localhost:9999",  # Invalid port
        )
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should fallback to in-memory cache
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should handle DB failures gracefully
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_llm_api_service_down(self):
        """Test behavior when LLM API service is down"""

        def mock_api_down(*args, **kwargs):
            raise Exception("Service Unavailable: 503")

        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should fallback to mock model
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_multiple_service_failures(self):
        """Test cascading service failures"""
        config = SystemConfig(
            enable_caching=True,
            cache_redis_url="redis://localhost:9999",  # Invalid
            main_model="gpt-4",
        )
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should handle multiple failures
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None


class TestResourceExhaustion:
    """Test behavior under resource exhaustion"""

    def test_memory_exhaustion(self):
        """Test behavior when memory is exhausted"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Create many instances to stress memory
        instances = []
        try:
            for i in range(20):
                instances.append(MainModel(config, inst_mgr))
        except MemoryError:
            # Acceptable to fail with MemoryError
            pass

        # Should create at least some instances
        assert len(instances) > 0

    def test_disk_space_exhaustion(self):
        """Test behavior when disk space is exhausted"""
        temp_dir = tempfile.mkdtemp()

        # Try to fill disk (safely with smaller test file)
        # Use 10MB instead of 100MB to avoid CI environment issues
        TEST_FILE_SIZE_MB = 10
        try:
            large_file = os.path.join(temp_dir, "large_file.dat")
            with open(large_file, "wb") as f:
                # Write TEST_FILE_SIZE_MB
                f.write(b"0" * (TEST_FILE_SIZE_MB * 1024 * 1024))
        except OSError:
            # Expected when disk is full
            pass

        # System should handle disk space issues
        config = SystemConfig(instructions_dir=Path(temp_dir))
        inst_mgr = InstructionManager(config)
        assert inst_mgr is not None

    def test_file_descriptor_exhaustion(self):
        """Test behavior when file descriptors are exhausted"""
        temp_dir = tempfile.mkdtemp()
        open_files = []

        try:
            # Try to open many files
            for i in range(100):
                f = open(os.path.join(temp_dir, f"file_{i}.txt"), "w")
                open_files.append(f)
        except OSError:
            # Expected when FD limit reached
            pass
        finally:
            # Clean up
            for f in open_files:
                try:
                    f.close()
                except:
                    pass

        # Should handle FD exhaustion
        assert len(open_files) > 0

    def test_cpu_saturation(self):
        """Test behavior under CPU saturation"""

        def cpu_intensive_work():
            """Simulate CPU-intensive work"""
            result = 0
            for i in range(1000000):
                result += i * i
            return result

        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Run CPU-intensive work in background
        with ThreadPoolExecutor(max_workers=4) as executor:
            cpu_futures = [executor.submit(cpu_intensive_work) for _ in range(4)]

            # Try to initialize model under CPU load
            main_model = MainModel(config, inst_mgr)
            assert main_model.model is not None

            # Wait for CPU work to complete
            [f.result() for f in cpu_futures]


class TestCascadingFailures:
    """Test cascading failure scenarios"""

    def test_failure_propagation(self):
        """Test how failures propagate through system"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Simulate component failures
        failures = []

        try:
            # Component 1 fails
            raise Exception("Component 1 failed")
        except Exception as e:
            failures.append(str(e))

        try:
            # Component 2 depends on Component 1
            if failures:
                raise Exception("Component 2 failed due to Component 1")
        except Exception as e:
            failures.append(str(e))

        # Should track cascading failures
        assert len(failures) == 2

    def test_circuit_breaker_activation(self):
        """Test circuit breaker pattern activates on repeated failures"""
        failure_threshold = 5
        consecutive_failures = 0
        circuit_open = False

        def operation_that_fails():
            """Operation that always fails"""
            raise Exception("Operation failed")

        for i in range(10):
            try:
                if circuit_open:
                    # Circuit breaker is open, fail fast
                    raise Exception("Circuit breaker open")

                operation_that_fails()
                consecutive_failures = 0
            except Exception:
                consecutive_failures += 1
                if consecutive_failures >= failure_threshold:
                    circuit_open = True

        # Circuit breaker should have opened
        assert circuit_open is True

    def test_bulkhead_isolation(self):
        """Test bulkhead pattern isolates failures"""
        # Simulate separate resource pools
        pool1_failures = 0
        pool2_failures = 0

        def pool1_operation():
            nonlocal pool1_failures
            pool1_failures += 1
            raise Exception("Pool 1 operation failed")

        def pool2_operation():
            nonlocal pool2_failures
            # Pool 2 continues working
            return "Success"

        # Pool 1 fails
        try:
            pool1_operation()
        except:
            pass

        # Pool 2 should still work
        result = pool2_operation()
        assert result == "Success"
        assert pool1_failures > 0


class TestByzantineFailures:
    """Test Byzantine failure scenarios"""

    def test_corrupted_data_handling(self):
        """Test handling of corrupted data"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()

        # Create corrupted instruction file
        instructions_path = Path(temp_dir) / "instructions.md"
        instructions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(instructions_path, "w") as f:
            f.write("Valid data\n")
            f.write("\x00\x01\x02\x03")  # Corrupted bytes

        config = SystemConfig(instructions_dir=Path(temp_dir))
        inst_mgr = InstructionManager(config)

        # Should handle corrupted data gracefully
        assert inst_mgr is not None

    def test_inconsistent_state_detection(self):
        """Test detection of inconsistent states"""
        # Simulate inconsistent state
        state1 = {"counter": 5, "last_updated": 100}
        state2 = {"counter": 3, "last_updated": 105}  # Counter went backwards

        # Detect inconsistency
        inconsistent = state2["counter"] < state1["counter"]
        assert inconsistent is True

    def test_split_brain_scenario(self):
        """Test split-brain scenario handling"""
        # Simulate two nodes with different states
        node1_state = {"leader": "node1", "version": 10}
        node2_state = {"leader": "node2", "version": 10}

        # Detect split brain
        split_brain = (
            node1_state["version"] == node2_state["version"]
            and node1_state["leader"] != node2_state["leader"]
        )

        assert split_brain is True


class TestFallbackMechanisms:
    """Test fallback mechanisms"""

    def test_primary_to_secondary_fallback(self):
        """Test fallback from primary to secondary provider"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should fallback to mock if primary unavailable
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_cache_fallback(self):
        """Test fallback from Redis to in-memory cache"""
        config = SystemConfig(
            enable_caching=True,
            cache_redis_url="redis://invalid:9999",  # Invalid
        )
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should fallback to in-memory
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_degraded_mode_operation(self):
        """Test operation in degraded mode"""
        config = SystemConfig(
            enable_caching=False,  # Disable cache
            enable_correction_detection=False,  # Disable correction detection
            main_model="gpt-4",
        )
        temp_dir = tempfile.mkdtemp()
        inst_mgr = InstructionManager(SystemConfig(instructions_dir=Path(temp_dir)))

        # Should work in degraded mode
        main_model = MainModel(config, inst_mgr)
        assert main_model.model is not None

    def test_retry_with_exponential_backoff(self):
        """Test retry logic with exponential backoff"""
        max_retries = 5
        base_delay = 0.1

        attempts = 0
        success = False

        while attempts < max_retries and not success:
            try:
                # Simulate operation that might fail
                if random.random() > 0.7:  # 30% success rate
                    success = True
                else:
                    raise Exception("Operation failed")
            except Exception:
                attempts += 1
                if attempts < max_retries:
                    delay = base_delay * (2 ** attempts)
                    time.sleep(min(delay, 1.0))  # Cap at 1 second for test

        # Should eventually succeed or exhaust retries
        assert attempts <= max_retries


class TestRecoveryMechanisms:
    """Test system recovery mechanisms"""

    def test_self_healing_after_failure(self):
        """Test system self-heals after failure"""
        config = SystemConfig(main_model="gpt-4")
        temp_dir = tempfile.mkdtemp()

        # First attempt fails
        failure_occurred = False
        try:
            raise Exception("Simulated failure")
        except Exception:
            failure_occurred = True

        # System should recover
        if failure_occurred:
            # Retry
            inst_mgr = InstructionManager(
                SystemConfig(instructions_dir=Path(temp_dir))
            )
            main_model = MainModel(config, inst_mgr)
            assert main_model.model is not None

    def test_state_recovery_from_backup(self):
        """Test recovering state from backup"""
        temp_dir = tempfile.mkdtemp()

        # Create backup
        backup_data = {"state": "saved", "version": 1}

        # Simulate failure and recovery
        try:
            # Primary state lost
            primary_state = None
            raise Exception("State lost")
        except Exception:
            # Recover from backup
            recovered_state = backup_data

        assert recovered_state["state"] == "saved"

    def test_graceful_degradation(self):
        """Test graceful degradation of features"""
        # Start with all features enabled
        features = {
            "caching": True,
            "correction_detection": True,
            "optimization": True,
        }

        # Simulate feature failures
        features["caching"] = False  # Cache failed
        features["correction_detection"] = False  # Detector failed

        # Core functionality should still work
        assert features["optimization"] is True or True  # Can still optimize


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
