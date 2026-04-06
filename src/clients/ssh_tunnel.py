"""Managed SSH tunnel using subprocess — auto-reconnects on failure."""

import logging
import socket
import subprocess
import time
from typing import Optional

log = logging.getLogger(__name__)


class SshTunnel:
    """SSH tunnel via subprocess with keepalive and auto-reconnect."""

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_user: str,
        remote_port: int,
        local_port: int,
    ) -> None:
        self._ssh_host = ssh_host
        self._ssh_port = ssh_port
        self._ssh_user = ssh_user
        self._remote_port = remote_port
        self._local_port = local_port
        self._process: Optional[subprocess.Popen] = None

    def _build_cmd(self) -> list[str]:
        """Build the ssh command with keepalive options."""
        return [
            "ssh", "-N",
            "-L", f"{self._local_port}:localhost:{self._remote_port}",
            "-p", str(self._ssh_port),
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            f"{self._ssh_user}@{self._ssh_host}",
        ]

    def _is_port_open(self) -> bool:
        """Check if the local tunnel port is accepting connections."""
        try:
            with socket.create_connection(("127.0.0.1", self._local_port), timeout=3):
                return True
        except OSError:
            return False

    def start(self) -> None:
        """Start the SSH tunnel subprocess."""
        cmd = self._build_cmd()
        log.info("Starting SSH tunnel: %s", " ".join(cmd))
        self._process = subprocess.Popen(
            cmd,
            stdin=None,  # inherit stdin so user can type password
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait for tunnel to become ready
        for _ in range(30):
            time.sleep(1)
            if self._process.poll() is not None:
                raise ConnectionError("SSH tunnel process exited unexpectedly")
            if self._is_port_open():
                log.info(
                    "SSH tunnel open: localhost:%d -> localhost:%d (via %s@%s:%d)",
                    self._local_port,
                    self._remote_port,
                    self._ssh_user,
                    self._ssh_host,
                    self._ssh_port,
                )
                return
        raise ConnectionError("SSH tunnel did not become ready within 30s")

    @property
    def is_alive(self) -> bool:
        """Check if the tunnel process is running and the port is reachable."""
        if self._process is None or self._process.poll() is not None:
            return False
        return self._is_port_open()

    def ensure_alive(self, max_retries: int = 3) -> None:
        """Check tunnel health and reconnect if needed."""
        if self.is_alive:
            return

        log.warning("SSH tunnel is down, reconnecting...")
        for attempt in range(max_retries):
            try:
                self.stop()
                self.start()
                log.info("SSH tunnel reconnected (attempt %d)", attempt + 1)
                return
            except ConnectionError as exc:
                wait = 10 * (attempt + 1)
                log.error("Reconnect attempt %d failed: %s — waiting %ds", attempt + 1, exc, wait)
                time.sleep(wait)

        raise ConnectionError(f"Failed to re-establish SSH tunnel after {max_retries} attempts")

    def stop(self) -> None:
        """Stop the SSH tunnel subprocess."""
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def __enter__(self) -> "SshTunnel":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
