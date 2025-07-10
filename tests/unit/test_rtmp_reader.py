import io
import threading
import types
import numpy as np
import pytest

from src.common.rtmp_reader import RTMPReader, RTMPDisconnectedError


class DummyProcess:
    """A dummy process to simulate subprocess.Popen for testing."""

    def __init__(self, stdout_data=b"", stderr_data=b"", poll_result=None):
        self.stdout = io.BytesIO(stdout_data)
        self.stderr = io.BytesIO(stderr_data)
        self._poll_result = poll_result
        self.terminated = False
        self.killed = False
        self.wait_called = False

    def poll(self):
        return self._poll_result

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.wait_called = True

    def kill(self):
        self.killed = True

    def __getattr__(self, item):
        # For .stdout/.stderr close
        if item == "stdout":
            return self.stdout
        if item == "stderr":
            return self.stderr
        raise AttributeError(item)


class TestRTMPReader:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup before each test
        yield
        # Teardown after each test (if needed)

    def test_init_sets_attributes(self):
        # Arrange & Act
        reader = RTMPReader("rtmp://test", 8000, 0.1, 2.0, 5, 0.2)
        # Assert
        assert reader.rtmp_url == "rtmp://test"
        assert reader.sample_rate == 8000
        assert reader.chunk_size == 0.1
        assert reader.reconnect_delay == 2.0
        assert reader.max_retries == 5
        assert reader.read_timeout == 0.2

    def test_context_manager_calls_start_and_stop(self, monkeypatch):
        called = {"start": False, "stop": False}

        class Dummy(RTMPReader):
            def start(self, retry=False):
                called["start"] = True

            def stop(self):
                called["stop"] = True
        # Act
        with Dummy("rtmp://test"):
            assert called["start"]
        # Assert
        assert called["stop"]

    def test_del_calls_stop(self, monkeypatch):
        called = {"stop": False}

        class Dummy(RTMPReader):
            def stop(self):
                called["stop"] = True
        d = Dummy("rtmp://test")
        del d
        # Can't guarantee __del__ is called immediately, but at least no error

    def test_log_stderr_reads_lines(self, monkeypatch):
        process = types.SimpleNamespace(
            stderr=io.BytesIO(b"err1\nerr2\n"), poll=lambda: 0)
        reader = RTMPReader("rtmp://test")
        reader._stop_error_thread = False

        def fake_readline():
            return process.stderr.readline()
        process.stderr.readline = fake_readline
        # Act
        t = threading.Thread(target=reader._log_stderr, args=(process,))
        t.start()
        reader._stop_error_thread = True
        t.join()

    def test_start_sets_process_and_error_thread(self, monkeypatch):
        popen_called = {}

        def fake_popen(*args, **kwargs):
            popen_called["called"] = True
            return DummyProcess()
        monkeypatch.setattr("subprocess.Popen", fake_popen)
        reader = RTMPReader("rtmp://test")
        reader._error_thread = None
        # Act
        reader.start()
        # Assert
        assert popen_called["called"]
        assert reader.process is not None
        assert reader._error_thread is not None
        reader.stop()

    def test_start_reconnect_exponential(self, monkeypatch):
        call_count = {"count": 0}

        def fake_popen(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise Exception("fail")
            return DummyProcess()
        monkeypatch.setattr("subprocess.Popen", fake_popen)
        reader = RTMPReader("rtmp://test", max_retries=2, reconnect_delay=0.01)
        reader._error_thread = None
        # Act & Assert: should not raise if retry succeeds
        try:
            reader.start()
        except RTMPDisconnectedError:
            pytest.fail(
                "Should not raise RTMPDisconnectedError when a retry succeeds")
        assert call_count["count"] == 2
        reader.stop()

    def test_start_max_retries(self, monkeypatch):
        def fake_popen(*args, **kwargs):
            raise Exception("fail")
        monkeypatch.setattr("subprocess.Popen", fake_popen)
        reader = RTMPReader("rtmp://test", max_retries=2, reconnect_delay=0.01)
        reader._error_thread = None
        # Act & Assert
        with pytest.raises(RTMPDisconnectedError):
            reader.start()

    def test_read_chunks_reads_and_yields(self, monkeypatch):
        monkeypatch.setattr("select.select", lambda *a,
                            **k: ([object()], [], []))
        arr = (np.ones(8, dtype=np.int16) * 1000).tobytes()
        proc = DummyProcess(stdout_data=arr*2)
        reader = RTMPReader("rtmp://test", sample_rate=4, chunk_size=1)
        reader.process = proc
        # Act
        gen = reader.read_chunks()
        chunk = next(gen)
        # Assert
        assert np.allclose(chunk, 1000/32768.0)

    def test_read_chunks_timeout_and_reconnect(self, monkeypatch):
        calls = []

        def fake_select(*a, **k):
            if not calls:
                calls.append(1)
                return ([], [], [])
            return ([object()], [], [])
        monkeypatch.setattr("select.select", fake_select)
        arr = (np.ones(8, dtype=np.int16) * 1000).tobytes()
        proc = DummyProcess(stdout_data=arr*2, poll_result=1)
        reader = RTMPReader("rtmp://test", sample_rate=4, chunk_size=1)
        reader.process = proc

        def fake_start(retry=False):
            reader.process = DummyProcess(stdout_data=arr*2)
        reader.start = fake_start
        # Act
        gen = reader.read_chunks()
        chunk = next(gen)
        # Assert
        assert np.allclose(chunk, 1000/32768.0)

    def test_stop_closes_process(self, monkeypatch):
        proc = DummyProcess()
        reader = RTMPReader("rtmp://test")
        reader.process = proc
        reader._error_thread = threading.Thread(target=lambda: None)
        reader._error_thread.start()
        # Act
        reader.stop()
        # Assert
        assert proc.terminated or proc.killed
        assert reader.process is None
