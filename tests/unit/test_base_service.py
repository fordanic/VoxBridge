import os
import signal
import time
from unittest import mock

import logging
import pytest

from src.common.base_service import BaseService


class _TestService(BaseService):
    """Concrete implementation of BaseService for testing"""

    def __init__(self, service_name):
        self.cleanup_called = False
        self.run_count: int = 0
        with mock.patch.object(BaseService, 'setup_logging'), \
                mock.patch.object(BaseService, 'load_config', return_value={}), \
                mock.patch('logging.getLogger') as mock_logger:
            mock_logger.return_value = mock.MagicMock()
            super().__init__(service_name)
            self.logger = mock_logger.return_value

    def cleanup(self):
        self.cleanup_called = True

    def health_check(self):
        return {"status": "ok"}

    def _run_service_loop(self):
        if hasattr(self, 'run_count'):
            self.run_count += 1
        else:
            self.run_count = 1

        if hasattr(self, 'raise_error') and self.raise_error:
            raise Exception("Test exception")

        if self.run_count >= 3:  # Stop after 3 iterations
            self.running = False


class TestBaseService:
    """Test cases for BaseService functionality using TestService implementation"""

    @pytest.fixture
    def service(self):
        """Fixture providing a basic TestService instance"""
        service = _TestService("test_service")
        yield service
        # Cleanup after each test
        if service.running:
            service.running = False
            service.cleanup()

    @pytest.fixture
    def config_mock(self):
        """Fixture to mock configuration loading"""
        test_config = {
            'log_path': '/tmp/test_logs',
            'log_level': 'DEBUG'
        }
        with mock.patch.object(BaseService, 'load_config', return_value=test_config):
            yield test_config

    def test_service_initialization(self, service):
        """Test basic service initialization"""
        assert service.service_name == "test_service"
        assert not service.running
        assert isinstance(service.logger, mock.MagicMock)

    def test_service_health_check(self, service):
        """Test health check implementation"""
        health_status = service.health_check()
        assert isinstance(health_status, dict)
        assert health_status["status"] == "ok"

    def test_service_cleanup(self, service):
        """Test cleanup is called appropriately"""
        assert not service.cleanup_called
        service.cleanup()
        assert service.cleanup_called

    def test_service_start_and_stop(self, service):
        """Test service start/stop functionality"""
        # Start service in a separate thread to avoid blocking
        import threading
        service_thread = threading.Thread(target=service.start)
        service_thread.daemon = True
        service_thread.start()

        # Wait for service to finish (it should stop after 3 iterations)
        service_thread.join(timeout=2.0)
        assert not service_thread.is_alive()
        assert hasattr(service, 'run_count')
        assert service.run_count == 3
        assert service.cleanup_called

    def test_service_error_handling(self, service):
        """Test error handling in service loop"""
        service.raise_error = True

        # Start service in a separate thread
        import threading
        service_thread = threading.Thread(target=service.start)
        service_thread.daemon = True
        service_thread.start()

        # Let it run and handle the error
        time.sleep(0.2)  # Give it time to hit the error at least once
        service.running = False  # Stop the loop
        service_thread.join(timeout=1.0)

        assert not service_thread.is_alive()
        assert service.cleanup_called

    def test_signal_handling(self, service):
        """Test signal handling (SIGTERM/SIGINT)"""
        with mock.patch.object(os, '_exit') as mock_exit:
            # Simulate SIGINT
            service.handle_shutdown(signal.SIGINT, None)
            assert not service.running
            assert service.cleanup_called
            mock_exit.assert_called_once_with(0)

        # Reset service for SIGTERM test
        service.cleanup_called = False
        service.running = True

        # Simulate SIGTERM
        service.handle_shutdown(signal.SIGTERM, None)
        assert not service.running
        assert service.cleanup_called

    def test_service_loop_max_iterations(self, service):
        """Test service stops after max iterations"""
        service.start()  # This will run for 3 iterations and stop
        assert not service.running
        assert service.run_count == 3
        assert service.cleanup_called

    def test_setup_logging_creates_log_dir_and_file(self, tmp_path):
        """Test that setup_logging creates log directory and file with correct log level."""
        test_config = {'log_path': str(tmp_path), 'log_level': 'DEBUG'}

        class LoggingTestService(BaseService):
            def cleanup(self): pass
            def health_check(self): return {}
            def _run_service_loop(self): pass
        with mock.patch.object(BaseService, 'load_config', return_value=test_config):
            LoggingTestService("logtest")
            logger = logging.getLogger("voxbridge.logtest")
            assert logger.level == logging.DEBUG
            # Check log file exists
            log_file = tmp_path / "logtest.log"
            assert log_file.exists()

    def test_setup_logging_invalid_log_level(self, tmp_path, caplog):
        """Test that invalid log level in config defaults to INFO and logs a warning."""
        test_config = {'log_path': str(tmp_path), 'log_level': 'INVALID'}

        class LoggingTestService(BaseService):
            def cleanup(self): pass
            def health_check(self): return {}
            def _run_service_loop(self): pass
        with mock.patch.object(BaseService, 'load_config', return_value=test_config):
            with caplog.at_level(logging.WARNING):
                LoggingTestService("badloglevel")
                logger = logging.getLogger("voxbridge.badloglevel")
                assert logger.level == logging.INFO
                assert any(
                    "Invalid log level" in r.message for r in caplog.records)

    def test_load_config_reads_yaml(self, tmp_path):
        """Test that load_config reads YAML config file correctly."""
        config_content = {'log_path': '/tmp/test_logs', 'log_level': 'DEBUG'}
        config_file = tmp_path / "development.yaml"
        import yaml as _yaml
        with open(config_file, 'w') as f:
            _yaml.safe_dump(config_content, f)
        with mock.patch.dict(os.environ, {"VOXBRIDGE_ENV": "development"}):
            with mock.patch.object(BaseService, 'setup_logging'), \
                    mock.patch('logging.getLogger') as mock_logger:
                logger_instance = mock.MagicMock()
                mock_logger.return_value = logger_instance
                import builtins
                real_open = builtins.open

                def fake_open(path, *args, **kwargs):
                    if path == "config/development.yaml":
                        return real_open(config_file, *args, **kwargs)
                    return real_open(path, *args, **kwargs)
                # Patch __init__ to set logger before load_config

                def fake_init(self, service_name):
                    self.logger = logger_instance
                    self.service_name = service_name
                    self.config = BaseService.load_config(self)
                with mock.patch.object(builtins, 'open', side_effect=fake_open):
                    with mock.patch.object(BaseService, '__init__', fake_init):
                        class ConfigTestService(BaseService):
                            def cleanup(self): pass
                            def health_check(self): return {}
                            def _run_service_loop(self): pass
                        s = ConfigTestService("cfgtest")
                        assert s.config['log_path'] == '/tmp/test_logs'
                        assert s.config['log_level'] == 'DEBUG'

    def test_load_config_error_logs_and_returns_empty(self):
        """Test that load_config logs error and returns empty dict on failure."""
        with mock.patch('builtins.open', side_effect=OSError("fail")):
            with mock.patch.object(BaseService, 'setup_logging'), \
                    mock.patch('logging.getLogger') as mock_logger:
                logger_instance = mock.MagicMock()
                mock_logger.return_value = logger_instance

                def fake_init(self, service_name):
                    self.logger = logger_instance
                    self.service_name = service_name
                    self.config = BaseService.load_config(self)
                with mock.patch.object(BaseService, '__init__', fake_init):
                    class ConfigTestService(BaseService):
                        def cleanup(self): pass
                        def health_check(self): return {}
                        def _run_service_loop(self): pass
                    s = ConfigTestService("cfgfail")
                    assert s.config == {}
                    logger_instance.error.assert_called()

    def test_signal_handlers_are_registered(self):
        """Test that signal handlers are registered for SIGTERM and SIGINT."""
        with mock.patch('signal.signal') as mock_signal:
            with mock.patch.object(BaseService, 'setup_logging'), \
                    mock.patch('logging.getLogger'):
                class SignalTestService(BaseService):
                    def cleanup(self): pass
                    def health_check(self): return {}
                    def _run_service_loop(self): pass
                SignalTestService("sigtest")
                calls = [mock.call(signal.SIGTERM, mock.ANY),
                         mock.call(signal.SIGINT, mock.ANY)]
                mock_signal.assert_has_calls(calls, any_order=True)

    def test_handle_shutdown_logs_and_calls_cleanup(self, service):
        """Test that handle_shutdown logs and calls cleanup, and exits on SIGINT."""
        with mock.patch.object(service, 'cleanup') as cleanup_mock, \
                mock.patch.object(service.logger, 'info') as info_mock, \
                mock.patch.object(os, '_exit') as exit_mock:
            service.handle_shutdown(signal.SIGINT, None)
            cleanup_mock.assert_called()
            info_mock.assert_any_call(
                f"Received shutdown signal {signal.SIGINT}")
            exit_mock.assert_called_once_with(0)

    def test_handle_shutdown_logs_cleanup_error(self, service):
        """Test that handle_shutdown logs error if cleanup raises."""
        with mock.patch.object(service, 'cleanup', side_effect=Exception("fail")), \
                mock.patch.object(service.logger, 'error') as error_mock:
            service.handle_shutdown(signal.SIGTERM, None)
            error_mock.assert_any_call("Error during cleanup: fail")


if __name__ == "__main__":
    pytest.main()
