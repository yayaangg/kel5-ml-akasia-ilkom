"""
============================================================
AKASIA - Run Real RAGAS Evaluation on 30 Questions
============================================================
Menjalankan metrik RAGAS asli berbasis LLM pada 30 pertanyaan
representatif dari evaluation_results.tsv.

Usage:
    python evaluation/run_ragas_real_30.py --ids 1,4,7,10,12,16,19,23,26,29,31,35,38,42,46,49,55,57,59,62,66,68,72,74,75,80,82,89,95,98 --resume
"""

import sys
import os

# Disable RAGAS telemetry to prevent hanging on socket checks
os.environ["RAGAS_DO_NOT_TRACK"] = "true"

import csv
import json
import time
import argparse
import shutil
import re
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(EVAL_DIR, "evaluation_results.tsv")
RAGAS_FILE = os.path.join(EVAL_DIR, "ragas_scores_real_30.tsv")
SUMMARY_FILE = os.path.join(EVAL_DIR, "summary_ragas_real_30.tsv")

RAGAS_COLUMNS = [
    "id", "category", "question", "faithfulness", "response_relevancy",
    "context_precision", "context_recall", "latency_seconds", "status", "notes"
]


def load_results(filepath):
    """Load evaluation results from TSV."""
    rows = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def classify_status(row):
    """Classify row status as Complete, Partial, or Failed."""
    # Check main metrics
    main_metrics = ["faithfulness", "response_relevancy", "context_precision", "context_recall", "latency_seconds"]
    is_complete = True
    for m in main_metrics:
        v = str(row.get(m, "")).strip()
        if v == "":
            is_complete = False
            break
            
    if is_complete:
        return "Complete"
        
    if row.get("status") == "Failed":
        return "Failed"
        
    return "Partial"


def load_existing_scores(filepath):
    """Load existing scores for resume mode."""
    if not os.path.exists(filepath):
        return {}
    scores = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            # Re-classify status based on metrics
            row["status"] = classify_status(row)
            scores[row["id"]] = row
    return scores


def save_scores(filepath, scores_list):
    """Save scores to TSV file."""
    # Re-classify status for all scores before saving
    for row in scores_list:
        row["status"] = classify_status(row)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RAGAS_COLUMNS, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        for row in scores_list:
            writer.writerow(row)


def _safe_float(val):
    """Safely convert value to float, return empty string if NaN or None."""
    if val is None:
        return ""
    try:
        f = float(val)
        if f != f:  # NaN check
            return ""
        return round(f, 4)
    except (ValueError, TypeError):
        return ""


def setup_metrics(mode="core"):
    """Setup RAGAS metrics dynamically based on version and mode."""
    metrics = []
    metric_map = {}
    
    # 1. Faithfulness
    if mode in ("core", "faithfulness"):
        try:
            from ragas.metrics import Faithfulness
            metrics.append(Faithfulness())
            metric_map["faithfulness"] = "Faithfulness"
            print("  ✓ Faithfulness loaded (RAGAS 0.2+)")
        except ImportError:
            try:
                from ragas.metrics import faithfulness
                metrics.append(faithfulness)
                metric_map["faithfulness"] = "faithfulness"
                print("  ✓ faithfulness loaded (Legacy)")
            except ImportError:
                print("  ❌ Gagal memuat Faithfulness")
            
    # 2. Relevancy (ResponseRelevancy atau AnswerRelevancy)
    if mode in ("core", "relevancy"):
        relevancy_inst = None
        try:
            from ragas.metrics import ResponseRelevancy
            relevancy_inst = ResponseRelevancy(strictness=1)
            metric_map["response_relevancy"] = "ResponseRelevancy"
            print("  ✓ ResponseRelevancy loaded (RAGAS 0.2+)")
        except ImportError:
            try:
                from ragas.metrics import AnswerRelevancy
                relevancy_inst = AnswerRelevancy(strictness=1)
                metric_map["response_relevancy"] = "AnswerRelevancy"
                print("  ✓ AnswerRelevancy loaded (RAGAS 0.2+)")
            except ImportError:
                try:
                    from ragas.metrics import answer_relevancy
                    relevancy_inst = answer_relevancy
                    metric_map["response_relevancy"] = "answer_relevancy"
                    print("  ✓ answer_relevancy loaded (Legacy)")
                except ImportError:
                    print("  ❌ Gagal memuat Relevancy")
        if relevancy_inst:
            metrics.append(relevancy_inst)
        
    # 3. Precision (WithReference -> WithoutReference -> Legacy)
    if mode in ("core", "retrieval"):
        precision_inst = None
        try:
            from ragas.metrics import LLMContextPrecisionWithReference
            precision_inst = LLMContextPrecisionWithReference()
            metric_map["context_precision"] = "LLMContextPrecisionWithReference"
            print("  ✓ LLMContextPrecisionWithReference loaded (RAGAS 0.2+)")
        except ImportError:
            try:
                from ragas.metrics import LLMContextPrecisionWithoutReference
                precision_inst = LLMContextPrecisionWithoutReference()
                metric_map["context_precision"] = "LLMContextPrecisionWithoutReference"
                print("  ✓ LLMContextPrecisionWithoutReference loaded (RAGAS 0.2+)")
            except ImportError:
                try:
                    from ragas.metrics import context_precision
                    precision_inst = context_precision
                    metric_map["context_precision"] = "context_precision"
                    print("  ✓ context_precision loaded (Legacy)")
                except ImportError:
                    print("  ❌ Gagal memuat Context Precision")
        if precision_inst:
            metrics.append(precision_inst)
        
    # 4. Recall (LLMContextRecall -> Legacy)
    if mode in ("core", "retrieval"):
        recall_inst = None
        try:
            from ragas.metrics import LLMContextRecall
            recall_inst = LLMContextRecall()
            metric_map["context_recall"] = "LLMContextRecall"
            print("  ✓ LLMContextRecall loaded (RAGAS 0.2+)")
        except ImportError:
            try:
                from ragas.metrics import context_recall
                recall_inst = context_recall
                metric_map["context_recall"] = "context_recall"
                print("  ✓ context_recall loaded (Legacy)")
            except ImportError:
                print("  ❌ Gagal memuat Context Recall")
        if recall_inst:
            metrics.append(recall_inst)
        
    return metrics, metric_map


from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List, Optional, Any
import subprocess
import os

class KiroChatModel(BaseChatModel):
    model_name: str = "deepseek-3.2"
    api_key: str = ""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = ""
        for m in messages:
            prompt += f"{m.content}\n"
            
        response_text = self._call_kiro(prompt)
        generation = ChatGeneration(message=AIMessage(content=response_text))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "kiro-chat"

    def _call_kiro(self, prompt: str) -> str:
        cmd = [
            "/Users/gustikrisnapranata/.local/bin/kiro-cli",
            "chat",
            "--no-interactive",
            "--trust-tools=",
            "--model", self.model_name,
            prompt
        ]
        
        env = os.environ.copy()
        if self.api_key:
            env["KIRO_API_KEY"] = self.api_key
            
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        stdout = result.stdout
        
        # Log to debug file
        with open("evaluation/kiro_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n=== PROMPT ({self.model_name}) ===\n{prompt}\n")
            f.write(f"=== RAW STDOUT ===\n{stdout}\n")
            f.write(f"=== RAW STDERR ===\n{result.stderr}\n")
            
        # Strip ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        stdout_clean = ansi_escape.sub('', stdout)
            
        lines = stdout_clean.splitlines()
        cleaned_lines = []
        for line in lines:
            if not cleaned_lines and not line.strip():
                continue
            if "WARNING: Failed to retrieve MCP settings" in line or "kiro-cli login" in line:
                continue
            if "Credits:" in line or "Time:" in line:
                continue
            
            line_stripped = line.strip()
            if line_stripped.startswith(">"):
                line_stripped = line_stripped[1:].strip()
                
            cleaned_lines.append(line_stripped)
            
        response = "\n".join(cleaned_lines).strip()
        
        # Extract JSON if present to satisfy RAGAS output parsers
        if "{" in response and "}" in response:
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx+1]
                
        with open("evaluation/kiro_debug.log", "a", encoding="utf-8") as f:
            f.write(f"=== CLEANED RESPONSE ===\n{response}\n")
            
        return response


def evaluate_single_row(row, metrics, api_keys, max_contexts, max_context_chars, delay_base=5, primary_model="llama-3.3-70b-versatile", fallback_model="llama-3.1-8b-instant"):
    """Evaluate a single row using RAGAS with API key rotation and model fallback."""
    from langchain_groq import ChatGroq
    from ragas import evaluate as ragas_evaluate
    from datasets import Dataset

    question = row["question"]
    answer = row.get("generated_answer", "")
    ground_truth = row.get("ground_truth", "")
    
    # 1. Parse & Slice Contexts
    contexts_json = row.get("retrieved_contexts_json", "[]")
    try:
        contexts = json.loads(contexts_json)
        if not isinstance(contexts, list):
            contexts = [str(contexts)]
    except (json.JSONDecodeError, TypeError):
        ctx = row.get("retrieved_context", "")
        contexts = [ctx] if ctx else []

    # Slice contexts to max_contexts
    contexts = contexts[:max_contexts]
    
    # Slice each context chunk to max_context_chars
    contexts = [c[:max_context_chars] for c in contexts if c.strip()]

    # 2. Validation before RAGAS
    if not question or question.strip() == "":
        return None, "Pertanyaan kosong", False
    if not answer or answer.strip() == "":
        return None, "generated_answer kosong", False
    if not ground_truth or ground_truth.strip() == "":
        return None, "ground_truth kosong", False
    if not contexts:
        return None, "retrieved_contexts kosong setelah pemotongan", False

    # Build dataset based on version
    try:
        # Check if RAGAS 0.2+ dataset keys are used
        from ragas.metrics import Faithfulness
        new_format = True
    except ImportError:
        new_format = False

    if new_format:
        data = {
            "user_input": [question],
            "retrieved_contexts": [contexts],
            "response": [answer],
            "reference": [ground_truth],
        }
    else:
        data = {
            "question": [question],
            "contexts": [contexts],
            "answer": [answer],
            "ground_truth": [ground_truth],
        }

    ds = Dataset.from_dict(data)
    
    # Setup embeddings model
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )

    # If using Kiro key, set fallback model to a Kiro model
    is_kiro_key = api_keys[0].startswith("ksk_")
    actual_fallback = "minimax-m2.1" if is_kiro_key else fallback_model

    models_to_try = [
        {"name": primary_model, "fallback": False},
        {"name": actual_fallback, "fallback": True}
    ]

    current_key_idx = 0
    total_keys = len(api_keys)
    last_error = None
    fallback_used = False

    for model_info in models_to_try:
        model_name = model_info["name"]
        is_fallback = model_info["fallback"]
        
        # Max attempts = retries per key * total keys
        attempts_per_model = total_keys * 2 
        
        for attempt in range(attempts_per_model):
            # Instantiate LLM
            api_key = api_keys[current_key_idx]
            
            if api_key.startswith("ksk_"):
                # Use Kiro model via subprocess
                llm = KiroChatModel(
                    model_name=model_name,
                    api_key=api_key
                )
            else:
                # Use Groq model
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model=model_name,
                    api_key=api_key,
                    temperature=0,
                    max_retries=3,
                )
            
            try:
                result = ragas_evaluate(
                    dataset=ds,
                    metrics=metrics,
                    llm=llm,
                    embeddings=embeddings,
                    raise_exceptions=False
                )
                
                # Check for evaluation errors
                result_df = result.to_pandas()
                
                # Verify if we got non-null metrics
                scores = {}
                scores_found = False
                for col in result_df.columns:
                    col_lower = col.lower()
                    val = result_df[col].iloc[0]
                    # Check if val is not None and not NaN
                    if val is not None and val == val:
                        if "faithful" in col_lower:
                            scores["faithfulness"] = _safe_float(val)
                            scores_found = True
                        elif "relevancy" in col_lower or "relevance" in col_lower:
                            if "answer" in col_lower or "response" in col_lower:
                                scores["response_relevancy"] = _safe_float(val)
                                scores_found = True
                        elif "precision" in col_lower:
                            scores["context_precision"] = _safe_float(val)
                            scores_found = True
                        elif "recall" in col_lower:
                            scores["context_recall"] = _safe_float(val)
                            scores_found = True
                
                if scores_found:
                    return scores, None, is_fallback
                else:
                    raise Exception("RAGAS returned empty or NaN scores")

            except Exception as e:
                last_error = str(e)
                # Rotate key if rate limited or unauthorized
                if "rate_limit" in last_error.lower() or "429" in last_error or "limit" in last_error.lower():
                    current_key_idx = (current_key_idx + 1) % total_keys
                    wait_time = delay_base * (attempt + 1)
                    print(f"    ⚠️ Rate limit model {model_name} dengan key {current_key_idx+1}/{total_keys}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Non-rate-limit error: just try next key or fallback
                    current_key_idx = (current_key_idx + 1) % total_keys
                    time.sleep(1)

        # If model failed, we move to fallback model
        if not is_fallback:
            print(f"  ⚠️ Model {model_name} gagal mengevaluasi ID. Beralih ke fallback model {models_to_try[1]['name']}...")
            fallback_used = True

    return None, f"Evaluasi RAGAS gagal: {last_error}", fallback_used


def generate_summary(all_scores, missing_ids):
    """Generate final summary TSV file."""
    # Classify all scores to ensure they have the latest status
    for s in all_scores:
        s["status"] = classify_status(s)
        
    complete_rows = [s for s in all_scores if s.get("status") == "Complete"]
    partial_rows = [s for s in all_scores if s.get("status") == "Partial"]
    failed_rows = [s for s in all_scores if s.get("status") == "Failed"]
    
    # Answered rows = Complete + Partial
    answered_rows = complete_rows + partial_rows
    
    total_sample = len(all_scores) + len(missing_ids)
    
    # Missing IDs per metric
    missing_by_metric = {
        "faithfulness": [],
        "response_relevancy": [],
        "context_precision": [],
        "context_recall": [],
        "latency_seconds": []
    }
    
    for r in all_scores:
        if r.get("status") != "Failed":
            for m in missing_by_metric.keys():
                v = str(r.get(m, "")).strip()
                if v == "":
                    missing_by_metric[m].append(r["id"])
                    
    summary_data = []
    
    # RAGAS metrics: averages based on Complete rows only
    metrics = [
        ("Faithfulness", "faithfulness", "Jawaban chatbot patuh pada konteks (Complete rows only)"),
        ("Response Relevancy", "response_relevancy", "Jawaban sesuai dengan pertanyaan (Complete rows only)"),
        ("Context Precision", "context_precision", "Presisi konteks yang terambil (Complete rows only)"),
        ("Context Recall", "context_recall", "Kelengkapan informasi ground truth yang terambil (Complete rows only)")
    ]
    
    for metric_name, key, desc in metrics:
        vals = [float(s[key]) for s in complete_rows if s.get(key) and s[key] != ""]
        if vals:
            avg = round(sum(vals) / len(vals), 4)
            mn = round(min(vals), 4)
            mx = round(max(vals), 4)
            cnt = len(vals)
        else:
            avg, mn, mx, cnt = "", "", "", 0
            
        summary_data.append({
            "metric": metric_name,
            "average_score": avg,
            "min_score": mn,
            "max_score": mx,
            "count": cnt,
            "interpretation": desc,
            "notes": "Rerata dari baris status Complete"
        })
        
    # Latency: based on all answered rows (Complete + Partial)
    latencies = [float(s["latency_seconds"]) for s in answered_rows if s.get("latency_seconds") and s["latency_seconds"] != ""]
    if latencies:
        avg_lat = round(sum(latencies) / len(latencies), 3)
        min_lat = round(min(latencies), 3)
        max_lat = round(max(latencies), 3)
        cnt_lat = len(latencies)
    else:
        avg_lat, min_lat, max_lat, cnt_lat = "", "", "", 0
        
    summary_data.append({
        "metric": "Latency",
        "average_score": avg_lat,
        "min_score": min_lat,
        "max_score": max_lat,
        "count": cnt_lat,
        "interpretation": "Rata-rata waktu respons chatbot (All answered rows)",
        "notes": "Diambil dari log kueri"
    })
    
    # Stats rows
    summary_data.append({
        "metric": "Total Sample",
        "average_score": total_sample,
        "min_score": "",
        "max_score": "",
        "count": "",
        "interpretation": "Total sampel pertanyaan",
        "notes": f"Ditargetkan: {total_sample}"
    })
    summary_data.append({
        "metric": "Complete Rows Count",
        "average_score": len(complete_rows),
        "min_score": "",
        "max_score": "",
        "count": "",
        "interpretation": "Baris dengan semua metrik terisi penuh",
        "notes": ""
    })
    summary_data.append({
        "metric": "Partial Rows Count",
        "average_score": len(partial_rows),
        "min_score": "",
        "max_score": "",
        "count": "",
        "interpretation": "Baris dengan metrik terisi sebagian",
        "notes": ""
    })
    summary_data.append({
        "metric": "Failed Rows Count",
        "average_score": len(failed_rows) + len(missing_ids),
        "min_score": "",
        "max_score": "",
        "count": "",
        "interpretation": "Baris gagal atau hilang dari dataset",
        "notes": f"Failed: {len(failed_rows)}, Missing: {len(missing_ids)}"
    })
    
    # Missing IDs lists per metric
    for m in ["faithfulness", "context_precision", "context_recall", "response_relevancy"]:
        m_ids = missing_by_metric[m]
        summary_data.append({
            "metric": f"Missing {m} IDs",
            "average_score": ", ".join(m_ids) if m_ids else "None",
            "min_score": "",
            "max_score": "",
            "count": len(m_ids),
            "interpretation": f"ID pertanyaan dengan metrik {m} kosong",
            "notes": ""
        })
        
    # Write summary TSV
    with open(SUMMARY_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "average_score", "min_score", "max_score", "count", "interpretation", "notes"], delimiter="\t")
        writer.writeheader()
        writer.writerows(summary_data)
        
    return summary_data, complete_rows, partial_rows, failed_rows, missing_by_metric



def main():
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on 30 representative questions")
    parser.add_argument("--ids", type=str, required=True, help="List of comma-separated question IDs to evaluate")
    parser.add_argument("--max-contexts", type=int, default=3, help="Max retrieved contexts to pass to RAGAS")
    parser.add_argument("--max-context-chars", type=int, default=1000, help="Max characters for each context string")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between evaluations in seconds")
    parser.add_argument("--resume", action="store_true", help="Resume from existing scores file")
    parser.add_argument("--metrics", type=str, default="core", choices=["core", "faithfulness", "retrieval", "relevancy"], help="Metrics mode to evaluate")
    parser.add_argument("--force", action="store_true", help="Force re-evaluation and overwrite existing scores")
    parser.add_argument("--model", type=str, default="llama-3.3-70b-versatile", help="Primary model to evaluate with")
    parser.add_argument("--output-scores", type=str, default="ragas_scores_real_30.tsv", help="Output TSV file name for scores")
    parser.add_argument("--output-summary", type=str, default="summary_ragas_real_30.tsv", help="Output TSV file name for summary")
    args = parser.parse_args()

    global RAGAS_FILE, SUMMARY_FILE
    RAGAS_FILE = os.path.join(EVAL_DIR, args.output_scores)
    SUMMARY_FILE = os.path.join(EVAL_DIR, args.output_summary)

    # Parse target IDs
    target_ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    
    print("=" * 60)
    print("📊 AKASIA - Evaluasi RAGAS Asli Berbasis LLM (30 Pertanyaan)")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Mode Metrik: {args.metrics}")
    print(f"⚡ Force Rerun : {args.force}")
    print(f"🤖 Model Utama : {args.model}")
    print()

    # Load results
    if not os.path.exists(RESULTS_FILE):
        print(f"❌ File hasil kueri RAG tidak ditemukan: {RESULTS_FILE}")
        print("   Jalankan evaluasi kueri RAG terlebih dahulu.")
        sys.exit(1)

    results = load_results(RESULTS_FILE)
    results_map = {r["id"]: r for r in results}

    # Identify rows to evaluate & missing IDs
    rows_to_eval = []
    missing_ids = []
    
    for qid in target_ids:
        if qid in results_map:
            rows_to_eval.append(results_map[qid])
        else:
            missing_ids.append(qid)

    if missing_ids:
        print(f"⚠️ Peringatan: ID berikut tidak ditemukan di {RESULTS_FILE}: {', '.join(missing_ids)}")
        print("   ID ini akan tercatat sebagai 'missing ID' pada summary.")
        print()

    print(f"📋 Target Evaluasi:")
    print(f"   → Total ID diinstruksikan: {len(target_ids)}")
    print(f"   → ID ditemukan & diproses: {len(rows_to_eval)}")
    print(f"   → ID hilang/tidak ditemukan: {len(missing_ids)}")
    
    # Load all existing scores from RAGAS_FILE to preserve other questions
    all_scores_map = {}
    if os.path.exists(RAGAS_FILE):
        all_scores_map = load_existing_scores(RAGAS_FILE)
        print(f"   → Loaded {len(all_scores_map)} existing scores from file.")
        
    # Backup if not resume and not force
    if os.path.exists(RAGAS_FILE) and not args.resume and not args.force:
        backup_name = RAGAS_FILE.replace(".tsv", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv")
        shutil.copy2(RAGAS_FILE, backup_name)
        print(f"   → Backup file RAGAS dibuat: {os.path.basename(backup_name)}")

    # Setup API keys from env
    from dotenv import load_dotenv
    load_dotenv()
    
    keys_str = os.environ.get("GROQ_API_KEYS", os.environ.get("GROQ_API_KEY", ""))
    api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    
    if not api_keys:
        print("❌ GROQ_API_KEYS tidak ditemukan di .env")
        sys.exit(1)

    # Initialize RAGAS metrics
    print()
    print("🔧 Menginisialisasi komponen RAGAS...")
    metrics, metric_map = setup_metrics(args.metrics)
    print("✅ RAGAS siap!")
    print()

    # Time Estimation
    # Average RAGAS call takes roughly 15 seconds (retries, rate limits, and network latency)
    est_seconds_per_row = 15.0 + args.delay
    
    # Calculate rows remaining
    rows_remaining = []
    for r in rows_to_eval:
        qid = r["id"]
        # Skip if resume, not force, and already exists in map
        if args.resume and not args.force and qid in all_scores_map:
            continue
        rows_remaining.append(r)
        
    est_total_seconds = len(rows_remaining) * est_seconds_per_row
    
    print(f"⏱️ Estimasi Waktu Evaluasi:")
    print(f"   → Pertanyaan sisa yang akan dievaluasi: {len(rows_remaining)}")
    print(f"   → Estimasi waktu total: {est_total_seconds/60:.1f} menit (~{est_seconds_per_row:.1f} detik/pertanyaan)")
    print()

    print(f"{'='*60}")
    print(f"🚀 Memulai evaluasi RAGAS asli untuk {len(rows_to_eval)} kueri...")
    print(f"{'='*60}")
    print()

    for i, row in enumerate(rows_to_eval):
        qid = row["id"]
        question = row["question"]
        
        # Check if we should skip
        if args.resume and not args.force and qid in all_scores_map:
            print(f"  [{i+1}/{len(rows_to_eval)}] ID {qid}: ⏭️ Dilewati (Resume)")
            continue

        print(f"  [{i+1}/{len(rows_to_eval)}] ID {qid}: {question[:55]}...")
        
        # Preserve existing metrics if row already evaluated
        if qid in all_scores_map:
            score_row = all_scores_map[qid].copy()
        else:
            score_row = {
                "id": qid,
                "category": row.get("category", ""),
                "question": question,
                "faithfulness": "",
                "response_relevancy": "",
                "context_precision": "",
                "context_recall": "",
                "latency_seconds": row.get("latency_seconds", ""),
                "status": "Failed",
                "notes": ""
            }

        # Run evaluation
        scores, error, fallback_used = evaluate_single_row(
            row=row,
            metrics=metrics,
            api_keys=api_keys,
            max_contexts=args.max_contexts,
            max_context_chars=args.max_context_chars,
            delay_base=5,
            primary_model=args.model,
            fallback_model="llama-3.1-8b-instant"
        )

        if scores and not error:
            # Overwrite only the newly evaluated metrics
            score_row.update(scores)
            # Reset status to Success to clear any previous "Failed" status
            score_row["status"] = "Success"
            score_row["status"] = classify_status(score_row)
            if fallback_used:
                fb_name = "minimax-m2.1" if api_keys[0].startswith("ksk_") else "llama-3.1-8b-instant"
                score_row["notes"] = f"Rerun metrics {args.metrics} (Fallback: {fb_name})"
            else:
                score_row["notes"] = f"Rerun metrics {args.metrics} (Model: {args.model})"
                
            parts = []
            for k in ["faithfulness", "response_relevancy", "context_precision", "context_recall"]:
                v = score_row.get(k, "")
                if v != "":
                    parts.append(f"{k[:5]}={v}")
            
            # Append latency if present
            lat = score_row.get("latency_seconds", "")
            if lat != "":
                parts.append(f"latency={lat}s")
                
            print(f"    ✅ Success: {' | '.join(parts)}")
        else:
            score_row["status"] = "Failed"
            score_row["notes"] = error or "Unknown error"
            print(f"    ❌ Failed: {(error or 'Unknown')[:80]}")

        # Update the map and save incrementally
        all_scores_map[qid] = score_row
        sorted_scores = sorted(all_scores_map.values(), key=lambda x: int(x["id"]))
        save_scores(RAGAS_FILE, sorted_scores)

        # Rate limit delay
        if i < len(rows_to_eval) - 1:
            time.sleep(args.delay)

    # Save final scores with updated statuses
    sorted_scores = sorted(all_scores_map.values(), key=lambda x: int(x["id"]))
    save_scores(RAGAS_FILE, sorted_scores)

    # Generate Summary based on the complete combined scores
    summary_data, complete_rows, partial_rows, failed_rows, missing_by_metric = generate_summary(sorted_scores, missing_ids)
    
    print()
    print("=" * 60)
    print("📊 RINGKASAN EVALUASI RAGAS ASLI (30 DATA REPRESENTATIF)")
    print("=" * 60)
    # Total sample is the total size of sorted_scores
    print(f"  Total RAGAS sample: {len(sorted_scores)}")
    print(f"  Complete Rows     : {len(complete_rows)}")
    print(f"  Partial Rows      : {len(partial_rows)}")
    print(f"  Failed Rows       : {len(failed_rows) + len(missing_ids)}")
    print()
    for m in ["faithfulness", "context_precision", "context_recall", "response_relevancy"]:
        m_ids = missing_by_metric[m]
        print(f"  Missing {m:<18} IDs: {', '.join(m_ids) if m_ids else 'None'}")
    print()
    
    # Calculate Averages based on Complete rows only
    print("  Average Metrics (Based on Complete Rows Only):")
    for k in ["faithfulness", "response_relevancy", "context_precision", "context_recall"]:
        vals = [float(s[k]) for s in complete_rows if s.get(k) and s[k] != ""]
        avg = sum(vals) / len(vals) if vals else 0.0
        print(f"    - {k.replace('_', ' ').title():<20}: {avg:.4f}")
        
    # Latency based on answered rows
    answered_rows = complete_rows + partial_rows
    latencies = [float(s["latency_seconds"]) for s in answered_rows if s.get("latency_seconds") and s["latency_seconds"] != ""]
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"  Average Latency (All Answered Rows)  : {avg_lat:.3f}s")
    
    print()
    print("📂 Output Files:")
    print(f"  - {RAGAS_FILE}")
    print(f"  - {SUMMARY_FILE}")
    print()
    print("✅ Evaluasi RAGAS Asli Selesai!")
    print()


if __name__ == "__main__":
    main()
