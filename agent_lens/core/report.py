import os
import json
import time
from typing import Dict, Any, List, Optional
from .cartography import CodebaseCartographer
from .radar import ArchitectureRadar
from .memory import AgentMemory
from .sentinel import PortSentinel


class ArchitectureReporter:
    """Generates comprehensive, executive-grade architectural health reports with Mermaid diagrams."""

    def __init__(self, cartographer: CodebaseCartographer, memory: Optional[AgentMemory] = None):
        self.cart = cartographer
        self.memory = memory or AgentMemory()
        self.radar = ArchitectureRadar(cartographer)

    def generate_report(self) -> str:
        """Generates full markdown architecture audit with Mermaid diagram."""
        if not self.cart.file_results:
            self.cart.scan()

        radar_data = self.radar.analyze()
        tasks = self.memory.get_tasks()
        hypos = self.memory.get_hypotheses()
        decs = self.memory.get_decisions()
        ports = [p for p in PortSentinel.list_listening_ports() if p.get("is_dev_port")]

        lines = [
            "# 🔬 AgentLens Codebase Architecture & Health Audit",
            f"> Generated on {time.strftime('%Y-%m-%d %H:%M:%S')} for `{os.path.basename(self.cart.root_path)}`",
            "",
            "## 1. Executive Summary",
            f"- **Repository Root**: `{self.cart.root_path}`",
            f"- **Files Indexed**: {len(self.cart.file_results)} files ({sum(res.line_count for res in self.cart.file_results.values()):,} total lines of code)",
            f"- **AST Symbols**: {sum(len(v) for v in self.cart.symbol_index.values()):,} functions, classes, and methods",
            f"- **Architectural Health**: **{radar_data['health_score']}/100** (`{radar_data['status']}`)",
            f"- **Circular Import Loops**: {radar_data['circular_count']}",
            f"- **Candidate Orphan Symbols**: {radar_data['orphan_count']}",
            "",
            "## 2. Core Architecture & Dependency Graph",
            "```mermaid",
            "flowchart TD",
        ]

        # Add top dependency links to Mermaid graph
        node_ids = set()
        link_count = 0
        for src, mods in self.cart.file_imports.items():
            if "test" in src.lower():
                continue
            src_clean = os.path.basename(src).replace(".", "_")
            for mod in mods:
                target = self.cart._resolve_module_to_file(mod)
                if target and "test" not in target.lower() and target != src:
                    tgt_clean = os.path.basename(target).replace(".", "_")
                    lines.append(f'    {src_clean}["{os.path.basename(src)}"] --> {tgt_clean}["{os.path.basename(target)}"]')
                    link_count += 1
                    if link_count >= 18:
                        break
            if link_count >= 18:
                break

        if link_count == 0:
            lines.append('    App["Application Core"] --> Utils["Utilities"]')

        lines.extend([
            "```",
            "",
            "## 3. High-Centrality God Modules",
            "| Module | In-Degree (Dependents) | Out-Degree | Lines | Architectural Risk |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])

        for g in radar_data["god_nodes"]:
            risk_badge = f"🔴 {g['risk']}" if g['risk'] == "HIGH" else f"🟡 {g['risk']}"
            lines.append(f"| `{g['file']}` | {g['in_degree']} | {g['out_degree']} | {g['lines']} | {risk_badge} |")

        lines.extend([
            "",
            "## 4. Top Critical Symbols & Blast Radius",
            "| Symbol | File | Kind | Direct Callers | Blast Impact Risk |",
            "| :--- | :--- | :--- | :---: | :---: |",
        ])

        # Find top 5 most called symbols
        sorted_symbols = sorted(
            self.cart.reverse_call_graph.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )[:6]

        for sym_key, callers in sorted_symbols:
            parts = sym_key.split("::")
            f_path = parts[0]
            s_name = parts[1] if len(parts) > 1 else ""
            blast = self.cart.calculate_blast_radius(f_path, symbol_name=s_name)
            risk_badge = f"🔴 {blast['risk_level']}" if blast['risk_level'] in ["HIGH", "CRITICAL"] else f"🟢 {blast['risk_level']}"
            lines.append(f"| `{s_name}` | `{f_path}` | Function | {len(callers)} | {risk_badge} |")

        lines.extend([
            "",
            "## 5. Active Agent Working Memory State",
            f"- **Hypotheses Logged**: {len(hypos)}",
        ])
        for h in hypos[:3]:
            lines.append(f"  - `[{h['status'].upper()}]` {h['statement']}")

        lines.append(f"- **Key Architectural Decisions**: {len(decs)}")
        for d in decs[:2]:
            lines.append(f"  - **{d['title']}**: {d['rationale']}")

        lines.append(f"- **Active Dev Ports**: {', '.join([str(p['port']) for p in ports]) if ports else 'None'}")
        lines.append("")

        return "\n".join(lines)

    def write_report_to_file(self, target_path: str = "ARCHITECTURE_REPORT.md") -> str:
        content = self.generate_report()
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return os.path.abspath(target_path)
