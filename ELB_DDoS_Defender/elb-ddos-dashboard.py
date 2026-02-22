#!/usr/bin/env python3
"""
ELB DDoS Defender - Advanced TUI Dashboard
Beautiful, detailed, real-time monitoring interface
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.align import Align
from rich import box
from datetime import datetime
import time
import random  # TODO: Replace with real data

console = Console()

class DDoSDefenderDashboard:
    def __init__(self):
        self.start_time = datetime.now()
        self.layout = Layout()
        self.setup_layout()
        
    def setup_layout(self):
        """Create the dashboard layout"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        self.layout["left"].split_column(
            Layout(name="load_balancers", ratio=2),
            Layout(name="eni_usage", ratio=1),
            Layout(name="statistics", ratio=1)
        )
        
        self.layout["right"].split_column(
            Layout(name="alerts", ratio=1),
            Layout(name="events", ratio=2),
            Layout(name="threats", ratio=1)
        )
    
    def make_header(self):
        """Create header with title and status"""
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]
        
        header_text = Text()
        header_text.append("🛡️  ELB DDoS Defender", style="bold cyan")
        header_text.append(" | ", style="dim")
        header_text.append("Real-Time Monitor", style="bold green")
        header_text.append(" | ", style="dim")
        header_text.append(f"Uptime: {uptime_str}", style="yellow")
        header_text.append(" | ", style="dim")
        header_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="blue")
        header_text.append(" | ", style="dim")
        header_text.append("[Q]uit [R]efresh [H]elp", style="dim")
        
        return Panel(
            Align.center(header_text),
            style="bold white on blue",
            box=box.DOUBLE
        )
    
    def make_load_balancers(self):
        """Create load balancer status panel"""
        table = Table(
            title="🔷 Load Balancers",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            expand=True
        )
        
        table.add_column("Name", style="bold white", width=20)
        table.add_column("Type", justify="center", width=6)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Packets/s", justify="right", width=12)
        table.add_column("Requests/s", justify="right", width=12)
        table.add_column("Connections", justify="right", width=12)
        table.add_column("Targets", justify="center", width=10)
        table.add_column("Errors", justify="right", width=10)
        
        # TODO: Replace with real data
        load_balancers = [
            {
                "name": "prod-alb-1",
                "type": "ALB",
                "status": "healthy",
                "packets": 1234,
                "requests": 890,
                "connections": 5678,
                "targets": "4/4",
                "errors": "12 (1.3%)"
            },
            {
                "name": "prod-alb-2",
                "type": "ALB",
                "status": "healthy",
                "packets": 2456,
                "requests": 1234,
                "connections": 8901,
                "targets": "3/3",
                "errors": "5 (0.4%)"
            }
        ]
        
        for lb in load_balancers:
            status_icon = "✓" if lb["status"] == "healthy" else "✗"
            status_color = "green" if lb["status"] == "healthy" else "red"
            
            table.add_row(
                lb["name"],
                lb["type"],
                f"[{status_color}]{status_icon} {lb['status'].upper()}[/{status_color}]",
                f"[cyan]{lb['packets']:,}[/cyan]",
                f"[blue]{lb['requests']:,}[/blue]",
                f"[yellow]{lb['connections']:,}[/yellow]",
                f"[green]{lb['targets']}[/green]",
                f"[red]{lb['errors']}[/red]"
            )
        
        # Add detailed metrics for each LB
        details = Table.grid(padding=(0, 2))
        details.add_column(style="dim")
        details.add_column()
        
        details.add_row(
            "ELB Nodes:",
            "[green]3/3 healthy[/green] | [cyan]eni-001[/cyan] (33%) [cyan]eni-002[/cyan] (33%) [cyan]eni-003[/cyan] (30%)"
        )
        details.add_row(
            "Targets:",
            "[green]i-abc123[/green] (22%) [green]i-def456[/green] (21%) [green]i-ghi789[/green] (20%) [green]i-jkl012[/green] (19%)"
        )
        details.add_row(
            "Health Checks:",
            "[green]✓ All passing[/green] | Last: 2s ago | Success rate: 100%"
        )
        details.add_row(
            "Attack Status:",
            "[green]✓ No attacks detected[/green] | Last scan: 1s ago"
        )
        
        return Panel(
            Table.grid(
                table,
                details,
                padding=(1, 0)
            ),
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def make_eni_usage(self):
        """Create ENI connection usage panel"""
        table = Table(
            title="🔌 ENI Connection Usage (55k limit per ENI)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            border_style="magenta",
            expand=True
        )
        
        table.add_column("ENI ID", style="bold white", width=18)
        table.add_column("Type", width=10)
        table.add_column("Usage", width=40)
        table.add_column("Connections", justify="right", width=15)
        table.add_column("Status", justify="center", width=10)
        
        # TODO: Replace with real data
        enis = [
            {"id": "eni-elb-001", "type": "ELB Node", "conn": 18234, "max": 55000},
            {"id": "eni-elb-002", "type": "ELB Node", "conn": 17890, "max": 55000},
            {"id": "eni-elb-003", "type": "ELB Node", "conn": 16543, "max": 55000},
            {"id": "eni-target-001", "type": "Target", "conn": 12000, "max": 55000},
            {"id": "eni-target-002", "type": "Target", "conn": 11500, "max": 55000},
            {"id": "eni-target-003", "type": "Target", "conn": 10800, "max": 55000},
            {"id": "eni-target-004", "type": "Target", "conn": 10200, "max": 55000},
        ]
        
        for eni in enis:
            pct = (eni["conn"] / eni["max"]) * 100
            
            # Color based on usage
            if pct < 50:
                color = "green"
                status = "✓ OK"
            elif pct < 80:
                color = "yellow"
                status = "⚠ WARN"
            else:
                color = "red"
                status = "🚨 HIGH"
            
            # Create progress bar
            bar_length = 30
            filled = int((pct / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            table.add_row(
                f"[cyan]{eni['id']}[/cyan]",
                eni['type'],
                f"[{color}]{bar}[/{color}] {pct:.1f}%",
                f"[{color}]{eni['conn']:,}/{eni['max']:,}[/{color}]",
                f"[{color}]{status}[/{color}]"
            )
        
        return Panel(table, border_style="magenta", box=box.ROUNDED)
    
    def make_statistics(self):
        """Create statistics panel"""
        table = Table(
            title="📊 Statistics (Last 60 seconds)",
            box=box.ROUNDED,
            show_header=False,
            border_style="blue",
            expand=True
        )
        
        table.add_column("Metric", style="bold white", width=25)
        table.add_column("Value", style="cyan", width=20)
        table.add_column("Details", style="dim", width=30)
        
        # TODO: Replace with real data
        table.add_row(
            "Total Packets",
            "[cyan]234,567[/cyan]",
            "TCP: 98% | UDP: 1% | Other: 1%"
        )
        table.add_row(
            "Total Connections",
            "[yellow]14,579[/yellow]",
            "Active: 12,345 | New: 2,234"
        )
        table.add_row(
            "HTTP Requests",
            "[blue]8,901[/blue]",
            "GET: 85% | POST: 12% | Other: 3%"
        )
        table.add_row(
            "Bandwidth",
            "[magenta]125 MB/s[/magenta]",
            "In: 100 MB/s | Out: 25 MB/s"
        )
        table.add_row(
            "Attacks Detected",
            "[green]0[/green]",
            "Last 24h: 0 | Total: 0"
        )
        table.add_row(
            "Port Scans",
            "[green]0[/green]",
            "Blocked IPs: 0"
        )
        table.add_row(
            "Retransmissions",
            "[yellow]234 (0.1%)[/yellow]",
            "Normal range"
        )
        table.add_row(
            "Packet Loss",
            "[green]0.01%[/green]",
            "Excellent"
        )
        
        return Panel(table, border_style="blue", box=box.ROUNDED)
    
    def make_alerts(self):
        """Create alerts panel"""
        table = Table(
            title="🚨 Active Alerts",
            box=box.ROUNDED,
            show_header=False,
            border_style="red",
            expand=True
        )
        
        table.add_column("Alert", style="bold")
        
        # TODO: Replace with real data
        alerts = []  # No active alerts
        
        if not alerts:
            table.add_row("[green]✓ No active alerts[/green]")
            table.add_row("[dim]All systems operating normally[/dim]")
        else:
            for alert in alerts:
                table.add_row(f"[red]🚨 {alert}[/red]")
        
        return Panel(table, border_style="green", box=box.ROUNDED)
    
    def make_events(self):
        """Create recent events panel"""
        table = Table(
            title="📋 Recent Events",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold white",
            border_style="white",
            expand=True
        )
        
        table.add_column("Time", style="dim", width=10)
        table.add_column("Level", width=8)
        table.add_column("Event", style="white")
        
        # TODO: Replace with real data
        events = [
            {"time": "14:36:42", "level": "INFO", "msg": "Health check passed: prod-alb-1 → i-abc123"},
            {"time": "14:36:40", "level": "INFO", "msg": "Health check passed: prod-alb-2 → i-def456"},
            {"time": "14:36:35", "level": "WARN", "msg": "High connection rate: eni-elb-001 (18k)"},
            {"time": "14:36:30", "level": "INFO", "msg": "Traffic spike detected: +25% (normal)"},
            {"time": "14:36:25", "level": "INFO", "msg": "Health check passed: prod-alb-1 → i-ghi789"},
            {"time": "14:36:20", "level": "INFO", "msg": "PyShark capture active: 1,234 pkt/s"},
            {"time": "14:36:15", "level": "INFO", "msg": "CloudWatch metrics published"},
            {"time": "14:36:10", "level": "INFO", "msg": "ENI discovery completed: 13 ENIs"},
        ]
        
        for event in events:
            level_color = {
                "INFO": "blue",
                "WARN": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold red"
            }.get(event["level"], "white")
            
            table.add_row(
                event["time"],
                f"[{level_color}]{event['level']}[/{level_color}]",
                event["msg"]
            )
        
        return Panel(table, border_style="white", box=box.ROUNDED)
    
    def make_threats(self):
        """Create threat intelligence panel"""
        table = Table(
            title="🌍 Threat Intelligence",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow",
            border_style="yellow",
            expand=True
        )
        
        table.add_column("Metric", style="bold white")
        table.add_column("Count", justify="right", style="cyan")
        
        # TODO: Replace with real data
        table.add_row("Unique Source IPs", "[cyan]1,234[/cyan]")
        table.add_row("Known Bad IPs", "[green]0[/green]")
        table.add_row("Tor Exit Nodes", "[green]0[/green]")
        table.add_row("Botnet IPs", "[green]0[/green]")
        table.add_row("", "")
        table.add_row("[bold]Top Countries:[/bold]", "")
        table.add_row("  🇺🇸 United States", "45%")
        table.add_row("  🇬🇧 United Kingdom", "20%")
        table.add_row("  🇩🇪 Germany", "15%")
        table.add_row("  🇯🇵 Japan", "10%")
        table.add_row("  🇨🇦 Canada", "10%")
        
        return Panel(table, border_style="yellow", box=box.ROUNDED)
    
    def make_footer(self):
        """Create footer with controls"""
        footer_text = Text()
        footer_text.append("Controls: ", style="bold white")
        footer_text.append("[Q]", style="bold cyan")
        footer_text.append("uit  ", style="white")
        footer_text.append("[R]", style="bold cyan")
        footer_text.append("efresh  ", style="white")
        footer_text.append("[H]", style="bold cyan")
        footer_text.append("elp  ", style="white")
        footer_text.append("[1]", style="bold cyan")
        footer_text.append(" Details  ", style="white")
        footer_text.append("[2]", style="bold cyan")
        footer_text.append(" Report  ", style="white")
        footer_text.append("[3]", style="bold cyan")
        footer_text.append(" Test Alert  ", style="white")
        footer_text.append("[4]", style="bold cyan")
        footer_text.append(" Settings", style="white")
        
        return Panel(
            Align.center(footer_text),
            style="white on black",
            box=box.DOUBLE
        )
    
    def generate(self):
        """Generate the complete dashboard"""
        self.layout["header"].update(self.make_header())
        self.layout["load_balancers"].update(self.make_load_balancers())
        self.layout["eni_usage"].update(self.make_eni_usage())
        self.layout["statistics"].update(self.make_statistics())
        self.layout["alerts"].update(self.make_alerts())
        self.layout["events"].update(self.make_events())
        self.layout["threats"].update(self.make_threats())
        self.layout["footer"].update(self.make_footer())
        
        return self.layout

def main():
    """Main dashboard loop"""
    dashboard = DDoSDefenderDashboard()
    
    try:
        with Live(dashboard.generate(), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)
                live.update(dashboard.generate())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

if __name__ == "__main__":
    main()
