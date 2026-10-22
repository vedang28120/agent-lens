"""Core modules for AgentLens - Autonomous AI Coding Assistant Exoskeleton."""

from .parser import CodeParser, Symbol, ImportInfo, FileParseResult
from .cartography import CodebaseCartographer
from .packer import ContextPacker
from .sandbox import GhostPatchSandbox
from .sentinel import PortSentinel
from .guard import HallucinationGuard
from .radar import ArchitectureRadar
from .planner import RefactorPlanner
from .preflight import PreflightChecker
from .report import ArchitectureReporter
from .watcher import CodebaseWatcher
from .memory import AgentMemory
from .shadow import GitShadowSandbox
from .delegation import DelegationContractGenerator
from .security import resolve_safe_path, is_safe_path

__all__ = [
    "CodeParser",
    "Symbol",
    "ImportInfo",
    "FileParseResult",
    "CodebaseCartographer",
    "ContextPacker",
    "GhostPatchSandbox",
    "PortSentinel",
    "HallucinationGuard",
    "ArchitectureRadar",
    "RefactorPlanner",
    "PreflightChecker",
    "ArchitectureReporter",
    "CodebaseWatcher",
    "AgentMemory",
    "GitShadowSandbox",
    "DelegationContractGenerator",
    "resolve_safe_path",
    "is_safe_path",
]
