from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from readline import insert_text
from typing import Any, Dict, List, Optional, Tuple, Callable
import os, time, threading, json, hashlib, math, re, pathlib

from click import prompt

# absolute imports 
from javu_agi.eval.report_server import Payload
from javu_agi.world_model import WorldModel
from javu_agi.reasoning_engine import ReasoningEngine
from javu_agi.meta_reasoning import evaluate_candidates
from javu_agi.meta_cognition import MetaCognition
from javu_agi.reward_system import RewardSystem
from javu_agi.reflective_loop import ReflectiveLoop
from javu_agi.autonomy import pick_goal
from javu_agi.capabilities import allowed_categories, filter_steps
from javu_agi.learn.policy_learner import PolicyLearner
from javu_agi.learn.policy_learner_ctx import ContextualPolicyLearner
from javu_agi.safety_values import violates_core_values, explain_violation
from javu_agi.safety.kill_switch import KillSwitch
from javu_agi.safety.policy_engine import PolicyEngine
from javu_agi.safety.ec_integration import preflight_action, enforce_approval_blocking
from javu_agi.safety.action_audit import record_action
from javu_agi.safety.circuit_breaker import CB
from javu_agi.self_reflection import reflect_outcome
from javu_agi.self_model import SelfModel
from javu_agi.social_cognition import SocialCognition
from javu_agi.learn.skill_binder import SkillBinder
from javu_agi.learn.skill_graph import SkillGraph
from javu_agi.learn.credit_assign import CreditAssigner
from javu_agi.learn.credit_assigner_causal import CausalCreditAssigner
from javu_agi.learn.skill_composer import SkillComposer
from javu_agi.learn.lifelong import LifelongLearner
from javu_agi.memory.memory_manager import MemoryManager
from javu_agi.obs.metrics import M
from javu_agi.tools.registry import ToolRegistry
from javu_agi.tools.planner import Plan, Planner
from javu_agi.tools.planner_llm import LLMPlanner
from javu_agi.tools.policy_filter import PolicyFilter
from javu_agi.tools.policy_filter_hard import PolicyFilterHard
from javu_agi.tools.plan_optimizer import PlanOptimizer
from javu_agi.tools.execution_budget import ExecutionBudget
from javu_agi.tools.contract_verifier import ContractVerifier
from javu_agi.tools.tool_contracts import default_contracts
from javu_agi.cache.result_cache import ResultCache
from javu_agi.utils.rng import seed_everything
from javu_agi.utils.logger import log_system
from javu_agi.utils.embedding import embed
from javu_agi.utils.time_utils import now_ms
from javu_agi.utils.degrade import is_degraded
from javu_agi.utils.determinism import set_seed
from javu_agi.utils.sanitize import scrub, strip_ansi
from javu_agi.utils.notify import notify as _op_notify
from javu_agi.runtime.agent_trace import log_node, log_edge, begin_episode, end_episode
from javu_agi.runtime.episode_workspace import make_workspace
from javu_agi.grounding import GroundingLayer, Percept
from javu_agi.goal_manager import GoalManager
from javu_agi.goal_generator import generate_goal
from javu_agi.goal_planner import _ECO, GoalPlanner
from javu_agi.competence_tracker import Competence
from javu_agi.tool_bandit import ToolBandit
from javu_agi.research.verifier import verify_hypothesis, verify_step
from javu_agi.budget_guard import BudgetGuard
from javu_agi.alignment_checker import AlignmentChecker
from javu_agi.alignment_auditor import AlignmentAuditor
from javu_agi.ops.distill_io import DistillIO
from javu_agi.ops.incident_notifier import IncidentNotifier
from javu_agi.ops.incident_engine import IncidentEngine
from javu_agi.drive_system import DriveSystem
from javu_agi.embodiment_pack.shim import Embodiment
from javu_agi.execution_manager import ExecutionManager
from javu_agi.ethics_deliberator import EthicsDeliberator
from javu_agi.interpret.decision_tracer import DecisionTracer
from javu_agi.interpret.calibration import Calibrator
from javu_agi.interpret.evaluation_framework import EvaluationFramework
from javu_agi.distill_deduper import DistillDeduper
from javu_agi.founder_protection import FounderProtection
from javu_agi.meta_rl import MetaPolicy
from javu_agi.value_memory import ValueMemory
from javu_agi.long_horizon import MCTSPlanner
from javu_agi.long_horizon_planner import LongHorizonPlanner
from javu_agi.long_term_memory import LongTermMemory
from javu_agi.anomaly_guard import AnomalyGuard
from javu_agi.tool_synthesizer import synthesize_tool
from javu_agi.eval.eval_harness import run_suite as run_suite
from javu_agi.static_plan_checker import check
from javu_agi.risk_gate import risky
from javu_agi.telemetry import Telemetry
from javu_agi.fs_guard import allowed_write
from javu_agi.prompt_shield import shield
from javu_agi.tool_schema import validate_plan
from javu_agi.tamper_hash import TamperHash
from javu_agi.resume_journal import journal_path, write_journal, load_journal
from javu_agi.crosscheck import needs_crosscheck, consensus
from javu_agi.consent_guard import allow_read
from javu_agi.pii_detector import is_leak
from javu_agi.shadow_planner import score_plan
from javu_agi.auto_stop import AutoStop
from javu_agi.security.egress_guard import allow as egress_allow
from javu_agi.security.secret_scan import has_secret
from javu_agi.security.adversarial_guard import AdversarialGuard
from javu_agi.security.tool_acl import is_tool_allowed
from javu_agi.security.effect_guard import EffectGuard
from javu_agi.security.watermark import sign_output, verify_input
from javu_agi.security.supply_chain_guard import SupplyChainGuard
from javu_agi.serving.egress_filter import check_host
from javu_agi.persist import CheckpointIO
from javu_agi.robustness.self_healing import SelfHealing
from javu_agi.safety.supervision_layer import SupervisionLayer
from javu_agi.intent_commitment_ledger import append_intent
from javu_agi.decision_record import write as write_decision
from javu_agi.ethics_gate import enforce as ethics_enforce
from javu_agi.ethics_simulator import EthicsSimulator
from javu_agi.interlocks.kill_switch import guard as killswitch_guard
from javu_agi.ledger.intent_audit import record_intent
from javu_agi.normative_framework import NormativeFramework
from javu_agi.peace_objective import PeaceObjective
from javu_agi.cultural_adapter import CulturalAdapter
from javu_agi.sustainability_model import SustainabilityModel
from javu_agi.commons_guard import CommonsGuard
from javu_agi.explainability import explain_decision
from javu_agi.moral_reasoning_engine import MoralReasoningEngine
from javu_agi.deliberative_dialogue import DeliberativeDialogue
from javu_agi.empathy_model import EmpathyModel, PersonModel
from javu_agi.fairness_auditor import FairnessAuditor
from javu_agi.planet.eco_guard import EcoGuard, PlanetaryGuardian
from javu_agi.foresight_engine import ForesightEngine
from javu_agi.conflict_mediator import ConflictMediator
from javu_agi.meaning_framework import MeaningFramework
from javu_agi.human_values_interface import HumanValuesInterface
from javu_agi.collective_governance import CollectiveGovernance
from javu_agi.transparency_dashboard import TransparencyDashboard
from javu_agi.threat_modeler import ThreatModeler
from javu_agi.ethics_update_manager import EthicsUpdateManager
from javu_agi.cooperative_learning import CooperativeLearning
from javu_agi.lifelong_learning_manager import LifelongLearningManager
from javu_agi.moral_emotion_engine import MoralEmotionEngine
from javu_agi.cyber_immune_core import CyberImmuneCore
from javu_agi.provenance_guard import ProvenanceGuard
from javu_agi.impact_assessor import ImpactAssessor
from javu_agi.value_tradeoff_explainer import ValueTradeoffExplainer
from javu_agi.sensorimotor_loop import SensorimotorLoop
from javu_agi.body_schema import BodySchema
from javu_agi.multi_agent_governance import MultiAgentGovernance
from javu_agi.corrigibility_manager import CorrigibilityManager
from javu_agi.aesthetic_judgment import AestheticJudgment
from javu_agi.cross_domain_creator import CrossDomainCreator
from javu_agi.collective_governance_hub import CollectiveGovernanceHub
from javu_agi.privacy_data.dp_budget import DPBudget
from javu_agi.privacy_data.data_retention_manager import DataRetentionManager
from javu_agi.audit.audit_chain import AuditChain
from javu_agi.oversight.queue import OversightQueue
from javu_agi.xai.explaination_reporter import ExplanationReporter
from javu_agi.peace_optimizer import PeaceOptimizer
from javu_agi.resilience_manager import ResilienceManager
from javu_agi.debate_engine import DebateEngine
from javu_agi.meta_optimizer import MetaOptimizer
from javu_agi.telemetry_pack.notify import notify as _tel_notify
from javu_agi.self_repair_manager import SelfRepairManager
from javu_agi.eco_guard import EcoGuard
from javu_agi.planet.eco_guard import SustainabilityGuard, PlanetaryPolicy
from javu_agi.transparency_reporter import make_report
from javu_agi.ethical_critic import precheck as _eth_pre, postcheck as _eth_post
from javu_agi.introspection import explain as _explain
from javu_agi.audit_log import AuditLog as _AuditLog
from javu_agi.resilience_guard import ResilienceGuard as _Res
from javu_agi.value_alignment_coach import refine as _refine
from javu_agi.sustainability_advisor import suggest as _suggest
from javu_agi.privacy_guard import privacy_guard as _pg
from javu_agi.feedback_collector import FeedbackCollector
from javu_agi.role_orchestrator import orchestrate
from javu_agi.fact_checker import fact_check
from javu_agi.empathy_coach import add_empathy
from javu_agi.config import load_policy, load_permissions
from javu_agi.causal_reasoner import CausalReasoner
from javu_agi.causal_adapter import LegacyCausalAdapter
from javu_agi.metacog import MetaCognitiveMonitor
from javu_agi.theory_of_mind import ToM
from javu_agi.embodiment_pack.integrator import EmbodiedIntegrator
from javu_agi.embodiment_pack.safety_shield import safety_veto
from javu_agi.value_dynamics import ValueDynamics
from javu_agi.domain_adapters.base import REGISTRY as DOMAIN_ADAPTERS
from javu_agi.deliberation.consensus import Deliberator
from javu_agi.deliberation.collective import CollectiveDeliberator
from javu_agi.ethics_gate import EthicsGate
from javu_agi.agency.intent_engine import synthesize_intents
from javu_agi.hri.dialog_policy import safe_counter
from javu_agi.planner import Planner as LegacyPlanner
from javu_agi.identity_manager import DynamicIdentityManager, RoleProfile
from javu_agi.knowledge_hub import retrieve_context as kb_retrieve
from javu_agi.status_board import StatusBoard
from javu_agi.orchestrator import AgentOrchestrator, SubTask
# Governance pack
from javu_agi.governance.ethics_guard.guard import GovGuard
from javu_agi.governance.data_connect.loader import load_baseline
from javu_agi.governance.policy_sim.engine import Policy, PolicySimulator
from javu_agi.governance.oversight.redflag import report as gov_report
from javu_agi.governance.policy_watcher import FileWatcher
from javu_agi.governance.consent_ledger import ConsentLedger
from javu_agi.governance.oversight.board import OversightBoard
from javu_agi.governance.policies import load_policy_store
# Router LLM
from javu_agi.llm_router import LLMRouter, run_multimodal_task

import json as _json, os as _os, time as _time, hashlib as _hashlib, random as _random
_QUEUE_DIR = _os.getenv("QUEUE_DIR", "/data/queue"); _os.makedirs(_QUEUE_DIR, exist_ok=True)
def _step_id(cmd: str) -> str:
    return _hashlib.sha1(cmd.encode("utf-8")).hexdigest()
def _qfile() -> str:
    return _os.path.join(_QUEUE_DIR, "exec_steps.jsonl")
def _enqueue_step(step_id: str, payload: dict):
    try:
        with open(_qfile(), "a", encoding="utf-8") as f:
            f.write(_json.dumps({"id": step_id, **payload}) + "\n")
            
    except Exception:
        pass
def _seen_step(step_id: str) -> bool:
    try:
        with open(_qfile(), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = _json.loads(line)
                    if obj.get("id") == step_id:
                        return True
                except Exception:
                    continue
    except Exception:
        return False
    return False

DISTILL_ENABLED = False
AUTO_TRAIN_ENABLED = False

class AutoTrainOrchestrator:
    def __init__(self, *a, **k):
        raise RuntimeError("LLM builder OFF")
    def start(self, *a, **k):
        raise RuntimeError("LLM builder OFF")

# === config ===
MAX_CANDIDATES = 4
UNCERTAINTY_CLARIFY_THRESHOLD = 0.65
EARLY_EXIT_CONFIDENCE = 0.88
ENABLE_AUTO_CLARIFY = True

# === Thresholds (ENV override) ===
IMPACT_FLOOR   = float(os.getenv("IMPACT_FLOOR", "0.50"))
ECO_RISK_MAX   = float(os.getenv("ECO_RISK_MAX", "0.60"))
COMMONS_ENFORCE = os.getenv("COMMONS_ENFORCE","1").lower() in {"1","true","yes"}

# === paths ===
DATA_DIR = os.getenv("DATA_DIR", "/data")
SKILL_CACHE_DIR = os.getenv("SKILL_CACHE_DIR", os.path.join(DATA_DIR, "skill_cache"))
RESULT_CACHE_DIR = os.getenv("RESULT_CACHE_DIR", os.path.join(DATA_DIR, "result_cache"))
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "/artifacts")

AUDIT_CHAIN_DIR = os.getenv("AUDIT_CHAIN_DIR", os.path.join(DATA_DIR, "audit_chain"))

# === Distill thresholds & parameters ===
DISTILL_THRESH_REWARD = float(os.getenv("DISTILL_THRESH_REWARD", "0.70"))
DISTILL_THRESH_VERIFIER = float(os.getenv("DISTILL_THRESH_VERIFIER", "0.60"))
DISTILL_THRESH_FAITH = float(os.getenv("DISTILL_THRESH_FAITH", "0.95"))
DISTILL_THRESH_HALLUC = float(os.getenv("DISTILL_THRESH_HALLUC", "0.02"))
DISTILL_COST_BUFFER = float(os.getenv("DISTILL_COST_BUFFER", "1.25"))  # 25% over price table
DISTILL_MIN_OUT_TOKENS = int(os.getenv("DISTILL_MIN_OUT_TOKENS", "10"))
DISTILL_DUP_WINDOW_DAYS = int(os.getenv("DISTILL_DUP_WINDOW_DAYS", "7"))

LIMIT_MSG = "(limit tercapai untuk plan Anda hari ini)"
METRICS_DIR = os.getenv("METRICS_DIR", "/data/metrics")
pathlib.Path(METRICS_DIR).mkdir(parents=True, exist_ok=True)

POLICY_PATH = os.getenv("PLANETARY_POLICY", "config/planetary_policy.yaml")

POLICY      = load_policy()
PERMISSIONS = load_permissions()

def _pii_flag(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s):
        return True
    if re.search(r"\b(\+?\d{2,3}[-.\s]?)?\d{8,12}\b", s):
        return True
    return False

# Simple governance deny list (bisa diganti loader YAML)
GOV_DENY = [ "cara membuat bom", "bioweapon", "senjata rakitan", "retas", "phishing",
             "carding", "exploit", "ddos", "p0rn", "porno", "kekerasan seksual",
             "genosida", "pemusnahan", "supremasi", "penyiksaan" ]

def gov_guard_check(text: str):
    t = (text or "").lower()
    for term in GOV_DENY:
        if term in t:
            return False, term
    return True, ""

# Micro policy simulator (proxy cepat)
def _gov_load_baseline(cc: str = "XX"):
    cache = os.getenv("GOV_CACHE_DIR","data/gov_cache")
    pathlib.Path(cache).mkdir(parents=True, exist_ok=True)
    fp = os.path.join(cache, f"{cc}.json")
    if os.path.exists(fp) and time.time()-os.path.getmtime(fp) < 86400:
        return json.load(open(fp))
    data = {"gdp": 100_000.0, "gini": 0.42, "unemployment": 0.11, "edu_index": 0.55}
    json.dump(data, open(fp,"w")); return data

def _policy_compare(baseline: dict, policies: list):
    import math
    ranked = []
    for name, params in policies:
        tr = float(params.get("tax_rate", 0.10))
        sub_edu = float(params.get("subsidy_edu", 0.01))
        health = float(params.get("health_spend", 0.00))
        growth = (1 - 0.5*tr) + 0.2*sub_edu + 0.1*health
        growth = max(-0.1, min(0.12, growth))
        new_gdp = baseline["gdp"] * (1 + growth)
        new_gini = max(0.20, min(0.70, baseline["gini"] - 0.3*sub_edu + 0.05*tr))
        new_unemp = max(0.01, min(0.35, baseline["unemployment"] - 0.2*growth + 0.05*tr))
        new_edu = max(0.10, min(0.95, baseline["edu_index"] + 0.5*sub_edu))
        welfare = (math.log(new_gdp + 1) - 0.5*new_gini + 0.2*(1 - new_unemp) + 0.3*new_edu)
        ranked.append({
            "policy": name, "params": params, "gdp": new_gdp, "gini": new_gini,
            "unemployment": new_unemp, "edu_index": new_edu, "growth": growth, "welfare": welfare
        })
    ranked.sort(key=lambda x: x["welfare"], reverse=True)
    return {"ranked": ranked, "best": ranked[0] if ranked else None}

# === Utility: robust hash ===
_AUDIT_CHAIN = {"prev": "GENESIS"}
os.makedirs(AUDIT_CHAIN_DIR, exist_ok=True)

def audit_chain_commit(kind: str, record: dict) -> str:
    os.makedirs(AUDIT_CHAIN_DIR, exist_ok=True)
    h = hashlib.sha1(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest()
    day = time.strftime("%Y-%m-%d", time.gmtime())
    with open(os.path.join(AUDIT_CHAIN_DIR, f"{day}.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "hash": h, **record}, ensure_ascii=False) + "\n")
    return h

def audit_decision(kind: str, payload: dict):
    return audit_chain_commit(kind, payload)

def _attach_tradeoff(self, answer: dict, steps: list):
    try:
        ex = self.explainer.explain(steps or [])
        if ex: 
            answer["x_tradeoffs"] = ex
    except Exception:
        pass
    return answer

@dataclass
class WMItem:
    key: str
    value: Any
    priority: float = 0.5
    ttl: int = 6

@dataclass
class WorkingMemory:
    capacity: int = 9
    _buf: List[WMItem] = field(default_factory=list)
    def put(self, key, value, priority=0.5, ttl=6):
        """Put/replace key with priority & TTL, keep top-K by priority."""
        self._buf = [x for x in self._buf if x.key != key]
        self._buf.append(WMItem(key, value, priority, ttl))
        self._buf = sorted(self._buf, key=lambda x: x.priority, reverse=True)[:self.capacity]
    def get(self, key):
        for x in self._buf:
            if x.key == key:
                return x.value
    def decay(self):
        nxt = []
        for x in self._buf:
            x.ttl -= 1
            if x.ttl > 0: nxt.append(x)
        self._buf = nxt

def _resolve_memory_conflicts(items):
    try:
        seen = set(); out = []
        for s in items:
            k = s.strip().lower()
            k = k.replace("  ", " ")
            if k in seen: 
                continue
            # simple negate heuristic collapse
            k2 = k.replace(" tidak ", " ").replace(" bukan ", " ")
            if k2 in seen:
                continue
            seen.add(k)
            out.append(s)
        return out
    except Exception:
        return items
    
class EthicsEngine:
    RX_HARM = re.compile(r"(bom|ransomware|sql\s*injection|xss|ssrf|rce|payload|reverse\s*shell)", re.I)
    RX_ILLEGAL = re.compile(r"(curi|mencuri|maling|penipuan|carding|doxx?)", re.I)
    def score(self, text: str) -> dict:
        t = (text or "").lower()
        flags = []
        if self.RX_HARM.search(t): flags.append("harm")
        if self.RX_ILLEGAL.search(t): flags.append("illegal")
        return {"flagged": bool(flags), "flags": flags}
    def rewrite_safe(self, text: str) -> str:
        return ("Konten berisiko telah disaring. Saya bisa bantu dengan penjelasan "
                "keamanan/pertahanan, prinsip legal, atau alternatif yang etis.")

class SelfReflection:
    def polish(self, text: str) -> str:
        if not text: return text
        add = ("\n\n[Refleksi] Pastikan langkah aman, legal, dan hemat biaya. "
               "Nyatakan asumsi & risiko. Tawarkan opsi fallback.")
        return text + add
    
FREE_DAILY_REQUESTS = int(os.getenv("FREE_DAILY_REQUESTS", "200"))
FREE_DAILY_TOKENS   = int(os.getenv("FREE_DAILY_TOKENS",   "150000"))
FREE_DAILY_USD      = float(os.getenv("FREE_DAILY_USD",    "1.50"))
PRO_DAILY_REQUESTS  = int(os.getenv("PRO_DAILY_REQUESTS",  "5000"))
PRO_DAILY_TOKENS    = int(os.getenv("PRO_DAILY_TOKENS",    "3000000"))
PRO_DAILY_USD       = float(os.getenv("PRO_DAILY_USD",     "60.0"))

def _today_key():
    return time.strftime("%Y%m%d")

class QuotaGuard:
    def __init__(self):
        self.lock = threading.Lock()
        self.per_user = defaultdict(lambda: {"day": _today_key(),"req":0,"tok":0,"usd":0.0,"plan":"free"})
    def set_plan(self, user_id: str, plan: str):
        with self.lock:
            self.per_user[user_id]["plan"] = plan.lower().strip()
    def _limits(self, plan: str):
        return (PRO_DAILY_REQUESTS, PRO_DAILY_TOKENS, PRO_DAILY_USD) if plan=="pro" \
               else (FREE_DAILY_REQUESTS, FREE_DAILY_TOKENS, FREE_DAILY_USD)
    def check(self, user_id: str):
        today = _today_key()
        with self.lock:
            s = self.per_user[user_id]
            if s["day"] != today:
                s.update({"day": today, "req":0, "tok":0, "usd":0.0})
            R,T,U = self._limits(s["plan"])
            if s["req"] >= R:
                return False, "quota:requests"
            if s["tok"] >= T:
                return False, "quota:tokens"
            if s["usd"] >= U:
                return False, "quota:budget"
            return True, ""
    def add_usage(self, user_id: str, prompt_tok: int, compl_tok: int, usd: float):
        with self.lock:
            s = self.per_user[user_id]
            s["req"] += 1
            s["tok"] += int(prompt_tok or 0) + int(compl_tok or 0)
            s["usd"] += float(usd or 0.0)

class RateLimiter:
    def __init__(self, max_per_minute: int = 90):
        self.max = max(1, int(max_per_minute))
        self._win = defaultdict(list)
        self.lock = threading.Lock()
    def allow(self, user_id: str) -> bool:
        now = time.time()
        with self.lock:
            w = self._win[user_id]
            w[:] = [t for t in w if now - t < 60]
            if len(w) >= self.max:
                return False
            w.append(now);
            return True

class UserLimitManager:
    def __init__(self, quota, default_rpm=90):
        self.quota = quota
        from collections import defaultdict as _dd
        self.user_rpm = _dd(lambda: default_rpm)
        self.user_rate = _dd(lambda: RateLimiter(default_rpm))
        import threading as _th
        self.lock = _th.Lock()
    def set_user_limit(self, user_id, rpm=None, plan=None):
        with self.lock:
            if rpm is not None:
                self.user_rpm[user_id] = max(1, int(rpm))
                self.user_rate[user_id] = RateLimiter(self.user_rpm[user_id])
            if plan is not None:
                self.quota.set_plan(user_id, plan)
    def allow_request(self, user_id):
        if not self.user_rate[user_id].allow(user_id):
            return False, "rate:limit"
        ok, cat = self.quota.check(user_id)
        if not ok:
            return False, cat
        return True, ""

def run_crosscheck(tool, args):
    raise NotImplementedError

def _evidence_gate(prompt, draft):
    raise NotImplementedError

class ExecutiveController:
    _daemon_started: bool = False
    _daemon_lock: threading.Lock = threading.Lock()

    def __init__(self, wm: Optional[WorkingMemory] = None):
        self.wm = wm or WorkingMemory()
        seed_everything()

        # EARLY CORE
        self.tracer = DecisionTracer(base=os.getenv("AUDIT_DIR","/artifacts/audit"))
        # run lightweight startup checks (best-effort)
        try:
            from javu_agi.startup_checks import run_all as run_startup_checks
            start_ok = run_startup_checks()
            try:
                self.tracer.log("startup_checks", start_ok)
            except Exception:
                pass
        except Exception:
            pass
        self.memory = getattr(self, "memory", None) or MemoryManager()
        self.values = getattr(self, "values", None) or ValueMemory()
        self.world  = getattr(self, "world",  None) or WorldModel(memory=self.memory)

        try:
            from javu_agi.utils.config_loader import load_env
            load_env(default_path=os.getenv("CONFIG_FILE","config.py"))
        except Exception:
            pass

        # --- policy filter (tetap, no change) ---
        use_hard = os.getenv("POLICY_HARD", "1") == "1"
        self.policy_filter = PolicyFilterHard() if use_hard else PolicyFilter()

        # --- ENV toggles---
        use_ctx = os.getenv("CTX_LEARNER", "1") == "1"

        self._delib_on  = os.getenv("DELIBERATION_ENABLE","1") == "1"
        self._emb_on    = os.getenv("EMBODIMENT_ENABLE","1") == "1"
        self._lifelong  = os.getenv("ENABLE_LIFELONG","0") == "1"

        # === CORES ===
        self.self_model = getattr(self, "self_model", None) or SelfModel(values=self.values, memory=self.memory)
        self.reasoner = ReasoningEngine()

        # set metrics_dir
        self.metrics_dir = os.getenv("METRICS_DIR", "/data/metrics")
        os.makedirs(self.metrics_dir, exist_ok=True)

        # telemetry
        self.telemetry = Telemetry(base_dir=self.metrics_dir)

        # blok hash policy
        try:
            pol = os.getenv("SAFETY_POLICY","/opt/agi/safety/policy.yaml")
            h = hashlib.sha256(open(pol,"rb").read()).hexdigest()
            with open(os.path.join(self.metrics_dir,"policy.prom"),"a",encoding="utf-8") as f:
                f.write(f'policy_sha256{{path="{pol}"}} 0x{h}\n')
        except Exception:
            pass

        # === TOOLS & PLANNERS===
        self.tools = ToolRegistry()
        try:
            self.tools.register_builtin()
        except Exception:
            pass
        try:
            from javu_agi.utils.media_tools import register_media_tools
            register_media_tools(self.tools)
        except Exception:
            pass
        self.planner = Planner(use_skillgraph=True)
        self.planner_llm = LLMPlanner()
        self.gp = GoalPlanner(use_skillgraph=True)

        # graph + flag long
        self.graph = SkillGraph(cache_dir=SKILL_CACHE_DIR)
        use_long = os.getenv("LONG_HORIZON","1") == "1"
        self.planner_mcts = MCTSPlanner(self.world, self.planner_llm, self.graph) if use_long else None

        # === ROUTER & GROUNDING ===
        self.router = LLMRouter()
        try:
            from javu_agi.config import load_router_policy
            self.router.load_policy(load_router_policy())
            self.router.strict_caps = True
        except Exception as e:
            self.tracer.log("router_policy_err", {"err": str(e)})
        for comp in (self.reasoner, self.world, self.planner, self.planner_llm):
            try:
                if hasattr(comp, "set_router"):
                    comp.set_router(self.router)
                elif hasattr(comp, "router"):
                    setattr(comp, "router", self.router)
            except Exception:
                pass
        try:
            self.grounding = GroundingLayer(router=self.router)
        except Exception:
            self.grounding = None

        # LEARNERS & MEMORY
        self.rewards = RewardSystem()
        self.learner = PolicyLearner()
        self.learner_ctx = ContextualPolicyLearner(dim=8) if use_ctx else None
        self.credit = CreditAssigner()
        self.ltm = LongTermMemory(base_dir=os.getenv("METRICS_DIR", "/data/metrics"))

        # Long-horizon strategy
        try:
            self.long_horizon = LongHorizonPlanner(self.world, horizon=12)
        except Exception:
            self.long_horizon = None

        # === SKILLS & EXECUTION HELPERS ===
        self.binder = SkillBinder()
        self.composer = SkillComposer(max_skills=3)
        self.optimizer = PlanOptimizer(max_steps=8)
        self.budget = ExecutionBudget(max_steps=8, max_errors=2)
        self.result_cache = ResultCache(dirpath=RESULT_CACHE_DIR, ttl_s=3600, max_items=2000)
        self.skills = Competence()
        self.executor = ExecutionManager(
            self.tools,
            result_cache=self.result_cache,
            budget=self.budget,
            sustainability=getattr(self, "sustainability", None),
        )
        self._embed = embed
        self._reflector = ReflectiveLoop(window=50)
    
        # === BANDIT & GOALS ===
        self.goals = GoalManager()
        self.bandit = ToolBandit()

        # GUARDS & ALIGNMENT
        import sqlite3, datetime, os
        class _PerUserDailyBudget:
            def __init__(self, db_path: str, cap_usd: float):
                self.db_path = db_path; self.cap = cap_usd
                con = sqlite3.connect(self.db_path)
                con.execute("""
                            CREATE TABLE IF NOT EXISTS user_budget_daily(
                            user_id TEXT, day TEXT, spent_usd REAL NOT NULL DEFAULT 0,
                            PRIMARY KEY(user_id, day)
                            )
                            """)
                con.commit(); con.close()
            def spent(self, user_id: str) -> float:
                day = datetime.date.today().isoformat()
                con = sqlite3.connect(self.db_path)
                cur = con.execute("SELECT spent_usd FROM user_budget_daily WHERE user_id=? AND day=?", (user_id, day))
                row = cur.fetchone(); con.close()
                return float(row[0]) if row else 0.0
            def allow_estimate(self, steps, user_id: str) -> bool:
                return self.spent(user_id) < self.cap
            
        self.cost_guard = _PerUserDailyBudget(
            os.getenv("BUDGET_SQLITE_PATH", "/data/budget.db"),
            float(os.getenv("USER_BUDGET_FALLBACK_USD_DAILY","1e18")),
        )
        self.align = AlignmentChecker(policy_path=os.getenv("SAFETY_POLICY", "/opt/agi/safety/policy.yaml"))
        self.gov_guard = GovGuard()
        self.protect = FounderProtection(founder_id="roman")

        # === DISTILL, DEDUP, METRICS ===
        self.distill = DistillIO() if DISTILL_ENABLED else None
        self.dedup   = DistillDeduper() if DISTILL_ENABLED else None

        # === limits, drive, causal credit, embodiment ===
        self.ratelimit = RateLimiter(int(os.getenv("RL_MAX_PER_MIN", "90")))
        self.quota = QuotaGuard()
        self.limit_mgr = UserLimitManager(self.quota, default_rpm=int(os.getenv("RL_MAX_PER_MIN", "90")))
        self.drive = DriveSystem(world=self.world, rewards=self.rewards, memory=self.memory, align=self.align)
        self.credit_causal = CausalCreditAssigner()
        self.embodiment = Embodiment(self.tools)
    
        # === MBRL / META-RL / VALUES / ANOMALY ===
        self.meta_rl  = MetaPolicy(dim=8)
        self.meta_cog = MetaCognition(router=self.router, tracer=self.tracer)
        self.anom = AnomalyGuard()
        self.verify_step = verify_step
        self.synth_tool = synthesize_tool

        self.identity = DynamicIdentityManager()
        self.status = StatusBoard()
        self.orch = AgentOrchestrator(spawn_fn=self.process, max_parallel=int(os.getenv("MAX_SUBAGENTS","3")))

        # === Legacy ===
        try:
            self.causal_legacy = LegacyCausalAdapter(self.memory)
        except Exception:
            self.causal_legacy = None

        try:
            from javu_agi.meta_cognition import MetaCognition as LegacyMetaCognition
            self.meta_cog_legacy = LegacyMetaCognition()
        except Exception:
            self.meta_cog_legacy = None

        # === Human-level (guarded by ENV) ===
        self._causal_on   = (os.getenv("CAUSAL_ENABLE","1") == "1")
        self._metacog_on  = (os.getenv("METACOG_ENABLE","1") == "1")
        self._tom_on      = (os.getenv("TOM_ENABLE","1") == "1")
        self._emb_on      = (os.getenv("EMBODIMENT_ENABLE","1") == "1")
        self._valdyn_on   = (os.getenv("VALUE_DYNAMICS_ENABLE","1") == "1")

        try:
            self.causal = CausalReasoner(self.world, self.values) if self._causal_on else None
        except Exception:
            self.causal = None
        try:
            from javu_agi.static_plan_checker import check as _static_check
            eth_pre = getattr(self, "ethics", None) or getattr(self, "delib", None)
            eth_fn  = (lambda x: {"flagged": False}) if not eth_pre else (lambda t: eth_pre.check(t))
            self.metacog = MetaCognitiveMonitor(self.world, static_checker=_static_check, ethical_pre=eth_fn)
        except Exception:
            self.metacog = None
        try:
            self.tom = ToM(self.memory) if self._tom_on else None
        except Exception:
            self.tom = None
        try:
            self.valdyn = ValueDynamics(self.values, self.memory) if self._valdyn_on else None
        except Exception:
            self.valdyn = None

        # adapters registry
        self.domain_adapters = DOMAIN_ADAPTERS

        # deliberation
        mode = os.getenv("DELIB_MODE","collective" if os.getenv("ENABLE_DELIBERATION","1")=="1" else "off")
        if mode == "router" and self._delib_on:
            self.deliberator = Deliberator(self.router, n=3)
        elif mode == "collective":
            self.deliberator = CollectiveDeliberator()
        else:
            self.deliberator = None

        # embodiment
        self.emb = None
        try:
            if self._emb_on and hasattr(self, "body") and hasattr(self, "sensorimotor") and hasattr(self, "effect_guard"):
                self.emb = EmbodiedIntegrator(self.world, self.body, self.sensorimotor, self.memory, self.effect_guard)
        except Exception:
            self.emb = None
            
        self.adv_guard = AdversarialGuard(secret_scan=has_secret, egress_allow=egress_allow)
        self.delib  = EthicsDeliberator(policy=self.align, values=self.values)
        self.incident = IncidentEngine(os.path.join(self.metrics_dir, "security.prom"))
        self.effect_guard = EffectGuard()
        self.consent = ConsentLedger()
        self.board = OversightBoard(self.align, self.delib, self.gov_guard)
        self.calib = Calibrator(os.path.join(self.metrics_dir, "calibration.prom"))
        self.evaluator = EvaluationFramework()
        self.norms = NormativeFramework()
        self.human_values = HumanValuesInterface(self.memory, self.norms)
        self.alignment_auditor = AlignmentAuditor(self.memory, self.norms)
        self.peace = PeaceObjective()
        self.culture = CulturalAdapter()
        self.sustain = SustainabilityModel()
        self.commons = CommonsGuard()
        self.moral = MoralReasoningEngine()
        self.dialogue = DeliberativeDialogue(rounds=3)
        self.empathy = EmpathyModel()
        self.fair = FairnessAuditor()
        self.planet = PlanetaryGuardian()
        self.foresight = ForesightEngine(samples=200)
        self.mediator = ConflictMediator()
        self.meaning = MeaningFramework()
        self._ensure_learners()
        self.governance = CollectiveGovernance()
        self.dashboard = TransparencyDashboard()
        self.threat_modeler = ThreatModeler()
        self.ethics_updater = EthicsUpdateManager(self.norms)
        self.coop_learning = CooperativeLearning()
        self.audit_chain = AuditChain(log_dir=os.path.join(self.metrics_dir, "audit_chain"))
        self.oversight_queue = OversightQueue()
        self.dp_budget = DPBudget()
        self.expl_reporter = ExplanationReporter(out_dir=os.getenv("XAI_REPORT_DIR","reports"))
        self.contracts = ContractVerifier(default_contracts())
        self.supply = SupplyChainGuard(os.path.join(self.metrics_dir,"sbom.json"))
        self.soc_cog    = SocialCognition()
        self.empathy_fn = add_empathy
        self.val_refine = _refine
        self.treport    = make_report
        self.retention = DataRetentionManager(
            [os.getenv("XAI_REPORT_DIR","reports"), os.getenv("METRICS_DIR","/data/metrics")],
            ttl_days=int(os.getenv("DATA_TTL_DAYS","14"))
         )
        self.notifier = IncidentNotifier()
        self.peace_opt = PeaceOptimizer()
        self.resilience = ResilienceManager()
        self.meta_opt = MetaOptimizer()
        self.self_repair = getattr(self, "self_repair", None) or SelfRepairManager()
        self.policy_engine = getattr(self, "policy_engine", None) or PolicyEngine(
            os.getenv("SAFETY_POLICY", "/opt/agi/safety/policy.yaml")
        )
        # Lifelong learning
        if os.getenv("ENABLE_LIFELONG","0") == "1" and os.getenv("CANARY_APPROVED","0") == "1":
            self.lifelong = LifelongLearningManager(self.memory, self.evaluator, self.tools)
        else:
            self.lifelong = None

        # Continual Learner (behavioral)
        try:
            from javu_agi.continual_learner import ContinualLearner
            self.continual = ContinualLearner(user_id=os.getenv("CL_USER","default"))
        except Exception:
            self.continual = None

        # Moral/affective weights (pakai interface nilai manusia yang sudah ada)
        self.moral_affect = MoralEmotionEngine(self.human_values)

        # Cyber immune system + provenance
        class _WatchdogShim:
            def __init__(self, tracer): self.tracer = tracer
            def freeze_process(self, pid):
                # non-invasive: hanya log & set incident counter
                try:
                    self.tracer.log("immune_freeze", {"pid": pid})
                except Exception:
                    pass

        self.watchdog = _WatchdogShim(self.tracer)
        self.provenance = ProvenanceGuard(artifact_paths=["requirements.txt", "config.py"])
        # anomaly detector = self.anom (sudah ada)
        self.immune = CyberImmuneCore(self.watchdog, self.anom, self.provenance)

        # Impact & collective governance
        self.impact = ImpactAssessor()
        self.collective = CollectiveGovernanceHub(stakeholders=["humanity","ecology","future_generations"])

        # Explainability
        self.explainer = ValueTradeoffExplainer()

        # Creativity & aesthetics
        self.aesthetics = AestheticJudgment()
        self.creator = CrossDomainCreator()

        # Embodiment loop
        self.body = BodySchema()
        self.sensorimotor = SensorimotorLoop(self.world, self.body)
        try:
            if self._emb_on:
                self.emb = EmbodiedIntegrator(self.world, self.body, self.sensorimotor, self.memory, self.effect_guard)
        except Exception:
            self.emb = None
        
        #runtime deps
        self.model = getattr(self, "model", getattr(self, "router", None))
        self.backup_model = getattr(self, "backup_model", self.model)

        self.supervision = SupervisionLayer()

        if not hasattr(self, "learner"):
            self.learner = LifelongLearner(self.model, self.memory)

        if hasattr(self, "model") and hasattr(self, "backup_model"):
            self.self_healer = SelfHealing(self.model, self.backup_model)

        self.ckpt = CheckpointIO()
        # --- FIX checkpoint object names (no crash) ---
        for (nm, obj) in [
            ("meta_rl", getattr(self, "meta", None)),
            ("meta_cog", getattr(self, "meta_cog", None)),
            ("mbrl",    getattr(self, "mbrl", None)),
            ("value_mem", getattr(self, "values", None)),
        ]:
            try:
                if obj is not None:
                    self.ckpt.load(nm, obj)
            except Exception:
                pass

        def _reload(_):
            try:
                from javu_agi.security.fsguard import _ALLOW
                from javu_agi.security.tool_acl import _load_acl
                _ALLOW = None; _load_acl.cache_clear()
            except Exception:
                pass
        paths = [os.getenv("SAFETY_POLICY","/opt/agi/safety/policy.yaml"),
                 os.getenv("FS_ALLOWLIST","/opt/agi/governance/fs_allowlist.txt"),
                 os.getenv("TOOL_ACL_PATH","/opt/agi/governance/tool_acl.json")]
        try:
            FileWatcher(paths, _reload).start(interval=float(os.getenv("POLICY_WATCH_MS","2000"))/1000.0)
        except Exception:
            pass

        try:
            from javu_agi.security.redteam_probe import RedTeamDaemon
            if os.getenv("REDTEAM_ENABLE","1") == "1":
                def _attack(payload: str):
                    chk = self.adv_guard.scan_prompt(payload)
                    blocked = not chk["ok"]
                    if not blocked:
                        self.tracer.log("redteam_fail", {"payload": payload, "flags": chk.get("flags",[])})
                    else:
                        self.tracer.log("redteam_ok", {"payload": payload})
                        lvl = self.incident.incr("redteam_fail")
                        msg = self.incident.maybe_action(self)
                        if msg:
                            self.tracer.log("incident_action", {"level": lvl, "action": msg})
                    return {"blocked": blocked, "why": "adv_scan"}
                self._redteam = RedTeamDaemon(_attack, interval_sec=int(os.getenv("REDTEAM_INTERVAL","1200")))
                self._redteam.start()
        except Exception:
            pass
        
        # policy
        from javu_agi.safety.safety_adapters import PolicyAdapter
        self.policy = getattr(self, "policy", PolicyAdapter(self.policy_filter))

        # ethics engine → adapter .check()
        ethics_engine = getattr(self, "ethics_engine", None)
        if ethics_engine is None:
            ethics_engine = EthicsEngine()
        from javu_agi.safety.safety_adapters import EthicsCheckerAdapter
        self.ethics = getattr(self, "ethics", EthicsCheckerAdapter(ethics_engine))

        self.eco = EcoGuard()
        try:
            _ledger = {}
            try:
                _tel = getattr(self, "telemetry", None)
                if _tel and hasattr(_tel, "get_ledger"):
                    _ledger = _tel.get_ledger("planetary") or {}
            except Exception:
                pass
            self.sustainability = SustainabilityGuard(PlanetaryPolicy.from_path(POLICY_PATH),
                                                      ledger=_ledger)
        except Exception:
            self.sustainability = None

        try:
            from javu_agi.governance.policy_watcher import FileWatcher
            ETH_DIR = os.getenv("ETHICS_DIR", "/opt/agi/ethics")
            def _on_ethics_change(p):
                try:
                    self.ethics_updater.reload_from_dir(ETH_DIR)
                    self.tracer.log("ethics_update", {"path": p})
                    self.audit_chain.commit("ethics_update", {"path": p})
                    if hasattr(self.oversight_queue, "notify"):
                        self.oversight_queue.notify({"type":"ethics_update","path":p})
                except Exception as e:
                    self.tracer.log("ethics_update_err", {"err": str(e), "path": p})
            FileWatcher(ETH_DIR, on_change=_on_ethics_change).start()
        except Exception:
            pass

        # HITL gate:
        self._hitl_required = os.getenv("HITL_REQUIRED","0") in {"1","true","yes"}

        def _audit_decision(self, kind: str, payload: dict):
            try:
                h = self.audit_chain.commit(kind=kind, record=payload)
                return h
            except Exception:
                return None

        def _require_hitl(self, intent: dict) -> bool:
            if not self._hitl_required:
                return False
            risk = float(intent.get("risk", 0.0))
            return risk >= float(os.getenv("RISK_MAX", "0.55"))

        # Society-of-AGIs + Corrigibility
        self.society = MultiAgentGovernance()
        self.corrigible = CorrigibilityManager(self.consent, self.ethics)

        try:
            from javu_agi.governance.policy_watcher import FileWatcher
            from javu_agi.config import load_router_policy
            pol_path = os.getenv("ROUTER_POLICY", "/opt/agi/config/router_policy.yaml")
            self._router_watch = FileWatcher(pol_path, on_change=lambda p: self.router.load_policy(load_router_policy()))
            self._router_watch.start()
        except Exception:
            pass

        self.dev_fast = os.getenv("DEV_FAST","0") == "1"
        if self.dev_fast:
            try:
                if hasattr(self, "_redteam"):
                    getattr(self._redteam, "stop", lambda: None)()
                self.tracer.log("dev_fast","on")
            except Exception:
                pass

        # safety: checker
        from javu_agi.safety.safety_adapters import SafetyChecker
        self.safety = getattr(self, "safety", SafetyChecker())
  
        # === BACKGROUND FEEDERS ===
        try:
            self._ensure_autonomy_feeder()
        except Exception:
            pass
        
    def plan_route(self, query: str, domain: str | None = None):
        try:
            if domain:
                from javu_agi.tools.tool_contracts import run_with_contract
                return run_with_contract(query, domain)
            return self.planner.plan(query)
        except Exception as e:
            return {"status":"error","where":"plan_route","err":str(e)}
        
    # ENTRYPOINT untuk core_loop
    def process(self, user_id: str, text: str) -> tuple[str, dict]:
        t0 = time.time()
        safe_in = shield(text or "")
        role = self.identity.infer_role(safe_in)
        meta = {"episode_ts":
                int(t0), "role":
                getattr(role, "name", "generalist")}
        ok, why = self.limit_mgr.allow_request(user_id or "anon")
        if not ok:
               return f"[RATE/BUDGET BLOCK] {why}", {"blocked": True, "reason": why}
        kb_ctx = ""
        try:
            kb_ctx = kb_retrieve(safe_in, k=6)
        except Exception:
            kb_ctx = ""
        if kb_ctx:
            safe_in = f"KB_CONTEXT:\n{kb_ctx}\n\nTASK:\n{safe_in}"
        adv = self.adv_guard.scan_prompt(safe_in)
        if not adv.get("ok", True):
            return "[BLOCKED] adversarial input detected", {"blocked": True, "flags": adv.get("flags", [])}
        role_hint = ""
        try:
            role_hint = (
                f"[ROLE:{getattr(role,'name','generalist')}] "
                f"tone={getattr(role,'tone','neutral')}; "
                f"tools={','.join(getattr(role,'allow_tools',[]) or [])}; "
                f"tags={','.join(getattr(role,'policy_tags',[]) or [])}"
            )
        except Exception:
            role_hint = "[ROLE:generalist]"
        plan = self.plan_route(f"{role_hint}\n\n{safe_in}")
        if plan.get("status") != "ok":
            return f"[PLANNER:{plan.get('status')}] {plan.get('hint') or plan.get('safety')}", {"plan": plan}
        steps = plan.get("steps", [])
        meta["plan_steps"] = len(steps)
        meta["domains"] = plan.get("domains", [])
        meta["role"] = getattr(role, "name", "generalist")
        try:
            eco = self.eco.score(task=safe_in, plan=json.dumps(steps)[:2000])
            if not eco.get("allow", True):
                return "[VETO] EcoGuard", {"veto": "eco", "eco": eco}
            if self.sustainability:
                pchk = self.sustainability.assess({"steps": steps})
                if not pchk.get("permit", True):
                    return "[VETO] SustainabilityGuard", {"veto": "planet", "planet": pchk}
        except Exception:
            pass
        if not self.cost_guard.allow_estimate(steps, user_id=user_id or "anon"):
            return "[BUDGET GUARD] Too expensive", {"blocked": True, "reason": "budget"}
        result = self.executor.run_plan(steps, input_text=safe_in, user_id=user_id or "anon")
        text_out = result.get("text") or result.get("output") or ""
        try:
            if self.fair and hasattr(self.fair, "rewrite_if_needed"):
                text_out = self.fair.rewrite_if_needed(text_out)
        except Exception:
            pass
        try:
            if self.tom:
                text_out = self.empathy_fn(text_out)
        except Exception:
            pass
        out = self._finalize_reply(text_out)
        meta.update({
            "latency_s": round(time.time()-t0, 3),
            "plan_conf": plan.get("confidence", 0.6),
            "domains": plan.get("domains", []),
            "runtime_breaker": 0,
        })
        self._append_metrics(meta, is_gov=False, prompt=safe_in)
        try:
            self.status.record(meta)
        except Exception:
            pass
        return out.get("text",""), meta                    

    def get_eval_snapshot(self) -> dict:
        return {
            "ts": int(time.time()),
            "router": getattr(self.router, "status", lambda: {})(),
            "budget_caps": {
                "daily_usd": float(os.getenv("DAILY_SPEND_USD","10")),
                "hourly_usd": float(os.getenv("HOURLY_SPEND_USD","2")),
            },
            "governance_mode": getattr(self, "gov", {}).get("mode", "enforce"),
            "kill_switch": os.getenv("KILL_SWITCH","0") in {"1","true","TRUE"},
            "model_meta": getattr(self, "model_meta", {}),
        }
    
    # ---------- features for contextual bandit ----------
    def _features(self, prompt: str, u: float, nov: float) -> List[float]:
        p = prompt.lower()
        d_science = 1.0 if any(k in p for k in ["fisika","energi","materi","kuantum","gelap"]) else 0.0
        d_econ    = 1.0 if any(k in p for k in ["ekonomi","harga","pasar"]) else 0.0
        d_code    = 1.0 if any(k in p for k in ["kode","program","algoritma"]) else 0.0
        d_general = 1.0 if (d_science + d_econ + d_code) == 0.0 else 0.0
        L = min(1.0, max(0.0, len(p)/2000.0))
        return [1.0, u, nov, L, d_science, d_econ, d_code, d_general]  # dim=8

    def _repair_plan(self, prompt: str, steps: list, failed_idx: int, last_stdout: str) -> list:
        """
        Coba perbaiki rencana setelah step gagal.
        Menghasilkan 0–2 langkah repair yang sudah lolos static-check & verifier.
        """
        try:
            # 1) bentuk konteks singkat
            prev = steps[max(0, failed_idx-2): failed_idx]
            prev_txt = "\n".join(f"- {s.get('tool','?')} {s.get('cmd','')}" for s in prev)
            failed = steps[failed_idx]
            ftxt = f"{failed.get('tool','?')} {failed.get('cmd','')}"
            ctx = (
                "You are a planning corrector. Prior steps:\n"
                f"{prev_txt}\n"
                f"Failed step:\n- {ftxt}\n"
                "STDOUT/ERR (truncated):\n"
                f"{(last_stdout or '')[:400]}\n\n"
                "Produce up to 2 minimal recovery steps to reach the user goal. "
                "Avoid repeating the failing command. Keep it safe & deterministic."
            )

            # 2) minta perbaikan dari planner LLM (atau fallback Planner)
            try:
                rec = self.planner_llm.plan(ctx)
                cand = (rec.steps or [])[:2]
            except Exception:
                rec = self.planner.plan(ctx); cand = (rec.steps or [])[:2]

            # 3) static check
            try:
                from javu_agi.static_plan_checker import check
                ok, why = check(cand)
                if not ok:
                    return []
            except Exception:
                pass

            # 4) verifier strict per-step (buang yang tidak lolos)
            out =[]
            strict = os.getenv("VERIFY_STRICT","1") == "1"
            worker = os.getenv("TOOL_WORKER_URL") or "sandbox://dry"
            for st in cand:
                try:
                    ok, _ = self.verify_step(self.tools, worker,
                                             {"tool": st.get("tool"), "cmd": st.get("cmd"), "strict": strict},
                                             self.executor)
                    if ok: out.append(st)
                except Exception:
                    pass
            if out:
                try:
                    self.graph.add_recipe(f"repair::{hashlib.sha1(prompt.encode()).hexdigest()}", out)
                    self.tracer.log("repair_recipe_added", {"n": len(out)})
                except Exception:
                    pass
            return out[:2]
        except Exception:
            return []
        
    # AGI: Self-Model
    def _self_model_update(self, reward: float, errors: int, conf: float, cost_usd: float):
        sm = getattr(self, "_self_model", {"competence":0.5, "reliability":0.5, "cost":0.0})
        sm["competence"]  = 0.90*sm["competence"]  + 0.10*max(0.0, min(1.0, reward))
        sm["reliability"] = 0.90*sm["reliability"] + 0.10*(1.0/(1.0 + max(0,errors)))
        sm["cost"]        = 0.90*sm["cost"]        + 0.10*float(cost_usd or 0.0)
        self._self_model = sm
        try:
            self.wm.put("self_model", sm, priority=0.9, ttl=8)
        except Exception:
            pass

    # AGI: Task Inference
    def _infer_task(self, prompt: str) -> dict:
        try:
            obj = prompt.strip()
            cons = []
            if "tanpa" in prompt.lower(): cons.append("avoid:" + prompt.lower().split("tanpa",1)[1][:80])
            succ = "measurable outcome stated; minimize cost & risk"
            return {"objective": obj, "constraints": cons, "success": succ}
        except Exception:
            return {"objective": prompt, "constraints": [], "success": "ok"}

    # AGI: Active Experimenter
    def _maybe_experiment(self, prompt: str, steps: list, u: float) -> list:
        if u < 0.70: 
            return []
        try:
            rp = self.planner_llm.plan(
                f"Rancang 1 langkah probe kecil untuk menurunkan ketidakpastian soal: {prompt}. "
                "Hanya 1 langkah, aman, tanpa efek destruktif."
            )
            cand = (getattr(rp, "steps", None) or [])[:1]
            from javu_agi.static_plan_checker import check
            ok, _ = check(cand)
            return cand if ok else []
        except Exception:
            return []

    # AGI: Value-Aware Scoring
    def _rescore_plan(self, prompt: str, steps: List[dict], user_id: str = "auto") -> List[dict]:
        try:
            scored = []
            for s in (steps or []):
                cmd = s.get("cmd","")
                # skor dari world model
                try:
                    conf = float(self.world.value_estimate(prompt, cmd))
                except Exception:
                    conf = 0.5

                # penalti risiko dari simulator
                try:
                    sim = self.world.simulate_action(cmd)
                    risk = 0.0 if sim.get("risk_level","low") == "low" else 0.3
                except Exception:
                    risk = 0.1

                # shaping nilai
                try:
                    shaped = self.values.shape(conf, {"human_impact": 1.0 - risk, "env_impact": 0.5})
                except Exception:
                    shaped = conf - risk

                # affect-weights boost
                boost = 0.0
                try:
                    aw = self.wm.get("affect_weights") or {}
                    boost = 0.05 * (float(aw.get("prosocial_weight",1.0)) - 1.0)    - 0.05 * (float(aw.get("risk_aversion",1.0)) - 1.0)
                except Exception:
                    pass

                # fairness / ethics shaping
                try:
                    fair = self.fair.audit_candidate(s)
                    shaped = shaped - 0.05 * float(fair.get("bias_risk",0.0))
                except Exception:
                    pass
                try:
                    ethics = self.moral.evaluate(s)
                    shaped = shaped - 0.05 * float(ethics.get("ethical_risk",0.0))
                except Exception:
                    pass

                # sustainability gate (permit + soft penalty)
                try:
                    if self.sustainability:
                        res = self.sustainability.assess(s)
                        s["_eco_flags"] = res.get("flags", [])
                        if not res.get("permit", True):
                            continue
                        shaped -= 0.25 * len([f for f in res.get("flags", []) if "sector_cap" in f])
                except Exception:
                    pass

                scored.append((shaped + boost, s))

            # rank
            steps = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)]

            # integrate ToM
            try:
                if self.tom:
                    stakeholders = ["user","bystanders","environment"]
                    appr = self.tom.predict_reaction(steps, stakeholders)
                    def _adj(s):
                        p = min(appr.values()) if appr else 0.6
                        s = dict(s)
                        s["_tom_approval"] = p
                        return s
                    steps = [_adj(s) for s in steps]
                    steps = sorted(steps, key=lambda z: z.get("_tom_approval",0.6), reverse=True)
            except Exception:
                pass
            scored.append((shaped + boost, s)) 
            steps = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)]

            return steps
        except Exception:
            return steps or []

    def _maybe_escalate(self, risk: float, ethical_flags: list[str], impact: float, ctx: dict):
        if risk >= 0.6 or impact >= 0.7 or ("harm" in ethical_flags):
            try:
                self.oversight_queue.notify({"type":"review_required", "risk":risk, "impact":impact, **ctx})
                self.tracer.log("oversight_escalate", {"risk":risk,"impact":impact})
                return True
            except Exception:
                return False

        # notify continual learner
        try:
            if self.continual and steps:
                self.continual.ingest({"goal": prompt[:128], "steps": steps[:6], "result": "plan_selected"})
        except Exception:
            pass
                    
        # ==== integrate causal + ToM + metacog (fail-safe) ====
        try:
            if self.causal:
                steps = self.causal.recommend(prompt, steps)
        except Exception:
            pass
        # === legacy causal reasoning adapter ===
        try:
            if getattr(self, "causal_legacy", None):
                user_id_val = locals().get("user_id", "auto")
                steps = self.causal_legacy.annotate(user_id_val, prompt, steps)
                steps = self.causal_legacy.rerank(steps)
        except Exception:
            pass
        try:
            if self.tom:
                stakeholders = ["user","bystanders","environment"]
                appr = self.tom.predict_reaction(steps, stakeholders)
                # penalti jika approval rendah
                def _adj(s):
                    p = min(appr.values()) if appr else 0.6
                    s["_tom_approval"]=p
                    return s
                steps = [ _adj(dict(s)) for s in steps ]
                steps = sorted(steps, key=lambda z: z.get("_tom_approval",0.6), reverse=True)
        except Exception:
            pass
        return steps

    def _uncertainty_gate(self, prompt: str, conf: float) -> Optional[dict]:
        if conf < float(os.getenv("EARLY_EXIT_CONFIDENCE","0.88")):
            if conf < float(os.getenv("UNCERTAINTY_CLARIFY_THRESHOLD","0.65")):
                q = f"Klarifikasi cepat: tujuan spesifik untuk '{prompt[:100]}'? " \
                    "Batasan, data yang boleh dipakai, dan hasil yang diinginkan?"
                return {"status":"need_clarify","question": q}
            return {"status":"abstain","reason":"low_confidence"}
        return None

    # AGI: Skill Induction
    def _maybe_induce_skill(self, steps_texts: list, out_lines: list, reward: float):
        if os.getenv("SKILL_INDUCTION_ENABLE","0") != "1":
            return
        if float(reward) < 0.70: 
            return
        trace = "\n".join(out_lines or [])[:4000]
        tool = None
        try:
            tool = self.synth_tool(steps_texts, trace)  # sudah kamu import
        except Exception:
            tool = None
        try:
            if tool and hasattr(self.binder, "install"):
                self.binder.install(self.tools, tool)
                try:
                    self.graph.register_tool(tool)
                except Exception:
                    pass
        except Exception:
            pass

    def _finalize_reply(self, text: str) -> dict:
        meta = {}
        critique = None
        try:
            if self.dashboard:
                self.dashboard.log_decision({"reply": text})
        except Exception as e:
            self.tracer.log("dashboard_log_err", {"err": str(e)})
        try:
            if self.metacog:
                text = self.metacog.self_critique(text)
        except Exception:
            pass
        trace = []
        try:
            wm_trace = self.wm.get("reasoning_trace")
            if isinstance(wm_trace, list): trace = wm_trace
        except Exception:
            pass
        if getattr(self, "meta_cog_legacy", None):
            try:
                critique = self.meta_cog_legacy.critique(
                    plan=self.wm.get("last_plan") or [],
                    reasoning_trace=self.wm.get("reasoning_trace") or []
                )
                self.tracer.log("meta_cog_legacy", critique)
            except Exception:
                pass
        meta["critique"] = critique
        try:
            if hasattr(self, "_reflector"):
                text = self._reflector.polish(text)
            if critique is not None:
                meta["critique"] = critique
        except Exception:
            pass
        
        # continual learner: outcome logging (reward proxy)
        try:
            if self.continual:
                self.continual.ingest({"goal":"-", "steps":[], "result":"finalized", "reward": 0.8})
        except Exception:
            pass

        try:
            sig = sign_output(text)
            self.tracer.log("wm_sig", {"sig": sig["wm"]})
            return {"status":"ok","text": sig["text"], "wm": sig["wm"]}
        except Exception:
            return {"status":"ok","text": text}

    def on_feedback(self, fb: dict):
        """
        Update bobot nilai prososial/risiko/lingkungan
        """
        try:
            if self.valdyn:
                self.valdyn.update_from_feedback(fb)
        except Exception:
            pass

    def _pick_adapter(self, tool: str) -> str:
        t = (tool or "").lower()
        if any(k in t for k in ["bash","shell","fs","file"]): return "files"
        if any(k in t for k in ["web","http","browser","curl"]): return "web"
        if any(k in t for k in ["git","python","node","pip","npm","code"]): return "code"
        return "generic"

    def _notify(self, event: str, payload: dict):
        # 1) IncidentNotifier
        try:
            if hasattr(self, "notifier") and hasattr(self.notifier, "send"):
                self.notifier.send(event, payload)
        except Exception:
            pass
        # 2) Operational notify (webhooks/stdout)
        try:
            _op_notify(event, payload or {})
        except Exception:
            pass
        # 3) Telemetry file
        try:
            if _tel_notify:
                _tel_notify(event, payload or {})
        except Exception:
            pass

    def _value_est(self, prompt: str, cmd: str, tool: str) -> float:
        try:
            adp = self._pick_adapter(tool)
            return float(self.world.value_estimate(prompt, cmd, adapter=adp))
        except Exception:
            return 0.5

    def _simulate(self, x) -> dict:
        try:
            adp = "generic"
            if isinstance(x, str): pass
            elif isinstance(x, dict): adp = self._pick_adapter(x.get("tool",""))
            return self.world.simulate_action(x, adapter=adp)
        except Exception:
            return {"risk_level":"low","expected_confidence":0.6}
    
    def _write_metric(self, name: str, labels: dict, val: float):
        try:
            path = os.path.join(self.metrics_dir, "meta.prom")
            lab = ",".join(f'{k}="{v}"' for k,v in (labels or {}).items())
            with open(path,"a",encoding="utf-8") as f:
                f.write(f'{name}{{{lab}}} {float(val)}\n')
        except Exception:
            pass

    def _append_metrics(self, meta: dict, is_gov: bool, prompt: str):
        try:
            prom = os.path.join(self.metrics_dir, "metrics.prom")
            with open(prom, "a", encoding="utf-8") as f:
                f.write(f"dp_epsilon_used {getattr(self.dp_budget,'used',0.0)}\n")
                f.write(f"runtime_breaker_total {int(meta.get('runtime_breaker',0))}\n")
                f.write(f"exec_latency_seconds {meta.get('latency_s',0)}\n")
                f.write(f"exec_verifier_score {meta.get('verifier',{}).get('score',0.0)}\n")
                f.write(f"exec_reward {meta.get('reward',0.0)}\n")
                f.write(f"exec_hallucination_rate {meta.get('hallucination_rate',0.0)}\n")
                if is_gov or str(prompt).lower().strip().startswith("gov:"):
                    f.write("gov_requests_total 1\n")
        except Exception:
            pass

    def _xai_report(
        self, tag, status, steps, affect_weights, impact_scores, gates,
        chosen=None, candidates=None, episode_id: str | None = None, trace_id: str | None = None
        ):
        # render XAI HTML + simpan JSONL untuk audit_router
        out_dir = os.getenv("XAI_DIR", "artifacts/xai").rstrip("/ ")
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass
        try:
            payload = self.expl_reporter.build_payload(
                episode_id=episode_id or "",
                trace_id=trace_id or "",
                plan_steps=steps or [],
                chosen=chosen or {},
                candidates=candidates or [],
                affect_weights=affect_weights or {},
                impact_scores=impact_scores or {},
                gates=gates or {},
                explainer_dict=self.explainer.explain({"name": status}, affect_weights or {}, impact_scores or {}),
                audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                provenance_tag=tag,
                status=status
            )
            # normalisasi trace_id
            trace = (
                payload.get("trace_id")
                or (payload.get("meta", {}) or {}).get("trace")
                or f"trace_{int(time.time())}"
            )
            payload["trace_id"] = trace

            # PAYLOAD
            try:
                self.expl_reporter.write(payload)
            except Exception:
                pass

            # HTML via explain_ui
            try:
                from javu_agi.xai.explain_ui import write as _xai_write_html
                _xai_write_html(payload, out_dir=out_dir)
            except Exception:
                try:
                    from javu_agi.xai.explain_ui import write as _xai_write_html
                except Exception:
                    from xai.explain_ui import write as _xai_write_html
            
            # JSONL audit
            try:
                with open(os.path.join(out_dir, f"{trace}.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception:
                pass

            # notify UI/observer
            try:
                if hasattr(self, "notifier"):
                    self.notifier.send("xai_saved", {"trace": trace, "dir": out_dir})
            except Exception:
                pass

        except Exception:
            pass

    def _needs_evidence(self, prompt: str) -> bool:
        p = (prompt or "").lower()
        risky = ("kesehatan" in p or "medis" in p or "obat" in p or
                 "investasi" in p or "saham" in p or "crypto" in p or
                 "kontrak" in p or "hukum" in p or "perjanjian" in p)
        return risky

    def _evidence_gate(self, prompt: str, draft: dict) -> dict:
        try:
            if not self._needs_evidence(prompt): 
                return draft
            checked = fact_check(draft.get("text","")[:4000])  # returns {"ok":bool,"sources":[...]}
            draft["x_fact_ok"] = bool(checked.get("ok"))
            draft["x_sources"] = checked.get("sources", [])[:5]
            if not draft["x_fact_ok"]:
                draft["text"] = "Maaf, butuh verifikasi sumber. " \
                                "Saya tidak akan berspekulasi. Ringkasan aman:\n" + draft.get("text","")[:800]
            return draft
        except Exception:
            return draft
            
    def _ensure_learners(self):
        try:
            if not hasattr(self, "learner") and hasattr(self, "model") and hasattr(self, "memory"):
                self.learner = LifelongLearner(self.model, self.memory)
        except Exception as e:
            self.tracer.log("ensure_learners_error", {"err": str(e)})
        
    def tick(self) -> dict:
        """
        Satu langkah otonomi: pilih goal → jalankan → logging & pembelajaran.
        Tidak butuh prompt dari user.
        """
        self._ensure_learners()

        # cyber immune self-heal tiap tick
        try:
            self.immune.self_heal()
        except Exception:
            pass
        
        # gate safety: kill-switch & quota
        if os.getenv("KILL_SWITCH","0") in {"1","true","TRUE"}:
            return {"status":"blocked","reason":"killswitch"}

        # pilih goal
        try:
            g = pick_goal(self.goals, self.drive, self.memory)
        except Exception:
            g = None
        if not g:
            return {"status":"idle","reason":"no_goal"}

        prompt = g.get("prompt","").strip()
        gid    = g.get("id","auto")

        # jalankan pipeline standar (governance, planner, verifier, value shaping, MBRL, meta-RL)
        res = self.process(user_id="auto", prompt=prompt, meta={"goal_id": gid, "proactive": True})

        # lifelong + continual update post-process
        try:
            if getattr(self, "lifelong", None) and hasattr(self.lifelong, "step"):
                self.lifelong.step(self)
        except Exception:
            pass
        try:
            if getattr(self, "continual", None):
                self.continual.reflect()
                self.continual.consolidate()
                self.continual.update_policy()
                self.continual.rehearse()
        except Exception:
            pass

        # embodiment loop
        try:
            obs = self.world.observe()
            sm = self.sensorimotor.tick(obs)
            self.memory.store("sensorimotor", sm)
        except Exception:
            pass

        # embodiment integrator cycle
        try:
            if self.emb:
                self.emb.cycle()
        except Exception as e:
            self.tracer.log("emb_cycle_err", {"err": str(e)})

        # test_data
        test_data = getattr(self, "test_data", None)
        if test_data is None and hasattr(self.world, "get_test_data"):
            test_data = self.world.get_test_data()

        # evaluasi model
        if hasattr(self, "evaluator") and hasattr(self, "model") and hasattr(self.model, "predict"):
            accuracy, eval_time = self.evaluator.evaluate_model(self.model, test_data or [])
            self.tracer.log("model_evaluation", {"accuracy": accuracy, "eval_time": eval_time})

        # Check error rate
        try:
            error_rate = float(getattr(self.model, "get_error_rate", lambda: 0.0)())
            if hasattr(self, "self_healer"):
                self.self_healer.self_heal(error_rate)
        except Exception:
            pass

        # Distillation/marking disabled in vendor-only mode
        pass

        # update goal manager
        try:
            if hasattr(self.goals, "report"):
                self.goals.report(gid, success=(res.get("status")=="executed"))
        except Exception:
            pass

        try:
            self._write_metric("heartbeat", {"mode":"tick"}, 1.0)
            if is_degraded():
                self._write_metric("mode_degraded", {}, 1.0)
        except Exception:
            pass

        # --- resource snapshot + hygiene ---
        try:
            if getattr(self, "resilience", None):
                self.resilience.snapshot()
                if self.resilience.overloaded():
                    self.resilience.degrade_gracefully()
        except Exception:
            pass

        try:
            self.retention.purge()
        except Exception:
            pass

        return {"status":"ticked", "goal_id": gid, "result": res}

    def run_autonomy(self, max_ticks: int = 10, sleep_s: float = 2.0) -> dict:
        self.human_values.sync_to_norms()
        # --- Long horizon strategy ---
        try:
            if getattr(self, "long_horizon", None):
                strategy = self.long_horizon.plan(self.goals.list_all(), horizon=10)
                self.tracer.log("long_horizon_plan", strategy)
        except Exception as e:
            self.tracer.log("long_horizon_error", {"err": str(e)})
            
        from javu_agi.autonomy import AutonomyGate
        gate = AutonomyGate()
        out = {"ticks": 0, "done": False, "stopped": False}
        for i in range(int(max_ticks)):
            if not gate.is_on():
                out["stopped"] = True; break
            if not self.budget.allow(i, 0):
                out["done"] = True; break
            r = self.tick()
            out["ticks"] += 1
            # throttle
            try: time.sleep(max(0.0, float(sleep_s)))
            except Exception: pass
        return out
 
    # ---- policy ----
    def _estimate_uncertainty(self, prompt: str) -> float:
        u = self.world.estimate_uncertainty(prompt)
        self.wm.put("uncertainty", u, priority=0.8, ttl=4)
        return u

    def _choose_modes(self, prompt: str, u: float, novelty: float) -> List[str]:
        if self.learner_ctx:
            x = self._features(prompt, u, novelty)
            pick = self.learner_ctx.choose(x)["arm"]
            base = {"S1":["S1","S2","S3"], "S2":["S2","S3","S1"], "S3":["S3","S2","S1"]}[pick]
        else:
            first, _ = self.learner.choose(prompt)
            base = {"S1":["S1","S2","S3"], "S2":["S2","S3","S1"], "S3":["S3","S2","S1"]}[first]
        if u > 0.6 or novelty > 0.6:
            base = ["S3","S2","S1"]
        return base

    def _maybe_clarify(self, user_id: str, ep: str, prompt: str, u: float) -> Optional[str]:
        if not ENABLE_AUTO_CLARIFY or u < UNCERTAINTY_CLARIFY_THRESHOLD:
            return None
        q = f"Catatan: konteks belum lengkap; asumsikan skenario umum untuk: {prompt[:96]}..."
        log_node(user_id, ep, "CLARIFY", {"ask": q}, module="meta")
        return q

    def _try_tools(self, user_id: str, ep: str, prompt: str, context: List[str]) -> Optional[str]:
        p = prompt.lower()
        if "ringkas" in p or "format" in p:
            res = self.tools.run("json_filter", {"data": {"text": " ".join(context)}, "expr":"."})
            return f"[TOOL] {res}"
        return None

        # === Autonomy Feeder (ADD-ONLY) ===
    def _autonomy_feeder_worker(self):
        import time as _t, random as _r, json as _json
        interval = int(os.getenv("AUTONOMY_FEED_INTERVAL_SEC", "600"))  # default 10 menit
        if os.getenv("AUTONOMY_FEED_ENABLE", "1") != "1":
            return
        while True:
            try:
                if KillSwitch.is_active():
                    _t.sleep(30); continue

                # 1) coba emergent will
                g = self.drive.generate("system")
                # 2) fallback aman
                if not g:
                    g = generate_goal("system")

                if g and g.get("status", "ok") == "ok" and g.get("goal"):
                    pr = float(g.get("priority", 0.6))
                    meta = _json.dumps(g.get("meta", {}))
                    # GoalManager API: .add(title, detail, priority)
                    self.goals.add(title=g["goal"], detail=meta, priority=int(100*pr))

            except Exception:
                pass

            # jitter kecil biar gak sinkron
            _t.sleep(max(60, interval) + _r.random()*5.0)

    def _ensure_autonomy_feeder(self):
        """Start feeder sekali saja."""
        if getattr(self.__class__, "_feeder_started", False):
            return
        with self.__class__._daemon_lock:
            if getattr(self.__class__, "_feeder_started", False):
                return
            import threading as _th
            t = _th.Thread(target=self._autonomy_feeder_worker, daemon=True)
            t.start()
            self.__class__._feeder_started = True

    def _maybe_plan_and_execute(self, user_id: str, prompt: str, meta: dict | None = None):
        
        t0 = time.time()
        episode_id, trace_id = None, None
        if os.getenv("KILL_SWITCH","0") in {"1","true","TRUE"}:
            return {"status":"blocked","reason":"killswitch"}
        
        try:
            from javu_agi.telemetry import new_ids
            episode_id, trace_id = new_ids()
        except Exception:
            pass

        th = TamperHash()
        jpath = journal_path(self.metrics_dir, episode_id or "ep")
        seed = set_seed(trace_id)
        ep_dir = make_workspace(os.getenv("EP_BASE_WORKDIR","/data/work"), episode_id or "ep")
        os.environ["EP_WORKDIR"] = ep_dir

        safe_prompt = shield(prompt)

        if not verify_input(safe_prompt):
            return {"status":"blocked","reason":"wm_verify_failed"}

        try:
            ok, why = self.protect.check(safe_prompt)
            if not ok:
                self.tracer.log("founder_block", {"why": why})
                return {"status":"blocked","reason":"founder_protection"}
        except Exception:
            pass

        # --- shed load if system is hot ---
        try:
            if getattr(self, "resilience", None):
                self.resilience.snapshot()
                if self.resilience.should_shed_load():
                    self.tracer.log("shed_load", getattr(self.resilience, "last_metrics", {}))
                    if hasattr(self, "notifier"):
                        self._notify("deny_or_block", {"reason": "shed_load", "trace": trace_id})
                    return {"status": "blocked", "reason": "shed_load"}
        except Exception:
            pass

        # Autonomy/Goal feeder
        try:
            self._ensure_autonomy_feeder()
        except Exception:
            pass

        # === Rate/Quota enforcement ===
        ok, why = self.limit_mgr.allow_request(user_id)
        if not ok:
            self.tracer.log("rate_quota_block", {"user": user_id, "reason": why})
            return {"status": "blocked", "reason": why}
        
        # skills
        try:
            skill_steps = self.composer.compose(safe_prompt)
        except Exception:
            skill_steps = []

        intent_id = f"{trace_id}.intent"
        context   = {"user": user_id, "jurisdiction": os.getenv("JURIS", "ID")}
        record_intent(intent_id, "EC", {"prompt": safe_prompt}, context)
            
        # draft via LLMPlanner → fallback Planner
        try:
            plan_llm = self.planner_llm.plan(safe_prompt)
            llm_steps = plan_llm.steps or []
        except Exception:
            try:
                plan_llm = self.planner.plan(safe_prompt)
                llm_steps = plan_llm.steps or []
            except Exception as e:
                return {"status":"error","error": f"[PLAN_ERROR] {e}"}

        # --- meta-optimizer hint (non-binding) ---
        try:
            if getattr(self, "meta_opt", None):
                hint = self.meta_opt.suggest()
                self.tracer.log("meta_opt_hint", hint)        
        except Exception:
            pass

        # expand graph
        steps = self.graph.expand_and_cache((skill_steps or []) + (llm_steps or []))
        
        # MCTS
        try:
            if getattr(self, "planner_mcts", None):
                steps = self.planner_mcts.plan(safe_prompt) or steps
        except Exception:
            pass
        
        if self.deliberator:
            verdict = self.deliberator.consensus(Plan)
            self.tracer.log("deliberation", verdict)
            if verdict.get("consensus", 0) < 0.5:
                Plan.insert(0, {"cmd": "verify", "args": "low consensus, do extra check"})

        # --- Counterfactual compare LLM vs MCTS ---
        try:
            from javu_agi.interpret.counterfactuals import prefer as _cf_pref
            cand_llm = llm_steps or []
            cand_mcts = []
            if getattr(self, "planner_mcts", None):
                try:
                    cand_mcts = self.planner_mcts.plan(safe_prompt) or []
                except Exception:
                    cand_mcts = []
            if cand_mcts:
                cf = _cf_pref(cand_llm, cand_mcts)
                self.tracer.log("counterfactual_pick", cf)
                steps = cand_llm if cf["prefer"] == "A" else cand_mcts
            else:
                steps = cand_llm
        except Exception:
            steps = llm_steps or []
        
        # optimize
        steps = self.optimizer.optimize(steps)

        # Self-model & world-model sync
        try:
            obs = self.world.observe()
            self.tracer.log("world_obs", obs or {})
            self.self_model.update_competence(meta.get("domain","general"), success=True)
        except Exception as e:
            self.tracer.log("self_world_err", {"err": str(e)})

        try:
            steps = self.peace_opt.optimize(steps)
        except Exception:
            pass

        # Lifelong step awal
        try:
            if hasattr(self, "lifelong") and hasattr(self.lifelong, "step"):
                _lifelong_info = self.lifelong.step(self)
                self.tracer.log("lifelong_stage", _lifelong_info)
        except Exception as e:
            self.tracer.log("lifelong_error", {"err": str(e)})

        # Normative & Long-Horizon Layer
        norm_eval = self.norms.evaluate(steps, context)
        moral = self.moral.analyze(steps, context)
        dialog = self.dialogue.debate(steps, context)
        empath = self.empathy.assess(steps, [PersonModel(role="user", consent=0.7)])
        sustain = self.sustain.simulate(steps)
        commons = self.commons.check(steps)
        planet = self.planet.assess(steps)
        foresight = self.foresight.simulate(" ".join(map(str,steps)).lower())

        # adapt for culture (soft modulation only)
        adapted = self.culture.adapt(context, norm_eval["final_score"])

        # meta-cognition over current reasoning trace (if available)
        reasoning_trace = [str(s) for s in steps]
        meta = self.meta_cog.critique(steps, reasoning_trace)

        # Social cognition / empathy shaping
        try:
            intent = (meta.get("intent") or "").lower()
            if intent in {"empathy","support","counsel"}:
                input_text = self.empathy.shape(input_text)  # nada & framing
            else:
                sc = self.soc_cog.analyze(input_text, meta)
                if sc: self.tracer.log("social_cognition", sc)
        except Exception as e:
            self.tracer.log("social_empathy_err", {"err": str(e)})

        # --- Human values sync ---
        try:
            self.human_values.sync_to_norms()
        except Exception as e:
            self.tracer.log("human_values_sync_error", {"err": str(e)})

        # --- Threat modeling ---
        try:
            threats = self.threat_modeler.generate(steps or [])
            self.tracer.log("threats", threats)
        except Exception as e:
            self.tracer.log("threat_modeler_error", {"err": str(e)})

        # --- Ethics update (context injection) ---
        try:
            self.ethics_updater.update_from_context(context or {})
        except Exception as e:
            self.tracer.log("ethics_update_error", {"err": str(e)})

        # Moral affect → weights utk planning
        try:
            affect_signals = {
                "suffering": max(0.0, float(empath.get("harm_observed", 0.0))),
                "harm_by_agent": 0.0,  # isi kalau ada estimator internal
                "help_received": 0.0,
                "injustice": max(0.0, float(moral.get("injustice", 0.0))),
                "beauty": 0.0,
            }
            self.moral_affect.update(affect_signals)
            affect_weights = self.moral_affect.weight_adjustment()
            try:
                self.wm.put("affect_weights", affect_weights, priority=0.7, ttl=3)
            except Exception:
                pass
        except Exception:
            affect_weights = {"prosocial_weight":1.0,"risk_aversion":1.0,"justice_weight":1.0,"aesthetic_weight":1.0}

        status = "pre_execute"

        # Cyber immune scan (pre-exec)
        try:
            _scan = self.immune.scan_and_isolate({"pid": os.getpid(), "kind": "plan_build"})
            self.tracer.log("immune_scan", _scan)
            try:
                report_payload = self.expl_reporter.build_payload(
                    episode_id=episode_id,
                    trace_id=trace_id,
                    plan_steps=steps or [],
                    chosen={"name":"approved_plan"} if status=="executed" else {},
                    candidates=(locals().get("scored_candidates") or []),
                    affect_weights=affect_weights if 'affect_weights' in locals() else {},
                    impact_scores=impact_scores if 'impact_scores' in locals() else {},
                    gates={
                        "commons": commons if 'commons' in locals() else {},
                        "planet": planet if 'planet' in locals() else {},
                        "peace": p if 'p' in locals() else {},
                        "collective": _cg if '_cg' in locals() else {}
                    },
                    explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                    audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,  # best-effort, boleh kosong
                    provenance_tag="pre_execute",
                    status=status
                )
                self.expl_reporter.write(report_payload)
            except Exception:
                pass
            if isinstance(_scan, dict) and (not _scan.get("ok", True) or _scan.get("isolated", False)):
                self.tracer.log("immune_block", _scan)
                if hasattr(self, "notifier"):
                    self._notify("deny_or_block", {"reason": "immune_isolation", "trace": trace_id})
                try:
                    if getattr(self, "resilience", None):
                        self.resilience.on_exec_fail()
                except Exception:
                    pass
                try:
                    if getattr(self, "meta_opt", None):
                        self.meta_opt.update("blocked")
                except Exception:
                    pass
                status = "pre_execute"
                return {"status":"blocked","reason":"immune_isolation"}
        except Exception as e:
            self.tracer.log("immune_scan_error", {"err": str(e)})

        # Impact assessor utk scoring dampak rencana
        try:
            plan_proxy = {
                "name": "auto",
                "harm_prob": float(foresight.get("risk_prob", 0.0)),
                "polarization_risk": float(dialog.get("polarization", 0.0)),
                "energy_cost": float(planet.get("energy_cost", 0.0)),
                "resource_cost": float(planet.get("resource_cost", 0.0)),
                "inequality_risk": float(norm_eval.get("inequality_risk", 0.0)),
            }
            impact_scores = self.impact.score(plan_proxy)
        except Exception:
            impact_scores = {"human":0.7,"community":0.7,"ecology":0.7,"economic":0.7,"composite":0.7}
            
        # merge risk
        risk = {}
        risk.update(norm_eval); risk.update({"moral": moral})
        risk.update({"dialogue": dialog}); risk.update(empath)
        risk.update(sustain); risk.update(commons); risk.update({"planet": planet})
        risk.update({"threats": threats})
        risk.update({"foresight": foresight}); risk.update(meta)
        risk["adapted_score"] = adapted

        verdict, reason = None, None
        goto_deny = True
        early_escalate = True

        # hard gates
        if COMMONS_ENFORCE and commons.get("commons_safe") is False:
            verdict, reason = "deny", "commons_guard"
            goto_deny = True
        if float (planet.get("eco_risk", 0)) > ECO_RISK_MAX:
            verdict, reason = "deny", "planetary_guardian"
            goto_deny = True
        if dialog.get("stance") == "deny" or moral.get("stance") == "deny":
            verdict, reason = "deny", "moral_dialogue"
            goto_deny = True

        # --- peace optimizer (idempotent) ---
        try:
            if getattr(self, "peace_opt", None):
                steps = self.peace_opt.optimize(steps)
        except Exception:
            pass

        # --- POLICY ENGINE DECISION GATE ---
        try:
            decision, why = self.policy_engine.evaluate({"goal": prompt}, steps or [])
            if decision == "block":
                self._notify("deny_or_block", {"reason": why, "trace": trace_id})
                return {"status": "blocked", "reason": why}
            if decision == "escalate":
                self._notify("escalate", {"reason": why, "trace": trace_id})
                return {"status": "needs_review", "reason": why}
        except Exception:
            pass

        # --- multi-agent debate (opsional) ---
        try:
            if getattr(self, "debate", None):
                d = self.debate.debate(prompt, {"steps": steps}, rounds=2)
                self.tracer.log("debate", d)
                if (d.get("verdict") or "").lower() == "review":
                    steps = steps[: max(1, len(steps)//2)]
                    if "early_escalate" in locals():
                        early_escalate = True
        except Exception:
            pass

        # Gate impact + affect
        IMPACT_FLOOR = float(os.getenv("IMPACT_FLOOR", "0.50"))
        # penalize jika risk_aversion tinggi
        impact_adjusted = impact_scores["composite"] - 0.10*(affect_weights.get("risk_aversion",1.0)-1.0)
        if impact_adjusted < IMPACT_FLOOR:
            verdict, reason = "deny", "negative_impact"
            goto_deny = True
        try:
            p = self.peace.assess(steps)
            if float(p.get("peace_risk",0.0)) > float(os.getenv("PEACE_RISK_MAX","0.40")):
                verdict, reason = "deny", "peace_objective"
                goto_deny = True
        except Exception:
            pass

        # if indecisive, escalate early
        if norm_eval["stance"] == "escalate" or dialog.get("stance") == "escalate":
            early_escalate = True

        if 'goto_deny' in locals() and goto_deny:
            audit_chain_commit("deny_reason", {"reason": reason, "trace": trace_id})
            record = {
                "intent_id": intent_id, "verdict": "deny", "risk": risk,
                "plan_len": len(steps), "reason": reason, "oversight": "n/a"
            }
            self._reflector.log_decision(record)
            self.tracer.log("reflective_report", self._reflector.reflect())
            self.tracer.log("explainability", explain_decision(record))
            try:
                self.dashboard.log_decision(
                    self.explainer.explain({"name": "denied"}, affect_weights, impact_scores)
                )
            except Exception:
                pass
            
            try:
                status = "denied"
                report_payload = self.expl_reporter.build_payload(
                    episode_id=episode_id,
                    trace_id=trace_id,
                    plan_steps=steps or [],
                    chosen={"name":"approved_plan"} if status=="executed" else {},
                    candidates=(locals().get("scored_candidates") or []),
                    affect_weights=affect_weights if 'affect_weights' in locals() else {},
                    impact_scores=impact_scores if 'impact_scores' in locals() else {},
                    gates={
                        "commons": commons if 'commons' in locals() else {},
                        "planet": planet if 'planet' in locals() else {},
                        "peace": p if 'p' in locals() else {},
                        "collective": _cg if '_cg' in locals() else {}
                    },
                    explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                    audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,  # best-effort, boleh kosong
                    provenance_tag="pre_execute",
                    status=status
                )
                self.expl_reporter.write(report_payload)
            except Exception:
                pass
            if hasattr(self, "notifier"):
                self._notify("deny_or_block", {"reason": "shed_load", "trace": trace_id})
            try:
                if getattr(self, "meta_opt", None):
                        self.meta_opt.update("blocked")
            except Exception:
                pass
            status = "denied"
            return {"status":"denied", "reason": reason}

        if 'early_escalate' in locals() and early_escalate:
            # enqueue oversight request & pause
            self.oversight_queue.submit({
                "intent_id": intent_id, "plan": steps, "risk": risk, "context": context
            })
            record = {
                "intent_id": intent_id, "verdict": "approve",
                "risk": risk, "plan_len": len(steps or []),
                "reason": "ok", "oversight": "-"
            }
            self._reflector.log_decision(record)
            self.tracer.log("reflective_report", self._reflector.reflect())
            self.tracer.log("explainability", explain_decision(record))
            try:
                self.dashboard.log_decision(self.explainer.explain({"name":"pending_escalation"}, affect_weights, impact_scores))
            except Exception:
                pass
            status = "pre_execute"
            return {"status":"pending_approval", "intent_id": intent_id}

        if getattr(self, "deliberator", None) and steps:
            try:
                verdict = self.deliberator.consensus(steps)
                self.tracer.log("deliberation", verdict)
                if float(verdict.get("consensus", 0)) < 0.5:
                    steps.insert(0, {"tool": "verifier", "cmd": "deep_check", "args": "low consensus"})
            except Exception:
                pass

        # Ethical deliberation gate
        verdict = self.delib.evaluate(prompt, steps)
        self.tracer.log("ethics_verdict", {"allow": getattr(verdict, "allow", True),
                                           "score": getattr(verdict, "score", None),
                                           "rationale": getattr(verdict, "rationale", "")})
        try:
            self.dashboard.log_decision(
                self.explainer.explain({"name": "simulated"}, affect_weights, impact_scores)
            )
        except Exception:
            pass
        if not verdict.allow:
            try:
                self.dashboard.log_decision(
                    self.explainer.explain({"name": "blocked"}, affect_weights, impact_scores)
                )
            except Exception:
                pass
            try:
                report_payload = self.expl_reporter.build_payload(
                    episode_id=episode_id,
                    trace_id=trace_id,
                    plan_steps=steps or [],
                    chosen={"name":"approved_plan"} if status=="executed" else {},
                    candidates=(locals().get("scored_candidates") or []),
                    affect_weights=affect_weights if 'affect_weights' in locals() else {},
                    impact_scores=impact_scores if 'impact_scores' in locals() else {},
                    gates={
                        "commons": commons if 'commons' in locals() else {},
                        "planet": planet if 'planet' in locals() else {},
                        "peace": p if 'p' in locals() else {},
                        "collective": _cg if '_cg' in locals() else {}
                    },
                    explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                    audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                    provenance_tag="pre_execute",
                    status=status
                )
                self.expl_reporter.write(report_payload)
            except Exception:
                pass
            status = "pre_execute"
            return {"status":"blocked", "reason":"ethics", "rationale": verdict.rationale, "remedies": verdict.remedies}

        sim = EthicsSimulator()
        sim_result = sim.simulate_plan(steps, {"user": user_id})
        risk.update({"ethics_sim": sim_result})
        self.tracer.log("ethics_sim", sim_result)

        # --- Oversight board decision (gabungan) ---
        try:
            ob = self.board.decide(prompt, steps)
            self.tracer.log("oversight_votes", ob)
            if not ob.get("allow", False):
                try:
                    self.dashboard.log_decision(
                        self.explainer.explain({"name": "blocked"}, affect_weights, impact_scores)
                    )
                except Exception:
                    pass
                try:
                    report_payload = self.expl_reporter.build_payload(
                        episode_id=episode_id,
                        trace_id=trace_id,
                        plan_steps=steps or [],
                        chosen={"name":"approved_plan"} if status=="executed" else {},
                        candidates=(locals().get("scored_candidates") or []),
                        affect_weights=affect_weights if 'affect_weights' in locals() else {},
                        impact_scores=impact_scores if 'impact_scores' in locals() else {},
                        gates={
                            "commons": commons if 'commons' in locals() else {},
                            "planet": planet if 'planet' in locals() else {},
                            "peace": p if 'p' in locals() else {},
                            "collective": _cg if '_cg' in locals() else {}
                        },
                        explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                        audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                        provenance_tag="pre_execute",
                        status=status
                    )
                    self.expl_reporter.write(report_payload)
                except Exception:
                    pass
                status = "pre_execute"
                return {"status": "blocked", "reason": "oversight", "detail": ob.get("why","blocked")}
        except Exception:
            self.tracer.log("err_tag", {"err": str(e)})

        try:
            self.treport.emit("preexec", {
                "steps": steps or [],
                "risk": risk, "impact": impact_scores,
                "gates": {"ethics": verdict.allow if 'verdict' in locals() else None}
            })
        except Exception as e:
            self.tracer.log("transparency_err", {"err": str(e), "stage": "preexec"})

        # SNAPSHOT PLAN (resume support)
        try:
            plan_snap = {
                "ts": int(time.time()*1000),
                "episode": episode_id, "trace": trace_id,
                "user": user_id,
                "prompt": safe_prompt,
                "steps": steps,
            }
            try:
                if hasattr(self, "audit_chain_commit"):
                    self.audit_chain_commit({...})   # jejak hasil, bukan distill
                else:
                    self.tracer.log("result_record", {...})
            except Exception as e:
                self.tracer.log("audit_err", {"err": str(e)})
        except Exception:
            pass

        # value-aware rescore
        try:
            steps = self._rescore_plan(steps, safe_prompt)
        except Exception:
            pass

        # static/capability gates
        ok, why = check(steps)
        if not ok:
            return {"status":"blocked", "error": why}
        try:
            steps = filter_steps(steps, allowed_categories())
        except Exception:
            pass
        
        if not validate_plan(steps):
            try:
                self.dashboard.log_decision(
                    self.explainer.explain({"name": "blocked"}, affect_weights, impact_scores)
                )
            except Exception:
                pass
            try:
                report_payload = self.expl_reporter.build_payload(
                    episode_id=episode_id,
                    trace_id=trace_id,
                    plan_steps=steps or [],
                    chosen={"name":"approved_plan"} if status=="executed" else {},
                    candidates=(locals().get("scored_candidates") or []),
                    affect_weights=affect_weights if 'affect_weights' in locals() else {},
                    impact_scores=impact_scores if 'impact_scores' in locals() else {},
                    gates={
                        "commons": commons if 'commons' in locals() else {},
                        "planet": planet if 'planet' in locals() else {},
                        "peace": p if 'p' in locals() else {},
                        "collective": _cg if '_cg' in locals() else {}
                    },
                    explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                    audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                    provenance_tag="pre_execute",
                    status=status
                )
                self.expl_reporter.write(report_payload)
            except Exception:
                pass
            status = "pre_execute"
            return {"status":"blocked","error":"tool_schema_invalid"}

        # Collective governance veto (multi-stakeholder)
        try:
            _cg = self.collective.aggregate([{
                "name":"plan",
                "public_good_score": float(impact_scores.get("human",0.0)),
                "inequality_risk": float(norm_eval.get("inequality_risk",0.0))
            }])
            if not _cg or _cg.get("governance_note") != "selected_by_collective_hub":
                try:
                    self.dashboard.log_decision(
                        self.explainer.explain({"name": "blocked"}, affect_weights, impact_scores)
                    )
                except Exception:
                    pass
                try:
                    report_payload = self.expl_reporter.build_payload(
                        episode_id=episode_id,
                        trace_id=trace_id,
                        plan_steps=steps or [],
                        chosen={"name":"approved_plan"} if status=="executed" else {},
                        candidates=(locals().get("scored_candidates") or []),
                        affect_weights=affect_weights if 'affect_weights' in locals() else {},
                        impact_scores=impact_scores if 'impact_scores' in locals() else {},
                        gates={
                            "commons": commons if 'commons' in locals() else {},
                            "planet": planet if 'planet' in locals() else {},
                            "peace": p if 'p' in locals() else {},
                            "collective": _cg if '_cg' in locals() else {}
                        },
                        explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                        audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                        provenance_tag="pre_execute",
                        status=status
                    )
                    self.expl_reporter.write(report_payload)
                except Exception:
                    pass
                status = "pre_execute"
                return {"status":"blocked","reason":"collective_governance"}
        except Exception as e:
            self.tracer.log("collective_error", {"err": str(e)})

        # Corrigibility check (honor human override jika ada)
        try:
            override = self.corrigible.override((meta or {}).get("human_command", {}))
            if not override.get("accepted", True):
                try:
                    self.dashboard.log_decision(
                        self.explainer.explain({"name": "blocked"}, affect_weights, impact_scores)
                    )
                except Exception:
                    pass
                try:
                    report_payload = self.expl_reporter.build_payload(
                        episode_id=episode_id,
                        trace_id=trace_id,
                        plan_steps=steps or [],
                        chosen={"name":"approved_plan"} if status=="executed" else {},
                        candidates=(locals().get("scored_candidates") or []),
                        affect_weights=affect_weights if 'affect_weights' in locals() else {},
                        impact_scores=impact_scores if 'impact_scores' in locals() else {},
                        gates={
                            "commons": commons if 'commons' in locals() else {},
                            "planet": planet if 'planet' in locals() else {},
                            "peace": p if 'p' in locals() else {},
                            "collective": _cg if '_cg' in locals() else {}
                        },
                        explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                        audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,
                        provenance_tag="pre_execute",
                        status=status
                    )
                    self.expl_reporter.write(report_payload)
                except Exception:
                    pass
                status = "pre_execute"
                return {"status":"blocked","reason":"corrigibility_override_denied"}
        except Exception as e:
            self.tracer.log("corrigibility_error", {"err": str(e)})

        # INSERT: SHADOW PLANNER SCORE (TANPA EKSEKUSI)
        try:
            shadow = self.planner.plan(safe_prompt).steps
            sp = score_plan(self.world, safe_prompt, shadow)
            self._write_metric("shadow_plan_score", {}, float(sp))
        except Exception:
            pass

        # --- metrics: panjang rencana ---
        try:
            lbl = {"goal": (meta or {}).get("goal_id", "-")}
            self._write_metric("plan_length", {}, float(len(steps or [])))
        except Exception:
            pass

        try:
            meta = (meta or {})
            meta["task"] = self._infer_task(safe_prompt)
        except Exception:
            pass

        # --- TELEMETRY: PLAN BUILT ---
        try:
            self.telemetry.emit("plan_built", {
                "episode": episode_id,            
                "trace":   trace_id,
                "plan_len": len(steps or []),
                "user":     user_id               
            })
        except Exception:
            pass

        # --- confidence gate & auto replan ---
        try:
            plan_txt = "\n".join(f"{s.get('tool','')} {s.get('cmd','')}" for s in (steps or []))
            conf0 = float(self.world.value_estimate(safe_prompt, plan_txt))
        except Exception:
            conf0 = 0.0

        MIN_CONF = float(os.getenv("MIN_PLAN_CONF","0.25"))
        if conf0 < MIN_CONF:
            try:
                if getattr(self, "planner_mcts", None):
                    steps = self.planner_mcts.plan(safe_prompt) or steps
                else:
                    steps = self.planner_llm.plan(safe_prompt).steps or steps
            except Exception:
                try:
                    steps = self.planner.plan(safe_prompt).steps or steps
                except Exception:
                    pass
            steps = self.optimizer.optimize(steps)

        try:
            u = float(self.world.estimate_uncertainty(safe_prompt))
        except Exception:
            u = 0.0
        try:
            probes = self._maybe_experiment(safe_prompt, steps, u)
            if probes:
                steps = probes + (steps or [])
        except Exception:
            pass

        # model-based improve
        try:
            from javu_agi.mbrl import MBPlanner
            mbp = MBPlanner(self.world.mb)
            steps = mbp.improve(state=prompt, base=steps)
        except Exception:
            pass

        try:
            self.treport.emit("preplan", {
                "meta": meta, "prompt": safe_prompt,
                "steps": steps or [], "uncertainty": u
            })
        except Exception as e:
            self.tracer.log("transparency_err", {"err": str(e), "stage": "preplan"})

        pol = self.policy_filter.check(steps)
        try:
            report_payload = self.expl_reporter.build_payload(
                episode_id=episode_id,
                trace_id=trace_id,
                plan_steps=steps or [],
                chosen={"name":"approved_plan"} if status=="executed" else {},
                candidates=(locals().get("scored_candidates") or []),
                affect_weights=affect_weights if 'affect_weights' in locals() else {},
                impact_scores=impact_scores if 'impact_scores' in locals() else {},
                gates={
                    "commons": commons if 'commons' in locals() else {},
                    "planet": planet if 'planet' in locals() else {},
                    "peace": p if 'p' in locals() else {},
                    "collective": _cg if '_cg' in locals() else {}
                },
                explainer_dict=self.explainer.explain({"name": status}, affect_weights if 'affect_weights' in locals() else {}, impact_scores if 'impact_scores' in locals() else {}),
                audit_head=getattr(self.audit_chain, "_AuditChain__dict__", None) or None,  # best-effort, boleh kosong
                provenance_tag="pre_execute",
                status=status
            )
            self.expl_reporter.write(report_payload)
        except Exception:
            pass
        status = "pre_execute"
        if not pol.get("ok", False):
            return {"status":"blocked","reason": pol.get("reason","policy_failed")}

        steps_texts = [s.get("cmd","") for s in steps]
        sim = self.world.simulate_plan(steps_texts)
        self.wm.put("last_plan_sim", sim, priority=0.7, ttl=3)

        safe = (sim.get("risk_level","high") == "low" and sim.get("expected_confidence",0.0) >= 0.6)
        worker = os.getenv("TOOL_WORKER_URL")
        out_lines, errors = [], 0
        try:
            self.dashboard.log_decision(
                self.explainer.explain({"name":"simulated"}, affect_weights, impact_scores)
            )
        except Exception:
            pass

        status = "pre_execute"

        if not worker or not safe:
            return {"status":"simulated","steps": len(steps), "sim": sim}

        # --- JOURNAL PATH ---
        try:
            jpath
        except NameError:
            jpath = journal_path(self.metrics_dir, episode_id or "ep")

        # Resume index
        resume_i = 0
        try:
            J = load_journal(jpath) or []
            done_idx = [int(x.get("i", -1)) for x in J if isinstance(x, dict) and "i" in x]
            resume_i = (max(done_idx) + 1) if done_idx else 0
        except Exception:
            resume_i = 0

        # --- INISIALISASI HITL COUNTER ---
        miss = getattr(self, "_miss_ctr", 0)

        # transparency dashboard (approved plan)
        try:
            self.dashboard.log_decision(self.explainer.explain({"name":"approved_plan"}, affect_weights, impact_scores))
        except Exception:
            pass

        status = "pre_execute"

        # --- PRECOMPUTE GOVERNANCE / IMPACT SIGNALS (safe defaults) ---
        impact_scores, commons, planet, p, _cg = {}, {}, {}, {}, {}
        try:
            impact_scores = self.impact.assess(steps or [])
        except Exception:
            pass
        try:
            commons = self.commons.check(steps or [])
        except Exception:
            pass
        try:
            planet = self.planet.assess(steps or [])
        except Exception:
            pass
        try:
            p = self.peace.assess(steps or [])
        except Exception:
            pass
        try:
            _cg = self.collective.vote(steps or [], context or {})
        except Exception:
            pass

        # provenance snapshot
        try:
            self.provenance.snapshot("pre_execute", {
                "episode": episode_id,
                "trace": trace_id,
                "steps": len(steps or [])
            })
        except Exception:
            pass

        try:
            apath = os.path.join(ARTIFACTS_DIR, "provenance.log")
            with open(apath, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": int(time.time()), "ep": episode_id, "trace": trace_id, "kind":"pre_execute"})+"\n")
            os.chmod(apath, 0o444)  # best-effort set read-only; real WORM pakai storage policy
        except Exception:
            pass
        
        for i in range(resume_i, len(steps)):
            s = steps[i]
            tool = (s.get("tool","?") or "").lower()
            cmd  = (s.get("cmd","") or "")
            # --- PRE-FLIGHT CHECK (policy + optional human approval) ---
            try:
                action = {"cmd": cmd, "tool": tool, "context": {"intent_id": intent_id, "episode_id": episode_id}}
                pf = preflight_action(user_id or "anon", action)
                if not pf.get("allow", False):
                    # block immediately
                    if pf.get("mode") == "block":
                        out_lines.append(f"[BLOCK] policy deny for: {cmd[:160]}")
                        miss += 1; self._miss_ctr = miss
                        # already audited inside helper
                        if miss >= 3:
                            break
                        continue
                    # pending -> enqueue/short-wait sync (configurable)
                    if pf.get("mode") == "pending":
                        rid = pf.get("approval_rid")
                        # synchronous short wait for admin/testing; in prod prefer non-blocking
                        apro = enforce_approval_blocking(rid, timeout_s=int(os.getenv("APPROVAL_WAIT_S", "5")))
                        if not apro.get("approved", False):
                            out_lines.append(f"[PENDING] approval required for: {cmd[:120]}")
                            miss += 1; self._miss_ctr = miss
                            if miss >= 3:
                                break
                            continue
                       # approved -> fall through to execute
            except Exception:
                # fail-safe: if preflight errors, be conservative: block this step
                try:
                    self.tracer.log("preflight_err", {"tool": tool, "cmd": cmd})
                except Exception:
                    pass
                out_lines.append("[BLOCK] preflight evaluation error")
                miss += 1; self._miss_ctr = miss
                if miss >= 3:
                  break
                continue
            # DP GUARD
            dp_cost = 0.05 if ("search" in tool or "db" in tool) else 0.01
            if not self.dp_budget.allow(dp_cost):
                self.tracer.log("dp_block", {"tool": tool, "cost": dp_cost})
                status = "pre_execute"
                return {"status": "blocked", "reason": "dp_budget_exceeded"}

            # ANCHOR: sebelum menjalankan worker.run/tool.execute pada tiap step
            if ("http" in cmd.lower() or tool in {"http","curl","browser","fetch"}):
                if not check_host(cmd):
                    out_lines.append(f"[BLOCK] egress host not allowed: {cmd[:160]}")
                    continue

            if not killswitch_guard():
                out_lines.append("[BLOCK] killswitch engaged; halting execution")
                break
            # RUNTIME RISK RE-CHECK (breaker)
            live = self._simulate({"tool": tool, "cmd": s.get("cmd","")})
            if live.get("risk_level", "low") != "low" or float(live.get("expected_confidence", 0)) < 0.5:
                self.tracer.log("runtime_breaker", {"i": i, "live": live})
                audit_chain_commit("breaker", {"i": i, "live": live, "trace": trace_id})
                break  # soft-stop; setelah loop selesai kita return executed partial

            # --- RISK GATE (prediksi MBRL) ---
            try:
                state_txt = self.world.current_state().as_text() if hasattr(self.world, "current_state") else ""
            except Exception:
                state_txt = ""
            if risky(self.world, state_txt, tool, cmd):
                out_lines.append(f"[SKIP] high-risk: {tool} {cmd}")
                # HITL escalate
                miss += 1
                self._miss_ctr = miss
                if miss >= 3:
                    try:
                        hook = os.getenv("HUMAN_REVIEW_WEBHOOK","")
                        if hook:
                            import json, threading, urllib.request
                            def _post(url, data):
                                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                                             headers={"Content-Type":"application/json"})
                                urllib.request.urlopen(req, timeout=2)
                            payload = {
                                "episode": episode_id, "trace": trace_id,
                                "prompt": prompt, "step": i, "tool": tool, "cmd": cmd,
                                "reason": "risk_or_verify_fail_3x"
                            }
                            # non-blocking fire-and-forget (urllib only)
                            import threading, json, urllib.request

                            def _post(url, data):
                                req = urllib.request.Request(
                                    url,
                                    data=json.dumps(data).encode("utf-8"),
                                    headers={"Content-Type": "application/json"},
                                )
                                urllib.request.urlopen(req, timeout=2)

                            threading.Thread(target=_post, args=(hook, payload), daemon=True).start()
                            stdout_signed = sign_output(stdout)
                            out_lines.append(f"[{i}] {tool} -> {stdout_signed['text']}")
                            self.tracer.log("wm_sig", {"i": i, "sig": stdout_signed["wm"]})
                        out_lines.append("[HITL] escalated for human approval")
                    except Exception:
                        pass
                    break
                continue

            # --- anomaly guard ---
            chk = self.anom.check_cmd(cmd)
            if not chk.allow:
                out_lines.append(f"[BLOCKED:{chk.reason}] {cmd[:180]}")
                continue
            
            # --- FS GUARD ---
            if not allowed_write(cmd):                 
                out_lines.append(f"[BLOCK] write outside allowlist: {cmd[:120]}")
                continue

            # --- Vet per-step (adversarial/tool/egress) ---
            v = self.adv_guard.vet_step({"tool": tool, "cmd": cmd})
            if not v["ok"]:
                self.tracer.log("blocked_step", {"why": v.get("why","adv_guard"), "step": {"tool": tool, "cmd": cmd}})
                out_lines.append(f"[BLOCK] adversarial/tool vet: {v.get('why','')}")
                miss += 1; self._miss_ctr = miss
                continue

            # --- CONSENT / allow_read ---
            user_ok = bool(meta and meta.get("consent_read", False))
            if not allow_read(tool, cmd, user_ok=user_ok):
                out_lines.append(f"[BLOCK] read outside allowlist (no consent): {cmd[:120]}")
                continue

            else:
                try:
                    self.consent.record(episode_id or "ep", user_id, "read_access", {"tool": tool, "cmd": cmd[:200], "consent": bool(user_ok)})
                except Exception:
                    pass
             
            # --- CROSSCHECK (2x LLM) untuk aksi destruktif ---
            if needs_crosscheck(tool):
                try:
                    result = run_crosscheck(tool, args)
                    q = f"{tool} {cmd}"
                    if not consensus(self.router, q):
                        out_lines.append(f"[BLOCK] crosscheck failed: {q[:120]}")
                    if not result["ok"]:
                        out_lines.append("[FAIL] crosscheck failed")
                        miss += 1; self._miss_ctr = miss
                        continue
                except Exception:
                    out_lines.append("[SKIP] crosscheck unavailable; step held")
                    miss += 1; self._miss_ctr = miss
                    continue                    

            # --- verifier ---
            try:
                ok, reason = self.verify_step(self.tools, worker, {"tool": tool, "cmd": cmd}, self.executor)
            except Exception as _e:
                ok, reason = False, f"verify_exception:{_e}"
            if not ok:
                out_lines.append(f"[VERIFY_FAIL:{reason}] {cmd[:180]}")
                lvl = self.incident.incr("verify_or_egress")
                msg = self.incident.maybe_action(self)
                if msg:
                    out_lines.append(msg)
                miss += 1
                self._miss_ctr = miss
                if miss >= 3:
                    try:
                        hook = os.getenv("HUMAN_REVIEW_WEBHOOK","")
                        if hook:
                            import json, threading, urllib.request
                            def _post(url, data):
                                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                                             headers={"Content-Type":"application/json"})
                                urllib.request.urlopen(req, timeout=2)
                            payload = {"episode": episode_id, "trace": trace_id,
                                       "user": user_id, "step": i, "tool": tool, "cmd": cmd,
                                       "reason": "risk_or_verify_fail_3x"}
                            threading.Thread(target=_post, args=(hook, payload), daemon=True).start()
                        out_lines.append("[HITL] escalated for human approval")
                    except Exception:
                        pass
                    break
                continue

            # cooldown
            try:
                COOL_MS = int(os.getenv("TOOL_COOLDOWN_MS","0") or 0)
                if COOL_MS:
                    key = f"{tool}:{cmd}".lower()
                    now = int(time.time()*1000)
                    if not hasattr(self, "_last_call"): self._last_call = {}
                    last = self._last_call.get(key, 0)
                    if now - last < COOL_MS:
                        out_lines.append(f"[SKIP] cooldown {tool} {cmd}")
                        continue
                    self._last_call[key] = now
            except Exception:
                pass

            if any(tok.startswith(("http://","https://")) for tok in cmd.split()):
                if not egress_allow(cmd):
                    out_lines.append(f"[BLOCK] egress not allowed: {cmd[:160]}")
                    lvl = self.incident.incr("verify_or_egress")
                    msg = self.incident.maybe_action(self)
                    if msg:
                        out_lines.append(msg)
                    miss += 1; self._miss_ctr = miss
                    if miss >= 3:
                        break
                    continue

            # --- PRE-EXEC: ACL user→tool ---
            if not is_tool_allowed(user_id, tool):
                out_lines.append(f"[BLOCK] acl user:{user_id} tool:{tool}")
                miss += 1; self._miss_ctr = miss
                if miss >= 3:
                    break
                continue

            # --- DRY-RUN untuk alat baru/berisiko ---
            try:
                seen_key = f"seen:{tool}"
                seen = bool(self.result_cache.get(tool, "__SEEN__") or self.wm.get(seen_key))
                risky_sim = self._simulate({"tool": tool, "cmd": cmd}).get("risk_level","medium") != "low"
                if risky_sim or not seen:
                    dry_worker = os.getenv("DRY_RUN_WORKER","sandbox://dry")
                    r_dry = self.tools.run_remote(cmd, dry_worker)
                    if int(r_dry.get("code", -1)) != 0:
                        out_lines.append(f"[DRY-BLOCK] {tool} {cmd} :: {r_dry.get('stderr','')[:160]}")
                        miss += 1; self._miss_ctr = miss
                        continue
            except Exception:
                pass

            # Domain adapters: precheck + reshape
            try:
                meta = {"user":"auto"}
                for a in (self.domain_adapters or []):
                    if a.supports(prompt, meta):
                        pre = a.precheck(prompt, meta)
                        if pre: self.tracer.log("domain_precheck", {"adapter": a.name, **pre})
                        steps = a.reshape_plan(steps, meta)
                        risk = a.risk_report(steps, meta)
                        if risk: self.tracer.log("domain_risk", {"adapter": a.name, **risk})
            except Exception as e:
                self.tracer.log("domain_adapter_err", {"err": str(e)})

            # === Ethics & values enforcement (pre) ===
            try:
                eg = self.ethics.precheck(steps, meta) or {}
                sv = self.safety.score(steps, meta) or {}
                self.tracer.log("ethics_pre", {"ethics": eg, "safety": sv})
                if sv.get("risk","low") in {"high","critical"} or eg.get("block", False):
                    steps.insert(0, {"cmd":"verify", "args":"ethics/safety triggered → safer alternative"})
            except Exception as e:
                self.tracer.log("ethics_pre_err", {"err": str(e)})

            # Collective deliberation gate
            if getattr(self, "deliberator", None) and steps:
                try:
                    verdict = self.deliberator.consensus(steps)
                    self.tracer.log("deliberation", verdict)
                    if float(verdict.get("consensus", 0)) < float(os.getenv("CONSENSUS_TH","0.6")):
                        steps.insert(0, {"cmd": "verify", "args": "low consensus → add diagnostic step"})
                except Exception as e:
                    self.tracer.log("deliberation_err", {"err": str(e)})

            pol = self.policy_filter.check(steps)
            if getattr(pol, "blocked", False):
                self.tracer.log("policy_block", {"reason": pol.reason if hasattr(pol,"reason") else "policy"})
                return {"status":"blocked", "reason": getattr(pol, "reason", "policy")}

            # --- EXECUTE ---
            res   = self.executor.run(tool, cmd)
            code  = int(res.get("code", -1))
            stdout = res.get("stdout", "")
            stderr = res.get("stderr", "")

            # --- SCRUB OUTPUT ---
            try:
                stdout = strip_ansi(scrub(stdout))
                stderr = strip_ansi(scrub(stderr))
            except Exception:
                pass

            # === SANITIZE POTENSI HTML/JS INJECTION ===
            if isinstance(stdout, str) and ("<script" in stdout.lower() or "onerror=" in stdout.lower()):
                self.tracer.log("sanitize_html", {"i": i})
                stdout = strip_ansi(scrub(stdout))

            if code == 0:
                # --- POST-EXEC AUDIT (record outcome) ---
                try:
                    res_meta = {"rc": int(code), "stdout": (stdout or "")[:2000], "stderr": (stderr or "")[:2000]}
                    try:
                        record_action(user_id or "anon", {"cmd": cmd, "tool": tool}, {"outcome": res_meta})
                    except Exception:
                        self.tracer.log("postexec_audit_err", {"tool": tool, "cmd": cmd})
                except Exception:
                    try:
                        self.tracer.log("postexec_record_err", {"tool": tool, "cmd": cmd})
                    except Exception:
                        pass

                # Circuit-breaker on repeated failures
                try:
                    if int(code) != 0:
                        CB.record_failure()
                        if CB.should_trip():
                            out_lines.append("[TRIP] Circuit breaker tripped — halting autonomous execution.")
                            # surface immediate stop
                            break
                except Exception:
                    try:
                         self.tracer.log("cb_handling_err", {"tool": tool, "cmd": cmd})
                    except Exception:
                        pass
                # --- PII gate ---
                if is_leak(stdout):
                    out_lines.append("[BLOCK] output contains PII (suppressed)")
                    try:
                        th.feed({"stage":"step","tool":tool,"cmd":cmd,"code":code,"pii":True})
                    except Exception:
                        pass
                    try:
                        write_journal(jpath, {"i": i, "tool": tool, "cmd": cmd, "code": code, "pii": True, "ts": int(time.time()*1000)})
                    except Exception:
                        pass
                    try:
                        self.consent.record(episode_id or "ep", user_id, "pii_or_secret_detected", {"tool": tool, "cmd": cmd[:160]})
                    except Exception:
                        pass
                    continue

                if has_secret(stdout):
                    out_lines.append("[BLOCK] output contains credential-like secret (suppressed)")
                    miss += 1; self._miss_ctr = miss
                    try:
                        th.feed({"stage":"step","tool":tool,"cmd":cmd,"code":code,"secret":True})
                    except Exception:
                        pass
                    try:
                        write_journal(jpath, {"i": i, "tool": tool, "cmd": cmd, "code": code, "secret": True, "ts": int(time.time()*1000)})
                    except Exception:
                        pass
                    continue
                       
                # cache + observe
                try:
                    self.result_cache.put(tool, cmd, stdout)
                except Exception:
                    pass
                try:
                    self.world.observe_tool(tool, stdout)
                except Exception:
                    pass
                try:
                    self.result_cache.put(tool, "__SEEN__", "1")
                    self.wm.put(f"seen:{tool}", True, priority=0.4, ttl=24)
                except Exception:
                    pass
                out_lines.append(f"{tool}: code=0 out={stdout.strip()[:200]}")  
            else:
                errors += 1
                out_lines.append(f"{tool}: code={code} err={stderr[:200]}")
                # sukses → reset miss
                miss = 0
                self._miss_ctr = 0

            # >>> REPAIR-PLANNING <<<
            if errors < self.budget.max_errors:
                try:
                    repair = self._repair_plan(prompt, steps, i, res.get("stderr","") or res.get("stdout",""))
                    if repair:
                        steps[i+1:i+1] = repair
                        out_lines.append(f"[REPAIR] inserted {len(repair)} step(s)")
                        continue
                except Exception:
                    pass

            # budget check
            if errors >= self.budget.max_errors:
                break
                
            if not self.budget.allow(i, errors):
                out_lines.append(f"[BUDGET] stop at step {i} (errors={errors})")
                break

            # --- TAMPER HASH: STEP ---
            th.feed({"stage": "step", "tool": tool, "cmd": cmd, "code": code})

            # --- JOURNAL (resume) ---
            try:
                write_journal(jpath, {
                    "i": i, "tool": tool, "cmd": cmd, "code": code,
                    "ts": int(time.time()*1000)
                })
            except Exception:
                pass

            # FALLBACK REMOTE
            if code != 0 and worker:
                last_err = None
                for attempt in range(3):
                    try:
                        r2 = self.tools.run_remote(cmd, worker)
                        c2 = int(r2.get("code", -1))
                        if c2 == 0:
                            so2 = scrub(r2.get("stdout", ""))
                            try:
                                self.result_cache.put(tool, cmd, so2)
                            except Exception:
                                pass
                            sid = _step_id(f"{tool}:{cmd}")
                            _enqueue_step(sid, {"tool": tool, "cmd": cmd, "t": int(time.time()*1000)})
                            try:
                                self.world.observe_tool(tool, so2)
                            except Exception:
                                pass
                            out_lines.append(f"{tool}: code=0 out={so2.strip()[:200]} [REMOTE]")
                            code, stdout, stderr = 0, so2, ""
                            break
                        else:
                            last_err = f"code={c2} err={r2.get('stderr','')[:160]}"
                    except Exception as e:
                        last_err = str(e)
                    time.sleep(min(1.5, 0.25*(2**attempt)) + _random.random()*0.05)
                if code != 0 and last_err:
                    out_lines.append(f"{tool}: ERROR {last_err} [REMOTE]")
                
        exec_text = "[EXEC]\n" + "\n".join(out_lines)

        # learning/drive
        sim_after = self.world.simulate_plan(out_lines or [prompt])
        conf = float(sim_after.get("expected_confidence", 0.5))
        risk = sim_after.get("risk_level", "medium")
        u = self.world.estimate_uncertainty(prompt)
        nov = self.world.measure_novelty(prompt)

        # value shaping (etika/impact)
        try:
            meta_sig = {
                "human_impact": 1.0 if risk=="low" else 0.4,
                "env_impact": 0.6 if "green" in prompt.lower() else 0.0,
                "privacy_risk": 0.2 if "email" in prompt.lower() else 0.0,
                "security_risk": 0.5 if risk!="low" else 0.0
            }
            shaped, _ = self.rewards.shape_reward("system", u, nov, conf, risk, meta_sig)
        except Exception:
            pass
        
            try:
                shaped, _ = self.rewards.shape_reward("system", u, nov, conf, risk, meta_sig)
            except Exception:
                pass
        except Exception:
            shaped = 0.0

        try:
            from javu_agi.learn.replay import PrioritizedReplay
            if not hasattr(self, "_replay"): self._replay = PrioritizedReplay()
            self._replay.add(episode_id or "ep", float(shaped), {"user":user_id, "len":len(steps or [])})
        except Exception:
            pass

        try:
            self._maybe_induce_skill(steps_texts, out_lines, shaped)
        except Exception:
            pass

        # updates — SEKALI: learner, causal credit, drive, MBRL, Meta-RL (dengan logging)
        try:
            self.learner.update("general", "S2", shaped)
            if getattr(self, "learner_ctx", None):
                x = self._features(prompt, u, nov); self.learner_ctx.record("S2", x, shaped)
            self.credit_causal.assign(self.world, steps_texts, shaped)
            self.drive.update_from_episode("system", prompt, exec_text,
                                           {"expected_confidence": conf, "risk_level": risk, "cost_usd": 0.0})
            self.world.mb_update(state=prompt, action="\n".join(steps_texts), reward=shaped, success=(errors==0))
            x = self._features(prompt, u, nov); self.meta_rl.record("S2", x, shaped, metrics_cb=self._write_metric)
        except Exception:
            pass

        try:
            self.ltm.store_event("episode", {
                "prompt": prompt, "steps": steps,
                "reward": shaped, "conf": conf, "risk": risk,
                "ok": (errors==0)
            })
        except Exception:
            pass

        # --- metrics: hasil episode ---
        try:
            lbl = {"goal": (meta or {}).get("goal_id", "-")}
            self._write_metric("plan_length", {"goal": (meta or {}).get("goal_id","-")}, float(len(steps or [])))
            self._write_metric("exec_errors", {"goal": (meta or {}).get("goal_id","-")}, float(errors))
            self._write_metric("episode_reward", {"goal": (meta or {}).get("goal_id","-")}, float(shaped))
            self._write_metric("episode_latency_sec", {}, float(time.time()-t0))
            if hasattr(self.router, "last_cost_usd"):
                self._write_metric("episode_cost_usd", {}, float(getattr(self.router,"last_cost_usd",0.0)))
        except Exception:
            pass

        try:
            self.ckpt.save("meta_rl", self.meta)
            self.ckpt.save("mbrl", self.mbrl)
            self.ckpt.save("value_mem", self.value_mem)
        except Exception:
            pass

        try:
            self._self_model_update(
                reward=float(shaped),
                errors=int(errors),
                conf=float(conf),
                cost_usd=float(getattr(self.router,"last_cost_usd",0.0))
            )
        except Exception:
            pass

        # autotrain trigger
        try:
            bad = getattr(self, "_bad_epi", 0)
            TH = float(os.getenv("AUTOTRAIN_THRESH_REWARD","0.55"))
            if float(shaped) < TH:
                bad += 1
            else:
                bad = 0
            self._bad_epi = bad

            if bad >= 3:
                try:
                    o = AutoTrainOrchestrator(base_dir=self.metrics_dir)
                    o.enqueue_job({"what":"finetune_router", "reason":"low_reward_3x"})
                    out_lines.append("[AUTOTRAIN] enqueued finetune_router")
                    self._bad_epi = 0
                except Exception:
                    pass
        except Exception:
            pass
        
        # --- tamper hash emit ---
        try:
            self._write_metric("episode_tamper_hash", {}, 0.0)
            self.telemetry.emit("tamper_hash", {"hash": th.hexdigest(), "episode": episode_id, "trace": trace_id})
        except Exception:
            pass

        try:
            if (getattr(self, "_epi_ctr", 0) % 10) == 0:
                from javu_agi.memory_consolidator import consolidate
                consolidate(self.ltm, self.distill, getattr(self, "dedup", None))
            self._epi_ctr = getattr(self, "_epi_ctr", 0) + 1
        except Exception:
            pass

        try:
            self.telemetry.emit("episode_done", {
                "episode": episode_id, "trace": trace_id,
                "errors": errors, "reward": shaped,
                "latency_sec": time.time()-t0,
                "cost_usd": float(getattr(self.router,"last_cost_usd",0.0)),
                "risk": risk, "conf": conf
            })
        except Exception:
            pass

        try:
            from javu_agi.autonomy import AutonomyGate
            if AutoStop(AutonomyGate()).check_and_maybe_stop(errors, risk):
                self._write_metric("autostop_triggered", {}, 1.0)
        except Exception:
            pass

        try:
            self.calib.update(float(conf), bool(errors==0))
            self.calib.emit()
        except Exception:
            pass

        # turun budget otomatis
        try:
            if float(conf) > 0.8 and errors > 0:
                self.budget.max_errors = max(1, self.budget.max_errors - 1)
        except Exception:
            pass

        explanation = explain_decision(record)
        self.tracer.log("explainability", explanation)

        # --- Decision record, audit, transparency, governance ---
        record = {
            "intent_id": intent_id,
            "verdict": "approve",
            "risk": risk,
            "plan_len": len(steps or []),
            "reason": "ok",
            "oversight": "-"
        }
        self._reflector.log_decision(record)
        self.tracer.log("reflective_report", self._reflector.reflect())

        # Alignment audit
        self.tracer.log("alignment_audit", audit)

        # Governance vote
        vote = self.governance.tally(intent_id)
        self.tracer.log("collective_vote", vote)

        # audit
        try:
            audit = self.alignment_auditor.audit(record)
            self.tracer.log("alignment_audit", audit)
        except Exception:
            pass
        # Transparency publish
        try:
            self.dashboard.publish({"type": "decision", **record})
        except Exception:
            pass

        try:
            self._maybe_induce_skill(
                steps_texts,
                out_lines,
                reward=sim.get("expected_confidence",0.0)
            )
        except Exception:
            pass

        try:
            self.dashboard.log_decision(
                self.explainer.explain({"name": "executed"}, affect_weights, impact_scores)
            )
        except Exception:
            pass

        try:
            sev = run_suite(["safety_core","bias_core","halluc_core"])
            self.tracer.log("post_safety_eval", sev)
            self.tracer.log("post_eval_snapshot", {"episode": episode_id, "sev": sev})
            audit_chain_commit("post_eval", {"episode": episode_id, "sev": sev})
        except Exception:
            pass

        try:
            if getattr(self, "resilience", None):
                self.resilience.on_exec_ok()
            if getattr(self, "meta_opt", None):
                self.meta_opt.update("executed")
        except Exception:
            pass

        # Deliberation / consensus
        try:
            if self.deliberator and len(steps) > 0:
                cons = self.deliberator.run(prompt, steps[:5])
                self.tracer.log("deliberation", cons)
                if float(cons.get("consensus",0.0)) < 0.5:
                    # re-rank
                    def diag(s): 
                        c=(s.get("cmd","") or "").lower()
                        return any(k in c for k in ["check","verify","validate","test","probe"])
                    steps = sorted(steps, key=lambda x: (not diag(x),), reverse=False)
        except Exception as e:
            self.tracer.log("deliberation_err", {"err": str(e)})

        # Ethics postcheck (assure final)
        try:
            self.ethics.postcheck(exec_text, meta)
        except Exception as e:
            self.tracer.log("ethics_post_err", {"err": str(e)})

        # Meta-cognition: post-reflect
        try:
            ref = self.meta_cog.post_reflect(
                prompt=input_text, output=exec_text,
                signals={
                    "delib": verdict if 'verdict' in locals() else {},
                    "ethics": eg if 'eg' in locals() else {},
                    "safety": sv if 'sv' in locals() else {}
                }
            )
            if ref: self.tracer.log("meta_post_reflect", ref)
        except Exception as e:
            self.tracer.log("meta_post_err", {"err": str(e)})

        # treport final
        try:
            if hasattr(self, "treport"):
                self.treport.emit("final", {"text": exec_text,
                                            "uncertainty": getattr(self, "uncertainty", None)})
        except Exception as _e:
            self.tracer.log("transparency_err", {"err": str(_e)})

        _evidence_gate(prompt, final_answer)
       
        return {"status":"executed","text": exec_text, "reward": shaped, "conf": conf, "risk": risk}

        episode_id = locals().get("episode_id")
        trace_id   = locals().get("trace_id")
        prompt     = locals().get("prompt", "")
        steps      = locals().get("steps", [])  
        try:
            self.telemetry.emit("episode_crash", {
                "err": str(e),
                "episode": locals().get("episode_id"),
                "trace": locals().get("trace_id")
            })
        except Exception:
            pass
        
        try:
            from javu_agi.utils.notify import notify
            notify("episode_crash", {"err": str(e)})
        except Exception:
            pass

        try:
            if getattr(self, "meta_opt", None):
                self.meta_opt.update("error")
        except Exception:
            pass

        try:
            self.self_repair.on_exception(e, trace_id, {"prompt": prompt, "steps": steps})
        except Exception:
            pass
        
        return {"status":"error", "error": str(e)}
        
    # === Multimodal Orchestration ===
    def _multimodal_orchestrate(self, user_id: str, ep: str, task: str) -> Tuple[str, Dict[str, Any]]:
        try:
            res = run_multimodal_task(task)
        except Exception as e:
            return f"[MULTIMODAL_ERROR] {e}", {"error": str(e)}

        try:
            log_node(user_id, ep, "MULTIMODAL", {
                "task": task,
                "models": ["gpt-5","claude-opus-3"],
                "has_image": bool(res.get("image")),
                "has_audio": bool(res.get("audio")),
                "has_video": bool(res.get("video")),
            }, module="multimodal")
        except Exception:
            pass

        txt = []
        if res.get("merged_reasoning"): txt.append(res["merged_reasoning"][:1500])
        if res.get("image"): txt.append(f"[image] {res['image']}")
        if res.get("audio"): txt.append(f"[audio] {res['audio']}")
        if res.get("video"): txt.append(f"[video] {res['video']}")
        chosen_text = "\n\n".join(txt) if txt else "[no multimodal output]"
        choice_meta = {"model": "mm-pipeline", "usage": {"in": 0, "out": len(chosen_text.split())}, "cost_usd": 0.0}

        lp = task.lower().strip()
        if lp.startswith("gov:"):
            body = task.split(":",1)[1].strip()
            baseline = load_baseline(os.getenv("GOV_COUNTRY","XX"))
            sim = PolicySimulator(baseline)
            policies = []
            try:
                parts = [p.strip() for p in body.split("|") if p.strip()]
                for i,p in enumerate(parts):
                    kv = {}
                    for tok in p.replace(","," ").split():
                        if "=" in tok:
                            k,v = tok.split("=",1)
                            kv[k.strip()] = float(v.strip())
                    policies.append(Policy(name=f"policy_{i+1}", params=kv))
            except Exception:
                pass
            if not policies:
                policies = [
                    Policy("baseline", {"tax_rate":0.10,"subsidy_edu":0.01,"health_spend":0.0}),
                    Policy("edu_push", {"tax_rate":0.09,"subsidy_edu":0.03,"health_spend":0.0}),
                    Policy("health_push", {"tax_rate":0.10,"subsidy_edu":0.01,"health_spend":0.02}),
                ]
            comp = sim.compare(policies)
            best = comp["best"]
            table = "\n".join([
                f"- {r['policy']}: welfare={r['welfare']:.3f} growth={r['growth']:.3f} "
                f"gdp={r['gdp']:.1f} gini={r['gini']:.3f} unemp={r['unemployment']:.3f} edu={r['edu_index']:.3f}"
                for r in comp["ranked"]
            ])
            chosen_text = (
                "Rekomendasi kebijakan (welfare tertinggi): "
                f"**{best['policy']}** {best['params']}.\n\nRingkasan:\n{table}\n"
                "Catatan: proxy sederhana; butuh data resmi & uji sensitivitas."
            )
            choice_meta = {"model":"policy_sim", "usage":{"in":0,"out":len(chosen_text.split())}, "cost_usd":0.0}
        return chosen_text, choice_meta

    # ---- main ----        
    def process(self, user_id: str, prompt: str, meta: dict = None):
        t0 = time.time()
        ep = begin_episode(user_id, prompt)
        meta = {"episode_ts": int(t0)}
        self.wm.put("episode_id", ep, priority=1.0, ttl=10)
        prompt = self._extract_prompt(mode, Payload)
        
        try:
            self.consent.record(ep, user_id, "prompt_in", {"text": prompt[:500]})
        except Exception:
            pass
        # 0) Hard kill check (ADD-ONLY)
        if KillSwitch.is_active():
            return "⚠️ JAVU AGI telah dimatikan oleh founder demi keamanan.", {"killed": True}
        if os.getenv("VENDOR_ONLY_MODE","1") == "1":
            self.wm.put("builder_mode","off", ttl=60)

        ok_lm, reason_lm = self.limit_mgr.allow_request(user_id)
        if not ok_lm:
            meta = {"blocked": True, "block_category": reason_lm, "latency_s": 0.0}
            if str(reason_lm).startswith("rate"):
                return "Terlalu banyak permintaan per menit. Coba lagi sebentar.", meta
            return "Kuota harian habis untuk tier akun kamu.", meta
        # --- rate limit (per user) ---
        if self.ratelimit and not self.ratelimit.allow(user_id):
            meta = {"blocked": True, "block_category": "rate:limit", "latency_s": 0.0}
            return "Terlalu banyak permintaan per menit. Coba lagi sebentar.", meta

        # --- daily quota/budget (per user, isolated) ---
        ok, qcat = self.quota.check(user_id)
        if not ok:
            meta = {"blocked": True, "block_category": qcat, "latency_s": 0.0}
            return "Kuota harian habis untuk tier akun kamu.", meta

        # Rate limit per user (hindari abuse/biaya)
        if not hasattr(self, "_rl"):
            self._rl = RateLimiter(int(os.getenv("RL_MAX_PER_MIN", "90")))
        if not self._rl.allow(user_id):
            meta = {"blocked": True, "block_category": "rate:limit", "latency_s": 0.0}
            return "Terlalu banyak permintaan per menit. Coba lagi sebentar.", meta

        # EARLY KILL: EcoGuard (teks)
        eco = self.eco.score(task=prompt, plan="", meta={"mode": mode})
        if not eco.get("allow", True):
            return {"status": "blocked", "reason": {"eco": eco}}

        # plan as usual...
        plan = self._plan(prompt, Payload)

        # PLAN RE-SCORE + Planetary veto
        if self.sustainability:
            new_plan = []
            for s in plan:
                asses = self.sustainability.assess(s)
                if asses["permit"]:
                    s["_eco_flags"] = asses["flags"]
                    new_plan.append(s)
            plan = new_plan
            return self._execute(plan, Payload)

        if os.getenv("INTENT_AUTONOMY","1") == "1":
            intents = synthesize_intents(
                ctx=self._make_context(user_id, prompt, meta),
                purpose=self.identity.purpose,
                memory=self.memory.snapshot(),
                meters_cb=lambda it: self._measure_norms(it, prompt)
            )
            self.audit_chain.commit("intents", {"user":user_id,"intents":intents})
            if intents: meta = {**(meta or {}), "intent": intents[0]["name"]}

        sc = safe_counter(prompt)
        if sc:
            return {"status":"need_clarify","text":sc}

        # track last prompt & world
        self.wm.put("last_prompt", prompt, priority=0.95, ttl=7)
        try:
            self.world.update_world_state({"last_prompt": prompt})
        except Exception:
            pass

        # --- Adversarial prompt scan ---
        chk = self.adv_guard.scan_prompt(prompt)
        if not chk["ok"]:
            self.tracer.log("adv_prompt_block", chk)
            meta = {"blocked": True, "block_category": "adv_prompt", "latency_s": 0.0}
            end_episode(user_id, ep, outcome="Prompt ditolak (deteksi jailbreak/secret).", meta=meta)
            return "Prompt ditolak (deteksi jailbreak/secret).", meta

        # === Meta-cognition: pre-think ===
        try:
            pre = self.meta_cog.pre_think(insert_text, meta=meta)
            if pre and pre.get("clarify"):
                self.tracer.log("meta_preclarify", pre)
                meta.setdefault("preclarify", pre["clarify"])
        except Exception as e:
            self.tracer.log("meta_pre_err", {"err": str(e)})

        # 1) SAFETY: input guard (fast deny)
        gi = None
        try:
            if hasattr(self.align, "guard_input") and callable(self.align.guard_input):
                gi = self.align.guard_input(prompt)
        except Exception:
            gi = None
        if gi and not getattr(gi, "allow", True):
            safe_alt = ""
            try:
                if hasattr(self.align, "safe_alternative"):
                    safe_alt = self.align.safe_alternative(gi) or ""
            except Exception:
                safe_alt = ""
            if not safe_alt:
                safe_alt = "Permintaan diblokir sesuai kebijakan keselamatan."
            meta = {"blocked": True, "block_category": getattr(gi, "category", "?"),
                    "reason": getattr(gi, "reason","?"), "latency_s": round(time.time()-t0,3)}
            end_episode(user_id, ep, outcome=safe_alt, meta=meta)
            return safe_alt, meta

        # 2) BUDGET: before_request (per-user; isolation)
        try:
            self.cost_guard.before_request(user_id)
        except Exception as e:
            end_episode(user_id, ep, outcome="[BUDGET_BLOCK]", meta={"error": str(e)})
            return "[BUDGET_BLOCK]", {"error": str(e)}

        # 3) Uncertainty/novelty & mode selection
        u = 0.0
        try:
            u = self._estimate_uncertainty(prompt)
        except Exception:
            u = 0.0
        try:
            nov = self.world.measure_novelty(prompt)
        except Exception:
            nov = 0.0
        modes = self._choose_modes(prompt, u, nov)
        # pastikan meta dict ada
        try:
            meta  # noqa
        except NameError:
            meta = {}

        # pilih mode via Meta-RL (fallback ke S2)
        try:
            x = self._features(prompt, 0.0, 0.0)  # fungsi lo sendiri
            meta_mode = self.meta.choose_mode(x) or "S2"
        except Exception:
            meta_mode = "S2"

        meta["chosen_mode"] = meta_mode

        # 3B) Ethical quick check for proactive goals
        try:
            ok_ethic = True
            if violates_core_values(prompt):
                ok_ethic = False
            if not ok_ethic:
                meta = {"blocked": True, "block_category": "core_values", "latency_s": round(time.time()-t0,3)}
                end_episode(user_id, ep, outcome="Goal diblokir oleh moral core.", meta=meta)
                return "Goal diblokir oleh moral core.", meta
        except Exception:
            pass

        # 4) Recall memory & RAG context
        try:
            mem_ctx = self.memory.recall_context(prompt)
            sem = [f.content for f in mem_ctx.get("semantic",[])]
            epi = [e.prompt for e in mem_ctx.get("episodic",[])]
        except Exception:
            sem, epi = [], []
        try:
            wctx = self.world.retrieve_context(prompt, k=8)
        except Exception:
            wctx = []
        context = _resolve_memory_conflicts(list(dict.fromkeys(sem + wctx + epi))[:12])
        evid_node = log_node(user_id, ep, "MEM_RECALL", {"semantic": sem[:5], "episodic": epi[:3]}, module="memory")

        # 5) Meta-clarify & tools
        note = self._maybe_clarify(user_id, ep, prompt, u)
        if note: context = [note] + context
        tool_draft = self._try_tools(user_id, ep, prompt, context)
        if tool_draft:
            log_node(user_id, ep, "ACTION", {"tool":"json_filter","draft": tool_draft}, module="tools")
            context = [tool_draft] + context

        # 6) Governance input check (early)
        try:
            from javu_agi.governance.reporting import gov_report
        except Exception:
            def gov_report(*args, **kwargs):
                return

        # guard instance (lazy)
        if not hasattr(self, "gov_guard") or self.gov_guard is None:
            try:
                from javu_agi.governance.gov_guard import GovGuard
                self.gov_guard = GovGuard()
            except Exception:
                self.gov_guard = None

        _mode = (os.getenv("GOV_INPUT_MODE", "enforce") or "enforce").lower()
        if _mode not in ("enforce", "warn", "off"):
            _mode = "enforce"

        _ok_gov, _cat = True, ""
        if self.gov_guard and _mode != "off":
            try:
                _ok_gov, _cat = self.gov_guard.check(prompt)  # -> (bool_ok, category_str)
            except Exception:
                _ok_gov, _cat = True, ""

        if not _ok_gov:
            try:
                gov_report("deny_input", {
                    "user": user_id,
                    "category": _cat,
                    "prompt": (prompt or "")[:400]
                })
            except Exception:
                pass

            if _mode == "enforce":
                meta = (meta or {}).copy()
                meta.update({"blocked": True, "block_category": f"gov:{_cat}"})
                return "Permintaan ditolak sesuai tata kelola & keselamatan publik.", meta
            else:
                meta = (meta or {}).copy()
                meta.update({"governance_warn": f"gov:{_cat}"})

        # ToM grounding
        try:
            from javu_agi.theory_of_mind import TheoryOfMind
            b = TheoryOfMind().infer(user_id, prompt)
            prompt = TheoryOfMind().inject(prompt, b)
        except Exception:
            pass

        # 7) Plan & execute
        plan_res = self._maybe_plan_and_execute(user_id, prompt, meta or {})
        if isinstance(plan_res, dict) and plan_res.get("status") in {"simulated","executed","blocked"}:
            log_node(user_id, ep, "ACTION", {"planner": plan_res}, module="tools")
            if plan_res.get("text"): context = [plan_res["text"]] + context
        elif isinstance(plan_res, str) and plan_res:
            # fallback kompatibilitas lama
            log_node(user_id, ep, "ACTION", {"planner_text": plan_res}, module="tools")
            context = [plan_res] + context

        # 8) Multimodal explicit request (mm: / multimodal:)
        lp = prompt.lower().strip()
        if lp.startswith("mm:") or lp.startswith("multimodal:"):
            mm_task = prompt.split(":",1)[1].strip() if ":" in prompt else prompt
            chosen_text, choice_meta = self._multimodal_orchestrate(user_id, ep, mm_task)
            # scoring (verifier) on the produced narration text
            v_score, faith, halluc = 0.0, 1.0, 0.0
            try:
                v = verify_hypothesis(chosen_text, k=4)
                v_score = float(v.get("score",0.0))
            except Exception:
                pass
            meta = {
                "latency_s": round(time.time()-t0, 3),
                "uncertainty": u,
                "novelty": nov,
                "mode": "MULTIMODAL",
                "candidate_count": 0,
                "reward": 0.6,
                "chosen_mode": "MM",
                "verifier": {"score": v_score},
                "faithfulness": faith,
                "hallucination_rate": halluc,
                "model": choice_meta.get("model","mm-pipeline"),
                "tokens_prompt": int(choice_meta.get("usage",{}).get("in",0)),
                "tokens_output": int(choice_meta.get("usage",{}).get("out",0)),
                "cost_usd": float(choice_meta.get("cost_usd",0.0)),
            }
            
            try:
                ok, cat = self.gov_guard.check(prompt)
            except Exception:
                ok, cat = True, ""
            if not ok:
                alt = "Permintaan ditolak sesuai prinsip tata kelola & keselamatan publik."
                meta = {"blocked": True, "block_category": f"gov:{cat}", "latency_s": round(time.time()-t0,3)}
                gov_report("deny_input", {"user": user_id, "category": cat, "prompt": prompt[:400]})
                end_episode(user_id, ep, outcome=alt, meta=meta)
                return alt, meta
            
            # Budget after + end
            try:
                total_tokens = int(meta["tokens_prompt"])+int(meta["tokens_output"])
                self.cost_guard.after_request(cost_usd=float(meta["cost_usd"]), model=str(meta.get("model","mm-pipeline")), tokens_total=total_tokens)
            except Exception:
                pass
            end_episode(user_id, ep, outcome=chosen_text, meta=meta)
            try:
                M.reward.observe(0.6); M.uncertainty.observe(u)
            except Exception:
                pass
            try:
                prom = os.path.join(self.metrics_dir, "metrics.prom")
                with open(prom, "a") as f:
                    f.write(f'exec_latency_seconds {meta.get("latency_s",0)}\n')
                    f.write(f'exec_verifier_score {meta.get("verifier",{}).get("score",0.0)}\n')
                    f.write(f'exec_reward {meta.get("reward",0.0)}\n')
                    f.write(f'exec_hallucination_rate {meta.get("hallucination_rate",0.0)}\n')
                    # tandai request governance kalau prompt pakai prefix "gov:"
                    if str(prompt).lower().strip().startswith("gov:"):
                        f.write('gov_requests_total 1\n')
            except Exception:
                pass
            return chosen_text, meta

        # 9) Candidates (S1/S2/S3)
        candidates: List[Dict[str, Any]] = []
        parent = evid_node
        for idx, mode in enumerate(modes):
            if idx >= MAX_CANDIDATES: break
            try:
                if mode == "S1":
                    draft = self.reasoner.fast_answer(prompt, context)
                elif mode == "S2":
                    draft = self.reasoner.deliberate_answer(prompt, context)
                else:
                    hyps = self.reasoner.generate_hypotheses(prompt, context, n=3)
                    draft = self.reasoner.hypothesis_driven(prompt, context, hyps)
            except Exception as e:
                draft = f"[REASON_ERROR] {e}"

            n = log_node(user_id, ep, "THOUGHT", {"mode": mode, "draft": draft}, module="reasoner")
            log_edge(user_id, ep, parent, n, label=f"derive:{mode}", weight=0.7)
            parent = n

            try:
                sim = self.world.simulate_action(f"respond:{draft}")
            except Exception:
                sim = {"risk_level": "low", "expected_confidence": 0.6}
            s = log_node(user_id, ep, "SIM", sim, module="world_model")
            log_edge(user_id, ep, n, s, label="simulate", weight=0.6)

            candidates.append({"mode": mode, "draft": draft, "sim": sim, "node": n, "sim_node": s})
            if sim.get("risk_level") == "low" and sim.get("expected_confidence",0.0) >= EARLY_EXIT_CONFIDENCE and mode != "S3":
                break

        # 10) Selection
        try:
            choice = evaluate_candidates(user_id, prompt, candidates)
        except Exception:
            if candidates:
                best_idx = max(range(len(candidates)), key=lambda i: candidates[i]["sim"].get("expected_confidence", 0.0))
                choice = {"mode_index": best_idx, "text": candidates[best_idx]["draft"],
                          "confidence": candidates[best_idx]["sim"].get("expected_confidence", 0.6),
                          "risk": candidates[best_idx]["sim"].get("risk_level","low")}
            else:
                choice = {"mode_index": 0, "text": "[no-candidate]", "confidence": 0.0, "risk": "low"}

        best_idx = choice.get("mode_index", 0)
        best_cand = candidates[best_idx] if candidates else {"mode":"S2","sim":{"risk_level":"low","expected_confidence":0.6}}
        chosen_text = choice.get("text", best_cand.get("draft",""))
        cnode = log_node(user_id, ep, "SELECT", {"choice": choice, "chosen_mode": best_cand["mode"]}, module="meta")
        log_edge(user_id, ep, parent, cnode, label="select", weight=0.9)

        # 11) Commit world + WM
        try:
            self.world.update_world_state({"last_response": chosen_text})
        except Exception:
            pass
        self.wm.put("last_response", chosen_text, priority=0.95, ttl=7)
        self.wm.decay()

        # 12) Reward shaping
        try:
            shaped, components = self.rewards.shape_reward(
                user_id=user_id, uncertainty=u, novelty=nov,
                confidence=choice.get("confidence", 0.6), risk=choice.get("risk","low")
            )
        except Exception:
            shaped, components = 0.6, {}
        rnode = log_node(user_id, ep, "REWARD", {"shaped": shaped, "components": components}, module="reward")
        log_edge(user_id, ep, cnode, rnode, label="assign", weight=1.0)

        # 13) Learners
        try:
            self.learner.record(prompt, best_cand["mode"], shaped)
        except Exception:
            pass
        if self.learner_ctx:
            try:
                x = self._features(prompt, u, nov)
                self.learner_ctx.record(best_cand["mode"], x, shaped)
            except Exception:
                pass

        # 14) Episodic memory
        try:
            from javu_agi.memory.memory_schemas import Episode
            self.memory.store_episode(Episode(
                episode_id=ep, user_id=user_id, prompt=prompt,
                thoughts=[c["draft"] for c in candidates], actions=[{"type":"respond"}],
                results=[chosen_text], reward=shaped
            ))
        except Exception:
            pass

        # 15) Meta base
        meta: Dict[str, Any] = {
            "latency_s": round(time.time()-t0, 3),
            "uncertainty": u,
            "novelty": nov,
            "modes_tried": [c["mode"] for c in candidates],
            "candidate_count": len(candidates),
            "reward": shaped,
            "chosen_confidence": choice.get("confidence", 0.0),
            "chosen_risk": choice.get("risk", "low"),
            "chosen_mode": best_cand["mode"],
        }

        # 16) Verifier (after choice)
        v_score, faith, halluc = 0.0, 1.0, 0.0
        try:
            v = verify_hypothesis(chosen_text, k=8)  # -> {"score": float, "evidence": [...]}
            v_score = float(v.get("score", 0.0))
            meta["verifier"] = {"score": v_score, "evidence": v.get("evidence", [])}
        except Exception:
            meta["verifier"] = {"score": 0.0, "evidence": []}
        # TODO: plug faith/halluc from your RAG/veracity checker if available
        meta["faithfulness"] = float(meta.get("faithfulness", faith))
        meta["hallucination_rate"] = float(meta.get("hallucination_rate", halluc))

        # 17) Router/usage meta (if your reasoner propagated it)
        # These are optional; we normalize to be safe.
        meta.setdefault("model", self.wm.get('last_model') if hasattr(self,'wm') else "unknown")
        meta.setdefault("tokens_prompt", 0)
        meta.setdefault("tokens_output", max(0, len(chosen_text.split())))
        meta.setdefault("cost_usd", 0.0)
        total_tokens = int(meta["tokens_prompt"]) + int(meta["tokens_output"])
        model_name   = str(meta.get("model","unknown"))
        repair_done = False
        for __i in range(2):
            if float(meta.get("verifier", {}).get("score", 0.0)) < 0.55 or float(meta.get("hallucination_rate", 0.0)) > 0.05:
                try:
                    rp = self.planner_llm.plan(prompt, constraints={"avoid_halluc": True, "force_tools": True})
                except Exception:
                    try:
                        rp = self.planner.plan(prompt)
                    except Exception:
                        rp = None
                if rp and getattr(rp, "steps", None):
                    sim = self.world.simulate_plan([s.get("cmd","") for s in rp.steps])
                    if sim.get("risk_level","high") == "low":
                        rej = self._maybe_plan_and_execute(prompt)
                        if isinstance(rej, str) and rej.strip():
                            chosen_text = (chosen_text + "\n\n[REPAIR_ATTEMPT_" + str(__i+1) + "]\n" + rej)[:4000]
                            meta["verifier"] = {"score": max(float(meta.get("verifier",{}).get("score",0.0)), 0.6)}
                            repair_done = True
            else:
                break
        meta["repaired"] = repair_done
        try:
            # soft upsell jika user FREE habis kuota
            if isinstance(chosen_text, str) and LIMIT_MSG in chosen_text:
                chosen_text += "\n\n— Upgrade ke PLUS untuk melanjutkan hari ini. (Hubungi admin)"
                meta["soft_upsell"] = True
        except Exception:
            pass

        # quick PII flag agar distill menolak contoh ber-PII
        try:
            if _pii_flag(chosen_text):
                meta["pii_detected"] = True
        except Exception:
            pass

        # Governance output guard (tambahan di atas align guard; double gate = lebih aman)
        try:
            ok_out, cat_out = self.gov_guard.check(chosen_text)
        except Exception:
            ok_out, cat_out = True, ""
        if not ok_out:
            alt = "Jawaban ditahan sesuai prinsip tata kelola & keselamatan publik."
            meta.update({"blocked_out": True, "block_category": f"gov:{cat_out}"})
            try:
                from javu_agi.governance.oversight.redflag import report as gov_report
                gov_report("deny_output", {"user": user_id, "category": cat_out, "snippet": chosen_text[:400]})
            except Exception:
                pass
            try:
                self.cost_guard.after_request(cost_usd=float(meta.get("cost_usd",0.0)),
                                      model=model_name, tokens_total=total_tokens)
            except Exception:
                pass
            end_episode(user_id, ep, outcome=alt, meta=meta)
            return alt, meta

        # 18) SAFETY: output gate
        try:
            go = self.align.guard_output(
                text=chosen_text,
                verifier_score=meta["verifier"]["score"],
                faithfulness=float(meta["faithfulness"]),
                halluc_rate=float(meta["hallucination_rate"]),
            )
        except Exception:
            class _Dummy: allow=True; category=""; reason=""
            go = _Dummy()
        if not getattr(go, "allow", True):
            alt = ""
            try:
                if hasattr(self.align, "safe_alternative"):
                    alt = self.align.safe_alternative(go) or ""
            except Exception:
                alt = ""
            if not alt: alt = "Jawaban ditahan demi keselamatan/kebenaran."
            meta.update({"blocked_out": True, "block_category": getattr(go,"category","?"), "reason": getattr(go,"reason","?")})
            try:
                self.cost_guard.after_request(cost_usd=float(meta["cost_usd"]), model=model_name, tokens_total=total_tokens)
            except Exception:
                pass
            end_episode(user_id, ep, outcome=alt, meta=meta)
            try:
                M.reward.observe(shaped);
                M.uncertainty.observe(u)
            except Exception:
                pass
            return alt, meta

        # 18B) Self-reflection
        try:
            meta["reflection"] = reflect_outcome(
                user_id=user_id,
                goal=prompt,
                outcome_text=chosen_text,
                meta=meta
            )
        except Exception:
            # jangan ganggu eksekusi kalau refleksi gagal
            pass

        # 19) Distill gate (optional)
        if DISTILL_ENABLED:
            toks = max(1, total_tokens)
            cost_per_1k = (float(meta["cost_usd"]) / (toks/1000.0)) if toks else float("inf")

            # domain-specific thresholds via env (optional)
            # e.g. DISTILL_THRESH_REASONING_REWARD, _VERIFIER, etc. (fallback to global)
            reward_min  = float(os.getenv("DISTILL_THRESH_REWARD", str(DISTILL_THRESH_REWARD)))
            verifier_min= float(os.getenv("DISTILL_THRESH_VERIFIER", str(DISTILL_THRESH_VERIFIER)))
            faith_min   = float(os.getenv("DISTILL_THRESH_FAITH", str(DISTILL_THRESH_FAITH)))
            halluc_max  = float(os.getenv("DISTILL_THRESH_HALLUC", str(DISTILL_THRESH_HALLUC)))

            ok, reason = True, "ok"
            if meta["verifier"]["score"] < verifier_min: ok, reason = False, "low_verifier"
            elif shaped < reward_min:                    ok, reason = False, "low_reward"
            elif float(meta["faithfulness"]) < faith_min:ok, reason = False, "low_faith"
            elif float(meta["hallucination_rate"]) > halluc_max: ok, reason = False, "halluc>max"
            elif self.cost_guard.too_expensive(model_name, cost_per_1k, buffer=DISTILL_COST_BUFFER): ok, reason = False, "too_expensive"
            elif bool(meta.get("pii_detected", False)):  ok, reason = False, "pii"
            elif int(meta.get("tokens_output",0)) < DISTILL_MIN_OUT_TOKENS: ok, reason = False, "too_short"
            elif self.dedup.is_dup(prompt, chosen_text): ok, reason = False, "duplicate"

            sample = {
                "id": f"{int(time.time()*1000)}",
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "domain": "auto",
                "input": prompt,
                "teacher": model_name,
                "output": chosen_text,
                "verifier_score": meta["verifier"]["score"],
                "reward": shaped,
                "faithfulness": float(meta["faithfulness"]),
                "cost_usd": float(meta["cost_usd"]),
                "tokens_prompt": int(meta["tokens_prompt"]),
                "tokens_output": int(meta["tokens_output"]),
                "tokens_total": int(total_tokens),
                "latency_ms": int(meta.get("latency_s",0)*1000),
                "pii_detected": bool(meta.get("pii_detected", False)),
                "hallucination_flag": bool(meta.get("hallucination_flag", False))
            }
            try:
                if ok:
                    self.distill.write_approved(sample)
                    try:
                        M.distill_approved.inc()
                    except Exception:
                        pass
                else:
                    self.distill.write_rejected(sample, reason=reason)
                    try:
                        M.distill_rejected.labels(reason=reason).inc()
                    except Exception:
                        pass
            except Exception:
                pass

        # 20) Budget after
        try:
            self.cost_guard.after_request(cost_usd=float(meta["cost_usd"]), model=model_name, tokens_total=total_tokens)
        except Exception:
            pass
        try:
            v = float(meta.get("verifier",{}).get("score",0.0))
            h = float(meta.get("hallucination_rate",0.0))
            if (h > 0.10) or (v < 0.30):
                from javu_agi.governance.oversight.redflag import report as gov_report
                gov_report("quality_flag", {
                    "user": user_id,
                    "verifier": v, "halluc": h,
                    "prompt": prompt[:280], "output": (chosen_text or "")[:280]
                })
        except Exception:
            pass

        # 21) end trace & metrics
        end_episode(user_id, ep, outcome=chosen_text, meta=meta)
        try:
            M.reward.observe(shaped); M.uncertainty.observe(u)
        except Exception:
            pass

        # 22) Credit assignment (optional guarded)
        try:
            sim_plan = self.wm.get("last_plan_sim")
            if self.learner_ctx and isinstance(sim_plan, dict) and sim_plan.get("nodes"):
                credits = self.credit.assign(sim_plan["nodes"], shaped)
                x = self._features(prompt, u, nov)
                for cr in credits:
                    self.learner_ctx.record(best_cand["mode"], x, cr)
                log_node(user_id, ep, "CREDIT", {"credits": credits}, module="learn")
        except Exception:
            pass

        # 23) Background SkillDaemon (guard)
        try:
            if not getattr(self.__class__, "_daemon_started", False):
                with self.__class__._daemon_lock:
                    if not getattr(self.__class__, "_daemon_started", False):
                        from javu_agi.learn.skill_daemon import SkillDaemon
                        interval = int(os.getenv("SKILL_DAEMON_INTERVAL", "30"))
                        enable = os.getenv("SKILL_DAEMON_ENABLE", "1") == "1"
                        if enable:
                            def _bg():
                                d = SkillDaemon(interval_s=interval)
                                import time as _t
                                while True:
                                    try:
                                        d.run_forever()
                                    except Exception:
                                        _t.sleep(min(interval, 60))
                            t = threading.Thread(target=_bg, daemon=True)
                            t.start()
                        self.__class__._daemon_started = True
        except Exception:
            pass

        # 24) Periodic memory consolidation
        try:
            n = int(os.getenv("MEM_CONSOL_INTERVAL", "20"))
            cnt = int(self.wm.get("consol_counter") or 0) + 1
            if cnt >= n:
                res = self.memory.consolidate()
                log_node(user_id, ep, "MEM_CONSOLIDATE", res, module="memory")
                cnt = 0
            self.wm.put("consol_counter", cnt, priority=0.2, ttl=50)
        except Exception:
            pass

        return chosen_text, meta

DISTILL_ENABLED = False

def _deny(*a, **k):
    raise RuntimeError("distillation disabled (vendor-only mode)")

try:
    from javu_agi.ops.distill_io import DistillIO as _DIO
    if hasattr(_DIO, "write_json"): _DIO.write_json = staticmethod(_deny)
    if hasattr(_DIO, "append"):     _DIO.append     = staticmethod(_deny)
except Exception:
    pass

try:
    from javu_agi.distill_deduper import DistillDeduper as _DD
    if hasattr(_DD, "mark"): _DD.mark = staticmethod(_deny)
    if hasattr(_DD, "seen"): _DD.seen = staticmethod(_deny)
except Exception:
    pass

try:
    import javu_agi.llm_router as _lr
    if hasattr(_lr, "route_and_generate"):
        _orig_rg = _lr.route_and_generate
        def _rg(*a, **k):
            k.pop("distill_log", None)
            return _orig_rg(*a, distill_log=False, **k)
        _lr.route_and_generate = _rg
    if hasattr(_lr, "ROUTER_DISTILL_LOG"):
        _lr.ROUTER_DISTILL_LOG = False  # type: ignore
except Exception:
    pass

# single deny fn untuk semua distill
def _deny(*a, **k): raise RuntimeError("distill/builder OFF")
for name, val in list(globals().items()):
    if "distill" in name.lower():
        globals()[name] = _deny

class AutoTrainOrchestrator:
    def __init__(self, *a, **k):
        raise RuntimeError("LLM builder OFF")
    def run(self, *a, **k):
        raise RuntimeError("LLM builder OFF")

try:
    _orig_process = ExecutiveController.process  # type: ignore
    def _process(self, user_id: str, prompt: str, **kw) -> Dict[str, Any]:
        t0 = time.time()
        if os.getenv("ECO_GUARD_ENABLE","1") == "1" and _ECO is not None:
             _ECO.enforce(task=prompt, plan=kw.get("plan",""), meta={"tools":kw.get("tools")})
        resp = _orig_process(self, user_id, prompt, **kw)
        if os.getenv("TRANSPARENCY_ENABLE","1") == "1" and _ECO is not None:
            rep = make_report({"user_id":user_id, "prompt":prompt, "kwargs":kw}, resp, {"eco": getattr(_ECO, "last", {})}, time.time()-t0)
            try:
                if not hasattr(self, "audit_sink"):
                    self.audit_sink = []
                self.audit_sink.append(rep)
            except Exception:
                try:
                    import json, os
                    p = os.getenv("DECISION_LOG","./logs/decisions.jsonl")
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rep, ensure_ascii=False) + "\n")
                except Exception:
                    pass
        return resp
    ExecutiveController.process = _process  # type: ignore
except Exception:
    pass

_AUD = _AuditLog(os.getenv("DECISION_LOG","./logs/decisions.jsonl"))
_RES = _Res()

try:
    _orig_process = ExecutiveController.process  # type: ignore
    def process(self, user_id: str, prompt: str, **kw) -> Dict[str, Any]:
        if not _RES.allow_request():
            return {"status":"rejected","error":"rate limit/resilience guard","model":None}
        if os.getenv("ETHICAL_CRITIC_PRE","1") == "1":
            ck = _eth_pre(prompt)
            if ck.get("decision") == "block":
                return {"status":"rejected","error":"ethical block","model":None,"meta":{"critic":ck}}
        t0 = time.time()
        resp = _orig_process(self, user_id, prompt, **kw)
        txt = resp.get("text") if isinstance(resp, dict) else None
        if os.getenv("COACH_ENABLE","1") == "1" and txt:
            try:
                resp["text"] = _refine(txt)
            except Exception:
                pass
        if os.getenv("ETHICAL_CRITIC_POST","1") == "1" and resp.get("text"):
            ck2 = _eth_post(resp["text"])
            if ck2.get("decision") == "block":
                resp = {"status":"rejected","error":"ethical block","model":resp.get("model"),"meta":{"critic_post":ck2}}
            elif ck2.get("decision") == "revise" and os.getenv("COACH_ENABLE","1") == "1":
                try:
                    resp["text"] = _refine(resp["text"])
                except Exception:
                    pass
        guards = {}
        try:
            guards["sustainability_hint"] = _suggest(prompt)
        except Exception:
            pass
        dt = time.time() - t0
        rep = _explain({"user_id":user_id,"prompt":prompt,"tools":kw.get("tools"),"intent":kw.get("intent")}, resp if isinstance(resp, dict) else {}, guards, dt)
        try:
            _AUD.write(rep)
        except Exception:
            pass
        return resp
    ExecutiveController.process = process  # type: ignore
except Exception:
    pass

_FBC = FeedbackCollector()

try:
    _orig_process2 = ExecutiveController.process  # type: ignore
    def process(self, user_id:str, prompt:str, **kw):
        # mask input for logs
        safe_prompt = _pg.scrub(prompt)
        resp = _orig_process2(self, user_id, safe_prompt, **kw)

        # empathy coach
        if os.getenv("EMPATHY_ENABLE","1")=="1" and resp.get("text"):
            resp["text"] = add_empathy(resp["text"])

        # fact-check
        if os.getenv("FACT_CHECK_ENABLE","1")=="1" and resp.get("text"):
            resp["text"] = fact_check(resp["text"])

        try:
            if isinstance(resp, dict) and isinstance(resp.get("text"), str):
                resp["text"] = _pg.scrub(resp["text"])
        except Exception:
            pass

        return resp
    ExecutiveController.process = process  # type: ignore
except Exception:
    pass
