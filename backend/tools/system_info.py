"""Tool: report host machine resource usage via psutil."""

import psutil
from langchain_core.tools import tool


@tool
def get_system_info() -> str:
    """
    Get current CPU usage, memory usage, and disk usage from the host machine.
    Use this when the user asks about system performance or resource availability.
    """
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return (
        f"CPU:    {cpu:.1f}%\n"
        f"Memory: {mem.percent:.1f}% used "
        f"({mem.used // 1024**3} GB / {mem.total // 1024**3} GB)\n"
        f"Disk:   {disk.percent:.1f}% used "
        f"({disk.used // 1024**3} GB / {disk.total // 1024**3} GB)"
    )
