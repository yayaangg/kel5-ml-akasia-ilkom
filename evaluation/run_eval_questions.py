"""
============================================
AKASIA - Run Evaluation Questions
============================================
Menjalankan semua pertanyaan evaluasi ke sistem RAG AKASIA
dan menyimpan hasil ke evaluation_results.tsv.

Usage:
    python evaluation/run_eval_questions.py                    # Full 100 data
    python evaluation/run_eval_questions.py --limit 5          # Uji cepat 5 data
    python evaluation/run_eval_questions.py --start-id 10 --end-id 20  # Sebagian
    python evaluation/run_eval_questions.py --resume            # Lanjutkan dari terakhir
    python evaluation/run_eval_questions.py --overwrite         # Tulis ulang semua
"""

import sys
import os
import csv
import json
import time
import argparse
import shutil
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_FILE = os.path.join(EVAL_DIR, "evaluation_dataset.tsv")
RESULTS_FILE = os.path.join(EVAL_DIR, "evaluation_results.tsv")

RESULTS_COLUMNS = [
    "id", "category", "question", "ground_truth", "source_document",
    "source_page_or_section", "retrieved_context", "retrieved_contexts_json",
    "generated_answer", "latency_seconds", "source_document_retrieved",
    "confidence", "status", "error_message"
]


def load_dataset(filepath):
    """Load evaluation dataset from TSV file."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def load_existing_results(filepath):
    """Load existing results for --resume mode."""
    if not os.path.exists(filepath):
        return {}
    results = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            results[row["id"]] = row
    return results


def save_results(filepath, results_list):
    """Save results to TSV file."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        for row in results_list:
            writer.writerow(row)


def validate_result(result):
    """Validate a single result row."""
    issues = []
    if result["status"] == "Success":
        if not result.get("generated_answer") or result["generated_answer"].strip() == "":
            issues.append("generated_answer is empty")
        if not result.get("retrieved_contexts_json"):
            issues.append("retrieved_contexts_json is empty")
        else:
            try:
                ctxs = json.loads(result["retrieved_contexts_json"])
                if len(ctxs) < 1:
                    issues.append("retrieved_contexts has 0 items")
            except json.JSONDecodeError:
                issues.append("retrieved_contexts_json is not valid JSON")
        latency = float(result.get("latency_seconds", 0))
        if latency <= 0:
            issues.append("latency is <= 0")
    return issues


def run_single_question(engine, question, max_retries=3, delay_base=2):
    """Run a single question through RAG with retry logic."""
    last_error = None
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            result = engine.query_for_evaluation(question)
            latency = time.time() - start_time
            result["latency_seconds"] = round(latency, 3)
            return result, None
        except Exception as e:
            last_error = str(e)
            if "rate_limit" in last_error.lower() or "429" in last_error:
                wait_time = delay_base * (attempt + 1)
                print(f"    ⚠️ Rate limit hit, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                # Non-rate-limit error, don't retry
                break
    return None, last_error


def main():
    parser = argparse.ArgumentParser(description="Run AKASIA RAG evaluation questions")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to run")
    parser.add_argument("--start-id", type=int, default=None, help="Start from this question ID")
    parser.add_argument("--end-id", type=int, default=None, help="End at this question ID (inclusive)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing results, skip already evaluated")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing results file")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between questions in seconds (default: 2)")
    args = parser.parse_args()

    print("=" * 60)
    print("🎓 AKASIA - Evaluasi RAG")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load dataset
    if not os.path.exists(DATASET_FILE):
        print(f"❌ File dataset tidak ditemukan: {DATASET_FILE}")
        sys.exit(1)

    dataset = load_dataset(DATASET_FILE)
    print(f"📋 Dataset: {len(dataset)} pertanyaan")

    # Filter by ID range
    if args.start_id is not None or args.end_id is not None:
        start = args.start_id or 1
        end = args.end_id or 99999
        dataset = [row for row in dataset if start <= int(row["id"]) <= end]
        print(f"   → Filtered ID {start}-{end}: {len(dataset)} pertanyaan")

    # Limit
    if args.limit is not None:
        dataset = dataset[:args.limit]
        print(f"   → Limited to: {len(dataset)} pertanyaan")

    # Handle resume mode
    existing_results = {}
    if args.resume and os.path.exists(RESULTS_FILE):
        existing_results = load_existing_results(RESULTS_FILE)
        print(f"   → Resume mode: {len(existing_results)} hasil sebelumnya ditemukan")

    # Backup existing file if overwrite
    if args.overwrite and os.path.exists(RESULTS_FILE):
        backup_name = RESULTS_FILE.replace(".tsv", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv")
        shutil.copy2(RESULTS_FILE, backup_name)
        print(f"   → Backup dibuat: {os.path.basename(backup_name)}")
        existing_results = {}

    print()
    print("🔧 Menginisialisasi RAG Engine...")
    
    # Initialize engine
    from rag_engine import RAGEngine
    engine = RAGEngine()
    print("✅ RAG Engine siap!")
    print()

    # Run evaluation
    all_results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0
    total_latency = 0

    print(f"{'='*60}")
    print(f"🚀 Memulai evaluasi {len(dataset)} pertanyaan...")
    print(f"{'='*60}")
    print()

    for i, row in enumerate(dataset):
        qid = row["id"]
        question = row["question"]
        
        # Check if already evaluated (resume mode)
        if qid in existing_results and not args.overwrite:
            all_results.append(existing_results[qid])
            skipped_count += 1
            print(f"  [{i+1}/{len(dataset)}] ID {qid}: ⏭️ Skipped (sudah ada)")
            continue

        print(f"  [{i+1}/{len(dataset)}] ID {qid}: {question[:60]}...")

        result_row = {
            "id": qid,
            "category": row.get("category", ""),
            "question": question,
            "ground_truth": row.get("ground_truth", ""),
            "source_document": row.get("source_document", ""),
            "source_page_or_section": row.get("source_page_or_section", ""),
            "retrieved_context": "",
            "retrieved_contexts_json": "[]",
            "generated_answer": "",
            "latency_seconds": 0,
            "source_document_retrieved": "",
            "confidence": 0,
            "status": "Failed",
            "error_message": ""
        }

        result, error = run_single_question(engine, question)

        if result and not error:
            generated = result.get("generated_answer", "")
            contexts = result.get("retrieved_contexts", [])
            sources = result.get("source_documents", [])
            confidence = result.get("confidence", 0)
            latency = result.get("latency_seconds", 0)

            # Human-readable context (first 3, truncated)
            readable_ctx = " | ".join([c[:200] for c in contexts[:3]])

            result_row["generated_answer"] = generated
            result_row["retrieved_context"] = readable_ctx
            result_row["retrieved_contexts_json"] = json.dumps(contexts, ensure_ascii=False)
            result_row["source_document_retrieved"] = ", ".join(sources)
            result_row["confidence"] = confidence
            result_row["latency_seconds"] = latency
            result_row["status"] = "Success"

            # Validate
            issues = validate_result(result_row)
            if issues:
                result_row["status"] = "Review"
                result_row["error_message"] = "; ".join(issues)
                print(f"    ⚠️ Review: {'; '.join(issues)}")
            else:
                success_count += 1
                total_latency += latency
                print(f"    ✅ OK ({latency:.1f}s, confidence: {confidence}%)")
        else:
            result_row["status"] = "Failed"
            result_row["error_message"] = error or "Unknown error"
            failed_count += 1
            print(f"    ❌ Failed: {error}")

        all_results.append(result_row)

        # Incremental save after each question
        save_results(RESULTS_FILE, all_results)

        # Delay between requests (avoid rate limit)
        if i < len(dataset) - 1:
            time.sleep(args.delay)

    # Final summary
    print()
    print("=" * 60)
    print("📊 RINGKASAN EVALUASI")
    print("=" * 60)
    print(f"  ✅ Berhasil:    {success_count}")
    print(f"  ❌ Gagal:       {failed_count}")
    print(f"  ⏭️ Dilewati:    {skipped_count}")
    print(f"  📝 Total:       {len(all_results)}")
    if success_count > 0:
        print(f"  ⏱️ Rata-rata latency: {total_latency/success_count:.2f}s")
    print(f"  📁 Hasil disimpan: {RESULTS_FILE}")
    print()

    # List failed IDs
    failed_ids = [r["id"] for r in all_results if r["status"] == "Failed"]
    if failed_ids:
        print(f"  ⚠️ ID yang gagal: {', '.join(failed_ids)}")
    
    review_ids = [r["id"] for r in all_results if r["status"] == "Review"]
    if review_ids:
        print(f"  ⚠️ ID yang perlu review: {', '.join(review_ids)}")

    print()
    print("✅ Selesai! Selanjutnya jalankan:")
    print("   python evaluation/run_ragas.py")
    print()


if __name__ == "__main__":
    main()
